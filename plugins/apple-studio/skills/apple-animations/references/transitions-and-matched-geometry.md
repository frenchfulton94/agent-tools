> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/anytransition, https://developer.apple.com/documentation/swiftui/transition, https://developer.apple.com/documentation/swiftui/view/matchedgeometryeffect(id:in:properties:anchor:issource:), https://developer.apple.com/documentation/swiftui/navigationtransition, https://developer.apple.com/documentation/swiftui/view/navigationtransition(_:), https://developer.apple.com/documentation/swiftui/view/matchedtransitionsource(id:in:), https://developer.apple.com/documentation/swiftui/matchedgeometryproperties, https://developer.apple.com/documentation/swiftui/geometryeffect, https://developer.apple.com/documentation/swiftui/namespace, https://developer.apple.com/documentation/swiftui/view/geometrygroup(), https://developer.apple.com/documentation/swiftui/view/transition(_:), https://developer.apple.com/documentation/swiftui/transitionproperties, https://developer.apple.com/documentation/swiftui/transitionphase, https://developer.apple.com/documentation/swiftui/asymmetrictransition, https://developer.apple.com/documentation/swiftui/view/matchedtransitionsource(id:in:configuration:), https://developer.apple.com/documentation/swiftui/matchedtransitionsourceconfiguration, https://developer.apple.com/documentation/swiftui/emptymatchedtransitionsourceconfiguration, https://developer.apple.com/documentation/swiftui/anynavigationtransition, https://developer.apple.com/documentation/swiftui/crossfadenavigationtransition
> sources: live Apple docs (no book input; judgment layer: apple-design/animation-taste.md)

# Transitions and Matched Geometry

Mechanics only: how `transition(_:)`, custom `Transition`s, `matchedGeometryEffect`, and navigation/zoom transitions actually work — their insertion/removal contract, their signatures, and their concrete failure modes. This file does not cover content morphing *within* a single view (`Text`/SF Symbol glyph changes, `.numericText`, etc.) — that's `ContentTransition`/`contentTransition(_:)`, fully covered in `animation-fundamentals.md`. The two are frequently confused by name: `transition(_:)` animates a view *entering or leaving* the hierarchy; `contentTransition(_:)` animates a value changing *within* a view that never leaves.

## The Insertion/Removal Contract

`transition(_:)` only has an effect when the view it's attached to is added to, or removed from, the view hierarchy — not when any other property of an already-present view changes (Apple docs: `View.transition(_:)`).

- The trigger is existence itself: a condition (`if`/`switch`, a `ForEach` losing/gaining an identified element) that controls whether the view is built at all for a given render.
- Wrap the mutating state change in `withAnimation` (or drive it through an `.animation(_:value:)`-bound value) — the transition needs an animation transaction in effect to interpolate across; without one, the view still appears/disappears, just as a hard cut.

**Classic mechanism-breaking mistake**: hiding a view with `.opacity()`/`.hidden()` while it stays permanently resident in the hierarchy, then attaching `.transition(_:)` to it. No insertion/removal event ever occurs, so the transition modifier has nothing to attach to and silently no-ops:

```swift
// Breaks transition(_:): the view never leaves the hierarchy, only its opacity changes.
MyBanner()
    .opacity(showBanner ? 1 : 0)
    .transition(.move(edge: .top))   // no-op

// Works: existence itself is the condition.
if showBanner {
    MyBanner()
        .transition(.move(edge: .top))
}
```

If you need to animate a property on a view that stays resident the whole time, that's implicit `.animation(_:value:)`, not `transition(_:)` — reaching for `transition` there is a category error, not a tuning problem.

`transition(_:)` has two overloads: one generic over any `Transition`-conforming type, one taking a type-erased `AnyTransition` (Apple docs: `View.transition(_:)`).

## `AnyTransition`: the Built-In Vocabulary

`AnyTransition` is the type-erased transition value most APIs traffic in (Apple docs: `AnyTransition`). Built-in vocabulary, purely mechanical descriptions (their semantic fit — when a fade communicates something different from a slide — is judgment covered in `apple-design/references/animation-taste.md § Transition-Type Judgment`, not restated here):

- `.identity` — output equals input; no visual change on insertion/removal.
- `.opacity` — interpolates alpha between transparent and opaque.
- `.move(edge:)` — offsets the view off- and on-screen from the given edge.
- `.offset(_:)` / `.offset(x:y:)` — offsets by a fixed vector rather than to/from an edge.
- `.scale` / `.scale(scale:anchor:)` — scales toward/away from an anchor point.
- `.slide` — inserts from the leading edge, removes toward the trailing edge.
- `.push(from:)` — combines a directional move with a fade.
- `.blurReplace`, `.symbolEffect`, `.symbolEffect(_:options:)` — view-level transitions built around blur and SF Symbol replacement mechanics; distinct from `ContentTransition`'s symbol-effect case (that one morphs a symbol's glyph in place; these apply on insertion/removal of the whole view). Symbol-morphing semantics are covered in `animation-fundamentals.md`, not here.

**Combining and configuring** (Apple docs: `AnyTransition`):

- `.combined(with:)` — layers two transitions so both apply simultaneously on the same insertion/removal.
- `.asymmetric(insertion:removal:)` — a different transition for insertion than for removal; appropriate exactly when appearing and disappearing aren't just each other run backward.
- `.animation(_:)` — attaches a specific `Animation` to the transition itself, independent of whatever transaction triggered the state change.

## Custom Transitions: the `Transition` Protocol

Write a custom `Transition` when the built-in vocabulary can't express the shape you need — e.g. combining more than opacity/geometry, or driving an effect that isn't decomposable into `.combined(with:)` layers (Apple docs: `Transition`).

Requirements (Apple docs: `Transition`):

- `func body(content: Content, phase: TransitionPhase) -> Body` — the only method; it receives the content view and the current `TransitionPhase`, and returns modified content.
- `static var properties: TransitionProperties` — declares high-level facts about the transition (currently just `hasMotion`) that other systems (accessibility) can inspect without running the transition.

`TransitionPhase` has three cases driving `body(content:phase:)` (Apple docs: `TransitionPhase`):

- `.willAppear` — about to be inserted; apply the "before" state of whatever you're animating.
- `.identity` — fully present; apply no visual change here — whatever modification `body` makes in this phase persists as long as the view is visible, so treat it as the resting state, not a step in the animation.
- `.didDisappear` — being removed; apply the "after" state.
- `.isIdentity: Bool` and `.value: Double` are convenience accessors — `value` is meant for effects that scale by phase (e.g. multiplying a rotation angle) rather than switching over the enum directly every time.

```swift
struct RotatingFadeTransition: Transition {
    func body(content: Content, phase: TransitionPhase) -> some View {
        content
            .opacity(phase.isIdentity ? 1.0 : 0.0)
            .rotationEffect(phase == .willAppear ? .degrees(30) : phase == .didDisappear ? .degrees(-30) : .zero)
    }
}
```

**Do not use identity-affecting modifiers (`.id(_:)`, or nesting another `if`/`switch` on the content) inside a custom transition's `body`.** Apple's docs call this out explicitly: doing so resets the state of whatever view the transition wraps, which both wastes work and can produce surprising behavior exactly at the moment the view is appearing or disappearing (Apple docs: `Transition`) — the one place you can least afford a silent state reset.

`AsymmetricTransition<Insertion, Removal>` is the concrete struct backing `.asymmetric(insertion:removal:)` for both `AnyTransition` and custom `Transition`s — `init(insertion:removal:)` stores one `Transition`-conforming value per direction (Apple docs: `AsymmetricTransition`).

`TransitionProperties.hasMotion` exists so accessibility-aware code can ask "does this transition move things" without inspecting its implementation — matched-geometry and zoom-style transitions are exactly the kind of motion Reduce Motion targets; see `apple-design/references/accessibility.md § Reduce Motion` for the gating obligation itself, not restated here.

## `matchedGeometryEffect`: End to End

### Namespace mechanics

A namespace scopes which `id` values are allowed to match each other — two views only link if they share both the same `id` *and* the same `Namespace.ID` (Apple docs: `Namespace`).

- `@Namespace private var namespace` creates a `Namespace.ID` scoped to the persistent identity of the view struct instance holding the property — read `namespace` directly in `body` (it behaves like `@State`'s wrapped value, not a wrapper you dereference).
- **A namespace is not global and not shared by name.** Two sibling views that each declare their own `@Namespace private var namespace` get two *different* `Namespace.ID` values, even though the Swift variable name is identical — matching only happens when the *same* `Namespace.ID` value is threaded to both views (as a parameter, via environment, or because both live in the same parent that owns the `@Namespace`). Declaring `@Namespace` separately in a child view instead of receiving the parent's is a common way to silently break matching — the ids can be identical strings and the effect will still do nothing.

### The modifier itself

Confirmed against the live declaration (Apple docs: `View.matchedGeometryEffect(id:in:properties:anchor:isSource:)`):

```swift
nonisolated func matchedGeometryEffect<ID>(
    id: ID,
    in namespace: Namespace.ID,
    properties: MatchedGeometryProperties = .frame,
    anchor: UnitPoint = .center,
    isSource: Bool = true
) -> some View where ID: Hashable
```

(Apple docs: `View.matchedGeometryEffect(id:in:properties:anchor:isSource:)`.)

- `properties` restricts *which* geometry is copied: `.position`, `.size`, or the default `.frame` (both) (Apple docs: `MatchedGeometryProperties`). Restricting to `.size` alone lets two views share a growing/shrinking size while keeping independent positions (or vice versa with `.position`) — not every pairing needs full frame lock.
- `anchor` is the `UnitPoint` used as the reference point for the shared position value — change it when the views should align by something other than their centers (e.g. `.topLeading`).
- **`isSource` is the discipline that decides which view is authoritative.** The system computes the shared geometry from whichever view in the `id`+namespace group has `isSource: true`, and every other view in that group is driven from it (Apple docs: `View.matchedGeometryEffect(id:in:properties:anchor:isSource:)`). Confirmed verbatim from Apple's own discussion text: "If the number of currently-inserted views in the group with `isSource = true` is not exactly one results are undefined, due to it not being clear which is the source view" — exactly one source view is required at any moment several views in the same group are present; zero sources means nothing defines the shared geometry, and more than one means the two sources can disagree about what that geometry even is.

### Failure modes (jump instead of animate)

- **Mismatched `id`** — a typo, or two ids that are `Equatable`-equal in your head but not in `Hashable` terms (e.g. an `Int` on one side, a `String(describing:)` of it on the other) — produces two unrelated entries; each view just appears/disappears on its own with no interpolation.
- **Different namespaces** — see above; this reads identically to a mismatched id (silent no-op) and is the harder of the two to spot because the `id` values genuinely match.
- **No animation transaction driving the state change** — `matchedGeometryEffect` links geometry, it doesn't itself decide *to* animate. If the state flip that swaps which view is shown isn't wrapped in `withAnimation` (or bound to an `.animation(_:value:)` value), the geometry still links correctly but resolves instantly — a jump, not a morph.
- **Zero or multiple simultaneous `isSource: true` views sharing one id+namespace** — undefined result per the above; typically shows as one instance winning arbitrarily or a visible glitch, especially in a `ForEach` where every row accidentally shares one static `id` instead of a per-row one.
- **Reparenting inside a `ForEach`/`List` without `geometryGroup()`** — SwiftUI normally coalesces position/size changes down to leaf views, so ancestor-level layout changes (e.g. a `ForEach` inserting/removing rows) can apply inconsistently across a matched pair's descendants, producing a visible wobble instead of one clean move. `.geometryGroup()` (Apple docs: `View.geometryGroup()`) forces the parent to resolve its own geometry animation before passing frames down, locking a matched view's subviews together as one rigid unit through the transition — reach for it whenever a matched-geometry pair sits inside a container whose members can be added/removed/reordered independently.

`GeometryEffect` (Apple docs: `GeometryEffect`) is a different, lower-level protocol — despite the name overlap with `matchedGeometryEffect`, it's the foundation for writing an arbitrary continuous geometric transform as a `ViewModifier` (`effectValue(size:) -> ProjectionTransform`, plus `ignoredByLayout()` to apply the transform only visually without affecting layout). It has nothing to do with linking two views' geometry across insertion/removal — don't reach for it when what you actually want is `matchedGeometryEffect`.

## Minimal Correct Pairing Pattern

A single conceptual element toggling between a collapsed and expanded layout, linked by one shared `id` in one namespace, with an explicit (unambiguous) source:

```swift
import SwiftUI

struct MatchedGeometryDemo: View {
    @Namespace private var shapeNamespace
    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 24) {
            if !isExpanded {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.blue)
                    .frame(width: 60, height: 60)
                    .matchedGeometryEffect(id: "card", in: shapeNamespace, isSource: true)
            } else {
                RoundedRectangle(cornerRadius: 24)
                    .fill(Color.blue)
                    .frame(width: 300, height: 200)
                    .matchedGeometryEffect(id: "card", in: shapeNamespace, isSource: false)
            }

            Button(isExpanded ? "Collapse" : "Expand") {
                withAnimation(.spring()) {
                    isExpanded.toggle()
                }
            }
        }
        .padding()
    }
}
```

Why this satisfies the discipline above: exactly one branch exists at a time (`if`/`else` inside a `ViewBuilder`), so exactly one view carries the `"card"` id+namespace pair at any completed frame; marking the collapsed state `isSource: true` and the expanded state `isSource: false` removes any ambiguity about which one defines the shared geometry during the transient frame where both are present mid-transition; and the toggle itself is wrapped in `withAnimation`, so the geometry link actually interpolates instead of jumping.

## Zoom and Navigation Transitions

`navigationTransition(_:)` sets the transition style used when a `NavigationLink` pushes its destination, or a presentation (e.g. a sheet) appears — apply it to the destination view, outside any container like a `VStack` (Apple docs: `View.navigationTransition(_:)`). Confirmed from Apple's own discussion text: "Add this modifier to a view that appears within a `NavigationStack` or a sheet, outside of any containers such as `VStack`."

`matchedTransitionSource(id:in:)` marks the view that visually originates the transition — typically the tappable thumbnail/icon a `NavigationLink`'s label wraps (Apple docs: `View.matchedTransitionSource(id:in:)`). Same `id`+`Namespace.ID` matching discipline as `matchedGeometryEffect`, but this pair spans two independent view hierarchies (source screen, destination screen) connected only through navigation, rather than two views coexisting in one hierarchy toggled by a condition:

```swift
struct ContentView: View {
    @Namespace private var namespace

    var body: some View {
        NavigationStack {
            NavigationLink {
                DetailView()
                    .navigationTransition(.zoom(sourceID: "world", in: namespace))
            } label: {
                Image(systemName: "globe")
                    .matchedTransitionSource(id: "world", in: namespace)
            }
        }
    }
}
```

(Apple docs: `View.navigationTransition(_:)`, example confirmed from live docs.)

A `.zoom(sourceID:in:)` navigation transition is conceptually a system-managed matched-geometry effect purpose-built for navigation: it interpolates the destination's frame from the source's frame the same way `matchedGeometryEffect` interpolates between two sibling views, but it's driven by push/dismiss/presentation events rather than an arbitrary `if`/`else`.

**`matchedTransitionSource(id:in:configuration:)`** is the styling overload — its trailing closure receives an `EmptyMatchedTransitionSourceConfiguration` and returns anything conforming to `MatchedTransitionSourceConfiguration`, letting you apply `.background(_:)`, `.clipShape(_:)`, or `.shadow(color:radius:x:y:)` to the source so those specific visual properties interpolate smoothly during the zoom rather than snapping at either end (Apple docs: `View.matchedTransitionSource(id:in:configuration:)`, `MatchedTransitionSourceConfiguration`). Reach for it only when the source's shape/background/shadow needs to visibly morph into the destination's chrome — plain `matchedTransitionSource(id:in:)` is sufficient whenever the frame interpolation alone is enough.

`NavigationTransition` is the protocol behind the `style:` argument, with built-in conforming types `AutomaticNavigationTransition` (the system default), `ZoomNavigationTransition` (via `.zoom(sourceID:in:)`), and `CrossFadeNavigationTransition` (via `.crossFade`) — a plain dissolve between source and destination with no shared-geometry interpolation at all, the right choice when there's no meaningful visual origin point to zoom from (Apple docs: `NavigationTransition`, `CrossFadeNavigationTransition`). Confirmed: `CrossFadeNavigationTransition` is currently beta across iOS, iPadOS, Mac Catalyst, tvOS, visionOS, and watchOS 27.0 — no stable-release platform yet, and notably no native macOS entry (Mac Catalyst only).

`AnyNavigationTransition` is the type-erased wrapper for dynamically choosing a `NavigationTransition` value at runtime — construct it from any conforming style (`AnyNavigationTransition(.crossFade)`, `AnyNavigationTransition(.automatic)`) when the choice depends on state rather than being fixed at the call site (Apple docs: `AnyNavigationTransition`).
