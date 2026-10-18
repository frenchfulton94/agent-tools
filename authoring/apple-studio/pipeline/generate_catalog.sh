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
  # Page-form /documentation/ links end in ".md" (the Phase 8 rule); the HIG
  # entry and the pinned exceptions stay bare. The $bare list below must equal
  # KNOWN_PAGE_FORM_EXCEPTIONS in tests/apple-doc-links.test.ts, which is the
  # source of truth: when one changes, change the other in the same commit.
  jq -r --argjson bare '[
    "https://developer.apple.com/documentation/applicationservices",
    "https://developer.apple.com/documentation/cloudkit/cksyncengine",
    "https://developer.apple.com/documentation/corelocation/clbackgroundactivitysession",
    "https://developer.apple.com/documentation/coreservices",
    "https://developer.apple.com/documentation/installer_js",
    "https://developer.apple.com/documentation/iokit",
    "https://developer.apple.com/documentation/kernel",
    "https://developer.apple.com/documentation/playgroundbluetooth",
    "https://developer.apple.com/documentation/playgroundsupport",
    "https://developer.apple.com/documentation/tvmljs",
    "https://developer.apple.com/documentation/webkitjs"
  ]' '
    .references[]
    | select(.type == "topic" and (.title // "") != "" and (.url // "") != "")
    | ("https://developer.apple.com" + .url) as $u
    | (if ($u | startswith("https://developer.apple.com/documentation/")) and (($u | endswith(".md")) | not) and (($bare | index($u)) == null) then $u + ".md" else $u end) as $link
    | "- **\(.title)** — \((.abstract // []) | map(.text // "") | join("")) — \($link)"
  ' "$TMP" | sort -fu
} > "$OUT"
rm -f "$TMP"
echo "Wrote $OUT: $(grep -c '^- ' "$OUT") entries"
