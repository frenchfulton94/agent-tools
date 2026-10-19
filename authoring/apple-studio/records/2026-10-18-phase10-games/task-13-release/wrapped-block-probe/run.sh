#!/bin/bash
# Runs the Swift gate on the two fixtures beside this script and writes run.log.
# Expected while deferred item 39 is open: the wrapped blocks PASS.
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../../../.." && pwd)"
cd "$root" || exit 1
rel="authoring/apple-studio/records/2026-10-18-phase10-games/task-13-release/wrapped-block-probe"
{
  echo "# Swift gate on platform-wrapped blocks, $(date +%Y-%m-%dT%H:%M%z), $(xcrun swiftc --version 2>&1 | head -1)"
  echo "\$ python3 authoring/apple-studio/pipeline/typecheck_snippets.py $rel/dual-target.md $rel/macos-only.md"
  python3 authoring/apple-studio/pipeline/typecheck_snippets.py "$rel/dual-target.md" "$rel/macos-only.md" 2>&1
  echo "exit: $?"
} > "$here/run.log"
cat "$here/run.log"
