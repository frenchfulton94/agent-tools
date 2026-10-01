# Phase 9 record: adaptive layout and iPhone Duo

Evidence for `docs/specs/2026-09-30-phase9-adaptive-layout-design.md` and
`docs/plans/2026-09-30-phase9-adaptive-layout.md`. One directory per task,
each with its report. `sdd-ledger.md` holds every controller ruling and
deferred finding. `decisions.md` holds the four brainstorming decisions.

## What is not committed, and where it is

- **Raw session transcripts.** These are the eval-sweep logs (Task 6
  `baseline/`, `after-edit/`, `diagnostic/`; Task 10 `run-*/`,
  `baseline-ad-fire-5-*/`), 177 files. They live only on the recording
  machine, compressed under `raw/`, which `.gitignore` excludes:
  - `raw/task-6-evals-session-logs.tar.xz`
  - `raw/task-10-routing-session-logs.tar.xz`

  Each archive keeps the original relative paths. A citation such as
  `task-10-routing/run-1/ad-fire-5.log:27` resolves after
  `tar -xJf raw/task-10-routing-session-logs.tar.xz -C task-10-routing`.
  They are not published because one transcript (Task 10
  `run-2/ar-fire-1.log`) captured `wrangler whoami` output, with account
  names, an account ID, and a work email. The summaries that cite them are
  committed: `results.tsv`, `tally.md`, `classification.md`, and the reports.
  To regenerate, re-run the sweep with `pipeline/run_evals.py` against
  `prompts.tsv`.
- **Task briefs 0–9.** Each one is a verbatim section of the committed plan
  ("Task N"). Task 10's brief is not in the plan, so it is committed.
- **`task-8-probe/build.log` and `bundle-id.txt`.** The build's result line
  (`** BUILD SUCCEEDED **`, iPhoneSimulator 27.1 SDK) is in
  `task-8-report.md`.

## Compressed but committed

- `task-2-typecheck/catalog-logs.tar.gz` holds `catalog-before.log` and
  `catalog-after.log`, the whole-catalog compiler output. `catalog-diff.log`
  summarizes it: one FAIL→PASS flip, no PASS→FAIL.

## Byte-identical screenshots kept once

- `task-8-probe/outer-portrait.inner.png` is the inner display while closed
  (black). The same bytes were captured as `outer-portrait-overflow.inner.png`,
  `outer-portrait-r2.inner.png`, `r7-control.inner.png`,
  `r7-messagedetail.inner.png`, and `r7-priority.inner.png`.
- `task-8-probe/inner-portrait.outer.png` is the outer display while open. The
  same bytes were captured as `inner-partial.outer.png`.
