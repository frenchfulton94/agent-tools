# A PARA file-organizing plugin

Date: 2026-09-15
Status: approved design, awaiting implementation plan

## 1. Goal

A new `para` plugin that organizes a directory on disk into Tiago Forte's PARA
structure — Projects, Areas, Resources, Archives — through an
approve-before-move workflow. The agent proposes a classification plan grouped
by decision, the user approves it, and tested scripts execute the moves and
record an undo trail.

The plugin implements the method. It does not redistribute the book.

The design targets macOS, which is where the user runs it and where the
richest classification signals live. Nothing in the architecture is
macOS-only; the signal layer degrades to portable metadata elsewhere.

## 2. Decision log

Each row records a decision made during design. A later change to one of these
reopens the design; it is not an implementation detail.

| # | Decision |
|---|---|
| 1 | Approve before move. The agent proposes, the user approves, scripts execute. |
| 2 | The plan is grouped by decision, not by file, so review cost scales with decisions (dozens) rather than files (thousands). This is what keeps the approval gate real rather than performative. |
| 3 | An undo manifest is written on execute regardless of the approval gate. The gate and the backstop are additive, not alternatives. |
| 4 | One named directory per run. `$HOME` is refused. |
| 5 | Only the `0`–`4` top-level folders are created up front. No subfolder is created without files landing in it — Forte's Never-Empty-Folder Rule. |
| 6 | The project list is proposed by the agent from a scan, then corrected by the user in **both** directions: delete proposed entries and add commitments the scan could not see. The two-way edit is what neutralises the anchoring bias of inference. |
| 7 | Each project-list entry carries a P/A/R classification set by the user. That judgement is not recoverable from the filesystem at any read depth. |
| 8 | The project list persists as a plain Markdown file in the organized root, owned and hand-editable by the user. Not hidden plugin state. |
| 9 | Classification is tiered: portable metadata and macOS Spotlight/xattr signals first, then a content peek for the unresolved remainder only. |
| 10 | The peek reads a bounded prefix only — first page or first few KB — under a stated budget (section 6.1), with a never-read denylist and a metadata-only escape flag. Every file opened is named in the plan. |
| 11 | Age decisions prefer `kMDItemLastUsedDate` and fall back to mtime, because mtime churns on sync, copy, and restore. |
| 12 | No book content ships. Skill prose is original, Forte is attributed, and the plugin defers to a locally installed `forte-para-method` skill for depth when one is present. |
| 13 | Shape C: two skills, three scripts with tests, one command, one guard hook. No subagent — deferred until a measured context problem justifies it. |

## 3. What ships

    plugins/para/
      .claude-plugin/plugin.json
      README.md
      commands/organize.md
      hooks/hooks.json
      scripts/
        scan.py
        apply.py
        undo.py
        guard_para_moves.py
        test/
          test_scan.py
          test_apply.py
          test_undo.py
          test_guard.py
      skills/
        organizing-files-with-para/
          SKILL.md
          references/
            classification-tests.md
            macos-signals.md
            plan-format.md
          evals/triggers.md
        maintaining-para-systems/
          SKILL.md
          references/
            upkeep.md
            starting-over.md
          evals/triggers.md

Names. The plugin `name` is `para`, `displayName` is `PARA`. Skill names are
`organizing-files-with-para` and `maintaining-para-systems`. The command is
`/para:organize`. `name` is install-breaking, so it is fixed here rather than
revisited. Nothing in the install surface carries the author's name, per
decision 12.

Version starts at `0.1.0` in `plugins/para/.claude-plugin/plugin.json`, and
the marketplace entry carries no version field.

## 4. The run

`/para:organize <dir>` drives seven steps. Steps 1 and 2 are read-only. Step 6
is the only one that moves anything.

1. **Validate the root.** Refuse `$HOME`, `/`, and any path above the user's
   home. Resolve symlinks. Record the volume.
2. **Scan.** `scan.py` walks the root and emits aggregated clusters
   (section 5.4). Tier one reads metadata and macOS signals; tier two peeks
   inside the unresolved remainder under budget.
3. **Propose the project list.** The agent reads the clusters and drafts
   candidate Projects, Areas, and Resources into `PARA.md`.
4. **User corrects the list.** Two-way edit: delete what is wrong, add
   commitments the scan could not see, set each entry's P/A/R classification.
   On a re-run an existing `PARA.md` is loaded instead of drafted, and the
   agent proposes only additions.
5. **Plan.** The agent classifies clusters against the corrected list and
   writes `plan.json` plus a rendered `plan.md`, grouped by decision.
6. **Approve and apply.** The user approves `plan.md`. `apply.py` creates the
   `0`–`4` skeleton, creates only those subfolders that receive files, moves
   the files, and writes the undo manifest as it goes.
7. **Report.** Counts moved, counts skipped, collisions renamed, path to the
   manifest, and the exact `undo.py` command to reverse the run.

A re-run over an already-organized root skips step 3 and treats `0-Inbox` as
its primary work surface — which is the maintenance path, and the boundary
between the two skills.

## 5. Artifacts

### 5.1 `PARA.md` — the project list

Lives at the organized root. The user's file: hand-editable, diffable, and the
single place policy is expressed. It is also, by construction, the ch11
artifact the method asks you to build.

    # PARA index

    Root: /Users/me/Documents
    Updated: 2026-09-15

    ## Projects
    - client-redesign — ship the new marketing site — due 2026-10-15
    - taxes-2025 — file the 2025 return — due 2027-04-15

    ## Areas
    - home-maintenance — house stays in working order
    - finances — accounts reconciled monthly

    ## Resources
    - photography
    - swipe-file

    ## Never read
    - ~/.ssh
    - **/*.kdbx
    - **/.env*

    ## Never move
    - **/*.app
    - **/node_modules

Parsing is deliberately forgiving: a heading plus a dash list. Text after the
first em-dash is a description and is never parsed for meaning. An entry's
section **is** its P/A/R classification, which is why the user edits sections
rather than a separate field.

### 5.2 `plan.json` — machine-readable plan

Written to `.para/plan-<ts>.json` under the root. The rendered review copy
(section 5.3) is written beside it as `.para/plan-<ts>.md`, sharing the same
timestamp so the pair is unambiguous.

    {
      "version": 1,
      "root": "/Users/me/Documents",
      "volume": "/",
      "generated": "2026-09-15T18:00:00Z",
      "metadata_only": false,
      "peeked": ["Scan 2024-03-11.pdf", "Document (3).pdf"],
      "groups": [
        {
          "id": "g1",
          "rule": "last used before 2025-03-15",
          "reason": "412 files untouched for 18 months",
          "destination": "4-Archives/2024",
          "count": 412,
          "samples": ["a.pdf", "b.docx", "c.png"],
          "files": ["rel/path/a.pdf", "rel/path/b.docx"]
        }
      ]
    }

All paths are relative to `root`. `samples` drives the rendered review;
`files` drives execution.

### 5.3 `plan.md` — what the user actually reads

One block per group. `files` is never rendered in full — that is the whole
point of decision 2.

    ## g1 — 412 files → 4-Archives/2024
    Rule: last used before 2025-03-15
    Why: untouched for 18 months
    Examples: a.pdf, b.docx, c.png

    ## g2 — 18 files → 1-Projects/client-redesign
    Rule: filename or download source mentions "client-redesign"
    Why: matches an open project in PARA.md (due 2026-10-15)
    Examples: brief-v3.docx, homepage-mock.png, contract.pdf

A closing section lists every file opened during tier two, so the privacy cost
of the peek is visible rather than implicit.

### 5.4 Scan output — aggregated clusters

`scan.py` emits clusters, not rows. Cluster kinds, in the order they are
applied:

- `project-match` — filename, path segment, Finder tag, or download host
  matches a `PARA.md` Projects entry.
- `area-match` / `resource-match` — the same against those sections.
- `age` — last-used (or mtime) older than a threshold.
- `tag` — a Finder tag with no `PARA.md` counterpart.
- `provenance` — a shared `kMDItemWhereFroms` host.
- `kind` — extension or content-type family.
- `unresolved` — matched nothing. This is the tier-two peek candidate set.

Each cluster carries `count`, `samples`, and the full member list. Emitting
counts and samples rather than rows is what keeps the inventory
decisions-sized in context, and is the reason no classifier subagent is needed
(decision 13).

### 5.5 Undo manifest

`.para/undo-<ts>.jsonl`, one JSON object per line, appended **before** each
move so an interrupted run still has a complete trail for what it did.

    {"from":"rel/old/a.pdf","to":"4-Archives/2024/a.pdf","size":81232,"mtime_ns":1726419600000000000,"inode":12345678}

`size`, `mtime_ns`, and `inode` are the change detector. `undo.py` refuses to
move a file back when any of the three has changed, reports it as skipped, and
continues with the rest. A full content hash is deliberately not taken: it is
expensive on large files and adds nothing over the triple for detecting
post-move edits.

## 6. Classification rules

The method's two hard distinctions, adapted to a filesystem:

- **Project vs. Area.** A project has a completion condition and a deadline;
  an area has a standard and no end date. The filesystem cannot see either, so
  both come from `PARA.md`, which is why decision 7 puts the classification in
  the user's hands.
- **Area vs. Resource.** Responsibility versus interest. The mechanical
  tiebreaker Forte offers — areas are private by default, resources are
  shareable — is usable as a *prompt* to the user during step 4, never as an
  automatic rule.

What the agent decides on its own, without asking:

- Age-based archiving. High confidence, needs no list, and is the largest
  single group in a typical run.
- Membership in an already-confirmed project, area, or resource, when name,
  tag, or provenance matches.

What always goes to `0-Inbox` rather than being guessed:

- Anything in the `unresolved` cluster after tier two.
- Anything matching two or more `PARA.md` entries in different sections.

Forte's rule that placement is low-stakes applies here: `0-Inbox` is a correct
answer, not a failure. The design prefers it over a confident wrong move.

### 6.1 Tunable defaults

Four numbers decide most of a run's behaviour. Each has a default, each is
overridable by a command flag, and each appears in `plan.json` so a plan always
records the settings that produced it.

| Tunable | Default | Flag |
|---|---|---|
| Age threshold for archiving | 12 months since last use | `--archive-after <months>` |
| Peek budget, files | 200 files per run | `--peek-files <n>` |
| Peek budget, bytes per file | 8 KB, or the first page of a PDF | `--peek-bytes <n>` |
| Tier two entirely off | off (peeking enabled) | `--metadata-only` |

`--metadata-only` sets `metadata_only: true` in `plan.json` and skips tier two
wholesale, for a directory the agent should never read inside.

**Archive destination.** Age-clustered files land in `4-Archives/<year>`, where
`<year>` is the year of last use — the same date the age decision was made on,
so the grouping is explainable from the rule that produced it. Files archived
for any other reason land directly in `4-Archives`. No other subfoldering is
invented, per decision 5.

## 7. macOS signals

Read by `scan.py` via `mdls` and `xattr`, all best-effort:

| Signal | Use |
|---|---|
| `kMDItemLastUsedDate` | age decisions, preferred over mtime (decision 11) |
| `kMDItemUserTags` | Finder tags — user judgement already recorded |
| `kMDItemWhereFroms` | download provenance; the host often names the project |
| `kMDItemFinderComment` | rare, free when present |
| `kMDItemContentTypeTree` | package detection (section 8) |

Every one of these can be absent: Spotlight indexing is off on some volumes,
and external and network volumes are frequently unindexed. Each falls back to
portable metadata — mtime, extension, path — and the scan reports how many
files came back unindexed so a degraded run is visible rather than silent.

## 8. Safety model

**Never move.** These are recorded as skipped with a reason, never relocated:

- macOS packages and bundles — `.app`, `.rtfd`, `.photoslibrary`, and anything
  whose `kMDItemContentTypeTree` contains `com.apple.package`. A package is
  one item, never a directory to descend into.
- Version-control working trees. The repository root may be classified; its
  contents are never walked or moved individually.
- `node_modules`, `.venv`, and similar dependency trees — one item, by their
  parent.
- Anything matching `## Never move` in `PARA.md`.

**Never read.** Enforced regardless of peek budget, and independent of the
never-move list: `.ssh`, `.gnupg`, keychains, `*.pem`, `*.key`, `*.kdbx`,
`.env*`, plus everything under `## Never read`.

**Same volume only.** Destinations must sit on the root's volume. A
cross-volume `mv` is a copy-then-delete with different failure and undo
semantics, so the plan rejects it rather than handling it.

**Symlinks** are moved as links and never followed. **Hardlinks** are
preserved. **Case-insensitive collisions** are detected explicitly, since APFS
defaults to case-insensitive and `a.pdf`/`A.pdf` will collide on arrival.

**Collisions.** `apply.py` appends ` (2)`, ` (3)`, … and records the actual
destination in the manifest, so undo reverses what happened rather than what
was planned.

**The guard hook.** `PreToolUse` on `Bash`, exit code 2 to block with a reason
on stderr. It blocks `rm` targeting anything under a registered PARA root, and
blocks `mv` under a registered root that does not go through `apply.py`.

Registered roots live in a plain newline-delimited file at
`~/.config/para/roots`, written by `apply.py` on first successful run. When
the file is absent the hook is a no-op.

That is a deliberate trade and worth stating plainly: a registry-scoped hook
fails open outside registered roots. The alternative — a hook that inspects
every `rm` anywhere — fires on ordinary work, and a hook that annoys gets
disabled, which fails open permanently and everywhere. Narrow and durable
beats broad and switched off.

The hook is what makes the rest of this section binding rather than
aspirational. Every other safety property here lives in prose an agent is
asked to follow; this one is enforced by the harness.

## 9. Error handling

- **Scan.** Unreadable directories and files are counted and reported, never
  fatal. A permissions-heavy root yields a partial scan with an explicit count
  of what could not be read.
- **Plan.** Validation before any execution: every source exists, every
  destination is writable, every destination is on the root's volume, no two
  groups claim the same file. A plan failing validation is rejected whole —
  there is no partial apply of an invalid plan.
- **Apply.** Manifest lines are written before their move. On a mid-run
  failure, `apply.py` stops, leaves the manifest complete for everything
  already done, and prints the undo command. It does not attempt self-repair,
  because a half-reversed run is worse than a stopped one.
- **Undo.** Per-file refusal on a changed size, mtime, or inode; the file is
  reported as skipped and the rest proceed. Undo is idempotent: re-running a
  manifest already reversed is a no-op, not an error.

## 10. Testing

Python tests under `plugins/para/scripts/test/`, run with `pytest` against
temporary directories — mirroring `unraid-ops`, which is the existing
precedent for tested plugin scripts in this repo.

Coverage that matters:

- `scan.py` — package directories treated as single items; denylist honoured
  regardless of budget; peek budget enforced; unindexed fallback to mtime;
  unreadable paths counted rather than fatal.
- `apply.py` — collision renaming recorded accurately; manifest written before
  the move; cross-volume destination rejected; skeleton created but empty
  subfolders never created.
- `undo.py` — refuses changed files, skips and continues, idempotent on
  re-run.
- `guard_para_moves.py` — blocks `rm` under a registered root, blocks
  bypassing `mv`, no-ops with no registry, and does not fire outside
  registered roots.

Repo-level `bun test` already covers registration in both directions, `name`
against directory, description match, skill-name uniqueness, and the README
row. Those need no new cases.

One piece of new repo tooling: a `bun test` case that shells out to `pytest`
when `python3` is available and skips otherwise. `unraid-ops` leaves its
Python tests unwired and manual; for a plugin whose scripts move the user's
files, the safety-critical code should be gated rather than trusted. The skip
path keeps the suite green where Python is absent.

`bun run audit` must pass, including the README skills column.

## 11. Attribution

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. The plugin README and both SKILL.md files state
this, link to the book, and state that the plugin is an independent
implementation, not affiliated with or endorsed by the author.

No book text ships: no chapter summaries, no glossary of the book's terms, no
extended quotes. All skill prose is written fresh for the filesystem task,
which is a different document from a chapter summary in any case.

When a `forte-para-method` skill is present on the machine, the skills point
to it for depth. They degrade cleanly when it is absent — the file-organizing
capability never depends on it.

This is a narrower posture than `plugins/security/.../owasp/`, and
deliberately so: that corpus is CC-BY-SA and redistributable, and this book is
neither.

## 12. Non-goals

- No task-manager integration. Importing a project list from Things,
  OmniFocus, or Notion to seed candidates is a later enhancement, explicitly
  not in this version.
- No cross-platform mirroring of the PARA structure into note apps or cloud
  drives.
- No file deduplication, no content rewriting, no renaming of files. The
  plugin moves files and creates folders; it does not edit anything.
- No deletion, ever. Archiving is a move. `4-Archives` is the terminal state,
  and the guard hook enforces that `rm` is not part of this plugin's
  vocabulary.
- No scheduled or background runs. Every run is user-initiated against a named
  directory.
