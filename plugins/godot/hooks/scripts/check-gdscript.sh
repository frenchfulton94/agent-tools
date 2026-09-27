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
#   - the project has no .godot/ cache, because a script referencing a
#     class_name defined elsewhere reports a spurious error before first import

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

# Before the first import there is no global class cache, so cross-file
# class_name references report errors that are not real.
[[ -d "$root/.godot" ]] || exit 0

rel="${file#"$root"/}"
errors=$("$godot_bin" --headless --path "$root" --check-only --script "$rel" 2>&1 >/dev/null \
  | grep -E '^(SCRIPT ERROR|ERROR):|^\s+at: .*\(res://' || true)

[[ -z "$errors" ]] && exit 0

jq -nc --arg m "godot --check-only reports errors in $rel (note: its exit code is 0 regardless, so these come from stderr):

$errors" \
  '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
