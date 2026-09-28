# The debugger panel, the profiler, and logging

Distilled from `tutorials/scripting/debug/` and `tutorials/scripting/logging.rst`
upstream (godotengine/godot-docs, `master`, matching the 4.7 docs this
plugin's vendored slice was synced from) — **none of it is vendored in this
plugin**, unlike the CLI flag tables cited below, so paths here are bare
upstream paths, not `${CLAUDE_PLUGIN_ROOT}`-prefixed ones; there is no local
copy on disk to point at. The debug/visualization CLI flags at the end of
this file *are* vendored and cited accordingly.

## Contents

- [The debugger panel](#the-debugger-panel)
- [The profiler](#the-profiler)
- [Custom performance monitors](#custom-performance-monitors)
- [Logging and backtraces](#logging-and-backtraces)
- [The vendored `--debug-*` and profiling flags](#the-vendored-debug--and-profiling-flags)

## The debugger panel

*(distilled from `tutorials/scripting/debug/overview_of_debugging_tools.rst`
and `tutorials/scripting/debug/debugger_panel.rst`)*

Opens automatically at the bottom of the editor when a running project hits
an unhandled error or a breakpoint. Its tabs:

- **Stack Trace** — opens automatically on a breakpoint; shows the call
  stack and the object's state, with Step Into / Step Over / Break /
  Continue controls. A breakpoint set by clicking the script editor's
  gutter persists across editor restarts but is local to your machine; the
  `breakpoint` keyword written directly into a script is version-controlled
  and travels with the file instead.
- **Errors** — where error and warning messages print while the game runs
  (project-settings-configurable which GDScript warnings even reach here).
- **Evaluator** — a REPL: while execution is paused at a breakpoint, type an
  expression (a member variable, a local in scope, a constant calculation)
  and see its value immediately, without adding a temporary `print()` and
  rerunning.
- **Profiler** — see below.

Note: breakpoints (gutter-based or the `breakpoint` keyword) are not
currently supported in `@tool` scripts running in the editor; use `print()`
there instead.

## The profiler

*(distilled from `tutorials/scripting/debug/the_profiler.rst`; see also
`tutorials/scripting/debug/objectdb_profiler.rst` for the separate
object/memory profiler this file doesn't cover)*

Off by default — it's continuous instrumentation overhead, so it only runs
when you ask it to. Open **Debugger → Profiler**, click **Start** (or check
**Autostart** to have it begin the next time the project runs; that
checkbox itself doesn't persist across editor restarts).

Core measurements: **Frame Time** (everything in one image, physics through
rendering), **Physics Frame** (the allocated budget between physics
updates — 16.66 ms by default for 60 FPS), **Idle Time** (non-physics
per-frame logic — `_process()`, idle-mode timers/cameras), **Physics Time**
(`_physics_process()` and physics-mode nodes). Frame Time *includes*
rendering time — a mysterious spike with fast scripts and physics is worth
checking against particle/visual-effect load before assuming a script bug.

Two measurement modes matter for tracking down *which* function is actually
slow versus merely waiting on one that is:

- **Inclusive** — a function's time including every nested call it made.
  Everything on a call chain looks slow here.
- **Self** — a function's own body time, excluding what it called out to.
  This is what actually isolates the slow function: callers that were
  mostly waiting drop out, and the genuinely slow leaf function stands out.

For finer-grained manual measurement than the profiler's own resolution,
wrap a suspect block with `Time.get_ticks_usec()` calls before and after and
diff them — microsecond precision, no profiler session needed:

```gdscript
var start = Time.get_ticks_usec()
worker_function()
var elapsed_usec = Time.get_ticks_usec() - start
```

The profiler does not currently support C# scripts; profile those with an
external tool (JetBrains Rider/dotTrace with the Godot support plugin,
per upstream).

## Custom performance monitors

*(distilled from `tutorials/scripting/debug/custom_performance_monitors.rst`)*

Beyond the built-in measurements, register your own value to show up
graphed in **Debugger → Monitors**:

```gdscript
func _ready():
	# The slash splits the monitor into a category ("game") and a name
	# ("enemies"). No slash falls back to a generic "Custom" category.
	Performance.add_custom_monitor("game/enemies", get_enemy_count)

func get_enemy_count():
	# Called once per second by the editor's monitor (more often if you
	# query it manually). Must return a number >= 0.
	return get_tree().get_nodes_in_group("enemies").size()
```

The registration doesn't have to live on the same node the metric is about
— an autoload is a reasonable place to centralize several. To read a custom
monitor's value from inside the running game itself (not the editor), call
`Performance.get_custom_monitor("game/enemies")` and display it however you
like (`Label`, custom drawing, …) — this also works in exported release
builds, unlike most of the rest of this file.

## Logging and backtraces

*(distilled from `tutorials/scripting/logging.rst`)*

Godot writes to `user://logs/godot.log` by default (desktop platforms),
rotating up to 5 files by default and renaming the previous session's log
with its rotation date — both the path (`debug/file_logging/log_path`) and
the retention count (`debug/file_logging/max_log_files`) are project
settings, and file logging can be turned off entirely
(`debug/file_logging/enable_file_logging`).

`--quiet`, `--verbose`, and `--print-fps` (all in the vendored CLI table
below) override the equivalent project settings for one run without
changing the project.

**Since Godot 4.5**, a runtime GDScript error automatically logs a full
`GDScript backtrace (most recent call first):` listing of every calling
frame, not just the frame the error occurred in — always on when running in
the editor or a debug export; off by default in release exports for
performance, re-enabled via **Debug → Settings → GDScript → Always Track
Call Stacks** if a production logging pipeline needs it. This is the exact
backtrace block `run_scene`'s own caveat (SKILL.md, `verify-loop.md` rung 2)
refers to: real, and printed to stderr, but not itself present in the MCP
tool's structured result — only the crash line is.

A native crash (not a GDScript error — an engine-level segfault) prints a
separate C++ backtrace *and* a GDScript backtrace to stderr, but only the
GDScript half is human-readable in an official build: official Godot
binaries ship without debug symbols, so the C++ frames resolve to bare
addresses (`godot() [0x4da3358] (??:0)`) rather than file:line pairs. A
usable C++ crash backtrace needs a custom build compiled with debugging
symbols — not something this skill's zero-install baseline can produce.

## The vendored `--debug-*` and profiling flags

The full command-line reference — every flag, its availability tier, and
its description — is vendored verbatim at
`${CLAUDE_PLUGIN_ROOT}/godot-docs/editor/command_line_tutorial.rst`. The
ones relevant to debugging and profiling specifically, pulled out of that
larger table:

| Flag | What it does |
|---|---|
| `-d`, `--debug` | Local stdout debugger. |
| `-b`, `--breakpoints <list>` | Comma-separated `source::line` breakpoint list (no spaces; use `%20`). |
| `--remote-debug <uri>` | Attach a remote debugger, e.g. `tcp://127.0.0.1:6007`. |
| `--debug-server <uri>` | Start the editor's own debug server (editor builds only). |
| `--profiling` | Enable profiling in the script debugger from the start. |
| `--gpu-profile` | Print a GPU task time breakdown for frame rendering. |
| `--debug-collisions` | Draw collision shapes while the scene runs. |
| `--debug-paths` | Draw path lines while the scene runs. |
| `--debug-navigation` | Draw navigation polygons while the scene runs. |
| `--debug-avoidance` | Draw navigation avoidance debug visuals. |
| `--debug-canvas-item-redraw` | Flash a rectangle each time a canvas item redraws — useful for chasing unnecessary redraws. |
| `--debug-stringnames` | Print every `StringName` allocation to stdout on quit. |
| `--print-fps` | Print FPS to stdout every second. |

These are visualization/instrumentation switches, not verification tools —
they help a human watching the window understand *why* something is slow or
misbehaving, which is a different job from the pass/fail verify ladder in
`verify-loop.md`. Most need a real window to be useful at all, the same
constraint `screenshot_scene`/`check_shader` have.
