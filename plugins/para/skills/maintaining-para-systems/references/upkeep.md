# The upkeep pass

Keep it short enough to actually happen. A maintenance routine that takes an
hour gets skipped, and a skipped routine is worth nothing.

## Order

1. **Archives first.** Finished projects are the highest-volume, lowest-risk
   move, and clearing them shrinks everything downstream.
2. **Then the inbox.** Re-scan `0-Inbox` as its own root.
3. **Then drift.** Report mismatches between `PARA.md` and the folders.

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
