### Task 7: Compile gate against the iOS 27.1 SDK (needs Xcode 27.1 beta)

**Files:**
- Modify: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md` (fix any failing snippet or wrong name; fill the header's SDK build)
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/{sdk.log,typecheck.log,names.log}`

**Interfaces:**
- Consumes: the directive (Task 2); the reference (Task 4).
- Produces: a clean `apple-design` gate that Task 9 re-runs.

- [ ] **Step 1: Confirm the SDK, and stop if it is missing.**

```bash
{ xcode-select -p; xcodebuild -version; xcrun --sdk iphoneos --show-sdk-version; } | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/sdk.log
```

   Expected: SDK version `27.1` or later. If it prints `27.0`, stop this task and tell the user the 27.1 beta is not installed or not selected; do not work around it.

- [ ] **Step 2: Run the gate.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/typecheck.log | tail -1`. Expected: `TOTAL: 8/8 snippets typecheck clean` (4 existing plus 4 new).

- [ ] **Step 3: Fix failures from the SDK, not from memory.** For each failure, find the real declaration in the shipped interface:

```bash
I="$(xcrun --sdk iphoneos --show-sdk-path)/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface"
grep -n "<the symbol from the diagnostic>" "$I" | head
```

   Correct the snippet to match the declaration. If a symbol the docs name is absent from the interface, remove the claim and record it in `typecheck.log` as documented-but-absent (the Phase 6 pattern). Re-run Step 2 until clean.

- [ ] **Step 4: Verify every name in prose, not only in snippets.** Snippets cover SwiftUI; the UIKit table and prose names are unchecked until this step.

```bash
SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
SW="$SDK/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface"
UK="$SDK/System/Library/Frameworks/UIKit.framework"
grep -o '`[A-Za-z][A-Za-z0-9_.]*' plugins/apple-studio/skills/apple-design/references/adaptive-layout.md \
  | tr -d '`' | awk -F. '{print $NF}' | sort -u | while read -r name; do
    if grep -qw "$name" "$SW" || grep -rqw "$name" "$UK/Headers" "$UK/Modules" 2>/dev/null; then
      echo "ok      $name"
    else
      echo "MISSING $name"
    fi
  done | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/names.log | grep MISSING
```

   Expected: only non-symbol words (file names like `adaptive-layout`, `xcode-loop`) listed as MISSING. For each real symbol listed, check its Objective-C spelling in the headers (for example `UIArrangementViewController` may appear under an `NS_SWIFT_NAME`), then correct or remove it. Record each resolution in `names.log`.

- [ ] **Step 5: Fill the header.** Replace `<build>` in the `verified:` line with the build from `sdk.log`, and replace `<every other URL…>` with the actual list of URLs cited.

- [ ] **Step 6: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design/references/adaptive-layout.md $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile
git commit -m "Phase 9 Task 7: adaptive-layout compiles against the iOS 27.1 SDK

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

