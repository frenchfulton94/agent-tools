---
name: animating-interfaces
description: 'Builds an animation from scratch on the Svelte stack, making the decisions in the order that determines whether it feels right — whether it should animate at all, what purpose it serves, which tool, which properties, which curve and duration, how it interrupts, how it exits — then writes the implementation. Use when asked to animate something, add motion, make a component feel alive, build a transition or a drawer or a toast, or fix motion that feels sluggish, janky, or like it came out of nowhere. Also use when a Svelte transition, an `animate:flip`, a `Tween`, or a `Spring` is being written for the first time, even when the request never says "animation". For critiquing motion that already exists use reviewing-animations; for surveying a whole codebase use improving-animations; for naming an effect use animation-vocabulary.'
license: MIT
---

# Animating Interfaces

A construction skill: turn a request for motion into an implementation that
would survive a strict review. The bar is Emil Kowalski's animation philosophy —
the same bar `reviewing-animations` enforces.

Two failure modes, and the first is worse:

1. **Animating something that should not animate.** The gate below exists to
   produce zero lines of code sometimes. That is a success, not a dodge.
2. **Animating the right thing with the wrong ingredients** — `ease-in` on an
   entrance, `scale(0)`, keyframes on a toast, a dropdown slow enough to feel
   like waiting.

Make the call, state the reasoning in one line, write the code. Motion is not a
menu of options for the user to pick from.

Svelte supplies most of the ingredients, and several of its defaults fail this
bar — `transition:scale` starts at `scale(0)`, `transition:fade` eases
`linear`, every built-in runs 400ms, and a CSS `prefers-reduced-motion` rule
does not reach any of them. Assume nothing about a Svelte default; the verified
table is in `references/svelte-motion-api.md`.

## The build sequence

Run it in order. Steps 1 and 2 gate everything — do not reach for a curve
before you know whether it animates at all.

### 1. Should this animate at all?

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation, ever. Stop here. |
| Tens of times/day (hover effects, list navigation) | Near-imperceptible only — fast and subtle, or nothing |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, success, celebration) | The delight budget lives here |

A keyboard-initiated action is a disqualifier, not a judgement call. Raycast has
no open/close animation, which is correct for something opened hundreds of times
a day. If the request fails this gate, say so plainly, skip the animation, and
offer the non-motion alternative — an instant state change, a static affordance.

### 2. What is the purpose?

Name it in one of these words before continuing: **feedback**, **spatial
consistency**, **state indication**, **preventing a jarring change**,
**explanation** (marketing and onboarding only), or **delight** (rare tier
only).

Cannot name it? Do not build it. "It looks cool" on a frequently-seen element is
a reason to stop.

Check **function** too: data the user is reading or acting on should not move
for style. A mouse-tracking effect belongs on a marketing page, not on a chart
in a banking app.

### 3. Pick the tool — cheapest that works

Walk down; stop at the first that fits.

| Need | Tool |
| --- | --- |
| Hover, press, colour, a state you can express as a class or `data-` attribute | **CSS transition** |
| Enter/exit tied to `{#if}` or `{#each}` membership | **`transition:`** from `svelte/transition` |
| Enter/exit where CSS alone suffices and the element is always mounted | **CSS `@starting-style`** |
| Reordering a keyed `{#each}` | **`animate:flip`** from `svelte/animate` |
| A numeric value the UI reads continuously (progress, a counter, a position) | **`Tween`** from `svelte/motion` |
| Drag, momentum, anything interruptible mid-flight | **`Spring`** from `svelte/motion` |
| Shared-element motion between two lists or views | **`crossfade`**, or the View Transitions API |
| Layout animations and gesture choreography beyond the above | **Motion** (`motion.dev`), via an attachment |

Prefer `transition:` over hand-rolled mount flags: it already waits for the
outro before unmounting, and it is reversible mid-flight.

If the task needs a *component* rather than an animation — a dialog, a drawer, a
command menu, a dropdown — build it on **Bits UI** rather than hand-rolling one.
Hand-rolled versions are how you end up with a `<div>` dropdown and no focus
management.

### 4. Pick the properties

- **`transform` and `opacity` only.** They skip layout and paint and run on the
  GPU. `width`/`height`/`margin`/`padding`/`top`/`left` trigger all three.
- **`transition:slide` animates height, padding, margin, and border-width** —
  seven layout properties, by construction. It is acceptable for an accordion,
  where there is no transform equivalent. Reach for `fly` or a scale elsewhere.
- **`transition:scale` defaults to `start: 0`.** Nothing in the real world
  appears from nothing. Pass `start: 0.95` (0.9–0.97) every time.
- **`transform-origin` at the trigger** for popovers, dropdowns, menus, and
  tooltips. Bits UI supplies it as
  `var(--bits-<component>-content-transform-origin)`. Modals are exempt — they
  are not anchored to a trigger, so they stay centred.
- **Percentages in `translate()`** are relative to the element's own size, so
  `translateY(100%)` moves it by its own height whatever the content. Prefer
  them over hardcoded pixels.
- **Do not drive a child's transform from a CSS variable on a parent.** In
  Svelte that includes passing `--offset={x}` to a component: it desugars to a
  `<svelte-css-wrapper>` carrying the variable, so every frame recalculates
  styles for the whole subtree. Set `transform` on the element itself.

### 5. Easing and duration — or a spring

| Situation | Easing |
| --- | --- |
| Entering or exiting | `ease-out` |
| Moving or morphing on screen | `ease-in-out` |
| Hover, colour change | `ease` |
| Constant motion (marquee, progress) | `linear` |
| Default | `ease-out` |

Never `ease-in` on UI. It starts slow, delaying the exact moment the user is
watching; `ease-out` at 200ms *feels* faster than `ease-in` at 200ms.

Built-in CSS easings are too weak. Define these as tokens and use them:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* iOS-like drawer (Ionic) */
```

In JavaScript — a `transition:` parameter, a `Tween`, a custom transition — pass
the matching function from `svelte/easing`: `quintOut` for `--ease-out`,
`quartInOut` for `--ease-in-out`. `--ease-drawer` has no close built-in; build
it with the `cubicBezier` helper in `references/svelte-motion-api.md` so the CSS
token and the JS easing stay the same curve.

`Tween` defaults to `easing: linear`. Always pass one.

**Duration:**

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing, explanatory | Can be longer |

UI animations stay under 300ms. A 180ms dropdown feels more responsive than a
400ms one — and 400ms is what every Svelte built-in transition does unless you
pass `duration`.

**Reach for a `Spring` instead** when the motion is a drag with momentum, an
element that should feel alive, a gesture the user can interrupt or reverse, or
decorative mouse-tracking. Svelte's `Spring` takes `stiffness` and `damping`
clamped to 0–1 (defaults `0.15` and `0.8`) — not the 100/10 scale Motion uses.
Translation table in `references/svelte-motion-api.md`. Keep bounce out of most
UI; reserve it for drag-to-dismiss and playful moments.

### 6. Interruption and exit

- **Use `transition:`, not `in:`/`out:`, for anything triggered rapidly.**
  `transition:` is bidirectional and reverses smoothly mid-flight; `in:` and
  `out:` play past each other and restart from scratch when aborted. Split them
  only when the enter and exit paths genuinely differ, and accept that cost.
- **Use transitions, not `@keyframes`,** for the same reason in plain CSS:
  transitions retarget from the current value, keyframes restart from zero.
- **Springs for gestures**, because they carry velocity through an interruption.
  `spring.set(value, { preserveMomentum: ms })` is the fling primitive.
- **Exit the way it entered.** A toast that slides in from the bottom leaves
  through the bottom. Symmetric paths are what make swipe-to-dismiss obvious.
- **Asymmetric timing where the user is deciding.** Slow on the deliberate phase
  (a hold-to-confirm press, 2s linear), snappy on the system response (release,
  200ms ease-out).

### 7. Reduced motion and pointer gating

These ship with the animation, not as a follow-up.

Svelte transitions are driven by the Web Animations API, so a global
`@media (prefers-reduced-motion: reduce)` rule that zeroes `transition-duration`
and `animation-duration` has no effect on them. Read the preference in
JavaScript instead:

```svelte
<script>
	import { prefersReducedMotion } from 'svelte/motion';
	import { fly } from 'svelte/transition';
</script>

{#if open}
	<div transition:fly={{ y: prefersReducedMotion.current ? 0 : 16, duration: 200 }}>
		…
	</div>
{/if}
```

Reduced motion means fewer and gentler animations, not zero — keep the opacity
and colour changes that aid comprehension, drop the movement.

CSS-driven motion still needs the media query, and hover motion needs pointer
gating because touch fires a false hover on tap:

```css
@media (hover: hover) and (pointer: fine) {
	.card:hover { transform: scale(1.02); }
}
```

## Never ship

Each of these is an automatic block in `reviewing-animations`.

| Never | Instead |
| --- | --- |
| `transition: all` | Name the exact properties |
| `transition:scale` with default `start` | `transition:scale={{ start: 0.95 }}` |
| Any Svelte transition with default `duration` on UI | Pass `duration: 150–250` |
| `transition:fade` with default easing | `easing: quintOut` |
| `ease-in` on a UI element | `ease-out` or a strong custom curve |
| Built-in `ease-out` on a deliberate animation | `cubic-bezier(0.23, 1, 0.32, 1)` |
| Animation on a keyboard shortcut or 100+/day action | No animation |
| UI duration over 300ms with no reason | 150–250ms |
| `transform-origin: center` on a trigger-anchored popover | `var(--bits-…-content-transform-origin)` (modals exempt) |
| `in:`/`out:` on a rapidly-triggered element | `transition:` |
| `transition:slide` outside an accordion | `fly` or a scale |
| A CSS variable on a parent driving a child's transform | `transform` on the element itself |
| A custom transition returning only `tick` | Return `css` so it runs off the main thread |
| A CSS reduced-motion rule as the only guard on a Svelte transition | `prefersReducedMotion.current` |
| Ungated `:hover` motion | `@media (hover: hover) and (pointer: fine)` |
| Everything entering at once | 30–80ms stagger |

## Where to look

- `references/recipes.md` — ready-to-build Svelte implementations for button
  press, dropdown, tooltip, modal, drawer, toast, accordion, stagger,
  hold-to-confirm, tab indicator, scroll reveal, list reorder, drag-to-dismiss,
  and page transitions. Read whenever the request matches one; start from the
  recipe rather than a blank file.
- `references/svelte-motion-api.md` — every built-in transition's real defaults,
  the `Spring`/`Tween` parameter translation, the easing mapping with a
  `cubicBezier` helper, the custom-transition contract, `animate:flip`,
  `crossfade`, and SvelteKit view transitions. Read when picking a Svelte API or
  when a default looks suspicious.

## Output

Write the code. Then, in a few lines:

- **The gate result** — frequency tier and the named purpose. If part of the
  request was rejected, say which and why.
- **The ingredients** — tool, properties, curve, duration or spring config.
- **What to feel-check** — when the result depends on feel you cannot judge from
  code (a crossfade, a spring's bounce, the opacity/height balance in an
  entering list), say so and point at the check: play it at 2–5× duration or in
  the DevTools animation inspector, step it frame by frame, test gestures on a
  real device, and look again the next day with fresh eyes.

The code is the deliverable, not a report. When the honest answer is "this
should not animate", give it — that answer is the reason this skill exists.
