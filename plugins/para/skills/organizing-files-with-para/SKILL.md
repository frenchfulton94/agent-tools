---
name: organizing-files-with-para
description: Organizes a directory on disk into the PARA structure — Projects, Areas, Resources, Archives — by scanning it, proposing a project list the user corrects, and producing an approve-before-move plan grouped by decision. Use when the user wants to organize, sort, clean up, or tidy a folder, a Downloads or Documents directory, or a drive full of loose files; when they mention PARA, Tiago Forte, or applying a second brain to files; or when they describe the symptom without naming a method — "my Downloads folder is a disaster", "I can't find anything", "help me file all this". For a PARA tree that already exists and has drifted, prefer maintaining-para-systems.
license: MIT
---

# Organizing files with PARA

PARA sorts files by **how actionable they are**, not by subject:

| Folder | Holds | Test |
|---|---|---|
| `0-Inbox` | Undecided | Anything you could not place confidently |
| `1-Projects` | A goal with a deadline | Can you mark it done? |
| `2-Areas` | A standard with no end date | Would you be embarrassed if it slipped? |
| `3-Resources` | Topics of interest | Useful, but nobody is relying on you |
| `4-Archives` | Anything above, now inactive | No longer live |

## The run

`/para:organize <dir>` drives seven steps. Never skip step 5.

1. **Validate the root.** `scan.py` refuses `$HOME`, `/`, and anything above
   home. If the user names one, ask for a subdirectory instead.
2. **Scan.** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan.py" <dir>` emits clusters as JSON. Add
   `--metadata-only` when the user does not want anything read. `--archive-after`
   changes the age cutoff from its 12-month default; `--peek-files` and
   `--peek-bytes` bound the content peek described in `references/macos-signals.md`.
3. **Propose the project list.** From the clusters, draft `PARA.md` at the
   root, in the format `references/para-index-format.md` documents — the
   parser fails silently on an unrecognized heading, so the five heading
   names matter exactly. Propose, never assume — you are guessing at
   commitments.
4. **Have the user correct it, both ways.** They delete what is wrong *and add
   commitments the scan could not see*. A project with no files yet will never
   appear in a scan, and that is exactly the entry that matters most.
5. **Render the plan.** Write `.para/plan-<ts>.json` and `.para/plan-<ts>.md`.
   Group by decision — one block per rule, never one line per file. Building
   the JSON's `groups` from the scan's `clusters` is its own step, not a
   pass-through — see `references/plan-format.md`.
6. **Apply on approval.** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/apply.py" .para/plan-<ts>.json`.
7. **Report.** Counts moved and skipped, collisions renamed, and the undo
   command:

       python3 "${CLAUDE_PLUGIN_ROOT}/scripts/undo.py" <manifest> [--root <dir>]

   `undo.py` infers the root from the manifest's location and requires it to
   sit in `<root>/.para/`; pass `--root` explicitly otherwise.

## What you decide, and what you must not

Decide alone:
- Age-based archiving. High confidence, no list needed, usually the largest group.
- Membership in a project, area, or resource the user has already confirmed —
  but render it in the plan like everything else. The name match behind it is
  deliberately loose; see `references/plan-format.md`.

Never decide alone — these are not visible in a filesystem at any read depth.
See `references/classification-tests.md` for the questions that surface each:
- Whether something is a **Project or an Area**. Projects end; areas do not.
- Whether something is an **Area or a Resource**. Responsibility versus interest.

When a file matches two `PARA.md` entries in different sections, or matches
nothing, it goes to `0-Inbox`. That is a correct answer, not a failure — a
confident wrong move costs the user far more than an undecided file.

## Rules that are not negotiable

- **Never create an empty folder.** Only `0`–`4` are made up front. A
  subfolder appears only when files land in it.
- **Never delete.** Archiving is a move. The guard hook enforces this.
- **Never move without a manifest.** Always go through `apply.py`.
- **One named directory per run.**

## Depth

For the method beyond what this skill covers, check whether a
`forte-para-method` skill is installed on this machine and use it. Do not
assume it is there; everything above works without it.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
