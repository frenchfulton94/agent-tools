# The verify loop, rung by rung

All output below is quoted from real runs against Godot 4.7.2 during this
plugin's build (either the bundled MCP server's `test/fixtures/sample-project`
fixture, or a scratch project made for this task) — not hypothetical
examples. Use the MCP tool where the harness offers it; the CLI equivalent
is here for the case where it doesn't, or where you want to see raw stderr
yourself (see the `run_scene` caveat under rung 2).

## Contents

- [Rung 0: the exit-code trap, in full](#rung-0-the-exit-code-trap-in-full)
- [Rung 1: `check_script`](#rung-1-check_script)
- [Rung 2: `run_scene`](#rung-2-run_scene)
- [Rung 3: `screenshot_scene`](#rung-3-screenshot_scene)
- [Rung 4: `check_shader`](#rung-4-check_shader)
- [If the MCP server isn't available at all](#if-the-mcp-server-isnt-available-at-all)

## Rung 0: the exit-code trap, in full

This fixture (`broken.gd`) has three genuine parse errors:

```gdscript
extends Node

func _ready() -> void:
	var x: int = "not an int"
	undefined_function_call()
```

Run directly:

```
$ godot --headless --path . --check-only --script broken.gd
Godot Engine v4.7.2.stable.official.ed1daf0bf - https://godotengine.org

SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
SCRIPT ERROR: Parse Error: Cannot assign a value of type String to variable "x" with specified type int.
          at: GDScript::reload (res://broken.gd:5)
SCRIPT ERROR: Parse Error: Function "undefined_function_call()" not found in base self.
          at: GDScript::reload (res://broken.gd:6)
ERROR: Failed to load script "res://broken.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
$ echo $?
0
```

Exit code `0`. Identical to what a clean script returns. The fourth
diagnostic's `at:` frame — `modules/gdscript/gdscript_resource_format.cpp:46`
— is a line inside Godot's own C++ source, not `broken.gd`; it is correctly
left with no file/line by anything that classifies this output (see rung 1).
Timing on this machine: three consecutive runs came in at 0.150s, 0.152s,
and 0.145s wall-clock — call it "~130–150 ms," not a precise constant, but
consistently well under the time it takes to reason about whether you even
need to run it.

Whatever you do with Godot's exit status elsewhere, never use it to answer
"did this work." The rest of this document reads stderr instead, every time.

## Rung 1: `check_script`

**Needs:** the binary, no display.
**MCP call:** `check_script(project_path, script_path)`, `script_path`
relative to the project root.
**CLI equivalent:** `godot --headless --path <project> --check-only --script <path>`,
reading stderr rather than the exit code.

Real output for `broken.gd` above, through the MCP tool:

```json
[
  {
    "severity": "SCRIPT ERROR",
    "message": "Parse Error: Cannot assign a value of type \"String\" as \"int\".",
    "file": "res://broken.gd",
    "line": 5
  },
  {
    "severity": "SCRIPT ERROR",
    "message": "Parse Error: Cannot assign a value of type String to variable \"x\" with specified type int.",
    "file": "res://broken.gd",
    "line": 5
  },
  {
    "severity": "SCRIPT ERROR",
    "message": "Parse Error: Function \"undefined_function_call()\" not found in base self.",
    "file": "res://broken.gd",
    "line": 6
  },
  {
    "severity": "ERROR",
    "message": "Failed to load script \"res://broken.gd\" with error \"Parse error\".",
    "file": null,
    "line": null
  }
]
```

The fourth entry's `file`/`line` are `null` — its `at:` frame pointed into
engine C++, not a `res://` path, so it isn't reported as a location in the
project. A clean script returns an empty list (the human-readable CLI wraps
this as "No diagnostics. The script parses and type-checks.").

This is the cheapest rung by a wide margin and catches the most common class
of "did I break something" — always run it first on a script you just edited.

## Rung 2: `run_scene`

**Needs:** the binary, no display.
**MCP call:** `run_scene(project_path, scene?, frames=120)`. `scene` defaults
to the project's main scene.
**CLI equivalent:** `godot --headless --path <project> --quit-after <frames> [--scene <path>]`.

Real output for a scene whose script raises a runtime error three calls deep
(`_ready` → `level_one` → `level_two`, an out-of-bounds array read in
`level_two`):

```json
{
  "stdout": "Godot Engine v4.7.2.stable.official.ed1daf0bf - https://godotengine.org\n\n",
  "diagnostics": [
    {
      "severity": "SCRIPT ERROR",
      "message": "Out of bounds get index '5' (on base: 'Array')",
      "file": "res://crasher.gd",
      "line": 20,
      "backtrace": [
        {"frame": 0, "function": "level_two", "file": "res://crasher.gd", "line": 20},
        {"frame": 1, "function": "level_one", "file": "res://crasher.gd", "line": 15},
        {"frame": 2, "function": "_ready", "file": "res://crasher.gd", "line": 11}
      ]
    }
  ],
  "timed_out": false
}
```

Raw stderr for the same run, for comparison:

```
SCRIPT ERROR: Out of bounds get index '5' (on base: 'Array')
          at: level_two (res://crasher.gd:20)
          GDScript backtrace (most recent call first):
              [0] level_two (res://crasher.gd:20)
              [1] level_one (res://crasher.gd:15)
              [2] _ready (res://crasher.gd:11)
```

Compare the two: `run_scene`'s `diagnostics` carries the crash site
(`level_two`, line 20) as `file`/`line`, exactly as before, and now also a
`backtrace` list matching the engine's own `GDScript backtrace (most recent
call first):` block frame for frame — `level_one` and `_ready` arrive
alongside the crash site rather than only existing in raw stderr. Verified
end to end: the real MCP server, not just the underlying Python, returns
this shape (confirmed over its actual JSON-RPC stdio protocol against a
three-deep crash). A frame whose location isn't a `res://` path (engine
C++, same rule as everywhere else in this skill) gets `file`/`line: null`
instead of a fabricated location, and the list is capped at 40 frames — a
deep or infinite recursion can print far more — with a
`backtrace_truncated` count on the diagnostic when frames were left out.

A `timed_out: true` here means the scene never quit within its frame budget
(a `while true` with no exit condition, for instance) — not the same thing
as "ran cleanly."

## Rung 3: `screenshot_scene`

**Needs:** the binary and a real display (a headless CI runner has neither
a rendering device nor a window server session; see the `has_display()`
check the tool makes before running at all).
**MCP call:** `screenshot_scene(project_path, scene, out_path?, width?, height?, frames?)`.
`out_path` must resolve outside the project directory.
**CLI equivalent:** none direct — this drives the engine windowed
(off-screen-positioned, not headless) through a small bundled GDScript
driver, which is what makes a real render possible at all; there's no single
flag combination that reproduces it.

Real output, screenshotting a two-node scene:

```json
{
  "path": "/…/shot.png",
  "diagnostics": [
    {
      "severity": "WARNING",
      "message": "res://main.tscn:3 - ext_resource, invalid UID: uid://cnnyipgx21jca - using text path instead: res://scripts/player.gd",
      "file": null,
      "line": null
    }
  ],
  "timed_out": false,
  "pixel": [77, 77, 77]
}
```

`pixel` is the rendered center pixel's `(r, g, b)` as actually captured —
check it against what you expect the scene to show. A blank/failed capture
and a genuine one can compress to nearly the same file size, so file size
alone never tells you the render worked; `pixel` is the tool's answer to
that specific gap. `diagnostics` here is whatever `check_script`/`run_scene`
would also report for the same scene load — a screenshot doesn't skip
script errors, it just also gives you pixels.

## Rung 4: `check_shader`

**Needs:** the binary and a real display, for the same reason as rung 3 —
shader compilation happens in the rendering server, and headless installs a
dummy one that performs none of it. See SKILL.md's second section for the
measured proof (a two-error shader that loads clean, with zero output, under
`--headless`).
**MCP call:** `check_shader(project_path, shader_path)`.
**CLI equivalent:** none direct, for the same reason as rung 3 (a bundled
driver script, not a flag combination).

Real output for a shader with an invalid `vec4` call on line 4 **and** an
independent invalid `vec2` call on line 5:

```json
[
  {
    "severity": "SHADER ERROR",
    "message": "Invalid arguments for the built-in function: \"vec4(float,float,float)\".",
    "file": "res://multi_error.gdshader",
    "line": 4
  }
]
```

One entry. The line-5 error is real (confirmed separately: removing line 4's
bug and re-running reports line 5 instead) but never appears in the same
compile attempt — compilation stops at the first error. Treat a clean
`check_shader` result as "no error found *yet*," not "shader has no more
errors," whenever you already know the file changed non-trivially. A
timed-out compile raises `ShaderCheckTimedOut` rather than returning an
empty list — an empty list already means "compiled with no errors," so a
timeout has to surface as a distinguishable failure, not silently read as
success.

## If the MCP server isn't available at all

Every rung above has a CLI form except 3 and 4, which need the bundled
driver scripts to get a real render without touching the project. Rungs 1
and 2 (`check_script`/`run_scene`) are fully reproducible by hand with the
`--check-only` and `--quit-after` invocations shown above — just remember to
read stderr, never the exit code.
