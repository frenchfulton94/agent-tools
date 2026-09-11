# Svelte motion API reference

Everything Svelte hands you for motion, with the defaults verified against the
`svelte` package source rather than recalled. Pull values from here; never
approximate one.

## Contents

- [Built-in transition defaults](#built-in-transition-defaults)
- [Which directive: `transition:` vs `in:`/`out:`](#which-directive-transition-vs-inout)
- [Easing: CSS tokens to `svelte/easing`](#easing-css-tokens-to-svelteeasing)
- [`Tween`](#tween)
- [`Spring`](#spring)
- [Custom transitions](#custom-transitions)
- [`animate:flip`](#animateflip)
- [`crossfade` — shared element motion](#crossfade--shared-element-motion)
- [Reduced motion](#reduced-motion)
- [Bits UI hooks for motion](#bits-ui-hooks-for-motion)
- [SvelteKit view transitions](#sveltekit-view-transitions)
- [Svelte-specific performance traps](#svelte-specific-performance-traps)

## Built-in transition defaults

From `svelte/transition` and `svelte/animate`. Every one of these is a default
you will normally override.

| Transition | Duration | Easing | Other defaults | What it actually animates |
| --- | --- | --- | --- | --- |
| `fade` | `400` | **`linear`** | — | `opacity` |
| `fly` | `400` | `cubicOut` | `x: 0`, `y: 0`, `opacity: 0` | `transform: translate`, `opacity` |
| `scale` | `400` | `cubicOut` | **`start: 0`**, `opacity: 0` | `transform: scale`, `opacity` |
| `slide` | `400` | `cubicOut` | `axis: 'y'` | **`height`/`width`, `padding-*`, `margin-*`, `border-*-width`, `opacity`** |
| `blur` | `400` | `cubicInOut` | `amount: 5`, `opacity: 0` | `filter: blur`, `opacity` |
| `draw` | `800` (or `len / speed`) | `cubicInOut` | — | `stroke-dasharray`, `stroke-dashoffset` |
| `crossfade` | `(d) => Math.sqrt(d) * 30` | `cubicOut` | — | `transform`, `opacity` |
| `flip` | `(d) => Math.sqrt(d) * 120` | `cubicOut` | — | `transform: translate` |

Three of these break the bar as shipped:

- **`scale` starts at `scale(0)`.** Always pass `start: 0.95` (0.9–0.97).
- **`fade` eases `linear`.** Linear is for constant motion — a marquee, a
  progress bar. An entrance wants `quintOut`.
- **`slide` animates seven layout properties.** Every frame costs layout and
  paint. It is the right tool for an accordion, where there is no transform
  equivalent, and the wrong one everywhere else. Keep the duration short.

`fly` with no `x` or `y` is a `fade` that reads the element's existing
transform. Pass a distance or use `fade`.

`scale` and `fly` both read `getComputedStyle(node).transform` and compose onto
it, so they coexist with a transform you already set. Neither sets
`transform-origin` — set that in CSS.

## Which directive: `transition:` vs `in:`/`out:`

`transition:` is **bidirectional**: interrupt it and it reverses smoothly from
wherever it is. `in:` and `out:` are not — an `in:` keeps playing alongside a
later `out:` rather than reversing, and an aborted `out:` restarts from scratch.

Use `transition:` by default, and for anything a user can trigger twice in a
second. Split into `in:`/`out:` only when the enter and exit paths genuinely
differ, and accept that interruption will be visible.

Transitions are **local by default** — they play only when their own block is
created or destroyed, not when a parent block is. Add `|global` when an element
should animate because an ancestor appeared.

```svelte
{#if visible}
	<p transition:fade|global>fades whenever any ancestor block changes</p>
{/if}
```

## Easing: CSS tokens to `svelte/easing`

The three house curves, and the closest built-in easing function for each,
measured as root-mean-square deviation across the curve:

| CSS token | Curve | `svelte/easing` | Fit |
| --- | --- | --- | --- |
| `--ease-out` | `cubic-bezier(0.23, 1, 0.32, 1)` | `quintOut` | Very close (rms 0.007) |
| `--ease-in-out` | `cubic-bezier(0.77, 0, 0.175, 1)` | `quartInOut` | Loose (rms 0.032) |
| `--ease-drawer` | `cubic-bezier(0.32, 0.72, 0, 1)` | none close | Build it |

When the fit matters — a drawer, or anywhere a CSS transition and a JS-driven
value animate side by side and must agree — generate the exact curve instead:

```js
// $lib/motion/easing.js
/** Sample a CSS cubic-bezier as an easing function for Tween and transitions. */
export function cubicBezier(x1, y1, x2, y2) {
	const cx = 3 * x1;
	const bx = 3 * (x2 - x1) - cx;
	const ax = 1 - cx - bx;
	const cy = 3 * y1;
	const by = 3 * (y2 - y1) - cy;
	const ay = 1 - cy - by;
	const sampleX = (t) => ((ax * t + bx) * t + cx) * t;
	const slopeX = (t) => (3 * ax * t + 2 * bx) * t + cx;

	return (x) => {
		let t = x;
		for (let i = 0; i < 8; i += 1) {
			const error = sampleX(t) - x;
			if (Math.abs(error) < 1e-7) break;
			const slope = slopeX(t);
			if (Math.abs(slope) < 1e-7) break;
			t -= error / slope;
		}
		return ((ay * t + by) * t + cy) * t;
	};
}

export const easeOut = cubicBezier(0.23, 1, 0.32, 1);
export const easeInOut = cubicBezier(0.77, 0, 0.175, 1);
export const easeDrawer = cubicBezier(0.32, 0.72, 0, 1);
```

`svelte/easing` also ships `backOut`, `bounceOut`, `circOut`, `elasticOut`, and
`expoOut` with their `In`/`InOut` variants. `elasticOut` and `bounceOut` are
almost always too much for UI.

## `Tween`

Svelte 5's tween class, for a numeric or interpolatable value the UI reads every
frame — a progress bar, a counter, a gauge. Not for enter/exit; that is what
`transition:` is for.

```svelte
<script>
	import { Tween } from 'svelte/motion';
	import { quintOut } from 'svelte/easing';

	const progress = new Tween(0, { duration: 250, easing: quintOut });
</script>

<div class="bar" style:transform="scaleX({progress.current})"></div>
<button onclick={() => (progress.target = 1)}>fill</button>
```

- **Defaults are `duration: 400` and `easing: linear`.** Pass both.
- `Tween.of(() => expression)` binds the tween to a reactive expression; it has
  to be called during component initialisation.
- `tween.set(value, options)` returns a promise that resolves when
  `tween.current` catches up, and lets you override the defaults per call.

Use the older `tweened` store only in code that has not migrated to runes — it
is deprecated in favour of `Tween`.

## `Spring`

The interruptible one. Reach for it for drag, momentum, anything reversible
mid-flight, and elements that should feel alive.

```svelte
<script>
	import { Spring } from 'svelte/motion';

	const x = new Spring(0, { stiffness: 0.15, damping: 0.8 });
</script>

<div style:transform="translateX({x.current}px)"></div>
```

**Svelte's spring parameters are not Motion's or Apple's.** `stiffness` and
`damping` are both clamped to 0–1 and default to `0.15` and `0.8`; they are
per-frame coefficients, not the physical constants Motion's
`stiffness: 100, damping: 10` describes, and not Apple's damping-ratio-plus-
response pair. Translate by feel against these anchors rather than by arithmetic:

| Want | Svelte `Spring` | Notes |
| --- | --- | --- |
| Default, graceful settle | `{ stiffness: 0.15, damping: 0.8 }` | The default; no visible overshoot |
| Snappy, no overshoot | `{ stiffness: 0.3, damping: 0.9 }` | Pointer-tracking, sliders |
| Momentum with a little bounce | `{ stiffness: 0.2, damping: 0.55 }` | Drag release, flick-to-dismiss |
| Slow and heavy | `{ stiffness: 0.05, damping: 0.9 }` | Large surfaces |

Raising `damping` toward `1` removes overshoot; lowering it adds bounce. Raising
`stiffness` shortens the settle. Tune these on a real interaction — a spring's
numbers do not read the way a duration does.

Two options on `set` matter:

- `spring.set(v, { instant: true })` jumps without animating. This is the
  reduced-motion escape hatch, and the way to seed a position without a
  fly-in from wherever the spring happened to be.
- `spring.set(v, { preserveMomentum: 150 })` keeps the current trajectory for
  that many milliseconds before pulling to the new target. This is the velocity
  handoff at the end of a drag — the seam between finger and animation.

`Spring.of(() => expression)` binds a spring to a reactive expression, during
component initialisation.

## Custom transitions

```js
function whoosh(node, params, options) {
	return {
		delay: 0,
		duration: 200,
		easing: quintOut,
		css: (t, u) => `transform: scale(${1 - 0.05 * u}); opacity: ${t}`
	};
}
```

**Return `css`, not `tick`, whenever the effect can be expressed as CSS.** Svelte
compiles a `css` function into a web animation that runs off the main thread; a
`tick` function runs on the main thread every frame and drops frames while the
page is loading, scripting, or painting. This is Svelte's form of the rule that
CSS beats JavaScript under load — the docs say so directly.

`t` runs 0→1 for an in-transition and 1→0 for an out-transition, after easing;
`u` is `1 - t`. So `1` is always the element's natural state. `options.direction`
is `'in'`, `'out'`, or `'both'`.

Elements with transitions dispatch `onintrostart`, `onintroend`, `onoutrostart`,
and `onoutroend` — useful for chaining, and for measuring how long a transition
actually takes.

## `animate:flip`

The Svelte answer to layout animation. It runs on the immediate children of a
**keyed** `{#each}` when the items reorder — not when items are added or
removed.

```svelte
{#each items as item (item.id)}
	<li animate:flip={{ duration: 200, easing: quintOut }}>{item.label}</li>
{/each}
```

FLIP animates `transform: translate` only, so it is GPU-friendly by
construction. The default duration is `Math.sqrt(distance) * 120` ms, which
exceeds the 300ms UI budget past about 6px of travel — pass an explicit
`duration` for a list the user reorders often.

Combine it with `transition:` on the same element to cover add and remove; the
two do not conflict.

## `crossfade` — shared element motion

`crossfade` returns a `[send, receive]` pair. An element leaving one list with
key `k` and an element arriving in another with the same key animate as one
object travelling between them.

```svelte
<script>
	import { crossfade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	const [send, receive] = crossfade({
		duration: 250,
		easing: quintOut,
		fallback: (node) => ({ duration: 200, easing: quintOut, css: (t) => `opacity: ${t}` })
	});
</script>

{#each todo as item (item.id)}
	<li in:receive={{ key: item.id }} out:send={{ key: item.id }}>{item.text}</li>
{/each}
```

The `fallback` is what plays when there is no counterpart — without one, an item
with no partner vanishes abruptly. Always supply it.

## Reduced motion

Svelte transitions are driven by the Web Animations API, so a global CSS
`@media (prefers-reduced-motion: reduce)` rule that zeroes `transition-duration`
and `animation-duration` **does not touch them**. This is documented Svelte
behaviour, not a bug, and it is the single most commonly missed accessibility
detail in a Svelte codebase.

```svelte
<script>
	import { prefersReducedMotion } from 'svelte/motion';
	import { fly } from 'svelte/transition';

	const enter = $derived(
		prefersReducedMotion.current
			? { y: 0, duration: 120 }
			: { y: 16, duration: 200, easing: quintOut }
	);
</script>

{#if open}<div transition:fly={enter}>…</div>{/if}
```

`prefersReducedMotion` is a `MediaQuery` from `svelte/motion`; read
`.current`. Keep the opacity change — reduced motion means gentler, not none.

For a `Spring`, branch on `instant`:

```js
spring.set(target, { instant: prefersReducedMotion.current });
```

CSS-driven motion in a `<style>` block still needs the media query. A codebase
usually needs both guards, not one.

## Bits UI hooks for motion

Bits UI is this stack's headless component layer, and it exposes the values a
correct animation needs.

| Need | What Bits UI gives you |
| --- | --- |
| Trigger-anchored `transform-origin` | `var(--bits-<component>-content-transform-origin)` — e.g. `--bits-popover-content-transform-origin`, `--bits-dropdown-menu-content-transform-origin`, `--bits-tooltip-content-transform-origin`, `--bits-select-content-transform-origin` |
| Open/closed state for CSS | `[data-state="open"]` / `[data-state="closed"]` |
| Which side the content opened on | `[data-side="top" \| "right" \| "bottom" \| "left"]` |
| Accordion content height | `var(--bits-accordion-content-height)` |
| Content width matching the trigger | `var(--bits-<component>-anchor-width)` |
| Tooltip that skips its delay | `[data-state="instant-open"]`, driven by `Tooltip.Provider skipDelayDuration` |

CSS transitions keyed on `data-state` are the default approach and need no extra
props — Bits UI holds the element in the DOM until the transition finishes. Use
`forceMount` plus the `child` snippet only when you want a Svelte `transition:`
directive on the content, and remember floating content also needs
`wrapperProps` spread onto an outer element. The `bits-ui` skill covers that
plumbing.

## SvelteKit view transitions

SvelteKit has no dedicated integration; call the browser API from `onNavigate`.

```js
import { onNavigate } from '$app/navigation';

onNavigate((navigation) => {
	if (!document.startViewTransition) return;

	return new Promise((resolve) => {
		document.startViewTransition(async () => {
			resolve();
			await navigation.complete;
		});
	});
});
```

Style it with `::view-transition-old(root)` / `::view-transition-new(root)` in a
global stylesheet, and gate it on `prefersReducedMotion.current` — the browser's
default cross-fade is motion the user did not ask for. Keep the duration inside
the UI budget: a page transition the user triggers all day is a high-frequency
animation.

## Svelte-specific performance traps

- **Passing a per-frame value as a component custom property.**
  `<Card --offset="{x}px" />` desugars to a `<svelte-css-wrapper>` carrying the
  variable, so updating it every frame recalculates styles for the whole
  subtree. Set `transform` on the animated element instead.
- **`style:` with a computed string** is fine — it writes one inline property on
  one element. `style:transform="translateY({y}px)"` is the idiomatic, cheap
  form.
- **`@keyframes` in a component `<style>` is scoped** by name hashing, along
  with the `animation` rules that reference it. A keyframe defined in one
  component is not reachable from another; put shared ones in a global
  stylesheet.
- **A `tick`-only custom transition** runs on the main thread. Prefer `css`.
- **`transition:slide` on a long list** pays layout on every frame for every
  transitioning element. Use it for one accordion panel, not for rows.
