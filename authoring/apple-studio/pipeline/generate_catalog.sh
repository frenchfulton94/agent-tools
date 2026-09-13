#!/usr/bin/env bash
# Regenerate the Apple framework catalog from the live Technologies index.
#
# Source shape (inspected 2026-08 against
# https://developer.apple.com/tutorials/data/documentation/technologies.json):
# `.references` is an object keyed by DocC identifier. Framework/technology
# entries have `.type == "topic"` (title, url, abstract, kind: symbol|article,
# role: collection|collectionGroup). A handful of `.type == "link"` entries
# are external URLs (swift.org, GitHub, a self-link to /documentation/technologies)
# and are excluded — they aren't frameworks. `.url` is root-relative
# (e.g. "/documentation/LocalAuthentication") and needs the host prepended.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT="$REPO_ROOT/plugins/apple-studio/skills/apple-frameworks/references/framework-catalog.md"
TMP="$(mktemp)"
curl -fsSL "https://developer.apple.com/tutorials/data/documentation/technologies.json" -o "$TMP"
{
  echo "# Apple framework catalog"
  echo
  echo "> generated: $(date +%Y-%m-%d) from the developer.apple.com Technologies index"
  echo "> regenerate: authoring/apple-studio/pipeline/generate_catalog.sh (rerun each phase and after WWDC)"
  echo
  jq -r '
    .references[]
    | select(.type == "topic" and (.title // "") != "" and (.url // "") != "")
    | "- **\(.title)** — \((.abstract // []) | map(.text // "") | join("")) — https://developer.apple.com\(.url)"
  ' "$TMP" | sort -fu
} > "$OUT"
rm -f "$TMP"
echo "Wrote $OUT: $(grep -c '^- ' "$OUT") entries"
