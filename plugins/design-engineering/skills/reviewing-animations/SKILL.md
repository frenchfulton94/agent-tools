---
name: reviewing-animations
description: 'Reviews animation and motion code against a high craft bar, producing a Before/After findings table and an explicit block-or-approve verdict. Use when asked to review, critique, or sanity-check motion in a diff, a branch, a pull request, or a component — including when the ask is softer, such as whether an animation feels right, why a transition looks sluggish or janky, or whether a drawer or dropdown is correct. Default is to flag; approval is earned. For writing new motion use animating-interfaces; for surveying a whole codebase into plans use improving-animations. Not a general code reviewer — it looks only at motion.'
license: MIT
---

# Reviewing Animations

A specialised review skill: judge animation and motion code against a high craft
bar. It does not write features, fix unrelated bugs, or review non-motion code.
Asked for a general review, decline and point at a general review skill.

## Operating posture

You are a senior design engineer with a brutal eye for craft. The bias is toward
**motion that feels right**, not motion that merely runs. A transition that
works but feels sluggish, lands from the wrong origin, fires too often, or drops
frames is a regression. Default to flagging. Approval is earned.

The substantive bar comes from Emil Kowalski's animation philosophy. The precise
values — curves, durations, spring configs, Svelte's real defaults — live in
`references/standards.md`. Load it whenever a finding needs an exact value to
cite, which is most findings.

## The ten standards

Every animation in the diff is measured against these. A violation is a finding.

1. **Justified motion.** Every animation answers "why does this animate?" —
   spatial consistency, state indication, feedback, explanation, or preventing a
   jarring change. "It looks cool" on a frequently-seen element is a block.

2. **Frequency-appropriate.** Keyboard-initiated and 100+/day actions get no
   animation. Tens/day gets near-imperceptible motion. Occasional gets standard.
   Rare and first-time can carry delight.

3. **Responsive easing.** Entering and exiting elements use `ease-out` or a
   strong custom curve. `ease-in` on UI is a block — it delays the moment the
   user watches most. Built-in easings are too weak; expect custom curves, and
   expect `quintOut` rather than a bare `cubicOut` on the JavaScript side.

4. **Sub-300ms UI.** Anything slower on a UI element needs a stated reason. On
   this stack that means every Svelte transition carries an explicit `duration`,
   because all of them default to 400ms.

5. **Origin and physical correctness.** Popovers, dropdowns, and tooltips scale
   from their trigger, not centre. Nothing animates from `scale(0)` — which is
   what `transition:scale` does unless `start` is passed. Modals are exempt from
   the origin rule; they stay centred.

6. **Interruptibility.** Rapidly-triggered and gesture-driven motion has to
   retarget from its current value: `transition:` rather than `in:`/`out:`, CSS
   transitions rather than `@keyframes`, a `Spring` rather than a `Tween` for
   anything a finger drives.

7. **GPU-only properties.** `transform` and `opacity`. Animating width, height,
   margin, padding, top, or left is a performance finding — including through
   `transition:slide`, which animates seven layout properties and is acceptable
   only in an accordion.

8. **Accessibility.** Reduced motion is honoured, gentler rather than zero. On
   Svelte transitions that requires `prefersReducedMotion.current` in
   JavaScript: a CSS `@media (prefers-reduced-motion: reduce)` rule does not
   reach them. Hover motion is gated behind
   `@media (hover: hover) and (pointer: fine)`.

9. **Asymmetric enter and exit.** Deliberate actions — a press, a hold, a
   destructive confirm — animate slower; system responses snap. Symmetric timing
   on a press-and-release interaction is a finding.

10. **Cohesion.** Motion matches the component's personality and the rest of the
    product: playful can be bouncier, a dashboard stays crisp. A mismatched
    personality, or a jarring crossfade where a subtle blur would bridge two
    states, is a finding. When unsure whether motion feels right, the strongest
    move is often to delete it.

## Flag on sight

- `transition: all`
- `transition:scale` with no `start`, or any `scale(0)` entrance
- Any Svelte transition with no explicit `duration` on a UI element
- `transition:fade` with no `easing` — the default is `linear`
- `ease-in` on a UI interaction; a weak built-in easing on a deliberate one
- Animation on a keyboard shortcut, command palette, or 100+/day action
- UI duration over 300ms with no stated reason
- `transform-origin: center` or none on a trigger-anchored popover
- `in:`/`out:` on something a user can trigger twice in a second
- `@keyframes` on toasts, toggles, or anything added rapidly
- `transition:slide` outside an accordion
- Any animated layout property: width, height, margin, padding, top, left
- A custom transition returning `tick` where `css` would do
- A component custom property (`--offset={x}`) driving a child transform
- A CSS reduced-motion rule as the only guard on a Svelte transition
- Ungated `:hover` motion
- A `Tween` where a `Spring` belongs — gestures, drags, anything reversible
- An unkeyed `{#each}` carrying `animate:flip`, which silently never runs
- `crossfade` with no `fallback`, so an unpaired item vanishes abruptly
- Symmetric enter/exit timing on a press-and-release or hold interaction
- Everything entering at once where a 30–80ms stagger belongs

## Remedial hierarchy

When proposing fixes, prefer earlier moves over later ones.

1. **Delete the animation** — high frequency, no purpose, keyboard-triggered.
2. **Reduce it** — shorter duration, smaller transform, fewer properties.
3. **Fix the easing** — `ease-in` to `ease-out` or a strong curve.
4. **Fix the origin and physicality** — correct `transform-origin`, replace
   `scale(0)` with `scale(0.95)` plus opacity.
5. **Make it interruptible** — `in:`/`out:` to `transition:`, keyframes to
   transitions, a `Tween` to a `Spring` for gestures.
6. **Move it to the GPU** — layout properties to `transform`/`opacity`, `tick`
   to `css`, a parent CSS variable to a direct `transform`.
7. **Asymmetric timing** — slow the deliberate phase, snap the response.
8. **Polish** — blur to mask a crossfade, stagger for groups,
   `@starting-style` for entry, a spring for something that should feel alive.
9. **Accessibility and cohesion** — `prefersReducedMotion`, hover gating, tune
   to the component's personality.

## Output

Two parts, in this order.

### Part 1 — findings table

A single markdown table, one row per issue. Not a Before:/After: list.

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms var(--ease-out)` | `all` animates unintended properties, off the GPU |
| `transition:scale` | `transition:scale={{ start: 0.95, duration: 200, easing: quintOut }}` | Svelte's default is `scale(0)` at 400ms — nothing appears from nothing, and 400ms is over budget |
| `in:fly` / `out:fly` on a toast | `transition:fly` | `in:`/`out:` restart from scratch when interrupted; toasts arrive rapidly |
| CSS `@media (prefers-reduced-motion)` only | `prefersReducedMotion.current` in the transition params | Svelte transitions run through the Web Animations API and ignore that rule |
| `transform-origin: center` on a popover | `var(--bits-popover-content-transform-origin)` | Popovers scale from their trigger; modals are the exception |

### Part 2 — verdict

Group remaining commentary by impact tier, highest first, omitting empty tiers:
feel-breaking regressions; missed simplifications; performance; interruptibility
and timing; origin, physicality, and cohesion; accessibility.

Close with an explicit decision:

- **Block** — any feel-breaking regression, animation on a keyboard or
  high-frequency action, `scale(0)` or `ease-in` on UI, a reduced-motion guard
  that does not actually reach the animation, or a non-GPU animation with an
  easy GPU fix.
- **Approve** — no feel-breaking regressions, nothing obviously worth deleting,
  durations and easing in bounds, interruptibility handled where it matters,
  reduced motion genuinely honoured.

Cite `file:line`. Pull every value from `references/standards.md` rather than
approximating. When feel genuinely cannot be settled from code — a crossfade, a
spring's bounce, the opacity-against-height balance in an entering list — say so
and recommend the check: slow playback, the DevTools animation inspector, a real
device for gestures, fresh eyes the next day.
