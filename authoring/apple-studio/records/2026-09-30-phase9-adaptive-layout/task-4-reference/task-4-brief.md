### Task 4: Distillation map, `adaptive-layout.md`, and `apple-design` routing

**Files:**
- Create: `$AS/pipeline/maps/apple-design-duo-live.md`
- Create: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`
- Modify: `plugins/apple-studio/skills/apple-design/SKILL.md:15` (routing line)
- Modify: `plugins/apple-studio/skills/apple-design/references/platform-idioms.md:1-7,49,83-93`
- Modify: `plugins/apple-studio/skills/apple-design/references/hig-patterns.md:1,31`
- Modify: `$AS/CONVENTIONS.md:48-49` (file-count rule)

**Interfaces:**
- Consumes: `docc.py --hig` (Task 1); the `> typecheck: ios 27.1` directive (Task 2).
- Produces: `adaptive-layout.md` with section anchors `## What layout reads`, `## System containers first`, `## Reserved regions`, `## Arrangement views`, `## Bars that adapt to space`, `## Games`, `## Checking a layout on iPhone Duo`, `## Maintaining older code: UIKit equivalents`. Task 7 compiles it; Task 8 fills its runtime citations; Task 5 and Task 8 link to its sections by these names.

- [ ] **Step 1: Write the distillation map.** Create `$AS/pipeline/maps/apple-design-duo-live.md` listing, one per line, the seed pages with the `docc.py` invocation for each:
  - `--hig designing-for-iphone-duo`, `--hig layout`, `--hig toolbars`, `--hig split-views`
  - `technologyoverviews/preparing-your-app-for-iphone-duo`
  - SwiftUI: `swiftui/reservedregion`, `swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:)`, `swiftui/arrangementview`, `swiftui/view/arrangementviewstyle(_:)`, `swiftui/environmentvalues/toolbarverticaledge`, `swiftui/view/toolbarverticalbehavior(_:)`, `swiftui/view/toolbarverticalcompressionbehavior(_:)`, `swiftui/toolbarcontent/axisbehavior(_:)`, `swiftui/toolbarcontent/visibilitypriority(_:)`, `swiftui/toolbaroverflowmenu`, `swiftui/toolbaritemplacement/topbarpinnedtrailing`, `swiftui/view/presentationplacement(_:)`, `swiftui/view/backgroundextensioneffect()`
  - UIKit: `uikit/uiarrangementviewcontroller`, `uikit/uiview/reservedregion`, `uikit/uiview/reservedregions(kind:options:)`, `uikit/uitraitcollection/verticalbaredge`, `uikit/uiviewcontroller/preferredverticalbarbehavior`, `uikit/uinavigationitem/pinnedtrailinggroup`, `uikit/uinavigationitem/additionaloverflowitems`, `uikit/uibarbuttonitem/axisbehavior-swift.property`, `uikit/uibarbuttonitem/visibilitypriority`, `uikit/uisheetpresentationcontroller/preferredplacement`, `uikit/uibackgroundextensionview`, `uikit/uiverticalbarcompressionbehavior`
  - `xcode/device-hub`, `avkit/choosing-a-camera-by-the-direction-it-faces`, `avfoundation/registering-a-camera-capture-accessory-on-iphone-duo`
  - App Store Connect screenshot specifications (WebFetch; see `survey/screenshot-specifications.txt`)

  Run each through `docc.py` (the ones with `(` need quoting), writing output to the session scratchpad, **not** the repo. Any that fail: add a `MISSING: <path> — <error>` line to the map.

- [ ] **Step 2: Amend the file-count rule.** In `$AS/CONVENTIONS.md`, replace lines 48–49:

```markdown
- Location: `plugins/apple-studio/skills/<skill>/references/<topic>.md`, one file per
  decision area, a few hundred lines each. Most skills need 3–6. A reference file MUST NOT
  be named for a device; name it for the decision it serves. (Amended 2026-09-30,
  Phase 9: iPhone Duo guidance lives in `apple-design/references/adaptive-layout.md`,
  because its APIs are documented for every platform.) Not book summaries —
  decision-grade guidance only.
```

- [ ] **Step 3: Write the header and sections 1–2 of `adaptive-layout.md`.** Header (fill the month and SDK build when Task 7 compiles):

```markdown
> verified: 2026-09 against https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo, https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo, <every other URL fetched in Step 1 that this file cites>; compiled against iPhoneOS 27.1 SDK (<build>)
> sources: live HIG and developer documentation (DocC JSON)
> typecheck: ios 27.1
> note: iPhone Duo APIs are iOS 27.1 beta as of 2026-09. Re-verify at 27.1 GA (docs/deferred.md). Behavioral claims R1–R4 cite runtime evidence in records/2026-09-30-phase9-adaptive-layout/task-8-probe/.
```

Then `# Adaptive Layout`, a two-sentence opening (this file owns layout that survives any size, shape, or pose; iPhone Duo is the hardest case, iPad windowing and iPhone Mirroring the familiar ones), and:

  - `## What layout reads` — must state, in our own words: layout decisions read size classes and the scene's or container's bounds; never `userInterfaceIdiom`, interface orientation, or screen dimensions (developer page); size views relative to their container. Move in, rewritten to fit, the content of `platform-idioms.md:85-93` (containers adapt; `horizontalSizeClass` over `#if os`). State the fluid-layout rule generally (arbitrary widths, not breakpoints) and note iPad windowing and Duo poses as two sources of it. Duo specifics: outer display is compact width, inner display regular width; together they cover every pose (HIG § Device poses). Don't redesign on resize — let the existing layout expand.
  - `## System containers first` — `NavigationSplitView` collapses on the outer display and expands on the inner, as between compact and regular elsewhere; split views adjust column width and margins to the fold; alerts, context menus, and sheets move off the fold on their own. Mail as the "one more level of hierarchy on the larger display" example (HIG § Best practices). Keep functionality and state identical across displays and poses.

- [ ] **Step 4: Write section 3, `## Reserved regions`.** Must state: two kinds, `occlusion` (hardware covers content) and `division` (the fold splits a view); a region is active or inactive and the query returns intersecting regions; `includeInactive` exists to also see inactive ones; Duo's three regions (outer camera always, inner camera only while the camera runs, fold only when partly open); iPad window controls as the familiar precedent; frames are in a fixed coordinate space, so a manual layout MUST account for right-to-left (`layoutDirectionBehavior`), while a custom `Layout` mirrors for you; prefer even column counts; favor small moves over rearrangement. Ship this snippet:

```swift
struct LiveBadgeOverlay: View {
    var body: some View {
        GeometryReader { proxy in
            let cameraRegions = proxy.reservedRegions(kind: .occlusion)
            let topTrailingBlocked = cameraRegions.contains { region in
                region.frame.minY < 80 && region.frame.maxX > proxy.size.width - 160
            }
            Text("Live")
                .padding(8)
                .background(.thinMaterial, in: .capsule)
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity,
                       alignment: topTrailingBlocked ? .bottomTrailing : .topTrailing)
        }
    }
}
```

   Prose after it: this is the manual fallback; system components already avoid regions, so reach for this only in a custom view.

- [ ] **Step 5: Write section 4, `## Arrangement views`.** Must state: primary plus secondary view; `split` puts them side by side when wider than tall and stacked when taller, adjusting around the fold; `overlay` layers primary over secondary when no division is active, and moves them to either side of the fold when partly open; the default style resolves to split; constrain axes with `axes(_:)`; `HStack`/`VStack` layouts map to split, `ZStack` to overlay; navigation containers go around an arrangement view, never inside; never put one inside a `List`, `ScrollView`, or `NavigationSplitView`. Ship:

```swift
struct TrackDetail: View {
    var body: some View {
        ArrangementView {
            Text("Now playing")
        } secondary: {
            Text("Lyrics")
        }
        .arrangementViewStyle(.split.axes(.horizontal))
    }
}
```

   One sentence: with `.axes(.horizontal)`, a tall container shows only the primary view.

- [ ] **Step 6: Write section 5, `## Bars that adapt to space`.** Must state:
  - Where bars go vertical: the outer display in every orientation; the inner display in landscape; not the inner display in portrait (HIG § Vertical controls). They stay on the hardware side in right-to-left languages. In Split View multitasking each app puts its bar on its outer edge.
  - Context rules (developer page): inspectors horizontal; in a multi-column split view, sidebar and content bars horizontal and detail bar vertical; sheets on the outer display vertical by default; sheets on the inner display horizontal for centered or leading placement and vertical for trailing.
  - Getting it for free: attach `toolbar(content:)` to a `NavigationStack` or `NavigationSplitView`; a custom bar view gets none of this.
  - Order: primary navigation (Back, Close) at the top, then prominent actions (Done), then the remaining groups in their original grouping.
  - Every item gets a title and a symbol: vertical uses the symbol, horizontal prefers the symbol, overflow uses both; a title-only item or a custom-view item never goes vertical. Keep text buttons rare.
  - Overflow: items overflow bottom-to-top by default; set `visibilityPriority(_:)` on groups first, then items; keep frequent actions and badged items visible longest; move any home-made overflow menu into `ToolbarOverflowMenu`; reserve the ellipsis symbol for overflow.
  - Compression: navigation-focused views keep the tab bar and overflow toolbar items (default); task-focused views keep toolbar items with `.prefersToolbarItems`.
  - Opting out: `toolbarVerticalBehavior(.disabled)` only for full-screen media or non-scrolling layouts like a calculator; don't override placement otherwise. `presentationPlacement(_:)` picks a sheet's side. `axisBehavior(_:)` restricts one item.
  - Custom views read `toolbarVerticalEdge` (nil where no vertical bar is ever used) and extend hero images under the bar with `backgroundExtensionEffect()`.
  - Full-width layouts for non-scrolling immersive screens, clear of the Dynamic Island and status bar (Calculator example). Keep controls near the content they affect (Mail's list controls stay over the list).

   Ship these two snippets:

```swift
struct MessageDetail: View {
    var body: some View {
        NavigationStack {
            Text("Message body")
                .navigationTitle("Message")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close", systemImage: "xmark") {}
                    }
                    ToolbarItem(placement: .topBarPinnedTrailing) {
                        Button("Done", systemImage: "checkmark") {}
                    }
                    ToolbarItem(placement: .secondaryAction) {
                        Button("Reply", systemImage: "arrowshape.turn.up.left") {}
                    }
                    .visibilityPriority(.high)
                    ToolbarItem(placement: .secondaryAction) {
                        Button("Flag", systemImage: "flag") {}
                    }
                    .visibilityPriority(.low)
                    ToolbarOverflowMenu {
                        Button("Print", systemImage: "printer") {}
                    }
                }
                .toolbarVerticalCompressionBehavior(.prefersToolbarItems)
        }
    }
}
```

```swift
struct FloatingPaletteHost: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        Image(systemName: "paintpalette")
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity,
                   alignment: barEdge == .leading ? .bottomTrailing : .bottomLeading)
    }
}
```

   Prose after the second: place custom floating controls on the edge opposite the vertical bar.

- [ ] **Step 7: Write sections 6–8.**
  - `## Games` — lock orientation if needed but fill the screen in every pose; keep text and control sizes steady; change the aspect ratio rather than letterbox; if letterboxing is unavoidable, fill the padding with artwork. Link the HIG games page.
  - `## Checking a layout on iPhone Duo` — a checklist: both displays; closed, open, partly folded; rotate each pose; every view, sheet, and popover; bars on the side; nothing important in the fold. Build with the current Xcode: apps built with Xcode 26 or earlier do not extend under the status bar and camera. Preview poses in Xcode's Device Hub; capture them per `xcode-loop` (Task 8 adds that section). Camera apps: one sentence pointing to Apple's "Choosing a camera by the direction it faces" and "Registering a camera capture accessory on iPhone Duo", noting a camera may face the other way after the device opens or closes.
  - `## Maintaining older code: UIKit equivalents` — a two-column table mapping each SwiftUI API named above to its UIKit counterpart: `ArrangementView`→`UIArrangementViewController`; `reservedRegions(kind:options:layoutDirectionBehavior:)`→`UIView.reservedRegions(kind:options:)`; `toolbarVerticalEdge`→`UITraitCollection.verticalBarEdge`; `toolbarVerticalBehavior(_:)`→`UIViewController.preferredVerticalBarBehavior`; `toolbarVerticalCompressionBehavior(_:)`→`UIVerticalBarCompressionBehavior`; `topBarPinnedTrailing`→`UINavigationItem.pinnedTrailingGroup`; `cancellationAction`→`UINavigationItem.leadingItemGroups`; `axisBehavior(_:)`→`UIBarButtonItem.axisBehavior`; `visibilityPriority(_:)`→`UIBarButtonItem.visibilityPriority`; `ToolbarOverflowMenu`→`UINavigationItem.additionalOverflowItems`; `presentationPlacement(_:)`→`UISheetPresentationController.preferredPlacement`; `backgroundExtensionEffect()`→`UIBackgroundExtensionView`. Plus two rules in prose: set items on a view controller inside a navigation controller rather than building a `UIToolbar`/`UINavigationBar`/`UITabBar` yourself; use automatic trait tracking and Auto Layout. No UIKit snippets; Task 7 verifies every UIKit name by header search.

- [ ] **Step 8: Rewire `apple-design`.**
  - `SKILL.md`: insert after the line `- iPhone vs iPad vs Mac in one codebase → \`references/platform-idioms.md\``:
    `- Layout across sizes, poses, and foldables (iPhone Duo), reserved regions, bars that move to the side → \`references/adaptive-layout.md\``
  - `platform-idioms.md`: replace lines 85–93 (from "SwiftUI's structural containers already handle…" through the `horizontalSizeClass` paragraph) with: `Layout shape — containers that adapt, size classes over platform checks, fluid widths — lives in \`adaptive-layout.md\` § What layout reads. What follows is the other half: the capabilities that genuinely differ by platform.` Keep the "Genuine reasons to branch" list and the closing paragraph. In line 49, change "build fluid layout, not fixed breakpoints" to end with "(see `adaptive-layout.md` § What layout reads)". In the file's opening paragraph (line 7), change "see the "When to branch" section for the boundary…" to point at `adaptive-layout.md` for layout shape. Add `re-checked 2026-09 (Phase 9: layout-shape content moved to adaptive-layout.md)` to its `verified:` line.
  - `hig-patterns.md`: after line 31 `(HIG: Tab Bars)`, add a paragraph: `Where bars move to a vertical edge — iPhone Duo's outer display and landscape inner display — item order, overflow, and toolbar-versus-tab-bar compression are in \`adaptive-layout.md\` § Bars that adapt to space.` Add `re-checked 2026-09 (Phase 9: pointer to adaptive-layout.md)` to its `verified:` line.

- [ ] **Step 9: Check the content requirements.** Run and save to `task-4-reference/checks.log`:

```bash
R=plugins/apple-studio/skills/apple-design/references/adaptive-layout.md
wc -l $R                                           # expect 200-300
grep -ci "right-to-left" $R                        # expect >= 2 (reserved regions, bars)
grep -c '^## ' $R                                  # expect 8
grep -n "userInterfaceIdiom" $R                    # expect a "never" rule
grep -rn "When to branch" plugins/apple-studio/skills/apple-design/   # no stale "see When to branch" pointers
vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini $R
```

   Reference prose is R1-E register: fix Vale warnings except where a warning conflicts with an API name.

- [ ] **Step 10: Typecheck what the 27.0 SDK can check.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md`. Expected on the 27.0 SDK: exit 2 with `installed iPhoneOS SDK 27.0 is older than the directive ios 27.1` for `adaptive-layout.md` and 4/4 for the rest. That exit is correct, not a failure of this task: Task 7 owns the 27.1 compile. Save the output to `task-4-reference/typecheck-27.0.log`.

- [ ] **Step 11: Run the catalog gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add $AS/pipeline/maps/apple-design-duo-live.md $AS/CONVENTIONS.md plugins/apple-studio/skills/apple-design $AS/records/2026-09-30-phase9-adaptive-layout/task-4-reference
git commit -m "Phase 9 Task 4: adaptive-layout reference and apple-design routing

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

