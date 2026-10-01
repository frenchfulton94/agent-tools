### Task 8: Runtime probe R1–R4 and the `xcode-loop` pose section (needs Xcode 27.1 beta)

**Files:**
- Create: `$AS/pipeline/fixtures/duo-probe/DuoProbeView.swift`
- Create: `$AS/pipeline/fixtures/duo-probe/run.sh`
- Modify: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md` (cite R1–R4)
- Modify: `plugins/apple-studio/skills/xcode-loop/references/headless-commands.md:1,6-7` and append a section
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe/` (discovery log, screenshots, unified-log extracts, `results.md`)

**Interfaces:**
- Consumes: Task 7's clean reference; the fixture (Task 6).
- Produces: runtime evidence for R1–R4; the `xcode-loop` pose instructions `adaptive-layout.md` § Checking a layout on iPhone Duo points to.

- [ ] **Step 1: Discover what the simulator offers.** Run and save everything to `task-8-probe/discovery.log`:

```bash
xcrun simctl list devicetypes | grep -i -E "duo|fold"
xcrun simctl list runtimes | grep -i ios
xcrun simctl help 2>&1 | grep -i -E "pose|posture|fold|hinge|display"
xcrun simctl help io 2>&1 | grep -i -E "pose|posture|fold|display"
```

   Classify the result as exactly one of: **A** — a Duo device type exists and `simctl` sets poses; **B** — a Duo device type exists, poses only through Device Hub or the Simulator GUI; **C** — no Duo device type. Write the classification and the exact command or menu path for poses to `discovery.log`. If **C**: skip to Step 7 and mark R1–R4 "documented, not runtime-checked".

- [ ] **Step 2: Create the device.** `xcrun simctl create "Duo Probe" "<device type identifier from Step 1>" "<iOS 27.1 runtime identifier>"`. Record the UDID.

- [ ] **Step 3: Write the probe view.** Create `$AS/pipeline/fixtures/duo-probe/DuoProbeView.swift`:

```swift
import SwiftUI
import os

private let probeLog = Logger(subsystem: "dev.frenchfultonjr.duoprobe", category: "probe")

/// Phase 9 runtime probe. Each label names the claim it checks; the unified
/// log carries the same values so a pose change is recorded even without a
/// screenshot.
struct DuoProbeView: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge
    @Environment(\.horizontalSizeClass) private var widthClass
    @State private var showSheet = false

    var body: some View {
        NavigationStack {
            GeometryReader { proxy in
                let divisions = proxy.reservedRegions(kind: .division, options: .includeInactive)
                let active = divisions.map(\.isActive)
                VStack(alignment: .leading, spacing: 12) {
                    Text("R1 toolbarVerticalEdge: \(String(describing: barEdge))")
                    Text("width class: \(String(describing: widthClass))  size: \(Int(proxy.size.width))×\(Int(proxy.size.height))")
                    Text("R3 divisions: \(divisions.count)  active: \(active.description)")
                    Button("R4 open sheet") { showSheet = true }
                }
                .padding()
                .onChange(of: active, initial: true) { _, value in
                    probeLog.log("R3 active=\(value.description, privacy: .public) count=\(divisions.count)")
                }
                .onChange(of: String(describing: barEdge), initial: true) { _, value in
                    probeLog.log("R1 edge=\(value, privacy: .public) size=\(Int(proxy.size.width))x\(Int(proxy.size.height))")
                }
            }
            .navigationTitle("Duo probe")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Share", systemImage: "square.and.arrow.up") {}
                }
                ToolbarItem(placement: .secondaryAction) {
                    Button("R2 TitleOnly") {}
                }
                ToolbarItem(placement: .secondaryAction) {
                    Button("R2 WithIcon", systemImage: "star") {}
                }
            }
        }
        .sheet(isPresented: $showSheet) { SheetProbe() }
    }
}

private struct SheetProbe: View {
    @State private var disableVertical = false
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        NavigationStack {
            Form {
                Text("R4 sheet toolbarVerticalEdge: \(String(describing: barEdge))")
                Toggle("toolbarVerticalBehavior(.disabled)", isOn: $disableVertical)
            }
            .navigationTitle("Sheet")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", systemImage: "checkmark") {}
                }
            }
            .toolbarVerticalBehavior(disableVertical ? .disabled : .automatic)
        }
    }
}
```

   If it fails to compile, fix it from the shipped interface as in Task 7 Step 3, not from memory.

- [ ] **Step 4: Write the run script.** Create `$AS/pipeline/fixtures/duo-probe/run.sh`:

```bash
#!/bin/bash
# Phase 9 Duo probe. Builds a scratch copy of StudioFixture with DuoProbeView
# as its root and installs it on the named simulator. Never touches
# ~/Projects/StudioFixture itself.
# Usage: run.sh <simulator-udid> <out-dir>
set -euo pipefail
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
```

   `chmod +x` it. Run: `$AS/pipeline/fixtures/duo-probe/run.sh <UDID> $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe`. Expected: `** BUILD SUCCEEDED **` in `build.log` and a `<bundle-id>: <pid>` line.

- [ ] **Step 5: Walk the poses.** For each state in this table, set it (by the Step 1 command or GUI path), wait two seconds, then capture `xcrun simctl io <UDID> screenshot task-8-probe/<state>.png`:

| State | Display | Pose |
|---|---|---|
| `outer-portrait` | outer | closed, portrait |
| `outer-landscape` | outer | closed, landscape |
| `inner-portrait` | inner | fully open, portrait |
| `inner-landscape` | inner | fully open, landscape |
| `inner-partial` | inner | partly folded |
| `outer-sheet` | outer | closed, portrait, sheet open |
| `outer-sheet-disabled` | outer | as above, toggle on |

   After the walk: `xcrun simctl spawn <UDID> log show --last 15m --predicate 'subsystem == "dev.frenchfultonjr.duoprobe"' > task-8-probe/unified.log`.

- [ ] **Step 6: Judge each claim against its evidence.** Write `task-8-probe/results.md`, one row per claim, verdict `CONFIRMED`, `CONTRADICTED`, or `NOT CHECKED`, with the screenshot or `unified.log` line that decides it:
  - **R1:** `edge` non-nil in `outer-portrait`, `outer-landscape`, `inner-landscape`; nil in `inner-portrait`.
  - **R2:** in a state with a vertical bar, "R2 WithIcon" appears in the vertical bar or its overflow, and "R2 TitleOnly" does not appear in the vertical bar.
  - **R3:** `active=[true]` only in `inner-partial`; `[false]` (or no active division) in fully open and closed states.
  - **R4:** `outer-sheet` shows the sheet's bar vertical and a non-nil sheet edge; `outer-sheet-disabled` shows it horizontal.
   A `CONTRADICTED` claim means the reference is wrong: correct `adaptive-layout.md` to match the runtime, and quote the evidence line in the correction.

- [ ] **Step 7: Cite the evidence in the reference.** In `adaptive-layout.md`, after each of the four claims, add `(runtime-checked 2026-09, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md)` or, for `NOT CHECKED` / discovery class C, `(documented, not runtime-checked)`. Re-run Task 7 Step 2; expect the same clean TOTAL.

- [ ] **Step 8: Add the `xcode-loop` pose section (deferred item 12 fires here).**
  - Replace `headless-commands.md` lines 6–7 (`Verified against a Multiplatform SwiftUI app fixture (\`~/Projects/StudioFixture\`, scheme\n\`StudioFixture\`, one target for iOS + macOS, Swift Testing unit tests).`) with `Verified against a multiplatform SwiftUI fixture app (one target for iOS + macOS, Swift Testing unit tests).`
  - Append `## 9. iPhone Duo — displays and poses` containing only what Step 1 and Step 5 verified: for class A, the exact `simctl` pose commands with their observed output; for class B, the Device Hub or Simulator menu path, stated plainly as not scriptable, followed by the screenshot command from § 7; for class C, one sentence that the Xcode 27.1 beta simulator had no iPhone Duo device type as of 2026-09. Commands not run do not go in this file (the file's own rule).
  - Append to its `verified:` line: `; § 9 verified 2026-09 against Xcode 27.1 beta (<build>), by execution`.

- [ ] **Step 9: Clean up.** `xcrun simctl shutdown <UDID>; xcrun simctl delete <UDID>; rm -rf "$(cat $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe/workdir.txt)"`. Then `xcrun simctl list devices booted` → expect no device, and `git -C ~/Projects/StudioFixture status --porcelain` → expect empty. Delete `workdir.txt` from the record (it names a temp path).

- [ ] **Step 10: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add $AS/pipeline/fixtures/duo-probe plugins/apple-studio/skills/apple-design/references/adaptive-layout.md plugins/apple-studio/skills/xcode-loop/references/headless-commands.md $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe
git commit -m "Phase 9 Task 8: runtime probe of four vertical-bar and fold claims; Duo poses in xcode-loop

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

