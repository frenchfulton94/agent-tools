# Evals for mapping-project-tooling

Test material for verifying this skill. Never loaded automatically; run these when
auditing or changing the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not, with notes on which are load-bearing.
- `cases.md` — 5 behavior cases with PASS/FAIL assertions for A/B runs in clean-context agents. Cases 1 and 2 are the must-pass pair: case 1 grades the generated file, case 2 grades what a later agent does with it.

Cases 2 and 5 are the ones that can regress silently. Both run **without** the skill
loaded, so they measure whether the artifact spec still works when nothing is around to
explain it.
Rerun both after any edit to `assets/TOOLS.template.md` or to the pointer snippet in
Stage 4 — the pointer's trigger scope is what decides whether the file is opened at all,
and case 5 is the only test that catches a trigger too narrow to reach the capability
section.
