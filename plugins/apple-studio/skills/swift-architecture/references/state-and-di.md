> verified: 2026-08 against https://developer.apple.com/documentation/observation.md, https://developer.apple.com/documentation/observation/observable().md, https://developer.apple.com/documentation/swiftui/state.md, https://developer.apple.com/documentation/swiftui/stateobject.md, https://developer.apple.com/documentation/swiftui/view/id(_:).md, https://developer.apple.com/documentation/swiftui/bindable.md, https://developer.apple.com/documentation/swiftui/environment.md, https://developer.apple.com/documentation/swiftui/environmentvalues.md, https://developer.apple.com/documentation/swiftui/environmentkey.md, https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro.md, https://github.com/swiftlang/swift-evolution/blob/main/proposals/0395-observability.md
> sources: Advanced iOS App Architecture, Thinking in SwiftUI

## Where should a given piece of state live?

Decide by asking, in order:

1. **Does only this view need it, and is it fine for it to reset when the view's identity resets?** → `@State` (value type or `@Observable` reference type). This is the default; reach for anything heavier only when one of the next questions forces you to.
2. **Does a child need read/write access to a value it does not own?** → `@Binding`. The child stays agnostic about where the value actually lives (Thinking in SwiftUI, ch. 3).
3. **Do many unrelated views, at arbitrary depth, need the same dependency without threading it through every initializer?** → SwiftUI environment.
4. **Does the object need to be shared, outlive individual view identity churn, be constructed with real dependencies, and be substitutable in tests independent of any view?** → own it outside the view tree (a DI container, an app-level root object) and inject it — via initializer where possible, via environment where it must reach deep into the view tree.

The classic mistake in both directions: promoting view-local UI state (a toggle's expanded/collapsed flag, a form's draft text) into a shared model "to be safe," and conversely stuffing business/service state into `@State` where it silently resets whenever the view's identity changes. Ownership should track the *actual* lifetime and sharing requirement of the data, not convenience.

## Identity governs state lifetime — the classic source of bugs

SwiftUI views are ephemeral value-type blueprints; the persistent thing is a render-tree node, and state lives attached to that node, not to the view struct. A node's identity is derived implicitly from its position in the view tree (structural identity), and can additionally be set explicitly with `.id(_:)`. When identity changes, SwiftUI destroys the old node (and all state attached to it, including `@State`, timers, `.task` work) and creates a fresh one; when identity is preserved, the node — and its state — persists across re-renders even though the view struct is rebuilt from scratch every time (Thinking in SwiftUI, ch. 2).

This produces two opposite classes of bugs, and the fix for both is the same skill: reason explicitly about whether the identity of the relevant view is changing.

**State doesn't reset when it should.** A view reused for different underlying data (e.g., a detail view for whichever item is selected) keeps its old `@State` if its identity doesn't change, because from SwiftUI's point of view it's the "same" view being updated, not a new one. The fix is to key the view's identity to the data with `.id(item.id)`, so switching items is modeled as swap-in of a new node rather than an update of the existing one.

**State resets when it shouldn't.** Any construct that introduces a branch in the view tree — `if`/`else`, `switch`, or a helper that conditionally wraps a view in a modifier — creates distinct identities per branch. Toggling the condition doesn't update a node in place; it tears one down and stands up another, discarding any `@State` that lived on it. A frequently-hit variant is a "conditionally apply a modifier" helper (`view.applyIf(condition) { $0.modifier() }`) that looks harmless but silently forks the tree into a `ConditionalContent` with two branches; avoid this pattern and instead make the *modifier's argument* conditional (e.g., `.background(condition ? .red : .clear)`) so the tree shape — and identity — stays stable (Thinking in SwiftUI, ch. 2).

**Initializer arguments don't update existing state.** Passing a new value into a view's initializer only changes the *initial* value of a `@State` property; once the node already exists, the initializer isn't re-run in a way that affects the live state, so the visible value doesn't change until the node is torn down and recreated. If a view needs to react to an externally-changing value after it's already on screen, that value shouldn't be owned via `@State` seeded from an initializer parameter — either drive it with a `@Binding`, hold the owning object outside the view and read it as a plain property, or explicitly re-key identity with `.id`.

Practical rule of thumb: only reach for `@State` (or `@StateObject` in legacy code) when the initial value can be assigned directly on the declaration line. If you find yourself wanting to pass a value into the initializer and assign it to a `@State`/`@StateObject` property, that's a signal the view either needs a `@Binding`, needs the object owned elsewhere and passed as a plain property, or needs its identity deliberately re-keyed.

## Observation framework (`@Observable`) — the modern default

`@Observable` is a macro (not a base class or protocol you implement) that instruments a class so that reading a property inside a tracked context (a view's `body`, `withObservationTracking`) registers a dependency on that specific property, and writing it notifies only the contexts that read it. Two consequences that should shape how you write model types:

- **Observation is automatic and reference-agnostic.** Any `@Observable` object's properties accessed in a view's body form a dependency *no matter how the object got there* — nested in an optional, in an array, reached through a global singleton, or handed in as a plain (unwrapped) property. You no longer need a property wrapper on the consuming side just to "opt in" to observation.
- **Granularity is per-property, not per-object.** A view that reads only `model.title` won't re-render when `model.subtitle` changes. This removes most of the old pressure to artificially split a model into many small `ObservableObject`s purely to control render granularity — but it's still worth keeping models focused, since per-property tracking doesn't help if a view's body happens to touch everything on a large model anyway.

**`@State` now serves one purpose with `@Observable` objects: lifetime, not observation.** Observation "just happens" from property access; `@State` is only needed when you want SwiftUI to own and preserve the object across the view's re-renders (i.e., the object is private, view-owned state). If the object's lifetime is owned somewhere else and simply handed to the view, store it as a plain property with no wrapper at all — wrapping an externally-owned `@Observable` object in `@State` reintroduces the "initializer only sets the initial value" bug described above.

**`@Bindable`** is needed only when you must construct a `Binding` (`$…`) into a property of an `@Observable` reference type — e.g., handing `$model.value` to a `TextField` or `Stepper`. Since `@Observable` properties are plain stored properties (no property-wrapper `projectedValue`), the `$` syntax isn't available directly on them; `@Bindable` (as a property wrapper, or inline via `Bindable(model)`) supplies it.

## Maintaining older code: `ObservableObject`

`ObservableObject` + `@Published` + `@StateObject`/`@ObservedObject` is the pre-iOS-17, Combine-backed observation model. Reach for it only when maintaining a codebase already built on it or targeting OS versions before the Observation framework's minimum, not for new code on a modern baseline.

The practical difference that matters when reading legacy code: `ObservableObject`'s `objectWillChange` publisher fires once per **object**, so any view observing that object re-renders on **any** published-property change, not just the one it reads — `@Observable`'s per-property tracking is strictly finer-grained. `@StateObject` parallels `@State` (view-owned lifetime, must be assignable on the declaration line, same "initializer only sets the initial value" trap); `@ObservedObject` parallels a plain `@Observable` property (no lifetime ownership, must be passed in from the outside, must not be constructed inside the view's initializer) (Thinking in SwiftUI, ch. 3). Don't mix the two systems inside one model type — pick one observation model per object.

## Bindings, briefly

A `Binding` is a getter/setter pair standing in for "read-write access to a value without knowledge of, or ownership over, where it's actually stored" — it exists to preserve a single source of truth while letting components read *and* write without becoming that source of truth themselves. Use `@Binding` for reusable, control-like views (a custom toggle, a form field) that mutate a parent's state; don't use it as a general substitute for passing a shared model, which is what an `@Observable` reference type already gives you for free.

## Dependency injection without a framework

DI here just means: dependencies are provided to an object from the outside (initializer, property, or method) rather than the object reaching out to construct or locate them itself. Do this without a framework — plain Swift closures, protocols, and structs are sufficient at any app size (Advanced iOS App Architecture, ch. 4).

**Injection style, in order of preference:** initializer injection whenever the object cannot function without the dependency (dependency is stored as an immutable, non-optional property, and there's no "not yet configured" state to handle). Fall back to property injection only when the framework controls object creation and you don't get to choose the initializer. Method injection is for dependencies used within a single call and not worth holding as state — prefer it over storing something an object rarely needs.

**Substitutability requires two separate decisions.** First, does this dependency need to be substitutable at all — pure/no-side-effect logic usually doesn't; anything touching the network, disk, or other non-deterministic effects usually does. Second, if it does, at compile time (build-configuration-gated, e.g., a fake API for a Test scheme) or at runtime (feature flags, launch arguments, TestFlight cohorts) or both. Either way, define a protocol for the dependency and centralize the resolution (which concrete type backs the protocol) at exactly one call site — don't scatter `#if`/`if` substitution logic across every place the dependency is constructed.

### The escalation ladder

Don't start at the top. Each rung solves a specific pain the previous one causes — introduce it when you hit that pain, not preemptively:

1. **On-demand.** Each consumer builds the full dependency graph it needs, right where it needs it. Fine for a small app or a single feature; breaks down once dependency graphs get deep, because every consumer duplicates the same construction logic and must know the full transitive graph.
2. **Factories.** Centralize construction into one stateless factories type with a method per dependency/object; consumers call a factory method instead of assembling the graph themselves. Solves duplication for *ephemeral* objects, but has no way to hold onto long-lived (singleton-like) dependencies.
3. **Single container.** A stateful version of the factories type: it holds long-lived dependencies as stored properties (initialized once, in `init`) alongside factory methods that can pull them for free (no parameters needed) instead of receiving them as arguments. Solves long-lived-dependency management, at the cost of becoming a large, growing type, and often forces optional-typed properties for dependencies that only exist during part of the app's lifetime (e.g., "the current user," which is `nil` while signed out) — every consumer of that optional now has to force-unwrap or handle absence redundantly.
4. **Container hierarchy.** Split the single container by *scope* — app, user/session, feature, interaction — each mapping to its own container tied to a real lifetime boundary (created/destroyed when that scope starts/ends). A child container takes its parent as an initializer dependency (or copies the specific values it needs out of the parent) so it can resolve app-level dependencies while adding its own scope-level ones; the rule is strictly one-directional — a parent never reaches into a child, since a child's lifetime is shorter and the parent can't assume any particular child instance currently exists. The payoff that matters most: data that's optional at the container-hierarchy's root (a signed-in user) becomes a required, non-optional, immutable property of the child scope's container, because that scope's container simply cannot exist unless that data exists — eliminating a whole class of redundant nil-checks. The cost is more types and a steeper onboarding curve for anyone new to the codebase.

**When to stop escalating:** a single small container (or even on-demand construction) is entirely adequate for an app whose whole object graph is a handful of services. Reach for a container hierarchy specifically when you have a recurring, painful *optional* representing a real lifetime boundary (signed-in session, active document, in-progress multi-step flow) that many consumers have to redundantly unwrap or guard — not because "big apps use container hierarchies."

## SwiftUI's environment vs. a hand-rolled container

Both are legitimate DI mechanisms in a SwiftUI app; they solve different problems and are normally used *together*, not as alternatives.

**`@Environment`/`.environment(_:)`** is SwiftUI's built-in mechanism for making a value or object reachable by any descendant view without threading it through every initializer in between. Reach for it when:
- The consumer is a **view**. The environment only reaches into the view tree; a plain `@Observable` service, use case, or repository type can't read from it, so those still need ordinary initializer injection regardless of how the view layer is wired.
- The dependency is genuinely cross-cutting — a shared app-wide model many unrelated screens read, a theme, locale, or feature-flag value — such that prop-drilling it through every intermediate view's initializer would be pure noise.
- You're comfortable with its default-value/optional-friendly failure mode: a missing custom environment key falls back to a declared default rather than failing to compile, which is convenient but means "this view forgot to inject its dependency" becomes a runtime concern (often only caught in a preview or at first use) instead of a compile-time one.

**Initializer injection (with or without a hand-rolled container)** is preferable when:
- The dependency is *required* for the type to function at all — making it an explicit initializer parameter documents the dependency in the public API and lets `swift-testing` construct the type directly with fakes, with no SwiftUI environment or view hierarchy involved.
- You want the compiler, not a runtime default, to enforce that the dependency is present.
- The object under construction isn't a view — a view model, a service, a repository — where environment doesn't apply at all.

**The normal shape of a real app combines both:** a small app-level container (on-demand, factories, or a container as warranted by the escalation ladder above) constructs the real object graph using initializer injection throughout, including the shared root `@Observable` model(s). That root model is then placed into the environment once, near the top of the view tree, so deeply nested views can read it without every intermediate view's initializer needing to know about it — while each view still takes its own view-specific, required dependencies directly as initializer parameters. Don't build a container hierarchy for an app whose entire graph would fit in a single view's initializer; equally, don't lean on the environment for a dependency that's only used by one or two views and would be clearer, more testable, and more discoverable as a plain initializer parameter.
