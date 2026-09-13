> verified: 2026-09 against https://developer.apple.com/documentation/swiftui/animations, https://developer.apple.com/documentation/swiftui/animation, https://developer.apple.com/documentation/swiftui/withanimation(_:_:), https://developer.apple.com/documentation/swiftui/view/animation(_:value:), https://developer.apple.com/documentation/swiftui/animatable, https://developer.apple.com/documentation/swiftui/spring, https://developer.apple.com/documentation/swiftui/transaction, https://developer.apple.com/documentation/swiftui/contenttransition, https://developer.apple.com/documentation/swiftui/withanimation(_:completioncriteria:_:completion:), https://developer.apple.com/documentation/swiftui/animationcompletioncriteria, https://developer.apple.com/documentation/swiftui/view/animation(_:), https://developer.apple.com/documentation/swiftui/view/animation(_:body:), https://developer.apple.com/documentation/swiftui/customanimation, https://developer.apple.com/documentation/swiftui/animationcontext, https://developer.apple.com/documentation/swiftui/animationstate, https://developer.apple.com/documentation/swiftui/animationstatekey, https://developer.apple.com/documentation/swiftui/unitcurve, https://developer.apple.com/documentation/swiftui/animatablevalues, https://developer.apple.com/documentation/swiftui/animatablepair, https://developer.apple.com/documentation/swiftui/vectorarithmetic, https://developer.apple.com/documentation/swiftui/emptyanimatabledata, https://developer.apple.com/documentation/swiftui/withtransaction(_:_:), https://developer.apple.com/documentation/swiftui/withtransaction(_:_:_:), https://developer.apple.com/documentation/swiftui/view/transaction(_:), https://developer.apple.com/documentation/swiftui/view/transaction(value:_:), https://developer.apple.com/documentation/swiftui/view/transaction(_:body:), https://developer.apple.com/documentation/swiftui/entry(), https://developer.apple.com/documentation/swiftui/transactionkey, https://developer.apple.com/documentation/swiftui/view/contenttransition(_:), https://developer.apple.com/documentation/swiftui/environmentvalues/contenttransition, https://developer.apple.com/documentation/swiftui/environmentvalues/contenttransitionaddsdrawinggroup, https://developer.apple.com/documentation/swiftui/placeholdercontentview; re-checked 2026-09 against https://developer.apple.com/documentation/swiftui/animation/spring(response:dampingfraction:blendduration:) for the `blendDuration` explanation, closing the forward reference from `apple-animations/references/fluid-interfaces.md` (Phase 7 Task 2)
> sources: live Apple docs (no book input; judgment layer: apple-design/animation-taste.md)

# Animation Fundamentals

Mechanics only: what each animation API is, what its parameters compute, and when its shape (not its feel) is the right tool.

For "should I animate this," "which curve/spring feels right," and spring-parameterization taste, see `apple-design/references/animation-taste.md` — this file does not restate that judgment.

## `withAnimation` vs `.animation(_:value:)`

Both ultimately do the same underlying thing — set the `animation` property on the current `Transaction` so that state changes processed under it get interpolated — but they attach at different points.

**`withAnimation(_:_:)`** is an explicit, imperative wrapper around a block of state mutations (Apple docs: `withAnimation(_:_:)`).

- It sets the given `Animation` (default `.default`) as the current `Transaction`'s animation, then runs `body`; any state writes inside `body` are animated under that transaction.
- It's a `rethrows` function returning whatever `body` returns, so it composes with throwing code and non-`Void` results.
- Nesting one `withAnimation` inside another lets the inner call's animation override the outer one for that specific mutation.

**`.animation(_:value:)`** is an implicit, declarative binding (Apple docs: `View.animation(_:value:)`).

- Attach it to a view, give it an `Animation?` and an `Equatable` `value`, and SwiftUI animates that view whenever `value` changes between updates — with no `withAnimation` block required anywhere in the mutating code.
- `value` isn't cosmetic — it's the change-detection key. SwiftUI can only know an animation should fire by comparing `value`'s old and new values, which is exactly why the parameter must conform to `Equatable`.

**The `value:` discipline**: scope `value` to *only* the state that should trigger this particular animation.

- The older, now-deprecated `View.animation(_:)` overload (no `value:` parameter) applied its animation to the view whenever *anything* about the view changed — any animatable property, not just the one you meant (Apple docs: `View.animation(_:)`, marked deprecated).
- That meant an unrelated state change elsewhere in the same view could pick up an animation you never intended. `.animation(_:value:)` exists specifically to close that hole by scoping the trigger to one comparable value.

**`.animation(_:body:)`** is a third, finer-grained form (Apple docs: `View.animation(_:body:)`).

- It hands `body` a `PlaceholderContentView<Self>`, and only the modifiers you apply *inside* that closure use the given animation — everything else on the view falls back to whatever transaction is otherwise in effect.
- Reach for it when you need one animation on one modifier chain without touching the rest of the view.

**Practical split**: reach for `withAnimation` when the state mutation itself is the natural unit (a button action, a gesture's `.onEnded`) and you want the animation co-located with the code that causes the change. Reach for `.animation(_:value:)` when the mutation happens far from the view (bindings, derived state, `@Observable` properties) and it's more natural to declare "animate *this* view when *this* value changes" at the view site instead.

**`withAnimation(_:completionCriteria:_:completion:)`** adds a completion callback via `Transaction.addAnimationCompletion` (Apple docs: `withAnimation(_:completionCriteria:_:completion:)`).

- Guaranteed to fire exactly once — immediately if `body` created no animations at all, otherwise once the animation(s) meet `completionCriteria`.
- `AnimationCompletionCriteria` has two cases (Apple docs: `AnimationCompletionCriteria`): `.logicallyComplete` (default) fires once the animation has reached its logical end state, even if it's still trailing off visually (e.g. a spring's tiny residual oscillation); `.removed` waits until the animation is fully finished and removed from the system before firing.
- Pick `.removed` when the completion action must not run until every visual trace is gone; `.logicallyComplete` is cheaper and usually sufficient for chaining follow-up state changes.

## `Animation` and Timing Curves

`Animation` represents how a view transitions between two values of a state over time — not a value itself, but the shape/pace of the interpolation (Apple docs: `Animation`).

Its built-in vocabulary:

- **`.linear`** / **`.linear(duration:)`** — constant speed throughout; reads as mechanical because velocity never changes.
- **`.easeIn`**, **`.easeOut`**, **`.easeInOut`** (each with a `(duration:)` overload) — vary acceleration across the animation rather than holding it constant, which is what makes eased motion read as natural rather than mechanical.
- **Custom timing curves**: `.timingCurve(_:duration:)` takes a `UnitCurve`; `.timingCurve(_:_:_:_:duration:)` takes four raw control-point doubles to build a cubic Bézier curve directly, for cases the named curves don't cover.
- **Configuration modifiers**, chainable off any `Animation`: `.delay(_:)` (push the start back by N seconds), `.repeatCount(_:autoreverses:)`, `.repeatForever(autoreverses:)`, and `.speed(_:)` (rescale duration).

(All of the above: Apple docs: `Animation`.)

**`UnitCurve`** is the standalone curve type backing custom timing curves (Apple docs: `UnitCurve`).

- A function mapping input progress `[0,1]` to output progress `[0,1]`, built from a cubic Bézier by default.
- Beyond `.linear`/`.easeIn`/`.easeOut`/`.easeInOut`, it also exposes `.circularEaseIn`/`.circularEaseOut`/`.circularEaseInOut` (circular rather than Bézier-based easing) and `.bezier(startControlPoint:endControlPoint:)` for fully custom control points.
- `value(at:)` returns output progress at a given input; `velocity(at:)` returns the curve's first derivative at a given input — useful for querying or reusing a curve's shape outside of driving a SwiftUI animation.
- `.inverse` swaps its axes for reversing a curve.

**`CustomAnimation`** is the escape hatch below all of this: a protocol for defining your own timing function outright rather than composing the built-in curves/springs (Apple docs: `CustomAnimation`).

- Requires `animate(value:time:context:)` — compute the interpolated value at a given time, returning `nil` once the animation is over.
- Requires `velocity(value:time:context:)` and `shouldMerge(previous:value:time:context:)` (whether this animation can merge with another already running on the same property).
- The `context: inout AnimationContext<V>` parameter gives access to `state` (your animation's own persistent storage across frames, via a key analogous to `EnvironmentKey`) and `environment` (the initiating view's environment values) (Apple docs: `AnimationContext`).
- This is rarely needed — reach for it only when neither a curve nor a spring can express the timing you need.

## The `Spring` API

Two layers exist: the `Spring` value type (a standalone representation you can inspect and convert between parameterizations) and `Animation`'s spring-producing static members (which use `Spring` under the hood to build an `Animation`). Mechanically, both expose the same two parameterization families.

**Physical parameters** — `Spring(mass:stiffness:damping:allowOverDamping:)` and the response-based `Spring(response:dampingRatio:)` (Apple docs: `Spring`).

- Describe the spring by the physics that drives it.
- `Animation`'s equivalent, `.spring(response:dampingFraction:blendDuration:)`, uses `dampingFraction` where `Spring`'s own initializer uses `dampingRatio` — confirmed the same quantity under two names: both are documented as "the amount of drag applied … as a fraction of [the] amount needed to produce critical damping" (Apple docs: `Animation.spring(response:dampingFraction:blendDuration:)`, `Spring.dampingRatio`).
- `response` is documented as "the stiffness of the spring, defined as an approximate duration in seconds"; `dampingRatio`/`dampingFraction` is "the amount of drag applied, as a fraction of the amount needed to produce critical damping."
- `blendDuration` is the third parameter on both spring forms above, and it's the one piece neither name explains: when a new spring supersedes one already running on the same property (a reversal, a re-target), `blendDuration` is the time in seconds over which the *response* value interpolates from the outgoing spring's to the incoming one's, rather than switching stiffness abruptly at the handoff instant (Apple docs: `Animation.spring(response:dampingFraction:blendDuration:)`: "the duration in seconds over which to interpolate changes to the response value of the spring"). Velocity is preserved across the handoff regardless of `blendDuration` — that's a separate guarantee of the spring-superseding-spring mechanism itself (see "preserve velocity" below); `blendDuration` only smooths the *stiffness* change, which is what keeps a reversal from reading as a discontinuity even though the underlying motion never actually lost velocity.

**Duration-first parameters** — `Spring(duration:bounce:)`, mirrored by `Animation.spring(duration:bounce:blendDuration:)` (Apple docs: `Spring`).

- Let you state the target settle duration directly and describe bounce as a single scalar, rather than deriving duration as an emergent property of mass/stiffness/damping.
- `Spring` also has `init(settlingDuration:dampingRatio:epsilon:)` for pinning the actual settle time (rather than the perceptual `duration`) with an explicit convergence tolerance (`epsilon`).

**Named presets**, available as both `Spring` statics and `Animation` statics (Apple docs: `Spring`, `Animation`):

- `.smooth` (no bounce), `.snappy` (small bounce), `.bouncy` (higher bounce) — each a predefined duration/bounce pair.
- Each has a `(duration:extraBounce:)` overload to retune while keeping the preset's character.

**Conversion and inspection** (Apple docs: `Spring`):

- `Spring` is convertible in both directions and lets you read back whichever parameterization you didn't construct it with — e.g. `Spring(duration: 0.5, bounce: 0.3)` exposes `.mass`, `.stiffness`, `.damping` computed from those inputs, and vice versa.
- It exposes `settlingDuration` (estimated time to be considered at rest) and lets you query motion directly, e.g. `spring.position(target:time:)`, independent of driving an actual SwiftUI animation.

**Older customizable-spring surface**: `Animation.spring`/`.interpolatingSpring`/`.interactiveSpring` (no arguments or with the physical-parameter forms) (Apple docs: `Animation`).

- `.interactiveSpring` is documented as a convenience for a lower-`response` spring intended for driving interactive, gesture-tracking animations.
- All spring-based `Animation`s preserve velocity when superseded by another spring on the same property mid-flight, rather than restarting from zero velocity.

See `apple-design/references/animation-taste.md` for which of these forms to reach for and why (it already covers this in detail, including why `duration:bounce:` sidesteps the "spring truncated before its natural settle" failure mode) — the summary above is the mechanical shape only.

## The `Animatable` Protocol

`Animatable` is what tells SwiftUI a type has data it can interpolate smoothly frame-by-frame rather than jump-cutting between values (Apple docs: `Animatable`).

- The one requirement is `animatableData`, a computed property whose type must conform to `VectorArithmetic` — an extension of `AdditiveArithmetic` adding `scale(by:)`, `interpolate(towards:amount:)`, and `magnitudeSquared` (Apple docs: `Animatable`, `VectorArithmetic`).
- When an animatable value changes inside `withAnimation` or under an `.animation(_:value:)` trigger, SwiftUI reads the old and new `animatableData`, then calls the setter every frame with an interpolated value computed via `VectorArithmetic` operations — your type gets a chance to update any derived state on each call.

**You rarely need to write this by hand** (Apple docs: `Animatable`).

- SwiftUI supplies built-in `Animatable` conformances for the types that already need one (numeric types, `CGFloat`, `CGPoint`, `CGSize`, `CGRect`, `EdgeInsets`, etc., and shapes/views built from them).
- Where a type maps its stored properties one-to-one onto animatable values, the `@Animatable()` macro generates the `animatableData` property for you rather than requiring it hand-written.

**Write `animatableData` manually only when the interpolated value needs logic that doesn't correspond one-to-one to a stored property** — normalization, clamping to a range, or driving a derived value from the interpolated input (Apple docs: `Animatable`).

- If your custom type is a plain aggregate of already-animatable properties, the macro (or a built-in conformance somewhere upstream) already covers it.
- Reach for manual `animatableData` only once you need to intercept each frame's value.

**Container types for combining animatable values:**

- **`AnimatablePair<First, Second>`** bundles exactly two `VectorArithmetic` values into one animatable unit, and is itself `VectorArithmetic`, so it can serve as `animatableData` for a type with two animatable properties (Apple docs: `AnimatablePair`).
- **`AnimatableValues<each Value>`** is the variadic-generics generalization of the same idea for more than two values. Its declaration (`struct AnimatableValues<each Value> where repeat each Value: VectorArithmetic`) confirms it holds an arbitrary tuple of `VectorArithmetic` values, mirroring `AnimatablePair`'s shape for N values instead of 2 (Apple docs: `AnimatableValues`). Neither type is marked deprecated and neither doc page recommends one over the other for 3+ properties (they're listed side by side under "Making data animatable") — treat `AnimatableValues` as the option for arity above 2 rather than nesting `AnimatablePair`s, not as a documented replacement for `AnimatablePair` at arity 2.
- **`EmptyAnimatableData`** is the explicit "nothing to animate" `animatableData` — a `VectorArithmetic`-conforming empty type for views/shapes whose properties don't need frame-by-frame interpolation at all, rather than leaving `animatableData` unimplemented (Apple docs: `EmptyAnimatableData`).

## `Transaction`: Overriding or Disabling Animation in a Scope

A `Transaction` is the context of the current state-processing update — it's how an animation (or other per-update metadata) propagates through a view hierarchy for one specific change (Apple docs: `Transaction`).

- The root transaction for a given update comes from whichever binding changed, plus anything set globally via `withTransaction` or `withAnimation`.
- Relevant properties: `animation` (the `Animation?` associated with the current update), `disablesAnimations` (a `Bool` that suppresses animation for the scope regardless of what `animation` is set to), `isContinuous` (whether the transaction originated from an action producing a sequence of values, e.g. a live gesture), and `tracksVelocity` (whether velocity of animatable properties is tracked across the transaction).

**Setting a transaction:**

- **`withTransaction(_:_:)`** takes a fully constructed `Transaction` and runs `body` under it — the more general counterpart to `withAnimation`, useful when you need to set more than just `animation` (custom values via a `TransactionKey`, `disablesAnimations`, etc.) in one call (Apple docs: `withTransaction(_:_:)`).
- **`withTransaction(_:_:_:)`** is a scoped variant that takes a `WritableKeyPath<Transaction, V>` and a value, mutating just that one property for the duration of `body` without needing to build a whole `Transaction` (Apple docs: `withTransaction(_:_:_:)`).

**Scoping a transaction to a view:**

- **`.transaction(_:)`** (view modifier) takes `(inout Transaction) -> Void` and applies it to every animation used within that view's scope — e.g. `t.animation = t.animation?.delay(2).speed(2)` to retime an animation, or setting `t.animation = nil` / `t.disablesAnimations = true` to kill it (Apple docs: `View.transaction(_:)`).
- Apple's docs explicitly warn to apply this to leaf views (e.g. `Image`, `Button`) rather than containers (`VStack`, `HStack`) — since it applies to all child views within scope, putting it on a container gives it unbounded reach.
- **`.transaction(value:_:)`** is the value-gated counterpart, mirroring `.animation(_:value:)`'s relationship to `.animation(_:)`: the mutation closure only runs when the given `Equatable` value changes, rather than on every animation the view happens to run (Apple docs: `View.transaction(value:_:)`).

**`disablesAnimations` vs. passing `animation: nil`**: setting a transaction's `animation` to `nil` simply means no animation is specified for that update; `disablesAnimations` is a separate, explicit Boolean flag on `Transaction` (Apple docs: `Transaction.disablesAnimations`). Confirmed use: SwiftUI itself sets it `true` during the initial phase of a two-part transition update specifically to prevent `.animation(_:)` from inserting new animations into that transaction — set it yourself when you need that same "suppress incoming animation for this scope" effect deliberately, e.g. via `.transaction(_:)` (Apple docs: `Transaction.disablesAnimations`).

Custom per-transaction data follows the same pattern as `EnvironmentKey`: conform a type to **`TransactionKey`** with a `defaultValue`, expose it via a computed property on `Transaction` (`self[MyKey.self]`), and set it through that property's key path (e.g. `withTransaction(\.myCustomValue, true) { ... }`) rather than touching the key type directly (Apple docs: `TransactionKey`).

## `contentTransition`: Animating a View's Content In Place

`ContentTransition` animates changes *within* a single view (e.g. a `Text`'s glyphs, an SF Symbol's paths) rather than a view's insertion/removal — that's what SwiftUI's `transition` modifier is for, a different mechanism entirely.

`contentTransition(_:)` only has an effect inside the context of an `Animation` — i.e., wrapped in `withAnimation` or driven by an `.animation(_:value:)` trigger; applied outside any animation context it does nothing (Apple docs: `ContentTransition`, `View.contentTransition(_:)`).

Cases:

- **`.identity`** — content changes don't animate at all.
- **`.opacity`** — the outgoing content fades from opaque to transparent and the incoming content fades in, the default fallback for content that can't interpolate structurally.
- **`.interpolate`** — SwiftUI attempts to interpolate the view's paths directly across the change (e.g. a `Text`'s font/color/weight change, or two SF Symbol glyphs whose paths are compatible), producing a gradual morph rather than a cross-fade.
- **`.symbolEffect(_:options:)`** / the default symbol-effect transition — applies SF Symbol–specific replace/transition behavior to symbol images within the affected hierarchy; unaffected views in the same scope are untouched.
- **`.numericText(value: Double)`** and **`.numericText(countsDown: Bool)`** — built specifically for `Text` views displaying numbers: in supporting environments, digit changes get a dedicated "rolling odometer" transition tailored to counting up or down rather than a generic fade/interpolate.
  - Use `countsDown:` when you know the direction of travel ahead of time (e.g. a countdown timer) — it takes an explicit `Bool`. Use the `value:` form when direction should be inferred automatically: confirmed the doc states "the difference between the old and new values … will be used to determine the animation direction" (Apple docs: `ContentTransition.numericText(value:)`), i.e. it diffs the value across the update rather than requiring you to declare direction.

(All cases above: Apple docs: `ContentTransition`.)

**`EnvironmentValues.contentTransitionAddsDrawingGroup`** controls whether SwiftUI wraps a content transition with `.drawingGroup(opaque:colorMode:)`, compositing the view's contents into an offscreen GPU-rendered image before display (Apple docs: `EnvironmentValues.contentTransitionAddsDrawingGroup`).

- Set `true` to trade memory/compositing overhead for GPU-accelerated rendering of the transition, useful for content transitions that are otherwise CPU-bound to render per frame.
