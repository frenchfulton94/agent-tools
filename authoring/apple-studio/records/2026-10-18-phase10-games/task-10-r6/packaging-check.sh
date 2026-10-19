#!/bin/bash
# Checks that the reference's packaging commands parse and produce the
# container they claim, on this machine, with no signing identity: the zip,
# the DMG by both hdiutil and diskutil, and an unsigned component pkg. Nothing
# is signed with an identity and nothing is uploaded.
#
#   packaging-check.sh <scratch-dir> > packaging.log 2>&1
#
# Run bundle.sh first. Outputs go to <scratch-dir>, never into a tracked path.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FIX="$(cd "$HERE/../../../pipeline/fixtures/metal-probe" && pwd)"
OUT="${1:?usage: packaging-check.sh <scratch-dir>}"
APP="$FIX/build/MetalProbe.app"
mkdir -p "$OUT"
rm -rf "$OUT/stage" "$OUT"/MetalProbe.*

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion), $(xcodebuild -version | head -1)"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
echo "\$APP is the fixture's build/MetalProbe.app; \$OUT is a scratch directory"

step() {   # step <title> <command...>
  echo
  echo "## $1"
  shift
  echo "\$ $*" | sed "s|$APP|\$APP|g; s|$OUT|\$OUT|g"
  "$@" 2>&1 | sed "s|$APP|\$APP|g; s|$OUT|\$OUT|g"
  echo "exit: ${PIPESTATUS[0]}"
}

step "Zip for upload" ditto -c -k --keepParent "$APP" "$OUT/MetalProbe.zip"
step "Zip contents" unzip -l "$OUT/MetalProbe.zip"
step "Stage the DMG folder" ditto "$APP" "$OUT/stage/MetalProbe.app"
step "DMG with hdiutil (UDZO)" hdiutil create -srcfolder "$OUT/stage" -volname MetalProbe -format UDZO -ov "$OUT/MetalProbe-hdiutil.dmg"
step "Verify the hdiutil DMG" hdiutil verify "$OUT/MetalProbe-hdiutil.dmg"
step "DMG with diskutil (UDZO)" diskutil image create from --format UDZO --volumeName MetalProbe "$OUT/stage" "$OUT/MetalProbe-diskutil.dmg"
step "Verify the diskutil DMG" hdiutil verify "$OUT/MetalProbe-diskutil.dmg"
step "Image format, hdiutil DMG" sh -c "diskutil image info '$OUT/MetalProbe-hdiutil.dmg' | grep -i -E 'format'"
step "Image format, diskutil DMG" sh -c "diskutil image info '$OUT/MetalProbe-diskutil.dmg' | grep -i -E 'format'"
step "DMG with diskutil, default format" diskutil image create from --volumeName MetalProbe "$OUT/stage" "$OUT/MetalProbe-default.dmg"
step "Image format, default" sh -c "diskutil image info '$OUT/MetalProbe-default.dmg' | grep -i -E 'format'"
step "Component pkg, unsigned (the signed form adds --sign)" productbuild --component "$APP" /Applications "$OUT/MetalProbe.pkg"
step "pkg signature status" pkgutil --check-signature "$OUT/MetalProbe.pkg"
step "Leftover mounts (expected: none)" sh -c "hdiutil info | grep -c MetalProbe"
