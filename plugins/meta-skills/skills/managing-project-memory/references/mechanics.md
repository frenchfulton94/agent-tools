# Project Memory Mechanics

How memory files actually load, in Claude Code specifically (other agent products differ in paths but rarely in principles). Design decisions should trace to one of these facts.

Contents:
- [Load model](#load-model)
- [File hierarchy](#file-hierarchy)
- [Directory-tree behavior](#directory-tree-behavior)
- [Imports](#imports)
- [Rules directories and path scoping](#rules-directories-and-path-scoping)
- [Compaction behavior](#compaction-behavior)
- [Cost model](#cost-model)
- [Interop: AGENTS.md and other agents](#interop-agentsmd-and-other-agents)
- [Advisory vs. enforced](#advisory-vs-enforced)
- [Maintenance affordances](#maintenance-affordances)

## Load model

- All applicable memory files load **in full at session launch**, before the first user message.
- Content is delivered as conversation-level instructions, **not** inside the system prompt — which is why compliance is good but not guaranteed, and why shorter files get better adherence than longer ones.
- Official guidance: target **under 200 lines** per file; adherence drops as length grows ("bloated files cause the agent to ignore your actual instructions").

## File hierarchy

Load order (earlier = broader; all are concatenated, none override):

| Scope | Path | Notes |
|---|---|---|
| Managed policy | OS-level managed settings dir | Organization-wide; cannot be excluded locally |
| User | `~/.claude/CLAUDE.md` | Personal, applies to all projects |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared, checked into git |
| Local | `./CLAUDE.local.md` | Personal per-repo; add to `.gitignore` |

Because levels concatenate, a contradiction between user-level and project-level rules is not resolved by precedence — the agent sees both and picks unpredictably. Audit across levels, not per file.

## Directory-tree behavior

- Walking **up** from the working directory: every `CLAUDE.md`/`CLAUDE.local.md` in ancestor directories loads at launch (root first, nearest last).
- Walking **down**: a subdirectory's memory file loads **lazily**, only when the agent reads a file in that subtree. Sibling branches never load.
- Monorepo implication: repo-wide facts in the root file; package-specific facts in each package's own file, where they cost nothing until that package is touched.

## Imports

- `@path/to/file` imports another file; relative paths resolve against the importing file; `@~/...` works for home paths.
- Maximum import depth: **4 hops**. Cycles and over-depth are failure modes to check in audits.
- Imports inside backticks or fenced code blocks are **not** processed — write `` `@README` `` to mention a path literally.
- Imported content **still loads at launch and still costs context**. Imports are for organization and sharing (e.g., a common file imported by several packages), not for saving tokens. The only true lazy mechanisms are subdirectory files and path-scoped rules.
- Project-level imports resolving outside the repo may require one-time user approval — prefer keeping project imports inside the repo.

## Rules directories and path scoping

- `.claude/rules/*.md`: topic-scoped rule files, discovered recursively.
- Without `paths:` frontmatter, a rules file loads at launch like memory — moving content there changes organization, not cost.
- With `paths:` frontmatter it loads **only when the agent touches matching files** — the primary tool for cutting always-loaded context:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
API handlers must validate input with zod before touching the DB.
```

- Route to a path-scoped rule anything that begins "when working in <area>...".

## Compaction behavior

When the context window compacts mid-session:

- The project-root memory file and unscoped rules are **re-injected from disk** — they survive.
- Path-scoped rules and lazily-loaded subdirectory files are **lost until re-triggered** by touching matching files again.
- Implication: a rule that is genuinely universal must live in the root file, not a path-scoped rule, or it will silently vanish in long sessions.

## Cost model

- The conversation — including all loaded memory — is re-sent with **every message**; prompt caching softens but doesn't eliminate the cost.
- A 400-line CLAUDE.md is paid for on every turn of every session by every teammate, whether or not its content is relevant to the task at hand. This is the economic argument for the routing table: skills and path-scoped rules make rarely-needed content free until needed.
- Instruction budget matters as much as tokens: models follow a limited number of instructions with high consistency, and the product's own system prompt already consumes a sizable share. Count instructions, not just lines, when auditing.

## Interop: AGENTS.md and other agents

- Claude Code reads `CLAUDE.md`, not `AGENTS.md`. Other agent tools read `AGENTS.md` and not `CLAUDE.md`.
- To keep one source of truth in a multi-agent repo: put shared content in `AGENTS.md`; make `CLAUDE.md` contain `@AGENTS.md` plus any Claude-specific additions. A symlink (`ln -s AGENTS.md CLAUDE.md`) works when there are no Claude-specific lines.
- Init tooling can also ingest legacy rule formats from other tools (Cursor rules, Copilot instructions) — fold them into the single source rather than maintaining parallel rule files.

## Advisory vs. enforced

Memory content is advice the agent weighs, not configuration the platform enforces. Under time pressure, conflicting instructions, or long contexts, an agent can skip a memory rule. The enforcement ladder:

1. **Memory line** — right for conventions and context; wrong for guarantees.
2. **Skill** — right for procedures; still advisory.
3. **Hook** (e.g., a pre-tool-use check) — executes regardless of what the agent decides. Right for "must never happen" (blocking pushes to main, forbidding edits to generated files, mandatory test runs).

When a user asks for "make the agent always/never X", deliver the hook recommendation first and the memory line as a supplement.

## Maintenance affordances

- Block HTML comments (`<!-- -->`) are stripped before injection — free for changelog notes, review dates, and per-line justifications that humans need and agents shouldn't see.
- Quick capture in Claude Code: pressing `#` (or saying "remember that…") folds a learning into memory without leaving the session, and `/memory` opens the files to edit. Route by scope — an explicit "add this to CLAUDE.md" edits the shared file; a bare "remember" goes to auto memory. Use these to capture learnings the moment they surface, then prune in a later pass so quick-capture doesn't re-bloat the file.
- Treat the file like code: review it when the agent misbehaves, prune on a schedule, and test edits by watching whether behavior actually shifts.
- Diagnostic heuristics: the agent repeatedly violates a written rule → the file is too long or the rule is buried; the agent asks questions the file answers → the phrasing is ambiguous; the agent follows a documented command that fails → currency rot, fix immediately (one broken command discredits the whole file).
