# Subagent tool access reference

Contents:
- [Resolution matrix](#resolution-matrix)
- [Filter 1: never available to subagents](#filter-1-never-available-to-subagents)
- [Filter 2: background subagents](#filter-2-background-subagents)
- [Canonical tool names](#canonical-tool-names)
- [MCP patterns](#mcp-patterns)
- [Agent(agent_type) syntax](#agentagent_type-syntax)
- [Permission rule specifiers](#permission-rule-specifiers)

## Resolution matrix

| Fields set | Result |
|---|---|
| Neither | Inherits every tool available to subagents |
| `tools` only | Only the listed tools |
| `disallowedTools` only | Every parent tool except the listed ones |
| Both | `disallowedTools` applies first; `tools` then resolves against what remains. A tool in both is removed |

Then the two filters below apply on top, which is why a `tools` list is a ceiling rather than a guarantee.

If nothing in `tools` resolves to a real tool, the subagent usually refuses to launch and the Agent tool errors naming the unresolved entries. Before v2.1.208 it launched with no tools at all and returned empty results, which is worth knowing when debugging an older setup.

Syntax differs by source: a comma-separated string in YAML frontmatter (`tools: Read, Grep, Glob, Bash`), a JSON array in `--agents` (`"tools": ["Read","Grep"]`).

## Filter 1: never available to subagents

Removed from every subagent even when explicitly listed:

`AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `Workflow`, and `Agent` when the nesting depth limit has been reached (in a fork the tool stays listed but errors instead of spawning).

## Filter 2: background subagents

Subagents run in the background by default since v2.1.198. A background subagent keeps every MCP tool but only these built-ins:

```text
Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch,
WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree,
Monitor, TaskStop, SendMessage, Artifact
```

Every other built-in is removed, inherited or listed. The consequence to internalize: **the same definition resolves to different tools in the foreground and the background.** An agent that needs `LSP`, `SendUserFile`, `ReportFindings`, or `PushNotification` will silently lack them when Claude decides to background it.

Agent-team teammates additionally keep `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `CronCreate`, `CronDelete`, and `CronList`.

Forks skip both filters and receive the main conversation's exact tool pool.

## Canonical tool names

The exact strings accepted in `tools`, `disallowedTools`, permission rules, and hook matchers. The second column marks tools that prompt for permission in default mode for paths inside the working directory.

| Tool | Prompts |
|---|---|
| `Agent` | No |
| `Artifact` | Yes |
| `AskUserQuestion` | No |
| `Bash` | Yes |
| `CronCreate` / `CronDelete` / `CronList` | No |
| `Edit` | Yes |
| `EndConversation` | No |
| `EnterPlanMode` | No |
| `EnterWorktree` | Yes |
| `ExitPlanMode` | Yes |
| `ExitWorktree` | No |
| `Glob` | No |
| `Grep` | No |
| `ListMcpResourcesTool` | No |
| `LSP` | No |
| `Monitor` | Yes |
| `NotebookEdit` | Yes |
| `PowerShell` | Yes |
| `PushNotification` | No |
| `Read` | No |
| `ReadMcpResourceTool` | No |
| `RemoteTrigger` | No |
| `ReportFindings` | No |
| `ScheduleWakeup` | No |
| `SendMessage` | No |
| `SendUserFile` | No |
| `ShareOnboardingGuide` | Yes |
| `Skill` | Yes |
| `TaskCreate` / `TaskGet` / `TaskList` / `TaskStop` / `TaskUpdate` | No |
| `TaskOutput` | No |
| `TodoWrite` | No |
| `ToolSearch` | No |
| `WaitForMcpServers` | No |
| `WebFetch` | Yes |
| `WebSearch` | Yes |
| `Workflow` | Yes |
| `Write` | Yes |

Caveats: `Read`, `Grep`, and `Glob` are marked as not prompting but still prompt for paths outside the working directory and additional directories. `Bash` prompts, but a built-in set of read-only commands runs without one. `TodoWrite` is disabled by default as of v2.1.142 in favor of `TaskCreate` / `TaskList` / `TaskUpdate`. `TaskOutput` is deprecated in favor of `Read` on the task's output file path.

To preload skills use the `skills` frontmatter field, not an entry for `Skill` in `tools` — `Skill` grants access, `skills` injects content.

## MCP patterns

`mcp__<server>` or `mcp__<server>__*` grants or removes every tool from that server. In `disallowedTools`, `mcp__*` removes every MCP tool from every server.

```yaml
---
name: local-only
description: Inherits every tool except those from the github MCP server. Use for work that must not reach external services.
disallowedTools: mcp__github
---
```

## Agent(agent_type) syntax

```yaml
tools: Agent(worker, researcher), Read, Bash
```

The parenthesized allowlist applies only to an agent running as the main thread through `claude --agent`. Inside a subagent definition, listing `Agent` lets it spawn subagents subject to the depth limit, and the type list in parentheses is ignored.

`tools: Agent, Read, Bash` allows spawning any subagent. Omitting `Agent` entirely means it can spawn none. The `Task` tool was renamed `Agent` in v2.1.63, and `Task(...)` still works as an alias.

## Permission rule specifiers

Relevant when pairing an agent with deny rules rather than a `tools` list.

| Rule | Applies to | Matching |
|---|---|---|
| `Bash(npm run *)` | Bash, Monitor | Command pattern |
| `PowerShell(Get-ChildItem *)` | PowerShell | Command pattern |
| `Read(~/secrets/**)` | Read, Grep, Glob, LSP | Path pattern |
| `Edit(/src/**)` | Edit, Write, NotebookEdit | Path pattern |
| `Skill(deploy *)` | Skill | Skill name |
| `Agent(Explore)` | Agent | Subagent type |
| `WebFetch(domain:example.com)` | WebFetch | Domain |
| `WebSearch` | WebSearch | No specifier |
