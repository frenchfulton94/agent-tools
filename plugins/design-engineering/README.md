# design-engineering

Interface craft and motion, on the Svelte stack. Seven skills covering the whole
loop — deciding whether something should animate, building it, reviewing it,
auditing a codebase of it, finding what is missing, naming what you can only
describe, and the judgement underneath all of that.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install design-engineering@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you
commit so the plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/design-engineering
claude plugin validate plugins/design-engineering --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `animating-interfaces` | Skill | Building an animation: the gate, the purpose, the tool, the properties, the curve, interruption, exit, reduced motion — plus Svelte recipes for the fifteen components that come up most |
| `reviewing-animations` | Skill | Reviewing motion against ten standards, producing a Before/After table and an explicit block-or-approve verdict |
| `improving-animations` | Skill | Surveying a whole codebase's motion into a prioritized audit and self-contained plans another agent can execute |
| `finding-animation-opportunities` | Skill | Sweeping for motion that is missing, and rejecting most of what it finds |
| `animation-vocabulary` | Skill | Reverse-lookup glossary: a description of an effect in, the exact term out |
| `design-engineering` | Skill | The judgement layer — taste, which details are worth it, defaults over options, cohesion, when to stop |
| `apple-design` | Skill | Gestures and spring physics, velocity handoff and momentum projection, translucent materials, typography, Apple's eight principles |

## Which one fires

All seven sit in one domain, so the boundaries are worth knowing:

- A request to **make** motion goes to `animating-interfaces`.
- A request to **judge** motion goes to `reviewing-animations` for one diff, or
  `improving-animations` for a codebase.
- A request for motion that **does not exist yet** goes to
  `finding-animation-opportunities`.
- A request to **name** an effect goes to `animation-vocabulary`.
- A request about a component or interface **as a whole** goes to
  `design-engineering`.
- Anything **gesture-driven, physical, or translucent** goes to `apple-design`.

`skills/design-engineering/evals/` holds a routing battery covering all seven,
plus the behaviour cases used while adapting them. Rerun it after editing any of
the descriptions — they compete for the same triggers, so a change to one can
pull requests away from another.

## What changed for Svelte

The skills are adapted, not copied. The substantive bar is unchanged; the
mechanics are this stack's. Every Svelte fact below was verified against the
`svelte` package source or the current docs rather than recalled.

- **Svelte's built-in transitions fail the bar by default.** `transition:scale`
  starts at `scale(0)`, `transition:fade` eases `linear`, `Tween` eases
  `linear`, every transition runs 400ms, and `transition:slide` animates seven
  layout properties. Each is now a named finding with its fix.
- **A CSS `prefers-reduced-motion` rule does not reach a Svelte transition** —
  they run through the Web Animations API. The skills require
  `prefersReducedMotion.current` from `svelte/motion`, and treat a CSS-only
  guard alongside `transition:` directives as a block rather than a warning.
- **`transition:` against `in:`/`out:`** replaces the CSS transitions-against-
  keyframes rule for interruptibility. `transition:` is bidirectional;
  `in:`/`out:` restart from scratch when aborted.
- **`Spring` and `Tween` replace Motion's hooks**, with a translation table.
  Svelte clamps `stiffness` and `damping` to 0–1, so a config pasted from a
  React example silently clamps and feels wrong.
- **Easing tokens map to `svelte/easing`** — `quintOut` for the strong ease-out
  (measured rms 0.007), `quartInOut` for the ease-in-out (0.032). The drawer
  curve has no close built-in, so a sampled `cubicBezier` helper ships with it.
- **Bits UI replaces Base UI** as the source of
  `var(--bits-…-content-transform-origin)`, `data-state`,
  `--bits-accordion-content-height`, and the `skipDelayDuration` /
  `instant-open` mechanism behind the instant-tooltip rule.
- **New Svelte-specific findings**: `animate:flip` on an unkeyed `{#each}`
  silently never runs; `crossfade` with no `fallback` makes unpaired items
  vanish; a custom transition returning `tick` instead of `css` runs on the main
  thread; a component custom property (`<Card --offset="{x}px" />`) driving a
  per-frame transform recalculates styles for the whole subtree.
- **SvelteKit view transitions** are treated as high-frequency motion, since
  `onNavigate` fires on every client-side navigation.

Two changes are not about Svelte. The upstream `emil-design-eng` opened with a
scripted greeting that withheld all content until the user asked a question —
dropped, since it fights the way skills load here. And that skill restated the
whole animation catalogue its siblings already carry; here it keeps the
judgement layer and points at them, so seven descriptions are not competing to
answer the same request.

## Boundaries

**Against `frontend`.** That plugin is the stack — Bits UI, Tailwind, BEM, FSD,
i18n. This one is the craft applied to it. "How do I wire a Bits UI popover"
goes there; "why does this popover feel wrong" comes here. The two are meant to
be installed together, and the skills here name `bits-ui`,
`styling-with-tailwind`, and `bem-css` where the mechanics belong to them.

**Against a general code reviewer.** `reviewing-animations` looks only at
motion. Asked for a general review it declines rather than widening.

## Attribution

Adapted from [emilkowalski/skills](https://github.com/emilkowalski/skills) by
Emil Kowalski, MIT licensed. See `NOTICE.md` for the mapping from upstream skill
names to the ones here, and what was changed. The underlying philosophy is
documented at [emilkowal.ski](https://emilkowal.ski/) and
[animations.dev](https://animations.dev/); `apple-design` additionally draws on
Apple's public WWDC design talks.

## License

MIT.
