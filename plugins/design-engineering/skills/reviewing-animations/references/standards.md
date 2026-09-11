# Animation standards reference

The precise values behind the review. Cite these in findings instead of
approximating. Distilled from Emil Kowalski's design engineering philosophy,
with the Svelte defaults verified against the `svelte` package source.

## Contents

- [Should it animate? (frequency)](#should-it-animate-frequency)
- [Easing](#easing)
- [Duration](#duration)
- [Svelte defaults that fail the bar](#svelte-defaults-that-fail-the-bar)
- [Physicality](#physicality)
- [Springs](#springs)
- [Interruptibility](#interruptibility)
- [Asymmetric timing](#asymmetric-timing)
- [Performance](#performance)
- [Transforms and clip-path](#transforms-and-clip-path)
- [Gestures and drag](#gestures-and-drag)
- [Stagger](#stagger)
- [Accessibility](#accessibility)
- [Cohesion](#cohesion)
- [Debugging when feel is uncertain](#debugging-when-feel-is-uncertain)

## Should it animate? (frequency)

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation, ever |
| Tens of times/day (hover effects, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, feedback, celebrations) | Can add delight |

Never animate a keyboard-initiated action — it repeats hundreds of times daily,
and animation makes it feel slow and disconnected. Raycast has no open/close
animation, which is correct.

Valid purposes: spatial consistency, state indication, explanation, feedback,
preventing a jarring change. "It looks cool" on a frequently-seen element is not
one.

A SvelteKit page transition counts against this table. Navigation is the core
loop of most apps, so a view transition on every route change is a
high-frequency animation and needs to justify itself as one.

## Easing

Decision order:

- Entering or exiting → **`ease-out`** (starts fast, feels responsive)
- Moving or morphing on screen → **`ease-in-out`**
- Hover, colour change → **`ease`**
- Constant motion (marquee, progress) → **`linear`**
- Default → **`ease-out`**

Never `ease-in` on UI. It starts slow, delaying the exact moment the user is
watching; `ease-out` at 200ms feels faster than `ease-in` at 200ms.

Built-in CSS easings are too weak:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* iOS-like drawer (Ionic) */
```

The `svelte/easing` counterparts, measured as root-mean-square deviation:
`quintOut` for `--ease-out` (rms 0.007, very close), `quartInOut` for
`--ease-in-out` (rms 0.032, loose). `--ease-drawer` has no close built-in — a
drawer that uses `cubicOut` because it was nearest to hand is a finding, and the
fix is a sampled `cubic-bezier` easing function.

Find further curves at [easing.dev](https://easing.dev/) or
[easings.co](https://easings.co/) rather than hand-rolling one.

## Duration

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing, explanatory | Can be longer |

UI animations stay under 300ms. A 180ms dropdown feels more responsive than a
400ms one. A faster spinner makes a load feel faster at identical elapsed time.
Instant tooltips after the first make a whole toolbar feel faster.

## Svelte defaults that fail the bar

Every built-in transition defaults to 400ms, over the UI budget. Three go
further:

| Default | Why it is a finding | Fix |
| --- | --- | --- |
| `scale` uses `start: 0` | A `scale(0)` entrance — the element comes from nowhere | `{ start: 0.95 }` |
| `fade` uses `easing: linear` | Linear is for constant motion, not entrances | `{ easing: quintOut }` |
| `slide` animates height, width, padding, margin, and border-width | Layout and paint on every frame | Acceptable in an accordion; use `fly` elsewhere |
| `Tween` uses `easing: linear` | Same as `fade` | Pass an easing |
| `animate:flip` duration is `√distance × 120` ms | Exceeds 300ms past roughly 6px of travel | Pass `duration` |
| `crossfade` with no `fallback` | An item with no counterpart vanishes abruptly | Supply a `fallback` |

`fly` with no `x` or `y` is a fade wearing a different name — either pass a
distance or use `fade`.

## Physicality

- **Never `scale(0)`.** Start from `scale(0.9–0.97)` plus `opacity: 0`. Nothing
  in the real world appears from nothing.
- **Origin-aware popovers.** Scale from the trigger:
  `transform-origin: var(--bits-popover-content-transform-origin)`, with the
  component's own prefix. Modals are exempt — they are not anchored to a
  trigger, so `transform-origin: center` is correct there and must not be
  reported.
- **Button press feedback.** `transform: scale(0.97)` on `:active`, with
  `transition: transform 160ms var(--ease-out)`. Subtle, 0.95–0.98. Applies to
  any pressable element.

## Springs

Springs feel natural because they simulate physics; they have no fixed duration
and settle on their parameters. Use them for drag with momentum, elements that
should feel alive, interruptible gestures, and decorative mouse-tracking.

Svelte's `Spring` takes `stiffness` and `damping` clamped to 0–1, defaulting to
`0.15` and `0.8`. These are **not** Motion's `stiffness: 100, damping: 10` and
not Apple's damping-ratio-and-response pair — a config copied from a React
example into `new Spring()` is a finding, because the values silently clamp.

| Intent | Config |
| --- | --- |
| Default, graceful settle | `{ stiffness: 0.15, damping: 0.8 }` |
| Snappy, no overshoot | `{ stiffness: 0.3, damping: 0.9 }` |
| Momentum with a little bounce | `{ stiffness: 0.2, damping: 0.55 }` |
| Slow and heavy | `{ stiffness: 0.05, damping: 0.9 }` |

Keep bounce out of most UI; reserve it for drag-to-dismiss and playful moments.
Springs carry velocity through an interruption where keyframes restart from
zero, which is why they suit gestures a user may reverse mid-motion.

For decorative mouse-tracking, interpolate the pointer position through a spring
rather than binding a transform to it directly — direct binding has no momentum
and reads as artificial. Only do this where the motion is decorative.

## Interruptibility

CSS **transitions** retarget mid-animation; **keyframes** restart from zero. In
Svelte the same split is `transition:` against `in:`/`out:` — `transition:` is
bidirectional and reverses smoothly, while an aborted `out:` restarts.

```svelte
<!-- Interruptible: reverses from wherever it is -->
<div transition:fly={{ y: '100%', duration: 250, easing: quintOut }}>

<!-- Not interruptible: plays past itself, restarts when aborted -->
<div in:fly={{ y: '100%' }} out:fade>
```

`@starting-style` gives entry without JavaScript for an element that is always
mounted. Bits UI keeps content in the DOM until its CSS transition finishes, so
`[data-state="open"]` / `[data-state="closed"]` styling needs no mount flag.

## Asymmetric timing

Slow where the user is deciding, fast where the system responds.

```css
.overlay { transition: clip-path 200ms var(--ease-out); }            /* release */
.button:active .overlay { transition: clip-path 2s linear; }          /* press */
```

## Performance

- **Only `transform` and `opacity`** skip layout and paint and run on the GPU.
  Padding, margin, height, width, top, and left trigger all three.
- **A custom transition should return `css`, not `tick`.** Svelte compiles `css`
  into a web animation that runs off the main thread; `tick` runs on the main
  thread every frame and drops frames while the page loads, scripts, or paints.
  This is Svelte's form of "CSS beats JavaScript under load", and the Svelte
  docs state it directly.
- **Do not drive a child transform from a CSS variable on a parent.** In Svelte
  that includes a component custom property: `<Card --offset="{x}px" />`
  desugars to a `<svelte-css-wrapper>` carrying the variable, so every frame
  recalculates styles for the whole subtree.

  ```svelte
  <Card --offset="{x}px" />                        <!-- recalc on all children -->
  <div style:transform="translateY({x}px)"></div>  <!-- one element -->
  ```

- **`@keyframes` in a component `<style>` is scoped by name hashing**, along
  with the `animation` rules referencing it. A shared keyframe belongs in a
  global stylesheet, not copied into five components.
- Keep transition-time `filter: blur()` under 20px — heavy blur is expensive,
  especially in Safari.

## Transforms and clip-path

- **`translate` percentages** are relative to the element's own size, so
  `translateY(100%)` moves it by its own height whatever the content. Svelte's
  `fly` accepts string values (`y: '100%'`) for exactly this. Prefer them over
  hardcoded pixels.
- **`scale()` scales children too** — font, icons, content. That is a feature
  for press feedback.
- **3D**: `rotateX`/`rotateY` with `transform-style: preserve-3d` gives depth,
  flips, and orbits without JavaScript.
- **`clip-path: inset(t r b l)`** is a strong animation tool; each value eats in
  from that side. Reveal on scroll, hold-to-delete overlays, seamless tab colour
  transitions (duplicate the list and clip the active copy), comparison sliders.

## Gestures and drag

- **Momentum dismissal**: do not require crossing a distance threshold. Compute
  `Math.abs(distance) / elapsedMs` and dismiss above roughly `0.11`. A flick
  should be enough.
- **Track 1:1 while the finger is down.** `spring.set(v, { instant: true })`
  during the drag, and let the spring take over at release. A spring smoothing
  the drag itself adds lag exactly where directness matters.
- **Velocity handoff at release**: `spring.set(target, { preserveMomentum: 150 })`
  continues the current trajectory instead of restarting from zero.
- **Pointer capture** once dragging starts, via `setPointerCapture`, so it
  continues when the pointer leaves the element's bounds.
- **Multi-touch protection**: ignore new pointers once a drag has begun, or
  switching fingers makes the element jump.
- **Friction, not a wall** — allow over-drag with rising resistance.

## Stagger

30–80ms between items; longer feels slow. Stagger is decorative and must never
block interaction. On a long list, cap the delay
(`Math.min(i, 6) * 50`) or the last row arrives seconds late.

```svelte
{#each items as item, i (item.id)}
	<li in:fly={{ y: 8, duration: 300, delay: Math.min(i, 6) * 50, easing: quintOut }}>
{/each}
```

## Accessibility

Svelte transitions run through the Web Animations API. A global
`@media (prefers-reduced-motion: reduce)` rule that zeroes `transition-duration`
and `animation-duration` has **no effect on them** — this is documented Svelte
behaviour and the most commonly missed accessibility detail in a Svelte
codebase. A diff whose only reduced-motion handling is that CSS rule, while the
motion in question comes from a `transition:` directive, is a block.

```svelte
<script>
	import { prefersReducedMotion } from 'svelte/motion';
</script>

{#if open}
	<div transition:fly={{ y: prefersReducedMotion.current ? 0 : 16, duration: 200 }}>
{/if}
```

For a `Spring`, `spring.set(target, { instant: prefersReducedMotion.current })`.
CSS-driven motion still needs the media query; most codebases need both guards.

Reduced motion means fewer and gentler animations, not zero — keep opacity and
colour transitions that aid comprehension, remove movement.

```css
@media (hover: hover) and (pointer: fine) {
	.element:hover { transform: scale(1.05); }
}
```

Gate hover motion — touch fires a false hover on tap.

## Cohesion

Match motion to the component's personality: playful can be bouncier, a
professional dashboard should be crisp and fast. Sonner feels right partly
because its easing, duration, design, and even its name are in harmony — it runs
slightly slower than typical UI and uses `ease` rather than `ease-out` to feel
elegant. Opacity against height in entering and exiting lists is trial and
error; there is no formula, only adjusting until it feels right.

Curves and durations belong in shared tokens. Five hand-typed cubic-beziers that
almost match is a consolidation finding.

## Debugging when feel is uncertain

- **Slow motion**: multiply the duration by 2–5×, or use the DevTools animation
  inspector. Check that colours crossfade cleanly, easing does not stop
  abruptly, `transform-origin` is right, and coordinated properties stay in
  sync.
- **Frame by frame**: the Chrome DevTools Animations panel reveals timing drift
  between coordinated properties.
- **Real devices** for gestures — connect a phone, hit the dev server by IP, use
  Safari remote devtools.
- **Fresh eyes the next day** — imperfections invisible during development
  surface later.
