#!/usr/bin/env bash
# Stop gate: if Swift files were edited this session, require a green build.
set -u
INPUT="$(cat)" || exit 0
command -v jq >/dev/null 2>&1 || exit 0
[ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && exit 0
SESSION="$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)" || exit 0
DATA="${CLAUDE_PLUGIN_DATA:-/tmp}/stop-gate"
MARKER="$DATA/$SESSION.edited"

# Xcode 27's Claude Agent runs Stop hooks but not PostToolUse (verified
# 2026-09-12), so in that host the marker is never written and this gate would
# pass every time without building. Recover the same signal from the transcript
# the Stop payload names, reading only the lines added since the last check so a
# green build stays green instead of rebuilding on every Stop.
if [ ! -f "$MARKER" ]; then
  TRANSCRIPT="$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)"
  if [ -n "${TRANSCRIPT:-}" ] && [ -f "$TRANSCRIPT" ]; then
    SEEN_FILE="$DATA/$SESSION.scanned"
    SEEN=0
    [ -f "$SEEN_FILE" ] && SEEN="$(cat "$SEEN_FILE" 2>/dev/null || printf '0')"
    case "$SEEN" in ''|*[!0-9]*) SEEN=0 ;; esac
    TOTAL="$(wc -l < "$TRANSCRIPT" 2>/dev/null | tr -d ' ')"
    case "${TOTAL:-}" in ''|*[!0-9]*) TOTAL=0 ;; esac
    if [ "$TOTAL" -gt "$SEEN" ]; then
      EDITED="$(tail -n "+$((SEEN + 1))" "$TRANSCRIPT" 2>/dev/null | jq -r '
        select((.message.content? // null) | type == "array")
        | .message.content[]
        | select(.type? == "tool_use")
        | select((.name? // "") | test("Write|Edit"))
        | (.input.file_path? // .input.filePath? // empty)' 2>/dev/null \
        | grep -E '\.swift$' | sort -u)"
      mkdir -p "$DATA" 2>/dev/null && printf '%s' "$TOTAL" > "$SEEN_FILE" 2>/dev/null
      [ -n "$EDITED" ] && printf '%s\n' "$EDITED" >> "$MARKER" 2>/dev/null
    fi
  fi
fi

[ -f "$MARKER" ] || exit 0
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)" || exit 0
[ -d "$CWD" ] || exit 0
DIR="$CWD"; PROJDIR=""
for _ in 1 2 3; do
  if find "$DIR" -maxdepth 1 \( -name '*.xcworkspace' -o -name '*.xcodeproj' \) -print -quit 2>/dev/null | grep -q .; then
    PROJDIR="$DIR"; break
  fi
  DIR="$(dirname "$DIR")"
done
[ -n "$PROJDIR" ] || exit 0
SCHEME="$( (cd "$PROJDIR" && xcodebuild -list -json 2>/dev/null) | jq -r '(.project.schemes // .workspace.schemes // [])[0] // empty' 2>/dev/null)" || exit 0
[ -n "$SCHEME" ] || exit 0
LOG="$DATA/$SESSION.build.log"
build_with() {
  (cd "$PROJDIR" && xcodebuild build -scheme "$SCHEME" -destination "$1" -quiet >"$LOG" 2>&1)
}
if build_with 'generic/platform=iOS Simulator'; then rm -f "$MARKER"; exit 0; fi
# A destination mismatch (macOS-only project) is not a code failure - retry macOS.
if grep -qiE 'unavailable|no destinations|does not support' "$LOG" 2>/dev/null; then
  if build_with 'platform=macOS'; then rm -f "$MARKER"; exit 0; fi
  # Neither platform applies to this project: fail open rather than false-block.
  grep -qiE 'unavailable|no destinations|does not support' "$LOG" 2>/dev/null && exit 0
fi
ERRS="$(grep -m 5 'error:' "$LOG" 2>/dev/null | tr '\n' ' ')"
jq -n --arg r "Stop gate: build failed after Swift edits. Fix before finishing. Errors: $ERRS" \
  '{decision: "block", reason: $r}' 2>/dev/null || exit 0
exit 0
