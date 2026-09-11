# Routing battery

This plugin ships seven skills whose descriptions all contain the word
"animation". That makes routing, not triggering, the failure mode worth testing:
a query that should build gets reviewed, a codebase audit gets answered as a
single-diff review, a naming question gets answered with an implementation.

Run by giving a clean-context agent the **descriptions only** — all seven, plus
the distractors — one query at a time, asking which single skill applies or
"none". Score each row against its expected target. A run is a pass when every
row routes correctly; anything else names the description that needs narrowing.

Useful distractors from this catalogue: `bits-ui` (headless component wiring),
`styling-with-tailwind` (utility classes), `bem-css` (class naming),
`reviewing-code-security` (OWASP review), `authoring-skills`.

## Routing (25)

Build — expect `animating-interfaces`:

| # | Query |
| --- | --- |
| R1 | "Animate this dropdown so it opens nicely." |
| R2 | "Add a swipe-to-dismiss gesture to the toast." |
| R3 | "This modal just pops into existence. Make it less jarring." |
| R4 | "Our drawer feels sluggish when it opens — fix it." |
| R5 | "Write the enter and exit transitions for this notification list." |

Review one diff — expect `reviewing-animations`:

| # | Query |
| --- | --- |
| R6 | "Review the motion in this PR." |
| R7 | "Does this transition look right to you?" |
| R8 | "Check the animations on this branch before I merge." |
| R9 | "Is a 400ms fade on a select the right call here?" |

Audit a codebase — expect `improving-animations`:

| # | Query |
| --- | --- |
| R10 | "Improve the animations across this app." |
| R11 | "Audit our motion and give me a roadmap." |
| R12 | "We have easing values scattered everywhere — consolidate them." |
| R13 | "This whole app feels janky. Where do I start?" |

Find what is missing — expect `finding-animation-opportunities`:

| # | Query |
| --- | --- |
| R14 | "What could be animated on this settings page?" |
| R15 | "This dashboard feels static. Any ideas?" |
| R16 | "Where would motion actually help in our onboarding flow?" |

Name an effect — expect `animation-vocabulary`:

| # | Query |
| --- | --- |
| R17 | "What's it called when a list shifts to make room as you drag an item?" |
| R18 | "What's the word for the iOS thing where scrolling resists and snaps back?" |
| R19 | "Is it a morph or a crossfade when one icon turns into another?" |

Judgement about a component as a whole — expect `design-engineering`:

| # | Query |
| --- | --- |
| R20 | "This component works but feels generic. What would make it feel considered?" |
| R21 | "How many props should our Button expose?" |
| R22 | "Is this detail worth the effort, or am I gold-plating?" |

Gestures, physics, materials, type — expect `apple-design`:

| # | Query |
| --- | --- |
| R23 | "Make this bottom sheet feel native — it should carry momentum when you flick it." |
| R24 | "How do I do frosted-glass chrome without the text going unreadable?" |
| R25 | "Our headings look loose at large sizes. What's the tracking supposed to be?" |

## Should not trigger (10)

Near-misses that share vocabulary or surface with the positives.

| # | Query | Belongs to |
| --- | --- | --- |
| N1 | "Wire up a Bits UI popover with a custom trigger." | `bits-ui` |
| N2 | "Why isn't my `animate-spin` class producing any CSS?" | `styling-with-tailwind` |
| N3 | "What should I call the modifier class for a disabled card?" | `bem-css` |
| N4 | "Review this PR for injection risks." | `reviewing-code-security` |
| N5 | "Our CI is slow. Where's the time going?" | none |
| N6 | "Write a skill that captures our motion review checklist." | `authoring-skills` |
| N7 | "The loading spinner never stops — the fetch must be hanging." | none |
| N8 | "Convert this animation config file from JS to TypeScript." | `refactoring-typescript` |
| N9 | "Add a `prefers-color-scheme` dark theme to the app." | `styling-with-tailwind` |
| N10 | "Make the video autoplay muted on mobile." | none |

N2, N8, and N9 are the valuable ones: each contains a motion word in a request
that is not about motion. If any of them fires a skill from this plugin, the
description doing it is too greedy.

## Known ambiguity

Two rows are genuinely borderline and are scored as passes for either target:

- **R9** — a single value judgement could reasonably route to
  `animating-interfaces` (it has the duration table) or `reviewing-animations`
  (it is a judgement on existing code). Either is useful.
- **R13** — "feels janky" could route to `improving-animations` (a codebase
  audit) or `finding-animation-opportunities` (motion that is missing). Prefer
  the audit; accept either.

Do not "fix" these by lengthening a description. Two skills answering one vague
question usefully is a better outcome than a description grown until it swallows
its neighbour's territory.
