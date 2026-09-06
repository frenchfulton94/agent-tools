# Behavior test cases: authoring-skills

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Create a skill (must-pass set)

**Prompt:** "Make me a skill that writes conventional commit messages for our repo. We use types feat/fix/chore/docs, scopes are the top-level package names, and the summary line has to stay under 72 characters."

**Assertions:**
1. Output includes a complete SKILL.md with YAML frontmatter containing `name` and `description`.
2. The `name` is lowercase-hyphenated, ≤64 chars, contains no reserved words, and would match its directory.
3. The description states capability in third person and contains a "Use when..." trigger clause.
4. The description contains no sequenced workflow steps (no "first/then", no numbered steps).
5. The body is under 200 lines and contains the exact commit template with a filled example.
6. The response includes some form of verification guidance (how to check the skill works), not just the skill text.
7. The description does not embed the rule content itself (the type list, the length limit) and does not tell the agent to "always consult this skill" — triggering conditions only. (Baselines reliably fail this: they compress the rules into the description, the fires-but-gets-skipped trap.)
8. The skill is grounded in an observed or reproduced failure (a baseline run, or an explicit reproduction of what goes wrong without it), not authored purely from imagination.
9. Mechanical validation was actually performed before delivery (validator script run, or the manual spec checklist applied item by item) — not merely suggested as a next step.

## Case 2 — Fix a non-triggering skill

**Prompt:** "This skill exists but Claude never uses it. Fix it.

```yaml
---
name: report-generator
description: This skill first gathers the quarterly metrics, then formats them into our standard template, then writes an executive summary at the top.
---
```
(body teaches a 5-step reporting workflow)"

**Assertions:**
1. Identifies that the description describes workflow instead of triggering conditions (names or clearly explains the failure).
2. Rewritten description adds user-intent triggers ("Use when...") and removes all sequenced steps.
3. Proposes testing the fix (trigger queries or equivalent), not just the rewrite.
4. Does not add emphasis inflation (no ALL-CAPS, no MUST walls) to force triggering.

## Case 3 — Edge: wrong tool for the job

**Prompt:** "Create a skill that forces Claude to always run the test suite before every commit, no exceptions."

**Assertions:**
1. Response recommends a hook (or equivalent enforced mechanism) rather than delivering only a skill, and explains that skills/memory are advisory while hooks are enforced.
2. If a skill or memory line is offered at all, it is framed as a supplement, not as the enforcement mechanism.
3. Response stays proportionate (does not scaffold a full skill package for content it just advised against).
