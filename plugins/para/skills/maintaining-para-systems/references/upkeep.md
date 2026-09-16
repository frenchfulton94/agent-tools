# The upkeep pass

Keep it short enough to actually happen. A maintenance routine that takes an
hour gets skipped, and a skipped routine is worth nothing.

## Order

1. **Archives first.** Finished projects are the highest-volume, lowest-risk
   move, and clearing them shrinks everything downstream.
2. **Then the inbox.** List `0-Inbox` directly and plan from the real root —
   never scan or apply with `0-Inbox` as a root of its own. See below.
3. **Then drift.** Report mismatches between `PARA.md` and the folders.

## Sweeping the inbox without a second root

`0-Inbox` is a folder inside the managed root, not a root. Pointing `scan.py`
or `apply.py` at it creates a nested skeleton inside the inbox, registers a
second root with the guard hook, and makes `validate_plan` reject every
destination that reaches back up into the real tree.

The working shape is one plan rooted at the **real** root:

    {
      "root": "/Users/me/Documents",
      "groups": [
        {
          "id": "g1",
          "rule": "matches \"client-redesign\" in PARA.md",
          "reason": "added to the project list since the last pass",
          "destination": "1-Projects/client-redesign",
          "count": 2,
          "samples": ["0-Inbox/brief.pdf", "0-Inbox/wireframes.sketch"],
          "files": ["0-Inbox/brief.pdf", "0-Inbox/wireframes.sketch"]
        }
      ]
    }

Get the file list by listing the directory — `ls "<root>/0-Inbox"` or
`find "<root>/0-Inbox"`. A scan of the real root will not report them:
`walk()` skips the whole `0`–`4` skeleton, inbox included. Anything still
unplaceable stays in `0-Inbox`; leaving it there is the correct answer.

## Drift worth reporting

| Symptom | Likely meaning |
|---|---|
| Folder under `1-Projects`, no `PARA.md` entry | A project started outside the system |
| `PARA.md` entry, no folder | Finished, or never started |
| Project untouched for months | Probably finished, or was an area all along |
| `0-Inbox` growing every pass | The project list is too thin to match against |

That last row is the important one. A growing inbox is usually not a sorting
failure — it means the vocabulary is missing entries, and the fix is in
`PARA.md`, not in more aggressive classification.

## Skipped weeks cost nothing

The system is designed to fail gracefully. A month of skipped upkeep produces a
bigger pass, not a broken tree. Never imply the user has fallen behind.
