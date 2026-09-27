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
import re
import subprocess
import sys
from pathlib import Path

from . import engine

DRIVERS = Path(__file__).parent / "drivers"
DRIVER_SCREENSHOT = DRIVERS / "screenshot.gd"
DRIVER_SHADER = DRIVERS / "shadercheck.gd"

# Far enough offscreen that the window does not appear on any real display.
OFFSCREEN = "5000,5000"

_PIXEL_LINE = re.compile(r"^GODOT_MCP_PIXEL (\d+),(\d+),(\d+)\s*$", re.MULTILINE)


class NoDisplay(Exception):
    pass


class ShaderCheckTimedOut(Exception):
    pass


def has_display() -> bool:
    if sys.platform == "darwin":
        # `launchctl print gui/<uid>` is Apple's documented way to check for
        # a bootstrapped per-user GUI domain -- exit 0 means this process
        # can reach a window server session, non-zero (or the command not
        # existing at all) means it cannot: a headless macOS CI runner or a
        # LaunchDaemon running outside any user's GUI session has neither.
        # Verified directly on this machine: `launchctl print gui/$(id -u)`
        # exits 0 in an interactive session.
        try:
            result = subprocess.run(
                ["launchctl", "print", f"gui/{os.getuid()}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except OSError:
            return False
    if sys.platform.startswith("win"):
        # Not measured: a Windows service running under Session 0 has no
        # interactive desktop and would need the same scrutiny this darwin
        # branch just got (some equivalent of checking for an attached
        # interactive window station). Left as an unconditional True because
        # neither of us can test a Windows box right now -- flagged rather
        # than silently assumed correct.
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _require_display():
    if not has_display():
        raise NoDisplay(
            "This operation needs a real rendering device and no display is "
            "available. Headless Godot returns a null viewport and compiles no "
            "shaders, so it cannot substitute."
        )


def _drive(driver: Path, root: str, extra_env: dict, width=800, height=600, timeout=90):
    """Run the engine windowed against `driver`, with `extra_env` visible to it.

    Builds a plain local dict (`{**os.environ, **extra_env}`) and passes it
    straight through to `engine.run(..., env=...)` -- never touches the
    process's own `os.environ`. An earlier version of this function mutated
    `os.environ` in place and restored it in a `finally`, which is a shared,
    unlocked, process-wide global: two concurrent calls (a long-lived MCP
    server -- see api.py's own docstring -- fields overlapping calls as a
    matter of course) race that same dict, and whichever call's update wins
    at the moment the OTHER call's subprocess actually spawns determines
    what THAT subprocess sees. Reproduced 3/3 with ordinary threading, no
    adversarial timing: two concurrent check_shader calls on different
    shaders both reported the same (wrong, for one of them) verdict -- a
    silently WRONG answer, not a crash, which is worse here. Building an
    independent dict per call and handing it to Popen via the `env=` kwarg
    removes the shared mutable state entirely rather than narrowing the
    race window; see TestDriveEnvIsolation in test_render.py.
    """
    _require_display()
    return engine.run(
        [
            "--path", root,
            "--script", str(driver),
            "--resolution", f"{width}x{height}",
            "--position", OFFSCREEN,
        ],
        env={**os.environ, **extra_env},
        timeout=timeout,
    )


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
    pixel_match = _PIXEL_LINE.search(result.stdout or "")
    pixel = tuple(int(c) for c in pixel_match.groups()) if pixel_match else None
    return {
        "path": os.path.abspath(out_path) if os.path.isfile(out_path) else None,
        "diagnostics": engine.diagnostics(result.stderr),
        "timed_out": result.timed_out,
        "pixel": pixel,
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

    The "message names the path" match is anchored to word-token boundaries
    (`(?<!\\w)<path>(?!\\w)`), not a bare substring test. A plain
    `shader_res_path in d["message"]` matched a completely unrelated file:
    a project with an autoload naming
    "res://good.gdshader_backup_v2.gdshader" poisoned a clean
    `check_shader(root, "res://good.gdshader")` call with that other file's
    errors, purely because the checked path is a string prefix of the
    other one. The anchored version still matches both real shapes Godot
    emits ("Cannot load shader: <path>" -- end of string -- and "Failed
    loading resource: <path>." -- a following "."), since neither is a
    `\\w` character, and rejects the collision, since the character right
    after the match in "..._backup_v2.gdshader" is "_", a word character.
    See TestCheckShaderPathAnchoring.

    Raises ShaderCheckTimedOut rather than silently returning `[]` when the
    compile attempt itself times out. `result.timed_out` and "no errors
    found" are not the same fact -- a timed-out attempt has no verdict at
    all, and Task 8's server renders an empty list as "compiled with no
    errors." Falling through to `[]` here would report a shader that was
    never actually checked as clean. See TestCheckShaderTimeout.
    """
    result = _drive(
        DRIVER_SHADER,
        root,
        {"GODOT_MCP_SHADER": shader_res_path},
        width=64,
        height=64,
        timeout=timeout,
    )
    if result.timed_out:
        raise ShaderCheckTimedOut(
            f"check_shader timed out after {timeout}s compiling {shader_res_path!r}. "
            "This is not a verdict -- it is not the same as a clean compile."
        )
    path_pattern = re.compile(r"(?<!\w)" + re.escape(shader_res_path) + r"(?!\w)")
    found = []
    for d in engine.diagnostics(result.stderr):
        if d["severity"] == "SHADER ERROR":
            found.append(d)
        elif d["severity"] == "ERROR" and path_pattern.search(d["message"]):
            found.append(d)
    return found
