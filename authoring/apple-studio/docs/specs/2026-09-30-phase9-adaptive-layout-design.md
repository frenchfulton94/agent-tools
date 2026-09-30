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

- Every ```swift block MUST typecheck under the `ios 27.1` directive.
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
