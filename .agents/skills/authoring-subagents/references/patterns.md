# Subagent patterns

Contents:
- [A reviewer](#a-reviewer)
- [A noise absorber](#a-noise-absorber)
- [A researcher with a private MCP server](#a-researcher-with-a-private-mcp-server)
- [Chaining](#chaining)
- [Built-in subagents](#built-in-subagents)
- [Subagents vs agent teams](#subagents-vs-agent-teams)
- [Resuming a subagent](#resuming-a-subagent)

## A reviewer

The most common shape: read-only tools, a description written for proactive delegation, and a body that specifies the output format because the caller sees only the final message.

```markdown
---
name: migration-reviewer
description: Reviews database migrations for destructive operations and missing rollbacks. Use proactively whenever a migration file is added or changed, and before any deploy that includes schema changes.
tools: Read, Grep, Glob
model: sonnet
color: yellow
---

You review database migrations before they ship.

For each migration in scope, check:
- Destructive operations (DROP, TRUNCATE, a column type narrowing) and whether
  the data they remove is recoverable.
- A corresponding down migration, and whether it actually reverses the up.
- Locking behavior on large tables — anything that rewrites a table in place.
- Data backfills mixed into a schema change, which cannot be rolled back cleanly.

Report findings most severe first. For each: the file and line, one sentence on
what breaks and under what conditions, and the concrete fix. If a migration is
sound, say so rather than manufacturing a finding.

Return only the findings list. Do not summarize the migrations you approved.
```

Read-only tools here are not just a safety measure — they keep the agent from "fixing" things mid-review and returning a diff nobody asked for.

## A noise absorber

The strongest case for a subagent: an operation whose output is enormous and whose answer is small.

```markdown
---
name: test-triage
description: Runs the test suite and reports only the failures with their error messages. Use when tests need running and the full output would flood the conversation.
tools: Bash, Read, Grep
model: haiku
---

Run the project's test suite. Determine the correct command from package.json,
Makefile, or the project's own configuration — do not guess.

Report only failing tests. For each: the test name, the file, the assertion or
error message, and the two or three most relevant lines of stack trace. Group
failures that share a root cause.

If everything passes, say so in one line and report the total count. Never paste
the full test output.
```

`model: haiku` is deliberate. Triage is mechanical, and the summary is what the parent pays for in context either way.

## A researcher with a private MCP server

Declaring an MCP server in frontmatter rather than `.mcp.json` keeps its tool descriptions out of the main conversation's context for the whole session.

```markdown
---
name: browser-verifier
description: Verifies a change in a real browser and reports what it observed. Use when a UI change needs checking against the running app rather than the source.
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
tools: Read, Grep, mcp__playwright
---

Navigate to the page under test, exercise the described interaction, and report
what you observed — not what the code implies should happen.

Report: the URL, the steps taken, the observed result, and any console errors.
Include a screenshot reference when the difference is visual.
```

Note that `mcpServers` and `tools` do different jobs here: the first makes the server available, the second grants its tools. Both are needed if `tools` is set at all.

## Chaining

Chaining happens in the calling conversation, not in the agent files. Each subagent returns to Claude, which decides what the next one needs to know.

```text
Use the migration-reviewer subagent on the pending migrations, then have the
implementer subagent fix whatever it flags as blocking.
```

Two costs worth naming before recommending a chain. Every hop is a cold start, so the second agent rediscovers context the first already had. And several agents returning detailed results consume as much of the main context as doing the work inline would have — the saving comes from summarization, not from delegation itself.

## Built-in subagents

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `Explore` | Inherits, capped at Opus on the Claude API | Read-only; Write and Edit denied | File discovery and code search |
| `Plan` | Inherits | Read-only | Codebase research for planning |
| `general-purpose` | Inherits | Everything available to subagents | Multi-step research and code modification |

Explore takes a thoroughness level — quick, medium, or very thorough. Explore and Plan are one-shot, return no agent ID, and cannot be resumed; use `general-purpose` or a custom agent when the work continues.

A user or project subagent named `Explore` overrides the built-in and keeps its own `model` field, which is the supported way to make exploration cheaper: define one with `model: haiku`.

To restrict them: `"deny": ["Agent(Explore)"]` in permissions, `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` to remove Explore and Plan specifically, or deny the `Agent` tool to block all delegation.

## Subagents vs agent teams

| | Subagents | Agent teams |
|---|---|---|
| Context | Own window; results return to the caller | Own window; fully independent |
| Communication | Report back to the caller only | Teammates message each other directly |
| Coordination | The main agent manages all work | A shared task list with self-coordination |
| Best for | Focused tasks where only the result matters | Work that needs discussion between tracks |
| Cost | Lower — results are summarized back | Higher — each teammate is a separate instance |

Team practices worth stating when recommending one: start with three to five teammates and five or six tasks each; partition files so teammates do not collide, because teams are **not** worktree-isolated; start with research and review work rather than parallel implementation.

Limits that matter when authoring for teams: there is no session resumption with in-process teammates (`/resume` and `/rewind` do not restore them), one team per session, no nested teams, and permissions are fixed at spawn with every teammate inheriting the lead's mode. A teammate cannot spawn a background subagent — asking for one, or using a definition with `background: true`, returns an error. Teammates do not inherit the lead's `/model` by default; that is a separate setting.

Definitions used as teammates also do not get `skills` preloading or `mcpServers`, so an agent that depends on either will behave differently on that path.

## Resuming a subagent

Claude resumes a subagent with the `SendMessage` tool, addressing it by ID or name. A completed subagent that receives one auto-resumes in the background with no new `Agent` invocation, which is cheaper than respawning and keeps its context.

Two refusals to know about. A subagent *you* stopped — through `x` in `/tasks`, or the SDK — does not auto-resume, and `SendMessage` returns a refusal until you type into its transcript (v2.1.191+). And since v2.1.199, `SendMessage` verifies that a name still refers to the same agent; if a newer agent took the name, the send is refused and the error names the agent the name now reaches.

No message from another agent counts as permission approval, and none can change a subagent's permission settings or configuration.
