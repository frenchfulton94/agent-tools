#!/bin/bash
# Phase 10 final fix: Vale over every file this round edited, before (at the
# round's base commit) and after. Run from the catalog root:
#   run_vale.sh <base-commit> <scratch-dir>
# Prints per-file error and warning counts both ways, then each error in the
# edited file. The "amend" warning is waived (Phase 9 ruling); it is counted
# with the other warnings.
set -u
base="${1:?usage: run_vale.sh <base-commit> <scratch-dir>}"
scratch="${2:?usage: run_vale.sh <base-commit> <scratch-dir>}"
ini=.claude/skills/controlled-engineering-english/scripts/vale/.vale.ini
files=(
  plugins/apple-studio/skills/apple-games/references/game-center-and-online.md
  plugins/apple-studio/skills/apple-games/references/input.md
  plugins/apple-studio/skills/apple-metal/references/command-model.md
  plugins/apple-studio/skills/apple-metal/references/cpp-and-rust.md
  plugins/apple-studio/skills/app-release/references/direct-distribution.md
  plugins/apple-studio/skills/apple-games/SKILL.md
  plugins/apple-studio/skills/apple-frameworks/SKILL.md
  authoring/apple-studio/docs/deferred.md
)
mkdir -p "$scratch"
status=0
echo "base: $base; vale $(vale --version | awk '{print $NF}')"
for f in "${files[@]}"; do
  old="$scratch/$(echo "$f" | tr '/' '_')"
  git show "$base:$f" > "$old"
  # Vale's line output (path:line:col:check:message) has no severity, so
  # errors are counted with --minAlertLevel=error.
  e_old=$(vale --config "$ini" --minAlertLevel=error --output=line "$old" 2>/dev/null | wc -l | tr -d ' ')
  e_new=$(vale --config "$ini" --minAlertLevel=error --output=line "$f" 2>/dev/null | wc -l | tr -d ' ')
  w_old=$(vale --config "$ini" --output=line "$old" 2>/dev/null | wc -l | tr -d ' ')
  w_new=$(vale --config "$ini" --output=line "$f" 2>/dev/null | wc -l | tr -d ' ')
  verdict=ok; [ "$e_new" -gt "$e_old" ] && { verdict="MORE ERRORS"; status=1; }
  echo
  echo "== $f"
  echo "errors: $e_old -> $e_new   all alerts: $w_old -> $w_new   [$verdict]"
  vale --config "$ini" --minAlertLevel=error --output=line "$f" 2>/dev/null | sed 's/^/  /'
done
echo
echo "== overall: $([ $status -eq 0 ] && echo 'PASS (no new errors)' || echo FAIL)"
exit $status
