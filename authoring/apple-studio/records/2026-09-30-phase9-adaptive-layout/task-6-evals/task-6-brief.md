### Task 6: Fixture screen, eval baseline, and the conditional description edit (deferred item 13)

**Files:**
- Create: `~/Projects/StudioFixture/StudioFixture/MailboxScreen.swift` (committed in the fixture's own repository)
- Modify: `~/Projects/StudioFixture/StudioFixture/ContentView.swift`
- Modify: `plugins/apple-studio/skills/apple-design/evals/triggers.md`
- Modify (conditional, Step 8): `plugins/apple-studio/skills/apple-design/SKILL.md:3`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/prompts.tsv`, `baseline/`, `after-edit/` (only if Step 8 runs)

**Interfaces:**
- Consumes: the routing line from Task 4; `run_evals.py` (runs each session with `cwd` set to the fixture, `run_evals.py:181`).
- Produces: a fixture with real UI that Task 8's probe copy also contains.

- [ ] **Step 1: Add the screen.** Create `~/Projects/StudioFixture/StudioFixture/MailboxScreen.swift` (the project uses folder-synchronized groups, so no project-file edit is needed). It uses only 27.0 APIs and must build for iOS, macOS, and visionOS:

```swift
import SwiftUI

struct MailboxScreen: View {
    @State private var selection: String?
    private let messages = ["Quarterly report", "Team lunch", "Build failed", "Design review"]

    var body: some View {
        TabView {
            Tab("Inbox", systemImage: "tray") {
                NavigationSplitView {
                    List(messages, id: \.self, selection: $selection) { message in
                        Text(message)
                    }
                    .navigationTitle("Inbox")
                    .toolbar {
                        ToolbarItem(placement: .primaryAction) {
                            Button("Compose", systemImage: "square.and.pencil") {}
                        }
                    }
                } detail: {
                    if let selection {
                        Text(selection)
                            .navigationTitle(selection)
                            .toolbar {
                                ToolbarItem { Button("Archive", systemImage: "archivebox") {} }
                                ToolbarItem { Button("Reply", systemImage: "arrowshape.turn.up.left") {} }
                                ToolbarItem { Button("Flag", systemImage: "flag") {} }
                            }
                    } else {
                        ContentUnavailableView("No Message Selected", systemImage: "envelope")
                    }
                }
            }
            Tab("Settings", systemImage: "gear") {
                Form {
                    Toggle("Notifications", isOn: .constant(true))
                }
            }
        }
    }
}

#Preview {
    MailboxScreen()
}
```

   In `ContentView.swift`, replace the body's `VStack { … }.padding()` with `MailboxScreen()`.

- [ ] **Step 2: Build for iOS.** `xcodebuild -project ~/Projects/StudioFixture/StudioFixture.xcodeproj -scheme StudioFixture -destination 'generic/platform=iOS Simulator' -derivedDataPath $TMPDIR/sf-dd build 2>&1 | tail -3`. Expected: `** BUILD SUCCEEDED **`.

- [ ] **Step 3: Build for macOS.** Same command with `-destination 'platform=macOS'`. Expected: `** BUILD SUCCEEDED **`. (Review Focus 5.) Save both tails to `task-6-evals/fixture-build.log`.

- [ ] **Step 4: Commit in the fixture repository.**

```bash
git -C ~/Projects/StudioFixture add StudioFixture/MailboxScreen.swift StudioFixture/ContentView.swift
git -C ~/Projects/StudioFixture commit -m "Add a mailbox screen with toolbars, tabs, and a split view for apple-design evals"
git -C ~/Projects/StudioFixture status --porcelain   # expect empty
rm -rf $TMPDIR/sf-dd
```

- [ ] **Step 5: Add the eval rows.** In `plugins/apple-studio/skills/apple-design/evals/triggers.md`, append under `## Should fire`:

```markdown
- "Make my app work on iPhone Duo"
- "My toolbar buttons disappear when the phone is closed"
- "Content gets cut off at the fold"
- "Should I use an arrangement view here?"
```

   and under `## Should NOT fire`:

```markdown
- "Screenshot the app on the iPhone Duo simulator"   (xcode-loop)
- "What screenshot sizes does the App Store need for iPhone Duo?"  (app-release)
```

- [ ] **Step 6: Write the sweep file.** Create `task-6-evals/prompts.tsv` with every row of `triggers.md` (existing 10 plus the 6 new), tab-separated as `id<TAB>apple-design<TAB>FIRE|NOFIRE<TAB>prompt`. IDs: `fire-1`…`fire-10`, `nofire-1`…`nofire-6`, in file order. Prompts copied exactly, without quotes or the trailing parenthetical.

- [ ] **Step 7: Run the baseline sweep with the description unchanged.**

```bash
python3 $AS/pipeline/run_evals.py $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/prompts.tsv $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/baseline
```

   Expected: a results table and `results.tsv` in `baseline/`; the fixture guard reports no writes (exit 1 with a `wrote` column otherwise — if so, the driver has already restored the tree; record which prompt wrote and continue). Record the pass rate, split into should-fire and should-NOT.

- [ ] **Step 8: Decide the description edit from the baseline, not from intuition.** For each failed row, read its session log and classify it per `.claude/rules/eval-harness.md`: `max_turns`, fixture-dependent (the prompt's referent is absent from the fixture), or routing miss (the session saw the skill list and chose another route). Write the classification to `task-6-evals/classification.md`.
  - If **no Duo should-fire row** (`fire-7`…`fire-10`) is a routing miss: do not edit the description. Record "description unchanged: baseline showed no Duo routing gap" and skip to Step 10.
  - If one or more is a routing miss: change `SKILL.md` line 3 `description:` to:

```
description: Apple Human Interface Guidelines conformance for iOS/iPadOS/macOS apps - layout and adaptive layout across sizes, poses, and foldables such as iPhone Duo, typography and Dynamic Type, color and materials, navigation and modality patterns, platform idioms, accessibility, and animation judgment. Use when designing or building UI, adapting a screen to a new size, pose, or fold, choosing a navigation or presentation pattern, styling views, making an app feel native, or fixing accessibility, Dynamic Type, or contrast issues. Not for brand identity or custom visual styling.
```

- [ ] **Step 9 (only if Step 8 edited the description): Sweep again.** Same command, output to `task-6-evals/after-edit`. Compare per row with `baseline/results.tsv`. A row that passed in the baseline and fails after the edit is a regression: revert the edit and record why.

- [ ] **Step 10: Update deferred item 13.** Append a `**Phase 9 (2026-09-30).**` paragraph: the fixture now has a real screen (commit hash from Step 4), the baseline and (if run) post-edit pass rates split by direction, the classification summary, and whether the description changed. State whether item 13 is resolved: resolved if every should-fire row (`fire-1`…`fire-10`) passes or is classified as non-routing and the should-NOT row "Design our brand color palette" passes; otherwise open, with the remaining rows named.

- [ ] **Step 11: Close checks, gates, and commit.**

```bash
git -C ~/Projects/StudioFixture status --porcelain   # expect empty
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design $AS/docs/deferred.md $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals
git commit -m "Phase 9 Task 6: fixture with real UI, apple-design eval baseline

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

