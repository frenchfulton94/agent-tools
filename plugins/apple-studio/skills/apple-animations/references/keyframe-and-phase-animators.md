> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/phaseanimator.md, https://developer.apple.com/documentation/swiftui/keyframeanimator.md, https://developer.apple.com/documentation/swiftui/keyframetrack.md, https://developer.apple.com/documentation/swiftui/timelineview.md, https://developer.apple.com/documentation/swiftui/controlling-the-timing-and-movements-of-your-animations.md, https://developer.apple.com/documentation/swiftui/view/phaseanimator(_:content:animation:).md, https://developer.apple.com/documentation/swiftui/view/phaseanimator(_:trigger:content:animation:).md, https://developer.apple.com/documentation/swiftui/view/keyframeanimator(initialvalue:repeating:content:keyframes:).md, https://developer.apple.com/documentation/swiftui/view/keyframeanimator(initialvalue:trigger:content:keyframes:).md, https://developer.apple.com/documentation/swiftui/keyframes.md, https://developer.apple.com/documentation/swiftui/keyframetimeline.md, https://developer.apple.com/documentation/swiftui/keyframetrackcontentbuilder.md, https://developer.apple.com/documentation/swiftui/keyframesbuilder.md, https://developer.apple.com/documentation/swiftui/keyframetrackcontent.md, https://developer.apple.com/documentation/swiftui/cubickeyframe.md, https://developer.apple.com/documentation/swiftui/linearkeyframe.md, https://developer.apple.com/documentation/swiftui/movekeyframe.md, https://developer.apple.com/documentation/swiftui/springkeyframe.md, https://developer.apple.com/documentation/swiftui/timelineschedule.md, https://developer.apple.com/documentation/swiftui/timelineviewdefaultcontext.md, https://developer.apple.com/documentation/swiftui/timelineview/context/cadence-swift.enum.md
> sources: live Apple docs (no book input; judgment layer: apple-design/animation-taste.md)

# Keyframe and Phase Animators

For the design judgment behind choosing discrete phases over continuous keyframe tracks — and why relative phase timing outlives absolute durations — see `apple-design/references/animation-taste.md § Discrete-Phase (Keyframe) Motion`. This file covers mechanics only: how to actually write a `PhaseAnimator`, a `KeyframeAnimator`/`KeyframeTrack`, and a `TimelineView`, plus the purely technical reasons to reach for one over another.

## PhaseAnimator: Discrete Phase Sequences

`PhaseAnimator<Phase, Content>` is a container (and matching `View` modifiers) that cycles a view through a sequence of discrete, `Equatable` phase values, applying a per-phase `Animation` on each transition (Apple docs: PhaseAnimator). There are two modifier overloads with different drivers (Apple docs: `phaseAnimator(_:content:animation:)`, `phaseAnimator(_:trigger:content:animation:)`):

- **`phaseAnimator(_:content:animation:)`** — continuously cycling. Once the view appears, it renders the first phase, then immediately moves to the second, animates the transition, and repeats through the sequence, looping back to the first phase after the last — with no external trigger involved.
- **`phaseAnimator(_:trigger:content:animation:)`** — trigger-driven. It renders the first phase and *holds there* until the `trigger` value (any `Equatable`) changes; only then does it advance to the next phase and animate. It keeps advancing one phase per trigger change, looping back to the first phase after the last.

Both overloads share the same `content` and `animation` closure shapes (Apple docs: `phaseAnimator(_:content:animation:)`):

- `content: (PlaceholderContentView<Self>, Phase) -> some View` — the first parameter is a proxy for the modified view, not the phase's raw data; you apply modifiers directly to that proxy based on the current phase, you don't rebuild a view from scratch.
- `animation: (Phase) -> Animation?` — called with the phase being transitioned *to*; return the `Animation` to use for that transition, or `nil` for no animation. Omit the parameter entirely and SwiftUI uses `.default` for every transition.

`phases` must be a non-empty `Sequence` of `Equatable` values — an empty sequence produces a runtime warning and a visible warning view instead of your content (Apple docs: `phaseAnimator(_:content:animation:)`).

### Minimal compiling example

```swift
import SwiftUI

enum PulsePhase: CaseIterable, Equatable {
    case initial
    case grown
    case settled
}

struct PulseView: View {
    var body: some View {
        Circle()
            .fill(.blue)
            .frame(width: 50, height: 50)
            .phaseAnimator(PulsePhase.allCases) { content, phase in
                content
                    .scaleEffect(phase == .grown ? 1.4 : 1.0)
                    .opacity(phase == .settled ? 0.85 : 1.0)
            } animation: { phase in
                switch phase {
                case .initial:
                    return .default
                case .grown:
                    return .easeOut(duration: 0.25)
                case .settled:
                    return .bouncy
                }
            }
    }
}
```

This uses the continuously-cycling overload — the circle pulses on a loop from the moment `PulseView` appears, with no external state driving it. Swap `phaseAnimator(PulsePhase.allCases) { … }` for `phaseAnimator(PulsePhase.allCases, trigger: someEquatableValue) { … }` to make it trigger-driven instead — same closures, the only change is adding `trigger:` and removing the free-running cycle.

## KeyframeAnimator + KeyframeTrack: Per-Property Timelines

`KeyframeAnimator<Value, KeyframePath, Content>` animates one composite `Value` (typically a small `Animatable` struct bundling several numeric properties) along an explicit timeline, re-invoking `content` every frame with the currently-interpolated value (Apple docs: KeyframeAnimator). Two modifier overloads mirror `PhaseAnimator`'s split (Apple docs: `keyframeAnimator(initialValue:repeating:content:keyframes:)`, `keyframeAnimator(initialValue:trigger:content:keyframes:)`):

- **`keyframeAnimator(initialValue:repeating:content:keyframes:)`** — loops the keyframe timeline continuously (`repeating` defaults to `true`); when `repeating` is `false`, `content` receives the timeline's starting value instead of an interpolated one.
- **`keyframeAnimator(initialValue:trigger:content:keyframes:)`** — plays the timeline once per change of `trigger`. If `trigger` changes again mid-animation, the `keyframes` closure is re-invoked with the *current* interpolated value (not the original `initialValue`), and velocity from the interrupted animation carries forward — cubic and spring keyframes stay continuous across the interruption unless you supply an explicit start velocity.

`content: (PlaceholderContentView<Self>, Value) -> some View` follows the same proxy pattern as `PhaseAnimator`. Because `content` re-runs every frame while animating, keep it cheap — no expensive work inside it (Apple docs: `keyframeAnimator(initialValue:repeating:content:keyframes:)`).

`keyframes: (Value) -> some Keyframes` is where the timeline is built, almost always by composing one or more `KeyframeTrack`s. `KeyframeTrack<Root, Value, Content>` is a sequence of keyframes driving a single property of `Root` on its own independent timeline — this is the mechanism that lets, say, `scale` finish settling while `rotation` is still mid-flight, all within one overall keyframe animation (Apple docs: KeyframeTrack). Two initializers:

- `KeyframeTrack(content:)` — animates the *entire* `Value`, not a sub-property.
- `KeyframeTrack(_ keyPath: WritableKeyPath<Root, Value>, content:)` — animates one property of `Root` via key path; this is the common case when your `Value` struct has several animatable fields, one `KeyframeTrack` per field.

`KeyframeTrack` itself conforms to the `Keyframes` protocol, which is the composition point `keyframeAnimator`'s `keyframes:` closure actually returns — you'd implement `Keyframes` directly only for custom interpolation logic beyond the four built-in keyframe types; in ordinary use you just return one or more `KeyframeTrack`s (Apple docs: Keyframes).

### Keyframe types — what each interpolation style means mechanically

- **`LinearKeyframe(_:duration:timingCurve:)`** — straight-line interpolation to the target value at a constant rate over `duration`; no easing (Apple docs: LinearKeyframe).
- **`CubicKeyframe(_:duration:startVelocity:endVelocity:)`** — cubic-curve interpolation. Leave velocities unspecified and SwiftUI computes them automatically so consecutive cubic keyframes form a Catmull-Rom spline (a smooth curve threading through every keyframe with continuous derivatives). A cubic keyframe adjacent to a differently-typed keyframe inherits/hands off velocity at that boundary, so motion stays continuous across a mixed-type track (Apple docs: CubicKeyframe).
- **`SpringKeyframe(_:duration:spring:startVelocity:)`** — interpolates via spring physics (a `Spring` value carrying stiffness/damping-equivalent parameters), so it can overshoot the target and settle rather than arrive monotonically — the one keyframe type that can produce genuine bounce within a track (Apple docs: SpringKeyframe).
- **`MoveKeyframe(_:)`** — no interpolation at all: an instantaneous jump to the value. Useful for snapping one property discretely while others on different tracks continue animating smoothly around it (Apple docs: MoveKeyframe).

## TimelineView: Time-Driven Redraw

`TimelineView<Schedule, Content>` is a container with no appearance of its own that re-invokes its `content` closure at dates produced by a `TimelineSchedule`, independent of any animation transaction — this is schedule-driven redraw, not a triggered or looping animation sequence (Apple docs: TimelineView). Each invocation hands `content` a `TimelineView.Context` (aliased as `TimelineViewDefaultContext` for the common case) carrying:

- `date` — the date from the schedule that triggered this redraw.
- `cadence` — a `TimelineView.Context.Cadence` value indicating how frequently the schedule is updating, so `content` can drop unnecessary detail at coarser cadences (e.g. hide a clock's second hand when cadence is coarser than `.seconds`) (Apple docs: TimelineViewDefaultContext). Confirmed three cases, coarse to fine: `.minutes`, `.seconds`, `.live` (Apple docs: `TimelineView.Context.Cadence`) — a view in a battery- or attention-constrained context (e.g. watchOS with the wrist lowered) may be handed a coarser cadence than its schedule's nominal update rate.

`TimelineSchedule` is the protocol behind the schedule argument; conforming types implement `entries(from:mode:)` to produce the sequence of dates (Apple docs: TimelineSchedule). Built-in schedules, each with a distinct mechanical cost/benefit:

- **`.periodic(from:by:)`** — fires at a fixed interval from a given start date; the straightforward "every N seconds" schedule.
- **`.animation`** / **`.animation(minimumInterval:paused:)`** — updates as fast as the display's own animation loop allows (no slower than `minimumInterval`), and can be paused/resumed — the right choice when you want the view to redraw in lockstep with ongoing animation work rather than a fixed clock interval.
- **`.everyMinute`** — fires once at the start of each minute; the cheapest option for anything that only needs minute-granularity (a clock face without a second hand).
- **`.explicit(_:)`** — fires only at the specific dates you supply, finite or irregular; use it when updates don't follow any regular period at all.

Mechanically, `TimelineView` gives you no interpolation between the dates it fires — Apple's own description is that it "redraws the content it contains at scheduled points in time" (Apple docs: TimelineView), i.e. each call to `content` is a fresh render for that date, not an eased transition from the previous one. If you need the value to visibly animate between updates rather than jump, wrap the relevant view state in `withAnimation`, an implicit `.animation(_:value:)`, or layer a `PhaseAnimator`/`KeyframeAnimator` on top — `TimelineView` itself only guarantees *when* the closure re-runs, not how the result transitions.

## Decision Block: Phases vs. Keyframes vs. Timeline

**Reach for `PhaseAnimator`** when the motion reduces to a short list of qualitatively distinct, `Equatable` configurations, each needing at most one `Animation` for its transition, and you don't need frame-level numeric control over how properties get there — you're saying "jump to this configuration, with this curve," not "trace this exact curve." It's also the simpler tool whenever a single view proxy with a handful of modifiers fully describes each state; you don't need a bespoke `Animatable` value type to use it.

**Reach for `KeyframeAnimator` + `KeyframeTrack`** when properties need independent timing within one overall animation — one property settling in 0.3s while another is still animating at 0.8s — or when you need explicit control over the interpolation curve itself (a Catmull-Rom cubic spline, specified start/end velocities, a spring with custom parameters mid-track) that a single `Animation` value applied to a single state change can't express. It's the right tool when what looked like "phases" are really points along a continuously-interpolated numeric track, not discrete states, and when you're willing to define a small `Animatable` struct to carry the properties being tracked.

**Reach for `TimelineView`** when redraw needs to be driven by wall-clock or schedule time on its own, independent of any triggered animation or transaction at all — a live clock face, a continuously-updating relative timestamp, a periodic counter. It is not a substitute for a triggered one-shot sequence: it has no concept of "trigger" or "phase," only "what date is it now, and how often should I re-render." If your motion is a response to a discrete event (a tap, a state flip), `PhaseAnimator` or `KeyframeAnimator` is mechanically the correct tool; if your view needs to keep redrawing purely because time is passing, `TimelineView` is the only one of the three built for that.
