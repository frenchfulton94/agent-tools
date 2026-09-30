# Task 4 report: distillation map, `adaptive-layout.md`, and `apple-design` routing

Status: DONE. Date: 2026-09-30. Branch: `phase9-adaptive-layout`.

## Pages fetched

Every Step 1 seed was fetched with `pipeline/docc.py`. Output went to the session scratchpad, not
the repository. All seeds returned DocC JSON 200.

- HIG: `designing-for-iphone-duo`, `layout`, `toolbars`, `split-views`, and
  `designing-for-games` (followed from the Duo page for § Games).
- MISSING: `--hig games` returned HTTP 404. The real slug is `designing-for-games`. The map records
  both.
- Developer overview, 13 SwiftUI pages, 12 UIKit pages, `xcode/device-hub`, and both camera
  articles: all 200.
- App Store Connect screenshot specifications: WebFetch succeeded. The sizes and the "upload
  support later this year" note match `survey/screenshot-specifications.txt`. Task 5 consumes
  this page; the reference does not.
- Thin pages: `uisheetpresentationcontroller/preferredplacement` has no abstract or discussion.
  `uiverticalbarcompressionbehavior` has only an abstract.
- `docc.py` rendering gap: the `ReservedRegion` and `UIView.ReservedRegion` pages hold a DocC
  `termList` node, which `docc.py` does not render. The output reads "There are two categories of
  reserved regions:" and then nothing. I read the raw JSON directly. It defines `occlusion` as
  "Dynamic Island, a camera, or window controls" and `division` as the fold. The map records this
  gap. It is a candidate follow-up for `docc.py`, outside this task.

## Snippet corrections

None were needed. The brief's four snippets compiled unchanged against the iPhoneOS 27.1 SDK
(Xcode 27.1 beta; `xcrun --show-sdk-build-version` reports `24A94403`). The gate then reported
**8/8 clean**: the 4 existing snippets and the 4 new ones (`typecheck-27.1.log`).

A negative control confirmed that the iOS directive catches invented API:
`.toolbarVerticalBehavior(.alwaysVertical)` failed with "type 'ToolbarVerticalBehavior' has no
member 'alwaysVertical'".

Every symbol that the reference names in prose was checked against the 27.1 SDK interface or
headers. No symbol is documented but absent. Key interface lines:

- `SwiftUICore.swiftinterface`: `public func reservedRegions(kind: ReservedRegion.Kind, options:
  ReservedRegion.QueryOptions = [], layoutDirectionBehavior: LayoutDirectionBehavior = .mirrors)`.
  `ReservedRegion` has `id`, `kind`, `frame`, `margins`, and `isActive`. `Kind` has `occlusion`
  and `division`. `QueryOptions` has `includeInactive`.
- `ArrangementView.init(primary:secondary:)`, `arrangementViewStyle(_:)`, the
  `.split`/`.overlay`/`.automatic` styles, and `axes(_ axes: Axis.Set)` on the split and overlay
  styles. `toolbarVerticalEdge: HorizontalEdge?`.
- `SwiftUI.swiftinterface`: `ToolbarVerticalBehavior` has `.automatic` and `.disabled`.
  `ToolbarVerticalCompressionBehavior` has `.automatic`, `.prefersToolbarItems`, and
  `.prefersTabBar`. `ToolbarItemAxisBehavior` has `.automatic`, `.horizontalOnly`, and
  `.verticalPreferred`. `ToolbarItemVisibilityPriority` has `.automatic`, `.low`, `.high`,
  `init(lowerThan:)`, and `init(higherThan:)`. Also present: `ToolbarOverflowMenu`,
  `topBarPinnedTrailing`, `presentationPlacement(_:)`, and `backgroundExtensionEffect()`.
- UIKit headers: `UINavigationItem.h:312`
  `@property UIVerticalBarCompressionBehavior verticalBarCompressionBehavior`. Also:
  `UIViewController.h:837` `preferredVerticalBarBehavior`, `UIVerticalBarEdge.h:33`
  `verticalBarEdge`, `UIBarButtonItem.h:170,179` `visibilityPriority`/`axisBehavior`,
  `UINavigationItem.h:231,239,242` `leadingItemGroups`/`pinnedTrailingGroup`/
  `additionalOverflowItems`, `UISheetPresentationController.h:120` `preferredPlacement`,
  `UIBackgroundExtensionView.h:21`, and `UIView.h:760-763` `reservedRegionsOfKind:options:`
  (Swift: `reservedRegions(kind:options:)`). The Swift interface has
  `UIArrangementViewController.updateArrangement(_:animated:)`.

## Docs-versus-brief contradictions (the docs won)

1. **Right-to-left and reserved regions (§ Reserved regions).** The brief says that frames are in
   a fixed coordinate space, so a manual layout MUST handle right-to-left through
   `layoutDirectionBehavior`, while a custom `Layout` mirrors for you. The docs, and the SDK
   default `layoutDirectionBehavior: ... = .mirrors`, say otherwise. The hardware is fixed, but
   the API mirrors region frames into the view's layout direction by default. As a result, a
   custom `Layout` and a check written in leading and trailing terms need no right-to-left code.
   Only `.fixed` returns physical frames, and then the caller owns the flip. The reference states
   the documented behavior. The prose after the badge snippet also explains why its trailing check
   is correct in right-to-left languages.
2. **Which regions the query returns by default.** The brief says that the query returns the
   intersecting regions and that `includeInactive` also returns inactive ones. The SwiftUI and
   UIKit overview pages say that the query returns every intersecting region "regardless of
   whether they are currently active". The SDK header `UIViewReservedRegion.h` documents
   `UIViewReservedRegionQueryOptionsIncludeInactive` as "Include inactive reserved regions", which
   implies that the default query excludes them. The reference follows the SDK option, says that
   the sources disagree, and tells readers to always check `isActive`. Task 8 could settle this at
   runtime.
3. **Header URL form.** The brief's header cites the developer page as
   `https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo`.
   The test `tests/apple-doc-links.test.ts` requires every page-form documentation link in
   apple-studio to end in `.md`, so `bun test` failed. I changed the URL to the `.md` form, which
   `curl` confirmed as `200 text/markdown`. HIG URLs are outside that test's pattern. Task 7 must
   also use `.md` forms for any `developer.apple.com/documentation/` URL that it adds to the
   placeholder list.
4. **UIKit compression mapping.** The brief maps `toolbarVerticalCompressionBehavior(_:)` to
   `UIVerticalBarCompressionBehavior`, which is an enum. The setter is
   `UINavigationItem.verticalBarCompressionBehavior` (`UINavigationItem.h:312`). The table cell
   gives both.
5. **Additions beyond the brief, sourced from the docs:** the overlay sides (the primary view goes
   to the trailing or bottom side); the `.automatic` default resolving to split; the resolution
   rule for `toolbarVerticalBehavior` (`NavigationStack` reads its top view, `TabView` its
   selected tab, `NavigationSplitView` its trailing column); the rule to not toggle it from view
   state, with `toolbarVisibility(_:for:)` for hiding; a pinned item overflows only during search;
   `ToolbarItemGroup` rather than fixed spacers; region frames already include margins. Two rows
   were added to the UIKit table: `arrangementViewStyle(_:)` → `updateArrangement(_:animated:)`,
   and `ReservedRegion` → `UIView.ReservedRegion`.

The four behavioral claims carry inline `[R1]`–`[R4]` tags so that Task 8 can find them and add
citations.

## `checks.log` results

- `wc -l`: 236 (expected 200–300). The prose uses one line per paragraph, which matches the house
  style of `platform-idioms.md` and `hig-patterns.md`. A first draft wrapped at 80 columns ran to
  372 lines.
- `right-to-left`: 3 lines (expected ≥ 2): § Reserved regions twice and § Bars once.
- `^## `: 8 (expected 8).
- `userInterfaceIdiom`: line 12, inside a "Never base a layout decision on…" rule.
- `When to branch`: one hit, the retained `platform-idioms.md` heading. It is not a pointer. No
  stale "see When to branch" pointers remain.
- Vale (R1-E): 0 errors, 0 warnings. An earlier draft had three warnings: "removes" and two
  sentences over 25 words. All three were fixed by rewording, with no waivers.

## Gates

- `DEVELOPER_DIR=<Xcode 27.1 beta> typecheck_snippets.py apple-design/references/*.md`:
  **8/8 clean, exit 0**.
- `bun test`: 198 pass, 0 fail. The first run failed on the header URL; see contradiction 3.
- `bun run audit`: 0 errors, 55 warnings. `adaptive-layout.md` adds one warning, "236 lines with
  no table of contents in the first 30 lines". Every other `apple-design` reference carries the
  same warning.
- `claude plugin validate . --strict`: passed.

## Files changed

- Created `authoring/apple-studio/pipeline/maps/apple-design-duo-live.md`.
- Created `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`.
- `plugins/apple-studio/skills/apple-design/SKILL.md`: added the routing line from the brief.
- `plugins/apple-studio/skills/apple-design/references/platform-idioms.md`: made the brief's four
  edits: the `verified:` re-check note, the pointer in the opening paragraph, the line 49 pointer,
  and the replacement of lines 85–93. **One extra edit:** the line 18 decision rule said "it
  already adapts by size class (see below)", and "below" was the moved `horizontalSizeClass`
  paragraph. It now points to `adaptive-layout.md` § What layout reads.
- `plugins/apple-studio/skills/apple-design/references/hig-patterns.md`: added the pointer
  paragraph after `(HIG: Tab Bars)` and the `verified:` re-check note.
- `authoring/apple-studio/CONVENTIONS.md`: replaced lines 48–49 with the brief's text.
- `records/.../task-4-reference/`: brief, `checks.log`, `typecheck-27.1.log`, and this report.

## Self-review

- All eight sections are present in order, with the required claims. The four snippets ship
  unchanged.
- No Apple sentence is copied. A 7-word n-gram scan against every fetched page found only short
  phrase overlaps and the two article titles. The three longest overlaps (7–10 words) were
  reworded.
- Right-to-left appears in § Reserved regions and § Bars.
- The UIKit table has 14 rows: the brief's 12 and 2 additions. It also carries the two prose rules.
- The routing edits match the brief exactly, plus the one extra stale-pointer fix listed above.
- The file restates no `hig-patterns.md` rule. It links to § Navigation instead.
- The header keeps the `<build>` and URL-list placeholders for Task 7. Only the developer URL
  changed, to its `.md` form (contradiction 3).

## Concerns

- The default for the reserved-region query (contradiction 2) is unresolved until runtime. Task 8
  should check whether an inactive fold appears without `.includeInactive`.
- The `platform-idioms.md` heading "When to branch code vs. when the system already adapts for
  you" now introduces only the first half of its title. The brief said to keep it. A rename is a
  possible follow-up, but Tasks 5 and 8 might reference it.
- `docc.py` does not render `termList` nodes (see Pages fetched).
- The other untracked `task-5` through `task-9` record directories were not part of this commit.

---

# Fix round 1 (2026-09-30)

The task review found three Important issues. The controller issued Ruling 9 for issue 3. Minor
findings wait for the final review and were not acted on.

## What changed

1. **Stale pointers to moved content.** Two pointers in `swiftui-design-implementation.md` sent
   `NavigationSplitView` collapse to `platform-idioms.md`, whose bullet this task had moved out.
   Line 3 now keeps menu bar, window state, and platform branching on `platform-idioms.md`, and
   sends `NavigationSplitView` collapse to `adaptive-layout.md` § System containers first. Line 87
   now points to `adaptive-layout.md` § System containers first.
   A grep of `apple-design/` for `platform-idioms`, `collapse`, `size class`,
   `horizontalSizeClass`, `fluid`, and `breakpoint` found no other pointer to the moved content.
   The other hits are either the file's own content (`hig-patterns.md:19-20` on the sidebar,
   `hig-foundations.md:23` on inspectors) or pointers that are still valid
   (`platform-idioms.md:18,49,85`, which this task already routed to `adaptive-layout.md`, and
   `swiftui-design-implementation.md:77` on menu bar, windows, and branching).
2. **`isActive` in the badge snippet.** The `LiveBadgeOverlay` predicate now starts with
   `region.isActive &&`, so the snippet follows the file's own "always check `isActive`" rule. The
   prose after the snippet adds one sentence: the predicate checks `isActive`, so an inactive
   camera does not move the badge.
3. **Bar-edge placement (Ruling 9).** I withdrew the unsourced "edge opposite the vertical bar"
   rule and replaced it with the sourced rule. Place custom bars and floating controls relative to
   `toolbarVerticalEdge`. Apple's own example aligns the control to the same edge as the bar.
   Handle `nil` with the layout that you use on devices without a vertical bar.
   `FloatingPaletteHost` now aligns to the bar's edge through a `paletteAlignment` switch:
   `.leading` → `.bottomLeading`, `.trailing` → `.bottomTrailing`, and `nil` → `.bottomTrailing`.
   Apple's docs state no rationale for the same-edge choice, so the reference states none.

`adaptive-layout.md` is now 245 lines, still inside the 200–300 range.

## Commands and output

- `DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer" python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md`
  gave `TOTAL: 8/8 snippets typecheck clean`, exit 0. The rewritten `LiveBadgeOverlay` (#1) and
  `FloatingPaletteHost` (#4) both pass as parse-as-library. `typecheck-27.1.log` was regenerated.
- Vale on `adaptive-layout.md`: 0 errors, 0 warnings.
- Vale on `swiftui-design-implementation.md`: 0 errors, 61 warnings. These are **identical to the
  pre-edit baseline** at `HEAD`, which also has 61 warnings. A sorted diff of the two
  `--output=line` listings differs only in the column of one existing warning on line 87
  (109 → 135), because the pointer text there is longer. The file predates the R1-E register.
  Rewriting it is outside this fix round.
- `bun test`: 198 pass, 0 fail.
- `bun run audit`: 0 errors, 55 warnings, unchanged from the Task 4 commit.
- `claude plugin validate . --strict`: passed.
