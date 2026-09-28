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
uid="uid://ypc0c31ly0bt"
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

The same guidance does **not** list `.import` files for exclusion, and two
separate things are lost if one goes missing. First, unlike a `.uid`
sidecar's path-derived determinism, a deleted `.import` sidecar is **not**
guaranteed to regenerate the same UID on reimport — measured alternating
between two different values across repeated delete-and-reimport cycles on
the same asset (see `uid-and-identity.md`). A scene that still names the
asset's unchanged `path=` keeps loading regardless, since Godot falls back to
the path when the UID doesn't match — and anything resolving that asset
*purely* by `uid://` is exposed to the churn too, but only on a fresh clone
or CI checkout. `.godot/uid_cache.bin` (itself gitignored, inside `.godot/`)
accumulates historical UID→path mappings rather than replacing them, so a
bare `uid://` load kept working in whatever local session did the reimport;
it's the checkout that never had that cache built up which actually sees the
stale UID resolve to nothing. Second, and independent of
UID continuity, a missing `.import` file loses the `[params]` block: any
non-default import setting — a specific compression mode, disabled
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
