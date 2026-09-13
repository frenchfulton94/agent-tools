---
name: fluid-interfaces
description: 'Apple''s approach to fluid, physical interface motion and design, translated to the web and the Svelte stack — response and latency, 1:1 direct manipulation, interruptibility, spring behaviour over scripted animation, velocity handoff, momentum projection, rubber-banding, translucent materials and depth, typography, and the design principles behind them. Use when building or reviewing a gesture-driven interface, a drag, swipe, sheet, or carousel, spring physics and momentum, an interaction that has to be grabbable mid-flight, translucent chrome and backdrop blur, type scales and tracking, or motion that should feel native and physical rather than merely animated. For the animation decision sequence and the everyday recipes use animating-interfaces. For native SwiftUI motion use apple-animations.'
license: MIT
---

# Apple Design

How Apple builds interfaces that stop feeling like a computer and start feeling
like an extension of you. Distilled from Apple's WWDC design talks — chiefly
*Designing Fluid Interfaces* (2018) — and translated to the web platform and
Svelte's motion primitives.

The through-line: **an interface feels alive when motion starts from the current
on-screen value, inherits the user's velocity, projects momentum forward, and can
be grabbed and reversed at any instant.** Springs are the tool that makes this
natural, because they are inherently interruptible and velocity-aware.

> "When we align the interface to the way we think and move, something magical
> happens — it stops feeling like a computer and starts feeling like a seamless
> extension of us."

Apple frames design as serving four human needs: safety and predictability,
understanding, achievement, and joy. Every rule here serves one of them.

## 1. Response — kill latency

The moment lag appears, the feeling of directness falls off a cliff. Response is
the foundation everything else is built on.

- **Respond on pointer-down, not on release.** Highlight a button the instant it
  is pressed. Waiting for `click` to show feedback feels dead.
- **Audit every latency on the input path** — debounces, artificial timers,
  transition waits. Anything not essential is a regression.
- **Feedback is continuous during the interaction, not only at the end.** For a
  drag, slider, or sheet, update the UI 1:1 with the pointer the whole way
  through.

```css
.button:active {
	transform: scale(0.97);
	transition: transform 100ms var(--ease-out);
}
```

## 2. Direct manipulation — 1:1 tracking

> "Touch and content should move together."

When the user drags something it stays glued to the finger, and it respects the
offset from *where they grabbed it*. Snapping to the element's centre on grab
breaks the illusion immediately.

Use Pointer Events with `setPointerCapture` so tracking continues when the
pointer leaves the element's bounds, and keep a short position-and-timestamp
history so you have velocity at release.

**Track with `{ instant: true }`, not with the spring's own smoothing.** While
the finger is down the element is the finger; the spring's job starts at
release. A spring smoothing the drag itself adds lag exactly where directness
matters most.

```js
spring.set(pointerY - grabOffset, { instant: true }); // during the drag
```

## 3. Interruptibility — the most important principle

> "The thought and the gesture happen in parallel."

Every animation is interruptible and redirectable at any moment. A user has to
be able to grab a moving element mid-flight and reverse it without waiting. A
closing sheet the user grabs again should follow the finger, not finish closing
and then reopen.

- **Never lock out input during a transition.**
- **Animate from the presentation value, never the target value.** On interrupt,
  start from where the element actually is on screen. Starting from the logical
  value causes a visible jump. Svelte's `Spring` does this by construction —
  `spring.current` is the presentation value, and changing `spring.target`
  retargets from it.
- **Avoid CSS `@keyframes`, and avoid `in:`/`out:`, for anything gesture-driven.**
  Neither can be grabbed and reversed mid-flight. `transition:` is bidirectional
  and reversible; a `Spring` is both and carries velocity too.
- **When a gesture reverses, blend velocity rather than hard-cutting it.**
  Replacing one animation with another at a reversal creates a velocity
  discontinuity that reads as a brick wall.
- **Decompose 2D motion into independent X and Y springs.** One spring on a 2D
  distance desyncs when the axes have different velocities.

## 4. Behaviour over animation — use springs

> "Think of animation as a conversation between you and the object, not
> something prescribed by the interface."

A scripted, fixed-duration animation cannot respond to new input. A spring can:
new input changes the target and the motion stays continuous. Reach for springs
for anything a user can touch.

Apple replaced the physics triplet with two designer-friendly parameters:

- **Damping ratio** — controls overshoot. `1.0` is critically damped, no bounce.
  Below `1.0` overshoots and oscillates; lower is bouncier.
- **Response** — how quickly the value reaches the target, in seconds. Lower is
  snappier. Not a duration: a spring's settle time emerges from its parameters.

Defaults: start most UI at damping `1.0`. Add bounce (damping around `0.8`)
**only when the gesture itself carried momentum** — a flick, a throw, a drag
release. Overshoot on a menu that just faded in feels wrong; overshoot on a card
you flicked feels right.

| Interaction | Damping | Response | Svelte `Spring` |
| --- | --- | --- | --- |
| Move / reposition | `1.0` | `0.4` | `{ stiffness: 0.2, damping: 0.9 }` |
| Rotation | `0.8` | `0.4` | `{ stiffness: 0.2, damping: 0.6 }` |
| Drawer / sheet | `0.8` | `0.3` | `{ stiffness: 0.25, damping: 0.6 }` |

Svelte's `stiffness` and `damping` are per-frame coefficients clamped to 0–1,
not Apple's ratio-and-response pair and not Motion's `100`/`10` scale. The
column above is a starting point to tune from, not an equivalence — verify it on
the real interaction.

## 5. Velocity handoff — the seam between drag and animation

When a gesture ends, the animation continues at the finger's exact velocity, so
there is no visible seam between dragging and animating. This detail is what
most separates "fluid" from "fine".

Svelte exposes it directly:

```js
spring.set(target, { preserveMomentum: 150 });
```

The spring keeps its current trajectory for that many milliseconds before
pulling toward the new target. Tune the window against the gesture: shorter for
a precise snap, longer for a thrown object.

## 6. Momentum projection — animate to where the gesture is going

> "Take a small input and make a big output."

Do not snap to the nearest boundary from the *release point*. Use velocity to
project the resting position, the way scroll deceleration does, then snap to the
target nearest that projection. This is what makes a flick feel like a throw.

```js
/** Apple's projection from the Designing Fluid Interfaces sample code. */
function project(initialVelocity /* px/s */, decelerationRate = 0.998) {
	return ((initialVelocity / 1000) * decelerationRate) / (1 - decelerationRate);
}

const projected = position + project(releaseVelocity);
const target = nearestSnapPoint(projected);
spring.set(target, { preserveMomentum: 150 });
```

`0.998` gives a normal scroll feel; `0.99` is snappier. The textbook
`v² / (2·deceleration)` is *not* what Apple ships — use the exponential-decay
form above. It is the behaviour behind good bottom sheets and carousels.

## 7. Spatial consistency

> "If something disappears one way, we expect it to emerge from where it came."

- **Enter and exit along the same path.** A panel that slides in from the right
  dismisses to the right. In-from-right, out-the-bottom feels disconnected.
- **Anchor interactions to their source.** A menu, popover, or sheet originates
  from the element that triggered it — set `transform-origin` to the trigger.
- **Mirror the easing on reversible transitions** so the outbound path matches
  the return, using inverse control points for the two directions.

## 8. Hint in the direction of the gesture

People predict a final state from a trajectory. Intermediate motion should
telegraph where things are going — Control Center modules grow up and out toward
your finger. Make the in-between frames point at the outcome rather than
interpolating blindly to it.

## 9. Rubber-banding — soft boundaries

At an edge, resist progressively instead of stopping hard. A hard stop reads as
frozen; continuous resistance reads as responsive with nothing more to find.

```js
/** The further past the bound, the less the element follows. */
function rubberband(overshoot, dimension, constant = 0.55) {
	return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}
```

Apply it while tracking, before the value reaches the spring.

## 10. Frame-level smoothness

Smoothness is about what is *in* the frames, not only the frame rate. Keep the
per-frame positional change below the perception threshold to avoid strobing;
for very fast motion a subtle blur or stretch encodes speed better than a hard
streak. Animate compositor-friendly properties only — `transform` and `opacity`
— and hint with `will-change` where motion is imminent.

## Where to look

- `references/gestures-and-springs.md` — the full gesture implementation: a
  Svelte drag attachment with pointer capture, multi-touch protection,
  rubber-banding, velocity, projection, and handoff, plus the gesture-design
  checklist (tap hysteresis, parallel recognition, disambiguation delays) and
  multimodal feedback. Read when building or reviewing any drag, swipe, sheet,
  or carousel.
- `references/materials-and-type.md` — translucency and depth with
  `backdrop-filter`, material weight and hierarchy, scroll edge effects,
  typography (optical sizing, tracking, leading, Dynamic Type), the three
  accessibility preference signals beyond reduced motion, and Apple's eight
  design principles. Read when building chrome, sheets, or a type scale, or when
  a review touches visual hierarchy rather than motion.

## Quick reference

| Need | Technique | Value |
| --- | --- | --- |
| Default UI spring | Critically damped, no overshoot | Svelte `{ stiffness: 0.2, damping: 0.9 }` |
| Momentum spring | Under-damped, slight bounce | Svelte `{ stiffness: 0.2, damping: 0.6 }` |
| Track a drag | 1:1, no smoothing | `spring.set(v, { instant: true })` |
| Release handoff | Continue at the finger's velocity | `spring.set(target, { preserveMomentum: 150 })` |
| Flick landing point | Project momentum | `current + (v/1000)·d/(1−d)`, `d ≈ 0.998` |
| Interrupt cleanly | Start from the presentation value | `spring.current`, not the target |
| Reverse or commit | Use the velocity sign, not position | at release |
| 1:1 drag | Pointer Events plus capture | respect the grab offset |
| Feedback | On pointer-down, continuous | never only at the end |
| Boundary | Rubber-band, not a hard stop | progressive resistance |
| Translucent chrome | `backdrop-filter` layer | content scrolls under |
| Type tracking | Size-specific, never fixed | `-0.02em` on display, near `0` on body |
| Reduced motion | Cross-fade, not slide or spring | `prefersReducedMotion.current` |
