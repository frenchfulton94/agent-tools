# Skill Skeletons

Contents:
- [Choosing a skeleton](#choosing-a-skeleton)
- [Technique skill](#technique-skill)
- [Workflow skill](#workflow-skill)
- [Reference skill](#reference-skill)
- [Inline vs. references decision](#inline-vs-references-decision)

## Choosing a skeleton

| The skill teaches... | Skeleton | Freedom level |
|---|---|---|
| A concrete method with a right way to do it (commit format, deploy steps) | Technique | Low — exact commands, one canonical path |
| A multi-step process with judgment calls and verification (code review, data cleaning) | Workflow | Medium — ordered stages, principles within stages |
| A body of lookup knowledge (API quirks, schema docs, style guide) | Reference | High — SKILL.md is a router into references/ |

## Technique skill

~60–120 lines. Everything inline; references rarely needed.

```markdown
---
name: writing-conventional-commits
description: Writes git commit messages following the Conventional Commits
  format with project-appropriate types and scopes. Use when the user asks for
  a commit message, asks to commit changes, or reviews commit history quality.
license: MIT
---

# Writing Conventional Commits

One-paragraph purpose: what this produces and why the project cares.

## Format

The exact recipe — a template with each field named, then one filled example:

    <type>(<scope>): <imperative summary ≤72 chars>

    <body: what and why, not how>

Example:
    fix(auth): reject expired refresh tokens

    Tokens past expiry were accepted when clock skew was negative.

## Rules

3–7 rules max, each with a one-clause why. Exact commands where fragile:
"Run exactly `git log --oneline -10` to match existing scope names."

## Verify

One check the agent performs before finishing (fits on 2–3 lines).
```

## Workflow skill

~120–200 lines. Stages inline; deep detail per stage in references/.

```markdown
---
name: reviewing-data-pipelines
description: <capability + Use-when triggers; no workflow steps>
license: MIT
---

# Reviewing Data Pipelines

Purpose paragraph. What "done" looks like.

## Before starting

Preconditions and inputs needed. Route away cases this skill shouldn't
handle ("For X, use Y instead").

## Stage 1: <name>

What to do, what to produce, when this stage is done.
Read `references/<topic>.md` if <specific condition>.

## Stage 2: <name>
...

## Verify

Checklist the agent runs against its own output before reporting done.

## Output contract

Exactly what the final response contains, in what order.
```

## Reference skill

SKILL.md ~50–100 lines acting as a router; the knowledge lives in references/.

```markdown
---
name: internal-api-conventions
description: <capability + Use-when triggers>
license: MIT
---

# Internal API Conventions

One paragraph: what's covered, what's not.

## Quick answers

The 5–10 facts needed most often, one line each (saves a reference load
for common cases).

## Where to look

- Read `references/auth.md` when the task touches tokens, sessions, or 401s.
- Read `references/pagination.md` when responses may exceed one page.
- Read `references/errors.md` when handling or producing error responses.

## Gotchas

Environment facts that defy reasonable assumptions, one line each.
```

## Inline vs. references decision

Keep in SKILL.md: the workflow itself, rules the agent needs on every use, gotchas, the output contract, short examples.

Move to references/: per-topic depth used only sometimes, long example galleries, API field tables, edge-case catalogs, anything you'd label "for details, see...".

Test: if a competent agent could do a typical run without opening the file, it belongs in references/. If most runs need it, it belongs inline. One authoritative home per fact — an inline one-line digest pointing at the reference is fine; equal-depth restatement is not.
