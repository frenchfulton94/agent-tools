#!/bin/bash
# Checks bundle.sh before R6: runs it, lints the Info.plist, runs the bundled
# binary for one frame, then ad hoc signs the bundle (identity "-", never a
# Developer ID identity) and verifies that signature. It ends by running
# bundle.sh again, so build/MetalProbe.app is left unsigned for R6.
#
#   bundle-check.sh > bundle.log 2>&1
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FIX="$(cd "$HERE/../../../pipeline/fixtures/metal-probe" && pwd)"
APP="$FIX/build/MetalProbe.app"
cd "$FIX" || exit 2

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion), $(xcodebuild -version | head -1)"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
echo "Paths below are relative to authoring/apple-studio/pipeline/fixtures/metal-probe"

step() {   # step <title> <command...>
  echo
  echo "## $1"
  shift
  echo "\$ $*" | sed "s|$FIX/||g"
  "$@" 2>&1 | sed "s|$FIX/||g"
  echo "exit: ${PIPESTATUS[0]}"
}

step "Build and bundle" ./bundle.sh
step "Bundle layout" find build/MetalProbe.app
step "Info.plist lint" plutil -lint build/MetalProbe.app/Contents/Info.plist
step "Info.plist identifier" plutil -extract CFBundleIdentifier raw -o - build/MetalProbe.app/Contents/Info.plist
step "Bundled binary architecture" lipo -archs build/MetalProbe.app/Contents/MacOS/MetalProbe
step "Bundled binary, one frame" build/MetalProbe.app/Contents/MacOS/MetalProbe render --frames 1
step "Signature as bundled (linker ad hoc on the binary only)" codesign -dv build/MetalProbe.app
step "Ad hoc sign the bundle (identity -)" codesign -s - -f -o runtime build/MetalProbe.app
step "Verify the ad hoc signature" codesign --verify --strict --verbose=2 build/MetalProbe.app
step "Display the ad hoc signature" codesign -dvv build/MetalProbe.app
step "Gatekeeper on the ad hoc bundle (expected: rejected)" spctl --assess -vv --type execute build/MetalProbe.app
step "Rebuild the bundle unsigned for R6" ./bundle.sh
step "Signature after the rebuild" codesign -dv build/MetalProbe.app
