# Term to Svelte API

The glossary names an effect; this maps the name onto the thing you actually
write on this stack. Use it when a naming question turns into a build question —
then hand off to `animating-interfaces`, which owns the decisions about whether
and how.

## Contents

- [Entrances and exits](#entrances-and-exits)
- [Sequencing and layout](#sequencing-and-layout)
- [Transitions between states](#transitions-between-states)
- [Scroll and navigation](#scroll-and-navigation)
- [Feedback and gestures](#feedback-and-gestures)
- [Easing and springs](#easing-and-springs)
- [Polish and effects](#polish-and-effects)
- [Terms with no Svelte-specific answer](#terms-with-no-svelte-specific-answer)

## Entrances and exits

| Term | Svelte / CSS |
| --- | --- |
| Fade in / out | `transition:fade` — override the default `linear` easing with `quintOut` |
| Slide in | `transition:fly={{ y: 16 }}` (percentage strings translate by the element's own size) |
| Scale in | `transition:scale={{ start: 0.95 }}` — the default `start` is `0`, which is the one entrance value never to ship |
| Pop in | `transition:scale` with `easing: backOut`, or a `Spring` with `damping` near `0.55` |
| Reveal | `clip-path: inset(…)` under a CSS transition, or a custom transition returning `css` |
| Enter / Exit | `transition:` for reversible motion; `in:`/`out:` only when the paths differ |

## Sequencing and layout

| Term | Svelte / CSS |
| --- | --- |
| Stagger | `delay: i * 50` inside a keyed `{#each}`, capped so a long list does not trail |
| Interpolation / Tween | `Tween` from `svelte/motion` — defaults to `linear`, so always pass an easing |
| Keyframes | `@keyframes` in a component `<style>`; the name is scoped by hashing, so it is unreachable from other components |
| Layout animation | `animate:flip` on the immediate children of a **keyed** `{#each}` — reorder only, not add or remove |
| Drag to reorder | `animate:flip` for the shifting siblings, plus a pointer-capture attachment for the dragged item |
| Accordion / Collapse | `height` transition against `var(--bits-accordion-content-height)`, or `transition:slide` |
| Orchestration | Transition events — `onintroend`, `onoutroend` — to chain one phase off another |

## Transitions between states

| Term | Svelte / CSS |
| --- | --- |
| Crossfade (same spot) | Two absolutely-positioned elements under `{#key}`, each with `transition:fade` |
| Shared element transition | `crossfade()` from `svelte/transition`, keyed — always supply the `fallback` |
| Continuity transition | `animate:flip`, or a View Transition with a `view-transition-name` on both states |
| Morph | No built-in; animate `clip-path` or `d` on an SVG path, or reach for Motion |
| Direction-aware transition | Branch the `x` passed to `fly` on navigation direction |

## Scroll and navigation

| Term | Svelte / CSS |
| --- | --- |
| Scroll reveal | `IntersectionObserver` in an `{@attach}`, toggling a class; fire once |
| Scroll-driven animation | CSS `animation-timeline: view()` / `scroll()` — no JavaScript, runs off the main thread |
| Page transition | `onNavigate` + `document.startViewTransition` in `+layout.svelte` |
| View transition | The same, styled via `::view-transition-old(root)` / `::view-transition-new(root)` |
| Parallax | `animation-timeline: scroll()` with differing `translateZ`, or a scroll attachment |

## Feedback and gestures

| Term | Svelte / CSS |
| --- | --- |
| Press / Tap feedback | `:active { transform: scale(0.97) }` — pure CSS, no Svelte machinery |
| Hover effect | CSS, gated behind `@media (hover: hover) and (pointer: fine)` |
| Hold to confirm | `clip-path` transition, slow on `:active`, snappy on release |
| Drag | `{@attach}` with Pointer Events and `setPointerCapture`, writing to a `Spring` |
| Swipe to dismiss | The same, dismissing on `Math.abs(distance) / elapsedMs > 0.11` |
| Rubber-banding | Divide the overshoot by a rising factor while tracking, before it reaches the spring |
| Momentum | `spring.set(target, { preserveMomentum: 150 })` at release |
| Shake / Wiggle | A CSS `@keyframes`, re-triggered by `{#key}` on the error value |

## Easing and springs

| Term | Svelte / CSS |
| --- | --- |
| Easing | `svelte/easing` for JS, `cubic-bezier()` tokens for CSS — keep the two in sync |
| Ease-out | `quintOut` ≈ `cubic-bezier(0.23, 1, 0.32, 1)` |
| Ease-in-out | `quartInOut` ≈ `cubic-bezier(0.77, 0, 0.175, 1)` |
| Cubic-bezier | Sample it into a JS easing function so both sides use one curve |
| Spring | `Spring` from `svelte/motion` — `stiffness` and `damping` clamped 0–1, not Motion's 100/10 scale |
| Stiffness | `stiffness`, default `0.15`; higher settles sooner |
| Damping | `damping`, default `0.8`; lower bounces more |
| Mass | Not exposed — approximate by lowering `stiffness` |
| Interruptible animation | `transition:` (bidirectional) or a `Spring`; never `in:`/`out:` or `@keyframes` |

## Polish and effects

| Term | Svelte / CSS |
| --- | --- |
| Blur | `transition:blur`, or `filter: blur(2px)` to mask a crossfade — keep it under 20px |
| Clip-path | A plain CSS transition on `clip-path: inset()` |
| Line drawing | `transition:draw` on a `<path>` or `<polyline>` |
| Number ticker | `Tween.of(() => value)` plus `font-variant-numeric: tabular-nums` |
| Text morph / Typewriter | A custom transition returning `tick` — one of the few cases where `tick` is unavoidable |
| Skeleton / Shimmer | A CSS `@keyframes` gradient sweep; it runs off the main thread while data loads |
| Tabular numbers | `font-variant-numeric: tabular-nums` |

## Terms with no Svelte-specific answer

These are plain CSS or plain browser behaviour, and Svelte adds nothing:
**Marquee**, **Loop**, **Alternate (yoyo)**, **Orbit**, **Pulse**, **Float**,
**Idle animation**, **Perspective**, **3D tilt**, **Skew**, **Mask**,
**Before / after slider**, **Ripple**, **will-change**, **Compositing**.

Two performance terms are worth naming precisely on this stack, because Svelte
has its own way to hit them:

- **Layout thrashing** — `transition:slide` animates height, padding, margin,
  and border-width, so it thrashes by construction. It is right for an accordion
  and wrong for a list.
- **Jank** — a custom transition that returns `tick` instead of `css` runs on the
  main thread every frame, which is the usual source in Svelte code.
