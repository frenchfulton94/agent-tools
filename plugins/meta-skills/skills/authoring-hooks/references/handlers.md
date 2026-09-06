# Hook handler reference

Contents:
- [Which events accept which handler](#which-events-accept-which-handler)
- [Fields common to all handlers](#fields-common-to-all-handlers)
- [The `if` field](#the-if-field)
- [Command handlers](#command-handlers)
- [HTTP handlers](#http-handlers)
- [MCP tool handlers](#mcp-tool-handlers)
- [Prompt and agent handlers](#prompt-and-agent-handlers)
- [Async handlers](#async-handlers)
- [Environment variables](#environment-variables)

## Which events accept which handler

**All five types** (`command`, `http`, `mcp_tool`, `prompt`, `agent`): `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied`, `Stop`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `UserPromptSubmit`, `UserPromptExpansion`.

**`command`, `http`, `mcp_tool` only** (no `prompt` or `agent`): `ConfigChange`, `CwdChanged`, `Elicitation`, `ElicitationResult`, `FileChanged`, `InstructionsLoaded`, `Notification`, `PreCompact`, `PostCompact`, `SessionEnd`, `StopFailure`, `SubagentStart`, `WorktreeCreate`, `WorktreeRemove`.

**`command` and `mcp_tool` only**: `SessionStart`, `Setup`.

## Fields common to all handlers

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `command`, `http`, `mcp_tool`, `prompt`, `agent` |
| `if` | no | Permission-rule syntax; evaluated only on tool events — see below |
| `timeout` | no | Seconds. Default 600 for `command`, `http`, `mcp_tool`; 30 for `prompt`; 60 for `agent` |
| `statusMessage` | no | Replaces the default spinner text |
| `once` | no | Runs once per session then unregisters. **Honored only in skill frontmatter**; ignored in settings files and agent frontmatter |

Timeout overrides by event: `UserPromptSubmit` lowers command, HTTP, and MCP handlers to 30 s; `MessageDisplay` lowers them to 10 s; `SessionEnd` runs on a 1.5 s budget.

Identical handlers are deduplicated — command handlers by command string plus `args`, HTTP handlers by URL.

## The `if` field

`if` takes exactly one permission rule: `"Bash(git *)"`, `"Edit(*.ts)"`. No `&&`, no `||`, no list syntax.

It is evaluated **only** on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, and `PermissionDenied`. On any other event, a handler carrying `if` never runs at all — which is a common cause of a hook that appears configured and does nothing.

File-tool matching is directory-sensitive: `"Edit(src/**)"` matches only the `src` directory in the working directory (v2.1.214+). Use `"Edit(**/src/**)"` to match at any depth.

Bash matching digs into the command string:

| Pattern | Command | Runs? | Why |
|---|---|---|---|
| `Bash(git *)` | `FOO=bar git push` | yes | Leading assignments are stripped |
| `Bash(git *)` | `npm test && git push` | yes | Each subcommand is checked |
| `Bash(rm *)` | `echo $(rm -rf /)` | yes | Command substitutions are checked |
| `Bash(rm *)` | `echo $(date)` | no | No subcommand matches |
| `Bash(git push *)` | `echo $(date)` | yes | Patterns naming more than the command run anyway on `$()`, backticks, and `$VAR` |

It fails open when the Bash command cannot be parsed, which is why `if` is a filter for convenience, not a security boundary. Use the permission system for hard allow and deny.

## Command handlers

| Field | Required | Notes |
|---|---|---|
| `command` | yes | Shell command; with `args`, the executable to spawn |
| `args` | no | Argument list — its presence switches to exec form |
| `async` | no | Run in the background, non-blocking |
| `asyncRewake` | no | Background plus wake Claude on exit 2; implies `async` |
| `shell` | no | `bash` or `powershell`. Defaults to bash, or PowerShell on Windows without Git Bash. Ignored when `args` is set |

**Exec form** (`args` present): `command` is resolved as an executable on `PATH` and spawned directly, with no shell. Each `args` element is one argument exactly as written; `$`, backticks, and apostrophes pass through verbatim. This is the safe form for untrusted input.

```json
{ "type": "command", "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/format.js", "--fix"] }
```

**Shell form** (`args` absent): the string goes to `sh -c`, Git Bash, or PowerShell, which tokenizes it and interprets pipes, `&&`, redirects, and globs. Quote every path.

```json
{ "type": "command", "command": "node \"${CLAUDE_PLUGIN_ROOT}\"/scripts/format.js --fix" }
```

Two platform notes: on Windows, `.cmd` and `.bat` shims in `node_modules/.bin` are not executables and cannot be spawned in exec form — point at the `.js` entry with `node` instead, or use shell form. And if `command` is a bare name containing whitespace while `args` is also set, Claude Code warns, because there is no executable named `node script.js`.

A subtle shell-form failure: profiles sourced through `BASH_ENV` and similar can prepend output to stdout, so the harness sees

```text
Shell ready on arm64
{"decision": "block", "reason": "Not allowed"}
```

and reports a JSON validation failure. Gate profile output on interactivity: `if [[ $- == *i* ]]; then echo "Shell ready"; fi`.

## HTTP handlers

| Field | Required | Notes |
|---|---|---|
| `url` | yes | POST target; the body is the hook's JSON input |
| `headers` | no | Values support `$VAR` and `${VAR}` |
| `allowedEnvVars` | no | Required for any interpolation to resolve; unlisted references become empty strings |

Response handling: 2xx with an empty body is success; 2xx with plain text adds the text as context; 2xx with JSON is parsed against the same output schema; anything non-2xx, plus connection failures and timeouts, is a non-blocking error and execution continues.

HTTP status codes alone cannot block. Return 2xx with `decision: "block"` or `hookSpecificOutput.permissionDecision: "deny"`.

The settings keys `allowedHttpHookUrls` and `httpHookAllowedEnvVars` constrain HTTP hooks from every source, including managed ones.

## MCP tool handlers

| Field | Required | Notes |
|---|---|---|
| `server` | yes | A configured server name. For a plugin-bundled server use the scoped `plugin:<plugin-name>:<server-name>`, not the bare key |
| `tool` | yes | Tool name |
| `input` | no | Arguments; string values support `${path}` substitution from the hook input, e.g. `"${tool_input.file_path}"` |

The server must already be connected — the hook never triggers OAuth or a connection. Text content is treated like command stdout; a disconnected server or an `isError: true` result is a non-blocking error. `SessionStart` and `Setup` typically fire before servers connect, so expect "not connected" on the first run.

## Prompt and agent handlers

| Field | Required | Notes |
|---|---|---|
| `prompt` | yes | `$ARGUMENTS` expands to the hook input JSON; if absent, the input is appended. Escape a literal with a backslash: `\$1.00` |
| `model` | no | Defaults to a fast model |
| `continueOnBlock` | no | Prompt handlers only. On `ok: false`, feed the reason back and continue rather than stopping |

Both return the same shape:

```json
{ "ok": true, "reason": "Explanation for the decision" }
```

An agent handler is a subagent with Read, Grep, and Glob, capped at 50 tool-use turns. It is experimental.

## Async handlers

`async: true` applies to `type: "command"` only.

- Async hooks cannot block or return decisions — `decision`, `permissionDecision`, and `continue` have no effect.
- Output is delivered on the next conversation turn, and waits for user interaction if the session is idle. The exception is `asyncRewake`, where exiting 2 wakes Claude immediately and shows stderr (or stdout when stderr is empty) as a system reminder.
- Only `additionalContext` reaches Claude; `systemMessage` goes to the user.
- JSON is validated against the same schema, and fields with the wrong type are dropped rather than crashing the session (v2.1.202+). `--debug` names what was dropped.
- Completion notifications are suppressed by default; `Ctrl+O` or `--verbose` shows them.
- There is no deduplication across firings — each execution is a separate process.

## Environment variables

| Variable | Meaning |
|---|---|
| `CLAUDE_PROJECT_DIR` | Project root |
| `CLAUDE_PLUGIN_ROOT` | Plugin install directory |
| `CLAUDE_PLUGIN_DATA` | Plugin persistent data directory |
| `CLAUDE_ENV_FILE` | `SessionStart`, `Setup`, `CwdChanged`, `FileChanged` only — append `export` lines to prefix every Bash command |
| `CLAUDE_EFFORT` | `low`, `medium`, `high`, `xhigh`, `max` |
| `CLAUDE_CODE_REMOTE` | `"true"` in remote web environments; unset in the local CLI |
| `CLAUDE_PLUGIN_OPTION_<KEY>` | Plugin `userConfig` values, key uppercased |
| `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` | Raises the 8-block `Stop` cap |
| `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` | `SessionEnd` budget in milliseconds |
| `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` | Extra matcher and query logging |

`ANTHROPIC_MODEL` is inherited from the shell and does not track `/model`. All `OTEL_*` exporter variables are stripped from every subprocess Claude Code spawns, hooks included.

## Documented limitations

Command hooks communicate only through stdout, stderr, and exit codes — they cannot trigger slash commands or tool calls. `PostToolUse` cannot undo anything, since the tool has already run. And when several `PreToolUse` hooks return `updatedInput` for the same tool, the last to finish wins, non-deterministically, because hooks run in parallel; keep it to one.
