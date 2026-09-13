> verified: 2026-09 against HIG: Motion (https://developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json); iOS Animations by Tutorials v7.0.0 (Kodeco), ch. 1–5, 7, 10, 12, 13, 23; live SwiftUI DocC JSON for current animation-API surface (`Animation` spring/smooth/snappy/bouncy statics, `PhaseAnimator`, `KeyframeAnimator`); Phase 7 Task 2 added the Cohesion and Worth-It rules and the `committedOffset` snippet fix — no new API claim, so no additional DocC check was needed for either
> sources: HIG: Motion; iOS Animations by Tutorials v7.0.0 (Kodeco); live SwiftUI DocC (API verification); Emil Kowalski's design-engineering writing (emilkowal.ski, MIT-licensed skills — the Cohesion and Worth-it rules only, not Apple-sourced)
> note: the Reduce Motion accessibility obligation is intentionally NOT covered here — `motion.json` doesn't cover that setting; the obligation itself (what to disable, how to gate custom animations) is sourced from the HIG Accessibility page and lives in `accessibility.md` § Reduce Motion. This file covers general motion taste that applies regardless of that setting. UIKit/Core Animation mechanics are isolated under "## Maintaining older code" and don't apply to SwiftUI, which has no separate presentation/model layer.

Implementation mechanics (the APIs) live in the apple-animations skill; this file owns judgment.

# Animation Taste

Motion is a design decision with a cost, not a free polish pass. Every animation you add is milliseconds someone has to wait through, a chance to disorient rather than clarify, and — for anyone with Reduce Motion enabled or vestibular sensitivity — a potential source of real discomfort. The default posture for a review should be suspicion of motion that doesn't earn its place, not appreciation of motion that looks nice in isolation (HIG: Motion, https://developer.apple.com/design/human-interface-guidelines/motion).

## When Not to Animate

- **Add motion purposefully; never add it because the API made it easy.** SwiftUI's implicit-animation model (attach `.animation(_:value:)`, change a `@State` value, get motion for free) makes gratuitous animation the path of least resistance — that ease is exactly why restraint has to be a deliberate choice, not a default (HIG: Motion).
- **Frequent, everyday interactions should stay close to the system's own subtlety.** The system already animates standard controls (buttons, toggles, navigation pushes) with restrained, practiced timing.
- A custom element that fires an elaborate animation on every tap forces people to sit through ceremony each time they use it — reserve expressive motion for infrequent, meaningful moments (a completed purchase, a milestone), not routine ones (HIG: Motion).
- **Never make motion the only channel for essential information.** Anyone who has Reduce Motion on, isn't looking at the screen at that instant, or is using an assistive technology needs the same information some other way — pair meaningful motion with haptics, sound, or a static state change, not motion alone (HIG: Motion).
- **Never trap someone behind an animation they didn't choose to watch twice.** If an animation can play more than once in the course of normal use (a repeated onboarding flow, a re-triggered transition), make sure people aren't forced to wait for it to finish before they can act — this is a bigger tax than a single first-run animation ever is (HIG: Motion).
- For the Reduce Motion accessibility obligation itself — what to disable and how to gate custom animations on it — see `accessibility.md § Reduce Motion`; this section is about motion judgment that applies regardless of that setting.

## Duration and Easing Judgment

- **Ease is the default assumption; linear is the exception.** Nothing in the physical world starts or stops instantly, so unmodulated linear motion reads as mechanical and cheap — reserve `.linear` for content that's inherently continuous and directionless, like an indeterminate progress spinner, not for anything with a clear start and end state (iOS Animations by Tutorials, ch. 3, ch. 12).
- **Match the easing direction to what triggered the motion.** Motion that begins as a direct response to a person's gesture or tap should start at full speed and decelerate into its resting position (ease-out) — starting slow (ease-in) in that position reads as sluggish, because a response to input should feel immediate.
- Motion that's leaving the scene rather than settling into place — a dismiss, an exit — can accelerate away (ease-in) instead, since nothing has to feel instantly responsive at that end.
- Symmetric ease-in-ease-out is the safe, natural-feeling default when neither end of the motion is more important than the other (iOS Animations by Tutorials, ch. 3).
- **Brevity beats visual richness for feedback animations.** A short, precise animation tied tightly to the triggering action communicates faster and more clearly than a longer, more elaborate one — err short, then lengthen only if the shorter version genuinely reads as abrupt (HIG: Motion).
- `Animation.default` is a preset baseline, not a universal correct answer. It was historically a ~0.35s `.easeInOut` curve, but SwiftUI's animation presets have expanded since (named springs like `.smooth`/`.snappy`/`.bouncy` now exist alongside the classic curves) — don't hardcode an assumption about its exact shape into a design decision; either confirm it empirically on the current OS or reach for an explicit named animation (`.easeInOut(duration:)`, `.smooth`, etc.) when the specific feel matters.
- **SwiftUI gives you interruption handling for free that other platforms require you to build.** A person changing their mind mid-animation — tapping again before it finishes, reversing a drag — doesn't produce a broken or half-finished layout; the framework re-targets the in-flight animation toward the new state on its own (iOS Animations by Tutorials, ch. 1).
- Don't build custom interruption logic to solve a problem the framework already solves — check first whether a plain state change mid-animation already does the right thing before reaching for something bespoke.
- **Custom cubic-Bézier control points let you encode intent that named curves can't.** Pulling a control point past the curve's normal 0–1 range produces overshoot: a value that briefly moves *past* its target before settling, or a value that dips *before* it starts moving in its intended direction (an anticipation "wind-up") (iOS Animations by Tutorials, ch. 23).
- This reads as elasticity or emphasis when used sparingly on something worth noticing, and reads as a bug or a comically exaggerated cartoon when overdone or applied to routine motion — treat negative/over-1.0 control points as a strong seasoning, not a base flavor.

## Transition-Type Judgment: What a Transition Should Communicate

A transition is not a generic "fade this in" tool — its type is itself information, and choosing the wrong one actively misleads:

- **Cross-fade (opacity)** communicates a neutral appearance/disappearance with no implied direction or spatial relationship — use it when the incoming/outgoing view has no meaningful spatial origin, or when a directional transition would suggest a relationship that doesn't exist between the two states.
- **Move/slide (edge-anchored offset)** implies the view is arriving from, or departing to, a specific place — use it only when that spatial story is true and useful (a screen genuinely lives "below" the one revealing it), not as a default flourish.
- **Scale** implies the view is growing out of, or shrinking into, a point of origin — appropriate for content that has an obvious origin point (a thumbnail expanding into a detail view), misleading otherwise.
- **Asymmetric transitions** (a different transition for insertion than for removal) are appropriate exactly when the two directions genuinely mean different things — appearing is not always the reverse-in-time of disappearing. Combine and layer transition types only when the composite still reads as one coherent motion, not an accidental collision of two unrelated effects (iOS Animations by Tutorials, ch. 5).

Conceptually, the transition cases worth distinguishing are: a view entering/leaving the hierarchy outright, a view toggling hidden/visible while staying resident, and one view being replaced by another (iOS Animations by Tutorials, ch. 5).

- SwiftUI's `transition` modifier targets the first case — insertion/removal driven by a condition controlling whether the view exists at all.
- Reaching for `transition` to animate a property change on a view that stays in the hierarchy the whole time is the wrong tool; that's what implicit `.animation(_:value:)` is for.

**A transition must match the gesture that reveals or dismisses the content it's attached to.**

- If a view is revealed by sliding down from the top, dismissing it via a sideways slide breaks the mental model the entrance just established.
- The exit motion should feel like a plausible reverse of, or at least a coherent complement to, the entrance (HIG: Motion).

**Gesture-driven animation should track the gesture's live value, not replay a canned trajectory once the gesture ends.**

- Binding an offset or scale directly to a `DragGesture`'s translation while the gesture is active, then animating to a resting state only once it ends, makes the motion feel physically connected to the person's finger.
- A pre-baked animation that merely starts when a gesture starts feels laggy and disconnected by comparison, even at identical duration (iOS Animations by Tutorials, ch. 2; HIG: Motion).

## Spring vs. Eased-Curve Judgment

Not every animation should be a spring, and not every spring should look the same:

- **Reach for an eased curve when the motion has a fixed, known endpoint and no need to communicate character** — layout reflows, cross-fades, anything where "the value gets from A to B smoothly" is the entire brief.
- **Reach for a spring when the motion should feel physically connected to something** — a response to direct touch, a element settling after being dragged, anything where a little overshoot communicates weight, elasticity, or delight rather than just movement.
- **High damping reads as restrained and professional; low damping reads as bouncy and playful.** Calibrate to the emotional register of what's animating (iOS Animations by Tutorials, ch. 4, ch. 13).
- A settings toggle or a data-heavy productivity screen wants a tight, low-overshoot spring; a like button, a completed-purchase confirmation, or anything meant to feel alive can afford visible bounce.
- **The underlying physical intuition — mass, stiffness, damping, and initial velocity — is worth having even if you only ever touch a couple of exposed parameters.** Higher stiffness makes the spring "pull" harder and settle faster; higher mass and higher initial velocity both extend how far and how long it swings before resting; higher damping suppresses that swing (iOS Animations by Tutorials, ch. 13).
- Reasoning about a bounce that's "too much" or "too fast" in these physical terms is faster than blindly trial-and-erroring numeric parameters. Confirmed against live `Animation` DocC: the current SwiftUI spring surface offers several idiomatic entry points rather than one — `.spring(response:dampingFraction:blendDuration:)` (the direct physics-parameter route), `.spring(duration:bounce:blendDuration:)` (duration-first, with bounce standing in for damping), and the named presets `.smooth`, `.snappy`, and `.bouncy` (each a predefined duration/bounce combination, each with a tunable `(duration:extraBounce:)` overload). Prefer a named preset or the `duration:bounce:` form for most product work — they're calibrated to read as "natural" without hand-tuning physics constants; drop to `response:dampingFraction:` only when you need the underlying physical parameters directly.
- **Don't pin a spring-driven animation to an arbitrary fixed duration that doesn't match its physics.** A spring animation has a natural settling time determined by its own parameters; forcing an already-defined spring to a shorter external duration than its natural settle time cuts it off mid-motion and produces a visible jump to the final value instead of a settle (iOS Animations by Tutorials, ch. 13). The modern `.spring(duration:bounce:)` form sidesteps this failure mode by construction — duration is a first-class parameter of the spring's own definition, not something imposed on it afterward, so reach for that form when you know the target duration up front rather than defining a spring by feel and then truncating it to fit.

## Discrete-Phase (Keyframe) Motion

Some motion isn't well modeled as a single continuous interpolation between two states — it has distinct phases with different characters (a launch sequence that accelerates, then tilts, then climbs, then fades) (iOS Animations by Tutorials, ch. 7).

- The judgment that transfers regardless of API: decompose a complex animation into a small number of named phases, each with its own duration and character, rather than trying to force one easing curve or one spring to cover the whole thing.
- A single global easing curve fights internal phase boundaries — each phase transition should feel like a deliberate handoff, not a discontinuity smoothed over by one curve that was never designed for it.
- Relative phase timing (a phase occupying, say, the first 25% of the total duration) is usually a more durable way to express the sequence than absolute per-phase durations, since it survives the whole animation's duration being retuned later without re-deriving every phase boundary by hand.

Confirmed against live DocC: this concept has a direct modern SwiftUI home in two distinct APIs (iOS 17+/macOS 14+), and the choice between them is itself a judgment call. `PhaseAnimator<Phase, Content>` cycles a view through a sequence of discrete, named phase values (each phase producing its own `Animation`) — reach for it when the phases are qualitatively distinct states (idle → charging → released), not points along one continuous curve. `KeyframeAnimator` interpolates one or more `Animatable` numeric tracks through explicit keyframes over a fixed timeline — reach for it when the motion is fundamentally about *values changing over time* (position, scale, rotation each on their own timeline) rather than about discrete named states. Both replace what this book's CALayer keyframe chapter modeled as a single flat keyframe array; the "decompose into named phases first" judgment above applies to picking `PhaseAnimator`'s phase sequence either way.

## Animated State Should Stay Reconciled With Real State

The classic animation bug, independent of platform: the thing on screen mid-animation stops matching the thing your interaction logic thinks is true. In SwiftUI this mostly can't happen by construction — the view *is* a function of state, so what's visible and what's "real" are the same value by default. It reappears the moment you introduce state that only exists for the duration of a gesture or animation and isn't reconciled back into your actual model:

```swift
struct ReconciledDragExample: View {
    @State private var committedOffset: CGFloat = 0
    @GestureState private var dragOffset: CGFloat = 0

    var body: some View {
        Circle()
            .offset(x: committedOffset + dragOffset)
            .gesture(
                DragGesture()
                    .updating($dragOffset) { value, state, _ in
                        state = value.translation.width
                    }
                    .onEnded { value in
                        committedOffset += value.translation.width
                    }
            )
    }
}
```

The transient (`dragOffset`) and committed (`committedOffset`) values are summed for display but only the committed value survives the gesture — get this reconciliation wrong (forget to fold the transient value back in, or let two separate pieces of state drift apart) and you reproduce the same "what's on screen isn't what the app thinks is true" bug that plagued presentation-layer animation in Core Animation, just with different plumbing (iOS Animations by Tutorials, ch. 10).

## Cohesion and Worth-It

Stack-agnostic judgment, not Apple-sourced — see the sourcing note in the header.

- **Cohesion.** Motion should match the component's personality and the rest of the product, not be tuned in isolation. A playful app can afford bouncier springs throughout; a professional dashboard stays crisp and low-overshoot throughout. One bouncy component sitting in an otherwise crisp app doesn't read as character or delight — it reads as a defect, because it breaks the motion vocabulary every other control in the app has already established.
- **Is this detail worth it?** A detail earns its place when its absence would be *felt* rather than *seen* — the interaction would feel subtly wrong or unfinished without it, not merely plainer. Decoration added to frequently-used UI is a recurring cost (milliseconds of delay, a chance to distract or annoy on the thousandth viewing), not a one-time bonus; weigh it against how often the surface is actually used, not against how good it looks the first time.

## Maintaining older code: UIKit / Core Animation

These are genuine footguns in `CALayer`-based animation code that a reviewer of an existing UIKit codebase needs to recognize; none of this applies to SwiftUI, where there's no separate presentation/model layer to desynchronize.

- **The presentation layer is not the model layer.** During a `CABasicAnimation`/`CASpringAnimation`, what's visible on screen is a temporary presentation-layer copy; the underlying model layer's properties don't actually change until you explicitly set them (iOS Animations by Tutorials, ch. 10).
- The presentation layer disappears the instant the animation completes and removes itself, leaving the (unanimated) model layer's original values visible again.
- The fix is to update the model layer's properties to match the animation's final values, ideally right when you add the animation, not to fight this by keeping the animation from being removed.
- **Avoid `isRemovedOnCompletion = false` combined with `fillMode` as a way to "keep the animation visible."** It's a performance cost, and it leaves a non-interactive phantom view on screen that can't receive touches or participate in the rest of the UI (iOS Animations by Tutorials, ch. 10).
- A genuinely interactive-looking text field frozen mid-animation that silently ignores taps is a classic result. Reach for `fillMode` only for animating non-interactive, purely visual layers where no other approach works.
- **`CASpringAnimation` exposes `mass`, `stiffness`, `damping`, and `initialVelocity` directly**, unlike the older `UIView` spring-animation convenience API which only exposes damping and initial velocity and silently adjusts the rest to fit a fixed duration (iOS Animations by Tutorials, ch. 4, ch. 13).
- This is why UIKit's `UIView.animate(…usingSpringWithDamping:…)` springs often feel subtly "forced" compared to a hand-tuned `CASpringAnimation` — use `settlingDuration` to size the animation's duration to its own physics rather than guessing.
- **`CAMediaTimingFunction`/`UIViewPropertyAnimator` custom cubic-Bézier control points are Core-Animation-level API**, distinct from SwiftUI's animation-curve vocabulary — the control-point *intuition* (see Duration and Easing Judgment above) transfers, the specific initializers do not.
- **Layer and animation `speed` values compound hierarchically** — setting `speed` on both a layer and an animation running on that (or a descendant) layer multiplies the effect, which is a common source of "why is this animating 4x faster than I set it to" bugs when speed is adjusted at more than one level of a layer tree.
