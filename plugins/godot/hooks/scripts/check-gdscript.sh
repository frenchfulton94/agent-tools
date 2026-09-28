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
#   - the project's class cache is missing, or a DIFFERENT .gd file newer
#     than the cache declares a class_name the cache doesn't know about yet
#     -- because a script referencing that class_name reports a spurious
#     "not declared" error until the next import picks it up. See the
#     freshness check below for why this is scoped to files other than the
#     one just edited, and to files that actually declare a class_name.

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

# Stay silent when the global class-name cache is missing, or when it is
# stale in the one way that actually produces a spurious diagnostic in the
# file being checked: a DIFFERENT .gd file, changed since the cache was
# written, that declares a class_name the cache doesn't know about yet.
# A directory-existence check (the original version of this script) only
# caught a brand-new checkout with no .godot/ at all. It missed the far more
# common case: an already-imported project where a class_name is added or
# changed in one file and a second file is written to use it in the very
# next edit, before anything re-imports. Reproduced against the engine:
# with the cache from a prior import still on disk, add `enemy_type.gd`
# declaring `class_name EnemyType`, then add a second script referencing
# `EnemyType` and run `--check-only` on IT — it reports "Could not find
# type EnemyType in the current scope" even though the type is spelled
# correctly and the file that declares it is sitting right there,
# unimported.
#
# Two things this staleness test must NOT do, both measured mistakes from
# earlier rounds of this same fix:
#
# 1. Include the file being checked in "is anything newer than the cache".
#    The file this hook is about to check was *itself* just written by the
#    edit that triggered this hook, so it is always newer than the last
#    import. A check that does not exclude it treats every single edit as
#    proof of a stale cache and silences the hook permanently after the
#    first post-import edit, on files with a real, unrelated parse error.
#    Confirmed empirically: touching only the target file (no other .gd in
#    the project) makes a same-file-inclusive `find` "detect" staleness on
#    every run, while excluding the target file via -samefile correctly
#    finds nothing stale.
#
# 2. Treat ANY newer-than-cache .gd file as disqualifying, regardless of
#    what it contains. An ordinary editing session touches several .gd
#    files in a row without reimporting between them; after the first edit,
#    every subsequent edit sees some other .gd file that is also newer than
#    the cache and, under a content-blind check, goes silent -- for the
#    rest of the session, on real errors that have nothing to do with class
#    resolution. A stale cache only produces a spurious diagnostic through
#    one mechanism: a class_name the cache hasn't indexed yet. Confirmed
#    empirically both ways: with a second, newer .gd file that declares no
#    class_name, the real error in the checked file must still be reported;
#    with a second, newer .gd file that DOES declare one, staying silent is
#    still correct. So the test below is not just "is something else
#    newer" but "does something else that's newer actually declare a
#    class_name" -- the only condition under which the cache being behind
#    can produce a wrong diagnostic in the file being checked now.
#
# -exec ... {} + (batched, one or a few grep processes covering every
# stale candidate) rather than -exec ... {} \; -quit (one grep process per
# candidate, short-circuited at the first class_name hit). Measured on a
# 20,000-file synthetic project with 50 files newer than the cache and none
# containing class_name -- the worst case, since a per-file exec then forks
# and execs grep 50 times before concluding there is nothing to suppress
# on: batched exec measured at ~62ms for the whole staleness test, versus
# ~150ms for the per-file version, on identical inputs. Process-spawn
# overhead per tiny file, not the grep itself, was the cost; batching
# removes it and scales with total bytes read instead of file count.
class_cache="$root/.godot/global_script_class_cache.cfg"
[[ -f "$class_cache" ]] || exit 0
stale_class_decl=$(find "$root" -name '*.gd' -newer "$class_cache" ! -samefile "$file" \
  -exec grep -lE '^[[:space:]]*class_name[[:space:]]' {} + 2>/dev/null | head -n 1)
[[ -z "$stale_class_decl" ]] || exit 0

rel="${file#"$root"/}"
errors=$("$godot_bin" --headless --path "$root" --check-only --script "$rel" 2>&1 >/dev/null \
  | grep -E '^(SCRIPT ERROR|ERROR):|^\s+at: .*\(res://' || true)

[[ -z "$errors" ]] && exit 0

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

# Deliberately does not say the errors ARE in $rel: --check-only compiles
# $rel, but a clean file that preloads a broken one reports errors whose
# `at:` frames point entirely at the preloaded file, not at $rel. Saying
# "errors in $rel" there would misattribute someone else's bug to every
# future edit of the innocent file. The `at:` lines carry the real location;
# the summary now says only that the check ran against $rel, not that $rel
# is where the problem lives.
jq -nc --arg m "godot --check-only flagged this while compiling $rel (its exit code is 0 regardless, so these come from stderr; errors may live in a res:// file $rel preloads, not in $rel itself):

$errors" \
  '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
