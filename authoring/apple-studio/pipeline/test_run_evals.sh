#!/usr/bin/env bash
# Self-test for pipeline/run_evals.py. Uses a stub `claude` and a throwaway git
# repo, so it runs offline, costs nothing, and never touches StudioFixture.
#
#   ./pipeline/test_run_evals.sh
#
# Each case asserts the behavior of one Phase 6 harness defect the driver exists
# to prevent. Exit 0 means all four cases held.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS="$ROOT/pipeline/fixtures/eval-harness"
STUB="$HARNESS/fake-claude.py"
PROMPTS="$HARNESS/prompts.tsv"
WORK="$(mktemp -d)"
FIXTURE="$WORK/fixture"
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

mkdir -p "$FIXTURE"
git -C "$FIXTURE" init -q
printf 'kept\n' > "$FIXTURE/Kept.swift"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" -c user.email=t@t -c user.name=t commit -qm init

run_sweep() {  # run_sweep <outdir> [extra args...]
  local out="$1"; shift
  python3 "$ROOT/pipeline/run_evals.py" "$PROMPTS" "$out" \
    --fixture "$FIXTURE" --claude-bin "$STUB" "$@" > "$out.stdout" 2> "$out.stderr"
  echo $?
}

echo "case 1 — scoring, fixture-write detection, and restore"
code="$(run_sweep "$WORK/out1")"
check "exit code is 1 (one FAIL and one fixture write)" 1 "$code"
check "FIRE match passes"            "PASS" "$(awk -F'\t' '$1=="a"{print $5}' "$WORK/out1/results.tsv")"
check "NOFIRE routed elsewhere passes" "PASS" "$(awk -F'\t' '$1=="b"{print $5}' "$WORK/out1/results.tsv")"
check "write attributed to its prompt" "LeakedByEval.swift" "$(awk -F'\t' '$1=="c"{print $7}' "$WORK/out1/results.tsv")"
check "turn exhaustion noted, not scored as a clean miss" "max_turns" "$(awk -F'\t' '$1=="d"{print $6}' "$WORK/out1/results.tsv")"
check "fixture restored after the write" "" "$(git -C "$FIXTURE" status --porcelain)"

echo
echo "case 2 — a dirty fixture refuses the run before any session starts"
printf 'stale\n' > "$FIXTURE/Stale.swift"
code="$(run_sweep "$WORK/out2")"
check "exit code is 2" 2 "$code"
check "no session ran" "absent" "$([ -f "$WORK/out2/results.tsv" ] && echo present || echo absent)"
rm -f "$FIXTURE/Stale.swift"

echo
echo "case 3 — the driver's own stdin must not reach the child"
code="$(python3 "$ROOT/pipeline/run_evals.py" "$PROMPTS" "$WORK/out3" \
  --fixture "$FIXTURE" --claude-bin "$STUB" --only a,b < "$PROMPTS" \
  > "$WORK/out3.stdout" 2> "$WORK/out3.stderr"; echo $?)"
check "exit code is 0" 0 "$code"
check "no log records a stdin leak" "" "$(grep -l stdin_leak "$WORK/out3"/*.log 2>/dev/null)"

echo
echo "case 4 — a non-git fixture refuses the run"
mkdir -p "$WORK/notrepo"
code="$(python3 "$ROOT/pipeline/run_evals.py" "$PROMPTS" "$WORK/out4" \
  --fixture "$WORK/notrepo" --claude-bin "$STUB" \
  > "$WORK/out4.stdout" 2> "$WORK/out4.stderr"; echo $?)"
check "exit code is 2" 2 "$code"

echo
if [ "$FAILED" -eq 0 ]; then
  echo "all cases passed"
else
  echo "one or more cases failed"
fi
exit "$FAILED"
