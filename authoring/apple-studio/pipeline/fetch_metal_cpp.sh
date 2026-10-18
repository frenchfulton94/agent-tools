#!/bin/bash
# Fetch a pinned metal-cpp release into the pipeline cache, for the C++ gate.
#
#   fetch_metal_cpp.sh <version> [cache-dir]
#
# Lands the headers at <cache>/metal-cpp/<version>/ (Foundation/, Metal/,
# MetalFX/, QuartzCore/ directly beneath), which is the -I directory
# typecheck_native.py passes to clang++. The cache defaults to the pipeline's
# gitignored tmp/ directory. Nothing is installed and nothing is published:
# this is a download.
#
# WHY A PINNED TABLE: https://developer.apple.com/metal/cpp/ no longer links the
# archive. It builds no .zip link in HTML or script and points at
# github.com/apple/metal-cpp instead. The conventional path
# https://developer.apple.com/metal/cpp/files/metal-cpp_<version>.zip still
# serves the archives Apple publishes (probed 2026-10-18: 26 and 26.4 return
# 200 application/zip; 26.1, 26.2, 26.3 and 26.5 onward return 300; 27 and
# later return 404). A hash recorded here means a changed archive fails loudly
# instead of changing what the gate compiles against. Add a row to PINS to
# support another version. The record of how the row was found is
# authoring/apple-studio/records/2026-10-18-phase10-games/task-2-gates/metal-cpp.txt.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VERSION="${1:-}"
CACHE="${2:-$HERE/tmp}"

# version  sha256
PINS="
26.4 4e7587c0f351d782f1f3e7c67c649b40d0ba780c051b2f6729f00ddc61ada28c
"

if [ -z "$VERSION" ]; then
  echo "usage: fetch_metal_cpp.sh <version> [cache-dir]" >&2
  exit 2
fi
WANT="$(awk -v v="$VERSION" '$1 == v { print $2 }' <<<"$PINS")"
if [ -z "$WANT" ]; then
  echo "fetch_metal_cpp.sh: no pinned sha256 for metal-cpp $VERSION; pinned versions:" >&2
  awk 'NF { print "  " $1 }' <<<"$PINS" >&2
  exit 2
fi

DEST="$CACHE/metal-cpp/$VERSION"
if [ -f "$DEST/Metal/Metal.hpp" ]; then
  echo "metal-cpp $VERSION already in cache: $DEST"
  exit 0
fi

# Each download gets its own new, empty directory.
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/metal-cpp-fetch.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
URL="https://developer.apple.com/metal/cpp/files/metal-cpp_$VERSION.zip"
curl -fsSL -o "$STAGE/metal-cpp.zip" "$URL"
GOT="$(shasum -a 256 "$STAGE/metal-cpp.zip" | awk '{ print $1 }')"
if [ "$GOT" != "$WANT" ]; then
  echo "fetch_metal_cpp.sh: sha256 mismatch for $URL" >&2
  echo "  want $WANT" >&2
  echo "  got  $GOT" >&2
  exit 2
fi
mkdir "$STAGE/x"
unzip -q "$STAGE/metal-cpp.zip" -d "$STAGE/x"
if [ ! -f "$STAGE/x/metal-cpp/Metal/Metal.hpp" ]; then
  echo "fetch_metal_cpp.sh: archive has no metal-cpp/Metal/Metal.hpp" >&2
  exit 2
fi
mkdir -p "$DEST"
cp -R "$STAGE/x/metal-cpp/." "$DEST/"
echo "metal-cpp $VERSION -> $DEST"
