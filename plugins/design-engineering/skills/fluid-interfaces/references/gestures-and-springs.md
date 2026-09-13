# Gestures and springs

The implementation layer for fluid interaction on the Svelte stack: one
worked drag attachment carrying every principle from SKILL.md, then the gesture
design details and the rules for combining motion with sound and haptics.

## Contents

- [A complete drag attachment](#a-complete-drag-attachment)
- [Why each piece is there](#why-each-piece-is-there)
- [Snap points and momentum projection](#snap-points-and-momentum-projection)
- [Tuning a Svelte spring](#tuning-a-svelte-spring)
- [Gesture design checklist](#gesture-design-checklist)
- [Multimodal feedback: motion, sound, haptics](#multimodal-feedback-motion-sound-haptics)
- [Reduced motion for gestures](#reduced-motion-for-gestures)

## A complete drag attachment

```svelte
<script>
	import { Spring, prefersReducedMotion } from 'svelte/motion';

	let { onDismiss } = $props();

	const y = new Spring(0, { stiffness: 0.2, damping: 0.6 });

	let dragging = $state(false);
	let pointerId = null;
	let grabOffset = 0;
	let history = []; /* recent {t, y} samples, for velocity at release */

	const DISMISS_VELOCITY = 0.11; /* px per ms — a flick alone is enough */
	const DISMISS_DISTANCE = 80;
	const HYSTERESIS = 10; /* px before we commit to a drag */

	/** Progressive resistance past a natural boundary. */
	function rubberband(overshoot, dimension, constant = 0.55) {
		return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
	}

	/** Project where a flick would come to rest, the way scroll deceleration does. */
	function project(velocityPxPerSecond, decelerationRate = 0.998) {
		return ((velocityPxPerSecond / 1000) * decelerationRate) / (1 - decelerationRate);
	}

	function drag(node) {
		function down(event) {
			if (pointerId !== null) return; /* ignore a second finger mid-drag */
			pointerId = event.pointerId;
			grabOffset = event.clientY - y.current; /* respect where they grabbed */
			history = [{ t: event.timeStamp, y: y.current }];
			node.setPointerCapture(event.pointerId);
		}

		function move(event) {
			if (event.pointerId !== pointerId) return;

			const raw = event.clientY - grabOffset;
			if (!dragging && Math.abs(raw) < HYSTERESIS) return;
			dragging = true;

			/* Above the resting position there is nothing to reveal — resist, do not refuse */
			const next = raw < 0 ? rubberband(raw, node.offsetHeight) : raw;

			y.set(next, { instant: true }); /* 1:1 with the finger, no smoothing */

			history.push({ t: event.timeStamp, y: next });
			if (history.length > 5) history.shift();
		}

		function up(event) {
			if (event.pointerId !== pointerId) return;
			pointerId = null;
			if (!dragging) return;
			dragging = false;

			const first = history[0];
			const last = history.at(-1);
			const elapsed = Math.max(last.t - first.t, 1);
			const velocityPxPerMs = (last.y - first.y) / elapsed;

			const projected = last.y + project(velocityPxPerMs * 1000);
			const flicked = velocityPxPerMs > DISMISS_VELOCITY;

			if (flicked || projected > DISMISS_DISTANCE) {
				y.set(node.offsetHeight, { preserveMomentum: 150 }).then(onDismiss);
			} else {
				y.set(0, { preserveMomentum: 150 });
			}
		}

		node.addEventListener('pointerdown', down);
		node.addEventListener('pointermove', move);
		node.addEventListener('pointerup', up);
		node.addEventListener('pointercancel', up);

		return () => {
			node.removeEventListener('pointerdown', down);
			node.removeEventListener('pointermove', move);
			node.removeEventListener('pointerup', up);
			node.removeEventListener('pointercancel', up);
		};
	}
</script>

<div {@attach drag} style:transform="translateY({y.current}px)" style:touch-action="none">
	<slot />
</div>
```

`touch-action: none` is required, not optional — without it the browser claims
the vertical gesture for scrolling and `pointermove` stops arriving.

## Why each piece is there

| Piece | Without it |
| --- | --- |
| `setPointerCapture` | The drag stops the moment the finger leaves the element's bounds |
| `pointerId` guard | A second finger takes over mid-drag and the element jumps |
| `grabOffset` | The element snaps its top to the finger on grab, breaking the illusion |
| `HYSTERESIS` | A tap with 2px of travel reads as a drag |
| `rubberband` | Dragging past the boundary hits an invisible wall |
| `{ instant: true }` while tracking | The spring adds lag between finger and element |
| Velocity from a short history | A single `pointermove` delta is noisy and often near zero |
| `preserveMomentum` at release | The animation restarts from rest, and the seam is visible |
| `pointercancel` handling | A system gesture leaves the element stuck mid-drag |
| `touch-action: none` | The browser scrolls instead, and the gesture never fires |

## Snap points and momentum projection

Against multiple snap points — a sheet with detents, a carousel — project first,
then pick the nearest snap to the projection, not to the release point:

```js
const projected = position + project(releaseVelocityPxPerSecond);
const target = snapPoints.reduce((best, p) =>
	Math.abs(p - projected) < Math.abs(best - projected) ? p : best
);
spring.set(target, { preserveMomentum: 150 });
```

`decelerationRate` of `0.998` gives a normal scroll feel; `0.99` is snappier.
Use the velocity **sign**, not the position, to decide reverse-or-commit: a user
who drags a sheet three-quarters closed and then flicks it back up has told you
what they want, whatever the position says.

## Tuning a Svelte spring

`stiffness` and `damping` are both clamped to 0–1 and default to `0.15` and
`0.8`. They are per-frame coefficients, so they translate to neither Apple's
damping-ratio-and-response pair nor Motion's `stiffness: 100, damping: 10`. A
config pasted from a React example silently clamps to `1` and feels wrong.

| Intent | Config |
| --- | --- |
| Default, graceful settle | `{ stiffness: 0.15, damping: 0.8 }` |
| Critically damped, snappy | `{ stiffness: 0.3, damping: 0.9 }` |
| Momentum with a little bounce | `{ stiffness: 0.2, damping: 0.55 }` |
| Sheet or drawer | `{ stiffness: 0.25, damping: 0.6 }` |
| Slow and heavy | `{ stiffness: 0.05, damping: 0.9 }` |

Raise `damping` toward `1` to remove overshoot; lower it for bounce. Raise
`stiffness` to shorten the settle. `precision` (default `0.01`) decides when the
spring stops; raise it for a large pixel value so it does not micro-settle for
frames after it looks finished.

Tune these on the real interaction. A spring's numbers do not read the way a
duration does, and the only reliable check is a finger on a real device.

## Gesture design checklist

- **Tap:** highlight on pointer-*down*, commit on pointer-*up*. Around 10px of
  hysteresis and hit padding, and allow cancel by dragging away and back.
- **Drag and swipe:** require a small movement threshold before committing to a
  direction, then track 1:1.
- **Detect all plausible gestures in parallel** from the first move, then cancel
  the losers once intent is clear. Avoid recognisers that report only a final
  state — a `swipeleft`-style event throws away the continuous tracking you need
  for feedback.
- **Minimise disambiguation delays.** Double-tap detection unavoidably delays
  single taps; only pay that cost where double-tap genuinely exists.
- **Test on hardware.** Connect a phone, reach the dev server by IP, and use
  Safari remote devtools. A simulator will not tell you whether a gesture feels
  right.

## Multimodal feedback: motion, sound, haptics

Three rules, from *Designing Audio-Haptic Experiences*:

1. **Causality** — it has to be obvious what caused the feedback. Trigger it on
   the actual causal event (the toggle flipping, the item snapping home) and
   match its character to the action's physicality.
2. **Harmony** — the visual, the sound, and the haptic fire on the same frame.
   Latency between them destroys the illusion. Do not let a CSS transition lag
   a `navigator.vibrate` call.
3. **Utility** — add feedback only where it earns its place. Reserve haptics and
   sound for meaningful moments — success, error, commit, snap. Over-feedback
   trains people to ignore all of it.

The Vibration API is unavailable on iOS Safari, so treat haptics as
progressive enhancement and never let a feature depend on them.

## Reduced motion for gestures

A gesture is direct manipulation, so the 1:1 tracking is not the part to remove
— the user is driving it. What to change is the *animated* half:

```js
spring.set(target, {
	instant: prefersReducedMotion.current,
	preserveMomentum: prefersReducedMotion.current ? 0 : 150
});
```

Drop the projection overshoot and the bounce; keep the tracking, the resistance
at boundaries, and the opacity feedback. Reduced motion means gentler, not an
interface that no longer responds to a finger.
