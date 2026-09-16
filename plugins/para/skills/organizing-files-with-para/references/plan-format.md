# Plan format

Two files, same timestamp: `.para/plan-<ts>.json` drives execution,
`.para/plan-<ts>.md` is what the user reads.

## The rule that makes the gate real

Group by **decision**, never by file. A 4,000-item directory must produce a
plan with dozens of blocks, not 4,000 lines. A plan nobody reads is a
rubber stamp, and a rubber stamp is not an approval.

Never render the full `files` array. Render `count` and up to five `samples`.

Matching against `PARA.md` is deliberately loose: it is a "mentions" match, so
a project named "taxes" matches any path whose tokens include "taxes" —
`taxes-are-fun.pdf` included. That looseness is only acceptable because
nothing moves until a human reads the plan it produced. Render what the match
actually found, wrong hits and all, in the `samples` for that group — do not
quietly tighten or second-guess the match yourself. The approval step is what
catches a bad match; a plan that hides it defeats the reason the match is
allowed to be loose in the first place.

## From scan clusters to plan groups

`scan.py` emits **clusters**, each keyed by `kind` (`age`, `project-match`,
`area-match`, `resource-match`, `unresolved`) — that is the vocabulary of a
scan, not of a plan. Building the plan's `groups` from a scan's `clusters` is
its own step, not a pass-through:

For each cluster you decide to keep, assign a sequential `id` (`g1`, `g2`, …)
in the order the groups appear in the plan, and carry the cluster's `rule`,
`reason`, `destination`, `count`, `samples`, and `files` through **unchanged**.
Drop `kind` — it names how the scan found the group, not what the plan does
with it, and nothing downstream reads it. `id` is what the rest of the run
addresses a group by: it is what `apply.py` names in a duplicate-claim error,
what the Markdown plan's headings key on, and what the final report can point
back to.

## JSON

    {
      "version": 1,
      "root": "/Users/me/Documents",
      "volume": 16777220,
      "generated": "2026-09-15T18:00:00+00:00",
      "metadata_only": false,
      "peeked": ["Scan 2024-03-11.pdf"],
      "groups": [
        {
          "id": "g1",
          "rule": "last used before 12 months ago",
          "reason": "412 files last used in 2024",
          "destination": "4-Archives/2024",
          "count": 412,
          "samples": ["a.pdf", "b.docx"],
          "files": ["a.pdf", "b.docx"]
        }
      ]
    }

All paths are relative to `root`.

## Markdown

    ## g1 — 412 files → 4-Archives/2024
    Rule: last used before 12 months ago
    Why: 412 files last used in 2024
    Examples: a.pdf, b.docx, c.png

Close with a section naming every file opened during the peek (`peeked`), so
the privacy cost is visible rather than implicit. A never-read denylist —
SSH keys, `.env` files, credentials — is enforced before `--peek-files` or
`--peek-bytes` is even consulted, and a symlink is never opened during a peek
regardless of budget; `peeked` is still the complete, honest list of what was
actually read, and it belongs in the plan even when it is short. If
`metadata_only` is true, say so explicitly instead of leaving `peeked` empty
and unexplained.
