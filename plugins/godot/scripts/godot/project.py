"""Read project.godot and export_presets.cfg.

Both use Godot's INI dialect: `[section]` headings, `key=value` pairs, and
values that may span lines when a bracket or brace is left open. Keys contain
slashes (`config/name`), so this is not configparser-compatible.

Nothing here invokes the Godot binary. A project can be described on a machine
with no engine installed, and test_no_binary_needed pins that.
"""

from __future__ import annotations

import os
import re

_SECTION = re.compile(r"^\[([^\]]+)\]\s*$")
# Godot's own ConfigFile accepts keys this pattern used to reject, and the
# rejected line was SILENTLY skipped. Measured on 4.7.2: InputMap.has_action()
# returns true for "2d_jump" and "move-left", and [layer_names] keys look like
# "2d_physics/layer_1" -- none of which start with a letter or underscore, or
# avoid hyphens. project_overview exposes input_actions as part of its
# contract, so those actions vanished from a read tool's answer with no error.
# Widened to accept, NOT to raise: an unrecognised line is still skipped
# rather than made fatal, which is the deliberate asymmetry parse_cfg keeps
# (it raises only on an unterminated value, where the file is truly corrupt).
_KEY = re.compile(r'^([^=\s\[][^=]*?)\s*=\s*(.*)$')


def _incomplete(value: str) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for ch in value:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_string:
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
    return depth > 0 or in_string


def parse_cfg(text: str) -> dict:
    out: dict = {"": {}}
    section = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.strip()
        if not stripped or stripped.startswith(";"):
            continue
        heading = _SECTION.match(stripped)
        if heading:
            section = heading.group(1)
            out.setdefault(section, {})
            continue
        kv = _KEY.match(stripped)
        if kv:
            key, value = kv.group(1), kv.group(2)
            value_start_line = i
            while _incomplete(value) and i < len(lines):
                value += "\n" + lines[i]
                i += 1
            if _incomplete(value):
                raise ValueError(
                    f"Value not closed before end of file: [{section}] {key} = ... (started at line {value_start_line})"
                )
            out.setdefault(section, {})[key] = value.strip()
    return out


def _unquote(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def _string_list(value: str | None) -> list:
    if not value:
        return []
    return re.findall(r'"([^"]*)"', value)


def find_root(start: str) -> str | None:
    path = os.path.abspath(start)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(path, "project.godot")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def overview(root: str) -> dict:
    with open(os.path.join(root, "project.godot")) as f:
        cfg = parse_cfg(f.read())
    presets_path = os.path.join(root, "export_presets.cfg")
    if os.path.isfile(presets_path):
        with open(presets_path) as f:
            cfg.update(parse_cfg(f.read()))
    app = cfg.get("application", {})

    autoloads = {}
    for name, value in cfg.get("autoload", {}).items():
        path = _unquote(value) or ""
        # A leading "*" marks the autoload as a singleton; it is not part of the path.
        autoloads[name] = path[1:] if path.startswith("*") else path

    presets = []
    preset_sections = sorted(
        (s for s in cfg if re.fullmatch(r"preset\.\d+", s)),
        key=lambda s: int(s.split(".")[1]),
    )
    for section in preset_sections:
        body = cfg[section]
        presets.append(
            {
                "name": _unquote(body.get("name")),
                "platform": _unquote(body.get("platform")),
                "runnable": body.get("runnable", "false").strip() == "true",
                "export_path": _unquote(body.get("export_path")),
            }
        )

    return {
        "name": _unquote(app.get("config/name")),
        "features": _string_list(app.get("config/features")),
        "main_scene": _unquote(app.get("run/main_scene")),
        "autoloads": autoloads,
        "input_actions": sorted(cfg.get("input", {}).keys()),
        "rendering_method": _unquote(
            cfg.get("rendering", {}).get("renderer/rendering_method")
        ),
        "export_presets": presets,
    }
