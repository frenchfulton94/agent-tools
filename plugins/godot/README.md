# Godot

A Claude Code plugin for [Godot 4](https://godotengine.org) game development —
project and scene architecture, the `.tscn`/`.tres` file formats and their
`uid://` identity rules, GDScript, and a verify loop built on the engine's own
headless tooling, rather than a bespoke editor integration.

## Skills

Four skills, each triggering on a different slice of "something touches
Godot." Where two skills' subject matter borders each other, each one's own
description names the sibling that owns the other side (see
`skills/TRIGGERS.md` for the reasoning behind that boundary, prompt by
prompt, including the two places it genuinely does not resolve cleanly).

| Skill | Covers |
|---|---|
| `gdscript` | Writing and reviewing GDScript: static typing and its inference gaps (including the `get_node()` trap that silently drops to the base `Node` type), the official style guide, the tri-state warning system, every `@export` annotation, doc comments, and format strings. |
| `godot-project-architecture` | Structural decisions: node vs. scene vs. script vs. resource, when an autoload is the right call and when it's a global variable in disguise, signals vs. direct calls, scene/project organization on disk, saving and serializing game data, version control, and upgrading between engine versions. |
| `godot-scene-files` | The `.tscn`/`.tres` grammar and the `uid://` identity system underneath it: `ext_resource`/`sub_resource`, when hand-editing a scene is safe, the `.uid`/`.import` sidecars, and diagnosing broken or orphaned references. |
| `godot-testing-and-debugging` | Proving a project actually works: checking scripts and shaders for errors, running scenes headlessly, capturing screenshots, writing unit tests (GUT, gdUnit4), and reading the debugger/profiler output. |

## The MCP server

Nine tools, all read/verify — none of them write project source. Two need a
real display; the rest run headless.

| Tool | Needs `godot` binary | Needs a display |
|---|---|---|
| `project_overview` | no | no |
| `scene_tree` | no | no |
| `reference_graph` | no | no |
| `check_script` | yes | no |
| `run_scene` | yes | no |
| `check_shader` | yes | **yes** |
| `screenshot_scene` | yes | **yes** |
| `lookup_class` | yes (once, to build the cache) | no |
| `search_classes` | yes (once, to build the cache) | no |

`check_shader` and `screenshot_scene` need a real rendering device because
headless mode renders nothing and silently passes broken shaders through
without catching them — confirmed against the engine, not assumed. The other
seven tools work on a machine with no display at all, and the first three
never invoke the Godot binary: a project can be described and its `.tscn`
files parsed with no engine installed.

## Why the server is read-only

This is load-bearing, not incidental. No tool in this server creates, edits,
or saves a project file — every mutation an agent makes goes through
`Edit`/`Write`/`Bash`, which is the tool surface the `godot-guard` hook can
see and reason about. That is the entire safety property this plugin rests
on: the guard can only stop a destructive file operation it can observe, and
`Edit`/`Write`/`Bash` are the only surfaces any hook in this catalog can see
at all.

An MCP tool that wrote project files — a convenience `save_scene`, say, or a
tool that patched a node's properties in place — would be a mutation path no
hook could observe, reopening exactly the gap the guard exists to close. If
you are the contributor adding the next tool to this server: this is why it
stays read-only, and a write tool here is not a small addition, it is a
different, unguarded architecture. Creating or modifying nodes, saving
scenes, and writing project files are all out of scope for this server for
this same reason.

## The hooks

Both operate on Bash and Edit/Write/MultiEdit — the surfaces a write tool in
the MCP server would, by design, bypass.

**`godot-guard.sh`** (`PreToolUse`, matcher `Bash`) blocks or asks about the
file operations that break `uid://` identity:

- **Denies** `mv`/`git mv`/`cp+rm`/`rsync --remove-source-files`/`find -exec
  mv` of a `.gd`, `.gdshader`, or imported asset that leaves its `.uid` or
  `.import` sidecar behind — this is unrepairable by any later `--import`
  pass, since the file mints a brand-new UID at its new path while every
  scene still names the old one.
- **Asks** before `rm` of a `.tscn`/`.tres`/`.gd`/`project.godot`/
  `export_presets.cfg` — recoverable from git, but orphans every reference
  pointing at it until it is restored.
- **Allows everything else silently**, including `rm` of a `.uid`/`.import`
  sidecar *in place* (the path doesn't change, so a reference naming that
  path still resolves) and `rm -rf .godot/` (purely regenerated cache). A
  guard that fires on harmless operations gets turned off, and then it
  protects nothing — including the one rule that matters.

**`check-gdscript.sh`** (`PostToolUse`, matcher `Edit|Write|MultiEdit`) is
advisory and never blocks: it runs `--check-only` against a `.gd` file just
edited and reports diagnostics as context, because `--check-only`'s own exit
code is `0` even on a script with parse errors — the obvious safety check
passes broken code silently, and this hook exists to surface what the exit
code hides. It requires `jq` (used to parse the hook payload and to build its
JSON output) in addition to `python3`; it degrades to a silent no-op if `jq`
or a `godot` binary isn't found, or if the edited file isn't part of an
already-imported Godot project.

## Running Godot creates artifacts — that's normal

Any tool call that invokes the engine — headless or not — creates a
`.godot/` cache directory and, as needed, per-file `.uid` sidecars, as an
ordinary side effect of Godot's own import process. This plugin does not
write these; Godot does, the same way it would from the editor. Expect them
to appear and don't treat their appearance as a bug or as the MCP server
mutating your project.

## `godot-docs/` is vendored verbatim — never edit it

Every file under `godot-docs/` is copied byte-for-byte from
[godotengine/godot-docs](https://github.com/godotengine/godot-docs); see
`godot-docs/VERSION` for the exact source branch, engine version, and sync
date. These are the slices where paraphrasing would corrupt exact material a
parser or a script is written against: the `.tscn` grammar, the CLI flag
tables, the GDScript style/typing/warning references, and the export and
feature-tag tables. Every skill's own `references/` distills from these
files; the vendored files themselves are never rewritten, only re-synced as a
whole against a newer docs commit. The engine's own class reference is
deliberately never vendored — `lookup_class`/`search_classes` generate it
from the user's own `godot` binary, so it always matches the engine version
they actually run.

## Prerequisites

None to load the plugin itself.

To act on what it covers: a local Godot 4 installation, and `jq` if you want
the advisory `check-gdscript.sh` hook to run (its absence degrades silently,
it does not break anything). The manifest's `godot_bin` setting points the
MCP server at a specific binary; leave it empty and the server looks for
`godot`, then `godot4`, on `PATH`, falling back to
`/Applications/Godot.app/Contents/MacOS/Godot` on macOS.

## Install

```bash
claude plugin install godot@agent-tools
```

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/godot
claude plugin validate plugins/godot --strict
```

## Local development

```bash
cd plugins/godot/scripts && python3 -m unittest discover -s test
```

Runs the whole Python suite (parsers, the engine wrapper, the render driver,
the guard, and the server's JSON-RPC dispatch) against fixture projects; a
handful of tests additionally drive the real engine end to end and are
skipped automatically when `godot` isn't on `PATH`.

```bash
claude --plugin-dir plugins/godot
```

Loads the plugin from this checkout without installing it, for exercising
the skills and the MCP server interactively.

## Sources

- Godot docs — <https://github.com/godotengine/godot-docs>, `master` branch, synced against engine 4.7.

## License

MIT.
