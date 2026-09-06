---
name: authoring-subagents
description: Creates, audits, and debugs Claude Code subagents — agent markdown files with frontmatter, tool grants, model and permission settings, and descriptions that drive delegation. Use when the user wants a specialized agent for a recurring task, wants to review or improve an agent they already have, wants to move noisy work out of the main context, wants to restrict which tools an agent can touch, or has a subagent that is never delegated to, launches with no tools, returns thin results, or ignores fields set in its frontmatter. Also use when the user asks whether to use a subagent, a skill, or an agent team for a piece of work.
license: MIT
---

# Authoring Subagents

A subagent is a markdown file: YAML frontmatter that configures it, and a body that becomes its entire system prompt. It runs in its own context window and returns a summary to whoever called it.

Two things make subagents harder to author than they look. The body is not an instruction added to Claude's existing context — it is all the context there is. And the `tools` field does not mean what it says: several tools are removed no matter what, and the default background execution mode strips more, so the same definition can resolve to different tools depending on how it runs.

## Subagent, skill, or main context?

| The work is... | Use... |
|---|---|
| Self-contained, verbose, and only the conclusion matters | A subagent |
| A reusable procedure the main conversation should follow itself | A skill |
| Iterative, or shares heavy context with what came before | The main conversation |
| Several tracks that need to talk to each other while working | An agent team |

The costs are real in both directions. A subagent starts cold and has to rediscover context, which adds latency; several returning detailed results consume as much context as doing the work inline would have. Reach for one when the output is large and the answer is small.

## Where the file goes

| Location | Scope |
|---|---|
| `.claude/agents/` | The project — checked in, shared with the team |
| `~/.claude/agents/` | All of your projects |
| `<plugin>/agents/` | Wherever the plugin is enabled |

Project definitions win over user ones, and both win over a same-named plugin agent. Both `.claude/agents/` and `~/.claude/agents/` are scanned recursively, and subdirectories are organizational only — identity comes from the frontmatter `name`, never the filename or folder.

Plugin-shipped agents silently ignore `hooks`, `mcpServers`, and `permissionMode`. This is a security restriction, not a bug, and there is no warning: the fields are simply dropped. If an agent needs them, it belongs in `.claude/agents/` instead.

Edits are picked up within a few seconds without a restart, with one exception — the file watcher only covers directories that existed when the session started, so creating the *first* agent in a brand-new `agents/` directory needs a restart.

## Frontmatter essentials

```yaml
---
name: changelog-reviewer
description: Reviews changelog entries for clarity and completeness. Use proactively after changelog files are edited.
tools: Read, Grep, Glob
model: sonnet
---
```

Only `name` and `description` are required. `name` is lowercase letters and hyphens, unique across the tree, and is what hooks see as `agent_type`. `model` defaults to `inherit`; set `sonnet` or `haiku` deliberately when cost matters. Everything else is optional — read `references/frontmatter.md` when reaching past these four.

## The description drives delegation

Claude decides whether to delegate by reading the description, the user's request, and the current context. A description that explains what the agent *is* gets ignored; one that says when to hand work to it gets used.

```yaml
# Weak: describes the agent
description: A specialist that knows about our database migrations.

# Strong: states the trigger, and invites proactive use
description: Reviews database migrations for destructive operations and missing
  rollbacks. Use proactively whenever a migration file is added or changed, and
  before any deploy that includes schema changes.
```

Phrases like "use proactively" and "use immediately after X" measurably increase automatic delegation. Users can also invoke one explicitly by name, by `@`-mention (`@agent-<name>`, or `@agent-my-plugin:<name>` for a plugin agent), or session-wide with `claude --agent <name>` — which replaces the default system prompt entirely.

## Tool access is where it goes wrong

Four rules, in the order they apply:

1. Omitting both `tools` and `disallowedTools` inherits every tool available to subagents. Setting `tools` restricts to that list. Setting `disallowedTools` subtracts from the inherited set. Setting both applies `disallowedTools` first, then resolves `tools` against what remains.
2. Some tools are removed from every subagent regardless of what `tools` says — `AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `EndConversation`, `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `Workflow`, and `Agent` at the nesting depth limit.
3. Subagents run in the background by default since v2.1.198, and a background subagent keeps only a reduced built-in set — Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact — plus every MCP tool. Anything else is dropped even when listed. The same definition therefore resolves differently in foreground and background.
4. If nothing in `tools` resolves to a real tool, the agent usually refuses to launch and the error names the unresolved entries. A misspelling is the common cause.

In YAML frontmatter `tools` is a comma-separated string; in `--agents` JSON it is an array. Both fields accept `mcp__<server>` or `mcp__<server>__*` to grant or remove a whole server.

Read `references/tool-access.md` for the canonical tool names and the full resolution matrix.

## The body is the entire system prompt

A subagent receives its own body plus basic environment details — not Claude Code's system prompt, not the conversation so far, not the output style, not the main conversation's memory. CLAUDE.md and a git-status snapshot do load, except for the built-in Explore and Plan agents, which skip both with no way to change that.

Write the body as if to someone who has never seen the project or the conversation:

- State the role and what a finished result looks like.
- Name the concrete steps where order matters, and give principles where judgment is needed.
- Say what to return, and in what shape — the caller sees only the final message.
- Do not reference "the file we discussed" or anything else from a conversation the agent cannot see.

## Auditing an existing subagent

Symptom first, because each one has a distinct cause.

- [ ] **Never delegated to** — the description describes the agent rather than when to use it, or omits proactive phrasing; or a same-named definition at a higher-priority scope is shadowing it
- [ ] **Launches with no tools, or the wrong ones** — a misspelled entry, a tool never available to subagents, or the background filter dropping built-ins that are listed
- [ ] **Frontmatter appears ignored** — `hooks`, `mcpServers`, or `permissionMode` in a plugin agent; or a parent running `bypassPermissions`, `acceptEdits`, or auto mode, which override the child's `permissionMode`
- [ ] **Returns thin or confused results** — the body was written as a note to someone who already has context; check it stands alone
- [ ] **`memory` set but nothing persists** — auto memory is disabled at the session level, which makes the field inert
- [ ] **Costs more than expected** — `model` left to `inherit` where `haiku` or `sonnet` would do
- [ ] Description contains no sequenced workflow that the caller might follow instead of dispatching
- [ ] Deletion pass, last: instructions the agent would have got right anyway, and constraints that no longer match how it is used

## Verify

Run `bun scripts/validate_agent.ts <file> --strict` (add `--plugin` when the agent ships in a plugin) for the mechanical faults. Then dispatch it once on a real task and confirm two things: that it was delegated to without being named explicitly, if that was the intent, and that what came back was usable. An agent that runs but returns a shrug is a body problem, not a configuration problem.

## Output contract

- **Creating:** the complete agent file, plus one line on where it goes and how it will be invoked.
- **Auditing:** findings keyed to the symptom checklist first, then the diffs, each with a one-line why. If the agent is sound, say so and stop — do not invent findings.

`references/patterns.md` has worked examples, chaining, and the comparison with agent teams. Read it when starting from a similar agent, or when the user asks whether a team fits better.

## Related skills

- `authoring-skills` — for reusable procedures that run in the main context instead. This skill is self-contained without it.
- `authoring-plugins` — for shipping agents inside a distributable plugin. Self-contained without it.
- `improving-prompts` — for tightening an agent body once its configuration is right. Self-contained without it.
