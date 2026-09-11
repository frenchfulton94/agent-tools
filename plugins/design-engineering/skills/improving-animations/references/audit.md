# Animation audit playbook

The eight audit categories, what to hunt for in each, and the exact values to
cite in findings and plans. Distilled from Emil Kowalski's design engineering
philosophy ([emilkowal.ski](https://emilkowal.ski/)), with Svelte defaults
verified against the `svelte` package source. Never approximate a value that
appears here — copy it.

## Contents

- [1. Purpose and frequency](#1-purpose-and-frequency)
- [2. Easing and duration](#2-easing-and-duration)
- [3. Physicality and origin](#3-physicality-and-origin)
- [4. Interruptibility](#4-interruptibility)
- [5. Performance](#5-performance)
- [6. Accessibility](#6-accessibility)
- [7. Cohesion and tokens](#7-cohesion-and-tokens)
- [8. Missed opportunities](#8-missed-opportunities)
- [Svelte defaults, in one table](#svelte-defaults-in-one-table)

## 1. Purpose and frequency

Every animation answers "why does this animate?" — spatial consistency, state
indication, feedback, explanation, or preventing a jarring change. "It looks
cool" on a frequently-seen element is not a purpose.

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation, ever |
| Tens of times/day (hover effects, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, feedback, celebrations) | Can add delight |

Hunt for: animation on keyboard-initiated actions; a command palette with an
open/close transition (Raycast has none, correctly); decorative motion on list
items or hover states hit constantly; a `startViewTransition` in the root layout
firing on every navigation. The strongest fix is usually **delete it**.

## 2. Easing and duration

Decision order: entering or exiting → **`ease-out`**; moving or morphing on
screen → **`ease-in-out`**; hover or colour → **`ease`**; constant motion →
**`linear`**; default → **`ease-out`**.

`ease-in` on UI is always a finding — it starts slow, delaying the exact moment
the user is watching. Built-in easings are too weak for deliberate motion; plans
introduce strong custom curves as tokens, matching repo conventions:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

On the JavaScript side, `quintOut` matches `--ease-out` closely (rms 0.007) and
`quartInOut` matches `--ease-in-out` loosely (rms 0.032). `--ease-drawer` has no
close built-in — a drawer easing on `cubicOut` is a finding, fixed with a
sampled `cubic-bezier` function so the CSS token and the JS easing are the same
curve.

Duration budgets — UI stays under 300ms:

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing, explanatory | Can be longer |

Hunt for: `ease-in` anywhere; bare `linear` on an entrance; any Svelte
transition or `Tween` with no explicit `duration` or `easing` (both default to
400ms, and `fade` and `Tween` default to `linear`); durations over 300ms on UI;
`animate:flip` with no duration; a tooltip delay plus animation on every tooltip
in a toolbar, where after the first they should be instant.

## 3. Physicality and origin

- **Never `scale(0)`** — nothing in the real world appears from nothing. Target
  `scale(0.9–0.97)` plus `opacity: 0`. `transition:scale` defaults to
  `start: 0`, so every un-parameterised use of it is this finding.
- **Popovers, dropdowns, and tooltips scale from their trigger**, not centre:
  `transform-origin: var(--bits-popover-content-transform-origin)`, with the
  component's own prefix. **Modals are exempt** — do not report
  `transform-origin: center` on one.
- **Press feedback**: `transform: scale(0.97)` on `:active` with
  `transition: transform 160ms var(--ease-out)`. Subtle, 0.95–0.98.

Hunt for: `transition:scale` with no `start`; pure-fade entrances with no
initial transform; trigger-anchored content with no `transform-origin`, or with
`center`; pressable elements with no `:active` feedback; `fly` with no `x` or
`y`, which is a fade wearing another name.

## 4. Interruptibility

CSS transitions retarget from the current state; keyframes restart from zero.
In Svelte the same split is `transition:` against `in:`/`out:` — `transition:`
is bidirectional and reverses smoothly mid-flight, while an aborted `out:`
restarts from scratch. Anything triggered rapidly or reversible mid-motion
(toasts stacking, toggles, drags, expand and collapse) needs the interruptible
form.

- Entry without JavaScript on an always-mounted element: `@starting-style`.
- Bits UI holds content in the DOM until its CSS transition finishes, so
  `[data-state="open"]` / `[data-state="closed"]` styling needs no mount flag.
- Gesture-driven motion uses a `Spring`, which carries velocity when interrupted.
  Svelte's `Spring` takes `stiffness` and `damping` clamped 0–1, defaults `0.15`
  and `0.8` — a config copied from a Motion example (`stiffness: 100`) silently
  clamps and is a finding.
- **Asymmetric timing**: deliberate phases (press, hold, destructive confirm)
  animate slower; the system's response snaps. Symmetric timing on
  press-and-release is a finding.

Hunt for: `in:`/`out:` on toasts, toggles, and rapidly-triggered UI; `@keyframes`
in the same places; a `Tween` driving something a finger controls; drags
dismissing on distance alone rather than `Math.abs(distance) / elapsedMs > 0.11`;
hard stops at drag boundaries instead of rising friction; `animate:flip` on an
unkeyed `{#each}`, where it silently never runs; `crossfade` with no `fallback`.

## 5. Performance

- **Animate `transform` and `opacity` only.** Width, height, margin, padding,
  top, and left trigger layout, paint, and composite.
- **`transition: all`** animates unintended properties off the GPU — always a
  finding.
- **`transition:slide` animates height, width, padding, margin, and
  border-width** — seven layout properties by construction. Acceptable in an
  accordion, where there is no transform equivalent. A finding anywhere else,
  and a compounding one on a list.
- **A custom transition returning only `tick`** runs on the main thread every
  frame. Svelte compiles a `css` function into a web animation that runs off the
  main thread; the docs say to prefer `css` wherever the effect can be expressed
  as CSS.
- **Do not drive a child transform from a CSS variable on a parent.** In Svelte
  that includes component custom properties: `<Card --offset="{x}px" />`
  desugars to a `<svelte-css-wrapper>` carrying the variable, so every frame
  recalculates styles for the whole subtree. `style:transform="translateY({x}px)"`
  writes one property on one element.
- **`@keyframes` in a component `<style>` is scoped by name hashing.** A shared
  keyframe copied into five components is a consolidation finding.
- Keep transition-time `filter: blur()` under 20px — heavy blur is expensive,
  especially in Safari.

Hunt for: `transition: all`; animated layout properties; `transition:slide`
outside accordions; custom transitions with `tick` and no `css`; component
custom properties updated per frame; `requestAnimationFrame` loops doing what
CSS could.

## 6. Accessibility

Svelte transitions are driven by the Web Animations API. A global
`@media (prefers-reduced-motion: reduce)` rule that zeroes `transition-duration`
and `animation-duration` **does not affect them**. A codebase whose only
reduced-motion handling is that CSS rule, while its motion comes from
`transition:` directives, has no reduced-motion handling at all — and it will
look as though it does, which is what makes this the highest-value accessibility
finding on this stack.

```svelte
<script>
	import { prefersReducedMotion } from 'svelte/motion';
</script>

{#if open}
	<div transition:fly={{ y: prefersReducedMotion.current ? 0 : 16, duration: 200 }}>
{/if}
```

For a `Spring`: `spring.set(target, { instant: prefersReducedMotion.current })`.
For a view transition: skip `startViewTransition` entirely.

```css
@media (hover: hover) and (pointer: fine) {
	.element:hover { transform: scale(1.05); }
}
```

Reduced motion means fewer and gentler animations, **not zero** — keep
transitions that aid comprehension, remove position changes.

Hunt for: movement with no reduced-motion handling; a CSS-only reduced-motion
rule alongside Svelte transitions; ungated `:hover` motion; reduced-motion
implementations that remove all feedback; `onNavigate` view transitions with no
preference check.

## 7. Cohesion and tokens

- Motion should match the product's personality — playful can be bouncier, a
  dashboard stays crisp. Mismatched personality across components is a finding.
- Curves and durations belong in shared tokens. Five hand-typed cubic-beziers
  that almost match is a consolidation finding, and so is the same
  `{ duration: 200, easing: quintOut }` object literal repeated across twenty
  components rather than exported once from `$lib`.
- Everything-at-once group entrances where a **30–80ms stagger** belongs.
  Stagger is decorative and must never block interaction; on a long list the
  delay needs a cap.
- A jarring crossfade that shows two overlapping states can be masked with
  `filter: blur(2px)` during the transition.

Hunt for: duplicated near-identical easings and durations; one bouncy component
in a crisp app; list and grid entrances with no stagger; uncapped stagger
delays; crossfades that visibly double-expose.

## 8. Missed opportunities

The additive category — places that do not animate but should.

- State changes that teleport (content swaps, `{#if}` blocks with no transition,
  layout jumps) where a brief transition would prevent a jarring change.
- Spatially-connected UI — a panel appearing from a trigger — with no motion
  explaining where it came from.
- Keyed `{#each}` lists that reorder with no `animate:flip`.
- Rare, high-emotion moments (first run, success, celebration) rendered with
  none of the delight budget they are allowed.
- `translateY(100%)` percentages and `clip-path: inset()` reveals as the tools
  for these, rather than hardcoded pixel offsets.

Report at most a handful, grounded in UX seams you actually observed rather than
a wishlist.

## Svelte defaults, in one table

Cite these directly; they are the source of a large share of findings.

| API | Duration | Easing | Other | Verdict |
| --- | --- | --- | --- | --- |
| `fade` | 400 | `linear` | — | Both wrong for an entrance |
| `fly` | 400 | `cubicOut` | `x: 0`, `y: 0` | Over budget; no distance means it is a fade |
| `scale` | 400 | `cubicOut` | `start: 0` | Over budget; `scale(0)` entrance |
| `slide` | 400 | `cubicOut` | `axis: 'y'` | Over budget; animates seven layout properties |
| `blur` | 400 | `cubicInOut` | `amount: 5` | Over budget |
| `draw` | 800 | `cubicInOut` | — | Fine for marketing |
| `crossfade` | `√d × 30` | `cubicOut` | no `fallback` | Unpaired items vanish |
| `flip` | `√d × 120` | `cubicOut` | — | Over budget past ~6px |
| `Tween` | 400 | `linear` | — | Both wrong for UI |
| `Spring` | — | — | `stiffness 0.15`, `damping 0.8` | Clamped 0–1, not Motion's scale |
