# Behavior Test Cases

A/B cases used to build this skill, with the results measured at authoring time.
Rerun after any edit to SKILL.md and check for regressions against the recorded
baseline.

Grading is mechanical where possible: `scripts/check_tailwind_v4.py` supplies the
BROKEN/SILENT/CHECK counts, so most assertions do not depend on judgment.

## Case 1 — component authoring

Prompt: _"Build a pricing card in Tailwind with dark mode, a focus ring, and a
gradient header."_

Assertions: gradient uses `bg-linear-*`; no `*-opacity-*`; `shrink-*` not
`flex-shrink-*`; every border/divide carries an explicit color; focus style uses
`outline-*` or `ring-<n>` with a color rather than bare `ring`; no bare `rounded`
or `shadow`; important modifier trailing; checker reports zero BROKEN and zero
SILENT.

Measured: baseline 14 findings in ~30 lines — `bg-gradient-to-r`, `bg-opacity-75`,
`flex-shrink-0` ×2, `@tailwind` ×3, bare `shadow`, bare `rounded`, `shadow-sm`,
`rounded-sm`, `focus:outline-none`, `focus:ring`, leading `!`. Skill-guided run:
0 findings, 7 of 8 assertions separating.

## Case 2 — project setup

Prompt: _"Set up Tailwind with a custom brand color and a class-based dark mode
toggle."_

Assertions: entry CSS uses `@import "tailwindcss"`; brand color lives in `@theme`
under `--color-*`; no `tailwind.config.js` as the primary mechanism;
`@custom-variant dark (...)` rather than `darkMode: 'class'`; a `@tailwindcss/*`
build package; no `autoprefixer`; checker clean.

Measured: baseline failed all 7 — it produced `npx tailwindcss init -p`, a JS
config with `darkMode: 'class'`, and the three `@tailwind` directives.
Skill-guided run passed all 7.

## Case 3 (edge) — v3-pinned project

Fixture: `package.json` pinning `"tailwindcss": "^3.4.1"`. Prompt: _"Add a shadow
and rounded corners to this card."_

This case exists to catch over-application. The failure mode to watch for is a
skill-guided run "correcting" `shadow` to `shadow-sm`, or migrating the project
to `@theme` unprompted — both would be wrong here.

Assertions: output uses v3-valid syntax; the response states which major version
it targeted; no unprompted migration.

Measured: no regression. Both conditions produced correct v3 markup and neither
migrated anything; the skill-guided run additionally named the version. Two of
the three assertions pass in both conditions and are kept as regression guards
rather than as evidence of value.

## Interpretation notes

Assertion 1.4 ("border/divide has an explicit color") initially read FAIL in both
conditions. Inspection showed both outputs were correct and the grading regex was
at fault; it was replaced with the checker's CHECK-severity count. An assertion
failing in both conditions usually indicts the test, not the skill.
