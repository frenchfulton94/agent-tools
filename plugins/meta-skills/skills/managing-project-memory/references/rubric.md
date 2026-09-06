# Audit Rubric

Score the project's memory files (all hierarchy levels together) against six criteria totaling 100 points, then apply the pass/fail mechanics gates. Present the full report before proposing any edit.

Contents:
- [Scoring criteria](#scoring-criteria)
- [Mechanics gates (pass/fail)](#mechanics-gates-passfail)
- [Red flags](#red-flags)
- [Report template](#report-template)

## Scoring criteria

**Commands and workflows — 20 points.**
Full marks: the build, test, lint, and run commands an agent needs are present, exact, and copy-pasteable, including nonstandard variants (`make test-fast`, required env vars). Half: commands present but generic or incomplete ("run the tests"). Zero: absent, or documented commands that would fail if run — verify against the repo's actual package.json/Makefile/CI config; a failing documented command scores zero for this criterion regardless of the rest.

**Architecture clarity — 20 points.**
Full: the 3–8 facts about structure an agent can't cheaply infer — where handlers/entry points live, how packages relate, what's generated vs. hand-written. Half: partial, or accurate but drowned in derivable detail. Zero: absent, or a file-by-file tour that substitutes for insight.

**Non-obvious patterns and gotchas — 15 points.**
Full: the environment facts that defy reasonable assumption (soft-delete filters, cross-service naming mismatches, known-broken tooling) captured one line each. Half: some present, mixed with restatements of standard practice. Zero: none, or only generic advice.

**Conciseness — 15 points.**
Full: ≤200 lines per file, one statement per bullet, no line that fails the governing test ("would removing this cause a mistake?"). Deduct proportionally for length beyond 200 lines, multi-clause bullets, filler ("write clean code"), and duplication within or across files.

**Currency — 15 points.**
Full: every referenced path exists, every command runs, no references to removed tools/files/processes. Deduct per stale item; more than two stale items caps this criterion at half, because staleness anywhere breeds distrust everywhere.

**Actionability — 15 points.**
Full: every line concrete enough to act on without a follow-up question ("Run `npm test` before committing", "handlers live in `src/api/handlers/`"). Deduct per vague line ("test your changes", "keep files organized", "be careful with the database").

Grade bands: A ≥90, B 80–89, C 70–79, D 60–69, F <60.

## Mechanics gates (pass/fail)

Independent of the score; any failure is a finding to fix:

- [ ] No contradictions across hierarchy levels (user vs. project vs. local) — levels concatenate, so contradictions are coin flips
- [ ] `CLAUDE.local.md`, if present, is in `.gitignore`
- [ ] Rules files intended as path-specific actually have `paths:` frontmatter (otherwise they're always-loaded memory in disguise)
- [ ] Import graph resolves: no missing targets, no cycles, depth ≤4
- [ ] No import used where lazy loading was intended (imports still load at launch)
- [ ] Universal rules live in the root file, not only in path-scoped rules (which don't survive compaction)
- [ ] Multi-agent repos: single source of truth (AGENTS.md bridge), not divergent parallel files

## Red flags

Immediate findings regardless of score:

- Template boilerplate left uncustomized (placeholder project names, generic section stubs)
- Multi-step procedures inline (route to a skill)
- "When working in <area>..." content in the root (route to a path-scoped rule)
- "Always/never" rules where the user's real requirement is enforcement (route to a hook)
- API documentation pasted in (link it or route it)
- Duplicate guidance across levels or files (one home per fact)
- Emphasis inflation (all-caps runs, repeated MUST) substituting for clarity
- Absent essentials: a required env var, a setup step, or the test/build command a newcomer needs is missing entirely (currency's mirror — audit for what should be there and isn't, not only for what's stale)

## Report template

```markdown
# Memory audit: <repo>

Files found: <list with line counts and hierarchy level>
Total always-loaded lines: <n> (target ≤200 per file)

| Criterion | Score | Evidence |
|---|---|---|
| Commands & workflows | x/20 | <quote or gap> |
| Architecture clarity | x/20 | ... |
| Non-obvious patterns | x/15 | ... |
| Conciseness | x/15 | ... |
| Currency | x/15 | ... |
| Actionability | x/15 | ... |
| **Total** | **x/100 (grade)** | |

Mechanics gates: <pass list / failures>
Red flags: <list>
Routing opportunities: <content → skill/rule/hook, one line each>

Proposed changes: <numbered diffs, each with a one-line why tied to a criterion>
```
