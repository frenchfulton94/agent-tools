# SDD ledger — plan: authoring/apple-studio/docs/plans/2026-09-30-phase9-adaptive-layout.md

Spec: authoring/apple-studio/docs/specs/2026-09-30-phase9-adaptive-layout-design.md
Branch: phase9-adaptive-layout (plan committed 193746b). SDK at start: iPhoneOS 27.0.

## Pre-flight scan

### Shared files / interfaces
| Tasks | Produces → consumes | Finding |
|---|---|---|
| T1 → T4, T8 | `docc.py --hig`, `print_page`, `url_for` → map fetches | consistent |
| T2 → T3, T4, T7, T9 | `> typecheck: ios X.Y`, exit 0/1/2 → T3 no directive (macOS), T4 expects exit 2 on 27.0 SDK, T7 expects 8/8, T9 gate | consistent |
| T2 ↔ T4 | both edit CONVENTIONS.md (pipeline bullet vs lines 48-49) | disjoint hunks; T4 line numbers shift by T2's insert only if T2's insert is above line 48 — it is below (pipeline tooling § is after reference files §)? Pipeline § is at line ~72, below 48 → no shift |
| T3 ↔ T4/T7/T8 | accessibility.md vs adaptive-layout.md | disjoint files |
| T4 ↔ T6 | SKILL.md line 15 routing vs line 3 description | disjoint lines |
| T0/T6/T9 | deferred.md items 1 / 13 / 7,12,14-17 | sequential, disjoint items |
| T4 → T5 | adaptive-layout § "Checking a layout on iPhone Duo" → app-release link | T5 runs after T4 |
| T4 → T8 | T4 § 7 says xcode-loop pose section "(Task 8 adds that section)" | dangling pointer between T4 and T8; resolved by T8 in all three discovery classes |
| T6 → T8 | fixture with MailboxScreen → probe copies fixture | consistent |
| T7/T8 → T9 | clean gate, R1-R4 verdicts → release | T9 blocks if SDK absent |

### Per-task self-consistency
| Task | Check | Finding |
|---|---|---|
| T0 | charter insert after line 193 | line 193 is `> rationale stands.` — correct |
| T1 | test calls `print_page(page, url)`; Step 4.3 signature `print_page(d, url, children=False)` | consistent |
| T2 | Step 7 "identical TOTAL" vs Step 5.2 adding a `proxy` preamble binding | a pre-existing snippet using `proxy` could flip FAIL→PASS → see Ruling 3 |
| T3 | lines 29-37 / 63-69; expect 4/4 | matches file and baseline |
| T4 | platform-idioms 85-93, line 49, SKILL.md line 15; Step 10 expects exit 2 on 27.0 | matches files; consistent with T2 |
| T5 | line 101 bullet | matches |
| T6 | ids fire-7..fire-10 = Duo rows | triggers.md has 6 FIRE + 4 NOFIRE → correct |
| T7 | 8/8 | 4 existing + 4 new snippets — correct |
| T8 | three discovery classes each have a path | consistent |
| T9 | Step 5 load check non-deterministic | accepted; validate --strict is the hard gate |

## Rulings
- Ruling 1: execute on branch `phase9-adaptive-layout` in the main checkout, no separate worktree — the branch already exists, the user approved the spec and plan on it, and the repo is clean — cost if wrong: none; history is on a branch either way.
- Ruling 2: task briefs and implementer reports go to `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-N-*/` (committed); only this ledger and review packages stay in the git-ignored workspace — CONVENTIONS.md § Verification records forbids committing phase records under `.superpowers/`, and review packages are regenerable from git — cost if wrong: extra files in the record.
- Ruling 3: T2 Step 7 passes if no snippet goes PASS→FAIL; a FAIL→PASS flip caused by the new `proxy` binding is an improvement and is recorded, not a failure — the step exists to catch regressions (Review Focus 1) — cost if wrong: a masked change in an unrelated skill's gate, visible in the logged diff.
- Ruling 4: run T0-T6 now; before T7, stop and ask the user if `xcrun --sdk iphoneos --show-sdk-version` is below 27.1. T9 depends on T7-T8, so it waits too — installing Xcode is a user action outside this worktree and the spec forbids shipping uncompiled snippets — cost if wrong: a pause.

## Progress
Task 0: dispatched implementer (sonnet), BASE 193746b
Task 0: implementer DONE_WITH_CONCERNS (0c18956) — scan: 0 genuine, 60 excluded (StudioFixture)
- Ruling 5: implementers' commits carry their own model's Co-Authored-By trailer rather than the plan's literal "Opus 5.5" line — a co-author trailer is an attribution claim and must name the model that wrote the commit — cost if wrong: cosmetic trailer mismatch against the plan text.
Task 0: ⚠️ Step 1 branch/ancestry — controller verified (ea4995c ancestor of 0c18956, branch phase9-adaptive-layout)
Task 0: complete (commits 193746b..0c18956, review clean)
Task 1: dispatched implementer (sonnet), BASE 0c18956
Task 1: implementer DONE (74d8f65)
User 2026-09-30: Xcode 27.1 beta installed at "/Applications/Xcode 27-1-beta.app" (27A9269, iPhoneOS 27.1). It replaced Xcode-beta.app; xcode-select now = /Applications/Xcode.app (27.0, 27A266a).
- Ruling 6: Tasks 7, 8 and T9's gate run with DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer" per command; xcode-select is not changed — it needs sudo and changes the user's system default — cost if wrong: a command run without the env var compiles against 27.0 and fails loudly via the directive's SDK check (exit 2), so it cannot pass silently.
- Ruling 7: Task 2 derives the macOS `-F` frameworks path from `xcrun --sdk macosx --show-sdk-platform-path` instead of the hardcoded /Applications/Xcode-beta.app path, which no longer exists — the hardcoded path now silently drops the AppIntentsTesting framework path — cost if wrong: the catalog before/after comparison may show FAIL→PASS flips in apple-intelligence, which Ruling 3 already classes as allowed and recorded.
Task 1: ⚠️ fixture nests reference in strong, not emphasis — controller resolved: emphasis/strong/newTerm share one branch (docc.py render), so coverage holds
Task 1: minor (deferred): `docc.py --hig` with no value raises IndexError instead of a message
Task 1: minor (deferred): render's new `table` branch has no test coverage
Task 1: minor (deferred): `--hig slug other/path` silently drops extra positional paths
Task 1: complete (commits 0c18956..74d8f65, review clean)
Task 2: dispatched implementer (sonnet), BASE 74d8f65
Task 2: implementer DONE (031f837) — catalog 31/51 → 32/51, one FAIL→PASS (app-intents-implementation #3, Ruling 7)
Task 2: ⚠️ no undisclosed flips — controller verified per-snippet verdict diff: exactly one change, app-intents-implementation.md #3 FAIL→PASS
Task 2: minor (deferred): docstring says directive precedes first fence; parser does not enforce position (typecheck_snippets.py:19 vs :87)
Task 2: minor (deferred): macOS branch shells out to xcrun per attempt; cache the platform path (typecheck_snippets.py:125-128)
Task 2: minor (deferred): new WHY comments name Phase 9 without the date the file's convention uses
Task 2: minor (deferred): no multi-block fixture under one directive
Task 2: complete (commits 74d8f65..031f837, review clean)
Task 3: dispatched implementer (sonnet), BASE 031f837
- Ruling 8: Task 4 Step 10 runs the gate with DEVELOPER_DIR set to the 27.1 beta (now installed) and treats failures as feedback to fix while writing, instead of expecting exit 2 on 27.0 — the SDK the plan waited for is present; Task 7 stays the formal gate with the name check and header fill — cost if wrong: none; Task 7 re-runs everything.
Task 3: implementer DONE (62f2262) — apple-design 2/4 → 4/4; gates pass
Task 3: ⚠️ classify-before-edit chronology not visible in a single commit — controller accepts: triage.md content matches the edits and the logs
Task 3: minor (deferred): report's block #2 line range off by one (71-84); triage.md cites "lines 4-5" (FILE line + FAIL line)
Task 3: complete (commits 031f837..62f2262, review clean)
Task 4: dispatched implementer (opus), BASE 62f2262
Task 4: implementer DONE (b66a498) — 8/8 clean on 27.1; gates pass. Carry-forwards:
  - Task 7: header URL list must use developer.apple.com/documentation `.md` URLs (bun test requires it)
  - Task 8: settle includeInactive default (docs say inactive returned; header option implies excluded) — probe already passes includeInactive; add a default-options query
  - deferred minor: docc.py does not render `termList` (definition lists); Task 4 read reserved-region kinds from raw JSON
Task 4: review — Needs fixes (3 Important: stale NavigationSplitView pointers in swiftui-design-implementation.md:3,87; LiveBadgeOverlay ignores isActive; opposite-edge rule unsourced, plan-mandated)
- Ruling 9: the "place a floating control on the edge opposite the vertical bar" rule (plan Task 4 Step 6, my own text) is withdrawn — the spec only requires "`toolbarVerticalEdge` for custom views", and Apple's toolbarVerticalEdge example aligns the control to the same edge as the bar. The reference states the sourced rule (read the edge, place custom controls relative to it; Apple's example groups them on the bar's edge) and the snippet follows Apple's pattern — cost if wrong: one sentence of guidance less opinionated than the plan wanted.
Task 4: minor (deferred): :168 "nil on hardware" drops "without a vertical bar"; :18 omits iPhone Mirroring; :18 repeats platform-idioms:49 clause; MessageDetail lacks TabView so compression modifier is inert as shown; badge uses magic 80/160 not frame.intersects; :41 cites a UIKit header outside the UIKit section
Task 4: carry to Task 8: check whether `.secondaryAction` items on iPhone start in overflow (affects MessageDetail's visibilityPriority teaching)
Task 4: fix round 1/5 dispatched (resume implementer), FIX_BASE b66a498
Task 4: fix round 1/5 (3 addressed, 0 open; commits b66a498..8055b87)
Task 4: complete (commits 62f2262..8055b87, review clean)
Task 5: dispatched implementer (haiku), BASE 8055b87
Task 5: implementer DONE (97e1ea8)
Task 5: review — Needs fixes (1 Important: task-5-report.md not committed)
Task 5: ⚠️ WebFetch re-execution not visible in diff — controller accepts: fetch.txt values match the survey and the brief
Task 5: minor (deferred): fetch.txt omits the source URL (survey/screenshot-specifications.txt carries it)
Task 5: minor (deferred): brief's line numbers (:1,:101) had drifted; content located correctly
Task 5: fix round 1/5 dispatched (resume implementer), FIX_BASE 97e1ea8
Task 5: fix round 1/5 (1 addressed, 0 open; commits 97e1ea8..0d6b72f)
Task 5: complete (commits 8055b87..0d6b72f, review clean)
Task 6: dispatched implementer (sonnet), BASE 0d6b72f
Task 6: implementer DONE (2b113ff; fixture 5287d2c) — baseline 11/16 (fire 6/10, nofire 5/6); fire-7/8/10 routing misses, fire-9 prompt-wording defect, nofire-1 pre-existing; description edit → 11/16 with nofire-6 and fire-5 regressions → reverted per Step 9; item 13 left open
Task 6: ⚠️ gates not re-run by reviewer — report shows them; only plugins/ change is triggers.md markdown. ⚠️ visionOS unbuilt — brief self-contradicts (Step 1 prose vs Steps 2-3 / Review Focus 5); APIs are visionOS-available
Task 6: minor (deferred): fire-9 "outside the harness" neutral-dir runs not saved; deferred item 13 relies on them — soften or save
Task 6: minor (deferred): fire-9 prompt ("Content gets cut off at the fold") is a known-bad row with no recorded reword trigger
Task 6: minor (deferred): classification.md/report wording slips (nofire-6 "apple-design's app-release"; fire-8 "reproduced identically"; fire-5 misattributed to item 6)
Task 6: minor (deferred): item 13 paragraph CEE slips (tense, "genuine", Step 8/9 without brief pointer, evidence list omits diagnostic/)
Task 6: minor (deferred, plan-mandated, pre-existing): fire-1 "Build the settings screen UI" breaks the no-"build X" harness rule
Task 6: minor (deferred): eval sessions loaded 50-101 tools inconsistently — harness variance source to record
Task 6: complete (commits 0d6b72f..2b113ff, review clean)
- Ruling 10: Task 6 closes with the Duo routing gap open (fire-7, fire-8, fire-10 route elsewhere; the one description edit the plan allowed regressed nofire-6 and fire-5 and was reverted). No second description attempt this phase — choosing new wording and a multi-run protocol to beat single-sweep noise is a design decision the plan did not make; it goes to the user in the final message — cost if wrong: the phase ships a reference that Duo-named prompts do not reach unless the prompt also reads as layout/UI work.
Task 7: dispatched implementer (sonnet), BASE 2b113ff
USER 2026-09-30: pause before the next task — finish Task 7 (implement + review), then do NOT dispatch Task 8 until the user says so
Task 7: implementer DONE (545e57a) — SDK 27.1 (27A9269), 8/8 clean, 7 MISSING resolved (5 in SwiftUICore, not SwiftUI.swiftinterface; 2 noise), header filled
Task 7: minor (deferred): the plan's Step 4 name-check grep misses SwiftUICore.framework (SwiftUI re-exports it); 5 false MISSING, resolved by hand — fix the check if reused
Task 7: minor (deferred): header rule "prose parenthetical citation = header URL" is a judgment call, not written in CONVENTIONS.md
Task 7: complete (commits 2b113ff..545e57a, review clean)
PAUSED before Task 8 per user instruction. Resume point: Task 8 (BASE 545e57a); brief at records/.../task-8-probe/task-8-brief.md
USER 2026-09-30: continue. Routing-fix question unanswered → Ruling 10 stands (gap stays deferred item 13). Task 8: dispatched implementer (opus), BASE 545e57a
- Ruling 11: Task 8 adds R5 (reservedRegions default includes inactive?) and R6 (.secondaryAction starts in overflow?) to the probe — both are open questions Task 4's implementer and reviewer raised about claims the reference makes; the probe is already running on the device that answers them — cost if wrong: a few extra lines in the probe and results.
Task 8: implementer NEEDS_CONTEXT — no iOS 27.1 simulator runtime installed (Duo device type exists; runtimes 26.5, 27.0 only; 27.1 SDK expects 24A94403). Probe + run.sh written and build succeeds; no commits. Waiting on user to install runtime (or approve the download). Resume implementer at Step 2.
USER 2026-09-30: approved running the iOS 27.1 simulator runtime download
Task 8: iOS 27.1 runtime installed (24A94401) by approved download; resumed implementer at Step 2
Task 8: implementer NEEDS_CONTEXT class B — poses and rotation GUI-only (devicectl orientation set / rotate report success, no effect). Sim 'Duo Probe' B4066944-1CF0-46D6-90A4-5FD552B36FE4 left booted. Partial: R4 CONFIRMED; R1 outer-portrait .trailing; R6 secondaryAction items absent from bar (Share + … only). Added capture.sh and launch args -DuoProbeOpenSheet/-DuoProbeSheetDisabled. Waiting on user pose walk.
Task 8: pose walk done (user + controller captures): outer-portrait-overflow (both secondaryAction items in overflow → R6), outer-landscape (.trailing, vertical), inner-landscape (relabelled; .trailing, 1 division inactive, default query 0), inner-portrait (nil, horizontal bar), inner-partial (division active, default query returns it → R3, R5). R2 confounded: secondaryAction items start in overflow regardless of icon → needs re-probe with items in .primaryAction on the closed display. Asked user to close device (portrait).
Task 8: user closed device (portrait); resumed implementer for R2 re-probe (.primaryAction) + Steps 6-10
Task 8: implementer DONE (32d956c) — R1-R4 CONFIRMED (R2 via .primaryAction re-probe), R5 default omits inactive (reference corrected), R6 secondaryAction starts in overflow on both displays; cleanup verified
Task 8: review — Needs fixes (2 Important: MessageDetail teaches visibilityPriority effect the reference calls unknown; xcode-loop § 9 states unobserved 180° hinge reading). All R1-R6 verdicts verified against screenshots.
Task 8: ⚠️ StudioFixture clean / gates / 8/8 not re-verified by reviewer — controller verified fixture clean and no booted sim after 32d956c
Task 8: minor (deferred): R1 orientations walked not named (portrait, landscapeRight; inner portrait was portraitUpsideDown)
Task 8: minor (deferred): R6 overflow opened on outer display only; "both displays" is inference
Task 8: minor (deferred): R4 side effect — .disabled sheet also moves presenting view's status bar to top; unrecorded
Task 8: minor (deferred): unified.log:32 size 585x783 matches no capture
Task 8: minor (deferred): citation trailing period makes fragment sentences (adaptive-layout.md 47,111,117,129,168)
Task 8: minor (deferred): R5 correction generalized from .division to all regions
Task 8: minor (deferred): adaptive-layout.md:4 header note says R1-R4, should cover R5-R6
Task 8: minor (deferred): § 9 output strings (Note: No display specified…, (1) LCD/(3) LCD-1) not in any log
Task 8: minor (deferred): rotation-commands-don't-work tested in closed pose only
Task 8: minor (deferred): results.md R5 row quotes a 7-word Apple phrase verbatim — paraphrase
Task 8: minor (deferred): committed probe is the R2 variant; other evidence came from a different build; R5 comment in Swift stale
Task 8: minor (deferred): deferred item 12 fixed but still listed open (Task 9 closes it)
Task 8: fix round 1/5 dispatched (resume implementer), FIX_BASE 32d956c
Task 8: fix round 1/5 (2 addressed, 0 open; commits 32d956c..1cb4e31) — R7 added: visibilityPriority works on .primaryAction (high stays, low overflows), no visible effect on .secondaryAction; MessageDetail moved to .primaryAction
Task 8: minor (deferred): task-8-report.md pre-fix Concerns item 1 left stale above the fix-round section
Task 8: complete (commits 545e57a..1cb4e31, review clean)
Task 9: dispatched implementer (sonnet), BASE 1cb4e31
- Ruling 12: Task 9 includes deferred item 17 despite R1-R4 all CONFIRMED, reworded to record that discovery was class B (poses GUI-only, probe cannot run unattended) and what the probe did not cover (landscapeLeft, RTL, occlusion regions) — the brief's own condition names class B as a trigger, and the GA re-verification in item 14 will need to know the probe needs a person — cost if wrong: one extra deferred item.
USER 2026-10-01: 'Fix the Duo routing gap after Task 9' — supersedes Ruling 10's deferral. After Task 9 + its review: present a short bounded design (description wording for apple-design + app-release boundary, multi-run eval protocol, fire-9 reword) and get approval before implementing; then final whole-branch review covers both.
Task 9: implementer DONE (9f3c3a6) — 0.10.0; items 7,12 updated, 14-17 added; 11/11 gates pass; spec append 9 PASS / 1 PARTIAL (evals)
- Ruling 13: accept Task 9's one-line rewording of spec line 163 ("Every ```swift block MUST typecheck" → "Every Swift code block MUST typecheck") — the inline fence opened an unterminated code block that broke Vale's parsing of the rest of the spec; meaning unchanged — cost if wrong: one line of spec text differs from its approved wording.
Task 9: minor (deferred): Vale coverage note in report; spec line-163 edit outside literal Modify list (pre-authorized, Ruling 13)
Task 9: complete (commits 1cb4e31..9f3c3a6, review clean)
Routing fix: design presented to user (descriptions for apple-design + app-release, fire-9 reword, app-release FIRE row, records; protocol A = 3 runs/row post-edit, re-baseline only a flagged row). AWAITING APPROVAL — do not implement before a yes.
USER 2026-10-01: approved routing-fix design, protocol A. Task 10 (routing fix) — brief written by controller at records/.../task-10-routing/task-10-brief.md; BASE 9f3c3a6
Task 10: dispatched implementer (sonnet), BASE 9f3c3a6 — 3 sweeps × 28 rows (~75 min)
Task 10: implementer DONE (641429c) — REVERT: Duo 4/4 held (3/3 each) but ad-fire-5 3/3 baseline → 1/3 post = confirmed regression per rule; implementer attributes to item-6 Bash/Edit leak; no revision round
Task 10: note — ad-fire-5 also failed in Task 6's after-edit run (both description edits hit it): combined post-edit 1/4 vs baseline 4/4
Task 10: review — Needs fixes (4 Important: revision round wrongly skipped on a misclassification (sessions split Skill vs Edit after Read MailboxScreen.swift; leak present in passes too); item 13 + spec addendum misattribute cause; spec addendum tally.md pointers wrong; item 13 omits rows still open / unmeasured ad-fire-9 / ad-fire-5 guard)
Task 10: minor (deferred): addendum says "Task 9 baseline" (is Task 6's); "App Store Connect exclusion" (is "App Store screenshots"); tally.md baseline section hand-appended but called generated; report's rule-change proposal rests on the misreading
- Ruling 14: run Step 6's one revision round with the reviewer's apple-design wording (adds "sheets, alerts, and confirmation dialogs before destructive actions" + "adding a confirmation or alert before a destructive action"), app-release at Step 2 text; re-run all 16 apple-design rows plus ar-fire-8 and ar-nofire-3 ×3 (54 sessions) rather than the reviewer's 8-row subset — a description change can move any apple-design row, and ar-nofire-3 ("Design the onboarding screens") is the app-release row most exposed to an apple-design wording change — cost if wrong: ~30 extra minutes of sweeps.
Task 10: fix round 1/5 dispatched (resume implementer), FIX_BASE 641429c
Task 10: fix round 1 implementer DONE (73447ef) — revision round KEEP: Duo 4/4 (3/3 each), ad-fire-5 3/3, ad-fire-3 2/3, ad-nofire-1 2/3 (excluded), 0 confirmed regressions; records corrected
Task 10: fix round 1/5 (4 addressed, 0 open; commits 641429c..73447ef)
Task 10: minor (deferred): deferred.md Task 9/Step 8 paragraph uses unprefixed row names vs Task 10's ad-/ar- prefixes
Task 10: complete (commits 9f3c3a6..73447ef, review clean) — KEEP
Final review: dispatching (opus), MERGE_BASE f8f8a8d
Final review (opus): With fixes — 0 Critical, 4 Important (arrangement-view nesting contradiction :92; toolbarVerticalEdge nil "on hardware" :172; badge snippet contradicts small-move rule :56/:79; apple-design description promises destructive-confirmation content no reference has), 9 Minor; triage: fix-before-merge = T4 nil wording, T4 :18 vs platform-idioms:49, T4 badge 80/160, T10 "Task 9 baseline"/"App Store Connect exclusion".
- Ruling 15: the single final fix wave takes all 4 Important + Minors 5-8, 10, 11, 13; Minor 9 is handled by linking the screenshot-specification page in the general bullet, NOT by editing app-release's description; Minor 12 (safe-area asymmetry guidance) included as one sourced sentence. No skill description changes in the fix wave — both were validated by the Task 10 revision-round sweep and any edit would invalidate it — cost if wrong: app-release's description keeps a slightly broad "every device size" phrase.
Final fix wave: dispatched (opus), FIX_BASE 73447ef
Final fix wave: DONE (156cbf7) — 13/13, 9/9 snippets, gates pass; descriptions untouched
Final fix wave: re-review — all 13 ADDRESSED, no new Critical/Important (commits 73447ef..156cbf7)
Final: parked — adaptive-layout.md:104 "For the same reason, avoid … List or ScrollView" gives the split-view reason, not Apple's (part of the view can become unreachable) — Ruling: real, minor, shipped wording; one-line fix offered to the user at finish rather than a second fix wave (the process allows one)
Final: parked — hig-patterns.md:72 "To confirm an action that people started, prefer an action sheet" overreaches; source scopes it to offering choices about an intentional action — Ruling: real, minor; offered to the user at finish
Final: parked — adaptive-layout.md:185 closest paraphrase of the HIG asymmetry passage (no full sentence quoted) — Ruling: acceptable as is; reword offered
Final: parked (nits) — hig-patterns:1 missing one confirmationDialog URL; LiveBadgeOverlay possible one-frame move on appear; "You can't undo this action." near Apple's stock text — Ruling: stay deferred
Final: out-of-scope — spec Deliverables §1 item 4 and plan :615 still say "never inside NavigationSplitView" (original design input, superseded by the shipped reference) — Ruling: leave design inputs as written; the verification results record the change
Final review clean. Workspace to be deleted after committing this ledger to the phase record.
USER 2026-10-01: fix open issues, then PR. Resolved the three parked shipped-text minors: adaptive-layout.md:104 (Apple's reason — part of the view can become unreachable), :185 (reworded further from the HIG passage), hig-patterns.md:72 (scoped to offering choices about an intentional action, per the Action sheets page).
