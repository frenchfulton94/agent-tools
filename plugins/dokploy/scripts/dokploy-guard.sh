#!/usr/bin/env bash
#
# PreToolUse guard for Bash commands touching a Dokploy instance.
#
#   deny  — removals with no undo. A project cascades to every service inside it; a
#           database or volume removal takes data that is in no git history and, unless
#           someone configured and tested backups, in no backup either.
#   ask   — disruptive but recoverable. An application is redeployable from git, a server
#           re-addable, a password resettable, an update re-runnable.
#   allow — everything else, silently, including deployment-history operations and every
#           read.
#
# The CLI and the API are the same surface, and every rule below carries both spellings,
# because one covering only the CLI is bypassed by a single curl. The API method is read
# off `dokploy <resource> <action> --help`, which names the `/api/<resource>.<method>` call
# it makes — not derived from the kebab-case command, since the resource segment camelCases
# too (`docker-volume remove-volume` is `/api/dockerVolume.removeVolume`, matched literally
# in the volume rule below). See the `automating-dokploy` skill for the discovery step.

set -uo pipefail

# Fail open when jq is absent. A guard that errors on every Bash call is worse than one
# that occasionally does not fire.
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$cmd" ]] && exit 0

# Collapse newlines and repeated spaces so multi-line and padded forms match.
norm=$(printf '%s' "$cmd" | tr '\n\t' '  ' | tr -s ' ')

# The help exemption is an anchored WHITELIST over the RAW command. Five things went wrong on
# the way here, so the reasoning matters more than the regex. These are states of this file, not
# fix rounds: item 1 is how it originally shipped, and items 2-5 are fix rounds 1-4, which is the
# numbering `tests/dokploy-guard.test.ts` uses for the same history.
#
#   1. (as first shipped) The original guard had no exemption logic at all — a bare substring
#      match on `--help` or ` -h` anywhere in the command. `-h` is the host flag for pg_dump,
#      psql, mysql, mysqldump, and redis-cli, so `pg_dump -h host app > a.sql && dokploy postgres
#      remove --postgresId db1` — "dump it, then remove it" — silently disarmed every rule below.
#   2. (fix round 1) Adding a blacklist on `; | &`, anchored to end-of-string, closed that — but
#      not command substitution, which needs no separator at all: `echo $(dokploy project remove
#      …)`, backticks, `cat <(…)`.
#   3. (fix round 2) Adding `$`, backtick, `(`, and newline to the blacklist, tested against the
#      raw command, closed substitution — but not `sh -c "<destructive>" --help`, where the
#      trailing flag is swallowed as `$0`, or `curl <api-url> -o -h`, where ` -h` is an option
#      *value*. Neither contains a blacklisted character, which is the actual lesson: a blacklist
#      of "characters that could chain a command" is unsound in principle, because `sh -c "cmd"
#      --help` needs no character at all. Only whitelisting the whole permitted shape works.
#   4. (fix round 3) Replacing the blacklist with an anchored whitelist, matched against `$norm`,
#      closed the shape problem — but `norm` is built with `tr '\n\t' ' '`, so a newline becomes
#      exactly the space the pattern expects: `dokploy project remove` + newline + `-h` matched.
#   5. (fix round 4) Matching the raw `$cmd` with `[[:blank:]]` (space and tab only), which
#      excludes newline, closed that too.
#
# Hence: match `$cmd`, never `$norm`, and use `[[:blank:]]` rather than `[[:space:]]`, so a
# newline cannot serve as a token separator. Bash anchors `^` and `$` to the whole string, so a
# second statement cannot hide anywhere.
#
# This can be tight because an exemption is only ever needed for a command that would otherwise
# match a rule below. A bare `dokploy --help` needs none — it matches no rule and falls through
# to allow on its own.
#
# There is deliberately no text-tool exemption. `printf '...' > /dev/tcp/host/80` reaches the API
# from a "text" tool with no chaining, so the premise that a text tool cannot execute was false.
if [[ "$cmd" =~ ^[[:blank:]]*dokploy([[:blank:]]+[a-z][a-z-]*){1,2}[[:blank:]]+(--help|-h)[[:blank:]]*$ ]]; then
  exit 0
fi

decide() {
  jq -nc --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

DBS='postgres|mysql|mongo|mariadb|redis|libsql'

# --- deny: removals with no undo ---------------------------------------------

if [[ "$norm" =~ dokploy[[:space:]]+project[[:space:]]+remove ]] \
   || [[ "$norm" =~ /api/project\.remove ]]; then
  decide deny "Removing a Dokploy project cascades to every application, database, and Compose service inside it, and to their volumes. Nothing here is recoverable from git. List what the project holds first with 'dokploy project one --projectId <id>', confirm with the user which services are safe to lose, and let them run the removal themselves. If you were only searching for this command or reading about it, run that search yourself — this guard cannot tell a mention from an invocation."
fi

if [[ "$norm" =~ dokploy[[:space:]]+($DBS)[[:space:]]+remove ]] \
   || [[ "$norm" =~ /api/($DBS)\.remove ]]; then
  decide deny "Removing a Dokploy database deletes the instance and its volume, and the data exists in no git history. Check whether a backup exists and is recent with 'dokploy backup list-backup-files', then let the user run the removal. If this only turned up in a grep or a file you were reading, rerun that lookup yourself — the guard has no way to distinguish a quoted command from a real one."
fi

if [[ "$norm" =~ dokploy[[:space:]]+docker-volume[[:space:]]+(remove-volume|delete-volume-file) ]] \
   || [[ "$norm" =~ /api/dockerVolume\.(removeVolume|deleteVolumeFile) ]]; then
  decide deny "This deletes volume data on the Dokploy host, which is where database and application state lives. Inspect it first with 'dokploy docker-volume get-volumes' and 'dokploy docker-volume list-volume-files', and let the user perform the deletion. If you only meant to echo or grep this string rather than run it, do that yourself instead — the guard denies the text either way, since it cannot tell them apart."
fi

# --- ask: disruptive, recoverable --------------------------------------------

if [[ "$norm" =~ dokploy[[:space:]]+application[[:space:]]+delete ]] \
   || [[ "$norm" =~ /api/application\.delete ]]; then
  decide ask "This deletes the application and its Dokploy configuration — domains, environment variables, and build settings. The code is still in git, but the configuration is not, and it has to be rebuilt by hand. If you were only quoting or searching for this command, do that lookup yourself — the guard reads the text of a command and cannot tell a quoted example from a real delete."
fi

if [[ "$norm" =~ dokploy[[:space:]]+backup[[:space:]]+remove ]] \
   || [[ "$norm" =~ /api/backup\.remove ]]; then
  decide ask "Removing a backup configuration stops future scheduled backups. Confirm another schedule covers this data before removing the one that does. If nothing is actually being removed here and the string is only text you were grepping or writing down, run that yourself instead; the guard matches on the text alone."
fi

if [[ "$norm" =~ dokploy[[:space:]]+server[[:space:]]+remove ]] \
   || [[ "$norm" =~ /api/server\.remove ]]; then
  decide ask "This detaches a remote server from the panel, so Dokploy stops managing and monitoring whatever is deployed on it. The containers keep running, unmanaged. Nothing is detached if this command merely appears inside something you were searching or editing — the guard cannot see that difference, so handle that text yourself."
fi

if [[ "$norm" =~ dokploy[[:space:]]+($DBS)[[:space:]]+change-password ]] \
   || [[ "$norm" =~ /api/($DBS)\.changePassword ]]; then
  decide ask "Rotating a database password breaks every application still holding the old credentials until each is redeployed. Confirm which services connect to it first. If no rotation is intended and the command is only being quoted, carry out that step yourself — a mention and an invocation look identical to the guard."
fi

if [[ "$norm" =~ install\.sh ]] && [[ "$norm" =~ -s([[:space:]]+--)?[[:space:]]+update ]]; then
  decide ask "This upgrades Dokploy in place on a live host, restarting the panel and Traefik. Confirm there is a current panel backup and that no deployment is mid-flight. No upgrade happens if this string is only being written down or searched for, but the guard sees the text and not the intent, so do that part yourself."
fi

exit 0
