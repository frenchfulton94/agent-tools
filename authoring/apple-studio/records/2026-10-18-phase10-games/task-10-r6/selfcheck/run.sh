#!/bin/bash
# Runs the swift block of direct-distribution.md ("A release smoke test in
# code") as the reference prints it. It extracts the block, adds one call that
# prints the result, and compiles it. Then it ad hoc signs the binary twice,
# with and without get-task-allow, and runs it each time. Identity "-" only.
#
#   run.sh <scratch-dir>
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../../.." && pwd)"
REF="$ROOT/plugins/apple-studio/skills/app-release/references/direct-distribution.md"
OUT="${1:?usage: run.sh <scratch-dir>}"
mkdir -p "$OUT"

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion), $(xcodebuild -version | head -1)"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"

awk '/^```swift$/{p=1;next} /^```$/{if(p){exit}} p' "$REF" > "$OUT/main.swift"
echo 'print("get-task-allow claimed: \(signatureClaimsGetTaskAllow())")  // probe' >> "$OUT/main.swift"
echo "Extracted $(grep -c '' "$OUT/main.swift") lines from direct-distribution.md (last line is the probe call)"

step() {   # step <title> <command...>
  echo
  echo "## $1"
  shift
  echo "\$ $*" | sed "s|$OUT|\$OUT|g; s|$HERE/||g"
  "$@" 2>&1 | sed "s|$OUT|\$OUT|g"
  echo "exit: ${PIPESTATUS[0]}"
}

step "Compile" xcrun swiftc -O -target arm64-apple-macos26.0 "$OUT/main.swift" -o "$OUT/selfcheck"
step "Sign ad hoc with get-task-allow" codesign -s - -f --entitlements "$HERE/get-task-allow.entitlements" "$OUT/selfcheck"
step "Entitlements as signed" codesign -d --entitlements - --xml "$OUT/selfcheck"
echo
step "Run (expect true)" "$OUT/selfcheck"
step "Sign ad hoc with no entitlements" codesign -s - -f "$OUT/selfcheck"
step "Entitlements as signed (expect none)" codesign -d --entitlements - --xml "$OUT/selfcheck"
echo
step "Run (expect false)" "$OUT/selfcheck"
