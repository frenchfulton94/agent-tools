#!/usr/bin/env python3
"""MCP server for Godot 4 projects.

Speaks JSON-RPC 2.0 over stdio using only the standard library, so the plugin
needs no install step.

Design notes:
  - Read-only with respect to project source. No tool creates, edits, or saves
    a project file. Every mutation an agent makes goes through Edit/Write/Bash,
    which is what keeps it visible to the guard hook. This is the property the
    whole architecture rests on, so it is enforced in code, not just in
    prose: screenshot_scene's out_path is the one tool argument that names a
    filesystem write destination the caller chooses, and call_tool() refuses
    any out_path that resolves inside the project directory rather than
    handing it to the renderer unchecked -- an unconstrained out_path could
    otherwise silently overwrite an arbitrary project file (project.godot
    itself, in the reported case) with PNG bytes, through a channel the
    Task 9 guard hook cannot see at all. Every other tool's arguments were
    re-checked for the same class of gap and none of them name a
    caller-chosen filesystem write destination. The containment check
    itself compares filesystem identity (device+inode via
    os.path.samefile()), not strings -- a string comparison is defeated for
    free on a case-insensitive-but-case-preserving filesystem (APFS, the
    macOS default; see _out_path_is_inside_project()'s docstring) -- and a
    separate check refuses any out_path that already exists as a
    multiply-linked file, since a hardlink names a file inside the project
    with no distinguishing path for any containment check to catch.
  - project_overview, scene_tree and reference_graph never invoke the Godot
    binary, so a project can still be described on a machine with no engine.
  - check_shader and screenshot_scene need a real rendering device. Headless
    returns a null viewport and compiles no shaders, so it cannot substitute.
  - Running Godot against a project creates .godot/ and .uid artifacts. That is
    normal import behaviour, not something this server writes.
  - api.load_dump() is NOT safe to json.dumps() directly: it stashes an
    internal "__api_search_index__" key on the dump dict it returns (see
    godot/api.py), which would leak into tool output and roughly double the
    payload. Only api.lookup_class() and api.search_classes() build fresh,
    caller-safe dicts -- call_tool must only ever reach the API through those
    two, never through api.load_dump() itself.
  - refs.graph() can report a fifth key, "parse_errors": scene/resource files
    it could not read or parse at all. `orphans` and `broken` are complete
    descriptions of the project only when that list is empty; when it is not,
    both are a lower bound, and `broken` can also OVERCOUNT (a scene that
    failed to parse contributes no uid of its own, so another scene
    referencing it by uid is reported broken even though the target exists).
    reference_graph's tool description says this, and its output puts
    parse_errors first and calls it out in prose rather than leaving it to be
    noticed at the end of a JSON blob.
  - render.check_shader() raises render.ShaderCheckTimedOut instead of
    returning [] when the compile attempt itself times out. That is handled
    as its own error case below: a timeout is not the same fact as "compiled
    with no errors", and reporting it as clean would reintroduce the bug
    Task 7 fixed.

Signal handling:
  engine.run() spawns Godot with start_new_session=True so a hung scene's own
  OS.execute()/OS.create_process() grandchildren can be reaped as a group (see
  godot/engine.py). The flip side is that the child is no longer in this
  server's process group either -- if THIS process is killed, the child is
  orphaned and keeps running until its own --quit-after expires. For
  check_shader and screenshot_scene that child is a real (offscreen) Godot
  window, not an invisible headless process.

  Python's own default SIGINT handling already turns Ctrl-C into a
  KeyboardInterrupt, which engine.run()'s `except BaseException` clause
  already tears down. SIGTERM has no such default: the OS terminates the
  process immediately without running any Python code at all, which would
  skip that cleanup entirely. So both signals are handled explicitly here,
  by wrapping subprocess.Popen process-wide to track every child this server
  spawns (there is at most one in flight at a time -- the server handles one
  JSON-RPC message at a time) and killing its whole process group -- not just
  its pid, for the same OS.execute()-grandchild reason engine.py documents --
  before this process exits.
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Track every child subprocess this server spawns, process-wide --------
#
# engine.run() (godot/engine.py) is the sole place subprocess.Popen is called,
# always with start_new_session=True, so proc.pid IS the child's process
# group id for its whole life (matching engine.py's own _kill_group(), which
# uses proc.pid directly rather than os.getpgid() for the same reason: on
# macOS, getpgid raises once the immediate child has exited even though the
# group -- still holding a live grandchild -- is perfectly valid to signal).
#
# Wrapping subprocess.Popen here, rather than modifying engine.py, tracks
# every child regardless of which module spawned it (engine.run() itself,
# and api.py/render.py, which only ever reach a child through engine.run())
# without adding bookkeeping to modules Tasks 2-7 already built and tested.
# The patch works regardless of import order: engine.py calls
# `subprocess.Popen(...)` as a live attribute lookup on the shared subprocess
# module at call time, not a name bound at import time, so reassigning
# subprocess.Popen here is visible to it as soon as this module is imported,
# no matter when engine.py itself was imported.
_LIVE_PROCS_LOCK = threading.Lock()
_LIVE_PROCS = set()
_RealPopen = subprocess.Popen


class _TrackedPopen(_RealPopen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with _LIVE_PROCS_LOCK:
            _LIVE_PROCS.add(self)

    def _prune_if_done(self, result):
        if result is not None:
            with _LIVE_PROCS_LOCK:
                _LIVE_PROCS.discard(self)
        return result

    def poll(self):
        return self._prune_if_done(super().poll())

    def wait(self, timeout=None):
        result = super().wait(timeout=timeout)
        self._prune_if_done(result)
        return result


subprocess.Popen = _TrackedPopen

from godot import api, engine, project, refs, render, tscn  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "godot", "version": "0.1.0"}

_PROJECT = {"type": "string", "description": "Absolute path to the project directory (contains project.godot)."}

TOOLS = [
    {
        "name": "project_overview",
        "description": "Summarise a Godot project: name, engine features, main scene, autoloads, input actions, rendering method, and export presets. Parses project.godot and export_presets.cfg directly and does not need the Godot binary.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    {
        "name": "scene_tree",
        "description": "Show the node hierarchy of a .tscn file with node types, attached scripts, key properties, and the external resources it references. Parses the file directly and does not need the Godot binary or the editor.",
        "inputSchema": {"type": "object", "properties": {"scene_path": {"type": "string", "description": "Absolute path to a .tscn or .tres file."}}, "required": ["scene_path"]},
    },
    {
        "name": "reference_graph",
        "description": "Report broken uid:// and res:// references, orphaned files, and duplicate UIDs across a project. Catches the case where a script was moved without its .uid sidecar, which no reimport can repair. A scene or resource file that cannot be read or parsed is skipped rather than aborting the whole report, and is listed in the result's `parse_errors`. `orphans` and `broken` are complete only when `parse_errors` is empty -- when it is not, both are a lower bound (a file referenced only from inside a skipped scene can be misreported as orphaned), and `broken` can also OVERCOUNT: a scene that fails to parse contributes no uid of its own, so another scene referencing it by uid is reported broken even though the target file exists. Does not need the Godot binary.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    {
        "name": "check_script",
        "description": "Parse and type-check one GDScript file, returning diagnostics with file and line. Note that Godot's own --check-only exits 0 even when a script has parse errors, so this reads the diagnostics rather than the exit status.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "script_path": {"type": "string", "description": "Path to the .gd file, relative to the project root."}}, "required": ["project_path", "script_path"]},
    },
    {
        "name": "run_scene",
        "description": "Run a scene headlessly for a bounded number of frames and return its output together with any runtime errors and their GDScript backtraces. Rendering is disabled in this mode; use screenshot_scene to see what a scene looks like.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "scene": {"type": "string", "description": "Scene to run, e.g. res://main.tscn. Defaults to the project's main scene."}, "frames": {"type": "integer", "description": "Frames to run before quitting. Default 120."}}, "required": ["project_path"]},
    },
    {
        "name": "check_shader",
        "description": "Compile a .gdshader under a real renderer and report compilation errors with line numbers. Requires a display: compiling headlessly reports success even for shaders that cannot compile. Compilation stops at the first error, so fixing shaders is iterative. If the compile attempt itself times out, this is reported as its own error rather than as a clean compile -- a timeout is not evidence the shader is fine, it means no verdict was reached.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "shader_path": {"type": "string", "description": "Shader to compile, e.g. res://water.gdshader."}}, "required": ["project_path", "shader_path"]},
    },
    {
        "name": "screenshot_scene",
        "description": "Render a scene and save a PNG of it. Runs the game windowed but positioned offscreen, driven by a script outside the project, so nothing is written into the project. Requires a display. out_path must resolve outside the project directory -- a path inside it (project.godot included) is refused rather than silently overwritten. The result also carries the centre pixel's (r, g, b) as rendered, which is how a caller can tell a real render from a blank frame -- file size alone cannot, since a blank capture and a genuine one compress to nearly the same PNG size.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "scene": {"type": "string", "description": "Scene to capture, e.g. res://main.tscn."}, "out_path": {"type": "string", "description": "Absolute path for the PNG. Defaults to a temporary file."}, "width": {"type": "integer"}, "height": {"type": "integer"}, "frames": {"type": "integer", "description": "Frames to advance before capturing. Default 4."}}, "required": ["project_path", "scene"]},
    },
    {
        "name": "lookup_class",
        "description": "Look up a Godot class: its inheritance chain, description, methods, properties, and signals, optionally narrowed to one member. Generated from the user's own engine binary, so it matches their Godot version exactly.",
        "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "Class name, e.g. CharacterBody2D."}, "member": {"type": "string", "description": "Optional method, property, or signal name."}}, "required": ["name"]},
    },
    {
        "name": "search_classes",
        "description": "Find Godot classes by name or by what they do, searching class names and brief descriptions. Use when the right node type for a job is unknown.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]},
    },
]


def _node_lines(node, depth=0):
    if node is None:
        return ["(no root node)"]
    label = f"{'  ' * depth}- {node.name}"
    if node.type:
        label += f" [{node.type}]"
    if node.instance:
        label += f" (instance {node.instance})"
    if "script" in node.props:
        label += f" script={node.props['script']}"
    lines = [label]
    for child in node.children:
        lines.extend(_node_lines(child, depth + 1))
    return lines


def _reference_graph_text(result: dict) -> str:
    """Render refs.graph()'s result with parse_errors surfaced up front.

    graph() returns parse_errors as its fifth key, which a plain
    json.dumps(result) would leave at the tail of the blob -- easy to miss
    for a caller skimming `broken: []` and concluding the report is clean.
    Reordering the dict puts it first in the JSON text too, and a non-empty
    list gets an explicit prose warning ahead of the JSON, spelling out both
    the lower-bound and the overcount consequences rather than leaving the
    caller to infer them from an empty-looking `broken`.
    """
    parse_errors = result.get("parse_errors", [])
    ordered = {"parse_errors": parse_errors}
    ordered.update({k: v for k, v in result.items() if k != "parse_errors"})

    lines = []
    if parse_errors:
        lines.append(
            f"WARNING: {len(parse_errors)} scene/resource file(s) could not be read "
            "or parsed and were skipped -- see parse_errors below. `orphans` and "
            "`broken` are therefore a LOWER BOUND, not a complete report: a file "
            "referenced only from inside a skipped scene can be misreported as "
            "orphaned. `broken` can also OVERCOUNT: a scene that fails to parse "
            "contributes no uid of its own, so another scene referencing it by uid "
            "is reported broken even though the target file exists."
        )
        lines.append("")
    lines.append(json.dumps(ordered, indent=2))
    return "\n".join(lines)


def _out_path_is_inside_project(resolved_out: str, project_root: str) -> bool:
    """True if `resolved_out` names a location at or under `project_root`,
    compared by filesystem identity (device + inode via os.path.samefile())
    rather than by string prefix.

    String comparison is not enough (fix round 2, CRITICAL 1): macOS's
    default filesystem, APFS, is case-insensitive but case-preserving, so
    os.path.realpath() does NOT canonicalise letter case for a real,
    existing directory component -- realpath("/tmp/x/PROJ") returns
    "/tmp/x/PROJ" verbatim even when the on-disk directory is
    "/tmp/x/proj", although both strings address the exact same directory
    (os.stat() on either returns the same (st_dev, st_ino), and
    os.path.samefile() says so). A caller changes nothing on disk and
    still slips a differently-cased out_path straight past
    `resolved_out.startswith(project_root + os.sep)` while landing on the
    very same file. Reproduced directly against a temp copy of the
    fixture: out_path pointed at its own project.godot via an upper-cased
    ancestor directory name, silently overwritten -- the same 372-byte
    config to 165-byte PNG corruption signature as the original,
    string-only bypass. This plugin's primary platform is macOS, so this
    is the default environment, not an edge case.

    Walks up resolved_out's directory chain (its immediate parent, that
    parent's parent, and so on to the filesystem root), comparing each
    ancestor to project_root with os.path.samefile() -- immune to case,
    trailing slashes, and a symlinked directory anywhere in the chain,
    because it compares the (st_dev, st_ino) a name resolves to rather
    than the name itself.

    Falls back to the previous normalised-string comparison only for an
    ancestor that does not exist on disk yet (samefile requires both sides
    to exist, and raises OSError otherwise). That residual imprecision
    cannot be exploited to overwrite anything: a write into a directory
    that does not exist fails cleanly (screenshot_scene reports "No image
    was produced"), unlike the case-insensitive bypass, which succeeded
    silently against a real, existing file.
    """
    if resolved_out == project_root:
        return True

    ancestor = os.path.dirname(resolved_out)
    while True:
        try:
            if os.path.samefile(ancestor, project_root):
                return True
        except OSError:
            return (
                resolved_out == project_root
                or resolved_out.startswith(project_root + os.sep)
            )
        parent = os.path.dirname(ancestor)
        if parent == ancestor:
            return False  # Reached the filesystem root with no match.
        ancestor = parent


def call_tool(name, args):
    if name == "project_overview":
        return True, json.dumps(project.overview(args["project_path"]), indent=2)

    if name == "scene_tree":
        text = open(args["scene_path"], errors="replace").read()
        blocks = tscn.parse(text)
        root = tscn.scene_tree(blocks)
        out = ["# Nodes", *_node_lines(root), "", "# External resources"]
        for res in tscn.ext_resources(blocks) or []:
            out.append(f"- {res['type']} {res['path']} ({res['uid']})")
        return True, "\n".join(out)

    if name == "reference_graph":
        return True, _reference_graph_text(refs.graph(args["project_path"]))

    if name == "check_script":
        found = engine.check_script(args["project_path"], args["script_path"])
        if not found:
            return True, "No diagnostics. The script parses and type-checks."
        return True, json.dumps(found, indent=2)

    if name == "run_scene":
        result = engine.run_scene(
            args["project_path"], args.get("scene"), int(args.get("frames", 120))
        )
        return True, json.dumps(result, indent=2)

    if name == "check_shader":
        # render.check_shader() raises ShaderCheckTimedOut rather than
        # returning [] on a timed-out compile attempt; that is caught in
        # main()'s dispatch below, alongside the other translated exceptions,
        # so it is reported as an error rather than silently falling into
        # the "no diagnostics" branch here.
        found = render.check_shader(args["project_path"], args["shader_path"])
        if not found:
            return True, "Shader compiled with no errors."
        return True, json.dumps(found, indent=2)

    if name == "screenshot_scene":
        out_path = args.get("out_path") or os.path.join(
            tempfile.mkdtemp(prefix="godot-shot-"), "scene.png"
        )
        # out_path reached the renderer with no containment check as
        # originally shipped. A caller-supplied path inside the project --
        # project.godot itself, in the reported case -- was silently
        # overwritten with PNG bytes: no warning, no isError, nothing a
        # guard hook could see, directly contradicting this server's one
        # load-bearing property (read-only w.r.t. project source). Two
        # independent checks below close two independent ways a
        # caller-chosen out_path can name a file inside the project without
        # looking like it does.
        project_root = os.path.realpath(args["project_path"])
        resolved_out = os.path.realpath(out_path)

        # CRITICAL 2 (fix round 2): a pre-existing hardlink from outside the
        # project to a file inside it has no distinct path to resolve -- it
        # IS the same inode under a second, unrelated-looking name, not a
        # reference to one -- so no path-based check, however careful, can
        # see through it; writing through that name corrupts the inside
        # file just as directly as the original bug. Reproduced directly:
        # hard-linking a file inside a temp copy of the fixture from an
        # "outside" name, then writing through that name, corrupted the
        # inside file with the same signature. A screenshot destination
        # that already exists as a multiply-linked file is never a
        # legitimate case, so refusing it costs nothing real.
        try:
            existing_out_stat = os.stat(resolved_out)
        except OSError:
            existing_out_stat = None
        if existing_out_stat is not None and existing_out_stat.st_nlink > 1:
            return False, (
                f"out_path {out_path!r} already exists as a file with more "
                "than one hard link (st_nlink > 1). Writing through it "
                "could modify whatever else shares that inode -- possibly "
                "a file inside the project -- and a hardlink has no "
                "distinct path for a containment check to catch. Refused."
            )

        # CRITICAL 1 (fix round 2): see _out_path_is_inside_project()'s own
        # docstring -- a plain string-prefix comparison here is defeated for
        # free by a case-insensitive-but-case-preserving filesystem (APFS,
        # the default on macOS, this plugin's primary platform).
        if _out_path_is_inside_project(resolved_out, project_root):
            return False, f"out_path must be outside the project directory; got {out_path!r}."

        # MINOR (fix round 2): both checks above validate `out_path` as
        # given (resolved once, above); render.screenshot_scene() below is
        # handed that same, not-re-resolved string. Their agreement is
        # load-bearing on this process's working directory being unchanged
        # between the two calls -- true today (nothing in this codebase
        # ever calls os.chdir()) but not documented anywhere else, so a
        # future change resolving a relative out_path against a different
        # cwd at write time than what was validated here would silently
        # reopen this whole class of gap.
        result = render.screenshot_scene(
            args["project_path"],
            args["scene"],
            out_path,
            width=int(args.get("width", 800)),
            height=int(args.get("height", 600)),
            frames=int(args.get("frames", 4)),
        )
        if not result["path"]:
            return False, "No image was produced.\n" + json.dumps(result, indent=2)
        return True, json.dumps(result, indent=2)

    if name == "lookup_class":
        # api.lookup_class() builds a fresh dict; never reach this through
        # api.load_dump() directly (see the module docstring above).
        found = api.lookup_class(args["name"], args.get("member"))
        if not found:
            return False, f"No such class: {args['name']}"
        return True, json.dumps(found, indent=2)[:60000]

    if name == "search_classes":
        # api.search_classes() likewise builds a fresh list; same rule.
        return True, json.dumps(
            api.search_classes(args["query"], int(args.get("limit", 25))), indent=2
        )

    return False, f"Unknown tool: {name}"


def respond(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def _kill_live_children():
    with _LIVE_PROCS_LOCK:
        procs = list(_LIVE_PROCS)
    for proc in procs:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


def _install_signal_handlers():
    def _handle(signum, frame):
        _kill_live_children()
        sys.exit(1)

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


def dispatch_tool_call(name, arguments):
    """Call `name`, translating the exceptions call_tool() lets through into
    a clean tool-error result rather than a bare traceback. Split out from
    main()'s loop so tests can drive this exception translation directly,
    without going through a subprocess and without needing the exact
    condition (a real timeout, a missing binary, no display) to actually
    occur.

    `arguments` is validated as a dict here, before call_tool() ever sees it
    (fix round 1, IMPORTANT 3): a JSON-RPC caller can send any JSON value for
    "arguments", including a bare string. call_tool()'s bodies all index into
    it as `args["some_key"]`, and indexing a string with a string key raises
    a raw `TypeError: string indices must be integers`, which -- unlike the
    four named exceptions below -- fell straight into the generic `except
    Exception` branch as a multi-line traceback with absolute paths, not a
    one-sentence error. None (arguments omitted) is treated as {}, matching
    prior behaviour for tools whose schema has no required properties.
    """
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return {
            "content": [{"type": "text", "text": (
                f"Invalid arguments for tool {name!r}: expected a JSON object, "
                f"got {type(arguments).__name__} ({arguments!r})."
            )}],
            "isError": True,
        }
    try:
        ok, text = call_tool(name, arguments)
    except engine.MissingBinary as exc:
        ok, text = False, str(exc)
    except render.NoDisplay as exc:
        ok, text = False, str(exc)
    except render.ShaderCheckTimedOut as exc:
        ok, text = False, str(exc)
    except tscn.TscnParseError as exc:
        ok, text = False, f"Could not parse the scene file: {exc}"
    except Exception:
        ok, text = False, traceback.format_exc(limit=3)
    result = {"content": [{"type": "text", "text": text}]}
    if not ok:
        result["isError"] = True
    return result


def main():
    _install_signal_handlers()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = message.get("method")
        request_id = message.get("id")

        if method == "initialize":
            requested = (message.get("params") or {}).get("protocolVersion")
            respond(request_id, {
                "protocolVersion": requested or PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            })
        elif method in ("notifications/initialized", "notifications/cancelled"):
            continue
        elif method == "ping":
            respond(request_id, {})
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = message.get("params") or {}
            # Pass the raw value through -- dispatch_tool_call() itself
            # treats a missing/None "arguments" as {} and rejects anything
            # else that isn't a dict. `or {}` here would also have silently
            # coerced a wrong-but-falsy type (0, False, "") into {}, masking
            # exactly the class of malformed input this is meant to catch.
            result = dispatch_tool_call(params.get("name", ""), params.get("arguments"))
            respond(request_id, result)
        elif request_id is not None:
            respond(request_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
