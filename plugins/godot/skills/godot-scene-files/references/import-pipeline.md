# The import pipeline

Read this when an imported asset (texture, audio, model, …) isn't behaving as
expected, when deciding what belongs in version control, or when a headless
CI step needs to force a reimport rather than relying on the editor to have
done it. The `.import` file's own field-level format isn't part of this
plugin's vendored doc slice, so treat the field names below as standard
Godot 4.x engine behavior rather than a measurement from this plan; the parts
about what belongs in version control are read directly off
`${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/version_control_systems.rst`.

## Contents

- [`.import` files](#import-files)
- [The `.godot/imported/` cache](#the-godotimported-cache)
- [`.godot/` is safe to delete — `.import` files are not](#godot-is-safe-to-delete--import-files-are-not)
- [What triggers a reimport](#what-triggers-a-reimport)

## `.import` files

Every imported asset gets a sidecar next to it, `<filename>.import`, in a
simple INI-style format. A texture's looks roughly like:

```ini
[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://b24e2fth3n3xk"
path="res://.godot/imported/player.png-a1b2c3d4e5f6.ctex"

[deps]

source_file="res://player.png"
dest_files=["res://.godot/imported/player.png-a1b2c3d4e5f6.ctex"]

[params]

compress/mode=0
mipmaps/generate=false
```

`[remap]` is where the `uid=` this skill's `uid-and-identity.md` refers to
actually lives — it's this line `reference_graph`'s UID index scans for.
`[deps].source_file` names the original asset; `dest_files` names the
generated artifact(s) in the cache. `[params]` is importer-specific — every
asset type (texture, audio, 3D scene, font, …) has its own set of options,
and those options are exactly what a `.import` file preserves that a plain
UID regeneration does not (see below).

## The `.godot/imported/` cache

`dest_files` points into `.godot/imported/`, where Godot stores the actual
engine-ready artifact — a compressed texture, an optimized mesh, a decoded
audio stream — generated from the source asset plus whatever `[params]`
says. This is pure derived output: given the source file and the `.import`
sidecar, Godot can always regenerate everything under `.godot/imported/`
from scratch.

## `.godot/` is safe to delete — `.import` files are not

The vendored version-control guidance is explicit that `.godot/` "stores
various project cache data" and belongs in `.gitignore` — nothing under it
is meant to be committed, and nothing is lost by deleting the whole folder:
the next time the project is opened (or reimported headlessly), Godot
regenerates it from the source assets and their `.import` sidecars.

The same guidance does **not** list `.import` files for exclusion. That's
deliberate, and for a more specific reason than "it carries the UID" — a
deleted `.import` sidecar regenerates an *identical* UID on reimport (see
`uid-and-identity.md`), so UID continuity alone wouldn't require committing
it. What a missing `.import` file actually loses is the `[params]` block:
any non-default import setting — a specific compression mode, disabled
mipmaps, a particular texture filter — resets to that importer's defaults on
regeneration, silently, with no error. Commit `.import` files; gitignore
`.godot/`.

## What triggers a reimport

- **Opening the project in the editor.** The editor's filesystem dock
  watches for new or changed source assets and reimports automatically.
- **`godot --headless --path . --import`** — the explicit, scriptable
  trigger, used in CI or any headless context where no editor session is
  open to notice a change on its own. This is also the repair step after a
  sidecar-preserving move (`uid-and-identity.md`).
- **A source asset's content changing** without a matching update to its
  `.import` sidecar — the importer detects the mismatch and regenerates the
  cached artifact (and, per the section above, an outright missing sidecar
  is treated as "needs reimport" too, not as an error).
