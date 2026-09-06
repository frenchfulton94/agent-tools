#!/usr/bin/env bash
#
# PreToolUse guard for Bash commands.
#
#   deny  — anything that irreversibly destroys volume data. Volumes hold
#           databases and other state that is in no backup and no git history.
#   ask   — machine-wide image and build-cache wipes. Recoverable, but slow and
#           they reach across every project on the host, not just this one.
#   allow — everything else, silently.
#
# Scoped cleanup (docker image prune, container prune, buildx prune --filter)
# passes through untouched, so the guard does not stand between anyone and
# reclaiming disk.

set -uo pipefail

# Fail open when jq is absent. A guard that errors on every Bash call is worse
# than one that occasionally does not fire.
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$cmd" ]] && exit 0

# Collapse newlines and repeated spaces so multi-line and padded forms match.
norm=$(printf '%s' "$cmd" | tr '\n\t' '  ' | tr -s ' ')

decide() {
  jq -nc --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

# --- deny: volume destruction -------------------------------------------------

if [[ "$norm" =~ docker[[:space:]]+volume[[:space:]]+(rm|prune|remove) ]]; then
  decide deny "Removing Docker volumes destroys database and application state that exists in no backup and no git history. List what is there first with 'docker volume ls' and 'docker volume inspect <name>', confirm with the user which volume is safe to lose, and let them run the removal themselves."
fi

if [[ "$norm" =~ docker[[:space:]]+(system[[:space:]]+)?prune ]] && [[ "$norm" =~ --volumes ]]; then
  decide deny "'--volumes' on a prune deletes named volumes across every project on this machine, not just this one. Run 'docker system df -v' to see what is actually using space, then prune images, containers, or build cache specifically."
fi

if [[ "$norm" =~ docker[-[:space:]]compose([[:space:]]|$) ]] \
   && [[ "$norm" =~ [[:space:]]down([[:space:]]|$) ]] \
   && [[ "$norm" =~ [[:space:]](-v|--volumes|-[a-zA-Z]*v)([[:space:]]|$) ]]; then
  decide deny "'docker compose down -v' deletes this project's named volumes and the data in them. Plain 'docker compose down' stops and removes the containers while keeping the volumes. If the data really should go, let the user run it."
fi

if [[ "$norm" =~ rm[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*-?[a-zA-Z]*[rR][a-zA-Z]* ]] \
   && [[ "$norm" =~ (OrbStack|\.colima|\.lima|com\.docker\.docker) ]]; then
  decide deny "That path holds the container runtime's entire disk — every image, volume, and Linux machine on this Mac. Use the runtime's own reset (OrbStack Settings, 'colima delete', Docker Desktop → Troubleshoot) so it can tear down cleanly, and let the user trigger it."
fi

# --- ask: machine-wide, recoverable ------------------------------------------

if [[ "$norm" =~ docker[[:space:]]+(system|image)[[:space:]]+prune ]] \
   && [[ "$norm" =~ [[:space:]](-a|--all|-[a-zA-Z]*a)([[:space:]]|$) ]]; then
  decide ask "This removes every unused image on the machine, including ones belonging to other projects. Nothing is lost permanently, but everything gets re-pulled or rebuilt. 'docker system df' shows whether it is worth it."
fi

if [[ "$norm" =~ docker[[:space:]]+(buildx|builder)[[:space:]]+prune ]] \
   && [[ "$norm" =~ [[:space:]](-a|--all)([[:space:]]|$) ]] \
   && [[ ! "$norm" =~ --filter ]]; then
  decide ask "This clears the entire build cache, so the next build of every project starts cold. 'docker buildx prune --filter until=168h' trims only what is older than a week."
fi

exit 0
