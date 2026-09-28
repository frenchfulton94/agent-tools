---
name: godot-scene-files
description: Works with Godot's .tscn and .tres files and the uid:// identity system underneath them — the file grammar and its five sections, what ext_resource and sub_resource mean, when hand-editing a scene is safe and when it corrupts the project, the .uid and .import sidecars, and diagnosing broken or orphaned references. Use when a scene will not load, a resource reference is broken, files need moving or renaming inside a project, a .tscn needs reading or editing directly, or import artifacts need explaining. For writing the GDScript a scene attaches, use gdscript; for running or screenshotting a scene, use godot-testing-and-debugging.
license: MIT
compatibility: Godot 4.x. Reference diagnosis uses the bundled MCP server, which needs no Godot binary for this skill's tools.
---

# Godot Scene Files

A `.tscn` (scene) or `.tres` (resource) file is Godot's text-based serialization
format, and every cross-file reference in a project — scene to script, scene
to sub-scene, resource to texture — resolves through the `uid://` identity
system underneath it, not through the path string alone. The facts below were
measured against a real Godot 4.7.2 project during this plugin's build, not
copied from documentation — several of them the official docs don't state at
all, and where the two disagree, the measurement is what's here.

## Identity lives in three different places, not one

| File type | Identity carrier | Where to find it |
|---|---|---|
| `.gd`, `.gdshader` | `.uid` sidecar file | `player.gd.uid`, one line, next to `player.gd` |
| Imported assets (`.png`, `.wav`, `.glb`, …) | `.import` sidecar | a `uid="uid://…"` line inside `player.png.import` |
| `.tscn`, `.tres` | inline, in the file's own opening heading | the `uid=` attribute on `[gd_scene …]` / `[gd_resource …]` |

A scene or resource is the one case that carries its identity in the same
file it identifies, rather than beside it in a separate sidecar — nothing to
strand by moving the file alone. Everything else needs its sidecar to travel
with it (next section).

UIDs are derived from the file's path, not stored arbitrarily, which makes a
missing sidecar cheap: deleting a `.uid` or `.import` sidecar **in place**
and letting Godot reimport it regenerates the **identical** UID — measured
directly, `uid://b24e2fth3n3xk` before deleting the sidecar and again after
reimport. Treat a missing sidecar as a nuisance, not data loss.

## Moving is the only destructive operation — and only without the sidecar

Moving a sidecar-bearing file *together with* its sidecar is fully
recoverable:

```bash
mv scripts/player.gd entities/player.gd
mv scripts/player.gd.uid entities/player.gd.uid
godot --headless --path . --import
```

The UID is unchanged, so every scene that references `player.gd` by UID keeps
resolving — even though its `ext_resource` heading still literally says
`path="res://scripts/player.gd"` until something resaves it. `--import`
reconciles the UID's filesystem location; it does not rewrite other files'
`path=` text, and it doesn't need to for the reference to work.

Moving the file *without* its sidecar mints a **new** UID at the new path,
and nothing reconciles it with the old one:

```bash
mv scripts/player.gd entities/player.gd   # scripts/player.gd.uid left behind
```

Measured: `uid://bwimerv1cyist` → `uid://byx1h08w7qpq8`. Every scene that
named the old UID is now broken — the old UID is orphaned, the new one is
referenced by nothing — and **no reimport reconciles this**, unlike the
missing-sidecar case above. The identical failure hits an asset moved without
its `.import` (measured: `uid://dka08b7p2ntk2` → `uid://badik1e5sp48k`). Once
this has happened, the only fix is to find every scene that named the old UID
(`reference_graph`'s `broken` list, below) and repoint each one by hand — there
is no command that reassociates an orphaned UID with content that no longer
carries it.

Moving a whole **directory** is always safe: every sidecar inside it moves
with its file, so nothing is left behind.

## The five sections, in file order

0. File descriptor — `[gd_scene format=3 uid="uid://…"]` (or `gd_resource`),
   always first.
1. External resources — `[ext_resource …]` blocks.
2. Internal resources — `[sub_resource …]` blocks.
3. Nodes — `[node …]` blocks, the scene tree itself.
4. Connections — `[connection …]` blocks, signal wiring.

A scene saved before Godot 4.6 also carries a `load_steps=<int>` attribute on
the file descriptor. It's deprecated as of 4.6 — ignore it wherever it's
still present; it plays no role in loading the file.

The full grammar with a worked example of every section is in
`references/tscn-format.md`; the verbatim upstream source is vendored at
`${CLAUDE_PLUGIN_ROOT}/godot-docs/file_formats/tscn.rst`.

## Hand-editing a `.tscn`: what's safe, what corrupts the project

**Safe:** reading the file; changing a scalar property's value
(`radius = 12.0` → `radius = 24.0`); fixing a stale `path=` on an
`ext_resource` heading once you've confirmed which file it should now point
at.

**Unsafe:**

- **Renumbering a resource id** (`id="1_7bt6s"` → `id="1"`). IDs are plain
  string labels the engine trusts, not a value it re-derives — every
  `ExtResource("1_7bt6s")` / `SubResource("1_7bt6s")` call site elsewhere in
  the file has to be updated to match, by hand, in the same edit. Miss one
  and that reference silently fails to resolve.
- **Reordering internal resources or nodes.** A resource that refers to
  another internal resource must appear *after* the one it refers to — order
  is load order, not cosmetic. Node order carries meaning too: the first node
  must be the unparented scene root, and where a node's `index=` is absent,
  appearance order is what decides precedence between inherited and plain
  nodes.
- **Editing anything binary-ish.** `PackedByteArray`/`PackedFloat32Array`
  blobs (mesh `vertex_data`, `index_data`, image bytes, animation `keys`) are
  packed binary encoded as comma-separated integers. A single dropped or
  shifted value corrupts the decoded structure with no parse-time signal —
  the file still parses as valid text.

## Diagnosing a broken or won't-load scene

1. Run `reference_graph` on the project first, **before** opening any
   specific scene. It reports `broken` references, `orphans`, and
   `duplicate_uids` across the whole tree without needing a Godot binary.
2. **Check `parse_errors` before trusting anything else it returned.** A
   scene or resource that fails to parse is skipped, not aborted-on — but
   that means `orphans` and `broken` are only a complete report when
   `parse_errors` is empty. When it isn't, both are a **lower bound** (a file
   referenced only from inside the unparsable scene can be misreported as
   orphaned), and `broken` can also **overcount**: a scene that fails to
   parse contributes no UID of its own, so another scene referencing it by
   UID is reported broken even though the target file exists. Fix or inspect
   whatever's in `parse_errors` first, then re-run before trusting `broken`.
3. Each `broken` entry carries a `reason`: `uid-not-found` means the
   reference names a UID that no file in the project currently owns — the
   signature of a sidecar-less move. `missing-path` means the reference
   carries no UID at all and its literal path doesn't resolve either —
   typically an older-format resource or one hand-edited down to a bare path.
4. Run `scene_tree` on the specific scene `reference_graph` flagged, to see
   which node, script, or `ext_resource` entry is the one actually at fault.
   `scene_tree` parses the file directly too — neither tool needs the engine
   installed.

Broader project- and folder-layout conventions (where scripts and scenes
should live relative to each other, `.gdignore`, addon placement) belong to
`godot-project-architecture`, not here.

## Where the rest lives

- `references/tscn-format.md` — the full five-section grammar with a worked
  example of each, including `groups=`, `node_paths=`, `unique_id=`, and the
  `binds=` connection attribute's literal trailing space.
- `references/uid-and-identity.md` — the sidecar table in full, both move
  outcomes with commands, duplicate UIDs, and exactly what `--import` does
  and does not repair.
- `references/import-pipeline.md` — `.import` file contents, the
  `.godot/imported/` cache, why `.godot/` is safe to delete (and belongs in
  `.gitignore`, unlike the `.import` files themselves), and what triggers a
  reimport.
- `${CLAUDE_PLUGIN_ROOT}/godot-docs/file_formats/tscn.rst` — the verbatim
  vendored source for the grammar.
