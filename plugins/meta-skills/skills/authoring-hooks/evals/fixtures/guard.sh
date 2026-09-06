#!/usr/bin/env bash
# Eval fixture: intends to block a dangerous command, but signals with exit 1.
# Exit 1 is a NON-BLOCKING error, so the tool call proceeds and nothing looks wrong.
# Reads stdin directly rather than through jq, so the fixture runs anywhere.
set -uo pipefail

input=$(cat)

if grep -q -- 'rm -rf' <<<"$input"; then
  echo "Refusing to run a recursive delete." >&2
  exit 1
fi

exit 0
