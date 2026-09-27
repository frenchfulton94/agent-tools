#!/usr/bin/env bash
#
# PreToolUse guard for Bash commands touching a Godot project.
#
#   deny  — breaks uid:// identity with no repair. Godot tracks files by UID, and
#           where the UID lives depends on the file type (measured, spec 3.7):
#             .gd, .gdshader      a .uid sidecar beside the file
#             imported assets     a .import sidecar carrying uid=
#             .tscn, .tres        inline, inside the file
#           Moving a sidecar-bearing file without its sidecar puts it at a new
#           path, so the next import mints a new UID while every existing
#           reference still names the old one. No reimport reconciles that; it is
#           repaired by hand. Measured both ways in spec 3.4 and 3.8.
#   ask   — recoverable from git, but orphans references until it is.
#   allow — everything else, silently. UIDs are derived from the path (measured,
#           spec 3.8), so deleting a .uid or .import IN PLACE regenerates the
#           identical UID and is harmless; only a move changes the path. Directory
#           moves are safe too, because the sidecars travel inside the directory.
#           A guard that fires on safe operations gets turned off, and then it
#           protects nothing — including the one rule that matters.

set -uo pipefail

# Fail open when jq is absent. A guard that errors on every Bash call is worse
# than one that occasionally does not fire.
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$input" 2>/dev/null) || exit 0
[[ "$tool" != "Bash" ]] && exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$cmd" ]] && exit 0

norm=$(printf '%s' "$cmd" | tr '\n\t' '  ' | tr -s ' ')

decide() {
  jq -nc --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

# macOS ships bash 3.2 (the last GPLv2 release), whose [[ =~ ]] regex engine is
# the platform's own libc regex, not glibc — and unlike glibc, it does not treat
# \b as a word-boundary assertion (measured: it matches nothing, as if \b were
# some other escape entirely). A pattern ending in \b here would silently never
# match on stock macOS, which is exactly the failure mode this guard cannot
# afford: the deny rules below would never fire. ([^a-zA-Z0-9_]|$) is the
# boundary that works identically under both the BSD/macOS and GNU/glibc regex
# implementations bash may be linked against.
SIDECAR_SRC='\.(gd|gdshader)([^a-zA-Z0-9_]|$)'
ASSET='\.(png|jpg|jpeg|webp|svg|wav|ogg|mp3|glb|gltf|fbx|obj|ttf|otf)([^a-zA-Z0-9_]|$)'

# --- deny: identity loss with no repair --------------------------------------

# A move naming a sidecar-bearing file, where the sidecar is not also named.
if [[ "$norm" =~ (^|[^a-zA-Z])(git[[:space:]]+)?mv[[:space:]] ]] \
   && [[ "$norm" =~ $SIDECAR_SRC ]] \
   && [[ ! "$norm" =~ \.uid ]]; then
  decide deny "This moves a .gd or .gdshader file without its .uid sidecar. Godot keeps that file's identity in the sidecar: move the file alone and the next import mints a new UID, while every scene referencing it still names the old one. No reimport reconciles that — the references are repaired by hand, one at a time. Move both (for example 'mv a.gd b/a.gd && mv a.gd.uid b/a.gd.uid') and then run 'godot --headless --path . --import', or do the move in the Godot editor, which handles the sidecar for you. Moving the whole directory is also safe. If this command was only being quoted or searched for, run that lookup yourself — the guard reads command text and cannot tell a mention from an invocation."
fi

# A move naming an imported asset, where its .import is not also named.
if [[ "$norm" =~ (^|[^a-zA-Z])(git[[:space:]]+)?mv[[:space:]] ]] \
   && [[ "$norm" =~ $ASSET ]] \
   && [[ ! "$norm" =~ \.import ]]; then
  decide deny "This moves an imported asset without its .import sidecar, which is where Godot stores that asset's uid://. Moving the asset alone gives it a new UID on reimport while existing references keep the old one, and no reimport reconciles the two. Move both files, or move the containing directory, or do it in the editor. If you were only quoting this command, run that lookup yourself — the guard matches on text alone."
fi

if [[ "$norm" =~ --convert-3to4 ]]; then
  decide deny "--convert-3to4 rewrites every file in the project in place, and there is no undo. Confirm the project is committed to git or otherwise backed up, then let the user run it themselves. To see what it would change without changing anything, use --validate-conversion-3to4, which is read-only."
fi

# --- ask: recoverable from git, but breaks references until it is ------------

if [[ "$norm" =~ (^|[^a-zA-Z])rm[[:space:]].*\.(tscn|tres|gd|gdshader)([[:space:]]|$) ]]; then
  decide ask "Deleting a scene, resource, or script orphans every uid:// reference pointing at it. Nothing reports the breakage at deletion time — it surfaces later as a scene that will not load. Check what references it first with the reference_graph MCP tool. The file itself is recoverable from git if it was committed."
fi

if [[ "$norm" =~ (^|[^a-zA-Z])rm[[:space:]].*(project\.godot|export_presets\.cfg)([[:space:]]|$) ]]; then
  decide ask "This removes a project-level configuration file. project.godot defines the project itself — autoloads, input map, rendering settings — and export_presets.cfg holds every export configuration including signing settings. Neither is regenerated, and both are recoverable only from git."
fi

exit 0
