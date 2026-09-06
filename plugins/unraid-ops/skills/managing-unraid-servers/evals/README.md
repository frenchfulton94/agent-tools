# Evals for managing-unraid-servers

Test material for verifying this skill. Never loaded automatically; run these when auditing or improving the skill itself.

- `triggers.md` — 10 queries that should trigger this skill and 10 near-misses that should not. Run as a descriptions-only routing test: give a clean-context agent the skill descriptions (this one plus distractors, ideally including a generic Linux/storage skill), one query at a time, and ask which applies or "none".
- `cases.md` — 5 behavior test cases with PASS/FAIL assertions, for A/B runs (with skill vs. without) in clean-context agents. Grade with quoted evidence; no benefit of the doubt.

The assertions in `cases.md` were written to fail on a baseline run. Case 1 in particular reproduces the failure this skill was built around: an unaided model, told a disk is unmountable, recommends the Format button the WebGUI itself offers — which erases the data and updates parity, removing any chance of reconstruction.
