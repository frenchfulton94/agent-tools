> verified: 2026-09 against https://developer.apple.com/documentation/swiftui/draggesture/value, https://developer.apple.com/documentation/swiftui/draggesture/value/velocity, https://developer.apple.com/documentation/swiftui/draggesture/value/predictedendtranslation, https://developer.apple.com/documentation/swiftui/draggesture/value/predictedendlocation, https://developer.apple.com/documentation/swiftui/gesturestate, https://developer.apple.com/documentation/swiftui/buttonstyleconfiguration/ispressed, https://developer.apple.com/documentation/swiftui/spring, https://developer.apple.com/documentation/swiftui/animation/spring(response:dampingfraction:blendduration:), https://developer.apple.com/documentation/swiftui/animation/interactivespring(response:dampingfraction:blendduration:), https://developer.apple.com/documentation/swiftui/animation/interpolatingspring(_:initialvelocity:), https://developer.apple.com/documentation/swiftui/scrolltargetbehavior, https://developer.apple.com/documentation/swiftui/scrolltargetbehaviorcontext, https://developer.apple.com/documentation/swiftui/scrolltargetbehaviorcontext/velocity, https://developer.apple.com/documentation/swiftui/scrollbouncebehavior, https://developer.apple.com/documentation/swiftui/view/scrollbouncebehavior(_:axes:), https://developer.apple.com/documentation/swiftui/view/presentationdetents(_:), https://developer.apple.com/documentation/swiftui/view/presentationdragindicator(_:), https://developer.apple.com/documentation/swiftui/view/interactivedismissdisabled(_:), https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct, https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct/normal, https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct/fast; the shipped `DragGesture.Value.velocity` body in iPhoneOS27.0.sdk SwiftUI.swiftinterface (arm64e-apple-ios); deceleration constants (normal 0.998, fast 0.99) measured at runtime on an iOS 27.0 simulator, because the doc pages above publish no values; the 1.996x projection ratio and SwiftUI's flat 0.250000 s of projected travel measured at runtime on an iOS 27.0 simulator over 48 flicks, both directions, 201-2125 pt/s (min 1.995999, max 1.996000); the release-boundary behavior measured on the same build — a `@GestureState` reset and a `withAnimation` on a separately committed offset do not land in one graph update, 191-210 pt of snap-back on a 210 pt drag on 12 of 12 flicks, confirmed in screen-recorded pixels
> sources: live Apple docs; Designing Fluid Interfaces (WWDC 2018); shipped SDK interface

# Fluid Interfaces: Gesture-Driven Motion

The seam between a finger and a spring: what SwiftUI already does for you, the two
places the handoff goes wrong silently, and the technique left where there is no API.

Boundaries. `animation-fundamentals.md` owns the animation APIs themselves —
`withAnimation`, `Transaction`, the `Spring` parameterizations, `blendDuration`;
`apple-design/references/animation-taste.md` owns whether to animate and how much.

## What SwiftUI already does

Five fluid-interface principles are free on this stack. A reader who does not know
they are free will hand-roll them, and the hand-rolled version is worse.

- **Respond on touch-down, not on touch-up.** `ButtonStyleConfiguration.isPressed` is
  already true while the finger is down. In a `ButtonStyle`, drive a `scaleEffect` or
  a tint from it. Do not attach a `DragGesture` to a button to find this out.
- **1:1 tracking.** `@GestureState` with `.updating` moves the element with the finger
  and resets it when the gesture ends. Set `transaction.disablesAnimations = true`
  inside the `updating` body — while the finger is down there is nothing to smooth,
  and a spring there is lag you added deliberately. Before summing that state with a
  separately animated position, read the release-boundary warning in "Velocity handoff".
- **Animate from the presentation value.** Spring animations retarget from where the
  element currently is, at the speed it currently has. Interrupting one does not jump
  and nothing needs to read the current position first. This is a spring-to-spring
  guarantee only — it does not survive the end of a gesture; see "Velocity handoff".
- **Grab and reverse mid-flight.** Same mechanism. An element already flying toward a
  target can be caught and thrown back, and velocity carries across. Do not write
  interruption logic — writing it is how this gets broken.
- **Blend velocity on reversal.** `blendDuration` on the `spring` family smooths
  between successive springs on one property instead of switching abruptly. Explained
  in `animation-fundamentals.md`; not restated here.

**And a sixth, before any of the code below: a multi-position sheet is free.**
`.presentationDetents([.medium, .large])` (iOS 16) gives a standard `.sheet` more
than one resting height, and the system supplies the drag tracking, the snap
between detents, the rubber-band at the ends, and interactive dismiss — none of it
yours to write. `.presentationDragIndicator(_:)` adds the grabber;
`.interactiveDismissDisabled(_:)` withholds drag-to-dismiss where the sheet must
not be abandoned mid-task. Hand-roll a drag only for what a detent sheet cannot
express: a surface that is not a sheet, a snap target computed from momentum at
release rather than chosen from a fixed set, or motion on an axis the sheet does
not offer. **That case is what the rest of this file is about.** Reaching for the
code below when `presentationDetents` would have done is the most expensive
mistake available here.

## Momentum projection and the 0.25 s prediction

`DragGesture.Value.predictedEndTranslation` is documented as a prediction of the final
translation "if dragging stopped now," and the documentation stops there — it never
says how far it projects. The shipped interface does, because `velocity` is declared
`@export(implementation)` and therefore ships its body rather than only its signature:

```
velocity = CGSize(width:  4.0 * (predictedEndLocation.x - location.x),
                  height: 4.0 * (predictedEndLocation.y - location.y))
```

Invert it: `predictedEndLocation == location + velocity * 0.25`. **SwiftUI projects a
flat 0.25 s of travel**, with no deceleration model behind it.

Apple's projection from *Designing Fluid Interfaces* is the closed form of exponential
deceleration — `(v / 1000) * d / (1 - d)`, where `d` is the per-millisecond
deceleration rate a scroll view uses. At `d = 0.998` that is 499 ms of travel:
**1.996x** what `predictedEndTranslation` gives for the same flick. Call it double when
you talk about it, but it is a constant rather than an approximation — `0.499 / 0.25` is
exact, and it held to six decimal places across 48 measured flicks from 201 to 2125 pt/s,
each of which put SwiftUI's own projection at 0.250000 s.

```swift
/// Apple's projection from Designing Fluid Interfaces (WWDC 2018).
/// decelerationRate 0.998 matches UIScrollView.DecelerationRate.normal,
/// measured on iOS 27.0; 0.99 (.fast) is snappier.
func project(initialVelocity: CGFloat, decelerationRate: CGFloat = 0.998) -> CGFloat {
    (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate)
}
```

Which to use:

- **`predictedEndTranslation` — a modest snap.** A sheet that commits or springs back,
  a two- or three-position drawer. The targets are far apart, so landing short of the
  true momentum is invisible and the arithmetic is free.
- **`project(initialVelocity:)` from `.velocity` — anything that should feel like
  scrolling.** A carousel, a picker, a long strip of snap points. Half-distance
  projection here is the bug everyone recognizes and nobody can name: the flick that
  stops one item early.

Apple no longer publishes the deceleration constants — the `UIScrollView.DecelerationRate`
pages for `normal` and `fast` carry an abstract and no value. Both were read at runtime
on an iOS 27.0 simulator; measure again if a later OS changes the feel.

Inside a `ScrollView` none of this applies: a custom `ScrollTargetBehavior` receives
release velocity directly as `ScrollTargetBehaviorContext.velocity`.

## Velocity handoff

`Animation.interpolatingSpring(_:initialVelocity:)` does accept the gesture's velocity,
but in **units of the from-to distance per second**. `DragGesture.Value.velocity` is in
**points per second**. Handing one to the other raw is the second trap: over a short
remaining distance the spring gets a number scaled by the very distance it should have
been divided by, and the element overshoots hugely. No crash, no warning, no compiler
complaint — it just looks broken.

Normalize by the **signed** distance still to travel, `target - released`. The sign is
load-bearing: a flick toward the top pairs a negative velocity with a negative delta and
the two cancel. `abs()` there hands the spring a negative normalized velocity — it reads
the element as moving away from its target and lurches backward before pulling in. Guard
the near-zero case rather than flooring the divisor; a floor passes raw points per
second straight through, which is the overshoot this section exists to warn about:

```swift
struct DismissableCard: View {
    @State private var offset: CGFloat = 0
    @State private var lastOffset: CGFloat = 0
    let snapPoints: [CGFloat] = [0, 200, 400]

    var body: some View {
        Color.clear
            .offset(y: offset)
            .gesture(
                DragGesture()
                    .onChanged { value in
                        // translation is measured from this drag's start, so it is
                        // added to where the last drag left the card, never assigned.
                        var t = Transaction()
                        t.disablesAnimations = true
                        withTransaction(t) { offset = lastOffset + value.translation.height }
                    }
                    .onEnded { value in
                        let released = offset
                        let projected = released + project(initialVelocity: value.velocity.height)
                        let target = snapPoints.min {
                            abs($0 - projected) < abs($1 - projected)
                        } ?? 0
                        lastOffset = target
                        // SIGNED — abs() here inverts the normalized velocity.
                        let delta = target - released
                        guard abs(delta) > 0.5 else {
                            withAnimation(.snappy) { offset = target }
                            return
                        }
                        withAnimation(.interpolatingSpring(
                            .snappy, initialVelocity: value.velocity.height / delta
                        )) { offset = target }
                    }
            )
    }
}
```

One stored value carries the drag and the release. That is not a stylistic choice.
Holding the live translation in a separate `@GestureState` and summing it with a
separately animated position **does not hand off continuously**: measured on iOS 27.0,
the gesture-state reset and the `withAnimation` on the committed value do not land in
the same graph update, so at release the composed offset renders at the pre-drag
position for a frame and the spring starts from there — the entire drag discarded and
then re-travelled, with `initialVelocity` normalized against a distance the animation
no longer covers. Write the drag into the value the release animates, and there is
nothing left to desynchronize.

**One scope limit on this example, derived by reading it rather than by measuring
it.** It does not support being caught mid-flight. Section 1's framework claim
holds — a spring retargets from wherever the element currently is — but that is a
property of the animation, and this gesture never asks for it: `lastOffset` is
committed to `target` at release, so a finger landing on a card still in flight
computes `offset = lastOffset + value.translation.height` from the *destination*,
with animations suppressed, and the card jumps by the travel that remained.
`@State offset` holds the animation's target, not its presentation value. Catching
an in-flight card means reading the presentation value at touch-down and committing
that instead. Treat this as unmeasured, because it is: nobody has put a finger on a
flying card here. The paragraph above is the same shape of claim and it was wrong
from reading alone until it was measured, which is the reason this one is labelled.

## Boundaries

A scrollable view already rubber-bands. `.scrollBounceBehavior(_:axes:)` configures it
— `.automatic`, `.always`, or `.basedOnSize` (bounce only when the content is actually
long enough to scroll), per axis.

A `DragGesture` gets none of it. The shipped SwiftUI interface has no public API for
resistance, overscroll, or rubber-banding of any kind; a custom drag past its own bound
tracks the finger 1:1 straight off the end unless you write the resistance yourself:

```swift
/// The further past the bound, the less the element follows.
func rubberband(overshoot: CGFloat, dimension: CGFloat, constant: CGFloat = 0.55) -> CGFloat {
    (overshoot * dimension * constant) / (dimension + constant * abs(overshoot))
}
```

Apply it **while tracking**, to the part of the translation that exceeds the bound,
before the value reaches any spring. `dimension` is the container extent along the drag
axis, so resistance scales with the element; `constant` is the tightness. Applying it
after the gesture ends is a different effect — a spring overshooting, not a boundary.

## Technique with no API

Four rules nothing in SwiftUI enforces.

- **Decompose 2D motion into independent X and Y springs.** One spring driving a 2D
  distance desynchronizes as soon as the axes carry different velocities: the slow axis
  is dragged to finish with the fast one, and a flick that was mostly horizontal
  arrives diagonally. Animate each axis against its own axis velocity.
- **Point the intermediate frames at the outcome.** Motion between two states should
  say where it is going from its first frame, rather than interpolating blindly and
  revealing the answer at the end. A sheet that leans in the direction it will travel
  is legible mid-gesture; one that merely slides is not.
- **Keep per-frame positional change below the perception threshold.** Smoothness is a
  property of step size between frames, not of frame rate alone: a large jump reads as
  a stutter even at a steady 120 Hz. Profiling it belongs to `apple-performance`.
- **Bounce only when the gesture carried momentum.** Overshoot is the visual record of
  energy the user put in. On an element that was flicked, it reads as physics; on a
  menu that merely faded in, it reads as a mistake. Match the spring's bounce to what
  the gesture actually supplied.
