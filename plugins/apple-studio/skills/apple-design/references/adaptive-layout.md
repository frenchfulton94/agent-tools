> verified: 2026-09 against https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo, https://developer.apple.com/design/human-interface-guidelines/layout, https://developer.apple.com/design/human-interface-guidelines/designing-for-games, https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo.md, https://developer.apple.com/documentation/swiftui/reservedregion.md, https://developer.apple.com/documentation/swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:).md, https://developer.apple.com/documentation/swiftui/arrangementview.md, https://developer.apple.com/documentation/swiftui/view/arrangementviewstyle(_:).md, https://developer.apple.com/documentation/swiftui/view/toolbarverticalbehavior(_:).md, https://developer.apple.com/documentation/swiftui/toolbarcontent/axisbehavior(_:).md, https://developer.apple.com/documentation/swiftui/environmentvalues/toolbarverticaledge.md; compiled against iPhoneOS 27.1 SDK (27A9269); re-checked 2026-10 against https://developer.apple.com/documentation/swiftui/view/ongeometrychange(for:of:action:).md and the `ReservedRegion` frame and margins in the iPhoneOS 27.1 SDK `UIViewReservedRegion.h` (Phase 9 final review: badge snippet, arrangement-view nesting, vertical-bar asymmetry)
> sources: live HIG and developer documentation (DocC JSON)
> typecheck: ios 27.1
> note: iPhone Duo APIs are iOS 27.1 beta as of 2026-09. Re-verify at 27.1 GA (docs/deferred.md). Behavioral claims R1–R7 cite runtime evidence in records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md. Each citation carries its label in brackets.

# Adaptive Layout

This file owns layout that must survive any size, shape, or pose. iPhone Duo is the hardest case, and iPad windowing and iPhone Mirroring are the familiar ones.

## What layout reads

Base every layout decision on two inputs: the size classes, and the bounds of the scene or the containing view. Never base a layout decision on `userInterfaceIdiom`, on the interface orientation, or on the screen dimensions. The idiom and the orientation do not tell you how much space your view has. The screen size is wrong whenever your app shares the display or runs on a second display. (HIG: Layout § Size classes; Preparing your app for iPhone Duo)

- Size each view relative to its container, not to a fixed iPhone width.
- Branch layout on `@Environment(\.horizontalSizeClass)`, not on `#if os(iOS)`. An iPad app in a narrow window reports `.compact`, the same as an iPhone in portrait. Keep OS checks for capabilities, not for shapes; `platform-idioms.md` lists the real capability branches.
- Let the system adapt what it already adapts. `List` and `Form` take each platform's list style. `Button`, `Toggle`, and `Picker` render in each platform's native style. Dynamic Type and Dark Mode adapt everywhere if you use semantic fonts and colors. A fixed frame or a platform branch here adds code and stops the adaptation.

Design for arbitrary widths, not for a set of breakpoints. Your app cannot detect or choose the size it gets. Two sources make this true today. First, iPad windows resize freely, and the API gives no signal about the window mode. Second, iPhone Duo moves your app between two displays and through several poses. Any width between the extremes is possible.

On iPhone Duo, the outer display is compact width and the inner display is regular width. A compact layout and a regular layout together cover every pose; do not design one layout for each pose. When the app resizes, let the current layout expand into the new space. Do not redesign the screen on resize. (HIG: Designing for iPhone Duo § Device poses)

## System containers first

Standard containers already handle the display change, camera occlusion, and the fold. Use them before you write any custom geometry.

- `NavigationSplitView` shows one column on the outer display and expands on the inner display. This is the same compact-to-regular change that it makes on other devices. On the inner display, split views also adjust column widths and margins so that each column stays clear of the fold.
- Alerts, context menus, and sheets move away from the fold without any code from you.
- `TabView`, `NavigationStack`, and `NavigationSplitView` host the bars that move to a vertical edge. See § Bars that adapt to space.

For the choice between a sidebar, a tab bar, and a split view, see `hig-patterns.md` § Navigation: Sidebar vs. Tab Bar vs. Split View. (HIG: Designing for iPhone Duo § Split views, § Reserved regions)

Use the larger display to show one more level of your hierarchy, and only where the content supports it. Mail is the model: closed, it shows the message list or one message; open, it shows both side by side. Keep functionality and the state of every element the same on both displays and in every pose. A control can move into an overflow menu when space is short, but it must stay reachable. (HIG: Designing for iPhone Duo § Best practices; Layout § Size classes)

## Reserved regions

A reserved region is an area of your view that another element owns. Your content must avoid it, or your layout must adapt to it. There are two kinds:

- `occlusion`: hardware covers the content, so the content is not visible. Cameras and the Dynamic Island are occlusions. Apple's definition also names window controls, so iPad's windowed mode is the familiar precedent.
- `division`: the fold splits one area into two separate areas.

A region is either active or inactive. Each `ReservedRegion` carries `isActive`, `frame`, and `margins`; the frame already includes the margins that interactive content needs. The default query returns only the active regions that intersect your view. Add the `.includeInactive` option to also receive inactive ones. On a fully open device, the default query returns no fold, and the `.includeInactive` query returns the fold with `isActive` false. The ReservedRegion docs say that the query returns regions whether or not they are active, but the runtime follows the SDK header [R5]. Check `isActive` before you move content anyway, so the code stays correct when a query adds `.includeInactive`. (ReservedRegion; `UIViewReservedRegion.h`, iPhoneOS 27.1 SDK; runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md)

iPhone Duo has three regions:

- The outer front camera. This occlusion is always active. It grows into the Dynamic Island for a Live Activity.
- The inner front camera. This occlusion is active only while the camera runs. At other times the camera is not visible.
- The fold. This division is active only when the device is partly open. It is inactive when the device is fully open [R3] (runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md).

(HIG: Designing for iPhone Duo § Reserved regions)

Right-to-left layout needs care. The hardware does not move for the language: the camera stays in the same physical corner in right-to-left languages. By default, `reservedRegions(kind:options:layoutDirectionBehavior:)` mirrors each frame into the view's layout direction. Because of this, a custom `Layout` or a leading-and-trailing check needs no extra code for right-to-left (documented, not runtime-checked). Pass `LayoutDirectionBehavior.fixed` only when you must position against the physical hardware. Then your code must handle right-to-left itself. (ReservedRegion § Overview)

Two layout rules follow from the fold:

- In a grid, prefer an even number of columns, so the fold falls between two columns and not through one.
- Move only what the region blocks. Small moves keep a control where people expect it. A control that jumps across the screen is hard to find again.

```swift
struct LiveBadgeOverlay: View {
    @State private var badgeSize = CGSize.zero
    private let inset: CGFloat = 16

    var body: some View {
        GeometryReader { proxy in
            // Where the badge sits when nothing blocks it.
            let restingFrame = CGRect(
                x: proxy.size.width - inset - badgeSize.width,
                y: inset,
                width: badgeSize.width,
                height: badgeSize.height
            )
            // The lowest edge of any active occlusion over that spot.
            let blockedUntil = proxy.reservedRegions(kind: .occlusion)
                .filter { $0.isActive && $0.frame.intersects(restingFrame) }
                .map(\.frame.maxY)
                .max()
            Text("Live")
                .padding(8)
                .background(.thinMaterial, in: .capsule)
                .onGeometryChange(for: CGSize.self) { $0.size } action: { badgeSize = $0 }
                .padding(.top, blockedUntil ?? inset)
                .padding(.trailing, inset)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
        }
    }
}
```

This is the manual fallback. System components already avoid reserved regions, so use this only in a custom view that the system does not move. The badge stays in its top trailing corner. It moves down only when an active occlusion overlaps its resting spot, and only as far as the bottom edge of that region. The region frame already includes the margins that interactive content needs, so the badge needs no extra gap. The filter checks `isActive`, so an inactive camera does not move the badge. The test uses the resting spot, not the moved badge, so the badge does not move back and forth. `inset` is the badge's distance from the top and trailing edges; any value works. The frames are mirrored by default, so the trailing position is correct in right-to-left languages (documented, not runtime-checked).

## Arrangement views

`ArrangementView` holds a primary view and a secondary view. It places them from the available size, the size class, and the reserved regions. It has two styles:

- `split` places the two views side by side when the container is wider than it is tall. It stacks them, primary on top, when the container is taller than it is wide. It also moves the views to stay clear of the fold.
- `overlay` layers the primary view over the secondary view when no division is active. That is the case when the device is closed or fully open. When the device is partly open, `overlay` moves the views to the two sides of the fold. The primary view goes to the trailing or bottom side.

The default style, `.automatic`, resolves to `split`. Limit the axes that a style can use with `axes(_:)`. (ArrangementView; Preparing your app for iPhone Duo § Arrange views in different poses)

Choose the style from the layout you already have. An `HStack` or `VStack` of two views maps to `split`. A `ZStack` that layers one view over another maps to `overlay`.

An arrangement view lays out content; it does not navigate. Put navigation containers, such as `NavigationStack` and `TabView`, around an arrangement view, not inside it. (HIG: Designing for iPhone Duo § Arrangement views)

Apple's two pages differ on `NavigationSplitView`. The HIG names navigation split views among the containers that go around an arrangement view. The developer overview says to avoid an arrangement view inside a navigation split view, a list, or a scroll view. It says the same of any other container that can hide part of the view. Follow the developer overview: avoid an arrangement view in a `NavigationSplitView` column. The split view already adapts its columns to the fold (see § System containers first), so the arrangement view adds nothing there. Also avoid an arrangement view inside a `List` or a `ScrollView`, where part of it can become unreachable. (HIG: Designing for iPhone Duo § Arrangement views; Preparing your app for iPhone Duo § Arrange views in different poses)

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

With `.axes(.horizontal)`, a container that is taller than it is wide shows only the primary view.

## Bars that adapt to space

**Where bars go vertical.** On iPhone Duo, the system moves the navigation bar, the toolbar, and the tab bar to one edge. The outer display does this in every orientation, and the inner display does it in landscape. The inner display in portrait keeps horizontal bars [R1] (runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md). The vertical bar stays on the hardware side in right-to-left languages (documented, not runtime-checked). When Split View multitasking puts two apps on the inner display, each app puts its bar on its own outer edge. (HIG: Designing for iPhone Duo § Vertical controls)

Some contexts have their own rules (Preparing your app for iPhone Duo § Optimize bars for vertical presentation):

- Inspectors: bars are always horizontal.
- A split view that shows more than one column: the sidebar and content columns get horizontal bars, and the detail column gets a vertical bar.
- Sheets on the outer display: bars are vertical by default [R4] (runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md).
- Sheets on the inner display: the toolbar is horizontal for a centered or leading sheet, and vertical for a trailing sheet.

**Get the behavior for free.** Attach `toolbar(content:)` inside a `NavigationStack` or `NavigationSplitView`. A bar that you build as a custom view gets none of this behavior.

**Order.** Put primary navigation, such as Back or Close, at the top of the vertical bar. Put prominent actions, such as Done, next. Keep the remaining items in their original groups; the system adds space between the groups from the top bar and the bottom bar. Use `.cancellationAction` for a custom Close button and `.topBarPinnedTrailing` for Done. A pinned item moves to the overflow menu only when search is active and space is short. Use `ToolbarItemGroup` to space items, not fixed spacers.

**Every item gets a title and a symbol.** The system picks the form for each context:

- A vertical bar shows the symbol.
- A horizontal bar shows the symbol or the title, and prefers the symbol.
- The overflow menu shows both.
- An item with a title and no symbol never goes into a vertical bar [R2] (runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md). An item with a custom view never goes into a vertical bar either.

Keep text-only buttons rare, and use a symbol wherever one works.

**Overflow.** Items overflow from the bottom of the bar toward the top by default. To change the order, set `visibilityPriority(_:)` on whole groups first, and then on single items. Keep frequent actions, such as Compose, and items with badges visible longest. Move any overflow menu that you built into `ToolbarOverflowMenu`, so all overflow actions are in one place. Use the ellipsis symbol only for the overflow menu. (HIG: Designing for iPhone Duo § Vertical controls)

**Compression.** When the tab bar and toolbar items share a vertical bar and space is short, one of them compresses first. In a navigation-focused view, keep the default: the tab bar stays and toolbar items overflow. In a task-focused view, apply `.toolbarVerticalCompressionBehavior(.prefersToolbarItems)`, so the tab bar minimizes and the task's actions stay.

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
                    ToolbarItem(placement: .primaryAction) {
                        Button("Reply", systemImage: "arrowshape.turn.up.left") {}
                    }
                    .visibilityPriority(.high)
                    ToolbarItem(placement: .primaryAction) {
                        Button("Flag", systemImage: "flag") {}
                    }
                    .visibilityPriority(.low)
                    ToolbarOverflowMenu {
                        Button("Print", systemImage: "printer") {}
                    }
                }
                // Takes effect when a TabView shares the vertical bar with this toolbar.
                .toolbarVerticalCompressionBehavior(.prefersToolbarItems)
        }
    }
}
```

On iPhone Duo, `.secondaryAction` items start in the overflow menu on both displays, with or without a symbol [R6]. `visibilityPriority(.high)` does not bring one into the bar, even when the bar has room [R7]. For `.primaryAction` items the priority works: when the bar overflows, a `.high` item stays and a `.low` item leaves first [R7]. For this reason, the example puts Reply and Flag in `.primaryAction`. R6 and R7 are runtime-checked (2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md).

**Opt out rarely.** Do not change the default bar placement in most apps. Apply `toolbarVerticalBehavior(.disabled)` only to full-screen media or a non-scrolling layout such as a calculator. Choose it once per screen, and do not toggle it from view state. To hide the bars instead, use `toolbarVisibility(_:for:)`. `NavigationStack` reads the behavior from its top view, `TabView` from the selected tab, and `NavigationSplitView` from its trailing column. On the inner display, `presentationPlacement(_:)` sets the side that a sheet uses, and so the axis of its bar. `axisBehavior(_:)` limits one item to `.horizontalOnly` or makes it `.verticalPreferred`. (toolbarVerticalBehavior(_:); axisBehavior(_:))

**Custom views.** Because the vertical bar sits along one edge, the content area is lopsided. Keep content inside the safe area, which carries an inset for the vertical bar. In Split View multitasking on the inner display, the other app's bar sits on the far edge. The safe area accounts for that bar too. (HIG: Designing for iPhone Duo § Vertical controls)

Read `toolbarVerticalEdge` to learn which edge holds the vertical bar. It reports the system's preferred edge even while the bar is hidden. It is `nil` on devices without a vertical bar, and in contexts that never use one. To extend a hero image or background under the vertical bar, apply `backgroundExtensionEffect()` to it.

```swift
struct FloatingPaletteHost: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        Image(systemName: "paintpalette")
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: paletteAlignment)
    }

    private var paletteAlignment: Alignment {
        switch barEdge {
        case .leading: .bottomLeading
        case .trailing: .bottomTrailing
        case nil: .bottomTrailing
        }
    }
}
```

Place custom bars and floating controls relative to `toolbarVerticalEdge`. Apple's own example aligns the control to the same edge as the vertical bar. Handle `nil` with the layout that you use on devices without a vertical bar. (toolbarVerticalEdge)

**Full width and proximity.** A visual, non-scrolling screen can use the full display width with no bars, as Calculator does. Keep it clear of the Dynamic Island and the status bar. A background can span the full width while scrolling content stays inset. Keep controls next to the content they change: Mail keeps its list controls above the list, not in the vertical bar. (HIG: Designing for iPhone Duo § Vertical controls)

## Games

- Lock to portrait or landscape if the game needs it, but fill the screen in every pose.
- Keep text and control sizes as constant as possible when the game resizes.
- Change the aspect ratio in preference to letterboxing or pillarboxing.
- If letterboxing is unavoidable, fill the padding with artwork.

(HIG: Designing for iPhone Duo § Best practices; Designing for games, https://developer.apple.com/design/human-interface-guidelines/designing-for-games)

## Checking a layout on iPhone Duo

Build with the current Xcode. An app that you build with Xcode 26 or earlier does not extend under the status bar and the camera. (Preparing your app for iPhone Duo § Overview)

Check each item:

- Both displays.
- Each pose: closed, fully open, and partly folded.
- Each pose rotated to every orientation that the app supports.
- Every view, sheet, and popover, not only the root screen.
- Bars on the side: order, overflow, and title-only items.
- Nothing important sits in the fold or under a camera.
- Sheets and popovers stay in position when the device opens or folds.

Preview poses in Xcode's Device Hub. Capture screenshots of each pose through the `xcode-loop` skill. For photo or video capture, read Apple's "Choosing a camera by the direction it faces" and "Registering a camera capture accessory on iPhone Duo". After the device opens or closes, a camera can face the opposite way.

## Maintaining older code: UIKit equivalents

| SwiftUI | UIKit |
|---|---|
| `ArrangementView` | `UIArrangementViewController` |
| `arrangementViewStyle(_:)` | `UIArrangementViewController.updateArrangement(_:animated:)` |
| `ReservedRegion` | `UIView.ReservedRegion` |
| `reservedRegions(kind:options:layoutDirectionBehavior:)` | `UIView.reservedRegions(kind:options:)` |
| `toolbarVerticalEdge` | `UITraitCollection.verticalBarEdge` |
| `toolbarVerticalBehavior(_:)` | `UIViewController.preferredVerticalBarBehavior` |
| `toolbarVerticalCompressionBehavior(_:)` | `UINavigationItem.verticalBarCompressionBehavior` (`UIVerticalBarCompressionBehavior`) |
| `topBarPinnedTrailing` | `UINavigationItem.pinnedTrailingGroup` |
| `cancellationAction` | `UINavigationItem.leadingItemGroups` |
| `axisBehavior(_:)` | `UIBarButtonItem.axisBehavior` |
| `visibilityPriority(_:)` | `UIBarButtonItem.visibilityPriority` |
| `ToolbarOverflowMenu` | `UINavigationItem.additionalOverflowItems` |
| `presentationPlacement(_:)` | `UISheetPresentationController.preferredPlacement` |
| `backgroundExtensionEffect()` | `UIBackgroundExtensionView` |

Two rules apply in UIKit:

- Set bar items on a view controller inside a navigation controller. Do not build a `UIToolbar`, `UINavigationBar`, or `UITabBar` yourself; a custom bar never moves to the vertical edge.
- Use Auto Layout, and use automatic trait tracking to follow `horizontalSizeClass` and `verticalSizeClass` changes.

(Preparing your app for iPhone Duo § Address common layout and resizing considerations, § Optimize bars for vertical presentation)
