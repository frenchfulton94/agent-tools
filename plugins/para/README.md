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
| Scripts | `scan.py` `apply.py` `undo.py` | The deterministic core |

## Safety model

- Nothing moves without an approved plan.
- `$HOME` and `/` are refused as roots.
- Every move is recorded in an undo manifest before it happens.
- Deletion is not in this plugin's vocabulary. Archiving is a move.
- A never-read denylist is enforced regardless of any budget.

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
