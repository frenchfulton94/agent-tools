# Godot

A Claude Code plugin for [Godot 4](https://godotengine.org) game development —
project and scene architecture, the `.tscn`/`.tres` file formats and their
`uid://` identity rules, GDScript, and a verify loop built on the engine's own
headless tooling, rather than a bespoke editor integration.

This is the plugin's foundation commit. It registers the plugin, vendors the
docs slice every later skill reads from, and ships the first skill. The MCP
server, the guard/check hooks, and the remaining sixteen skills land in later
commits against this same plugin; the facts below about the server and the
hooks are design commitments already made (see
`docs/superpowers/specs/2026-09-26-godot-plugin-design.md`), stated here so a
later contributor implements against them rather than re-deciding them.

## Components

| Component | Shape | Covers |
|---|---|---|
| `gdscript` | Skill | Writing and reviewing GDScript — static typing and inference (with the `get_node()` inference trap that silently drops to the base `Node` type), the official style guide's naming and code-order rules, the tri-state warning system and its full warning table, every `@export` annotation and its inspector effect, doc comments, and format strings. |

## The MCP server will be read-only, by design

Once it ships, the server reads and verifies a project — parses scenes and
scripts, runs a scene headless, checks a shader, takes a screenshot, and
serves the class reference generated from the user's own `godot` binary — but
it will never write project source itself. Every mutation stays on
`Edit`/`Write`/`Bash`, the tool surface the `godot-guard` hook can see. An MCP
tool that wrote project files would be a mutation path no hook in this
catalog can observe: not a convenience trade-off, a safety property. Creating
or modifying nodes, saving scenes, and writing project files are out of
scope for the server for this same reason — a future `save_scene` tool would
reopen exactly the gap the guard hook exists to close.

Two of the nine planned tools, `check_shader` and `screenshot_scene`, need a
real display (windowed offscreen rendering) because headless mode renders
nothing and headless shader loading silently passes broken shaders through
without catching them. The other seven need no display. Running Godot at all
— headless or not — creates a `.godot/` cache directory and, as needed,
`.uid` sidecar files as side effects; expect them to appear after any tool
call that invokes the engine, and don't treat their appearance as a bug.

## `godot-docs/` is vendored verbatim — never edit it

Every file under `godot-docs/` is copied byte-for-byte from
[godotengine/godot-docs](https://github.com/godotengine/godot-docs) (see
`godot-docs/VERSION` for the exact commit, engine version, and sync date).
These are the slices where paraphrasing would corrupt exact material a
parser or a script is written against: the `.tscn` grammar, the CLI flag
tables, the GDScript style/typing/warning references, and the export and
feature-tag tables. Every skill's own `references/` distills from these
files; the vendored files themselves are never rewritten, only re-synced as a
whole against a newer docs commit. The engine's own class reference is
deliberately never vendored — it's generated from the user's own `godot`
binary so it always matches the engine version they actually run.

## Prerequisites

None to load the plugin itself.

To act on what it covers, once shipped: a local Godot 4 installation. The
manifest's `godot_bin` setting points the (future) MCP server at a specific
binary; leave it empty and the server looks for `godot`, then `godot4`, on
`PATH`, falling back to `/Applications/Godot.app/Contents/MacOS/Godot` on
macOS.

## Install

```bash
claude plugin install godot@agent-tools
```

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/godot
claude plugin validate plugins/godot --strict
```

## Sources

- Godot docs — <https://github.com/godotengine/godot-docs>, `master` branch, synced against engine 4.7.

## License

MIT.
