# UID and identity

Read this before moving, renaming, or deleting anything in a Godot project,
or when `reference_graph` reports a broken reference and you need to know
which repair path applies. Everything here was measured against a real
Godot 4.7.2 project during this plugin's build — the official documentation
does not state most of it.

## Contents

- [Where identity lives, file type by file type](#where-identity-lives-file-type-by-file-type)
- [Deleting a sidecar in place is safe](#deleting-a-sidecar-in-place-is-safe)
- [Moving without the sidecar is not](#moving-without-the-sidecar-is-not)
- [Duplicate UIDs](#duplicate-uids)
- [What `--import` does and does not repair](#what---import-does-and-does-not-repair)

## Where identity lives, file type by file type

| File type | Identity carrier | Concretely |
|---|---|---|
| `.gd`, `.gdshader` | `.uid` sidecar | `player.gd.uid` next to `player.gd`, one line: `uid://…` |
| Imported assets (`.png`, `.wav`, `.glb`, …) | `.import` sidecar | a `uid="uid://…"` line inside `player.png.import` |
| `.tscn`, `.tres` | inline, in the file's own heading | `[gd_scene format=3 uid="uid://…"]` / `[gd_resource … uid="uid://…"]` |

A scene or resource is the only case where the identity travels *inside* the
same file — nothing to strand by moving it alone (see the next two
sections). Every other file type depends on a second file sitting beside it,
and that second file is what a move can leave behind.

## Deleting a sidecar in place is safe

UIDs are derived deterministically from the file's path, not assigned once
and stored arbitrarily. So deleting a `.uid` or `.import` sidecar — while
the file it identifies stays exactly where it is — and letting Godot
reimport it regenerates the **identical** UID.

Measured directly: `uid://b24e2fth3n3xk` before deleting `player.gd.uid`,
and `uid://b24e2fth3n3xk` again after `godot --headless --path . --import`
regenerated it. A missing sidecar for a file that hasn't moved is a
nuisance, recoverable by reimporting — never treat it as data loss, and
never treat "the `.uid` file is gone" alone as evidence a reference is
broken.

## Moving without the sidecar is not

Moving a sidecar-bearing file *together with* its sidecar keeps the UID, and
is fully recoverable even though nothing rewrites the stale `path=` text
elsewhere:

```bash
mv scripts/player.gd entities/player.gd
mv scripts/player.gd.uid entities/player.gd.uid
godot --headless --path . --import
```

Every scene that references `player.gd` by UID keeps resolving after this —
the UID never changed, `--import` just reconciles which filesystem path it
currently maps to. Note what it does *not* do: a scene's `ext_resource`
heading can still literally read `path="res://scripts/player.gd"`
afterward. That's fine — the engine resolves through the `uid=` attribute
on the same heading, not the `path=` text, so a stale path string next to a
correct UID is not itself a bug.

Moving the file *without* the sidecar is a different outcome entirely: the
file at its new path has no sidecar to carry forward, so Godot mints a
**brand new** UID for it there. Measured:

```bash
mv scripts/player.gd entities/player.gd   # scripts/player.gd.uid left behind
```

`uid://bwimerv1cyist` (the file's UID before the move) → `uid://byx1h08w7qpq8`
(a new UID minted at the new path). Every scene that named the old UID is now
broken: the old UID is orphaned (owned by nothing), the new UID is referenced
by nothing. **No reimport reconciles this** — reimporting only maps a UID to
a path, it does not merge two different UIDs that both "should" mean the
same logical file.

The identical failure hits an imported asset moved without its `.import`
sidecar. Measured: `uid://dka08b7p2ntk2` → `uid://badik1e5sp48k`.

**The only fix once this has happened:** there is no command that
reassociates an orphaned UID with the content that used to carry it. Find
every scene that names the old UID — `reference_graph`'s `broken` list, with
`reason: "uid-not-found"` — and repoint each one by hand, either by editing
the `ext_resource` heading's `uid=`/`path=` attributes directly or by
re-adding the reference through the editor's inspector (which resolves
against the file's *current* location).

Moving a whole **directory** is always safe, moved-without-sidecar risk
included: every sidecar inside the directory travels with the files it
belongs to, since nothing separates them from their file when the parent
folder itself is what moves.

## Duplicate UIDs

`reference_graph`'s `duplicate_uids` key reports a UID that resolves to more
than one file. This typically comes from copying a file at the OS/filesystem
level (rather than through Godot's own Duplicate/Instance mechanisms) —
copying `player.gd` to `player_backup.gd` with its `.uid` sidecar copied
alongside it leaves two files both claiming the same UID, and whichever one
a `uid://` reference resolves to becomes ambiguous. Each entry lists the UID
and every path currently claiming it; the fix is to delete the sidecar from
whichever copy shouldn't own that identity and reimport, which — per the
section above — mints it a fresh UID of its own rather than reassigning the
original.

## What `--import` does and does not repair

`godot --headless --path . --import` re-scans the project and reconciles
each UID it can still find a sidecar or inline heading for, against that
file's *current* path. Concretely:

- **Does repair:** a UID whose sidecar (or, for a scene/resource, whose
  inline heading) still exists somewhere in the project, at a path different
  from where it last resolved — the exact situation left by a
  sidecar-preserving move.
- **Does not repair:** a UID with no sidecar and no inline heading anywhere
  in the project any more — there's nothing left for the reimport to find
  and reconcile. This is the state a sidecar-less move leaves the *old* UID
  in permanently.
- **Does not rewrite** other files' `path=` text to match a file's new
  location. A scene that resolves correctly through a UID can still show a
  stale `path=` string on the same `ext_resource` heading indefinitely; that
  string only gets refreshed if and when the scene itself is resaved (by the
  editor, or by a tool that rewrites it explicitly).
- **Does not merge** two UIDs that a human considers "the same file" — e.g.
  the old and new UIDs left behind by a sidecar-less move. Reconciliation
  operates per-UID, not per "thing a person means by this file."
