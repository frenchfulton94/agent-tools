# Hook recipes

Contents:
- [Format on write](#format-on-write)
- [Block a dangerous command](#block-a-dangerous-command)
- [Inject repository context at session start](#inject-repository-context-at-session-start)
- [Gate the end of a turn on tests](#gate-the-end-of-a-turn-on-tests)
- [Protect generated files with context, not a block](#protect-generated-files-with-context-not-a-block)
- [Notify without a terminal](#notify-without-a-terminal)
- [Bundle a hook in a plugin](#bundle-a-hook-in-a-plugin)

Each recipe is complete. Adapt the matcher and the script body; keep the exit-code and JSON conventions as written.

## Format on write

The simplest useful hook. `PostToolUse` cannot block, so nothing here needs a decision.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/format.sh"],
            "timeout": 30,
            "statusMessage": "Formatting..."
          }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
input=$(cat)
file=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[[ -z "$file" ]] && exit 0
case "$file" in
  *.ts|*.tsx|*.js|*.json) npx --yes prettier --write "$file" >/dev/null 2>&1 || true ;;
esac
exit 0
```

The `|| true` matters: a formatter failing on a half-written file should not surface as a hook error on every edit.

## Block a dangerous command

`PreToolUse` with exit 2. Note the matcher is the exact string `Bash`, not a pattern.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "bash", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.sh"] }]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
cmd=$(jq -r '.tool_input.command // empty')
if [[ "$cmd" =~ git[[:space:]]+push.*--force ]] && [[ "$cmd" =~ (main|master) ]]; then
  echo "Force-pushing to a protected branch is blocked. Open a pull request instead." >&2
  exit 2
fi
exit 0
```

Everything about the block travels on stderr and the exit code. Printing JSON here would be discarded, since JSON is read only on exit 0. The JSON equivalent, if you prefer it, is exit 0 with:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Force-pushing to a protected branch is blocked."
  }
}
```

A `PreToolUse` deny holds in every permission mode, including `bypassPermissions`.

## Inject repository context at session start

`SessionStart` is one of the few events where plain stdout already reaches Claude, so the JSON wrapper is optional. It is still worth using when you also want to set a session title.

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "bash", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/context.sh"] }] }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
dirty=$(git status --porcelain 2>/dev/null | head -20)
context="Current branch: ${branch}"
[[ -n "$dirty" ]] && context="${context}"$'\n'"Uncommitted changes:"$'\n'"${dirty}"
jq -nc --arg ctx "$context" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
```

Two things this recipe gets right and hand-written versions usually do not. `additionalContext` is nested inside `hookSpecificOutput` — at the top level it is silently dropped. And the context is phrased as facts about the repository rather than as instructions to the agent, which keeps it from reading as an injected system command.

## Gate the end of a turn on tests

The archetypal `Stop` hook, and the one that most needs the loop guard.

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "bash", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/test-gate.sh"], "timeout": 300 }] }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
set -uo pipefail
input=$(cat)

# Stand down once we have already blocked — the harness overrides a Stop hook after
# 8 consecutive blocks, and looping past that is worse than letting the turn end.
[[ "$(jq -r '.stop_hook_active' <<<"$input")" == "true" ]] && exit 0

if ! output=$(npm test --silent 2>&1); then
  jq -nc --arg r "Tests are failing. Fix them before finishing:"$'\n'"$(tail -20 <<<"$output")" \
    '{decision: "block", reason: $r}'
  exit 0
fi
exit 0
```

Exit 0 with `decision: "block"` and exit 2 with a stderr message are equivalent here. The JSON form is preferred when the reason is long or structured, because stderr on exit 2 is passed through as-is.

## Protect generated files with context, not a block

A blocked edit tells Claude what it may not do. Context tells it what to do instead, which usually resolves the situation in one turn rather than several.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "if": "Edit(**/*.generated.ts)",
        "hooks": [{ "type": "command", "command": "bash", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/generated.sh"] }]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
jq -nc '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "This file is generated. Edit src/schema.ts and run `bun generate` instead."
  }
}'
```

`if` is evaluated here because `PreToolUse` is a tool event. On a non-tool event the same handler would never run at all.

## Notify without a terminal

Hooks run without a controlling terminal, so `/dev/tty` is unavailable. `terminalSequence` is the supported channel, restricted to an allowlist of OSC sequences (`0`, `1`, `2`, `9`, `99`, `777`, and bare BEL).

```bash
#!/usr/bin/env bash
input=$(cat)
body=$(jq -r '.message // "Needs your attention"' <<<"$input")
seq=$(printf '\033]777;notify;%s;%s\007' "Claude Code" "$body")
jq -nc --arg seq "$seq" '{terminalSequence: $seq}'
```

Pair it with the `Notification` event and a matcher such as `permission_prompt` or `agent_completed`.

## Bundle a hook in a plugin

The configuration moves to `hooks/hooks.json` at the plugin root, and every path goes through `${CLAUDE_PLUGIN_ROOT}`. The inner `hooks` object is identical to the settings form, so migration is a copy.

```json
{
  "description": "Blocks edits to vendored dependencies",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash", "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/vendor-guard.sh"] }
        ]
      }
    ]
  }
}
```

Three plugin-specific constraints. A malformed `hooks/hooks.json` stops the whole plugin from loading, not just its hooks. `${CLAUDE_PLUGIN_ROOT}` changes on every plugin update, so a hook that caches anything must write to `${CLAUDE_PLUGIN_DATA}`. And a hook targeting the plugin's own MCP server needs the scoped name — matcher `mcp__plugin_<plugin>_<server>__.*`, and `server: "plugin:<plugin>:<server>"` for an `mcp_tool` handler.
