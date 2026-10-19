#!/bin/bash
# Checks the plutil half of the release block's step 6: that plutil reads a
# JSON file, prints a string value with `raw`, and exits non-zero on a missing
# key. The JSON below is a SAMPLE written for this check. It is not notarytool
# output: the keys of `notarytool submit -f json` are unverified until R6.
#
#   submit-json-check.sh <scratch-dir> > submit-json.log 2>&1
set -uo pipefail
OUT="${1:?usage: submit-json-check.sh <scratch-dir>}"
mkdir -p "$OUT"
SUBMIT_JSON="$OUT/sample-submit.json"

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion)"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
printf '{"id":"00000000-0000-0000-0000-000000000000","status":"Accepted","message":"sample"}\n' > "$SUBMIT_JSON"
echo "Sample (invented) JSON: $(cat "$SUBMIT_JSON")"

step() {   # step <title> <command...>
  echo
  echo "## $1"
  shift
  echo "\$ $*" | sed "s|$OUT|\$OUT|g"
  "$@" 2>&1 | sed "s|$OUT|\$OUT|g"
  echo "exit: ${PIPESTATUS[0]}"
}

step "status, as the release block prints it" plutil -extract status raw -o - "$SUBMIT_JSON"
step "id, as the release block captures it" plutil -extract id raw -o - "$SUBMIT_JSON"
SUBMISSION_ID="$(plutil -extract id raw -o - "$SUBMIT_JSON")"
echo "SUBMISSION_ID=$SUBMISSION_ID"
step "a missing key (expected: exit 1)" plutil -extract no-such-key raw -o - "$SUBMIT_JSON"
