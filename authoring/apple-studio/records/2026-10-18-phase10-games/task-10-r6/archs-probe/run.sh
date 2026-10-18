#!/bin/bash
# Which architectures does Xcode build for a generic macOS destination, at a
# deployment target of 26.0 and of 27.0, when ARCHS is left at its default?
#
#   run.sh <scratch-dir>
#
# The derived data goes to <scratch-dir>, never into a tracked path.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="${1:?usage: run.sh <scratch-dir>}"
cd "$HERE" || exit 2

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion), $(xcodebuild -version | head -1) ($(xcodebuild -version | tail -1))"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"

# case <name> <deployment target> [extra build setting]
probe() {
  name="$1"; target="$2"; shift 2
  dd="$SCRATCH/dd-$name"
  echo
  echo "## MACOSX_DEPLOYMENT_TARGET=$target ${*:-(ARCHS not set)}"
  echo "\$ xcodebuild build -scheme ArchsProbe -destination 'generic/platform=macOS' -configuration Release -derivedDataPath <scratch>/dd-$name MACOSX_DEPLOYMENT_TARGET=$target $*"
  xcodebuild build -scheme ArchsProbe -destination 'generic/platform=macOS' \
    -configuration Release -derivedDataPath "$dd" \
    MACOSX_DEPLOYMENT_TARGET="$target" "$@" > "$SCRATCH/build-$name.log" 2>&1
  echo "exit: $?"
  grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$SCRATCH/build-$name.log"
  grep -i -E 'x86_64|architecture' "$SCRATCH/build-$name.log" | grep -i -E 'warning|ignor|skip' | sort -u | head -5
  bin="$(find "$dd/Build/Products" -type f -name ArchsProbe -perm -u+x | head -1)"
  echo "\$ lipo -archs ${bin#$dd/}"
  lipo -archs "$bin"
}
probe t26 26.0
probe t27 27.0
probe t27-x86 27.0 "ARCHS=arm64 x86_64"
probe t26-arm 26.0 "ARCHS=arm64"

echo
echo "## ARCHS_STANDARD and the x86_64 deployment range in Xcode's macOS architecture spec"
spec="/Applications/Xcode.app/Contents/SharedFrameworks/SwiftBuild.framework/Versions/A/PlugIns/SWBBuildService.bundle/Contents/PlugIns/SWBApplePlatformPlugin.bundle/Contents/Frameworks/SWBApplePlatform.framework/Versions/A/Resources/macOSArchitectures.xcspec"
echo "\$ grep -n -e RealArchitectures -e DeploymentTargetRange -e 'Identifier = \"x86_64\"' SWBApplePlatform.framework/Resources/macOSArchitectures.xcspec"
grep -n -e 'RealArchitectures' -e 'DeploymentTargetRange' -e 'Identifier = "x86_64"' "$spec"
