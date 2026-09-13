# Attribution

The seven skills in this plugin are adapted from
[emilkowalski/skills](https://github.com/emilkowalski/skills) by Emil Kowalski.

- **Source:** https://github.com/emilkowalski/skills
- **License:** MIT — see the upstream `LICENSE`
- **Vendored at:** 2026-09-10

They are **adapted, not reproduced**: rewritten for the Svelte and SvelteKit
stack, re-scoped against each other, and edited to this catalogue's skill
conventions. Do not treat any passage here as a verbatim quotation of the
upstream text.

The underlying design philosophy is documented at
[emilkowal.ski](https://emilkowal.ski/) and taught at
[animations.dev](https://animations.dev/). `fluid-interfaces` additionally draws on
Apple's public WWDC design talks — chiefly *Designing Fluid Interfaces* (2018),
*Designing Audio-Haptic Experiences*, *The Details of UI Typography* (2020), and
*Principles of Great Design*.

## Name mapping

| Upstream | Here |
|---|---|
| `animate` | `animating-interfaces` |
| `review-animations` | `reviewing-animations` |
| `improve-animations` | `improving-animations` |
| `find-animation-opportunities` | `finding-animation-opportunities` |
| `emil-design-eng` | `design-engineering` |
| `animation-vocabulary` | `animation-vocabulary` |
| `apple-design` | `fluid-interfaces` |

Renamed to this catalogue's descriptive/gerund convention, which every other
plugin here follows. Upstream ships further skills — `animate-expo`,
`write-swift`, `pick-ui-library`, `prototype`, `ask-sonner` — that were not
brought over; they target React Native, Swift, and Emil's own libraries rather
than this stack.

## What was changed

**Stack.** React, Framer Motion, and Base UI examples were replaced with Svelte
5, `svelte/transition`, `svelte/motion`, `svelte/animate`, and Bits UI. Every
Svelte default and API claim was verified against the `svelte` package source or
the current documentation rather than recalled; the easing correspondences were
measured numerically.

**Added.** Svelte-specific findings with no upstream equivalent: the built-in
transition defaults that break the bar; the Web Animations API reason a CSS
`prefers-reduced-motion` rule never reaches a Svelte transition; `transition:`
against `in:`/`out:` for interruptibility; `animate:flip` on an unkeyed `{#each}`;
`crossfade` without a `fallback`; `tick` against `css` in custom transitions;
component custom properties driving per-frame transforms; SvelteKit view
transitions as high-frequency motion.

**Removed.** `emil-design-eng`'s scripted opening message, which withheld
content until the user asked a question — it conflicts with how skills load
here. Its animation catalogue was also cut back to a pointer at the sibling
skills that own it, so the seven descriptions do not compete to answer the same
request.

**Editorial.** Frontmatter descriptions were rewritten to this catalogue's
trigger conventions, bodies were split into `references/` against the 500-line
skill limit, and emphasis inflation was removed.
