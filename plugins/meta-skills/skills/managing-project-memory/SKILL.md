---
name: managing-project-memory
description: Audits, improves, and creates CLAUDE.md files and the rest of a repo's project memory — CLAUDE.local.md, AGENTS.md, .claude/rules — the instruction files coding agents load at session start. Use when the user asks to audit, fix, shrink, restructure, write, or init a CLAUDE.md, when memory files are bloated, stale, or ignored, when deciding whether guidance belongs in memory, a skill, a rules file, or a hook, when capturing what a session revealed so the next session has it, or when setting up a repo so agents behave consistently. Also use on symptoms alone — "the agent keeps forgetting our conventions", "it ignores our style guide", "I repeat the same setup every session".
license: MIT
---

# Managing Project Memory

Create and maintain the instruction files agents load at session start. The core tension: every line costs context on every turn of every session, and past ~200 lines adherence measurably drops — a bloated memory file causes the very "agent ignores our rules" symptom it was written to prevent. The job is choosing the few lines that earn permanent residence, and routing everything else to a better home.

## How memory actually works

Design against the mechanics, not folklore. Read `references/mechanics.md` when a decision depends on load order, import resolution, rules scoping, or compaction behavior.

- Memory files load **in full at session start** and their tokens are re-sent with every message. They arrive as instructions, not as enforced configuration — an agent can and will deviate under pressure. Anything that must happen every time belongs in a **hook**, not a memory line.
- The hierarchy **concatenates, never overrides**: managed policy → user (`~/.claude/CLAUDE.md`) → project (`./CLAUDE.md` or `./.claude/CLAUDE.md`) → local (`./CLAUDE.local.md`, gitignored). Contradictions between levels aren't resolved — the agent picks arbitrarily. Audits must read all levels together.
- Ancestor-directory files load at launch; **subdirectory files load lazily** when the agent reads files there — put area-specific guidance in that area's own file, not the root.
- `@path` imports (max 4 hops, skipped inside backticks/code blocks) **still load into context at launch** — they organize, they don't save tokens.
- `.claude/rules/*.md` files with `paths:` frontmatter load **only when matching files are touched** — this is the actual context-saving mechanism for path-specific guidance.
- After context compaction, the root memory file is re-injected, but path-scoped rules are lost until re-triggered — keep universally-critical rules in the root.
- HTML comments are stripped before the agent sees the file — free for maintainer notes.
- For cross-agent repos, keep one source of truth: put shared content in AGENTS.md and make CLAUDE.md `@AGENTS.md` plus Claude-specific lines (or symlink).

## What belongs

| Include | Exclude |
|---|---|
| Commands the agent can't guess (`make test-fast`, not `npm test` if that's standard) | Anything derivable by reading the code |
| Conventions that differ from language/framework defaults | Standard conventions the model already knows |
| Repo etiquette: branch naming, PR format, commit style | API documentation (link or route to a rules file) |
| Environment quirks: required env vars, known-broken tooling | Frequently-changing info (goes stale, then misleads) |
| Gotchas that defy reasonable assumption (soft deletes; same field named differently across services) | File-by-file codebase descriptions |
| How to verify changes: test, typecheck, build commands | Self-evident advice ("write clean code", "handle errors") |

The governing test, applied per line: **"Would removing this cause the agent to make a mistake?" If not, cut it.** And each surviving line must be concrete enough to act on: "Run `npm test` before committing", never "Test your changes"; "API handlers live in `src/api/handlers/`", never "Keep files organized".

## Routing table

Memory is one of five homes. Route before writing:

| Content | Home | Why |
|---|---|---|
| Facts needed in every session | Memory file | Always loaded, paid on every turn |
| Multi-step procedures, techniques | A skill | Loads only when triggered |
| Guidance tied to specific paths | `.claude/rules/` with `paths:` | Loads only with those files |
| Rules that must never be skipped | A hook | Enforced, not advisory |
| Personal or machine-specific settings | `CLAUDE.local.md` (gitignored) | Doesn't burden teammates' context |

## Creating from scratch

1. **Discover.** Use the environment's init/analysis command if available; otherwise survey the build system, CI config, README, and recent PRs yourself. Collect candidate facts: build/test/lint commands, nonstandard layout, conventions visible in code review comments.
2. **Prune hard.** Auto-generated drafts fail the governing test on most lines (they describe what's derivable). Apply the include/exclude table and per-line test; expect to cut most of the draft. Never ship generated output unedited.
3. **Structure.** Markdown headers grouping related bullets — `# Commands`, `# Architecture`, `# Gotchas`. Under 200 lines; under 60 is excellent for most repos. One statement per bullet.
4. **Route the residue.** Facts that failed the "every session" test but are real → skills, rules files, or hooks per the routing table. Note what you routed and where.

Starter templates by project type, each line pre-justified: `references/templates.md`.

## Auditing an existing file

Produce the report **before** editing anything — the user decides on evidence, not on a diff fait accompli.

1. **Discover all files:** every `CLAUDE.md` variant across hierarchy levels (user, project, local, subdirectories), `.claude/rules/`, `AGENTS.md`. If you can execute code, `bun scripts/audit_memory.ts <repo-root>` collects inventory, line counts, import graph, and mechanical red flags; otherwise gather the same by hand.
2. **Score** against the rubric in `references/rubric.md` — six weighted criteria totaling 100 points, plus pass/fail mechanics gates (no cross-level contradictions, local file gitignored, rules path-scoped, imports within depth).
3. **Report:** score with per-criterion evidence, red flags (stale paths, commands that would fail, template boilerplate, duplicated guidance), and the routing opportunities.
4. **Then propose diffs**, each with a one-line why tied to a criterion. Cuts are the usual bulk of the value: worked before/after examples are in `references/examples.md`.

## Capturing session learnings

The highest-value memory edits come from a session that just hit friction — a command you had to discover, a convention you kept re-explaining, a gotcha you tripped on. Fold those in deliberately rather than dumping raw notes:

1. Name the one specific fact that was missing and would have prevented the friction.
2. Apply the include test and route it: a durable fact → the memory file; a procedure → a skill; path-specific guidance → `.claude/rules`; a machine-local detail → CLAUDE.local.md.
3. Add it as one concrete line in the right home and show the diff — do not let a learnings pass silently re-bloat the file past its size target.

In Claude Code, a quick "remember that…" routes to auto memory while an explicit "add this to CLAUDE.md" edits the file; both persist across sessions, so pick the one whose scope matches the fact.

## Verify

- **Always:** cold-read the final file as a brand-new agent would — no repo knowledge, no conversation context. Every line must be actionable without asking a question. Check commands against the repo's actual config files (a documented command that fails teaches the agent to distrust the whole file).
- **If you can run clean-context agents:** give one the revised file plus a representative task touching a documented convention; check it uses the documented command/convention rather than guessing. An A/B against the old file on the same task is the strongest evidence a trim didn't lose anything load-bearing. (This skill ships its own test material in `evals/` — maintainers rerun it after edits.)

## Output contract

Deliver, in order: (1) the audit report or discovery summary (for a learnings pass, the specific fact being captured); (2) the new/updated file content, or diffs each with a why; (3) the routed-content list — what moved out to skills/rules/hooks and why; (4) the final line count against the 200-line target. For audits where the file is already lean and current, say so — do not invent cuts to justify the exercise.

## Related skills

- `authoring-skills` — for content routed out of memory into an Agent Skill. Self-contained without it.
- `improving-prompts` — for system prompts and agent instructions that aren't memory files. Self-contained without it.
