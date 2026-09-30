### Task 3: Triage the two `accessibility.md` failures (deferred item 7)

**Files:**
- Modify: `plugins/apple-studio/skills/apple-design/references/accessibility.md:29-37` and `:63-69`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md`

**Interfaces:**
- Consumes: `typecheck_snippets.py` from Task 2 (macOS default is correct here; do not add a directive).
- Produces: `apple-design` at 4/4 before Task 4 adds blocks.

- [ ] **Step 1: Classify before editing.** Write `triage.md` with one row per failure: snippet, compiler error (quote from `survey/typecheck-apple-design-baseline.log`), classification, reason.
  - `#1 Slider(value: $guess.red)`: **framing artifact** — `$guess` is never declared and the expressions sit at top level. **Plus a reference defect** — `accentColor(_:)` is deprecated from iOS 27.2 in favour of `tint(_:)` (`task-1-docc/live-check.log`).
  - `#2 @Environment(\.accessibilityReduceMotion)`: **framing artifact** — a property wrapper at top level. **Plus a reference defect** — `AnyView` in a ternary erases view identity; an `if`/`else` in a `@ViewBuilder` body is the SwiftUI form.

- [ ] **Step 2: Replace block #1** (lines 29–37) with:

```swift
struct ColorGuessRow: View {
    @State private var red = 0.5

    var body: some View {
        VStack {
            Slider(value: $red)
                .tint(.red)
                .accessibilityValue("red \(Int(red * 255))")

            Image("decorative-background")
                .resizable()
                .accessibilityHidden(true)
        }
    }
}
```

- [ ] **Step 3: Replace block #2** (lines 63–69) with:

```swift
struct StatusGlyph: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        if reduceMotion {
            Image(systemName: "circle.fill")
        } else {
            Image(systemName: "circle.fill")
                .symbolEffect(.pulse)
        }
    }
}
```

- [ ] **Step 4: Update the prose around both blocks.** The sentence before block #1 names no API that changed. The sentence before block #2 says "gate custom animations on the environment value" — keep it. Update the file's `verified:` line to add `re-checked 2026-09 (Phase 9: snippets reframed, accentColor → tint)`.

- [ ] **Step 5: Run the gate.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/typecheck.log | tail -1`. Expected: `TOTAL: 4/4 snippets typecheck clean`.

- [ ] **Step 6: Run the catalog gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design/references/accessibility.md $AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y
git commit -m "Phase 9 Task 3: triage and fix apple-design's two snippet failures

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

