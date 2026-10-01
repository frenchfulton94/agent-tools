# Task 9 report: deferred items, version bump, final gates, spec append

Status: DONE. Date: 2026-10-01. Branch: `phase9-adaptive-layout`, starting HEAD `1cb4e31`.

## Deferred items (`authoring/apple-studio/docs/deferred.md`)

- **Item 1** (kill-switch): unchanged — already carries the Phase 9 measurement
  from Task 0 (0 genuine non-fixture invocations since 2026-09-12). Cited, not
  re-edited.
- **Item 7** (snippet ship-gate triage): appended a "Phase 9 (2026-09-30)"
  paragraph. Records that the item's trigger passed unaddressed through
  Phase 8; Phase 9 triaged and fixed the two `apple-design` failures (both
  framing artifacts, each with a reference defect — deprecated `accentColor`,
  `AnyView` in a ternary; evidence `task-3-a11y/triage.md`); 17 failures
  remain, none in `apple-design`; trigger stands for the next phase.
- **Item 12** (`StudioFixture` path citation): appended a "Resolved
  2026-09-30, Phase 9 Task 8" note and marked the item **closed**. Task 8
  rewrote `headless-commands.md:6-7` to name the fixture with no
  machine-specific path.
- **Item 13** (apple-design eval misses): left as Task 6 last updated it — not
  resolved. No change needed; a fact check found nothing stale.
- **New item 14**: re-verify every iOS 27.1 claim at GA, triggered by the
  first non-beta Xcode shipping a 27.1 iPhoneOS SDK.
- **New item 15**: a camera primer for direction-aware capture, triggered by
  the first real app that captures photos or video on iPhone Duo.
- **New item 16**: App Store Connect upload support for Duo screenshots,
  triggered by Apple's screenshot-spec page dropping its "later this year"
  note.
- **New item 17**: iPhone Duo pose control is GUI-only (Task 8's discovery
  class B — `simctl`/`devicectl` can create, boot, and launch the Duo
  simulator but expose no pose or rotation command; Device Hub set every pose
  by hand). Per the controller's framing, included even though R1–R4 were all
  runtime-checked, because discovery itself was class B. Records what the
  probe did not cover: `landscapeLeft`, right-to-left layouts, and the camera
  occlusion regions. Trigger: the first `simctl`/`devicectl` release that sets
  poses from the command line.

All four new items and both updated items pass Vale (Controlled Engineering
English) on every line I added — checked by isolating the exact added line
ranges (478-486, 653-658, 731-761) after two rounds of sentence-length and
one dictionary-word ("remove" → "delete") fix.

## Version and description changes

- `plugins/apple-studio/.claude-plugin/plugin.json`: `version` 0.9.1 →
  0.10.0. `description` gained ", adaptive layout across sizes, poses, and
  foldables" after "Human Interface Guidelines conformance and
  accessibility".
- `.claude-plugin/marketplace.json:78`: same description change (marketplace
  entries carry no `version` field, confirmed, so nothing to bump there).

## Gates (full log: `task-9-release/gates.log`)

1. `typecheck_snippets.py` over `apple-design/references/*.md`, iOS 27.1
   (`DEVELOPER_DIR` = Xcode 27.1 beta) — **PASS**, `TOTAL: 8/8 snippets
   typecheck clean`.
2. `pipeline/test_docc.py` — **PASS**, `PASS test_docc.py`, exit 0.
3. `pipeline/test_typecheck_snippets.sh` (default toolchain, Xcode 27.0) —
   **PASS**, 6/6 `ok`, exit 0.
4. `pipeline/test_run_evals.sh` — **PASS**, all 4 offline cases / 12
   assertions, "all cases passed", exit 0.
5. `bun test` — **PASS**, 198 pass, 0 fail, 429 `expect()` calls.
6. `bun run audit` — **PASS**, 0 error(s), 55 warning(s), exit 0 (all
   warnings pre-existing — table-of-contents/nesting/trigger-clause
   advisories unrelated to this task's files).
7. `bun run audit --since main` — **PASS**, no unbumped-plugin warning
   emitted (apple-studio carries commits since `main` and its on-disk
   version already reads 0.10.0 ≠ the 0.9.1 recorded at `main`).
8. `claude plugin validate . --strict` — **PASS**, "Validation passed".
9. `claude --plugin-dir plugins/apple-studio -p "List the apple-design
   skill's reference files" ...` — **PASS** (non-deterministic gate, recorded
   as observed): named all 7 reference files including `adaptive-layout.md`.
10. `git -C ~/Projects/StudioFixture status --porcelain` — **PASS**, empty.
11. `xcrun simctl list devices booted` — **PASS**, no device line (only
    runtime headers).

Every line met its expectation; the SDK was present throughout (Xcode 27.1
beta, build 27A9269), so none of the "blocked on the SDK" exit-2 conditions
applied.

Re-verified `bun test` / `bun run audit` / `claude plugin validate . --strict`
a second time after the spec-prose fix round (see below); unchanged results,
appended to `gates.log`.

## Spec append — verdict per item (`docs/specs/2026-09-30-phase9-adaptive-layout-design.md`, new "## Verification results" section)

1. Kill-switch — **PASS** (0 genuine non-fixture invocations, third
   consecutive zero).
2. Charter amendment (ML stays the outstanding long-tail item) — **PASS**.
3. `adaptive-layout.md` shipped, 247 lines, 8/8 snippets clean three times
   over (Tasks 4, 7, 9), invented-symbol check fails as required — **PASS**.
   Records three corrections the phase made to its own planning, found wrong
   during implementation and fixed in Task 4: (a) right-to-left layout needs
   no manual handling for reserved regions — the SDK default mirrors frames,
   contradicting the brief's MUST; (b) floating controls align to the *same*
   edge as the vertical bar, not the opposite one (Ruling 9 withdrew the
   unsourced rule); (c) the default `reservedRegions` query omits inactive
   regions, contradicting the doc page's wording (settled at runtime by R5).
   Also records the one authorized deviation from the spec's Deliverables §4
   (UIKit preamble bindings not added; decided in planning, not a runtime
   finding).
4. Snippet ship gate, repo-wide — **PASS**, with an environment regression
   caught and fixed: catalog-wide moved 31/51 → 32/51 at Task 2 (one FAIL→PASS
   flip, Ruling 7's macOS framework-path fix); records that this also means
   the Phase-7-inherited 32/51 baseline had silently regressed to 31/51
   between phases from an environment change, not a code edit. `apple-design`'s
   own subset moved 2/4 → 4/4 at Task 3 (item 7's two triaged fixes).
5. `docc.py` offline test and `test_run_evals.sh` — **PASS**.
6. R1–R7 runtime verdicts — **PASS (R1–R4 all CONFIRMED)**, with three extra
   claims (R5–R7) the implementation needed along the way, all reported in a
   table with per-row evidence pointers. Records that R2's first walk was
   confounded and needed a re-probe, and that R7 (added in Task 8's fix
   round) caused the `MessageDetail` snippet to move Reply/Flag from
   `.secondaryAction` to `.primaryAction`. Explicitly calls out discovery
   class B (GUI-only pose control) and what the probe never covered
   (`landscapeLeft`, right-to-left, camera occlusion regions) — linked to new
   deferred item 17.
7. Trigger evals — **PARTIAL**, deliberately not rounded up to PASS. Both
   pass rates (baseline 11/16, post-edit 11/16 — not the same 11) are
   reported as the spec's letter requires, but the underlying gap (3 of 4 new
   Duo should-fire rows still fail to route; the description-edit fix was
   tried and reverted on regression) is real and unresolved, so a PASS
   verdict would have buried it. Fixture git status confirmed empty at close.
8. `bun test` / `bun run audit` / `bun run audit --since main` — **PASS**.
9. `claude plugin validate . --strict` and the plugin-load check — **PASS**.
10. No simulator left booted — **PASS**.

A "Carried forward" closing section lists items 7, 12 (closed), 13 (open),
14–17 (new), and the ML charter note, so a reader doesn't have to cross-check
`deferred.md` separately to know what's still open.

## Vale / Controlled Engineering English

Ran `vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini`
against both `docs/deferred.md` and the spec file, iterated until every line
I added was clean except the waived "amend"/"amended" CoreWords warning
(G-X1, pre-existing waiver, reused per the Phase 7 precedent).

One non-trivial finding along the way: the spec file (pre-existing line 163,
in the Deliverables section written during planning, not part of this task's
assigned edits) contained a literal ```` ```swift ```` inside a bullet instead
of plain/escaped text. This opened an unterminated Markdown code fence that
corrupted Vale's sentence segmentation for the rest of the document — every
sentence-length check from that point to the next (or, after my fix, to end
of file) was measured against a garbled, merged "sentence" rather than real
prose, which is why several of my own well-formed sentences were initially
flagged as 30-130+ words long. I reworded that one pre-existing line ("Every
Swift code block MUST typecheck...", no literal backtick-fence) since it was
actively blocking Vale from correctly checking this task's own prose, and
made sure not to reintroduce the same pattern in my own added text (§3 of the
append originally did the same thing and was also fixed). This is a one-line,
meaning-preserving prose fix to pre-existing content, not a requirements
change.

## Files changed

- `plugins/apple-studio/.claude-plugin/plugin.json` — version + description.
- `.claude-plugin/marketplace.json` — description (apple-studio entry).
- `authoring/apple-studio/docs/deferred.md` — items 7, 12 updated; items
  14–17 added.
- `authoring/apple-studio/docs/specs/2026-09-30-phase9-adaptive-layout-design.md`
  — new "## Verification results" section appended; one pre-existing line
  (163) reworded to fix the Markdown-fence/Vale defect described above.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-9-release/`
  — this report, `gates.log`, and the pre-existing `task-9-brief.md`.

## Concerns

- The Markdown-fence fix at spec line 163 touches a pre-existing line outside
  this task's literal edit list (deferred.md, plugin.json, marketplace.json,
  the spec's own append). I judged it in scope because (a) it is a one-line,
  non-substantive prose fix with no meaning change, (b) it was actively
  preventing Vale from correctly checking this task's own required prose
  check, and (c) leaving a stray unterminated code fence in a shipped spec
  document is itself a latent Markdown-rendering defect independent of this
  task. Flagging for the controller in case a stricter reading of "append
  only" was intended.
- Deferred item 13 was left exactly as Task 6 last wrote it — I verified the
  facts there are still accurate against `task-6-evals/classification.md` and
  made no edit, per the brief's "leave it unless a fact there is now wrong".
- No blocking concerns. All 11 gates pass; the SDK was present throughout, so
  the exit-2 "blocked on SDK" condition never applied.
