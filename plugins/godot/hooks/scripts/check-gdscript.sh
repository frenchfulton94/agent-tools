#!/usr/bin/env bash
#
# PostToolUse handler. Reports GDScript parse and type errors in a .gd file
# Claude just edited.
#
# Advisory by design: always exits 0 and emits additionalContext rather than a
# decision. Game projects sit in deliberately broken intermediate states — a
# script referencing a node that is not in the scene yet is ordinary
# mid-refactor work — so blocking here would fight how the work is done.
#
# The reason this exists at all: `godot --check-only` exits 0 even when the
# script has parse errors, so the obvious safety check passes broken code
# silently. The diagnostics are only on stderr.
#
# Stays quiet in three cases, each of which would otherwise cry wolf:
#   - the edited file is not a .gd
#   - it is not inside a Godot project
#   - the project's class cache is missing entirely (nothing to check
#     staleness against at all -- see the early exit below)
# ...and, per diagnostic rather than per file, drops only the specific
# diagnostics a stale class-name cache would produce -- see "Per-diagnostic
# filtering" below for why suppression is scoped this narrowly.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
file=$(jq -r '.tool_input.file_path // .tool_input.path // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$file" ]] && exit 0
[[ "$file" != *.gd ]] && exit 0
[[ -f "$file" ]] || exit 0

godot_bin="${GODOT_BIN:-}"
if [[ -z "$godot_bin" ]]; then
  godot_bin=$(command -v godot 2>/dev/null || command -v godot4 2>/dev/null || true)
fi
if [[ -z "$godot_bin" && -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
  godot_bin="/Applications/Godot.app/Contents/MacOS/Godot"
fi
[[ -x "$godot_bin" ]] || exit 0

# Walk up for project.godot.
dir=$(cd "$(dirname "$file")" && pwd)
root=""
while [[ "$dir" != "/" ]]; do
  if [[ -f "$dir/project.godot" ]]; then root="$dir"; break; fi
  dir=$(dirname "$dir")
done
[[ -z "$root" ]] && exit 0

# No cache at all (brand-new checkout, never imported) -- nothing to compare
# a "newer than the cache" test against, so there is no way to tell a stale
# cross-file class_name reference from a real error. Stay silent entirely,
# same as always. Once the cache exists, staleness is handled per diagnostic
# below, not by silencing the whole file.
class_cache="$root/.godot/global_script_class_cache.cfg"
[[ -f "$class_cache" ]] || exit 0

rel="${file#"$root"/}"
errors=$("$godot_bin" --headless --path "$root" --check-only --script "$rel" 2>&1 >/dev/null \
  | grep -E '^(SCRIPT ERROR|ERROR):|^\s+at: .*\(res://' || true)

[[ -z "$errors" ]] && exit 0

# Per-diagnostic filtering.
#
# Two earlier rounds of this same fix suppressed at the wrong granularity --
# first "does .godot/ exist" (round 1), then "is some other .gd file newer
# than the cache" (round 1, refined in round 2 to "...and does it contain
# the text class_name"). Both silenced the whole file's check based on a
# fact about OTHER files, which a review reproduced three ways:
#   A. a bystander file with the substring "class_name" inside a multi-line
#      string (not a declaration at all, compiles cleanly) still silenced
#      a genuine, unrelated error in the file being checked;
#   B. -samefile compares an inode, so a symlinked edited path could be
#      "matched" by its own target under a different name and suppress its
#      own real error;
#   C. ANY class_name file anywhere newer than the cache silenced
#      everything, including during active scaffolding, which is exactly
#      when new class_name declarations are being added on purpose.
#
# A stale cache produces exactly one diagnostic shape: a reference to a
# specific class_name it hasn't indexed yet, which GDScript reports as
# either `Could not find type "X" in the current scope` (X used as a type
# annotation) or `Identifier "X" not declared in the current scope` (X used
# as a value, e.g. `X.new()`) -- confirmed against the engine that a single
# `var e: EnemyType = EnemyType.new()` line produces BOTH shapes for the
# same missing name, one per usage position. So filtering happens per
# diagnostic pair, keyed on the specific name X each one names, not on
# whether any newer file merely contains the word class_name:
#   - walk the diagnostics in the strict [message, at:] pairs the earlier
#     grep already produces;
#   - for a pair whose message matches either shape, extract X;
#   - drop that pair only if some .gd file newer than the cache (other than
#     the file being checked -- -samefile still excludes it, exactly as
#     before, but is no longer what decides suppression) declares
#     `class_name X` for that exact name;
#   - every other pair survives unconditionally, including a second,
#     unrelated missing-type error in the very same file that isn't backed
#     by any stale declaration.
# This closes A (a string can't match a specific name unless a real error
# happens to name-collide with it, which is a different, purely
# hypothetical failure mode the given tests don't construct), closes B
# (identity comparison no longer decides suppression -- a symlinked file's
# own real, unrelated error is never a name-matching candidate regardless
# of what -samefile does with its target), and closes C (an unrelated
# class_name elsewhere cannot match a name it doesn't share).
# bash 3.2 (macOS's shipped /usr/bin/env bash) has no mapfile/readarray, so
# the diagnostics are split into an array by hand rather than with either.
err_lines=()
while IFS= read -r line || [[ -n "$line" ]]; do
  err_lines+=("$line")
done <<<"$errors"
type_re='Could not find type "([^"]+)" in the current scope'
ident_re='Identifier "([^"]+)" not declared in the current scope'
kept=()
have_located=0
# Memoize the class_name lookup by name: the engine reports the SAME missing
# name via both diagnostic shapes for one bad reference (a type-annotation
# use and a value use both fail), so a file with one stale reference already
# produces two pairs naming the same X. Without this, the expensive find+
# grep below would run twice for one underlying cause. Plain parallel
# arrays, not an associative array (bash 3.2 -- see above -- has neither).
memo_names=()
memo_hits=()
i=0
n=${#err_lines[@]}
while (( i < n )); do
  msg="${err_lines[i]}"
  at=""
  if (( i + 1 < n )) && [[ "${err_lines[i+1]}" =~ ^[[:space:]]+at: ]]; then
    at="${err_lines[i+1]}"
  fi

  name=""
  if [[ "$msg" =~ $type_re ]]; then
    name="${BASH_REMATCH[1]}"
  elif [[ "$msg" =~ $ident_re ]]; then
    name="${BASH_REMATCH[1]}"
  fi

  drop=0
  if [[ -n "$name" ]]; then
    hit=""
    memo_idx=-1
    for j in "${!memo_names[@]}"; do
      if [[ "${memo_names[$j]}" == "$name" ]]; then
        memo_idx=$j
        break
      fi
    done
    if (( memo_idx >= 0 )); then
      hit="${memo_hits[$memo_idx]}"
    else
      hit=$(find "$root" -name '*.gd' -newer "$class_cache" ! -samefile "$file" \
        -exec grep -lE "^[[:space:]]*class_name[[:space:]]+${name}([[:space:]]|\$)" {} + 2>/dev/null | head -n 1)
      memo_names+=("$name")
      memo_hits+=("$hit")
    fi
    [[ -n "$hit" ]] && drop=1
  fi

  if [[ "$drop" -eq 0 ]]; then
    kept+=("$msg")
    if [[ -n "$at" ]]; then
      kept+=("$at")
      have_located=1
    fi
  fi

  if [[ -n "$at" ]]; then
    i=$((i + 2))
  else
    i=$((i + 1))
  fi
done

# Every diagnostic pair that names a specific location was a stale-cache
# artifact: nothing left to report. This also covers the generic trailing
# `ERROR: Failed to load script ... with error "Parse error"` line the
# engine always appends after any parse failure -- it has no `at:` line of
# its own (its C++ frame is filtered out upstream) and restates nothing
# beyond "loading failed", so surviving alone, with every specific cause
# dropped as stale-cache noise, it is not something worth breaking silence
# over. Confirmed against the engine: the exact stale-cache repro
# (class_name added elsewhere, referenced here, checked before reimport)
# leaves only this trailer once both of its diagnostic pairs are dropped,
# and reporting a bare "failed to load" with no cause is exactly the kind
# of uninformative noise this hook exists to avoid producing.
(( have_located == 0 )) && exit 0
errors=$(printf '%s\n' "${kept[@]}")

# Cap the message: an error repeated across a large file (one bad base class
# referenced many times, say) produces one diagnostic pair per occurrence,
# and an uncapped dump has been measured at ~150 KB / 2000 lines from a single
# 500-line file. That is a transcript flood on every single edit to the file
# until the root cause is fixed, which is its own way of getting this hook
# turned off.
total=$(printf '%s\n' "$errors" | grep -c .)
if [[ "$total" -gt 40 ]]; then
  errors=$(printf '%s\n' "$errors" | head -n 40)
  errors="$errors
... ($((total - 40)) more line(s) truncated)"
fi

# The preload hedge only earns its place when some surviving `at:` frame
# actually points somewhere other than $rel: --check-only compiles $rel, but
# a clean file that preloads a broken one reports errors whose `at:` frames
# point entirely at the preloaded file, not at $rel. Unconditionally hedging
# ("errors may live in a preloaded file") under-credits a genuine local
# error on a skim when every location already IS $rel. So check first.
foreign=0
while IFS= read -r line; do
  if [[ "$line" =~ \(res://([^:]+): ]] && [[ "${BASH_REMATCH[1]}" != "$rel" ]]; then
    foreign=1
    break
  fi
done <<<"$errors"

if [[ "$foreign" -eq 1 ]]; then
  header="godot --check-only flagged this while compiling $rel (its exit code is 0 regardless, so these come from stderr; errors may live in a res:// file $rel preloads, not in $rel itself):"
else
  header="godot --check-only reports these errors in $rel (its exit code is 0 regardless, so these come from stderr):"
fi

jq -nc --arg m "$header

$errors" \
  '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
