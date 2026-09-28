---
name: godot-testing-and-debugging
description: Verifies that a Godot project actually works — checking scripts and shaders for errors, running scenes headlessly, capturing screenshots of what a scene renders, writing unit tests with GUT or gdUnit4, reading the debugger and profiler, and interpreting the engine's own error output. Use when something should be run, tested, or proven to work, when an error message needs interpreting, when a scene behaves wrongly at runtime, or when a change needs visual confirmation. For what the error means about the code itself, use gdscript; for what it means about the scene file, use godot-scene-files.
license: MIT
compatibility: Godot 4.x on PATH or at GODOT_BIN. Screenshots and shader checking need a display. GUT and gdUnit4 are optional project addons and are never assumed installed.
---

# Godot Testing and Debugging

Every other skill in this plugin eventually hands off to this one for the
same question: does it actually work? The facts below were measured directly
against a real Godot 4.7.2 binary during this plugin's build — run again for
this task, not merely copied forward — and several of them contradict what
the engine's own exit code or the obvious CLI invocation would tell you. Read
this skill before trusting either.

## Never trust the exit code

`--check-only` exits `0` whether the script parses cleanly or not. Measured
directly: a `.gd` file with three real parse errors, checked with
`godot --headless --path <project> --check-only --script broken.gd`, returns
exit code `0` — identical to a clean script. The diagnostics exist only on
stderr, one line per error:

```
SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
```

A wrapper that runs the command and checks `$?` — the obvious safety check —
reports broken code as fine. This is the single most consequential fact in
this skill: never test a Godot invocation's exit status as evidence of
correctness. Read stderr (or `check_script`'s returned diagnostics, which do
exactly that) instead. The same applies to `run_scene`: a scene that throws a
runtime error every frame still exits `0` when its frame budget runs out.

## `--headless` renders nothing — and that silently passes broken shaders

`--headless` installs a dummy rendering server. `get_viewport().get_texture()`
returns null under it, so there is no such thing as a headless screenshot.
More consequential: shader compilation happens in the rendering server, and
the dummy one performs none. Measured directly: `load()` on a `.gdshader`
with two independent compile errors (an invalid `vec4` call and an invalid
`vec2` call) returns a non-null `Shader` under `--headless` and prints
nothing at all — no warning, no error, on either stream. The identical file
loaded under a real renderer reports `SHADER ERROR: Invalid arguments for
the built-in function: "vec4(float,float,float)"` at
`res://multi_error.gdshader:4`, and stops there — the second error, on the
line right after it, is never reported in the same run. Shader fixing is
therefore iterative, not batch: fix the reported line, recompile, see what
was hiding behind it. **A shader check that runs headless (the obvious way
to run one in CI) will report success on a shader that cannot compile at
all.** Always check a shader under a real renderer (`check_shader`, or the
CLI equivalent in `references/verify-loop.md`), never headless.

## The verify ladder — cheapest first

Run these in order and stop at the first one that finds the problem; each
one costs more than the last and needs more to be available.

1. **`check_script`** (~130–150 ms, no display needed) — parse and type
   errors in one `.gd` file.
2. **`run_scene`**, headless — logic and runtime errors, with the crash
   site's file and line. Needs no display; catches what static checking
   can't (a null reference reached only after five frames of state).
3. **`screenshot_scene`** — what a scene actually renders. Needs a display.
4. **`check_shader`** — whether a `.gdshader` compiles. Needs a display.

Don't reach for 3 or 4 to answer a question 1 or 2 can already answer — a
script that fails to parse doesn't need a screenshot to explain why a scene
is blank. Full MCP-call-and-CLI-equivalent detail, including sample output
for every rung, is in `references/verify-loop.md`.

`run_scene`'s returned diagnostics give you the *immediate* error site (the
frame where the error was actually raised) *and* the full calling chain
behind it — verified directly: a three-deep call chain (`_ready` →
`level_one` → `level_two`) crashing in `level_two` returns a diagnostic
whose top-level `file`/`line` name `level_two`'s crash site, plus a
`backtrace` list (most recent call first, one `{frame, function, file,
line}` per caller) naming `level_one` and `_ready` right alongside it — the
same `GDScript backtrace (most recent call first):` list Godot prints to
stderr, structured rather than left as text you'd have to go read yourself.
A frame whose location resolves into engine C++ rather than a `res://` path
gets `file`/`line: null`, the same rule applied everywhere else in this
skill. The list is capped at 40 frames — a deep or infinite recursion can
print far more than that — with a `backtrace_truncated` count on the
diagnostic saying how many deeper frames were left out, if any.

`screenshot_scene` returns a `pixel` key — the rendered center pixel's
`(r, g, b)` — specifically so you can tell a real render from a blank one.
File size can't do this: a blank capture and a genuine one compress to
nearly the same PNG size. `check_shader` raises a distinct
`ShaderCheckTimedOut` error rather than returning an empty diagnostics list
when the compile attempt itself times out — an empty list already means
"compiled clean," so a timeout has to be a different, unambiguous outcome
rather than silently looking like success.

## GUT and gdUnit4 are optional, not prerequisites

The zero-install baseline — `check_script` plus `run_scene` — needs no addon
and answers most "does it work" questions on its own: does the script parse,
does the scene run without throwing. Reach for a test framework only when
the project already has one installed, or the user asks for unit tests by
name. Don't tell someone to install GUT or gdUnit4 before you've established
that the zero-install baseline can't answer their actual question. When one
is warranted, `references/test-frameworks.md` covers installing either,
writing a first test, running headless in CI, and which of the two to
reach for.

## Reading what the engine actually says

Godot's own error output has a vocabulary worth learning once:

- **`SCRIPT ERROR`** — a GDScript-level failure: parse error, type error, a
  runtime exception raised inside a script. This is what `check_script` and
  `run_scene` both key off of.
- **`SHADER ERROR`** — a shader compile failure, only ever emitted by the
  shader compiler itself, and only ever under a real renderer (see above).
- **`ERROR`** — a generic engine-level failure. Godot uses this for things
  like a resource that couldn't be loaded at all, so its `at:` frame is
  frequently in engine code (see next point) rather than the res:// file
  that triggered it.
- **`WARNING`** — non-fatal; still worth reading (a stale UID reference in
  a scene reports here, for one real example).

Every diagnostic carries an `at: <function> (<location>:<line>)` frame
immediately after it. **Only a `res://...` location names a file in the
project.** An `at:` frame that instead reads something like
`at: load (modules/gdscript/gdscript_resource_format.cpp:46)` is a line
inside the Godot engine's own C++ source, not a file you can open or fix —
`check_script`/`run_scene`/`check_shader` all already filter these out into
a `null` file/line rather than reporting a fake location, but reading raw
stderr yourself means recognizing the same distinction.

When a runtime error's location matters beyond the immediate crash line,
Godot also prints (since 4.5, on by default in the editor and debug
exports) a full `GDScript backtrace (most recent call first):` list of every
calling frame — `run_scene` carries this through as the diagnostic's own
`backtrace` list (see the ladder section above). The debugger panel, profiler,
custom performance monitors, and file logging are covered — distilled from
upstream, not vendored — in `references/debugging-and-profiling.md`, along
with the `--debug-*` visualization and profiling flags from the vendored
CLI reference.

## Where the rest lives

- `references/verify-loop.md` — every rung of the ladder above with its
  exact MCP call, CLI equivalent, and sample output, plus the exit-code trap
  laid out in full with the measured transcript.
- `references/test-frameworks.md` — installing GUT or gdUnit4, writing a
  first test in each, running headless in CI, and choosing between them.
- `references/debugging-and-profiling.md` — the debugger panel (stack
  trace, breakpoints, the expression evaluator), the profiler (inclusive vs.
  self time, manual microsecond timing), custom performance monitors, file
  logging and log rotation, and the vendored `--debug-*`/profiling CLI
  flags at
  `${CLAUDE_PLUGIN_ROOT}/godot-docs/editor/command_line_tutorial.rst`.

For what a diagnostic means about the script's own code (a warning name, a
type error's fix), use `gdscript`. For what it means about the scene file
that failed to load in the first place (a broken `uid://`, a corrupt
`.tscn`), use `godot-scene-files`. Neither running the engine nor
interpreting what it says belongs to either of those — that's this skill.
