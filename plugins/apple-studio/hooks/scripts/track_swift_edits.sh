#!/usr/bin/env bash
# Record Swift edits per session so the Stop gate knows a build check is due.
set -u
INPUT="$(cat)" || exit 0
command -v jq >/dev/null 2>&1 || exit 0
# Claude Code sends file_path; Xcode's mcp__xcode-tools__XcodeWrite sends
# filePath. Accept both rather than silently tracking nothing on one of them.
FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty' 2>/dev/null)" || exit 0
case "$FILE" in *.swift) ;; *) exit 0 ;; esac
SESSION="$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)" || exit 0
DATA="${CLAUDE_PLUGIN_DATA:-/tmp}/stop-gate"
mkdir -p "$DATA" 2>/dev/null || exit 0
printf '%s\n' "$FILE" >> "$DATA/$SESSION.edited" 2>/dev/null
exit 0
