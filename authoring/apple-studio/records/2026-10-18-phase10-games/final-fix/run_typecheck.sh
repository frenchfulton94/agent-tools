#!/bin/bash
# Phase 10 final fix: run the snippet gates over every reference this round
# edited, and bash -n over each shell block in them. Run from the catalog root.
# Output goes to stdout; typecheck.log in this directory is one run of it.
set -u
refs=(
  plugins/apple-studio/skills/apple-games/references/game-center-and-online.md
  plugins/apple-studio/skills/apple-games/references/input.md
  plugins/apple-studio/skills/apple-metal/references/command-model.md
  plugins/apple-studio/skills/apple-metal/references/cpp-and-rust.md
  plugins/apple-studio/skills/app-release/references/direct-distribution.md
)
status=0
echo "== date: $(date -u +%Y-%m-%dT%H:%MZ)"
echo "== $(sw_vers -productName) $(sw_vers -productVersion); $(xcrun swiftc --version 2>&1 | head -1)"
for f in "${refs[@]}"; do
  echo
  echo "== typecheck_snippets.py $f"
  python3 authoring/apple-studio/pipeline/typecheck_snippets.py "$f" 2>&1 | grep -E '^\s+\[|^TOTAL|FAIL|error:' ; s=${PIPESTATUS[0]}
  echo "exit: $s"; [ "$s" -eq 0 ] || status=1
  if grep -qE '^> typecheck-(metal|cpp|rust):' "$f"; then
    echo "== typecheck_native.py $f"
    python3 authoring/apple-studio/pipeline/typecheck_native.py "$f" 2>&1 | tail -n 40; s=${PIPESTATUS[0]}
    echo "exit: $s"; [ "$s" -eq 0 ] || status=1
  fi
  echo "== bash -n on each bash/sh block in $f"
  python3 -I - "$f" <<'PY' || status=1
import re, subprocess, sys
text = open(sys.argv[1]).read()
bad = 0
for n, (lang, body) in enumerate(re.findall(r"```(bash|sh)\n(.*?)```", text, re.S), 1):
    first = body.strip().split("\n")[0][:60]
    r = subprocess.run(["bash", "-n"], input=body, text=True, capture_output=True)
    print(f"  [{'PASS' if r.returncode == 0 else 'FAIL'}] {lang} #{n}  {first}")
    if r.returncode:
        print(r.stderr); bad = 1
sys.exit(bad)
PY
done
echo
echo "== overall: $([ $status -eq 0 ] && echo PASS || echo FAIL)"
exit $status
