### Task 9: Deferred items, version bump, final gates, spec append

**Files:**
- Modify: `$AS/docs/deferred.md` (items 7 and 12; new items 14–17)
- Modify: `plugins/apple-studio/.claude-plugin/plugin.json` (version, description)
- Modify: `.claude-plugin/marketplace.json:78` (apple-studio description, which mirrors plugin.json)
- Modify: `$AS/docs/specs/2026-09-30-phase9-adaptive-layout-design.md` (append verification results)

**Interfaces:**
- Consumes: every task's record.

- [ ] **Step 1: Update item 7.** Append `**Phase 9 (2026-09-30).**`: its trigger ("the phase after Phase 7") passed in Phase 8 unaddressed; Phase 9 triaged the two `apple-design` failures (both framing artifacts, each with a reference defect: deprecated `accentColor`, `AnyView` in a ternary) and fixed them — evidence `records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md`. 17 remain, none in `apple-design`. The trigger stands: triage them in the next phase.

- [ ] **Step 2: Update item 12.** Append: resolved 2026-09-30 in Phase 9 Task 8, which edited `headless-commands.md` for the Duo pose section and rewrote the citation.

- [ ] **Step 3: Add new items.** After item 13:
  - **14. Re-verify every iOS 27.1 claim at GA.** `adaptive-layout.md` was compiled against a 27.1 beta SDK (build from `task-7-compile/sdk.log`). Beta APIs can be renamed. **Trigger: the first Xcode release whose iPhoneOS SDK is 27.1 non-beta** — re-run the gate and Task 8's probe.
  - **15. A camera primer for direction-aware capture.** Apple's "Choosing a camera by the direction it faces" and the iPhone Duo camera-accessory article are cited once in `adaptive-layout.md`; no AVFoundation primer exists. **Trigger: the first real app that captures photos or video on iPhone Duo.**
  - **16. App Store Connect upload support for Duo screenshots.** `app-store-submission.md` states uploads are not yet accepted. **Trigger: Apple's screenshot specification page drops that note** — then remove the caveat.
  - **17. R1–R4 runtime status.** Include this item only if any claim is `NOT CHECKED` or discovery was class B/C; name each unchecked claim and the reason. **Trigger: the first simulator or device that exposes the missing pose control.**

- [ ] **Step 4: Bump the version and descriptions.** In `plugin.json`: `"version": "0.10.0"`. In both `plugin.json` and `marketplace.json`, change `Human Interface Guidelines conformance and accessibility,` to `Human Interface Guidelines conformance and accessibility, adaptive layout across sizes, poses, and foldables,`.

- [ ] **Step 5: Run every gate and save the output to `task-9-release/gates.log`.**

```bash
python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tail -1   # TOTAL: n/n clean
python3 $AS/pipeline/test_docc.py                                                                           # PASS
bash $AS/pipeline/test_typecheck_snippets.sh                                                                # six ok, exit 0
bash $AS/pipeline/test_run_evals.sh                                                                         # passes
bun test
bun run audit
bun run audit --since main                                                                                  # no unbumped plugin
claude plugin validate . --strict
claude --plugin-dir plugins/apple-studio -p "List the apple-design skill's reference files" --allowedTools "Skill Read" --max-turns 6 < /dev/null   # names adaptive-layout.md
git -C ~/Projects/StudioFixture status --porcelain                                                          # empty
xcrun simctl list devices booted                                                                            # no device
```

   Every line must meet its expectation. If Task 7 or 8 could not run for lack of the SDK, the first line exits 2: stop and report the phase as blocked on the SDK rather than shipping.

- [ ] **Step 6: Append verification results to the spec.** Under a new `## Verification results (appended <date>, Phase 9 Task 9)` heading, one subsection per item in the spec's § Verification, each with **PASS**, **PARTIAL**, or **FAIL** and `<file>:<line-range>` evidence pointers into the phase record. Where the phase found one of the spec's own claims wrong, record the correction beside the claim (Phase 7 precedent). Include the kill-switch count, the eval pass rates, and R1–R4 verdicts.

- [ ] **Step 7: Prose check and commit.** Run Vale over `deferred.md` and the spec; fix any non-"amend" warning in the lines you added.

```bash
git add $AS/docs plugins/apple-studio/.claude-plugin/plugin.json .claude-plugin/marketplace.json $AS/records/2026-09-30-phase9-adaptive-layout/task-9-release
git commit -m "Phase 9 Task 9: apple-studio 0.10.0 — adaptive layout and iPhone Duo

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 8: Hand off.** Do not push, open a PR, or tag without the user's go-ahead. Report the branch, the commit list, and the gate log, then use superpowers:finishing-a-development-branch. The tag `apple-studio-v0.10.0` goes on the merge commit on `main`, after merge. Remind the user that Xcode imports a copy of the plugin and needs a re-import after merge (`deferred.md` item 3).
