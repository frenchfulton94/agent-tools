# Component craft

The component-level decisions, with the code. Each exists because its absence is
felt rather than seen — which is the test for whether a detail is worth the
effort.

## Contents

- [Buttons have to feel pressed](#buttons-have-to-feel-pressed)
- [Nothing appears from nothing](#nothing-appears-from-nothing)
- [Popovers come out of their trigger](#popovers-come-out-of-their-trigger)
- [Tooltips after the first are instant](#tooltips-after-the-first-are-instant)
- [Entry without a mount flag](#entry-without-a-mount-flag)
- [Transitions, not keyframes, for anything dynamic](#transitions-not-keyframes-for-anything-dynamic)
- [Blur masks a transition that will not settle](#blur-masks-a-transition-that-will-not-settle)
- [The opacity-against-height problem](#the-opacity-against-height-problem)
- [Perceived performance](#perceived-performance)
- [Six principles from building Sonner](#six-principles-from-building-sonner)
- [Designing a component's API](#designing-a-components-api)

## Buttons have to feel pressed

`transform: scale(0.97)` on `:active`. Instant feedback that the interface heard
the user.

```css
.button {
	transition: transform 160ms var(--ease-out);
}

.button:active {
	transform: scale(0.97);
}
```

Subtle — 0.95 to 0.98. `scale()` scales children too, so the label and any icon
come along, which is what makes it read as physical rather than as a rectangle
shrinking. Applies to any pressable element, not only `<button>`.

No hover gating needed: `:active` is a real press on touch. Gate any separate
`:hover` styling behind `@media (hover: hover) and (pointer: fine)`.

## Nothing appears from nothing

Nothing in the real world disappears and reappears completely. An element
animating from `scale(0)` looks like it came out of nowhere. Start from
`scale(0.9)` or higher with opacity — even a barely-visible initial scale makes
the entrance feel natural, the way a deflated balloon still has a shape.

```svelte
<!-- Svelte's scale transition defaults to start: 0 — always pass one -->
<div transition:scale={{ start: 0.95, duration: 200, easing: quintOut }}>
```

## Popovers come out of their trigger

The CSS default `transform-origin: center` is wrong for almost every popover. It
should scale from the element that opened it.

```css
.popover {
	transform-origin: var(--bits-popover-content-transform-origin);
}
```

Swap the prefix per component: `--bits-dropdown-menu-content-transform-origin`,
`--bits-tooltip-content-transform-origin`,
`--bits-select-content-transform-origin`.

**Modals are the exception.** They are not anchored to a trigger — they appear
centred in the viewport — so `transform-origin: center` is correct there.

Whether a user notices the difference on one popover does not matter. In
aggregate, unseen details become visible.

## Tooltips after the first are instant

A tooltip should delay before appearing, to prevent accidental activation. But
once one is open, hovering a neighbouring trigger should open that one
instantly, with no delay and no animation. This feels faster without defeating
the purpose of the initial delay, and it is what makes a whole toolbar feel
quick.

```svelte
<Tooltip.Provider delayDuration={600} skipDelayDuration={300}>
```

`skipDelayDuration` is the grace window. Bits UI then marks the content
`data-state="instant-open"` rather than `"delayed-open"`, so the animation can be
switched off for exactly those:

```css
.tooltip[data-state='instant-open'] {
	transition-duration: 0ms;
}
```

## Entry without a mount flag

`@starting-style` animates an element's first rendered state in pure CSS.

```css
.toast {
	opacity: 1;
	transform: translateY(0);
	transition: opacity 400ms ease, transform 400ms ease;

	@starting-style {
		opacity: 0;
		transform: translateY(100%);
	}
}
```

This replaces the pattern of setting a `mounted` flag in an effect and keying
styles off it. In Svelte, `transition:` covers the same ground for anything
tied to `{#if}` or `{#each}` membership, and additionally holds the element in
the DOM until the outro finishes. Reach for `@starting-style` on elements that
are always mounted and change state via a `data-` attribute — which is how Bits
UI content works.

## Transitions, not keyframes, for anything dynamic

CSS transitions can be interrupted and retargeted mid-animation; keyframes
restart from zero. For anything a user can trigger twice in a second — toasts
arriving, a toggle — transitions are visibly smoother.

Svelte has the same split one level up: `transition:` is bidirectional and
reverses smoothly, while `in:` and `out:` play past each other and restart when
aborted. Default to `transition:`.

## Blur masks a transition that will not settle

When a crossfade between two states feels off despite trying different easings
and durations, add a subtle `filter: blur(2px)` during the transition.

Without blur you see two distinct objects overlapping — the old state and the
new one — which reads as unnatural. Blur bridges the gap, tricking the eye into
perceiving a single smooth transformation instead of two objects swapping.

```css
.content {
	transition: filter 200ms ease, opacity 200ms ease;
}

.content--transitioning {
	filter: blur(2px);
	opacity: 0.7;
}
```

Keep it under 20px. Heavy blur is expensive, especially in Safari.

## The opacity-against-height problem

When items enter and leave a list and the list reflows, the opacity change has to
work against the height change. This is trial and error. There is no formula —
adjust until it feels right, then look again the next day.

Say so when you hit it rather than presenting a guessed pair of values as
settled. It is one of the few places where the honest answer is "this needs a
feel check".

## Perceived performance

Speed in animation is not only about feeling snappy; it changes how fast the
whole product seems.

- A faster-spinning spinner makes loading feel faster at identical elapsed time.
- A 180ms select feels more responsive than a 400ms one.
- Instant tooltips after the first make a whole toolbar feel faster.
- `ease-out` at 200ms feels faster than `ease-in` at 200ms, because the user sees
  immediate movement.

Perception of speed matters as much as actual speed, and easing amplifies it.

## Six principles from building Sonner

From building a toast library with 13M+ weekly installs. They generalise to any
component.

1. **Developer experience is the feature.** No hooks, no context, no setup.
   Mount `<Toaster />` once, call `toast()` from anywhere. The less friction to
   adopt, the more people use it.
2. **Good defaults matter more than options.** Ship beautiful out of the box.
   Most users never customise, so the default easing, timing, and visual design
   have to be excellent.
3. **Naming creates identity.** "Sonner" (French, "to ring") reads as more
   elegant than "svelte-toast". Trade discoverability for memorability when it
   is worth it.
4. **Handle edge cases invisibly.** Pause timers when the tab is hidden. Fill
   the gaps between stacked toasts with pseudo-elements so hover state survives.
   Capture pointer events during a drag. Nobody notices any of it, which is
   exactly right.
5. **Transitions, not keyframes, for dynamic UI.** Toasts arrive rapidly and
   keyframes restart from zero.
6. **Build a real documentation site.** Let people touch the thing and play with
   it before adopting it. Interactive examples with copyable code lower the bar
   more than prose does.

## Designing a component's API

The through-line of the six: a component is an interface for the developer
before it is one for the user, and the same taste applies.

- **One obvious way in.** A component that can be used four ways will be used
  four ways in one codebase.
- **Props resolve genuine conflicts, not indecision.** Every prop is a decision
  moved onto the call site. Eleven spacing props means eleven chances to be
  inconsistent.
- **Expose state, not styling.** A `data-state` attribute lets the consumer style
  anything; a `variant` prop lets them style what you anticipated. This is why
  the headless-component pattern works.
- **Make the accessible path the default path.** Focus management, escape to
  close, and labelled controls belong inside the component, not in a
  documentation note. On this stack that usually means wrapping a Bits UI
  primitive rather than starting from a `<div>`.
