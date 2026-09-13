> verified: 2026-08 against https://developer.apple.com/documentation/swiftui.md, https://developer.apple.com/documentation/appkit.md, https://developer.apple.com/documentation/swiftui/appkit-integration.md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable.md, https://developer.apple.com/documentation/swiftui/nsviewcontrollerrepresentable.md, https://developer.apple.com/documentation/swiftui/nshostingcontroller.md, https://developer.apple.com/documentation/swiftui/nshostingview.md, https://developer.apple.com/documentation/swiftui/nshostingcontroller/sizingoptions.md, https://developer.apple.com/documentation/swiftui/nshostingsizingoptions.md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable/makensview(context:).md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable/updatensview(_:context:).md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable/makecoordinator().md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable/dismantlensview(_:coordinator:).md, https://developer.apple.com/documentation/swiftui/nsviewrepresentable/sizethatfits(_:nsview:context:).md, https://developer.apple.com/documentation/swiftui/nsviewrepresentablecontext.md, https://developer.apple.com/documentation/swiftui/nsviewrepresentablecontext/coordinator.md, https://developer.apple.com/documentation/swiftui/nsgesturerecognizerrepresentable.md, https://developer.apple.com/documentation/swiftui/unifying-your-app-s-animations.md
> sources: macOS by Tutorials v1.0.0 (judgment only), live Apple docs

## When SwiftUI genuinely isn't enough

Reach for AppKit interop only when SwiftUI has no first-party equivalent for a specific capability — not by default, and not because an AppKit pattern feels more familiar. Verify the specific gap you're about to rely on before committing to an interop path: SwiftUI's AppKit-parity surface grows every OS cycle (recent additions like `NSGestureRecognizerRepresentable`, `NSHostingSizingOptions`, and richer `TextEditor`/`AttributedString` support each closed a gap that used to require interop), so treat any "SwiftUI can't do X" claim as perishable. Check the current https://developer.apple.com/documentation/swiftui.md topic index and, if the AppKit side is what you actually need to confirm, https://developer.apple.com/documentation/appkit.md — don't carry forward a gap list from training data or an old blog post.

Decision framework, in order:

1. **Redesign first.** If the only reason you're reaching for AppKit is to force a UIKit/AppKit-shaped interaction onto SwiftUI, check whether a native SwiftUI pattern gets you the same user-facing result with less code and full state-management integration. This is the common case — most "SwiftUI can't do this" moments are really "I'm modeling this the AppKit way."
2. **Wait, if the gap is cosmetic and narrow.** A missing modifier or a slightly different animation curve isn't worth the maintenance cost of a `Representable` wrapper if you can ship an acceptable approximation now and revisit next OS cycle.
3. **Interop, when the gap is structural.** Reach for `NSViewRepresentable`/`NSViewControllerRepresentable`/`NSGestureRecognizerRepresentable` when the capability genuinely has no SwiftUI surface at all — not a worse version, an absent one. See "Recurring reasons to reach for interop" below for the common categories.

For how a hosted AppKit control should *look and behave* like a native Mac control once it's embedded, see `apple-design`'s `platform-idioms.md` — this file only covers the bridging mechanics, not visual/interaction correctness.

## The two directions of hosting

AppKit interop is bidirectional and the two directions use different types — don't confuse them:

- **SwiftUI view inside an AppKit app** → `NSHostingController` (a view controller, drop into an existing `NSWindowController`/`NSViewController` hierarchy) or `NSHostingView` (a plain `NSView`, drop into any AppKit view hierarchy directly). Chain for a whole new window: `NSWindowController → NSWindow → NSHostingController → your SwiftUI View` (macOS by Tutorials, ch. 9). Construct with `NSHostingController(rootView:)` / `NSHostingView(rootView:)`; read back the live view via the `rootView` property (mutable — reassigning it re-renders) (https://developer.apple.com/documentation/swiftui/nshostingcontroller.md, https://developer.apple.com/documentation/swiftui/nshostingview.md).
- **AppKit view inside a SwiftUI app** → `NSViewRepresentable` (wraps an `NSView`) or `NSViewControllerRepresentable` (wraps an `NSViewController`) as a SwiftUI `View` conformance with `Body == Never` — you never write a `body`, only the lifecycle methods below (https://developer.apple.com/documentation/swiftui/nsviewrepresentable.md, https://developer.apple.com/documentation/swiftui/nsviewcontrollerrepresentable.md).

Both directions exist because interop is about *which side owns the window/root of the hierarchy*, not just "can SwiftUI and AppKit views coexist" — an AppKit-lifecycle app hosting one SwiftUI screen and a SwiftUI-lifecycle app embedding one AppKit control are different shapes of the same problem.

## NSHostingController / NSHostingView mechanics

- `NSHostingController<Content>` is an `NSViewController` subclass; treat it exactly like any other view controller in your AppKit hierarchy — set it as an `NSWindow`'s `contentViewController`, push it in a split view, etc. (macOS by Tutorials, ch. 9; https://developer.apple.com/documentation/swiftui/nshostingcontroller.md).
- Sizing between the hosted SwiftUI content and the surrounding AppKit layout is governed by `sizingOptions` (`NSHostingSizingOptions`): it controls whether the controller derives minimum/maximum/ideal Auto Layout constraints from the SwiftUI content's own sizing. These constraints only take effect when the containing window is otherwise using Auto Layout, and when the controller is a window's `contentViewController` it also drives that window's min/max size. Narrow `sizingOptions` to fewer flags when you can assume a fixed frame — fewer options means fewer layout measurement passes (https://developer.apple.com/documentation/swiftui/nshostingcontroller/sizingoptions.md, https://developer.apple.com/documentation/swiftui/nshostingsizingoptions.md). `NSHostingView` exposes the equivalent `sizingOptions` for the plain-view case.
- Every window in an AppKit app needs an explicit `NSWindowController`, even when its content is entirely SwiftUI — there's no scene-graph shortcut the way `WindowGroup`/`Window` give you on the SwiftUI-lifecycle side; see `mac-app-structure.md` for that scene-based alternative when you control the whole app (macOS by Tutorials, ch. 9).
- Activate the app (`NSApp.activate(ignoringOtherApps: true)`) before showing a newly created window from AppKit-side code — SwiftUI's own window-presentation plumbing does this for you, but manually constructed `NSWindowController` flows don't (macOS by Tutorials, ch. 9).

## NSViewRepresentable / NSViewControllerRepresentable mechanics

Both protocols share the same lifecycle shape; `NSViewControllerRepresentable` mirrors `NSViewRepresentable` method-for-method with `NSViewController` in place of `NSView`, so the descriptions below apply to both unless noted.

**Required methods:**

- `makeNSView(context:) -> NSViewType`  — called exactly once, the first time SwiftUI needs the view. Create and configure the AppKit view here using the initial data. Never treat this as a place to react to later state changes (https://developer.apple.com/documentation/swiftui/nsviewrepresentable/makensview(context:).md).
- `updateNSView(_ nsView: NSViewType, context: Context)` — called on every subsequent SwiftUI state change that could affect this view. This is the only place ongoing state sync happens; `makeNSView` never runs again for the same view instance (https://developer.apple.com/documentation/swiftui/nsviewrepresentable/updatensview(_:context:).md).

**Optional methods:**

- `makeCoordinator() -> Coordinator` — implement only if the AppKit view needs to talk back to SwiftUI (delegate callbacks, target-action). Called once, before the first `makeNSView`, so the coordinator instance is available when you configure the view's delegate/target inside `makeNSView` (https://developer.apple.com/documentation/swiftui/nsviewrepresentable/makecoordinator().md).
- `dismantleNSView(_ nsView:, coordinator:)` (static) — clean-up hook (remove observers, tear down notifications) called when the view is about to be removed (https://developer.apple.com/documentation/swiftui/nsviewrepresentable/dismantlensview(_:coordinator:).md).
- `sizeThatFits(_ proposal: ProposedViewSize, nsView:, context:) -> CGSize?` — return `nil` to fall back to the default sizing algorithm; SwiftUI may call this multiple times per layout pass with different proposals while it resolves the composite size, so it must be cheap and side-effect-free (https://developer.apple.com/documentation/swiftui/nsviewrepresentable/sizethatfits(_:nsview:context:).md).

**Sizing behavior to internalize:** the represented view doesn't get to unilaterally decide its size the way it might standalone — SwiftUI proposes a size, `sizeThatFits` (if implemented) or the view's own intrinsic/Auto Layout behavior resolves an actual size, and that resolved size becomes the frame SwiftUI lays the wrapper out at. This is the same proposal/response negotiation every SwiftUI view participates in, not an AppKit-specific mechanism — don't fight it by forcing a fixed frame inside `makeNSView` when a `sizeThatFits` implementation is the actual lever.

## Coordinator: the AppKit-to-SwiftUI channel

Data flows two directions across the boundary, and they use different mechanisms:

- **SwiftUI → AppKit**: ordinary property passing. Store the values your view needs as `struct` properties on the `Representable`, then read them in `updateNSView` to push into the AppKit view. This direction needs no coordinator at all.
- **AppKit → SwiftUI**: only the `Coordinator` can carry this direction, because `NSViewRepresentable` is a `struct` — it can't itself be an `NSTextViewDelegate`, a target for `NSButton` actions, or a KVO/notification observer without a reference-type intermediary. Make the `Coordinator` a `class`, conform *it* to the delegate protocol you need, and give it a way back into SwiftUI — typically closures or `Binding`s captured from the parent `Representable` at `makeCoordinator()` time. Set the AppKit view's `delegate`/`target` to `context.coordinator` inside `makeNSView`, never inside `updateNSView` (https://developer.apple.com/documentation/swiftui/nsviewrepresentablecontext/coordinator.md).

```swift
struct RichTextView: NSViewRepresentable {
    @Binding var text: NSAttributedString

    func makeNSView(context: Context) -> NSTextView {
        let view = NSTextView()
        view.delegate = context.coordinator
        return view
    }

    func updateNSView(_ view: NSTextView, context: Context) {
        if view.attributedString() != text { view.textStorage?.setAttributedString(text) }
    }

    func makeCoordinator() -> Coordinator { Coordinator(text: $text) }

    final class Coordinator: NSObject, NSTextViewDelegate {
        var text: Binding<NSAttributedString>
        init(text: Binding<NSAttributedString>) { self.text = text }
        func textDidChange(_ notification: Notification) {
            guard let view = notification.object as? NSTextView else { return }
            text.wrappedValue = view.attributedString()
        }
    }
}
```

`Context` (`NSViewRepresentableContext`/`NSViewControllerRepresentableContext`) also exposes `environment` (the current SwiftUI `EnvironmentValues`, for reading things like `colorScheme` inside `updateNSView`) and `transaction` (the active `Transaction`, for matching AppKit-side animation to the SwiftUI update that triggered it) — both read-only, both refreshed on every `update` call (https://developer.apple.com/documentation/swiftui/nsviewrepresentablecontext.md).

## Recurring reasons to reach for interop

These are the categories that most often justify the bridging above — named here as judgment, not as an AppKit API tutorial (AppKit's own surface is out of scope for this file; verify specifics against https://developer.apple.com/documentation/appkit.md when a claim needs pinning):

- **Rich text editing/display** — attributed-string editing with `NSTextView`-level control (custom text attachments, layout managers, spell-check integration) beyond what SwiftUI's `TextEditor`/`AttributedString` support currently covers. Confirm the current `TextEditor`/`AttributedString` rich-text ceiling against the live `swiftui` topic index before assuming this gap still applies to your case — this is one of the fastest-moving parity areas.
- **Advanced tables and outlines** — `NSTableView`/`NSOutlineView`-level behavior (multi-column resizing/reordering with fine-grained delegate control, complex drag-reordering, cell-level editing states) beyond what SwiftUI `Table`/`List` currently expose. Confirm the current `Table`/`List` ceiling against your specific interaction before reaching for this path.
- **Custom drawing and low-level event handling** — direct `draw(_:)` overrides, precise `NSResponder`/`NSEvent` handling (custom hit-testing, pressure-sensitive input, low-latency drag tracking) where `Canvas`, `.gesture()`, and `.onContinuousHover()` don't give you the control surface you need. `NSGestureRecognizerRepresentable` (current as of the latest SwiftUI/AppKit-integration index) narrows this specific case — it lets an existing `NSGestureRecognizer` subclass drive SwiftUI gesture state without a full view wrapper, so check it before reaching for a whole `NSViewRepresentable` just to host a gesture recognizer (https://developer.apple.com/documentation/swiftui/nsgesturerecognizerrepresentable.md).
- **Framework-mandated AppKit types** — a third-party or system framework (e.g., `WKWebView`) that only ships an `NSView` API, with no SwiftUI-native equivalent at all. This is the cleanest case for interop: there's no redesign option, only wrap-or-don't-use-it (macOS by Tutorials, ch. 10).

If you're bridging animation timing specifically (keeping an AppKit-driven animation and a SwiftUI-driven one visually in sync), see https://developer.apple.com/documentation/swiftui/unifying-your-app-s-animations.md rather than hand-rolling transaction plumbing.

## Concurrency and testing notes

- Every protocol and type covered here (`NSViewRepresentable`, `NSViewControllerRepresentable`, `NSGestureRecognizerRepresentable`, `NSHostingController`, `NSHostingView`, and their `Context`/`Coordinator` types) is `@MainActor` in the current SwiftUI headers. Under Swift 6 strict concurrency this is enforced, not advisory — don't call `make`/`update`/coordinator methods from a background actor, and don't store non-`Sendable` state your coordinator mutates off the main actor.
- `Coordinator` classes are the one place in this pattern that commonly need `@unchecked Sendable` or careful isolation review if you close over mutable state from multiple call sites — keep them main-actor-isolated by default rather than fighting the compiler.
- For Swift Testing coverage of a `Representable`, test the pure Swift logic your `Coordinator` exposes (the binding-update closures, delegate-callback handlers) directly rather than trying to drive `makeNSView`/`updateNSView` through the SwiftUI rendering pipeline in a unit test — those lifecycle methods are meant to be exercised by running the app, not asserted on directly.

## Maintaining older code: legacy AppKit-first apps

An app whose lifecycle is AppKit-native from the start (Storyboard-based `AppDelegate`, no SwiftUI `App` type) still hosts SwiftUI screens the same way — `NSHostingController`/`NSHostingView` — but every window needs its own `NSWindowController` you write by hand, since there's no `WindowGroup`/`Window` scene graph managing window lifecycle for you (macOS by Tutorials, ch. 9). If you're deciding whether a project like this is worth migrating to a SwiftUI-lifecycle `App`, that's a `mac-app-structure.md`-level decision, not an interop one — this file only covers how the two coexist once that decision is made either way.

Build/run workflows for exercising either direction of interop belong to `xcode-loop`, not this file.
