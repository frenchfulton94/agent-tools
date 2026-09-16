# macOS signals

`scan.spotlight` shells out to `mdls -plist - <path>` once per file. It passes
no `-name`, so the whole attribute set comes back, but only four keys are ever
read out of it — the four below. Every one can be absent — Spotlight indexing
is off on many external and network volumes — so each falls back to portable
metadata and the scan reports an `unindexed` count.

| Key | What the code does with it |
|---|---|
| `kMDItemLastUsedDate` | Becomes the entry's `last_used`, which drives every age decision. Preferred over mtime. |
| `kMDItemUserTags` | Collected onto the entry as `tags`. Gathered only — no clustering rule reads it yet. |
| `kMDItemWhereFroms` | Collected onto the entry as `where_from`. Gathered only, the same way. |
| `kMDItemContentTypeTree` | One of the four presence probes behind the entry's `indexed` flag. Nothing else. |

`indexed` is true when *any* of those four keys came back non-null; it is the
signal behind the scan's `unindexed` count. Any key not in this table —
`kMDItemFinderComment` included — is never looked up, however much of it
`mdls` returned.

## Why last-used beats mtime

mtime changes on sync, copy, restore, and cloud re-download. A folder restored
from backup has a uniformly recent mtime and a correct last-used date. Since
age-based archiving is the highest-volume rule in a typical run, the difference
decides the largest group in the plan.

## Packages are single items — but not all of them are unmovable

Package detection is `para_paths.is_package`, and it uses no Spotlight at all
— just two portable checks, so it behaves identically on an unindexed volume:

- the directory's **name** is one of `.git`, `node_modules`, `.venv`, `venv`,
  `.tox`; or
- it is a directory whose **suffix** is one of `.app`, `.rtfd`,
  `.photoslibrary`, `.musiclibrary`, `.bundle`, `.framework`, `.pkg`,
  `.xcodeproj`, `.xcworkspace`, `.playground`.

Anything matching is **one item**, never a directory to walk into. Descending
into a package scatters it and breaks it; a dependency tree is one item by its
parent, not a subtree to sort file-by-file. The flip side of a fixed list is
that a bundle with a suffix not on it is walked into like an ordinary folder —
add it under `## Never move` in `PARA.md` if that matters for a given root.

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
