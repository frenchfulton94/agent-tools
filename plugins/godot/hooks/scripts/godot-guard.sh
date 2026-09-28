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
#           repaired by hand. Measured both ways in spec 3.4 and 3.8. The same
#           identity loss happens via `cp` (or `install`) followed by removing
#           the original, `rsync --remove-source-files`, and `find ... -exec mv
#           ... \;` — all treated the same as a plain `mv`.
#   ask   — recoverable from git, but orphans references until it is.
#   allow — everything else, silently. Deleting a .uid or .import IN PLACE (the
#           file it identifies stays exactly where it is) is harmless (measured,
#           spec 3.8): the file's path hasn't changed, so a scene naming its
#           unchanged path= still resolves either way. This is NOT because both
#           sidecars regenerate the identical UID on reimport — only the .uid
#           case does; a deleted .import sidecar reliably comes back as *some*
#           UID, but not the same one cycle to cycle. Only a move changes the
#           path, which is what actually breaks a uid://-only reference.
#           Directory moves are safe too, because the sidecars travel inside
#           the directory. A guard that fires on safe operations gets turned
#           off, and then it protects nothing — including the one rule that
#           matters.
#
# ## Why this file is three lines of logic and a delegate, not the whole guard
#
# Task 9 originally shipped this guard as pure bash regex over the whole
# command string (`[[ "$norm" =~ ... ]]`). An independent review (fix round 1)
# confirmed, by running the actual script rather than reading the regexes,
# that a whole-command text test cannot express "did THIS file's sidecar get
# named too" once more than one file, one statement, or a comment is on the
# line — `mv scripts/a.gd scripts/a.gd.uid scripts/b.gd entities/` contains
# ".uid" in the command, but only a.gd is paired; b.gd is not, and a substring
# test cannot tell the difference. That, plus case-sensitivity (`[[ =~ ]]`
# never folds case, so `MV a.gd b.gd` matched no rule at all), plus quoting
# defeating the ask-tier boundary regex, plus several unguarded command shapes
# (rsync --remove-source-files, cp+rm, find -exec mv), forced a rewrite onto
# real tokenization: split the command into statements, split statements into
# arguments (respecting quotes and comments), and reason per argument.
#
# That is what godot_guard.py does, using Python's `shlex` — confirmed
# empirically (not assumed) to strip quotes, drop comments, and split shell
# operators into their own tokens exactly as needed here. This plugin already
# requires python3 for its MCP server, so depending on it here trades one
# already-required dependency for another; it does not add a new one to the
# plugin as a whole. jq is no longer used anywhere in this guard.
#
# Full rationale, the specific bugs this replaced, and their test coverage
# live in godot_guard.py's module docstring and in scripts/test/test_guard.py.

set -uo pipefail

# Fail open when python3 is absent. A guard that errors on every Bash call is
# worse than one that occasionally does not fire — same principle the
# original bash-only version applied to a missing jq.
command -v python3 >/dev/null 2>&1 || exit 0

exec python3 "$(dirname -- "${BASH_SOURCE[0]:-$0}")/godot_guard.py"
