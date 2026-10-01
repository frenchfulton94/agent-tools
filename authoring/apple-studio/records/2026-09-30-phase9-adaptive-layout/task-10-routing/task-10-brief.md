### Task 10: Duo routing fix (deferred item 13) — controller-written brief

User-approved design, 2026-10-01 (option A). Not in the original plan; added at the user's request after Task 9.

**Goal:** iPhone Duo prompts reach `apple-design`; App Store screenshot questions stay with `app-release`. Decide with three runs per eval row, not one.

**Files:**
- Modify: `plugins/apple-studio/skills/apple-design/SKILL.md:3` (description)
- Modify: `plugins/apple-studio/skills/app-release/SKILL.md:3` (description)
- Modify: `plugins/apple-studio/skills/apple-design/evals/triggers.md` (reword one row)
- Modify: `plugins/apple-studio/skills/app-release/evals/triggers.md` (add one row)
- Modify: `authoring/apple-studio/docs/deferred.md` (item 13)
- Modify: `authoring/apple-studio/docs/specs/2026-09-30-phase9-adaptive-layout-design.md` (addendum after the Task 9 verification results)
- Create: `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-10-routing/` — `prompts.tsv`, `run-1/`, `run-2/`, `run-3/`, `tally.py`, `tally.md`, report; `baseline-*/` only if Step 6 needs it.

`$R` below = `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout`.

- [ ] **Step 1: Edit the `apple-design` description** (line 3) to exactly:

```
description: Apple Human Interface Guidelines conformance for iOS/iPadOS/macOS apps - layout and adaptive layout across sizes, poses, and foldables such as iPhone Duo (reserved regions like the fold, arrangement views, toolbars that move to a vertical edge), typography and Dynamic Type, color and materials, navigation and modality patterns, platform idioms, accessibility, and animation judgment. Use when designing or building UI, adapting a screen to a new size, pose, or fold, choosing a navigation or presentation pattern, styling views, making an app feel native, or fixing accessibility, Dynamic Type, or contrast issues. Not for brand identity, custom visual styling, or App Store screenshots.
```

- [ ] **Step 2: Edit the `app-release` description** (line 3) to exactly:

```
description: Shipping iOS/macOS apps - code signing and provisioning, certificates and App Store Connect API keys, TestFlight beta distribution, App Store submission and rejection avoidance, App Store screenshots and metadata for every device size, privacy manifests and export compliance, version and build numbering, push notification (APNs) setup and delivery debugging, and CI release automation with Xcode Cloud. Use when archiving or distributing a build, fixing signing or provisioning errors, setting up TestFlight, preparing screenshots or metadata for App Store Connect, preparing for or responding to App Review, configuring push infrastructure, or automating releases. Not for in-app feature work, UI, or local-notification API usage.
```

- [ ] **Step 3: Eval rows.**
  - `apple-design/evals/triggers.md`: replace the row `- "Content gets cut off at the fold"` with `- "Part of my list is hidden where the screen folds"`. (Task 6 classified the old wording as a prompt defect: the model read it as its own message being truncated.)
  - `app-release/evals/triggers.md`: append under `## Should fire`: `- "What screenshot sizes does the App Store need for iPhone Duo?"`

- [ ] **Step 4: Sweep file.** Write `$R/task-10-routing/prompts.tsv` with every row of both triggers.md files, tab-separated `id<TAB>skill<TAB>FIRE|NOFIRE<TAB>prompt`, prompts copied exactly without quotes or trailing parentheticals. IDs: `ad-fire-1`…`ad-fire-10`, `ad-nofire-1`…`ad-nofire-6` for apple-design (file order; `ad-fire-9` is the reworded row); `ar-fire-1`…`ar-fire-8`, `ar-nofire-1`…`ar-nofire-4` for app-release (file order; `ar-fire-8` is the new row). 28 rows.

- [ ] **Step 5: Three sweeps.** Run `python3 authoring/apple-studio/pipeline/run_evals.py $R/task-10-routing/prompts.tsv $R/task-10-routing/run-N` for N = 1, 2, 3, one after another. Run them in the background and wait. Each takes about 25 minutes. Then write `tally.py` (Python 3 stdlib) that reads the three `results.tsv` files and prints, per row id: expectation, PASS count out of 3, the `fired` value of each run, and any `max_turns` notes. Save its output to `tally.md`.

- [ ] **Step 6: Decide by the rule, not by intuition.**
  - A row **holds** if it passes in at least 2 of 3 runs.
  - **Duo FIRE rows:** `ad-fire-7`, `ad-fire-8`, `ad-fire-9`, `ad-fire-10`. Task 6's baseline passed 0 of them.
  - **Candidate regressions:** every row that does not hold, except `ad-nofire-1` (the pre-existing brand-color misroute, deferred item 13, out of scope; report its count anyway) and the four Duo FIRE rows. For each candidate, re-run its baseline three times against the descriptions before this task. Create a temporary worktree: `git worktree add <scratchpad>/baseline-9f3c3a6 9f3c3a6`. Run `run_evals.py --plugin-dir <worktree>/plugins/apple-studio --only <id>` three times, into `$R/task-10-routing/baseline-<id>-N`. Use the Task 6 baseline prompt text for `ad-fire-9`. A candidate is a **confirmed regression** if its baseline holds (at least 2 of 3) and its post-edit count does not. Remove the worktree afterwards with `git worktree remove`.
  - **Classify every non-passing session** per `.claude/rules/eval-harness.md` (max_turns, fixture-dependent, or routing miss), citing log lines, before deciding.
  - **KEEP** the edits if there is no confirmed regression and more Duo FIRE rows hold than at baseline (at least 1 of 4).
  - **One revision round is allowed:** if a confirmed regression or a Duo FIRE row still fails as a routing miss and a wording change could plausibly address it, revise either description once. Re-run only the affected rows three times into `run-rev-N`, and apply the same rule. No second revision.
  - **REVERT** both description edits if the KEEP condition fails after the revision round. Keep the eval-row changes from Step 3 either way: the fire-9 reword fixes a corpus defect, and the new app-release row documents the boundary.

- [ ] **Step 7: Records.**
  - Update deferred item 13 with a `**Phase 9 Task 10 (2026-10-01).**` paragraph. Include: the decision (KEEP/REVERT), per-row hold counts for the Duo rows and any candidates, confirmed regressions, and the rows still open. Mark the item resolved only if all four Duo FIRE rows hold and there is no confirmed regression. `ad-nofire-1` stays open regardless, under its existing wording.
  - Append to the Phase 9 spec, after the Task 9 verification results, a `### Addendum (2026-10-01, Task 10): Duo routing` subsection. Give the eval protocol, the result, and `<file>:<line-range>` pointers into `tally.md`. It supersedes the PARTIAL eval verdict only to the extent the evidence supports.
  - Prose: Controlled Engineering English, spec register. Check with `vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini <file>`. The "amend" warning is waived. Judge only the lines you added.

- [ ] **Step 8: Gates and commit.** `bun test`, `bun run audit`, `bun run audit --since main`, `claude plugin validate . --strict`. `git -C ~/Projects/StudioFixture status --porcelain` must be empty. The version stays 0.10.0: this branch is unreleased. Commit with subject `Phase 9 Task 10: route iPhone Duo prompts to apple-design; screenshot sizes stay with app-release` (or `… Task 10: Duo routing attempt reverted; evidence recorded` on REVERT). Include the whole `task-10-routing/` directory and use your own model's Co-Authored-By trailer.
