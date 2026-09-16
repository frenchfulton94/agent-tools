# macOS signals

`scan.py` reads these via `mdls`. Every one can be absent — Spotlight indexing
is off on many external and network volumes — so each falls back to portable
metadata and the scan reports an `unindexed` count.

| Key | Use |
|---|---|
| `kMDItemLastUsedDate` | Age decisions. Preferred over mtime. |
| `kMDItemUserTags` | Finder tags — judgement the user already recorded. |
| `kMDItemWhereFroms` | Download provenance; the host often names the project. |
| `kMDItemFinderComment` | Rare, free when present. |
| `kMDItemContentTypeTree` | Package detection. |

## Why last-used beats mtime

mtime changes on sync, copy, restore, and cloud re-download. A folder restored
from backup has a uniformly recent mtime and a correct last-used date. Since
age-based archiving is the highest-volume rule in a typical run, the difference
decides the largest group in the plan.

## Packages are single items — but not all of them are unmovable

`.app`, `.rtfd`, `.photoslibrary`, `.xcodeproj` and anything whose
`kMDItemContentTypeTree` contains `com.apple.package` is **one item**, never a
directory to walk into. Descending into a package scatters it and breaks it.
The same applies to `.git`, `node_modules`, and `.venv` — a dependency tree is
one item by its parent, not a subtree to sort file-by-file.

That is a statement about *walking*, not about *moving*, and the two are not
the same set. `.app`, `node_modules`, `.git`, and anything under a `Library`
directory are never moved at all — they never enter a cluster and never
appear in a plan, because the scan skips them outright. A user-content package
like `.rtfd`, `.photoslibrary`, `.xcodeproj`, or a `.venv`/`.tox` directory is
still a single item, but it is an ordinary one: it can be archived or filed as
a whole, the same as any other file, once a rule picks it up.

## A degraded scan must be visible

When `unindexed` is high, say so in the plan. A silently degraded scan that
reports confident groupings from mtime alone is worse than one that admits
Spotlight had nothing.
