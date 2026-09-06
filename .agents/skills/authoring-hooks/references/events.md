# Hook event catalog

Contents:
- [Common input fields](#common-input-fields)
- [Blocking summary](#blocking-summary)
- [Session lifecycle](#session-lifecycle)
- [Prompt events](#prompt-events)
- [Tool events](#tool-events)
- [Turn and agent events](#turn-and-agent-events)
- [Task and teammate events](#task-and-teammate-events)
- [Environment events](#environment-events)
- [Compaction and elicitation](#compaction-and-elicitation)

## Common input fields

Every event receives some subset of: `session_id`, `prompt_id` (v2.1.196+, absent until the first user input), `transcript_path`, `cwd`, `permission_mode`, `effort`, `hook_event_name`, and — inside a subagent — `agent_id` and `agent_type`.

`transcript_path` is written asynchronously and may lag the current turn. On `Stop` and `SubagentStop`, read `last_assistant_message` instead of parsing the transcript.

`permission_mode` is one of `default`, `plan`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`. The mode labeled *Manual* in the UI arrives as `default`, never `manual`. Not every event carries the field.

Only `SessionStart` can receive `model`, and not reliably. There is no `$CLAUDE_MODEL` environment variable.

Field names that differ from the obvious guess: `UserPromptSubmit` uses `prompt`, `Setup` uses `trigger`, `FileChanged` uses `event`, `PostToolBatch` uses `tool_calls`, and `PostToolUse` uses `tool_response`.

## Blocking summary

| Event | Exit 2 does |
|---|---|
| `PreToolUse` | Blocks the tool call |
| `PermissionRequest` | Denies the permission |
| `UserPromptSubmit` | Blocks processing and erases the prompt |
| `UserPromptExpansion` | Blocks the expansion |
| `Stop` | Prevents stopping; the conversation continues |
| `SubagentStop` | Prevents the subagent stopping |
| `TeammateIdle` | Keeps the teammate working |
| `TaskCreated` | Rolls back task creation |
| `TaskCompleted` | Prevents completion |
| `ConfigChange` | Blocks the change, except for `policy_settings` |
| `PostToolBatch` | Stops the agentic loop before the next model call |
| `PreCompact` | Blocks compaction |
| `Elicitation` | Denies the elicitation |
| `ElicitationResult` | Blocks the response; the action becomes decline |
| `WorktreeCreate` | **Any** non-zero exit fails creation |
| `PostToolUse`, `PostToolUseFailure` | Nothing — stderr is shown to Claude; the tool already ran |
| `PermissionDenied` | Nothing — use `hookSpecificOutput.retry: true` |
| `SessionStart`, `Setup`, `SubagentStart` | Nothing — stderr renders as a hook-error notice the user sees and Claude does not |
| `Notification`, `SessionEnd`, `CwdChanged`, `FileChanged`, `PostCompact`, `WorktreeRemove`, `InstructionsLoaded`, `StopFailure`, `MessageDisplay` | Nothing |

Since v2.1.214, a hook that exits 2 while printing JSON that fails schema validation still blocks, using stderr as the reason.

## Session lifecycle

**`SessionStart`** — matchers `startup`, `resume`, `clear`, `compact`, `fork` (`fork` added v2.1.214; earlier versions reported `resume`). Input carries `source`, optionally `model` and `session_title`. Plain stdout already reaches Claude for this event. Output fields: `additionalContext`, `initialUserMessage`, `sessionTitle` (applied on `startup`/`resume`/`fork`, ignored on `clear` and `compact`), `watchPaths` (absolute paths that will drive `FileChanged`), `reloadSkills`. Handler types: `command` and `mcp_tool` only.

**`Setup`** — matchers `init`, `maintenance`. Fires only with `--init-only`, or `--init` / `--maintenance` in `-p` mode. Input field is `trigger`. Plain stdout goes to the debug log only, so context must be returned as JSON. Handler types: `command` and `mcp_tool` only.

**`SessionEnd`** — matchers `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`. Default timeout is **1.5 seconds**, not 600. The overall budget rises to the highest per-hook `timeout` across settings files, capped at 60 s; timeouts on plugin-provided hooks do not raise it. Override with `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`.

**`InstructionsLoaded`** — matchers `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`. Input: `file_path`, `memory_type` (`User`/`Project`/`Local`/`Managed`), `load_reason`, `globs`, `trigger_file_path`, `parent_file_path`. No decision control; the exit code is ignored.

`CLAUDE_ENV_FILE` is available to `SessionStart`, `Setup`, `CwdChanged`, and `FileChanged` only. Appending `export` lines to it makes them a preamble before every Bash command:

```bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
```

## Prompt events

**`UserPromptSubmit`** — no matcher. Input field is `prompt`. Output: `decision: "block"` (which erases the prompt), `reason`, `additionalContext`, `sessionTitle`, `suppressOriginalPrompt`. Timeout drops to 30 s for command, HTTP, and MCP handlers; a timed-out hook is canceled and its output discarded, while the prompt still reaches Claude. This event cannot replace the prompt text.

**`UserPromptExpansion`** — matches the command name. Input: `expansion_type` (`slash_command` or `mcp_prompt`), `command_name`, `command_args`, `command_source`, `prompt`. This covers the path `PreToolUse` misses — typing `/skillname` directly never produces a `Skill` tool call.

**`MessageDisplay`** — no matcher. Input: `turn_id`, `message_id`, `index`, `final`, `delta`. Output: `hookSpecificOutput.displayContent`, which is display-only — the transcript and Claude both keep the original. Timeout 10 s. In `-p` and SDK runs it fires once per message with `index: 0`, `final: true`, and the full text in `delta`; treat `final` rather than a non-empty delta as end-of-message.

## Tool events

All five tool events match on the tool name.

**`PreToolUse`** — input: `tool_name`, `tool_input`, `tool_use_id`. Output goes in `hookSpecificOutput`: `permissionDecision` (`allow`/`deny`/`ask`/`defer`), `permissionDecisionReason`, `updatedInput`, `additionalContext`.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Force-push to main is blocked by policy."
  }
}
```

- Fires before any permission-mode check, in every mode including `dontAsk` and `bypassPermissions`. A `deny` blocks even under `--dangerously-skip-permissions`. Hooks tighten; they never loosen.
- `permissionDecisionReason` is shown to the user for `allow` and `ask`, to Claude for `deny`, and ignored for `defer`.
- `updatedInput` replaces the entire input object — include the fields you are not changing.
- `defer` works only in `-p` mode and only when the turn contains a single tool call.
- Does not fire for files referenced with `@` in a prompt (no tool call is made — use a `Read` deny rule), or for `EndConversation`.
- Top-level `decision`/`reason` is deprecated for this event.

Per-tool `tool_input` shapes: **Bash** `command, description, timeout, run_in_background`; **Write** `file_path, content`; **Edit** `file_path, old_string, new_string, replace_all`; **Read** `file_path, offset, limit`; **Glob** `pattern, path`; **Grep** `pattern, path, glob, output_mode`; **WebFetch** `url, prompt`; **WebSearch** `query, allowed_domains, blocked_domains`; **Agent** `prompt, description, subagent_type, model`.

**`PostToolUse`** — input adds `tool_response` and `duration_ms`. Output: `decision: "block"` with `reason` (which appends to the result — Claude still sees the original output), `additionalContext`, `updatedToolOutput`. `updatedToolOutput` must match the tool's own output shape; a mismatch on a built-in tool is silently ignored and the original is used.

**`PostToolUseFailure`** — input adds `error`, `is_interrupt`, `duration_ms`. Output: `additionalContext` only. Does not fire for pre-execution rejections such as an unknown tool, a schema-validation failure, or a permission denial — those fire neither `PreToolUse` nor this event.

**`PermissionRequest`** — input adds `permission_suggestions` and has **no** `tool_use_id`. Output is `hookSpecificOutput.decision` with `behavior` (`allow`/`deny`), plus `updatedInput`, `updatedPermissions`, and `message`. Does not fire in `-p` mode — use `PreToolUse` there.

**`PermissionDenied`** — fires only for auto-mode classifier denials, not for manual denials, `PreToolUse` blocks, or deny rules. Output: `hookSpecificOutput.retry: true`.

**`PostToolBatch`** — no matcher. Input field is `tool_calls`, an array whose `tool_response` holds the serialized content the model sees, which differs from the structured object `PostToolUse` receives.

## Turn and agent events

**`Stop`** — no matcher. Input: `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons` (the last two need v2.1.145+). Output: `decision: "block"` with a required `reason`, or `hookSpecificOutput.additionalContext` to continue the turn under the same loop protections without a hook-error notice.

Claude Code overrides a `Stop` hook after it blocks 8 consecutive times. Guard on the input flag so the hook stands down once it has had its say:

```bash
#!/bin/bash
INPUT=$(cat)
if [ "$(jq -r '.stop_hook_active' <<<"$INPUT")" = "true" ]; then exit 0; fi
```

Raise the cap with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`. `Stop` does not fire on user interrupts; API errors fire `StopFailure` instead.

**`StopFailure`** — matchers `rate_limit`, `overloaded`, `authentication_failed`, `oauth_org_not_allowed`, `billing_error`, `invalid_request`, `model_not_found`, `server_error`, `max_output_tokens`, `unknown`. Input: `error`, `error_details`, and a `last_assistant_message` that holds the API error string rather than a reply. Output and exit code are both ignored. Its matcher uses the narrow exact-match set: letters, digits, `_`, and `|` only.

**`SubagentStart` / `SubagentStop`** — match the agent type (`general-purpose`, `Explore`, custom names, or plugin-scoped `^my-plugin:reviewer$`). `SubagentStart` output is `additionalContext`, injected into the *subagent's* context. To inject into the parent after a subagent returns, hook `PostToolUse` on the `Agent` tool instead. `SubagentStop` carries `agent_transcript_path` and `last_assistant_message`.

In subagent frontmatter, a `Stop` hook is automatically converted to `SubagentStop`.

## Task and teammate events

**`TaskCreated` / `TaskCompleted`** — no matcher. Input: `task_id`, `task_subject`, `task_description`, `teammate_name`, and a deprecated `team_name`. **`TeammateIdle`** — no matcher; input `teammate_name`. All three block via exit 2 or `{"continue": false, "stopReason": "..."}`.

**`Notification`** — matchers `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed`. Input: `message`, `title`, `notification_type`.

## Environment events

**`ConfigChange`** — matchers `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`. Input: `source`, `file_path`. Blocking works except for `policy_settings`.

**`CwdChanged`** — no matcher. Input: `old_cwd`, `new_cwd`. Output: `watchPaths`, which replaces the dynamic watch list; matcher-configured paths are always watched, and an empty array clears the dynamic list.

**`FileChanged`** — input field is `event` (`change`, `add`, `unlink`), plus `file_path`. Its matcher does double duty: split on `|` it builds the literal-filename watch list in the working directory, and it also filters which groups run, matched against the changed file's basename. Regex is useless in the first role — `^\.env` watches a file literally named `^\.env`. Like `StopFailure`, its matcher uses the narrow exact-match set, so only `|` separates alternatives.

**`WorktreeCreate` / `WorktreeRemove`** — no matcher. `WorktreeCreate` input carries `name`; a command hook returns the worktree path as the last non-empty line of stdout, with everything else redirected to stderr, while an HTTP hook returns `hookSpecificOutput.worktreePath`. Configuring a `WorktreeCreate` hook replaces default git behavior entirely, so `.worktreeinclude` is not processed. Absolute paths containing `.` or `..` segments, and any path passing through a symlink below the repo root, are refused (v2.1.216+). Any non-zero exit fails creation.

## Compaction and elicitation

**`PreCompact` / `PostCompact`** — matchers `manual`, `auto`. `PreCompact` input carries `trigger` and `custom_instructions`; `PostCompact` carries `trigger` and `compact_summary`. Blocking a proactive auto-compaction skips it and continues; blocking one triggered to recover from a context-limit error the API already returned makes the underlying error surface and the request fail.

**`Elicitation` / `ElicitationResult`** — match the MCP server name. `Elicitation` input: `mcp_server_name`, `message`, `mode` (`form` or `url`), `requested_schema` or `url`, optional `elicitation_id`. Output: `hookSpecificOutput.action` (`accept`/`decline`/`cancel`) and `content`. `ElicitationResult` reports the resolved `action` and `content`.
