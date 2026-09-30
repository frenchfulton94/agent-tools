# Task 6 report: fixture screen, eval baseline, conditional description edit

## Fixture

`~/Projects/StudioFixture/StudioFixture/MailboxScreen.swift` added verbatim
from the brief (mailbox with `NavigationSplitView`, `TabView`, per-context
toolbars). `ContentView.swift` now returns `MailboxScreen()`. Folder-sync
groups confirmed (`PBXFileSystemSynchronizedRootGroup` present) — no
project-file edit was needed.

**Fixture commit:** `5287d2c` — "Add a mailbox screen with toolbars, tabs,
and a split view for apple-design evals". `git -C ~/Projects/StudioFixture
status --porcelain` is empty both after that commit and at the close of this
task (re-checked after both sweeps, which each wrote to and had their writes
restored from the fixture — see below).

Toolchain: Xcode 27.0 (Build 27A266a), matching `xcode-select -p`. Both
builds specified by the brief (Steps 2–3) succeeded:

```
=== iOS build (generic/platform=iOS Simulator) ===
note: Disabling hardened runtime with ad-hoc codesigning.
** BUILD SUCCEEDED **

=== macOS build (platform=macOS) ===
** BUILD SUCCEEDED **
```

Full tails in `fixture-build.log`. The brief's prose also names visionOS as
a target platform for the screen's APIs, but Steps 2–3 specify only iOS and
macOS build commands; no visionOS build was run, matching the steps as
written.

## Eval rows

`plugins/apple-studio/skills/apple-design/evals/triggers.md` gained 4
should-fire rows (`fire-7`..`fire-10`) and 2 should-NOT-fire rows
(`nofire-5`, `nofire-6` in `prompts.tsv` numbering), verbatim from the
brief. `task-6-evals/prompts.tsv` holds all 16 rows in file order.

## Baseline sweep (description unedited)

`baseline/results.tsv`: **11/16 PASS.**

- Should-fire: **6/10** — `fire-1` through `fire-6` pass; `fire-7` through
  `fire-10` (all four Duo rows) fail.
- Should-NOT: **5/6** — `nofire-1` ("Design our brand color palette") fails;
  the rest pass.

## Failure classification (full evidence and transcript quotes in
`classification.md`)

| row | classification | evidence |
|---|---|---|
| `fire-7` | **Duo routing miss** | Session searches `simctl`/codebase for "Duo," finds nothing, answers from priors that iPhone Duo doesn't exist. No `Skill` call. |
| `fire-8` | **Duo routing miss** | Session reads the toolbar code, then explicitly invokes `Skill apple-studio:xcode-loop` (wrong skill) to try to reproduce the bug empirically; runs out of turns pursuing that plan. |
| `fire-9` | **Prompt-wording defect, not a routing miss** | The model reads "[X] gets cut off" as a claim its own message was truncated, and never engages the task. Reproduced 3x, including twice from a neutral directory with no fixture in play. Bisected: swapping "fold"→"crease" does not fix it; the trigger is "cut off," not "fold." Excluded from the Step 8 Duo-routing-miss count. |
| `fire-10` | **Duo routing miss** | Session asks whether "arrangement view" means a DAW-style view, calling it "not a term from SwiftUI or the HIG" — false: `ArrangementView` is documented in this skill's own `references/adaptive-layout.md:81-102` for iPhone Duo poses, which routing never reached. |
| `nofire-1` | **Routing miss, pre-existing, non-Duo** | Reproduces the Phase 8 `deferred.md` item 13 finding verbatim: `apple-design` fires on pure brand-color work, which its own description already disclaims. Unrelated to this task's edit either way. |

Net: 3 of 4 Duo should-fire rows (`fire-7`, `fire-8`, `fire-10`) are genuine
routing misses, satisfying Step 8's edit trigger.

## Description edit: made, then reverted (regression)

Step 8's exact description text was applied to `SKILL.md:3`. The post-edit
sweep (`after-edit/results.tsv`) also scored **11/16**, but not the same 11:

- **Fixed:** `fire-7` and `fire-8` now pass (`apple-design` fires first for
  both).
- **Unchanged:** `fire-9` (prompt defect), `fire-10` (the "arrangement view"
  term itself was never added to the description), `nofire-1` (unrelated
  bug) all still fail.
- **New regressions (previously-passing rows now fail):**
  - `nofire-6` ("What screenshot sizes does the App Store need for iPhone
    Duo?") — now calls `apple-design` first (pulled in by the added "iPhone
    Duo" wording), self-correcting to `app-release` only afterward. Verdict
    scores on the first skill invoked, so this is a FAIL. Directly
    traceable to the edit.
  - `fire-5` ("Add a confirmation flow before deleting") — stops invoking
    any `Skill` at all and implements the change directly via `Bash`/`Edit`.
    No wording overlap with the edit; most likely routing variance
    (`--allowedTools` leak, `deferred.md` item 6) rather than the edit
    itself, but recorded as a regression per the brief's mechanical rule
    regardless of suspected cause.

Per Step 9's rule ("a row that passed in the baseline and fails after the
edit is a regression: revert the edit and record why"), **the description
edit is reverted.** `git diff plugins/apple-studio/skills/apple-design/SKILL.md`
is empty — the file is byte-identical to before Step 8. `fire-7`/`fire-8`'s
fix does not ship this phase.

## Deferred item 13

Appended a "Phase 9 (2026-09-30)" paragraph to `docs/deferred.md` item 13
(lines 669–714) recording: the fixture's new screen and commit hash,
baseline/post-edit pass rates by direction, the classification summary
above, and the revert. **Item 13 is recorded as not resolved** — open
should-fire rows `fire-7`, `fire-8`, `fire-10` (Duo routing misses) and open
should-NOT row `nofire-1` (brand-color, pre-existing). A new trigger is
recorded for the next attempt: a fix that catches the three open Duo rows
without pulling `apple-design` ahead of `app-release` on release-logistics
questions that merely mention iPhone Duo.

Checked against Controlled Engineering English: `vale --config
.claude/skills/controlled-engineering-english/scripts/vale/.vale.ini
authoring/apple-studio/docs/deferred.md` reports 90 warnings total, none on
the lines added by this task (confirmed by filtering to lines 669–715).
Two "use 'try'/'change' instead of 'attempt'" warnings on my first draft
were fixed before the final version (`edit attempt` → `edit`; `Trigger for
the next attempt` → `Trigger for the next try`). Sentence lengths in the
added paragraph were kept under 25 words throughout.

## Gates

- `bun test`: **198 pass, 0 fail** (429 expect() calls, 9 files).
- `bun run audit`: **0 error(s), 55 warning(s)** — exit 0, all pre-existing
  warnings unrelated to this task's changes.
- `claude plugin validate . --strict`: **Validation passed.**

## Fixture status at close

`git -C ~/Projects/StudioFixture status --porcelain` is empty. Both sweeps
wrote to `StudioFixture/MailboxScreen.swift` (baseline: `fire-5`, 1 write;
after-edit: `fire-5`, `fire-7`, `fire-8`, 3 writes) — in every case
`run_evals.py`'s guard detected, attributed, and restored the write, and the
final porcelain check after each sweep and again now is empty.

## Files changed (this repo)

- `plugins/apple-studio/skills/apple-design/evals/triggers.md` — 6 new eval
  rows (Step 5).
- `plugins/apple-studio/skills/apple-design/SKILL.md` — edited (Step 8),
  then reverted (Step 9); no net diff.
- `authoring/apple-studio/docs/deferred.md` — item 13 updated (Step 10).
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-6-evals/` —
  brief, `prompts.tsv`, `fixture-build.log`, `baseline/` (17 files: 16 logs
  + `results.tsv`, ~1.1 MB), `after-edit/` (17 files, ~1.3 MB), `diagnostic/`
  (a 4-row re-run used to confirm `fire-7`/`fire-8`/`fire-9`/`fire-10`
  reproduce before writing the classification, ~188 KB — not named in the
  brief's file list but kept as cited evidence), `classification.md`, this
  report. Session logs are kept in full per the brief ("keep them — they
  are the evidence") despite their size.

## Files changed (fixture repo, separate)

- `StudioFixture/MailboxScreen.swift` (new), `StudioFixture/ContentView.swift`
  (modified) — committed at `5287d2c`.

## Concerns

- **Item 13 is still open.** The Duo routing gap this task set out to
  measure is confirmed real (3 of 4 Duo rows), but the one fix attempted —
  broadening the description — traded two fixes for two regressions and was
  reverted. Whatever fixes `fire-7`/`fire-8`/`fire-10` next needs to avoid
  pulling `apple-design` ahead of `app-release` on Duo-adjacent
  release-logistics questions, which a plain keyword-style broadening
  (adding "iPhone Duo" to the description) does not do safely.
- **`fire-5`'s regression is unexplained.** It shares no wording with the
  edit, so its cause is most likely `--allowedTools` routing variance
  (`deferred.md` item 6) rather than anything Step 8 changed, but a single
  sample cannot rule out an edit-driven effect. Recorded honestly as
  unexplained rather than asserted either way.
- **`fire-9`'s prompt is a defect in this task's own added corpus.** "Content
  gets cut off at the fold" is self-referentially ambiguous to the model
  ("cut off" reads as a claim about the message itself) and should probably
  be reworded in a future phase — not done here, since the brief specifies
  the prompt text verbatim and rewording it was out of this task's scope.
- Session log volume: `baseline/` and `after-edit/` are ~1.1–1.3 MB each
  (32 transcripts total plus a 4-row diagnostic set). Kept per the brief's
  instruction to preserve evidence.
