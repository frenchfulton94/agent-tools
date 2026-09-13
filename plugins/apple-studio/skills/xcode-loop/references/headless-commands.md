> verified: 2026-08 against Xcode 27.0 beta, by execution
> sources: none (empirical)

# Headless build/test/run/screenshot commands

Verified against a Multiplatform SwiftUI app fixture (`~/Projects/StudioFixture`, scheme
`StudioFixture`, one target for iOS + macOS, Swift Testing unit tests). Every command below
was actually run and its representative output shape captured. Commands not verified here
do not belong in this file — see `mcpbridge.md` for the non-headless alternative.

## Known noise (harmless, do not treat as failure)

Xcode 27.0 beta prints this stderr line on `build` and `test` invocations, immediately, before
any real work happens — and the command still succeeds:

```
2026-08-03 ... xcodebuild[PID:TID] [MT] IDERunDestination: Supported platforms for the
buildables in the current scheme is empty.
```

During `test` runs you'll also see repeated harmless lines like:

```
[MT] IDELaunchParametersSnapshot: debugger version lookup failed for path '<nil>': noURL
[MT] IDELaunchParametersSnapshot: no debugger version
```

Neither indicates failure. Judge success by exit code and the `** BUILD SUCCEEDED **` /
`Test suite ... passed` / `-resultBundlePath` output, not by stderr being clean.

## 1. Discover schemes and targets

```bash
cd <project-dir>
xcodebuild -list -json
```

Output shape:

```json
{
  "project" : {
    "configurations" : ["Debug", "Release"],
    "name" : "StudioFixture",
    "schemes" : ["StudioFixture"],
    "targets" : ["StudioFixture", "StudioFixtureTests", "StudioFixtureUITests"]
  }
}
```

Never guess the scheme name — read it from here.

## 2. Discover available runtimes and devices

```bash
xcrun simctl list devices available --json | jq '.devices | keys'
```

Output shape (one key per installed iOS runtime):

```json
["com.apple.CoreSimulator.SimRuntime.iOS-26-5", "com.apple.CoreSimulator.SimRuntime.iOS-27-0"]
```

To get concrete device names/UDIDs for a runtime:

```bash
xcrun simctl list devices available -j | \
  jq -r '.devices["com.apple.CoreSimulator.SimRuntime.iOS-27-0"][] | "\(.name) | \(.udid) | \(.state)"'
```

Use a `name` from this list (e.g. `iPhone 17`) in destination strings — don't hardcode UDIDs,
they vary per machine.

## 3. Choose a destination string

- iOS build (no simulator needed to boot, just compiles for the platform):
  `generic/platform=iOS Simulator`
- iOS test/run (needs a concrete device to execute on):
  `platform=iOS Simulator,name=iPhone 17`
- macOS build/test/run: `platform=macOS`

## 4. Build

```bash
xcodebuild build -scheme StudioFixture -destination 'generic/platform=iOS Simulator' -quiet
```

```bash
xcodebuild build -scheme StudioFixture -destination 'platform=macOS' -quiet
```

Both exit 0 with only the `IDERunDestination` noise line on stderr; `-quiet` suppresses the
rest. On real failure, `-quiet` still surfaces `error:` lines — show those verbatim, not a
summary.

To get a built product you can install/launch, add `-derivedDataPath`:

```bash
xcodebuild -scheme StudioFixture -destination 'platform=iOS Simulator,name=iPhone 17' \
  -derivedDataPath /tmp/sfdd build
```

```bash
xcodebuild -scheme StudioFixture -destination 'platform=macOS' \
  -derivedDataPath /tmp/sfdd-mac build
```

Both end with `** BUILD SUCCEEDED **`; product lands at
`/tmp/sfdd/Build/Products/Debug-iphonesimulator/StudioFixture.app` (iOS) or
`/tmp/sfdd-mac/Build/Products/Debug/StudioFixture.app` (macOS).

## 5. Test + parse results

```bash
xcodebuild test -scheme StudioFixture \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  -resultBundlePath /tmp/sf.xcresult -quiet
```

```bash
xcodebuild test -scheme StudioFixture -destination 'platform=macOS' \
  -resultBundlePath /tmp/sf-macos.xcresult -quiet
```

Both print `Writing result bundle at path: ...`, then per-test lines like:

```
Test case 'StudioFixtureTests/example()' passed on 'Clone 1 of iPhone 17 - StudioFixture (...)' (0.000 seconds)
```

`-resultBundlePath` must point at a path that does not already exist. Verified: re-running
against an existing bundle path (empty dir or a real prior `.xcresult`, both tried) fails
immediately, before any build/test work starts, with exit 64:

```
xcodebuild: error: Existing file at -resultBundlePath "/tmp/sf-collision.xcresult"
```

Delete/rename any stale bundle first (`rm -rf <path>.xcresult`).

Parse the bundle. The brief's guessed syntax (`xcresulttool get test-results summary --path`)
matched Xcode 27's actual CLI exactly — no correction needed, but note `xcresulttool get
object` (the old default form) is now deprecated in favor of the `test-results`/`test-report`
family; discovered via `xcrun xcresulttool get --help` and `get test-results --help`:

```bash
xcrun xcresulttool get test-results summary --path /tmp/sf.xcresult
```

Output shape (same on macOS, just a different `device` block):

```json
{
  "devicesAndConfigurations" : [ { "device" : { "deviceName" : "iPhone 17", "platform" : "iOS Simulator", "osVersion" : "27.0" }, "passedTests" : 3, "failedTests" : 0 } ],
  "expectedFailures" : 0,
  "failedTests" : 0,
  "passedTests" : 3,
  "result" : "Passed",
  "testFailures" : [],
  "totalTestCount" : 3
}
```

Check `"result"` and `"failedTests"`; walk `"testFailures"` for details on a red run.

## 6. Run in the iOS simulator

Boot, wait for it to actually be ready (don't sleep-guess), install, launch:

```bash
xcrun simctl boot "iPhone 17"
xcrun simctl bootstatus "iPhone 17"
```

`boot` returns immediately with exit 0 and no output on a cold boot. Verified: re-running
`boot` against a device that's already booted exits 149 (non-zero — do not treat a nonzero
exit alone as failure here) and prints:

```
An error was encountered processing the command (domain=com.apple.CoreSimulator.SimError, code=405):
Unable to boot device in current state: Booted
```

Treat that specific message as success (device is already in the desired state), not a real
error — check the message, not just the exit code. `bootstatus` blocks and streams
`Status=N, isTerminal=NO/YES` lines, ending with `Finished` when the simulator is actually
interactive — that's the real "ready" signal, not `boot` returning.

```bash
xcrun simctl install booted /tmp/sfdd/Build/Products/Debug-iphonesimulator/StudioFixture.app
```

Exit 0, no output on success.

Get the bundle id to launch with:

```bash
plutil -p /tmp/sfdd/Build/Products/Debug-iphonesimulator/StudioFixture.app/Info.plist | grep CFBundleIdentifier
```

```bash
xcrun simctl launch booted <bundle-id>
```

Prints `<bundle-id>: <pid>` on success, e.g. `dev.frenchfultonjr.StudioFixture: 76202`.

## 7. Screenshot — iOS simulator

```bash
xcrun simctl io booted screenshot /tmp/sf.png && file /tmp/sf.png
```

Prints `Wrote screenshot to: /tmp/sf.png`; `file` confirms `PNG image data, <w> x <h>,
8-bit/color RGBA, non-interlaced`. Give the simulator a beat after `launch` before
screenshotting (UI needs a frame or two to draw) — a couple seconds is enough, no need for a
long sleep.

## 8. Run + screenshot — macOS

There's no simulator step for macOS; launch the built `.app` directly and capture the real
display:

```bash
open /tmp/sfdd-mac/Build/Products/Debug/StudioFixture.app
sleep 3   # let the window draw
screencapture -x -D 1 /tmp/sf-macos.png
```

`-x` suppresses the capture sound; `-D 1` targets the main display explicitly — plain
`screencapture -x <file>` with no `-D` failed in this environment with `could not create
image from display` (exit 1, no file written), so always pass `-D 1` (or the target display
number from a multi-display setup). With `-D 1` it exits 0 and writes a full-screen PNG
(verified: 3024x1964 8-bit RGBA) showing the app's window. This captures the whole screen,
not just the app window — acceptable for a "did it draw" check; there is no verified
window-only capture command here.

Quit when done: `osascript -e 'tell application "StudioFixture" to quit'`.
