#!/usr/bin/env bash
# Self-test for the stop-gate hooks. Offline: no xcodebuild, no real session.
#
#   ./pipeline/test_stop_gate.sh
#
# The cases encode what the 2026-09-12 Xcode run found: the Stop hook runs but
# PostToolUse does not, and Xcode's write tool is named mcp__xcode-tools__Xcode-
# Write with a camelCase `filePath` key. Every case runs the scripts in a temp
# directory with no .xcodeproj above it, so stop_gate.sh stops after deciding
# whether a build is due -- which is the decision under test.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TRACK="$ROOT/plugins/apple-studio/hooks/scripts/track_swift_edits.sh"
GATE="$ROOT/plugins/apple-studio/hooks/scripts/stop_gate.sh"
WORK="$(mktemp -d)"
FAILED=0

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

check() {  # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then
    printf 'ok    %s\n' "$1"
  else
    printf 'FAIL  %s: expected %s, got %s\n' "$1" "$2" "$3"
    FAILED=1
  fi
}

session() { printf 'sess-%s' "$1"; }
marker()  { printf '%s/stop-gate/%s.edited' "$WORK/data" "$(session "$1")"; }

# A Stop payload naming a transcript.
stop_payload() {  # stop_payload <session> <transcript path>
  printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","hook_event_name":"Stop","stop_hook_active":false}' \
    "$(session "$1")" "$2" "$WORK/proj"
}

# One transcript line carrying a tool_use.
tool_line() {  # tool_line <tool name> <input key> <path>
  printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"%s","input":{"%s":"%s"}}]}}\n' \
    "$1" "$2" "$3"
}

mkdir -p "$WORK/proj" "$WORK/data"
export CLAUDE_PLUGIN_DATA="$WORK/data"

echo "case 1 — PostToolUse records a Swift edit (Claude Code's key)"
printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$(session 1)" "$WORK/proj/A.swift" | "$TRACK"
check "marker written" "yes" "$([ -s "$(marker 1)" ] && echo yes || echo no)"

echo
echo "case 2 — PostToolUse accepts Xcode's camelCase filePath"
printf '{"session_id":"%s","tool_input":{"filePath":"%s"}}' "$(session 2)" "$WORK/proj/B.swift" | "$TRACK"
check "marker written" "yes" "$([ -s "$(marker 2)" ] && echo yes || echo no)"

echo
echo "case 3 — non-Swift edits are ignored"
printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$(session 3)" "$WORK/proj/notes.txt" | "$TRACK"
check "no marker" "no" "$([ -s "$(marker 3)" ] && echo yes || echo no)"

echo
echo "case 4 — Stop recovers the edit from the transcript when PostToolUse never ran"
tool_line "mcp__xcode-tools__XcodeWrite" "filePath" "$WORK/proj/C.swift" > "$WORK/t4.jsonl"
stop_payload 4 "$WORK/t4.jsonl" | "$GATE" > "$WORK/out4" 2>&1
check "exit 0 (no project above cwd, so no build)" 0 "$?"
check "marker recovered" "yes" "$([ -s "$(marker 4)" ] && echo yes || echo no)"
check "marker names the file" "$WORK/proj/C.swift" "$(cat "$(marker 4)" 2>/dev/null)"

echo
echo "case 5 — a transcript that only READ Swift does not trigger a build"
tool_line "mcp__xcode-tools__XcodeRead" "filePath" "$WORK/proj/D.swift" > "$WORK/t5.jsonl"
tool_line "Read" "file_path" "$WORK/proj/E.swift" >> "$WORK/t5.jsonl"
stop_payload 5 "$WORK/t5.jsonl" | "$GATE" > "$WORK/out5" 2>&1
check "no marker" "no" "$([ -s "$(marker 5)" ] && echo yes || echo no)"

echo
echo "case 6 — a transcript with only non-Swift writes does not trigger a build"
tool_line "Write" "file_path" "$WORK/proj/README.md" > "$WORK/t6.jsonl"
stop_payload 6 "$WORK/t6.jsonl" | "$GATE" > "$WORK/out6" 2>&1
check "no marker" "no" "$([ -s "$(marker 6)" ] && echo yes || echo no)"

echo
echo "case 7 — a missing transcript is not an error"
stop_payload 7 "$WORK/does-not-exist.jsonl" | "$GATE" > "$WORK/out7" 2>&1
check "exit 0" 0 "$?"
check "no marker" "no" "$([ -s "$(marker 7)" ] && echo yes || echo no)"

echo
echo "case 8 — fail-open when jq is unavailable"
# PATH must still resolve bash, or `#!/usr/bin/env bash` fails with 127 before
# the script runs and the test measures the harness instead of the hook.
mkdir -p "$WORK/minbin"
ln -sf "$(command -v bash)" "$WORK/minbin/bash"
for tool in cat printf wc tail grep sort tr mkdir dirname find rm; do
  src="$(command -v "$tool" 2>/dev/null)" && ln -sf "$src" "$WORK/minbin/$tool"
done
check "jq really is hidden" "" "$(PATH=$WORK/minbin command -v jq)"
code="$(printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$(session 8)" "$WORK/proj/F.swift" \
  | PATH="$WORK/minbin" "$TRACK" > /dev/null 2>&1; echo $?)"
check "track exits 0" 0 "$code"
check "track wrote nothing" "no" "$([ -s "$(marker 8)" ] && echo yes || echo no)"
code="$(stop_payload 8 "$WORK/t4.jsonl" | PATH="$WORK/minbin" "$GATE" > /dev/null 2>&1; echo $?)"
check "gate exits 0" 0 "$code"

echo
echo "case 9 — a re-entrant Stop is ignored"
printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","hook_event_name":"Stop","stop_hook_active":true}' \
  "$(session 9)" "$WORK/t4.jsonl" "$WORK/proj" | "$GATE" > "$WORK/out9" 2>&1
check "no marker" "no" "$([ -s "$(marker 9)" ] && echo yes || echo no)"

echo
echo "case 10 — a green build stays green: the same transcript is not rescanned"
# Case 4 already scanned t4.jsonl for session 4 and left a marker. A successful
# build removes the marker; the next Stop must not resurrect it from the same
# lines, or every Stop after one Swift edit rebuilds forever.
rm -f "$(marker 4)"
stop_payload 4 "$WORK/t4.jsonl" | "$GATE" > "$WORK/out10" 2>&1
check "no marker from already-scanned lines" "no" "$([ -s "$(marker 4)" ] && echo yes || echo no)"
tool_line "Edit" "file_path" "$WORK/proj/G.swift" >> "$WORK/t4.jsonl"
stop_payload 4 "$WORK/t4.jsonl" | "$GATE" > "$WORK/out10b" 2>&1
check "a NEW edit is still caught" "$WORK/proj/G.swift" "$(cat "$(marker 4)" 2>/dev/null)"

echo
if [ "$FAILED" -eq 0 ]; then echo "all cases passed"; else echo "one or more cases failed"; fi
exit "$FAILED"
