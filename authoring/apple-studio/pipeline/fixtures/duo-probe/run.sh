#!/bin/bash
# Phase 9 Duo probe. Builds a scratch copy of StudioFixture with DuoProbeView
# as its root and installs it on the named simulator. Never touches
# ~/Projects/StudioFixture itself.
# Usage: run.sh <simulator-udid> <out-dir>
set -euo pipefail
# The probe needs the iOS 27.1 SDK. xcode-select may point at an older Xcode
# and must not be changed, so pin the 27.1 beta toolchain for every
# xcodebuild, xcrun, and simctl call below.
export DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer"
UDID="$1"; OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
mkdir -p "$OUT"
cp -R "$HOME/Projects/StudioFixture" "$WORK/"
rm -rf "$WORK/StudioFixture/.git"
cp "$HERE/DuoProbeView.swift" "$WORK/StudioFixture/StudioFixture/"
sed -i '' 's/ContentView()/DuoProbeView()/' "$WORK/StudioFixture/StudioFixture/StudioFixtureApp.swift"
sed -i '' 's/IPHONEOS_DEPLOYMENT_TARGET = 27.0;/IPHONEOS_DEPLOYMENT_TARGET = 27.1;/' \
  "$WORK/StudioFixture/StudioFixture.xcodeproj/project.pbxproj"
xcodebuild -project "$WORK/StudioFixture/StudioFixture.xcodeproj" -scheme StudioFixture \
  -destination "id=$UDID" -derivedDataPath "$WORK/dd" build > "$OUT/build.log" 2>&1
APP="$WORK/dd/Build/Products/Debug-iphonesimulator/StudioFixture.app"
xcrun simctl boot "$UDID" 2>/dev/null || true   # "already booted" is fine; bootstatus is the real check
xcrun simctl bootstatus "$UDID"
xcrun simctl install "$UDID" "$APP"
BID="$(plutil -extract CFBundleIdentifier raw "$APP/Info.plist")"
xcrun simctl launch "$UDID" "$BID"
echo "$WORK" > "$OUT/workdir.txt"
echo "$BID" > "$OUT/bundle-id.txt"
