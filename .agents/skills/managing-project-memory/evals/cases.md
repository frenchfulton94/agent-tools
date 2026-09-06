# Behavior test cases: managing-project-memory

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Audit a bloated file (must-pass set)

**Prompt:** "Audit the CLAUDE.md in this repo and fix it. The agent has been ignoring half of what's in there." (Working directory: `fixtures/bloated-repo/`.)

**Assertions:**
1. A structured audit report (scores or findings per criterion) is produced **before** any rewritten content or diffs.
2. The report identifies the stale reference (`scripts/deploy_v1.sh` does not exist) as a currency problem.
3. Derivable content (the framework tutorial section and the file-by-file directory listing) is cut, with reasoning tied to "would removing this cause a mistake" or equivalent.
4. The multi-step release procedure (~19 lines) is routed out (to a skill or equivalent on-demand home), not merely deleted and not left inline.
5. The nonstandard command facts (`make test-unit`, the port-6543 gotcha) survive the cut.
6. The final file is substantially leaner than the original (at most roughly half the word count) and the response states the final size against the 200-line target.

## Case 2 — Create from scratch

**Prompt:** "Set up a CLAUDE.md for this repo." (Working directory: `fixtures/fresh-repo/`.)

**Assertions:**
1. The generated file documents `make check` (the repo's actual, nonstandard test-and-lint entry point found in the Makefile) rather than a guessed `npm test`/`pytest`.
2. The file contains no generic filler ("write clean code", "follow best practices", framework tutorials).
3. The file is ≤60 lines.
4. The response shows evidence of discovery (mentions the Makefile or the files it derived facts from).

## Case 3 — Edge: enforcement request

**Prompt:** "Add a rule to our CLAUDE.md so the agent always runs the linter before committing, without exception."

**Assertions:**
1. The response explains that memory files are advisory and recommends a hook (or equivalent enforced mechanism) for the "without exception" requirement.
2. Any memory line offered is framed as a supplement to the hook, not as the guarantee.
3. The memory line, if offered, is stated once, plainly, without emphasis inflation (no ALWAYS/MUST caps).
