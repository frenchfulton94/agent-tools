# Behaviour test cases

A/B cases for the adaptation, graded against written assertions. Rerun after
editing any skill in this plugin and check for regressions.

Each case is run twice against a small SvelteKit app: once with no skill loaded,
once with the named skill. Grade with quoted evidence from the output — no
benefit of the doubt. The assertions are mechanical wherever possible, because
the whole point of these skills is that the values are not a matter of opinion.

## Case 1 — the Svelte defaults

Prompt: _"Animate this dropdown open and closed."_ Target:
`animating-interfaces`.

Assertions: `transition:scale` carries an explicit `start` of 0.9–0.97; carries
an explicit `duration` of 150–250; carries an explicit `easing` that is not
`linear` or a bare built-in; `transform-origin` is set from a
`--bits-…-content-transform-origin` variable; reduced motion is handled through
`prefersReducedMotion.current` rather than a CSS media query alone.

This is the load-bearing case. Without the skill, an agent that knows Svelte
writes `transition:scale` and ships a 400ms `scale(0)` entrance from centre,
which violates four of the ten standards at once and looks like correct,
idiomatic Svelte.

## Case 2 — reduced motion that does not work

Prompt: _"Make sure our animations respect prefers-reduced-motion."_ Target:
`animating-interfaces` or `reviewing-animations`.

Assertions: the answer states that a CSS `@media (prefers-reduced-motion)` rule
does not affect `transition:` directives; it reaches for `prefersReducedMotion`
from `svelte/motion`; it keeps opacity feedback rather than removing all motion;
it does not claim the CSS rule alone is sufficient.

The failure this catches is silent and looks like success: a reviewer sees a
media query in the stylesheet, marks accessibility as handled, and every Svelte
transition in the app keeps playing at full strength.

## Case 3 — spring parameters from the wrong library

Prompt: _"Add a spring to this drag so it settles nicely — use stiffness 100,
damping 10."_ Target: `animating-interfaces` or `fluid-interfaces`.

Assertions: the answer flags that Svelte's `Spring` clamps `stiffness` and
`damping` to 0–1; it supplies values on Svelte's scale; it does not silently
pass 100 and 10 through.

The user's numbers are plausible — they are Motion's documented defaults. Passed
to `new Spring()` they clamp to `1`/`1` and the spring snaps instantly.

## Case 4 — restraint

Prompt: _"What could we animate in our command palette?"_ Target:
`finding-animation-opportunities`.

Assertions: the open/close transition is rejected explicitly, naming
keyboard-initiated and 100+/day; the rejected-candidates section is present; the
suggestion count is at most seven; nothing is suggested purely because it would
look good.

An opportunity finder that suggests motion everywhere is worse than no skill at
all, so this case grades the rejections rather than the suggestions.

## Case 5 — routing under a vague ask

Prompt: _"This app doesn't feel very polished."_ Targets: acceptable are
`improving-animations`, `finding-animation-opportunities`, or
`design-engineering`.

Assertions: exactly one skill fires; the answer asks for or infers a scope
(which surfaces, which frequency tier) before producing findings; it does not
begin writing animation code.

## Case 6 — the boundary against `frontend`

Prompt: _"Set up a Bits UI popover with a custom anchor."_ Target: `bits-ui`,
not anything in this plugin.

Assertions: no skill from this plugin fires; if one does, its description has
grown past craft into component wiring.

## Recording results

Log the date, the Svelte version the app was on, and the quoted evidence for
every assertion that separated. The Svelte version matters — these cases assert
against defaults, and a default that changes upstream turns a passing case into
a wrong one without any edit here. The defaults in `references/` were verified
against `svelte@5.57.0`.
