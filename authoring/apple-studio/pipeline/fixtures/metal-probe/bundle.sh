#!/bin/bash
# Wraps the release MetalProbe in an app bundle, build/MetalProbe.app, for the
# Phase 10 R6 notarization run (app-release/references/direct-distribution.md).
#
#   bundle.sh        # builds release, writes build/MetalProbe.app, prints its path
#
# The bundle is left unsigned apart from the linker's ad hoc signature on the
# binary. Signing with a Developer ID identity is a separate, documented step,
# so this script never chooses an identity. build/ is gitignored.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

swift build -c release --product MetalProbe >&2
BIN=.build/release/MetalProbe
[ -x "$BIN" ] || { echo "bundle.sh: $BIN is missing after the build" >&2; exit 2; }

APP=build/MetalProbe.app
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
# ditto, not cp: it is the copy tool Apple's distribution pages specify.
ditto "$BIN" "$APP/Contents/MacOS/MetalProbe"
printf 'APPL????' > "$APP/Contents/PkgInfo"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleExecutable</key>
	<string>MetalProbe</string>
	<key>CFBundleIdentifier</key>
	<string>dev.frenchfultonjr.apple-studio.metal-probe</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>MetalProbe</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0.0</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>LSMinimumSystemVersion</key>
	<string>26.0</string>
</dict>
</plist>
PLIST

plutil -lint "$APP/Contents/Info.plist" >&2
echo "$HERE/$APP"
