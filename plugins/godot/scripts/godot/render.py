"""Renderer-backed operations: screenshots and shader validation.

Both need a real rendering device. Headless installs a dummy one, which returns
a null viewport texture (spec 3.2) and compiles no shaders (spec 3.5), so both
operations run windowed with the window positioned far offscreen.

Both drive the engine through a GDScript file that lives in this package rather
than in the user's project, so nothing is written into the project being
inspected.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import engine

DRIVERS = Path(__file__).parent / "drivers"
DRIVER_SCREENSHOT = DRIVERS / "screenshot.gd"
DRIVER_SHADER = DRIVERS / "shadercheck.gd"

# Far enough offscreen that the window does not appear on any real display.
OFFSCREEN = "5000,5000"


class NoDisplay(Exception):
    pass


def has_display() -> bool:
    if sys.platform == "darwin" or sys.platform.startswith("win"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _require_display():
    if not has_display():
        raise NoDisplay(
            "This operation needs a real rendering device and no display is "
            "available. Headless Godot returns a null viewport and compiles no "
            "shaders, so it cannot substitute."
        )


def _drive(driver: Path, root: str, env: dict, width=800, height=600, timeout=90):
    _require_display()
    previous = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        return engine.run(
            [
                "--path", root,
                "--script", str(driver),
                "--resolution", f"{width}x{height}",
                "--position", OFFSCREEN,
            ],
            timeout=timeout,
        )
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def screenshot_scene(root, scene, out_path, width=800, height=600, frames=4, timeout=90):
    result = _drive(
        DRIVER_SCREENSHOT,
        root,
        {
            "GODOT_MCP_SCENE": scene,
            "GODOT_MCP_OUT": os.path.abspath(out_path),
            "GODOT_MCP_FRAMES": str(frames),
        },
        width=width,
        height=height,
        timeout=timeout,
    )
    return {
        "path": os.path.abspath(out_path) if os.path.isfile(out_path) else None,
        "diagnostics": engine.diagnostics(result.stderr),
        "timed_out": result.timed_out,
    }


def check_shader(root, shader_res_path, timeout=60):
    """Compile one shader under a real renderer and report what it says.

    Filtering here is deliberately NOT `(d["file"] or "").endswith(".gdshader")`
    (as an earlier draft of this function had it), for two measured reasons --
    both reproduced against the real engine, not just theorised:

    1. A genuine, correctly-located "SHADER ERROR" can point at a *different*
       res:// file than `shader_res_path` -- e.g. a `#include`d
       ".gdshaderinc". `bad.gdshader`'s own error is reported at
       "res://bad.gdshader:4", but a shader whose bug lives in an included
       file is reported at "res://common.gdshaderinc:LINE". The literal
       ".gdshader" suffix check drops that second case outright, even though
       it is a real, located compile error -- see fixtures
       badinclude.gdshader / common.gdshaderinc and
       test_broken_shader_via_include_is_not_dropped.
    2. When the shader resource itself cannot be loaded at all (missing file,
       wrong extension), Godot's own errors ("Cannot load shader: ...",
       "Failed loading resource: ...") carry only an engine-C++ `at:` frame,
       so `engine.diagnostics` correctly leaves `file` as None for them (that
       frame is not the user's file). The suffix check requires `d["file"]`
       to be a string before calling `.endswith`, so these are ALSO dropped --
       and check_shader would report "no errors" for a shader that could not
       be loaded at all. See test_missing_shader_is_reported_not_swallowed.

    So the rule instead is: keep every "SHADER ERROR" (that severity is only
    ever emitted by the shader compiler itself -- in every case measured here
    it names a real res:// location, just not always `shader_res_path`
    itself), and keep a generic "ERROR" only when its message names the
    shader path we were actually asked to check. That second clause is what
    keeps unrelated engine "ERROR" noise out: two such lines appear on every
    broken-shader run ("Shader compilation failed" / "Parameter \"version\"
    is null", both wrapper noise from the same failed compile, both without
    any res:// location and without the shader path in their message) and
    neither passes this filter.
    """
    result = _drive(
        DRIVER_SHADER,
        root,
        {"GODOT_MCP_SHADER": shader_res_path},
        width=64,
        height=64,
        timeout=timeout,
    )
    found = []
    for d in engine.diagnostics(result.stderr):
        if d["severity"] == "SHADER ERROR":
            found.append(d)
        elif d["severity"] == "ERROR" and shader_res_path in d["message"]:
            found.append(d)
    return found
