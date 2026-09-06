#!/usr/bin/env bash
# Eval fixture: places additionalContext at the top level of the JSON object, where
# Claude Code silently ignores it. It belongs inside hookSpecificOutput.
set -uo pipefail

cat <<'JSON'
{
  "additionalContext": "This file is generated. Edit src/schema.ts and run `bun generate` instead."
}
JSON
