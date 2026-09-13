---
name: design-engineering
description: 'The craft judgement behind interfaces that feel right — what taste is and how it is trained, why unnoticed details compound, and the component-level decisions that separate software people love from software that merely works: press feedback, good defaults over options, invisible edge cases, cohesion between a component''s motion and its personality. Use when a component or interface is being designed, polished, or critiqued as a whole rather than for one animation; when the ask is that something feel more considered, more premium, less generic, or less like a template; when choosing defaults and API shape for a shared component; and when deciding whether a detail is worth the effort. For building one animation use animating-interfaces; for the gesture and materials layer use fluid-interfaces.'
license: MIT
---

# Design Engineering

The judgement layer. Individual animations have their own skills; this one is
about the decisions around them — what makes a component feel considered, which
details are worth the effort, and when to stop.

The philosophy is Emil Kowalski's, from building Sonner and Vaul and from years
at Vercel and Linear. Its claim is that in a world where everyone's software is
good enough, taste is the differentiator.

## Core philosophy

**Taste is trained, not innate.** Good taste is not personal preference. It is a
trained instinct: the ability to see past the obvious and recognise what
elevates. It comes from surrounding yourself with great work, thinking about why
something feels good, and practising. When building UI, do not just make it
work. Study why the best interfaces feel the way they do, reverse-engineer
animations, inspect interactions.

**Unseen details compound.** Most details users never consciously notice — that
is the point. When a feature behaves exactly as someone assumed it would, they
proceed without a second thought.

> "All those unseen details combine to produce something that's just stunning,
> like a thousand barely audible voices all singing in tune." — Paul Graham

**Beauty is leverage.** People choose tools on the whole experience, not the
feature list. Good defaults and good motion are real differentiators, and beauty
is underused in software.

## What this skill decides

Four questions come up constantly, and getting them wrong is what makes an
interface read as generic.

### Is this detail worth it?

A detail earns its place when it removes a moment of friction or confusion the
user would otherwise absorb silently. Pausing a toast timer when the tab is
hidden is worth it — nobody notices, and without it the toast is gone when they
come back. A second bounce on a menu is not.

The test is whether its absence would be *felt* rather than *seen*. Details that
are only seen are decoration, and decoration on frequently-used UI is a cost.

### Defaults or options?

**Good defaults matter more than options.** Ship beautiful out of the box, since
most users never customise. The default easing, timing, and visual design should
be the ones you would choose anyway. An option exists to resolve a genuine
conflict between two reasonable users, not to avoid making a decision.

This applies inside a codebase as much as in a library. A shared component with
eleven props for spacing has moved the decision onto every call site.

### What personality does this have, and does its motion match?

Motion should match the component's personality and the rest of the product.
Playful can be bouncier; a professional dashboard should be crisp and fast.
Sonner feels satisfying partly because everything is in harmony — it runs
slightly slower than typical UI and uses `ease` rather than `ease-out` to feel
elegant, and that choice agrees with its visual design and even its name.

A mismatch is a real defect: one bouncy component in a crisp app reads as a bug,
not as character.

### When do I stop?

Motion and polish have a point past which more is worse. When unsure whether
something feels right, the strongest move is usually to delete it. Review with
fresh eyes the next day — imperfections invisible during development surface
later — and play animations in slow motion or frame by frame to catch timing
problems that are invisible at full speed.

## Component craft

The specific decisions, with the code, are in
`references/component-craft.md`: press feedback, origin-aware popovers, tooltip
delay behaviour, `@starting-style` entry, the opacity-against-height problem in
entering lists, and the six principles from building a component 13 million
people install a week. Read it when designing or reviewing a component rather
than a single animation.

## Reviewing UI code

When reviewing, use a markdown table with Before, After, and Why columns — one
row per issue. Not a list with "Before:" and "After:" on separate lines.

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms var(--ease-out)` | Name the properties; `all` animates unintended ones off the GPU |
| `transition:scale` | `transition:scale={{ start: 0.95, duration: 200 }}` | Svelte's default is `scale(0)` at 400ms — nothing appears from nothing |
| `ease-in` on a dropdown | `ease-out` with a custom curve | `ease-in` delays the moment the user is watching |
| No `:active` state on a button | `transform: scale(0.97)` on `:active` | A pressable element has to feel pressed |
| `transform-origin: center` on a popover | `var(--bits-popover-content-transform-origin)` | Popovers scale from their trigger; modals stay centred |

For a motion-only review with severity tiers and an explicit verdict, use
`reviewing-animations` — it carries the full standards catalogue. This table is
for the broader case where motion is one part of a UI review.

## Where the rest lives

This skill deliberately does not restate the animation catalogue. Its siblings
own those, and each is self-contained:

| For | Use |
| --- | --- |
| Building an animation, with the full decision sequence and Svelte recipes | `animating-interfaces` |
| Reviewing motion against the ten standards, with a verdict | `reviewing-animations` |
| Auditing a codebase's motion into executable plans | `improving-animations` |
| Finding motion that is missing, and rejecting what should stay still | `finding-animation-opportunities` |
| Gestures, spring physics, translucent materials, typography | `fluid-interfaces` |
| Naming an effect someone can only describe | `animation-vocabulary` |

For the stack underneath — headless components, utility classes, class naming —
the `frontend` plugin's `bits-ui`, `styling-with-tailwind`, and `bem-css` skills
cover the mechanics this skill assumes.

## Tone

Opinionated and brief. Make the call and say why in a line; do not present a
menu of options. Where feel genuinely cannot be settled from code, say so and
name the check rather than guessing at a value.
