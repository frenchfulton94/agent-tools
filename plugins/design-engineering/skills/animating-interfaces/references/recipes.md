# Animation recipes

Ready-to-build Svelte implementations for the cases that come up most. Start
from the recipe and adapt; do not rebuild from a blank file.

Curves are the `--ease-out`, `--ease-in-out`, and `--ease-drawer` tokens from
SKILL.md, and their `svelte/easing` counterparts from
`svelte-motion-api.md`. Reduced-motion and hover gating are shown once each and
apply throughout.

## Contents

- [Button press](#button-press)
- [Dropdown, popover, menu, select](#dropdown-popover-menu-select)
- [Tooltip](#tooltip)
- [Modal](#modal)
- [Drawer / sheet](#drawer--sheet)
- [Toast](#toast)
- [Accordion / collapse](#accordion--collapse)
- [Stagger a group entrance](#stagger-a-group-entrance)
- [List reorder](#list-reorder)
- [Hold to confirm](#hold-to-confirm)
- [Tab indicator with a colour transition](#tab-indicator-with-a-colour-transition)
- [Scroll reveal](#scroll-reveal)
- [Drag to dismiss](#drag-to-dismiss)
- [Number ticker](#number-ticker)
- [Masking a crossfade that will not settle](#masking-a-crossfade-that-will-not-settle)
- [Page transition](#page-transition)

## Button press

Instant feedback that the interface heard the user. Pure CSS — no Svelte
machinery earns its place here.

```svelte
<button class="button">Save</button>

<style>
	.button {
		transition: transform 160ms var(--ease-out);
	}

	.button:active {
		transform: scale(0.97);
	}

	@media (prefers-reduced-motion: reduce) {
		.button { transition: none; }
	}
</style>
```

`scale()` scales children too, so the label and any icon come along — that is
what makes it read as a physical press. `:active` is a real press on touch, so
no hover gating is needed here; gate any separate `:hover` styling.

## Dropdown, popover, menu, select

Scales out of its trigger, not out of thin air. Bits UI supplies the origin.

```svelte
<script>
	import { Popover } from 'bits-ui';
</script>

<Popover.Root>
	<Popover.Trigger>Open</Popover.Trigger>
	<Popover.Portal>
		<Popover.Content class="popover">…</Popover.Content>
	</Popover.Portal>
</Popover.Root>

<style>
	:global(.popover) {
		transform-origin: var(--bits-popover-content-transform-origin);
		transition:
			opacity 200ms var(--ease-out),
			transform 200ms var(--ease-out);
	}

	:global(.popover[data-state='closed']) {
		opacity: 0;
		transform: scale(0.95);
	}

	:global(.popover[data-state='open']) {
		@starting-style {
			opacity: 0;
			transform: scale(0.95);
		}
	}
</style>
```

The `transform-origin` is the whole point: the panel should look like it came
out of the thing you clicked. Swap the variable prefix for the component —
`--bits-dropdown-menu-content-transform-origin`,
`--bits-select-content-transform-origin`.

Bits UI keeps the element mounted until the transition finishes, so `data-state`
alone is enough. Reach for `forceMount` + the `child` snippet only if you want a
Svelte `transition:` directive here instead.

## Tooltip

The same shape, faster, plus the detail most implementations miss.

```svelte
<script>
	import { Tooltip } from 'bits-ui';
</script>

<Tooltip.Provider delayDuration={600} skipDelayDuration={300}>
	<Tooltip.Root>
		<Tooltip.Trigger>?</Tooltip.Trigger>
		<Tooltip.Content class="tooltip">Rename</Tooltip.Content>
	</Tooltip.Root>
</Tooltip.Provider>

<style>
	:global(.tooltip) {
		transform-origin: var(--bits-tooltip-content-transform-origin);
		transition:
			opacity 125ms var(--ease-out),
			transform 125ms var(--ease-out);
	}

	:global(.tooltip[data-state='closed']) {
		opacity: 0;
		transform: scale(0.97);
	}

	/* Once one tooltip has opened, neighbours open with no delay and no motion */
	:global(.tooltip[data-state='instant-open']) {
		transition-duration: 0ms;
	}
</style>
```

The initial delay prevents accidental activation. Skipping both the delay and
the animation afterwards is what makes the whole toolbar feel faster.
`skipDelayDuration` on the provider is the grace window in which that applies.

## Modal

The one popover that stays centred.

```css
:global(.modal) {
	transform-origin: center; /* exempt — not anchored to a trigger */
	transition:
		opacity 250ms var(--ease-out),
		transform 250ms var(--ease-out);
}

:global(.modal[data-state='closed']) {
	opacity: 0;
	transform: scale(0.96);
}

:global(.overlay) {
	transition: opacity 250ms var(--ease-out);
}
```

Animate the overlay's opacity alongside it so the two read as one surface.

## Drawer / sheet

```svelte
{#if open}
	<div class="drawer" transition:fly={{ y: '100%', duration: 500, easing: easeDrawer }}>
		…
	</div>
{/if}
```

`y: '100%'` is a string, so it translates by the drawer's own height whatever
the content — the same reason Vaul uses a percentage. `easeDrawer` is the
`cubic-bezier(0.32, 0.72, 0, 1)` helper from `svelte-motion-api.md`; the
built-in easings have nothing close.

Add drag and it becomes a gesture problem — see **Drag to dismiss**.

## Toast

```css
.toast {
	opacity: 1;
	transform: translateY(0);
	transition:
		opacity 400ms ease,
		transform 400ms ease;

	@starting-style {
		opacity: 0;
		transform: translateY(100%);
	}
}
```

`ease` rather than `ease-out`, slightly slower than the usual UI budget: Sonner
reads as elegant partly because its motion is tuned to the component's
personality rather than to the generic budget. Transitions rather than
keyframes, because toasts arrive rapidly and a keyframe restarts from zero.

When toasts stack and the list reflows, the opacity change has to work against
the height change. There is no formula for that pair — adjust until it feels
right, then look again the next day.

## Accordion / collapse

The sanctioned exception to "transform and opacity only": there is no transform
equivalent for height. Bits UI measures the content for you.

```css
:global(.accordion-content) {
	overflow: hidden;
	transition:
		height 200ms var(--ease-out),
		opacity 200ms var(--ease-out);
}

:global(.accordion-content[data-state='open']) {
	height: var(--bits-accordion-content-height);
}

:global(.accordion-content[data-state='closed']) {
	height: 0;
	opacity: 0;
}
```

Keep it short — this animation costs layout on every frame, so a long duration
is expensive as well as sluggish. Never animate to `height: auto`.

`transition:slide` does the same job and also animates padding, margin, and
border-width. It is acceptable here and nowhere else.

## Stagger a group entrance

For a list or grid a user sees occasionally — not one they scroll past all day.

```svelte
{#each items as item, i (item.id)}
	<li in:fly={{ y: 8, duration: 300, delay: i * 50, easing: quintOut }}>
		{item.label}
	</li>
{/each}
```

30–80ms between items. Longer feels slow. Stagger is decorative, so it must
never block interaction while it plays — and cap the delay on a long list
(`Math.min(i, 6) * 50`) or the last row arrives seconds late.

## List reorder

```svelte
<script>
	import { flip } from 'svelte/animate';
	import { fly } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
</script>

{#each items as item (item.id)}
	<li
		animate:flip={{ duration: 200, easing: quintOut }}
		in:fly={{ y: 8, duration: 200, easing: quintOut }}
		out:fly={{ y: -8, duration: 150, easing: quintOut }}
	>
		{item.label}
	</li>
{/each}
```

`animate:flip` handles reorder; the transitions handle add and remove. The each
block has to be keyed or none of it runs. FLIP animates `transform` only, so it
stays on the GPU. Its default duration scales with distance and runs past 300ms
quickly — pass one.

## Hold to confirm

For destructive actions where a plain click is too easy to fire by accident.

```css
.overlay {
	clip-path: inset(0 100% 0 0);
	transition: clip-path 200ms var(--ease-out); /* release: snappy */
}

.button:active .overlay {
	clip-path: inset(0 0 0 0);
	transition: clip-path 2s linear;             /* press: slow, deliberate */
}

.button:active {
	transform: scale(0.97);
}
```

`linear` is correct here — the fill is a progress indicator, and progress should
not ease. This is the asymmetric-timing rule in its clearest form: slow where
the user is deciding, fast where the system responds.

## Tab indicator with a colour transition

Timing individual colour transitions across a tab list never quite lands. Clip
instead: duplicate the tab list, style the copy as the active state, and clip
the copy so only the active tab shows.

```svelte
<div class="tabs">
	{#each tabs as tab}<button>{tab.label}</button>{/each}
</div>
<div class="tabs tabs--active" style:clip-path={activeClip} aria-hidden="true">
	{#each tabs as tab}<button tabindex="-1">{tab.label}</button>{/each}
</div>

<style>
	.tabs--active {
		position: absolute;
		inset: 0;
		transition: clip-path 250ms var(--ease-in-out);
	}
</style>
```

`activeClip` is `inset(0 {right}% 0 {left}%)` computed from the active tab's
position. Text and background change together, perfectly in sync, because they
are one element being revealed rather than two colours being interpolated. Hide
the copy from assistive technology.

## Scroll reveal

Marketing surfaces only. Do not do this to functional UI a user visits daily.

```svelte
<script>
	import { prefersReducedMotion } from 'svelte/motion';

	let visible = $state(false);

	/** Reveal once, when the element first enters the viewport. */
	function reveal(node) {
		if (prefersReducedMotion.current) {
			visible = true;
			return;
		}
		const observer = new IntersectionObserver(
			([entry]) => {
				if (!entry.isIntersecting) return;
				visible = true;
				observer.disconnect();
			},
			{ rootMargin: '-100px' }
		);
		observer.observe(node);
		return () => observer.disconnect();
	}
</script>

<figure {@attach reveal} class="reveal" class:reveal--visible={visible}>…</figure>

<style>
	.reveal {
		clip-path: inset(0 0 100% 0);
		transition: clip-path 600ms var(--ease-in-out);
	}

	.reveal--visible {
		clip-path: inset(0 0 0 0);
	}
</style>
```

Fire it once. Re-animating on every scroll-by is an interface fighting its
reader.

## Drag to dismiss

Springs, not durations, because the user can reverse mid-motion. The shape:

```svelte
<script>
	import { Spring } from 'svelte/motion';

	const y = new Spring(0, { stiffness: 0.2, damping: 0.55 });
</script>

<div {@attach drag} style:transform="translateY({y.current}px)" style:touch-action="none">
	…
</div>
```

Inside the attachment:

```js
y.set(pointerY - grabOffset, { instant: true });     // tracking: 1:1, no smoothing
y.set(target, { preserveMomentum: 150 });            // release: continue at the finger's velocity
```

Six details separate a good drag from a bad one:

- **Velocity dismissal.** Dismiss when `Math.abs(distance) / elapsedMs > 0.11`,
  so a flick is enough on its own without crossing the distance threshold.
- **Pointer capture** once the drag starts, so it continues when the pointer
  leaves the element's bounds.
- **Multi-touch protection** — bail on a new pointer while dragging, or
  switching fingers makes the element jump.
- **`{ instant: true }` while tracking.** During the drag the element is the
  finger; the spring's job starts at release. Letting the spring smooth the drag
  itself adds lag exactly where directness matters.
- **`preserveMomentum` at release**, so the animation continues at the finger's
  velocity instead of restarting from zero. That seam is what separates "fluid"
  from "fine".
- **`touch-action: none`**, or the browser claims the gesture for scrolling and
  `pointermove` stops arriving.

Set `transform` on the element, never a CSS variable on its parent — a variable
on a parent recalculates styles for every child on every frame.

The complete implementation — grab offset, hysteresis, rubber-banding at
boundaries, a velocity history, momentum projection to snap points, and listener
cleanup — is in the `apple-design` skill's
`references/gestures-and-springs.md`. Start from that rather than rebuilding it.

## Number ticker

```svelte
<script>
	import { Tween } from 'svelte/motion';
	import { quintOut } from 'svelte/easing';

	let { value } = $props();
	const display = Tween.of(() => value, { duration: 400, easing: quintOut });
</script>

<span class="ticker">{Math.round(display.current).toLocaleString()}</span>

<style>
	.ticker { font-variant-numeric: tabular-nums; }
</style>
```

`tabular-nums` is not optional: without fixed-width digits the number jitters
horizontally while it counts, which reads as jank rather than motion.

## Masking a crossfade that will not settle

When two states overlap visibly during a transition and no amount of easing or
duration tuning fixes it, blur the seam.

```css
.content {
	transition:
		filter 200ms ease,
		opacity 200ms ease;
}

.content--transitioning {
	filter: blur(2px);
	opacity: 0.7;
}
```

Without blur the eye reads two distinct objects swapping. Blur blends them into
one perceived transformation. Keep it under 20px — heavy blur is expensive,
especially in Safari.

## Page transition

```svelte
<!-- src/routes/+layout.svelte -->
<script>
	import { onNavigate } from '$app/navigation';
	import { prefersReducedMotion } from 'svelte/motion';

	onNavigate((navigation) => {
		if (!document.startViewTransition || prefersReducedMotion.current) return;

		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});
</script>
```

```css
/* src/app.css */
::view-transition-old(root),
::view-transition-new(root) {
	animation-duration: 200ms;
	animation-timing-function: var(--ease-out);
}
```

A page transition fires on every navigation, which puts it near the top of the
frequency table. Keep it short, or leave it out — an app whose core loop is
navigation is one where no transition is the right answer.
