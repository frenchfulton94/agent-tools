# Evals for managing-project-memory

Test material for verifying this skill. Never loaded automatically; run these when auditing or improving the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not. Run as a descriptions-only routing test with distractor skills present.
- `cases.md` — 3 behavior test cases with PASS/FAIL assertions for A/B runs (with skill vs. without) in clean-context agents. Grade with quoted evidence; no benefit of the doubt.
- `fixtures/bloated-repo/` — fixture for case 1: a repo with an oversized, stale CLAUDE.md.
- `fixtures/fresh-repo/` — fixture for case 2: a small repo with a nonstandard test command in its Makefile and no CLAUDE.md yet.
