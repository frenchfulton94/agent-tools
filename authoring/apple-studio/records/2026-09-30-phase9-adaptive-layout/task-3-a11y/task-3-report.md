# Task 3 report: Triage the two `accessibility.md` failures

## Classification summary

Both failures in `plugins/apple-studio/skills/apple-design/references/accessibility.md` were classified as **framing artifact + reference defect**, matching the brief's expected classification exactly. Full detail in `triage.md`:

- **#1** (`Slider(value: $guess.red)`, lines 29-37): framing — `$guess` undeclared, top-level expressions with no enclosing type, fails identically across all five harness wrapping modes. Reference defect — `.accentColor(_:)` deprecated iOS/macOS/etc. 27.2 in favor of `.tint(_:)`, confirmed live in `task-1-docc/live-check.log` line 8.
- **#2** (`@Environment(\.accessibilityReduceMotion) ...`, lines 63-69): framing — property wrapper at top level (rejected outright by Swift), `staticGlyph`/`animatedGlyph` never defined. Reference defect — `AnyView` ternary erases view identity across the branches; `if`/`else` in a `@ViewBuilder` body is the idiomatic SwiftUI form.

## Before/after typecheck TOTAL

- Before (baseline, `survey/typecheck-apple-design-baseline.log`): `TOTAL: 2/4 snippets typecheck clean`
- After (`typecheck.log`, this run): `TOTAL: 4/4 snippets typecheck clean`

## Gate results

- `python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md` — 4/4 clean (log saved to `task-3-a11y/typecheck.log`).
- `bun test` — 198 pass, 0 fail, 429 expect() calls. 54 pre-existing advisory warnings (unrelated to this change — line-count/TOC/nesting warnings across many other apple-studio reference files, present before this task).
- `bun run audit` — 0 error(s), 54 warning(s) (same pre-existing warnings as above; exits 0 since it only fails on errors).
- `claude plugin validate . --strict` — Validation passed (exit 0).

No `test:engine` run — this task doesn't touch `plugins/godot/`.

## Files changed

- `plugins/apple-studio/skills/apple-design/references/accessibility.md` — replaced blocks #1 (lines 29-37→29-45) and #2 (lines 63-69→71-83), updated the `verified:` header line to append `re-checked 2026-09 (Phase 9: snippets reframed, accentColor → tint)`. No other prose changed (brief confirmed neither adjacent sentence names a changed API).
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md` — created.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/typecheck.log` — created (Step 5 gate output).
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/task-3-report.md` — this file.

## Self-review findings

- Verified the exact replacement code from the brief (Steps 2-3) was used verbatim — diff matches the brief's fenced blocks exactly, no incidental changes.
- Confirmed `typecheck_snippets.py` was invoked with no per-file iOS directive for `accessibility.md`, per the brief's Task 2 interface note (macOS default is correct; the snippets are cross-platform SwiftUI with no iOS-only symbol).
- Confirmed the `accentColor` deprecation claim against `task-1-docc/live-check.log` line 8 rather than trusting the brief's assertion blindly — matches.
- Confirmed scope discipline: `git diff` on `accessibility.md` touches only the two code blocks and the `verified:` line; no other reference file in `apple-design` was touched by this task (the 2/4→4/4 delta is fully attributable to these two edits).
- Re-read the sentences immediately before both blocks after the swap: neither names an API that changed, both still read correctly with the new snippets in place.

## Concerns

None. All three required gates pass; typecheck gate hits the brief's expected 4/4; classification and fixes match the brief verbatim.
