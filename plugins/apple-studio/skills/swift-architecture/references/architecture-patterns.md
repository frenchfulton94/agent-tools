> verified: 2026-08 against https://github.com/swiftlang/swift-evolution/blob/main/proposals/0395-observability.md, https://developer.apple.com/documentation/observation, https://developer.apple.com/documentation/swiftui/navigationstack, https://developer.apple.com/documentation/swiftui/navigationpath, https://developer.apple.com/forums/thread/731822
> sources: Advanced iOS App Architecture, App Architecture, Design Patterns by Tutorials, Thinking in SwiftUI
> note: TCA currency claim (line ~64) sourced via web search 2026-08, not Apple docs

# Architecture Patterns

## Choose problems, not patterns

Don't start by picking MVVM vs. MVC vs. Redux. Start by naming the actual pain: a screen's logic is unreadable, a change keeps causing regressions elsewhere, a type can't be unit-tested without booting the whole app, two teammates can't work on the same feature without colliding, or builds are slow. Architecture patterns are tools for specific problems, not a checkbox to tick before writing code (Advanced iOS App Architecture, ch. 2). If nothing on your team is actually painful right now, don't add structure pre-emptively — you're solving a problem you don't have yet.

Two root causes explain almost every architecture complaint: **highly interdependent code** (types reaching into each other's concrete internals instead of through small protocols) and **large types** (a view, view model, or manager that has grown too many responsibilities). Whatever pattern you reach for, its only job is to shrink one or both of those. A well-organized MVC codebase can outperform a poorly organized MVVM one — the pattern name is a much weaker predictor of quality than whether types stay small and coupling stays low (Advanced iOS App Architecture, ch. 2).

Before adopting a pattern, or a new layer inside one you already have, run it against these questions — if the answers are bad, the pattern isn't paying for itself here:

- Does it produce boilerplate, and if so does that boilerplate actually make the code easier to follow, or is it just ceremony?
- Does it produce empty pass-through files that just forward calls to another object?
- How much existing code has to be refactored to fit the shape the pattern wants?
- Does it introduce vocabulary/concepts the whole team now has to learn?
- Does it require a third-party dependency?

(Advanced iOS App Architecture, ch. 2)

## A decision lens: five recurring tasks

Whatever the architecture, it has to answer five questions. Use these as the actual axis of comparison instead of comparing pattern names (App Architecture, ch. 2):

1. **Construction** — who builds the view and its dependencies, and when?
2. **Updating the model** — what does a user action actually touch first?
3. **Changing the view** — does the view learn about state changes by direct call, or only by observing something?
4. **View state** — where does transient, non-persisted UI state (selection, scroll position, in-progress edits) live?
5. **Testing** — what can you exercise without spinning up the view hierarchy?

Most disagreements about "is this good architecture" are really disagreements about one of these five, phrased as a pattern-name argument instead.

## Plain SwiftUI is a first-class option, not a placeholder

None of the classic architecture literature had SwiftUI to work with, so it's worth reasoning about this directly rather than retrofitting MVVM-era advice. A SwiftUI `View` is a cheap, declarative value type recomputed from state — it already plays the role that MVC's controller and MVVM's binding layer used to play by hand. `@State` for view-local transient state, `@Observable` model types for shared/business state, and `Environment` for dependency propagation cover the five tasks above for a large fraction of real screens with no additional layer:

- **Construction**: the view initializer plus `@Environment`/`@State` defaults.
- **Updating the model**: a method call on an `@Observable` object, or a local `@State` mutation.
- **Changing the view**: automatic — the `@Observable` macro's synthesized `ObservationRegistrar` tracks exactly which properties a view's `body` read, and only invalidates views that read a property that actually changed. That's finer-grained than `ObservableObject`, where any `@Published` property's change fires the single shared `objectWillChange` publisher and can invalidate every view observing that object, regardless of which specific property that view actually reads.
- **View state**: `@State`, scoped to the view that owns it.
- **Testing**: plain Swift Testing tests against the `@Observable` model, independent of any view.

Default to this. Add a dedicated view-model layer only when one of these becomes false — for example, when the transformation logic between model and displayed values is substantial enough to want its own test target, when the same presentation logic is reused across more than one view, or when a screen's async orchestration (multiple in-flight requests, debouncing, cancellation) is complex enough that burying it in a `View` makes the view file itself hard to read. Even then, prefer a plain `@Observable` class over a Combine-based `ObservableObject` — it's less machinery for the same job and fits Swift 6 concurrency checking more directly: `@Observable`'s tracking is plain Swift with no Combine types involved, so isolating the class to `@MainActor` (the common case for UI-facing state) is generally enough to satisfy strict concurrency checking, whereas `ObservableObject`'s `objectWillChange` is a Combine `ObservableObjectPublisher` that more often creates friction under strict checking. Note that `@Observable` doesn't make a class `Sendable` on its own — actor isolation or explicit `Sendable` conformance is still something you add deliberately either way.

A concrete smell to watch for: a "view model" that does nothing but restate the model's properties one-for-one with no transformation, or that exists only so the screen has "a view model" for consistency's sake. That's the MV- version of an empty pass-through file — cut it and bind the view straight to the model.

## MVVM: when it earns its ceremony

MVVM's actual payoff is narrow: it gives you a layer that has no compile-time reference to the view and can therefore be tested and reused independent of the rendering framework, and it gives designers/engineers a seam where visual redesigns don't ripple into business logic (Advanced iOS App Architecture, ch. 5; App Architecture, ch. 4). It is not, by itself, a fix for a messy screen — a view model can become exactly as bloated as the view controller it replaced if it absorbs coordination and formatting and validation and networking without further decomposition (Advanced iOS App Architecture, ch. 2).

Reach for a real view model (as opposed to plain `@Observable` state, above) when:
- the model-to-display transformation is nontrivial (formatting, aggregation, derived/computed fields) and you want it unit-tested without a view in the loop;
- the same presentation logic backs more than one view (e.g., a `RideOptionPickerViewModel` driving both a segmented control and, say, a list on a wider screen);
- collaboration between screens needs an explicit seam — one scene's view model needs to notify another when something happens, without either one knowing the other's concrete type (Advanced iOS App Architecture, ch. 5).

Two things to avoid regardless of era: piling both UI state and side-effecting dependencies into the same object without separating them (makes the type hard to read even though it's "just a view model"), and building collaborating view model graphs so tangled that no single screen's state changes are traceable in isolation (Advanced iOS App Architecture, ch. 5).

## Redux-style unidirectional state: when the overhead pays off

A single store, immutable state, and reducers as the only path to a state change buys you consistency guarantees you don't get for free anywhere else: every observer sees the same value at the same time, state changes are inspectable and replayable, and reducers are trivially unit-testable pure functions (Advanced iOS App Architecture, ch. 6). That's a real advantage for apps where the same data appears in multiple places simultaneously (iPad multi-pane layouts, dashboards, anything where "these two screens disagreeing" is an actual bug class you've hit).

It's expensive in a different way than MVVM: every feature touches multiple files (action, reducer, state shape, dispatch site), the whole app's state graph can end up implicitly coupled if reducers aren't kept scoped to their own slice, and it doesn't map onto an imperative UI framework as naturally as it does onto a declarative one (Advanced iOS App Architecture, ch. 6) — which is worth noting since SwiftUI itself is declarative and already gives you one-way data flow through `@Observable`/bindings for a single screen. That narrows Redux's unique selling point in SwiftUI to cross-screen state consistency and time-travel/replay debugging specifically, not "unidirectional data flow" in general — you already have that from plain `@Observable` state. Don't add a store-and-reducer library to get something SwiftUI already gives you; add it when you need one global, inspectable source of truth shared by many independent screens. If you go this route, The Composable Architecture (TCA) from Point-Free is the modern equivalent of the `ReSwift` used in the source material and remains the most widely adopted third-party option for this pattern in Swift; current releases target Swift 6's language mode, with `Sendable`-conformant `State`/`Action` types and a `@Reducer` macro built to satisfy strict concurrency checking.

## Coordinator / router: judge it by navigation complexity, not by habit

The coordinator pattern exists to solve one problem: in UIKit, view controllers had to know about their siblings and how to present them, which coupled every screen to its neighbors and made screens hard to reuse or test in isolation (App Architecture, ch. 4; Design Patterns by Tutorials, ch. 23). A coordinator (plus, in some formulations, a router) takes over "what shows after this" so the screen itself only reports *that* something happened, not *what to do about it*.

SwiftUI changes the calculus. `NavigationStack(path:)` binds directly to either a `NavigationPath` or a plain typed array of route values, and either one already externalizes navigation state into a value you can construct, inspect (`.count`, `.isEmpty`), mutate (`.append`, `.removeLast`), and hand to a view from outside — which is most of what a coordinator existed to provide. For deep-link restoration, a typed `[Route]` array is usually the simpler choice when every destination is a single `Codable & Hashable` route type, since you can decode straight into it; `NavigationPath` is for stacks that mix multiple unrelated destination types and exposes its own `codable` property (a `NavigationPath.CodableRepresentation`) for saving and restoring a heterogeneous path, though that only works when every type ever pushed onto it conforms to `Codable`. For a large share of apps, an `@Observable` app-state or router object holding `var path: [Route]` (or a few `NavigationPath`s, one per tab/flow) *is* the coordinator — no protocol hierarchy of `Coordinator`/`Router`/`children` required.

Add a heavier coordinator-style abstraction when you have evidence of one of these, not preemptively:
- a flow (onboarding, checkout, a multi-step wizard) needs to be started from more than one entry point and should be a genuinely reusable, self-contained unit;
- independent feature modules must compose navigation without importing each other's screen types directly;
- you need to unit-test "does this sequence of user actions lead to this screen" without instantiating views.

If none of those apply, a router/coordinator layer is indirection for its own sake — exactly the "empty proxy object" smell called out above. Where you do build one, keep the same judgment the source material applies to UIKit coordinators: decouple screens from *each other*, not from all knowledge of navigation — a screen still knows it can request "go to detail," it just doesn't know how that request gets fulfilled (Design Patterns by Tutorials, ch. 23).

### Maintaining older code: coordinator (UIKit)

In UIKit, the coordinator is a class holding `children: [Coordinator]` and a `router: Router` (usually a thin wrapper over `UINavigationController`); view controllers hold a weak delegate reference to their coordinator instead of instantiating the next view controller themselves, and the coordinator's router does the actual `pushViewController`/`present` call (Design Patterns by Tutorials, ch. 23). If you're extending existing UIKit-coordinator code, keep the convention that a coordinator's own `dismiss` delegates to its router, and that `presentChild` is how parent coordinators track and tear down children — don't have view controllers reach past the coordinator to touch a `UINavigationController` directly, or you've reintroduced the exact coupling the pattern was added to remove.

## Where does networking/data ownership live?

This is really a question about who owns shared state, and the answer generalizes past "networking": **if the fetched data is only ever used by the one screen that fetched it, owning and caching it locally in that screen's state is fine and simpler.** The moment a second screen needs the same data and the two must agree, pull it out into a shared, observable owner (App Architecture, ch. 5).

- *View-owned* (the SwiftUI-era version of "controller-owned networking"): a screen's `@Observable` view model or the view itself issues the request and holds the result as local state. Fast to build, no model layer needed, but every consumer refetches independently and there's no single source of truth once more than one screen wants the same data (App Architecture, ch. 5).
- *Model-owned*: a shared service/store owns the data, performs the fetch, and all consumers observe it. Guarantees consistency across screens and is the only sane option once data is shared, at the cost of needing an explicit shared type up front (App Architecture, ch. 5).

Default to view-owned for screen-specific, non-shared data — it's less machinery. Move to a shared, model-owned store as soon as you can point to a second consumer, and lean that way earlier if you can already see the app's feature set growing, since retrofitting sharing later usually means threading a new observable type through code that assumed local ownership (App Architecture, ch. 5). Either way, keep the actual `URLSession`/networking mechanics out of view code — wrap them in a plain service type regardless of who owns the resulting data, so error handling and request-building aren't duplicated per screen.

## A service/use-case layer for business logic

Independent of whichever presentation pattern you use, it's often worth pulling one unit of business logic — "sign the user in," "delete this item," "submit this form" — into its own small, named, testable type rather than leaving it inline in a view or view model. Name it after the user-facing task, not the mechanism (`SignInUseCase`, not `AuthManager.doStuff`); give it its dependencies through its initializer; and make it independently testable without a view in the loop (Advanced iOS App Architecture, ch. 8).

This earns its keep when the same piece of logic needs to be triggered from more than one screen (a "like" button that shows up in three different lists), when you want functional/integration tests that chain several actions together without touching UI, or when a screen's inline logic has grown large enough that extracting it is the difference between a readable view and an unreadable one (Advanced iOS App Architecture, ch. 8). It's *not* a mandate to wrap every button tap in its own type — a one-line state mutation doesn't need a use-case object around it; that's ceremony without payoff.

## Delegation vs. closures

Default to closures for one-off callbacks — "call me when this finishes," "tell me what was tapped." That's most of what delegation is used for in modern Swift, and a closure captures the call site's context without a separate protocol declaration. Reach for an actual delegate protocol instead when: the relationship has *multiple* related callback methods that belong together as one coherent interface (mirroring `UITableViewDataSource`/`UITableViewDelegate`'s grouping of "provides data" vs. "receives events"), or when the delegating object needs to hold the relationship for its whole lifetime and object identity matters, not just a captured closure (Design Patterns by Tutorials, ch. 4).

Watch for an object accumulating too many delegate protocols — that's usually a large-type smell, and the fix is splitting the object's responsibilities, not adding a sixth delegate. Conversely, if you find yourself wanting a *strong* reference to a delegate (unusual — delegates are normally `weak` to avoid retain cycles), that's a signal the relationship isn't really delegation and a different pattern (or just passing the dependency at initialization) fits better (Design Patterns by Tutorials, ch. 4).

## Observer pattern — mostly subsumed, but keep the judgment

`@Observable`/`@Published` give you the observer pattern natively now, so there's rarely a reason to hand-roll it. The judgment call that still matters: only make a property observable if something legitimately needs to react to it changing. Marking every property `@Published`/observable "just in case" adds machinery and invalidation noise for no benefit — a value that's set once and never mutated again should be a plain `let`, not an observed property (Design Patterns by Tutorials, ch. 8).

## Factory pattern — still useful, now often via DI container or environment

Use a factory when object creation itself has decision logic worth isolating: producing one of several concrete types behind a shared protocol (e.g., turning a decoded server payload into the right model subtype), or building a single type that needs several pieces of configuration/dependencies assembled before it's usable (Design Patterns by Tutorials, ch. 11). In a SwiftUI app this is often satisfied by a small dependency container or by composing values in `Environment`, but the underlying judgment is the same: don't let call sites duplicate the assembly logic for a type that has real construction complexity — centralize it once.

## View composition and decomposition (SwiftUI-specific)

SwiftUI's layout model — parent proposes a size, child decides its own size and reports it back, parent places the child — means composition/decomposition decisions are really about *where you want a sizing or alignment decision to be made*, not just about readability (Thinking in SwiftUI, ch. 4).

**When to extract a separate `View` type vs. a computed property returning `some View`:** a computed property is fine for pure organization — it doesn't change layout behavior at all, since it's inlined into the same view tree. Extract an actual `View` type when the subtree owns its own `@State` or when it's reused in more than one place. Don't extract purely for line-count aesthetics — that's ceremony that doesn't change what the user sees or how the view re-renders.

**When to write a custom `ViewModifier` vs. a container view:** if you're applying the same combination of styling/behavior modifiers across otherwise-unrelated view types (a "card" look, a "destructive action" style), a `ViewModifier` extension is the right unit — it doesn't participate in layout as a new box, it just composes existing modifiers. Reach for an actual container view (a `View` wrapping other views, e.g. a custom stack or card component) when you need to *own layout* — arrange multiple children, coordinate their alignment, or hold state that affects how children are shown.

**`ZStack` vs. `.overlay`/`.background`:** these look interchangeable but aren't — `.overlay`/`.background` size themselves to the *primary* subview only and ignore the secondary view's size for layout purposes, while `ZStack` sizes itself to the union of all its children's frames. A badge or decoration that shouldn't affect a view's footprint among its siblings belongs in `.overlay`, not a `ZStack`; if you actually want the decoration to expand the parent's layout box, that's when `ZStack` is correct (Thinking in SwiftUI, ch. 4).

**Two classic footguns worth knowing before you hit them:**
- `.fixedSize()` forces a view to its ideal size regardless of what's proposed, which is useful for forcing `Text` to stop wrapping/truncating — but SwiftUI doesn't clip by default, so a `.fixedSize()` text can render outside its parent's bounds rather than being constrained (Thinking in SwiftUI, ch. 4).
- Inside `HStack`/`VStack`, a flexible-looking child (like `Text`) can still wrap or truncate even when there's visually "enough room," because the stack allocates remaining width across children in order of least-to-most flexible, not by final visual outcome. If a particular child should win the space contest, give it explicit `.layoutPriority(_:)` rather than fighting the default allocation order (Thinking in SwiftUI, ch. 4).

**Custom alignment guides:** reach for a custom `AlignmentID`/`HorizontalAlignment`/`VerticalAlignment` only when you need sibling views *nested inside different containers* to align with each other — e.g., a circular button at the bottom of a `VStack` that must line up with buttons nested one level deeper inside sibling `HStack`s. A built-in `.leading`/`.center`/`.trailing` alignment parameter on the stack itself is sufficient whenever everything that needs to line up is a direct child of the same container; don't reach for custom alignment IDs to solve a problem a plain stack alignment parameter already solves (Thinking in SwiftUI, ch. 4).

## What each pattern actually buys you in testability

"More testable" is the most common justification for adding architecture, so be specific about what kind of testability you're actually getting:

- **Plain MVC-style code** (logic living directly in a view controller or, in SwiftUI, an untyped mix of view and inline logic) is really only exercisable through integration tests that stand up the whole connected view/model graph — expensive to write, but they do cover the wiring between components, not just the logic in isolation (App Architecture, ch. 3).
- **MVVM's view model** gives you a real seam: interface tests that construct the view model directly, drive its inputs, and assert on its published outputs, with no view in the loop at all. That's cheaper to write and faster to run, but it only covers the view model — logic left behind in the view itself (there's always some) is untested by this layer (App Architecture, ch. 4).
- **Redux-style reducers** are pure functions of `(state, action) -> state`, so they're the cheapest thing here to test exhaustively: no view, no view model, not even the store — just call the reducer and assert on the result (Advanced iOS App Architecture, ch. 6).
- **A `@Observable` model plus plain SwiftUI views** sits close to the MVVM case: the model is directly testable with Swift Testing since it has no view dependency, and the view itself is thin enough that most teams accept covering it with UI/snapshot tests rather than unit tests.

Pick the minimum layer that gives you the specific testing guarantee you actually need. If you don't have a concrete testing pain point today, this isn't a reason to add a layer preemptively — it's a reason to keep the option available (small, protocol-seamed types) without building the seam until something needs it.

## Mixing patterns and changing your mind later

Patterns in this space were mostly designed independently, not to be combined — but nothing stops you from doing so, and real codebases usually end up as a blend rather than a pure instance of one pattern (Advanced iOS App Architecture, ch. 2). A screen with heavy shared cross-screen state can use a small Redux-style store while the rest of the app stays plain `@Observable` state; a complex flow can get a coordinator while simple flows just push onto a shared `NavigationPath`. Consistency within one screen or one flow matters far more than consistency across the whole app — don't force-fit a pattern onto a part of the app that doesn't need it just to keep the codebase "uniform."

This also means the choice isn't permanent. Try a pattern on a real screen before committing the whole app to it; if it doesn't pay off, back out of it on that screen rather than treating the initial choice as a one-way door (Advanced iOS App Architecture, ch. 2). Draw a baseline for new code, but expect to revisit it once you've seen how it holds up against a real feature, not a toy example.

## Quick reference: red flags that a pattern isn't paying for itself

- A "view model," "coordinator," or "use case" that only forwards calls with no transformation or decision logic of its own.
- Multiple files touched for every trivial feature addition (classic Redux/unidirectional overhead when applied to a screen that doesn't need cross-screen consistency).
- A delegate protocol with one method that's really just a closure wearing a costume.
- View state duplicated between an `@Observable` model and the view's own `@State` "just in case."
- A navigation abstraction (coordinator/router) built before there's a second flow, a second entry point, or a testing need that justifies it.
- Extracting view types purely to shorten a file, with no state, reuse, or diffing motivation behind the split.
- Adopting VIPER/Clean-Architecture-style strict layering "to fix massive views" and ending up with *more* total code and more indirection than the massive view it replaced, because the layering was applied uniformly instead of where the complexity actually was (App Architecture, ch. 2).

When in doubt, apply the same test the source material applies to every pattern it covers: does this concretely shrink coupling or shrink a type that's actually too large right now — or does it just add vocabulary and files. If it's the latter, don't add it yet.
