# Subagent frontmatter reference

Contents:
- [Field table](#field-table)
- [model](#model)
- [permissionMode](#permissionmode)
- [skills](#skills)
- [mcpServers](#mcpservers)
- [memory](#memory)
- [hooks](#hooks)
- [background, isolation, effort](#background-isolation-effort)
- [Context isolation](#context-isolation)
- [Limits](#limits)

## Field table

Only `name` and `description` are required.

| Field | Notes |
|---|---|
| `name` | Lowercase letters and hyphens, unique across the tree. Hooks receive it as `agent_type`. The filename is irrelevant |
| `description` | When to delegate. Drives automatic invocation |
| `tools` | Comma-separated in YAML, an array in `--agents` JSON. Omitting it inherits everything available to subagents |
| `disallowedTools` | Subtracted from the inherited or specified list |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`. Defaults to `inherit` |
| `permissionMode` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, or `manual` (an alias for `default`, v2.1.200+). Ignored for plugin agents |
| `maxTurns` | Maximum agentic turns before the subagent stops |
| `skills` | Skills preloaded into context at startup, in full |
| `mcpServers` | MCP servers available to this subagent. Ignored for plugin agents |
| `hooks` | Lifecycle hooks scoped to this subagent. Ignored for plugin agents |
| `memory` | `user`, `project`, or `local`. Enables a persistent memory directory |
| `background` | `true` to always run as a background task. Unset lets Claude choose, and it chooses background by default since v2.1.198 |
| `effort` | `low`, `medium`, `high`, `xhigh`, `max`. Overrides session effort; available levels depend on the model |
| `isolation` | `worktree` runs the agent in a temporary git worktree |
| `color` | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. Display only |
| `initialPrompt` | Auto-submitted as the first user turn when the agent runs as the *main* session agent via `--agent`. Prepended to any user prompt |

Plugin-shipped agents support everything above except `hooks`, `mcpServers`, and `permissionMode`, which are dropped silently.

## model

Resolution order, highest first: the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable, the per-invocation model Claude passes, the frontmatter `model`, then the main conversation's model. Setting `CLAUDE_CODE_SUBAGENT_MODEL=inherit` is the same as leaving it unset (v2.1.196+).

Values are checked against the organization's `availableModels` allowlist; an excluded value is skipped and the agent runs on the inherited model instead. Subagents inherit the main conversation's extended-thinking configuration (v2.1.198+) — there is no per-subagent thinking setting.

## permissionMode

| Mode | Behavior |
|---|---|
| `default` | Standard permission checking with prompts |
| `acceptEdits` | Auto-accepts file edits and common filesystem commands inside the working directory |
| `auto` | A background classifier reviews commands and protected-directory writes |
| `dontAsk` | Auto-denies prompts; explicitly allowed tools still work |
| `bypassPermissions` | Skips permission prompts |
| `plan` | Read-only exploration |

The parent wins in three cases. A parent in `bypassPermissions` or `acceptEdits` takes precedence and cannot be overridden by the child. A parent in auto mode passes auto mode down and the child's `permissionMode` is ignored entirely. Launching a subagent does not itself prompt; its own tool calls are checked as it runs.

Under `bypassPermissions`, writes to `.git`, `.claude`, `.vscode`, `.idea`, and similar directories become possible. Explicit `ask` rules, organization-level connector tools, MCP tools flagged `requiresUserInteraction`, and root or home removals still prompt.

## skills

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

The full content of each listed skill is injected at startup, not just its description. This controls preloading, not access — without it the agent can still discover and invoke skills through the `Skill` tool. To block skills entirely, omit `Skill` from `tools` or add it to `disallowedTools`.

Skills marked `disable-model-invocation: true` cannot be preloaded; as of v2.1.215 that includes the bundled `/verify` and `/code-review` skills. A missing or disabled entry is skipped with a warning to the debug log.

## mcpServers

```yaml
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github
```

It is a list, and each entry is either an inline server definition keyed by server name or a bare string referencing an already-configured server. Inline definitions use the `.mcp.json` schema and support `stdio`, `http`, `sse`, and `ws`.

Inline servers connect when the subagent starts and disconnect when it finishes; string references share the parent session's connection. Defining a server here rather than in `.mcp.json` keeps its tool descriptions out of the main conversation's context, which is a genuine saving for large servers.

As of v2.1.153, `--strict-mcp-config`, `--bare`, managed MCP config, and the `allowedMcpServers` / `deniedMcpServers` policies all cover servers declared in subagent frontmatter. `--strict-mcp-config` does not filter servers passed inline through `--agents` or the SDK.

## memory

| Scope | Location |
|---|---|
| `user` | `~/.claude/agent-memory/<agent-name>/` |
| `project` | `.claude/agent-memory/<agent-name>/` |
| `local` | `.claude/agent-memory-local/<agent-name>/` |

`project` is the recommended default. When enabled, the system prompt gains read and write instructions for the memory directory and includes the first 200 lines or 25 KB of `MEMORY.md`, whichever comes first, with instructions to curate beyond that. `Read`, `Write`, and `Edit` are enabled automatically.

The trap: subagent memory is part of auto memory. If auto memory is off — through the `autoMemoryEnabled` setting or `CLAUDE_CODE_DISABLE_AUTO_MEMORY` — the field has no effect at all. No instructions, no tool access, no error.

Pair it with an instruction in the body, or the agent will read memory and never write it:

```markdown
Update your agent memory as you discover codepaths, patterns, library locations,
and key architectural decisions. Write concise notes about what you found and where.
```

## hooks

Frontmatter hooks run only while the agent is active and are cleaned up when it finishes. They fire both when the agent is spawned through the Agent tool and when it runs as the main session via `--agent`. A `Stop` hook declared here is automatically converted to `SubagentStop`. Session-wide hooks from settings files, managed policy, and plugins also fire inside subagents, where the input carries `agent_id` and `agent_type`.

Since v2.1.218, frontmatter hooks in a *project* subagent run only after workspace trust is accepted.

## background, isolation, effort

Subagents run in the background by default since v2.1.198; Claude runs one in the foreground when it needs the result before continuing. `Ctrl+B` backgrounds a running task, and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` disables background execution entirely. Under `CLAUDE_CODE_FORK_SUBAGENT=1` everything runs in the background and the `background` field has no effect.

Background matters for tool access — see `tool-access.md` for the reduced set.

`isolation: worktree` (v2.1.203+) runs the agent in a temporary git worktree, branched from your **default branch**, not the parent session's `HEAD`. The worktree is cleaned up automatically if the agent changes nothing. Commands that resolve to the main checkout fail; since v2.1.216 the check inspects the Bash command itself, so `git -C`, `--git-dir`, `GIT_DIR`, `GIT_WORK_TREE`, or a `cd` back into the main checkout all fail, as does a command too complex to analyze.

## Context isolation

A non-fork subagent's initial context contains exactly: its own system prompt plus environment details; the delegation prompt Claude wrote; every CLAUDE.md the main conversation loads; a git-status snapshot from the start of the parent session; the full content of any preloaded `skills`; and, when `SendMessage` is among its tools and other named agents exist, a roster of siblings (v2.1.206+).

It never receives conversation history, previously invoked skills, files already read, the output style, or the main conversation's auto memory. Its context window is sized by its own model, not the parent's.

Explore and Plan are the only subagents that omit CLAUDE.md and git status, and no frontmatter field changes that. A rule that must reach them has to be restated in the delegation prompt.

Working directory: the agent starts in the main conversation's cwd, and a `cd` does not persist between Bash calls or affect the parent. Transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` and are unaffected by main-conversation compaction.

## Limits

| Limit | Default | Environment variable |
|---|---|---|
| Nesting depth | 3 layers below the main conversation | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (v2.1.217+) |
| Per session | 200 | `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` (v2.1.212+) |
| Concurrent | 20 | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (v2.1.217+) |

Set the depth to `1` to turn nesting off. At the depth limit, `Agent` is withheld from every subagent except a fork, where the tool remains listed but errors. `/clear` resets the session count.

Specific agents can be blocked with a permission rule — `"deny": ["Agent(Explore)", "Agent(my-custom-agent)"]` — or from the CLI with `--disallowedTools "Agent(Explore)"`.
