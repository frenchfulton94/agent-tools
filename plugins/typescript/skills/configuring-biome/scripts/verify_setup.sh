#!/bin/sh
# Verify a Biome setup. Non-interactive; exits 1 if any check fails.
# Usage: sh verify_setup.sh [project-dir]   (defaults to the current directory)

set -u
DIR="${1:-.}"
cd "$DIR" 2>/dev/null || { echo "FAIL  no such directory: $DIR"; exit 1; }
FAILED=0
note() { echo "$1"; }
fail() { echo "FAIL  $1"; FAILED=1; }

# --- 1. locate the config, in Biome's own resolution order ---
CONFIG=""
for f in biome.json biome.jsonc .biome.json .biome.jsonc; do
  if [ -f "$f" ]; then CONFIG="$f"; break; fi
done
if [ -z "$CONFIG" ]; then
  fail "no biome.json / biome.jsonc found in $(pwd)"
  exit 1
fi
note "ok    config: $CONFIG"

# --- 2. resolve the binary ---
BIOME=""
if [ -x "./node_modules/.bin/biome" ]; then
  BIOME="./node_modules/.bin/biome"
elif command -v biome >/dev/null 2>&1; then
  BIOME="biome"
elif command -v npx >/dev/null 2>&1; then
  BIOME="npx --no-install @biomejs/biome"
fi
if [ -z "$BIOME" ]; then
  fail "biome binary not found (no node_modules/.bin/biome, no biome on PATH)"
  exit 1
fi

INSTALLED=$($BIOME --version 2>/dev/null | tr -dc '0-9.\n' | grep -m1 '[0-9]\.[0-9]')
if [ -z "$INSTALLED" ]; then
  fail "could not read the installed Biome version — is @biomejs/biome installed?"
  exit 1
fi
note "ok    installed version: $INSTALLED"

# --- 3. $schema must match the installed version ---
SCHEMA_VER=$(grep -o 'schemas/[0-9][0-9.]*/schema.json' "$CONFIG" 2>/dev/null | head -1 | cut -d/ -f2)
if grep -q 'configuration_schema.json' "$CONFIG" 2>/dev/null; then
  note "ok    \$schema points at the local node_modules schema"
elif [ -z "$SCHEMA_VER" ]; then
  note "warn  no \$schema in $CONFIG — editors cannot validate this file"
elif [ "$SCHEMA_VER" != "$INSTALLED" ]; then
  fail "\$schema says $SCHEMA_VER but $INSTALLED is installed — editor validation will be wrong"
else
  note "ok    \$schema matches the installed version"
fi

# --- 4. v1 field shapes that parse but do nothing in v2 ---
case "${INSTALLED%%.*}" in
  1) note "warn  Biome v1 is installed; run 'biome migrate --write' after upgrading" ;;
  *)
    # collapse to one line so multi-line "key": { ... } is matchable
    FLAT=$(tr -d '\n\r\t' < "$CONFIG" | tr -s ' ')
    # v1 organizeImports takes an object; v2's assist action takes a string
    if printf '%s' "$FLAT" | grep -q '"organizeImports" *: *{'; then
      fail "$CONFIG has a v1 \"organizeImports\" block — use assist.actions.source.organizeImports"
    fi
    for pat in '"include"' '"ignore"'; do
      if printf '%s' "$FLAT" | grep -q "$pat *:"; then
        fail "$CONFIG contains $pat — a v1 field name, renamed to \"includes\" in v2"
      fi
    done
    ;;
esac

# --- 5. does it actually run, and does it match any files? ---
OUT=$($BIOME check --reporter=summary 2>&1)
STATUS=$?
if echo "$OUT" | grep -qi 'deserializ\|configuration.*error\|unknown key\|failed to parse'; then
  fail "Biome reported a configuration problem:"
  echo "$OUT" | sed 's/^/      /'
elif echo "$OUT" | grep -q 'Checked 0 files\|No files were processed'; then
  fail "Biome checked 0 files — files.includes matches nothing"
elif [ $STATUS -eq 0 ]; then
  note "ok    biome check passed"
else
  note "ok    config is valid; biome check reported diagnostics (run 'biome check' to see them)"
fi

# --- 6. competing formatters ---
for f in .prettierrc .prettierrc.json .prettierrc.js prettier.config.js \
         .eslintrc .eslintrc.json .eslintrc.js eslint.config.js eslint.config.mjs; do
  [ -f "$f" ] && note "warn  $f still present — two formatters will fight on save"
done

[ $FAILED -eq 0 ] && note "" && note "All checks passed."
exit $FAILED
