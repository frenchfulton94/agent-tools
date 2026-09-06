# Evals for authoring-hooks

Test material for verifying this skill. Never loaded automatically; run these when auditing or improving the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not. Run as a descriptions-only routing test with distractor skills present.
- `cases.md` — 3 behavior test cases with PASS/FAIL assertions, for A/B runs (with skill vs. without) in clean-context agents. Grade with quoted evidence; no benefit of the doubt.
- `fixtures/broken-hooks.json` plus `guard.sh`, `context.sh`, and `rm-payload.json` — a hook configuration carrying the faults this skill exists to catch. Used by case 2 and as the negative test for `scripts/validate_hooks.ts`. Run the validator from the skill root so the fixture's relative handler paths resolve.
