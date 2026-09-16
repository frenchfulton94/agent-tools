# PARA

Organizes a directory into Tiago Forte's PARA structure — Projects, Areas,
Resources, Archives — through an approve-before-move workflow.

## What it ships

| Component | Name | Does |
|---|---|---|
| Skill | `organizing-files-with-para` | The run: scan, project list, plan, approve, apply |
| Skill | `maintaining-para-systems` | The recurring pass: inbox, archiving, drift |
| Command | `/para:organize <dir>` | Entry point for a run |
| Hook | `PreToolUse` on Bash | Blocks deletion and unplanned moves in a managed root |
| Script | `scan.py` | Walks a root and emits clusters — grouped decisions, not one row per file |
| Script | `apply.py` | Validates a plan whole, then moves, logging each move to an undo manifest first |
| Script | `undo.py` | Reverses one run from its manifest, skipping any file edited since |
| Script | `para_paths.py` | Every path rule in one place: root validation, denylists, packages, collisions |
| Script | `para_index.py` | Parses and renders `PARA.md`, the user's project list |
| Script | `guard_para_moves.py` | The hook's handler — judges a Bash command against the registered roots |

## Safety model

- Nothing moves without an approved plan.
- `$HOME` and `/` are refused as roots.
- Every move is recorded in an undo manifest before it happens.
- Deletion is not in this plugin's vocabulary. Archiving is a move.
- A never-read denylist is enforced regardless of any budget.

## The managed-root registry

The guard hook only has an opinion inside a root this plugin has been used on.
It learns which those are from one plain text file, and that file is the
plugin's only state outside the directories it organizes:

    ~/.config/para/roots

One absolute path per line. `apply.py` appends a root the first time it
applies an approved plan there, creating the file and its parent directory if
needed; nothing else writes it, and nothing ever removes a line. Set
`PARA_ROOTS_FILE` to point both `apply.py` and the guard somewhere else.

`guard_para_moves.py` reads it on every Bash call. Outside every listed root —
and whenever the file is missing, empty, or unreadable — the guard returns no
opinion at all and the command proceeds untouched. Inside one, it denies a
command that deletes, and denies an `mv` that would move files without an undo
manifest. It never allows anything that would otherwise be blocked.

**To unregister a root**, delete its line:

    $EDITOR ~/.config/para/roots

The next Bash call reads the shorter file and the guard stops having an
opinion about that directory. Removing the whole file unregisters everything.
Nothing else stores the list, and unregistering touches no organized file —
the tree, its `PARA.md`, and its `.para/` manifests all stay exactly as they
are, and re-running `apply.py` there simply registers it again.

## Limits

- macOS signals (Spotlight, Finder tags, download provenance) are best-effort.
  Unindexed volumes fall back to portable metadata, and the scan reports how
  many files came back unindexed.
- Cross-volume destinations are rejected rather than handled.
- No deduplication, no renaming, no content edits.

## Local development

    claude --plugin-dir plugins/para
    python3 -m unittest discover -s plugins/para/scripts/test -p 'test_*.py'

## Attribution

PARA is the method of Tiago Forte, from
[*The PARA Method: Simplify, Organize, and Master Your Digital Life*](https://www.buildingasecondbrain.com/para).
This plugin is an independent implementation. It is not affiliated with or
endorsed by the author, and it ships no text from the book.
