---
description: "Security review against the vendored OWASP Cheat Sheet Series"
argument-hint: "[--baseline] [path]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Skill", "Agent"]
---

# Security Audit

Arguments: "$ARGUMENTS"

Use the `reviewing-code-security` skill for this review. Resolve the scope from the arguments
before doing anything else:

| Arguments | Scope |
|---|---|
| empty | The diff between `HEAD` and the merge base with `main`. Follow `references/diff-review.md`. |
| `--baseline` | The whole repository. Dispatch the `security-auditor` agent, which writes a verified report to `docs/security-reviews/`. |
| a path | That file or directory. Follow `references/baseline.md` scoped to that subtree — inline for a handful of files, otherwise dispatch `security-auditor` scoped to the path. |
| `--baseline` and a path | That subtree. Dispatch `security-auditor` scoped to it; it writes a verified report to `docs/security-reviews/`. |

If the repository has no `main` branch, check for `master` or the upstream default before asking —
and ask rather than reviewing against a guess, since the wrong base hides real changes.

Report in the format from the skill's `references/findings.md`. Nothing precedes the report except
one sentence naming the scope and the number of files examined.
