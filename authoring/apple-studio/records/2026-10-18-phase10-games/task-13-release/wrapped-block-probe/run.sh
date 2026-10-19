#!/bin/bash
# Runs the Swift gate on the two fixtures beside this script and writes
# run-<label>.log (default label: after-fix).
# Before the ruling P50 gate fix (run-before-fix.log), both wrapped blocks PASS.
# After it (run-after-fix.log), dual-target.md block 1 FAILS on iOS; the
# macos-only.md block still passes, because its file declares no iOS target.
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../../../.." && pwd)"
cd "$root" || exit 1
rel="authoring/apple-studio/records/2026-10-18-phase10-games/task-13-release/wrapped-block-probe"
{
  echo "# Swift gate on platform-wrapped blocks, $(date +%Y-%m-%dT%H:%M%z), $(xcrun swiftc --version 2>&1 | head -1)"
  echo "\$ python3 authoring/apple-studio/pipeline/typecheck_snippets.py $rel/dual-target.md $rel/macos-only.md"
  python3 authoring/apple-studio/pipeline/typecheck_snippets.py "$rel/dual-target.md" "$rel/macos-only.md" 2>&1
  echo "exit: $?"
} > "$here/run-${1:-after-fix}.log"
cat "$here/run-${1:-after-fix}.log"
