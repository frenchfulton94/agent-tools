# Evals for using-crossover-mac

Test material for verifying this skill. Never loaded automatically; run these when auditing or improving the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not. Run as a descriptions-only routing test: give a clean-context agent the skill descriptions (this one plus distractors, ideally a generic macOS skill and a virtualization skill), one query at a time, and ask which applies or "none".
- `cases.md` — 5 behavior cases with PASS/FAIL assertions, for A/B runs (with the skill vs. without) in clean-context agents. Grade with quoted evidence; no benefit of the doubt.

The assertions in `cases.md` target the failures this skill exists to prevent: describing Advanced Settings that do not exist in the user's CrossOver version, removing one application from a bottle (the KB says it is impossible), deleting a bottle without archiving it, inventing configuration keys the KB never documents, and offering anti-cheat workarounds.
