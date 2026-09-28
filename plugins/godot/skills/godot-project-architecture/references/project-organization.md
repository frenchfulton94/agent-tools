# Project organization, version control, and upgrading

Read this for folder layout, naming, what to commit versus ignore, and the
practical path for moving a project between Godot versions. Distilled from
the vendored
`${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/project_organization.rst`
and `${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/version_control_systems.rst`,
with the version-control identity facts corrected against direct
measurement on Godot 4.7.2 (the vendored doc predates the `.uid` sidecar
system and doesn't mention it at all). The upgrade-path and project-settings
material is distilled from upstream files not vendored in this plugin —
`tutorials/migrating/` and `tutorials/editor/project_settings.rst` — and
marked as such below.

## Contents

- [Folder layout and naming](#folder-layout-and-naming)
- [What to commit, what to ignore](#what-to-commit-what-to-ignore)
- [Project settings versus your own config](#project-settings-versus-your-own-config)
- [Upgrading between Godot versions](#upgrading-between-godot-versions)

## Folder layout and naming

Godot has no enforced project structure and no asset database — it uses the
filesystem as-is, and because a scene carries much of its own resource data
inline, a Godot project generally has fewer loose files than an equivalent
project in an engine that externalizes everything. The practical convention
this earns: **group assets close to the scenes that use them**, rather than
segregating by asset type project-wide.

```
/project.godot
/characters/player/cubio.dae
/characters/player/cubio.png
/characters/enemies/goblin/goblin.dae
/characters/enemies/goblin/goblin.png
/levels/riverdale/riverdale.tscn
```

Style guide, for consistency and to sidestep case-sensitivity bugs that only
surface after export:

- **snake_case** for folders and files (C# scripts are the one exception —
  name them after the class in PascalCase, matching C# convention).
- **PascalCase** for node names, matching built-in node casing.
- Third-party resources go in a top-level `addons/` folder by default, even
  when they aren't editor plugins — this makes "what's ours vs. vendored"
  greppable at a glance. Exception: third-party assets tied to one specific
  character or feature can live alongside that feature's own files instead,
  if that's clearer for that case.

Godot's exported `.pck` filesystem is case-sensitive even when the
development machine's filesystem (Windows, and recent macOS by default) is
not — sticking to lowercase `snake_case` project-wide avoids a class of bug
that only appears after export, on a platform the developer may not be
testing on day to day.

To keep a folder out of the import process entirely (faster initial import,
hidden from the FileSystem dock), drop an empty `.gdignore` file in it. Its
contents are ignored — it's a presence marker, not a pattern list like
`.gitignore`. Anything inside becomes unloadable via `load()`/`preload()`
while the marker is present.

## What to commit, what to ignore

**Ignore:** `.godot/` (the engine's project cache — safe to delete and
regenerates automatically) and `*.translation` files (binary-compiled from
source CSV, regenerable from the CSV that should itself be committed).

**Commit — including both sidecar-carrying identity files:**

| File type | Identity carrier | Commit it? |
|---|---|---|
| `.gd`, `.gdshader` | `.uid` sidecar | Yes |
| Imported assets (`.png`, `.wav`, `.glb`, …) | `.import` sidecar | Yes |
| `.tscn`, `.tres` | inline `uid=` on the file's own heading | Yes (the whole file) |

This corrects the vendored
`${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/version_control_systems.rst`,
which predates the
`.uid` sidecar system and says nothing about it. Measured directly against
Godot 4.7.2 for this plugin's build:

- A `.uid` sidecar deleted **in place** (the `.gd`/`.gdshader` file left
  exactly where it is) regenerates the **identical** UID on reimport — the
  UID is derived deterministically from the file's path, reproduced across
  repeated delete-and-reimport cycles, including with `.godot/`'s UID cache
  wiped cold first. Losing a `.uid` sidecar is a nuisance, not a data-loss
  event — but that's exactly why it's still worth committing: regenerating
  it costs a reimport pass, and skipping that cost project-wide is free.
- A `.import` sidecar deleted in place does **not** reliably regenerate the
  same UID — measured alternating between two different values across
  repeated cycles on the same asset. Unlike the `.uid` case, this one *can*
  matter: a reference that resolves purely by `uid://` with no `path=` to
  fall back on can break on a fresh clone or CI checkout once the old UID is
  gone and nothing regenerates it back.

Committing both sidecar types means every clone and every CI checkout starts
from the same UIDs the authoring machine had, rather than regenerating them
(identically, for `.uid`; possibly differently, for `.import`) on first
import. **This skill states what to track and why it matters for version
control; it does not own the deeper UID mechanics** — the full measurement,
the sidecar-less-move failure mode, and how `reference_graph` diagnoses a
broken reference all belong to `godot-scene-files`.

Everything else the vendored doc says still holds: set
`git config --global core.autocrlf input` on Windows to avoid Git marking
files modified purely from CRLF conversion (the editor's own
**Generate Version Control Metadata** command writes a `.gitattributes` that
enforces LF and makes this unnecessary), and reach for Git LFS before the
first commit (not after) if the project has large binary assets — retrofitting
LFS onto an already-committed history means removing and re-adding the
tracked files, which `git lfs migrate` can automate but is enough of a
one-way operation to warrant reading up first.

## Project settings versus your own config

*(distilled from `tutorials/editor/project_settings.rst`, not vendored)*

`project.godot` is a plain-text INI file, editable through the **Project
Settings** window, from code via `ProjectSettings.set_setting()`, or by hand
— all three write the same file, so hand-editing it isn't unsafe, just
usually less convenient than the window.

The one trap: most settings are read **once**, at startup, into a runtime
singleton (`Engine`, `DisplayServer`, a physics/rendering server). Calling
`ProjectSettings.set_setting()` after that point changes the stored value
but has no runtime effect — the thing that already read it isn't watching
for changes. To change something at runtime, use that runtime class
directly (`Engine.max_fps = 60`, not
`ProjectSettings.set_setting("application/run/max_fps", 60)`).

This is also the deciding line for "should this be a project setting or a
value in an autoload/`Resource`": a project setting is right for
engine-level, mostly-static configuration (rendering method, physics tick
rate, input map). A value that changes during play, or that's specific to
one save file or one player, belongs in an autoload or a `Resource` — not in
`project.godot`, which is shared, one-per-project, and not meant to be
rewritten as gameplay state.

## Upgrading between Godot versions

*(distilled from `tutorials/migrating/`, not vendored)*

**3.x → 4.x (a major version bump):** back up first — the project upgrade
tool performs no backup of its own, so use version control or a plain
folder copy. Then run the Project Manager's **Convert Full Project**, or the
command-line equivalent (`godot --path <dir> --convert-3to4`, with optional
size-limit overrides for very large files) if the GUI tool balks. Expect a
large amount of manual follow-up regardless: the converter handles renamed
nodes and many renamed methods/properties automatically, but signal
connection syntax, several inverted properties, and any custom shader code
need a human pass afterward. This project's compatibility line is Godot
4.x, so this path only matters when importing a genuinely legacy project —
most day-to-day upgrades are the next case.

**4.x → 4.(x+1) (a minor version bump):** each release publishes its own
"Upgrading from Godot 4.N to Godot 4.(N+1)" page with a breaking-changes
table, one row per API change, columned by **GDScript Compatible**, **C#
Binary Compatible**, and **C# Source Compatible**. Read the column that
applies to the project before upgrading — a change can break C# binary
compatibility while remaining fully GDScript-compatible, so a GDScript-only
project may need to check nothing beyond skimming the table. Most entries
across the 4.1–4.7 upgrade pages are additive (a new optional parameter, a
method moved to a shared base class) rather than removals, which is why
each page opens with "for most games and apps made with 4.N, it should be
relatively safe to migrate."

Version control matters most for this path, not the 3-to-4 one: commit
before upgrading, upgrade, run the project, and use the diff against that
commit — not memory — to see what the editor or the conversion step
actually touched.
