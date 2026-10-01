# apple-studio Phase 9: Adaptive layout and iPhone Duo — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`). Decisions taken 2026-09-30;
this doc is the input to the Phase 9 implementation plan.

Register: spec prose (engineer audience). No project glossary exists; terms
follow CONVENTIONS.md. Paths are relative to `authoring/apple-studio/` unless
they start with `plugins/`.

## Goal

Teach the plugin to build iOS apps that adapt to iPhone Duo. Organize that
knowledge by concept, not by device, so it outlives the device.

Ship one new `apple-design` reference, `adaptive-layout.md`. It owns layout
that must survive any size, shape, or pose. iPhone Duo is its most demanding
case, and iPad windowing and iPhone Mirroring are its comparisons.

Version bump to 0.10.0. Tag `apple-studio-v0.10.0`.

**No new skill.** `apple-design` already triggers on layout, toolbars, and
navigation. A device-named skill would compete with it for the same prompts.

### Origin

A user request on 2026-09-30, not the charter's long tail. Apple published two
pages that define the work:

- HIG, *Designing for iPhone Duo* —
  https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo
  (change log: new page, September 9, 2026).
- *Preparing your app for iPhone Duo* —
  https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo

iPhone Duo is a foldable iPhone with a compact outer display and a large inner
display. Its hinge supports several poses. On the outer display, and on the
inner display in landscape, the system moves toolbars and tab bars to a
vertical bar on the side.

### Charter amendment

The charter says ML "moves to Phase 8"
(`docs/specs/2026-08-03-apple-studio-design.md:186-193`). Phase 8 shipped the
catalog migration instead and did not amend that line. Phase 9 MUST amend it:
ML remains the one outstanding long-tail item, and Phase 9 is on-demand work.
Amending the line is a task in this phase, not a side effect of this spec.

## What the survey established

Evidence root: `records/2026-09-30-phase9-adaptive-layout/survey/`.

### Finding 1 — the Duo layout APIs are iOS 27.1 beta and absent from the installed SDK

Both installed Xcodes are 27.0 (`27A5228h` beta and `27A266a`) and ship
`iPhoneOS27.0.sdk` (`sdk-survey.log:3-10`). The shipped SwiftUI and UIKit
interfaces contain none of the Duo layout symbols (`sdk-survey.log:11-44`).
Apple documents them as iOS 27.1 beta (`sdk-survey.log:47-55`).

| Symbol group | Documented | In 27.0 SDK |
|---|---|---|
| `ArrangementView`, `UIArrangementViewController` | iOS 27.1 beta | no |
| `ReservedRegion`, `UIView.ReservedRegion`, `reservedRegions(…)` | iOS 27.1 beta | no |
| `toolbarVerticalEdge`, `toolbarVerticalBehavior(_:)`, `axisBehavior(_:)`, `ToolbarVerticalCompressionBehavior` | iOS 27.1 beta | no |
| `ToolbarOverflowMenu`, `ToolbarItemVisibilityPriority`, `topBarPinnedTrailing`, `presentationPlacement(_:)`, `backgroundExtensionEffect()` | iOS 27.0 | yes |

Consequence: the compile gate cannot pass on this machine for any 27.1 symbol.
Decision A (below) resolves it by installing the Xcode 27.1 beta.

### Finding 2 — the compile gate targets macOS

`pipeline/typecheck_snippets.py` calls `swiftc -typecheck` with no `-sdk` and
no `-target`. The Phase 7 spec recorded that it compiles for
`arm64-apple-macosx27.0.0` (`docs/specs/2026-09-12-phase7-fluid-interfaces-design.md:60-65`).
That was sound for cross-platform SwiftUI. It is unsound here:
`UIArrangementViewController`, `UIView.ReservedRegion`, and
`ToolbarOverflowMenu` have no macOS availability (`sdk-survey.log:49-50,56`). A
correct snippet would fail, and the failure would read as an invented symbol.
The script also has no UIKit import hint.

### Finding 3 — `docc.py` drops defined terms and cannot reach the HIG

`pipeline/docc.py` walks `inlineContent` only inside paragraphs. It drops the
text of emphasis, strong, and new-term nodes. The developer page's defined
terms render as gaps: "represent an , which is" for "represent an *arrangement
view*, which is". A distiller reading that output loses every defined term.

`docc.py` also knows only the `documentation/` and `tutorials/` prefixes. HIG
pages live at `/tutorials/data/design/human-interface-guidelines/<slug>.json`.
This survey fetched the HIG page by hand.

### Finding 4 — `apple-design` is red before this phase writes anything

`typecheck_snippets.py` over `plugins/apple-studio/skills/apple-design/references/*.md`
reports `TOTAL: 2/4` (`typecheck-apple-design-baseline.log:337`). Both failures
are in `accessibility.md` (`typecheck-apple-design-baseline.log:4-5,179`). They are
two of the 19 untriaged failures in `docs/deferred.md` item 7.

### Finding 5 — the eval fixture has no UI

`~/Projects/StudioFixture` is the stock template: `ContentView.swift`,
`StudioFixtureApp.swift`, and the test targets (`fixture-state.log:1-11`).
`docs/deferred.md` item 13 records that `apple-design` should-fire rows fail
on it because the session finds nothing to review.

## Decisions (user-approved 2026-09-30)

| Question | Decision |
|---|---|
| The 27.1 compile gate | **Install the Xcode 27.1 beta** and compile every snippet. No uncompiled snippet ships. |
| Where Duo knowledge lives | **A concept-named reference**, `adaptive-layout.md`, as a seventh `apple-design` file. Not a device file, not a new skill, not spread across existing files. |
| Runtime verification depth | **Compile everything; check four behavioral claims at runtime** on the Duo simulator. |
| Eval fixture and the description edit | **Seed StudioFixture with real UI, baseline, then edit the description only if the baseline shows a gap.** |

The reasoning behind each decision is recorded in the phase record, not
repeated here.

## Deliverables

### 1. New reference `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`

About 250 lines. Header:

```
> verified: <YYYY-MM> against <doc URLs checked, including the SDK build>
> sources: live HIG and developer documentation (DocC JSON)
> typecheck: ios 27.1
```

Sections, in order:

1. **What layout reads.** Size classes and scene or container bounds. Never
   `userInterfaceIdiom`, interface orientation, or screen dimensions. This
   section absorbs `platform-idioms.md` § "When to branch code vs. when the
   system already adapts for you" and its iPad fluid-layout rule.
2. **System containers first.** What `NavigationSplitView`, `TabView`, and
   `NavigationStack` already do across compact and regular width, camera
   occlusion, and the fold.
3. **Reserved regions.** Occlusion versus division. Active versus inactive.
   Duo's three regions, with iPad window controls as the comparison. Querying
   through `ReservedRegion`. Even grid column counts. Small adjustments over
   rearrangement.
4. **Arrangement views.** Split versus overlay. Mapping from
   `HStack`/`VStack`/`ZStack`. Axis limits. Navigation containers go outside.
   Never inside a `List`, `ScrollView`, or `NavigationSplitView`.
5. **Bars that adapt to space.** When bars go vertical, including the sheet,
   inspector, and split-view rules. Item order. Icon and title on every item.
   Visibility priority. The system overflow menu. Toolbar-versus-tab-bar
   compression. `toolbarVerticalEdge` for custom views.
   `backgroundExtensionEffect()`. Full-width layouts. Default placement is not
   overridden.
6. **Games.** Fill the screen in every pose. Prefer an aspect change to
   letterboxing.
7. **Checking a layout on iPhone Duo.** Both displays, each pose, rotated.
   Build with the current Xcode: apps built with Xcode 26 or earlier do not
   extend under the status bar and camera. Device Hub. One pointer to Apple's
   camera-direction and camera-accessory articles.
8. **`## Maintaining older code: UIKit equivalents`.** A mapping table, per the
   stack baseline in CONVENTIONS.md.

Requirements:

- Every Swift code block MUST typecheck under the `ios 27.1` directive.
- Every behavioral claim in the runtime set (deliverable 6) MUST cite its
  probe result, or carry the marker "documented, not runtime-checked".
- The file MUST NOT restate a rule that `platform-idioms.md` or
  `hig-patterns.md` keeps. It links to it.

### 2. Changes to existing `apple-design` files

- `SKILL.md`: one routing line, "Layout across sizes, poses, and foldables
  (iPhone Duo) → `references/adaptive-layout.md`". The description changes
  only if the eval baseline shows Duo prompts missing the skill (deliverable 5).
- `platform-idioms.md`: § "When to branch" moves out. A one-line pointer and a
  scope-note update replace it. Menus, input, windows, and reach stay.
- `hig-patterns.md`: the toolbar and tab-bar guidance gains a pointer to
  `adaptive-layout.md` § 5.
- `accessibility.md`: the two failing snippets are triaged under deferred item
  7. Each is classified as framing artifact or reference defect before it is
  edited.

### 3. Changes to other skills

- `app-release/references/app-store-submission.md`: the iPhone Duo screenshot
  sizes, with Apple's note that App Store Connect upload support comes later
  (`survey/screenshot-specifications.txt`).
- `xcode-loop`: capturing screenshots of a Duo pose. If Device Hub or `simctl`
  sets a pose headlessly, document the command. If pose control is GUI-only,
  state that. Deferred item 12 fires on this edit: rewrite the
  `~/Projects/StudioFixture` citation in `headless-commands.md:6-7`.

A camera primer is out of scope; see Out of scope.

### 4. Pipeline changes

- `pipeline/docc.py`: render the content of emphasis, strong, and new-term
  nodes, and render asides and tables. Add `--hig <slug>` for HIG pages. Add
  an offline test that renders a saved JSON fragment and asserts that defined
  terms survive.
- `pipeline/typecheck_snippets.py`: read a `> typecheck: ios <version>` header
  directive. Under it, compile against the iPhoneOS SDK with
  `-target arm64-apple-ios<version>`. A file without the directive keeps
  today's behavior. Add a UIKit import hint. Add accurate preamble bindings for
  `GeometryProxy` and `UIView` fragments.
- The directive MUST catch invented API. One deliberately invented symbol MUST
  fail under it.

### 5. Eval fixture UI (`~/Projects/StudioFixture`)

Add one real screen: a `NavigationSplitView` with a toolbar, a tab bar, and a
two-pane detail. It MUST build for iOS and macOS with the 27.0 SDK, so the
fixture never depends on a beta. Commit it in the fixture's own repository.

Then run the eval sequence:

1. Baseline: sweep `apple-design/evals/triggers.md`, including the new rows,
   with the description unchanged.
2. If any Duo should-fire row misses, edit the description and sweep again.
3. Report both pass rates. Do not edit the description to fix a
   fixture-dependent miss (deferred item 6).

New should-fire rows:

- "Make my app work on iPhone Duo"
- "My toolbar buttons disappear when the phone is closed"
- "Content gets cut off at the fold"
- "Should I use an arrangement view here?"

New should-not-fire rows:

- "Screenshot the app on the iPhone Duo simulator" (`xcode-loop`)
- "What screenshot sizes does the App Store need for iPhone Duo?" (`app-release`)

### 6. Runtime probe (`pipeline/fixtures/duo-probe/`)

One SwiftUI screen and a run script. The script copies StudioFixture into a
scratch directory, adds the probe, builds with the 27.1 SDK, and runs it on
the Duo simulator. It MUST NOT change `~/Projects/StudioFixture`.

Four claims, each recorded with a screenshot or log:

| # | Claim | Why code depends on it |
|---|---|---|
| R1 | `toolbarVerticalEdge` reports a vertical bar on the outer display in both orientations and on the inner display in landscape only. | Custom views lay out against it. |
| R2 | A toolbar item with a title and no icon does not appear in a vertical bar. | An item silently leaves the vertical bar. |
| R3 | The fold region is active only when the device is partially open. | Custom views query it. |
| R4 | A sheet on the outer display gets vertical bars by default, and `toolbarVerticalBehavior(_:)` disables them. | Sheets need an explicit opt-out. |

If the simulator exposes poses only in the GUI, drive them by hand and
capture screenshots. If it exposes no poses, R1–R4 ship marked "documented,
not runtime-checked", and a new deferred item records the gap.

### 7. Distillation map `pipeline/maps/apple-design-duo-live.md`

The seed list: both Apple pages, the linked SwiftUI and UIKit symbols, and the
screenshot specifications. Record expected pages that fail as `MISSING:`.

### 8. CONVENTIONS.md amendments

- Reference files per skill: replace "3–6 files per skill" with one file per
  decision area. A reference file MUST NOT be named for a device.
- Document the `> typecheck: ios <version>` directive under Pipeline tooling.

### 9. Release and records

- `plugins/apple-studio/.claude-plugin/plugin.json`: 0.9.1 → 0.10.0. The
  description gains "adaptive layout across sizes, poses, and foldables".
- `docs/deferred.md`, new items:
  - Re-verify every 27.1 claim at 27.1 GA.
  - A camera primer for direction-aware capture.
  - App Store Connect upload support for Duo screenshots.
  - Any R1–R4 claim not checked at runtime.
- `docs/deferred.md`, existing items: update 7, 12, and 13 with what this
  phase did. Item 7 records that its trigger passed in Phase 8 unaddressed.
- Phase record: `records/2026-09-30-phase9-adaptive-layout/`.

## Opening task: phase sweep

1. **Kill-switch measurement.** Re-run the `input.skill` scan over
   `~/.claude/projects` since 2026-09-12, per `docs/deferred.md` item 1. The
   precondition is still unmet, so no skill is cut. Record the number.
2. **Verified-header check** on `platform-idioms.md` and `hig-patterns.md`,
   the two existing files this phase edits.

## Sequence and the external dependency

Order: pipeline fixes → distillation map → write `adaptive-layout.md` →
compile → runtime probe → fixture and evals → gates → release.

Only compile and the probe need the 27.1 SDK. Writing proceeds while it
installs. The user installs the Xcode 27.1 beta; no task automates it.

## Verification (definition of done)

- `typecheck_snippets.py` over `apple-design/references/*.md` reports every
  block clean, `adaptive-layout.md` included under `ios 27.1`.
- The invented-symbol check fails under the iOS directive.
- The `docc.py` offline test passes. `pipeline/test_run_evals.sh` passes.
- R1–R4 each carry runtime evidence or the "not runtime-checked" marker.
- Trigger evals run through `pipeline/run_evals.py`. Baseline and post-edit
  pass rates are both reported. `git -C ~/Projects/StudioFixture status
  --porcelain` is empty at close.
- `bun test` and `bun run audit` pass. `bun run audit --since main` reports
  no unbumped change.
- `claude plugin validate . --strict` passes. The plugin loads under
  `--plugin-dir`.
- No simulator is left booted.

Evidence pointers use `<file>:<line-range>`, per CONVENTIONS.md.

## Out of scope

- **A camera primer.** `apple-frameworks` has no AVFoundation primer to
  extend. Direction-aware capture is a framework topic, not layout. Deferred.
- **iPad and visionOS rewrites.** `adaptive-layout.md` names them as
  comparisons only.
- **The other 17 failures under deferred item 7.** They are in other skills.
- **A device-named skill or reference.** See Goal and deliverable 8.

## Waiver

**G-X1 — CEE.CoreWords, "amend", 2026-09-30.** The controlled-English
dictionary prefers "change". CONVENTIONS.md uses "amend" as a term of art for
a deliberate edit to a standing document. Phase 7 took the same waiver.

## Open questions for the plan

- Whether R1–R4 run in one probe screen or four. The plan decides by what the
  simulator's pose control allows.

## Verification results (appended 2026-10-01, Phase 9 Task 9)

Evidence root: `records/2026-09-30-phase9-adaptive-layout/`. Pointers are
`<file>:<line-range>` per CONVENTIONS.md. Where this phase found one of its
own claims wrong, the correction sits beside the claim. It does not replace
the claim — the Phase 7 precedent.

### 1. Kill-switch measured, gate correctly did not fire — PASS
2,168 transcripts since 2026-09-12; **0 genuine non-fixture invocations** of
an `apple-studio:*` skill. All 60 excluded hits came from `StudioFixture`.
The precondition for cutting a skill — one real feature shipped through the
plugin — stays unmet, so no skill is cut, the third consecutive zero.
Evidence: `task-0-sweep/killswitch.log:1-3`;
`docs/deferred.md:126-135` (item 1's Phase 9 paragraph).

### 2. Charter amended — ML stays the one outstanding long-tail item — PASS
`docs/specs/2026-08-03-apple-studio-design.md:195-198`. Phase 8 shipped the
catalog migration, not ML, and left the "strongest Phase 8 candidate" line
unamended. The new block states that, names Phase 9 as on-demand work, and
does not move ML again. Evidence: `task-0-sweep/task-0-report.md:46-57`
(inserted text, verbatim against the brief).

### 3. New reference `adaptive-layout.md` shipped, three claims corrected — PASS
`plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`,
247 lines, all eight sections in the spec's order. Every Swift code block
typechecks under `> typecheck: ios 27.1`. Task 4 confirmed it while writing
the file: 8/8 (`task-4-reference/typecheck-27.1.log:32`). Task 7 confirmed
it again against build 27A9269: 8/8 (`task-7-compile/typecheck.log:31`).
This task's own gate run confirms it a third time, unchanged: 8/8
(`task-9-release/gates.log`, Gate 1). A deliberately invented symbol,
`.toolbarVerticalBehavior(.alwaysVertical)`, fails to compile under the same
directive. Routing added at `apple-design/SKILL.md`, not a new skill, as the
Goal section required.

**Three claims in this phase's own planning were wrong. The docs corrected
the first two during Task 4, and the Task 8 runtime probe corrected the
third (R5):**

- **Right-to-left layout does not need manual handling for reserved
  regions.** The brief said a manual layout MUST account for right-to-left,
  because region frames sit in a fixed coordinate space. The SDK default,
  `layoutDirectionBehavior: ... = .mirrors`, mirrors each frame into the
  view's layout direction instead. A custom `Layout` written in leading and
  trailing terms needs no right-to-left code as a result. Only `.fixed`
  returns physical frames, and then the caller owns the flip. Corrected in
  `adaptive-layout.md:51` and recorded in
  `task-4-reference/task-4-report.md:65-73`.
- **Floating controls align to the same edge as the vertical bar, not the
  opposite one.** The plan's first version placed custom bars and floating
  controls on the edge opposite the toolbar's vertical bar. Apple's own
  example aligns the control to the *same* edge instead. The controller's
  Ruling 9 withdrew the unsourced rule. `adaptive-layout.md:209` now states
  the sourced one, and `FloatingPaletteHost` (`:189-207`) aligns to
  `barEdge` rather than its opposite. Evidence:
  `task-4-reference/task-4-report.md:191-197` (fix round 1, issue 3).
- **The default `reservedRegions` query omits inactive regions.** The
  `ReservedRegion` doc page reads as if the default query always returns
  every intersecting region. Runtime says no: on a fully open device the
  default query returns no fold. `.includeInactive` is needed to see it,
  with `isActive: false`. `adaptive-layout.md:41` now states the runtime
  behavior and keeps the "always check `isActive`" rule. Evidence:
  `task-8-probe/results.md:41` (R5). The pre-runtime reading that flagged
  the conflict is at `task-7-compile/task-7-report.md:74-81`.

One deviation from the design spec's Deliverables §4 was decided in
planning, not found wrong at runtime. The spec asked for preamble bindings
for both `GeometryProxy` and `UIView` fragments. Only `GeometryProxy` was
added — rebinding `view` would have broken snippets that depend on `view:
__View`. The reference ships no UIKit snippets. UIKit names are verified by
SDK header and interface search instead (Task 7), not by compiling a bound
fragment. Evidence: `docs/plans/2026-09-30-phase9-adaptive-layout.md:27`.

### 4. Snippet ship gate, repo-wide — PASS, with an environment regression caught and fixed
Repo-wide (51 reference files, Task 2's own edits, no `adaptive-layout.md`
yet), the gate moved **31/51 → 32/51**. One FAIL → PASS flip; zero PASS →
FAIL flips. The flip is
`apple-intelligence/references/app-intents-implementation.md` snippet #3
(`IntentDefinitions`). Ruling 7 fixed it: the hardcoded `Xcode-beta.app`
macOS framework search path no longer exists on this machine. The gate now
derives it from `xcrun --sdk macosx --show-sdk-platform-path` instead. Per
Ruling 3, a FAIL → PASS flip is recorded, not treated as a regression
needing a fix. Evidence: `task-2-typecheck/catalog-diff.log:1-20`.

This also means the 32/51 baseline from Phase 7 had silently regressed to
31/51 between phases. The cause was an environment change, the beta
Xcode's bundle name, not a code edit. Task 2 caught it only by chance,
while re-deriving the path. No action is needed beyond the fix. The
catalog-wide total is not this phase's gate; the `apple-design`-scoped one
is. `docs/deferred.md` item 7 tracks the untriaged count separately.

`apple-design`'s own subset moved from the Finding-4 baseline of **2/4** to
**4/4** at Task 3. Both `accessibility.md` failures were framing artifacts,
each paired with a reference defect: a deprecated `accentColor`, and an
`AnyView` in a ternary. Task 3 triaged and fixed both, per `docs/deferred.md`
item 7's rule. The item now records 17 untriaged failures left, none in
`apple-design`. Evidence:
`task-3-a11y/typecheck.log:24` (`TOTAL: 4/4`), `task-3-a11y/triage.md`,
`docs/deferred.md:478-486`.

### 5. `docc.py` offline test and `test_run_evals.sh` — PASS
`pipeline/test_docc.py` passes offline against a fixture JSON, confirmed in
this task's own gate run. Three live checks back it: emphasis/strong/
newTerm nodes now render (`represent an *arrangement view*,` rather than a
gap), `--hig designing-for-iphone-duo` reaches a real HIG page, and a
deprecation now prints (`DEPRECATED: iOS 27.2`). `test_run_evals.sh`'s
four offline cases (12 assertions) pass, confirmed again in this task's run.
Evidence: `task-1-docc/task-1-report.md:71-84`; `task-9-release/gates.log`,
Gates 2 and 4.

### 6. R1–R7 runtime verdicts — PASS (R1–R4), with three claims extended beyond the spec's four
The spec asked for four behavioral claims. Each one needed runtime evidence,
or the "documented, not runtime-checked" marker. All four shipped
CONFIRMED. Task 8 added three more (R5–R7) that the implementation needed
along the way. At Task 9, `adaptive-layout.md`'s header note named only
R1–R4, and R5–R7 carried their own inline citations. The final review fix
wave extended the note to R1–R7 (`adaptive-layout.md:4`) and labeled each
inline citation with its claim.

| Claim | Verdict | Evidence |
|---|---|---|
| R1. Vertical bar on the outer display in every orientation, and on the inner display in landscape only. | CONFIRMED. | `task-8-probe/results.md:37` |
| R2. A title-only item never appears in a vertical bar. | CONFIRMED, by re-probe. | `task-8-probe/results.md:38` |
| R3. The fold region is active only when the device is partly open. | CONFIRMED. | `task-8-probe/results.md:39` |
| R4. An outer-display sheet gets vertical bars by default. `toolbarVerticalBehavior(_:)` disables them. | CONFIRMED. | `task-8-probe/results.md:40` |
| R5. Does the default `reservedRegions` query include inactive regions? | The SDK-header reading holds, not the doc page's. | `task-8-probe/results.md:41` |
| R6. Do `.secondaryAction` items start in the overflow menu? | Yes, on both displays. | `task-8-probe/results.md:42` |
| R7. Does `visibilityPriority` change what stays in the vertical bar? | Yes for primary-action items. No visible effect for secondary-action items. | `task-8-probe/results.md:43` |

R2's first walk was confounded. Both items were `.secondaryAction`, and
both went to the overflow menu regardless of a symbol. It never tested the
claim. The re-probe moved both to `.primaryAction` and settled it.

R7 was added after the `MessageDetail` snippet taught a
`visibilityPriority` with no observed effect. The probe measured it before
the snippet shipped. It found priority inert on `.secondaryAction` items.
The snippet was rewritten to put Reply and Flag on `.primaryAction`
instead. Evidence: `task-8-probe/task-8-report.md:103-129` (fix round 1).

**Discovery was class B, not class A.** `simctl` and `devicectl` can
create, boot, and launch the Duo simulator. Neither exposes a pose or
rotation command. Device Hub set every pose and rotation by hand, so the
probe cannot run unattended. The probe also did not cover `landscapeLeft`,
right-to-left layouts, or the camera occlusion regions. `unified.log` shows
only transient `leading`-edge readings during launches and pose changes,
never a settled one. Recorded as `docs/deferred.md` item 17, with a
command-line-pose trigger. Evidence: `task-8-probe/discovery.log`,
`task-8-probe/results.md:55` (the transient-edge note),
`docs/deferred.md:843-853`.

### 7. Trigger evals: both pass rates reported, fixture clean — PARTIAL
The mechanical requirement is met: both sweeps ran through
`pipeline/run_evals.py`, and both pass rates are reported here. The verdict
is PARTIAL rather than PASS because the gap the sweep measured is still
open, and a clean-sounding verdict would bury that.

**Baseline, description unchanged: 11/16.** Should-fire 6/10 — `fire-1`
through `fire-6` pass, all four Duo rows (`fire-7`–`fire-10`) fail.
Should-NOT 5/6 — `nofire-1` ("Design our brand color palette") fails, the
pre-existing Phase 8 finding, unrelated to Duo. Three of the four Duo
failures are genuine routing misses: `fire-7`, `fire-8`, `fire-10`. The
fourth, `fire-9`, is a prompt-wording defect, not a routing miss — the
model reads "gets cut off" as a claim about its own message. This
reproduced outside the fixture and outside the harness.

**A description edit was tried and reverted.** The edit fixed `fire-7` and
`fire-8`. It regressed two previously-passing rows. `nofire-6` ("What
screenshot sizes does the App Store need for iPhone Duo?") started calling
`apple-design`, before self-correcting to `app-release`. `fire-5` stopped
calling any skill at all. Post-edit also scored 11/16, not the same
11. Per the project's own revert rule, a regression on a previously-passing
row reverts the edit; `SKILL.md` carries no diff from before the edit.
`docs/deferred.md` item 13 stays open, with `fire-7`, `fire-8`, and
`fire-10` as genuine Duo routing misses and `nofire-1` as the pre-existing
one — none fixed this phase. Evidence: `task-6-evals/prompts.tsv`,
`task-6-evals/baseline/results.tsv:1-17`,
`task-6-evals/after-edit/results.tsv:1-17`,
`task-6-evals/classification.md:9-183`, `docs/deferred.md:684-730`.

`git -C ~/Projects/StudioFixture status --porcelain` is empty at close,
confirmed in this task's own gate run (Gate 10). Both sweeps wrote to the
fixture — the guard attributed every write to its prompt and restored the
tree each time.

### 8. `bun test`, `bun run audit`, `bun run audit --since main` — PASS
`bun test`: 198 pass, 0 fail, 429 `expect()` calls. `bun run audit`: 0
errors, 55 warnings — all pre-existing, none newly introduced by this
phase's files. `bun run audit --since main` reports no unbumped plugin:
`apple-studio` carries commits since `main` and its version moved 0.9.1 →
0.10.0 in the same working tree the check reads. Evidence:
`task-9-release/gates.log`, Gates 5–7.

### 9. `claude plugin validate . --strict` and the plugin load check — PASS
Clean: `✔ Validation passed`. The `--plugin-dir` load check (non-deterministic
by the brief's own description) named `adaptive-layout.md` among
`apple-design`'s reference files on this run. Version moved in
`plugins/apple-studio/.claude-plugin/plugin.json` only, from 0.9.1 to
0.10.0. The description gained "adaptive layout across sizes, poses, and
foldables" in both `plugin.json` and `.claude-plugin/marketplace.json`. The
marketplace file carries no `version` key. Evidence:
`task-9-release/gates.log`, Gates 8–9.

### 10. No simulator left booted — PASS
`xcrun simctl list devices booted` lists no device, checked at the close of
Task 8 and again in this task's own gate run. Evidence:
`task-8-probe/task-8-report.md:70-75`; `task-9-release/gates.log`, Gate 11.

### Carried forward
- **`docs/deferred.md` item 7**: 17 untriaged snippet failures remain,
  across 12 files, none in `apple-design`. Trigger unchanged: triage in the
  next phase.
- **Item 12** is closed: Task 8 rewrote the `~/Projects/StudioFixture`
  citation in `headless-commands.md`.
- **Item 13** stays open: three genuine Duo routing misses
  (`fire-7`, `fire-8`, `fire-10`) and one pre-existing brand-color miss
  (`nofire-1`). A new trigger asks for a fix that does not pull
  `apple-design` ahead of `app-release` on Duo-adjacent release-logistics
  questions. **Superseded by the Task 10 addendum below:** item 13 is
  resolved for the Duo should-fire rows, and only `ad-nofire-1` stays
  open.
- **New items 14–17.** Item 14 asks to re-verify every 27.1 claim at GA.
  Item 15 is a camera primer for direction-aware capture, out of this
  phase's scope. Item 16 is App Store Connect upload support for Duo
  screenshots. Item 17 records that iPhone Duo pose control is GUI-only,
  which left `landscapeLeft`, right-to-left layouts, and the camera
  occlusion regions unprobed.
- **Item 18**, added in the final review fix wave: `docc.py` does not
  render `termList` nodes, and its `table` branch leaks blank lines.
- **ML remains the charter's one outstanding long-tail item**, on-demand
  rather than scheduled, per the amendment in item 2 above.

### Addendum (2026-10-01, Task 10): Duo routing

Task 9's Gate 7 verdict was PARTIAL. Three genuine Duo routing misses
(`fire-7`, `fire-8`, `fire-10`) and the pre-existing brand-color miss
(`nofire-1`) were open. A single-run description edit had already been
tried, and reverted for a regression on one sample. Task 10 tried the fix
again, with a sweep protocol the single run lacked. It ran three runs per
row, applied a mechanical hold threshold, and re-ran the baseline for
every candidate regression before deciding.

**Protocol.** `apple-design` and `app-release` each received a revised
description. `apple-design` gained Duo/pose/fold wording and an App Store
screenshots exclusion; `app-release` gained an "App Store screenshots and
metadata" clause. `triggers.md` changed in both skills. `apple-design`'s
`fire-9` row was reworded from "Content gets cut off at the fold" to "Part
of my list is hidden where the screen folds". The old wording is a
prompt-corpus defect, not a routing question, per
`task-6-evals/classification.md:57-116`. `app-release` gained a
should-fire row with the text of `apple-design`'s existing should-NOT row,
"What screenshot sizes does the App Store need for iPhone Duo?" All 28
rows of both files ran three times through `pipeline/run_evals.py`
against the revised descriptions (`task-10-routing/run-1`..`run-3`). A
row holds at 2 of 3 PASS or better.

**Result.** All four Duo should-fire rows held at 3/3:
`task-10-routing/tally.md:10-13,38-41` (`ad-fire-7`, `ad-fire-8`,
`ad-fire-9`, `ad-fire-10`), against 0 of 4 at the Task 6 baseline. One
other row failed to hold: `ad-fire-5` ("Add a confirmation flow before
deleting"), 1/3 PASS (`task-10-routing/tally.md:8`). It is neither a Duo
row nor the pre-existing brand-color miss. A three-run baseline re-run,
against the pre-Task-10 descriptions in a worktree at `9f3c3a6`, scored
3/3 PASS for the same row (`task-10-routing/tally.md:43-48`).

**First-pass error, corrected.** The initial decision called `ad-fire-5`
a confirmed regression with no viable revision, and reverted both
description edits without running Step 6's revision round. A review found
this wrong. All six `ad-fire-5` sessions, across the original sweep and
the baseline re-run, show the same tool access and the same opening
`Bash`/`Read` sequence. That condition is constant across passes and
fails alike. It cannot be what explains the split between them.
"Tool-permission leak" is not one of `.claude/rules/eval-harness.md`'s
three categories.

The two failing sessions are routing misses
(`task-10-routing/run-1/ad-fire-5.log`, `run-2/ad-fire-5.log`). The model
chose `Bash`/`Edit` over `Skill` with turns still in budget. One session
even named "HIG for destructive actions" in its own plan text, without
ever consulting the skill that owns that guidance.

Pooled across both Duo-wording tries to date, the original description
scored 4/4 on this row. That total is Task 6's baseline, plus Task 10's
three-run baseline. The two Duo-heavy edits scored 1/4 on the same row.
That total is Task 6's single post-edit run, plus Task 10's first
post-edit sweep. The split is too wide to call noise. At the time, no
`apple-design` reference covered confirmation before a destructive
action; `references/hig-patterns.md` § Modality covered alerts in
general. The final review fix wave added that guidance to § Modality.
Neither edit's description named confirmation dialogs, and both pushed
"navigation and modality patterns" further back. Step 6's revision round
applied and had not been tried.

**Revision round.** `apple-design`'s description was revised to name
"confirmation dialogs before destructive actions" in its modality clause
and add a matching "Use when" trigger. `app-release`'s description
returned to its Step 2 text. The rows touching either skill's revised
wording or boundary — the 16 `ad-*` rows, plus `ar-fire-8` and
`ar-nofire-3` — were swept three more times
(`task-10-routing/run-rev-1`..`run-rev-3`). All 18 rows held at 2 of 3 or
better (`task-10-routing/tally.md:50-79`). `ad-fire-5` held 3/3
(`tally.md:57`). All four Duo rows held 3/3 (`tally.md:59-62,76-79`).
`ad-nofire-1` improved to 2/3 (`tally.md:63`), though it stays open under
the brief's standing exception. No candidate regression exists in the
revision round.

**Decision: KEEP.** No confirmed regression remains, and all 4 of 4 Duo
rows hold (the rule requires at least 1). The revised `apple-design`
description and the Step 2 `app-release` description ship.
`docs/deferred.md` item 13 is resolved for the Duo should-fire rows;
`nofire-1` (the pre-existing brand-color miss) stays open under its
existing wording.

This supersedes Gate 7's PARTIAL verdict. The Duo routing gap that Task 9
measured is closed for `ad-fire-7`, `ad-fire-8`, `ad-fire-9`, and
`ad-fire-10`, and `ad-fire-5` no longer regresses. Evidence:
`records/2026-09-30-phase9-adaptive-layout/task-10-routing/`
(`prompts.tsv`, `run-1/`..`run-3/`, `run-rev-1/`..`run-rev-3/`,
`baseline-ad-fire-5-1/`..`-3/`, `tally.py`, `tally.md`,
`task-10-report.md`).
