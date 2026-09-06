# Evals for maintaining-plugin-marketplaces

Test material for verifying this skill. Never loaded automatically; run these when auditing or improving the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not. The negatives that matter belong to `authoring-skills` and `authoring-plugins`, whose subject matter is one layer down from this one.
- `cases.md` — 3 behavior test cases with PASS/FAIL assertions, for A/B runs (with skill vs. without) in clean-context agents. Grade with quoted evidence; no benefit of the doubt.

These are hand-written rather than measured. The marketplace's own `battery.ts` harness is the stronger instrument, but it is built around a single target and costs roughly 60 paid model calls per run; the confusions this description has to survive are separable by cold reading.
