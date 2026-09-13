# apple-studio Phase 1: Architecture + Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first usable increment of the apple-studio plugin: four skills (`xcode-loop`, `swift-architecture`, `swift-concurrency`, `swift-testing`), the `apple-frameworks` skill (catalog + 16 primers), the `swift-reviewer` agent, and the stop-gate build hook — all verified against a real fixture app on Xcode 27.

**Architecture:** Knowledge skills carry distilled references (from the 10 converted books in `corpus/` + live Apple docs); workflow components (`xcode-loop`, reviewer, hook) consume them. Everything lives in `plugin/` per the repo layout in `docs/specs/2026-08-03-apple-studio-design.md`. Build order: toolchain/fixture → xcode-loop → distillation → knowledge skills → reviewer → hook → apple-frameworks → integration.

**Tech Stack:** Claude Code plugin (skills/agents/hooks), bash + jq, pandoc/pdftotext (already run), `xcodebuild`/`xcrun simctl`/`xcrun mcpbridge`, Xcode 27.0 beta on macOS 27.

## Global Constraints

- Repo: `~/Projects/apple-studio`. All paths below are relative to it unless absolute.
- Toolchain: Xcode 27.0 beta (`/Applications/Xcode-beta.app`). Never assume Xcode ≤26 behavior; verify every Xcode-specific claim by running it or fetching current docs.
- Stack baseline (CONVENTIONS.md): SwiftUI-first, Swift 6 strict concurrency, async/await, SPM, Swift Testing. Legacy (UIKit/Combine/XCTest/GCD) only under `## Maintaining older code:` headings.
- Live-docs-first: any Apple API claim in a committed reference must be checked against developer.apple.com fetched during the task, not memory. Docs win over books.
- Every reference file starts with the header block defined in CONVENTIONS.md (`> verified: 2026-08 against <urls>` / `> sources: <books>`).
- Never commit anything from `corpus/` (gitignored, copyrighted). Committed references are distilled guidance in our own words — no paragraphs copied from books.
- Hooks fail OPEN: every unexpected condition in a hook script exits 0.
- SKILL.md ≤ ~150 lines; knowledge depth goes in `references/`.
- Commit after every task (at minimum). Version bump to 0.2.0 happens only in Task 9.
- Fixture app: `~/Projects/StudioFixture` (created in Task 0; **Multiplatform** SwiftUI app — one target building for iOS and macOS — + Swift Testing unit tests). It is the verification target for Tasks 1, 6, 7, and 9. Platform-specific verification: commands and hooks are verified against BOTH `iOS Simulator` and `platform=macOS` destinations.

---

### Task 0: Toolchain + fixture app setup (user-assisted)

**Files:**
- No repo files. System state + `~/Projects/StudioFixture` (user-created, outside this repo).

**Interfaces:**
- Produces: active Xcode 27 toolchain (`xcodebuild -version` → `Xcode 27.0`); fixture project at `~/Projects/StudioFixture/StudioFixture.xcodeproj` with scheme `StudioFixture` and a Swift Testing unit-test target `StudioFixtureTests`. All later tasks assume these exist.

- [ ] **Step 1: Ask the user to activate Xcode 27**

Tell the user to run in-session (the `!` prefix runs it in the conversation):

```
! sudo xcode-select -s /Applications/Xcode-beta.app
```

- [ ] **Step 2: Verify the toolchain**

Run: `xcodebuild -version && xcrun mcpbridge --help 2>&1 | head -5`
Expected: `Xcode 27.0` on the first line; mcpbridge prints usage (any output that is not "unable to find utility"). If mcpbridge is absent on Xcode 27, note it in the task summary and continue — Task 1 documents it as unavailable.

- [ ] **Step 3: Ask the user to create the fixture app**

Ask the user to do this in Xcode (≈2 minutes): File → New → Project → **Multiplatform** → App. Product Name `StudioFixture`, Interface SwiftUI, Language Swift, Testing System: Swift Testing (include unit tests), save at `~/Projects/` so the project lands at `~/Projects/StudioFixture`. No git needed. (Multiplatform so iOS and macOS verification share one fixture.)

- [ ] **Step 4: Verify the fixture builds and tests headlessly**

```bash
cd ~/Projects/StudioFixture
xcodebuild -list -json | jq '.project.schemes'
xcodebuild build -scheme StudioFixture -destination 'generic/platform=iOS Simulator' -quiet && echo IOS_BUILD_OK
xcodebuild build -scheme StudioFixture -destination 'platform=macOS' -quiet && echo MACOS_BUILD_OK
xcodebuild test -scheme StudioFixture -destination 'platform=iOS Simulator,name=iPhone 17' -quiet && echo TEST_OK
```

Expected: schemes include `StudioFixture`; `IOS_BUILD_OK`; `MACOS_BUILD_OK`; `TEST_OK`. If the simulator name differs on Xcode 27, list available ones with `xcrun simctl list devices available | head -20` and use the first iPhone; record the working destination string — Tasks 1 and 7 reuse it.

---

### Task 1: `xcode-loop` skill

**Files:**
- Create: `plugin/skills/xcode-loop/SKILL.md`
- Create: `plugin/skills/xcode-loop/references/headless-commands.md`
- Create: `plugin/skills/xcode-loop/references/mcpbridge.md`
- Create: `plugin/skills/xcode-loop/evals/triggers.md`

**Interfaces:**
- Consumes: fixture app + verified destination string from Task 0.
- Produces: verified command patterns other tasks reuse verbatim — `BUILD_CMD` = `xcodebuild build -scheme <scheme> -destination 'generic/platform=iOS Simulator' -quiet`; `TEST_CMD` = `xcodebuild test -scheme <scheme> -destination '<verified destination>' -resultBundlePath <path>.xcresult`; screenshot flow via `xcrun simctl io booted screenshot <file>.png`. Task 7's hook and Task 9's verification use these.

- [ ] **Step 1: Verify every candidate command against the fixture** (before writing docs — the reference contains only commands that ran successfully on Xcode 27)

Run each; record exact working syntax and one line of representative output:

```bash
cd ~/Projects/StudioFixture
xcodebuild -list -json                                   # project discovery
xcrun simctl list devices available --json | jq '.devices | keys'   # runtimes
xcodebuild build -scheme StudioFixture -destination 'generic/platform=iOS Simulator' -quiet
xcodebuild build -scheme StudioFixture -destination 'platform=macOS' -quiet          # macOS side of the multiplatform target
xcodebuild test -scheme StudioFixture -destination '<verified destination>' -resultBundlePath /tmp/sf.xcresult -quiet
xcodebuild test -scheme StudioFixture -destination 'platform=macOS' -quiet           # tests on macOS too
xcrun xcresulttool get test-results summary --path /tmp/sf.xcresult   # result parsing (Xcode 27 syntax may differ; try `xcrun xcresulttool --help` and record what works)
xcrun simctl boot '<device name>' ; xcrun simctl bootstatus '<device name>'
xcodebuild -scheme StudioFixture -destination '<verified destination>' -derivedDataPath /tmp/sfdd build
xcrun simctl install booted /tmp/sfdd/Build/Products/Debug-iphonesimulator/StudioFixture.app
xcrun simctl launch booted <bundle-id from Info>          # get bundle id: plutil -p on the built app's Info.plist
xcrun simctl io booted screenshot /tmp/sf.png && file /tmp/sf.png
```

- [ ] **Step 2: Write `references/headless-commands.md`** — the verified commands from Step 1, organized as: discover → choose destination → build → test + parse results → run in simulator → screenshot. Each command with its verified output shape and the failure modes actually observed. Start with the CONVENTIONS.md header (`verified: 2026-08 against Xcode 27.0 beta, by execution`; `sources: none (empirical)`).

- [ ] **Step 3: Write `references/mcpbridge.md`** — setup (`claude mcp add --transport stdio xcode -- xcrun mcpbridge`; Xcode Settings → Intelligence → "Allow external agents to use Xcode tools"), when to prefer it (Xcode has the project open; project-aware edits/builds), fallback rule (headless commands are the default and the CI path). If Step 2 of Task 0 found mcpbridge missing, this file says so and records the check command (`xcrun mcpbridge --help`) so it can be re-verified on later betas.

- [ ] **Step 4: Write `SKILL.md`**

```markdown
---
name: xcode-loop
description: Build, test, run, and screenshot Apple-platform apps from the command line or via Xcode's MCP bridge. Use when the user asks to build or run an iOS/macOS app, run its tests, boot a simulator, capture app screenshots, or verify that a Swift change actually works.
---

# Xcode build/test/run loop

Two drive modes. Pick per session:
1. **Xcode MCP bridge** — if the `xcode` MCP server is connected and Xcode has the project open, prefer it. See `references/mcpbridge.md`.
2. **Headless CLI** — the default and the only CI option. Follow `references/headless-commands.md` exactly; every command there was verified on Xcode 27.

Core loop for verifying a change: build → run tests with a result bundle → parse the bundle → if UI-relevant, install+launch in a booted simulator and screenshot.

Rules:
- Discover schemes/destinations with the discovery commands first; never guess scheme names.
- Always pass `-quiet` for builds; full logs only when diagnosing a failure.
- On failure, show the actual `error:` lines, not a summary of them.
- Screenshots: boot → bootstatus → install → launch → `simctl io booted screenshot`.
```

- [ ] **Step 5: Write `evals/triggers.md`**

```markdown
# xcode-loop trigger evals
## Should fire
- "Build the app and make sure it compiles"
- "Run the test suite for BreeziTip"
- "Boot an iPhone simulator and screenshot the onboarding screen"
- "Did my change break anything? Verify it runs"
- "Install the app on a simulator and launch it"
## Should NOT fire
- "Explain actor isolation in Swift 6"          (swift-concurrency)
- "Review this diff for architecture problems"  (swift-reviewer)
- "What's the best way to store user settings?" (swift-architecture)
- "Write a test for the parser"                 (swift-testing — writing, not running)
```

- [ ] **Step 6: Validate and smoke-test loading**

Run: `claude plugin validate . --strict` (expect pass), then `claude --plugin-dir ./plugin -p "What skills do you have available? List names only." --max-turns 1` and confirm `xcode-loop` appears.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/xcode-loop && git commit -m "feat: xcode-loop skill with Xcode 27-verified commands"
```

---

### Task 2: Distillation infrastructure (prompt + chapter maps)

**Files:**
- Create: `pipeline/distill-prompt.md`
- Create: `pipeline/maps/swift-architecture.md`, `pipeline/maps/swift-concurrency.md`, `pipeline/maps/swift-testing.md`

**Interfaces:**
- Consumes: `corpus/*.md`, `corpus/*.toc.md`, `corpus/*.txt` (already generated).
- Produces: the distillation prompt text and per-skill chapter maps that Tasks 3–5 feed to subagents verbatim. Map format: one `## <corpus-file>` section per book, bullet lines `- L<start>–L<end>: <chapter title> → <target reference file>`.

- [ ] **Step 1: Write `pipeline/distill-prompt.md`** (the exact prompt Tasks 3–5 give each distillation subagent, with `{PLACEHOLDER}` slots filled per dispatch):

```markdown
You are distilling book chapters into a reference file for a Claude Code skill.

Read: {CORPUS_FILE} lines {START}-{END} (and any other ranges listed for this topic).
Target: {REFERENCE_FILE} for the {SKILL} skill. Topic: {TOPIC}.

Extract ONLY decision-grade guidance: principles, trade-offs, decision criteria,
checklists, canonical patterns, classic mistakes. Rules:
1. WORTH-IT: skip anything a strong Swift developer (or Claude) already reliably
   knows. No tutorials, no API walkthroughs, no history. If a chapter yields
   nothing above that bar, yield nothing.
2. BASELINE: write for SwiftUI + Swift 6 strict concurrency + Swift Testing.
   Material that only applies to UIKit/Combine/XCTest/GCD goes under a
   "## Maintaining older code: <topic>" heading or is dropped.
3. CURRENCY: flag every API-specific claim with [VERIFY: <claim>] — the
   dispatcher checks these against live docs before commit. Do not flag pure
   design judgment.
4. OWN WORDS: never copy sentences from the source. Cite as (Book, ch. N).
Output: markdown body only (no header block — the dispatcher adds it),
target 100–250 lines. Dense, imperative, example-light (short Swift snippets
only where a pattern is clearer as code).
```

- [ ] **Step 2: Build the three chapter maps.** For each map, read the relevant `corpus/*.toc.md` files (they contain `line:heading` pairs) and the PDF text files' visible structure (grep `^Chapter|^\d+\.` in the `.txt` files to locate chapters). Assign chapters to target reference files:

- `swift-architecture.md` map covers: `advanced-ios-app-architecture-v4-0-0.md` (all architecture chapters), `app-architecture-2018-05-07.txt` (MVC/MVVM/patterns chapters), `design-patterns-by-tutorials-v3-0-0.md` (only patterns relevant to SwiftUI apps: MVVM, delegation→closures, factory, coordinator, observer; skip Obj-C-era filler), `thinking-in-swiftui-2023-09-22.txt` (view trees, state, layout chapters) → targets from Task 3.
- `swift-concurrency.md` map covers: `modern-concurrency-in-swift-v2-0-0.md` (all), `concurrency-by-tutorials-v3-0-0.md` (all), `swift-concurrency-by-example-2024-11-15-pdf.txt` (all), `combine-asynchronous-programming-with-swift-v4-0-0.md` (ONLY chapters useful for Combine→async migration; everything else skipped) → targets from Task 4.
- `swift-testing.md` map covers: `ios-test-driven-development-by-tutorials-v2-0-0.md` (all), `testing-swift-2025-05-15-pdf.txt` (all) → targets from Task 5.

Acceptance: every target reference file named in Tasks 3–5 appears in a map with at least one source range; every range was checked to exist (`sed -n '<start>p' corpus/<file>` shows the chapter heading).

- [ ] **Step 3: Commit**

```bash
git add pipeline && git commit -m "feat: distillation prompt and Phase 1 chapter maps"
```

---

### Task 3: `swift-architecture` skill

**Files:**
- Create: `plugin/skills/swift-architecture/SKILL.md`
- Create: `plugin/skills/swift-architecture/references/architecture-patterns.md` (choosing/keeping an architecture; MVVM-vs-plain-SwiftUI; coordinator/router judgment; pattern-vs-ceremony)
- Create: `plugin/skills/swift-architecture/references/state-and-di.md` (state ownership, Observation vs ObservableObject, dependency injection without frameworks, environment)
- Create: `plugin/skills/swift-architecture/references/module-boundaries.md` (SPM module decomposition, feature isolation, protocol boundaries, when NOT to modularize)
- Create: `plugin/skills/swift-architecture/references/persistence.md` (SwiftData vs Core Data vs CloudKit sync vs files/UserDefaults; migration and testability implications — distilled mainly from live docs)
- Create: `plugin/skills/swift-architecture/references/existing-code.md` (working in shipped apps: seams, incremental refactors, legacy UIKit/Combine coexistence)
- Create: `plugin/skills/swift-architecture/evals/triggers.md`

**Interfaces:**
- Consumes: `pipeline/distill-prompt.md`, `pipeline/maps/swift-architecture.md` (Task 2).
- Produces: `references/` directory read by `swift-reviewer` (Task 6). File names above are load-bearing — Task 6 lists this exact directory.

- [ ] **Step 1: Dispatch distillation subagents** — one per reference file (parallel), each given `pipeline/distill-prompt.md` with slots filled from the chapter map. `persistence.md`'s subagent additionally fetches and distills from live docs: `https://developer.apple.com/documentation/swiftdata`, `https://developer.apple.com/documentation/coredata`, `https://developer.apple.com/documentation/cloudkit`, `https://developer.apple.com/documentation/foundation/userdefaults`.

- [ ] **Step 2: Resolve every `[VERIFY: …]` flag.** For each flagged claim, WebFetch the relevant developer.apple.com page; rewrite or delete the claim; none may remain in committed files (`grep -rn "VERIFY" plugin/skills/swift-architecture/references/` → empty).

- [ ] **Step 3: Add header blocks** to each reference per CONVENTIONS.md, listing the doc URLs actually checked and source books actually used.

- [ ] **Step 4: Write `SKILL.md`**

```markdown
---
name: swift-architecture
description: Architecture and code-structure judgment for Apple-platform apps - choosing an app architecture, state management and dependency injection in SwiftUI, module boundaries, persistence choice (SwiftData/Core Data/CloudKit/files), and working safely in existing shipped code. Use when designing a new app or feature, restructuring code, deciding where state or logic lives, choosing a persistence stack, or before large refactors.
---

# Swift app architecture

Before designing or restructuring, read the reference for the decision at hand:
- Choosing/keeping an architecture, pattern-vs-ceremony → `references/architecture-patterns.md`
- State ownership, DI, Observation → `references/state-and-di.md`
- Module/SPM decomposition → `references/module-boundaries.md`
- Storing data → `references/persistence.md`
- Changing shipped code → `references/existing-code.md`

Process: state the decision explicitly → read the matching reference → apply its
decision criteria to THIS app's size and constraints → prefer the simplest
structure the criteria allow (ceremony is a cost, not a virtue) → record
non-obvious choices in code comments only where the code cannot show the why.
```

- [ ] **Step 5: Write `evals/triggers.md`**

```markdown
# swift-architecture trigger evals
## Should fire
- "Where should this view's state live?"
- "Should I use SwiftData or Core Data for this app?"
- "Split this app into Swift packages"
- "I'm adding a big feature to my shipped app - how do I structure it?"
- "Is MVVM overkill for this screen?"
- "Design the module layout for a new iOS app"
## Should NOT fire
- "Fix this Sendable warning"              (swift-concurrency)
- "Build and run the app"                  (xcode-loop)
- "Write tests for the sync engine"        (swift-testing)
- "Does Apple have a framework for weather?" (apple-frameworks)
```

- [ ] **Step 6: Consume-test.** In a fresh session (`claude --plugin-dir ./plugin`), prompt: "I'm building a habit-tracking iOS app: 4 screens, iCloud sync later, solo project. Design the architecture and persistence." Confirm the skill fires, at least two reference files get read, and the answer applies their criteria (not generic advice). If a reference never loads or adds nothing, cut or merge it now.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/swift-architecture && git commit -m "feat: swift-architecture skill with distilled references"
```

---

### Task 4: `swift-concurrency` skill

**Files:**
- Create: `plugin/skills/swift-concurrency/SKILL.md`
- Create: `plugin/skills/swift-concurrency/references/strict-concurrency.md` (actor isolation, Sendable, global actors, isolation regions, fixing strict-concurrency errors by understanding them rather than annotating them away)
- Create: `plugin/skills/swift-concurrency/references/structured-concurrency.md` (Task/TaskGroup, cancellation discipline, AsyncSequence, bridging callbacks)
- Create: `plugin/skills/swift-concurrency/references/migration.md` (`## Maintaining older code:` GCD→async and Combine→async migration patterns)
- Create: `plugin/skills/swift-concurrency/evals/triggers.md`

**Interfaces:**
- Consumes: `pipeline/distill-prompt.md`, `pipeline/maps/swift-concurrency.md`.
- Produces: `references/` read by `swift-reviewer` (Task 6).

- [ ] **Step 1: Dispatch distillation subagents** — one per reference file, slots from the chapter map. `strict-concurrency.md`'s subagent additionally fetches `https://developer.apple.com/documentation/swift/concurrency` and `https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/` (the books predate Swift 6 strictness; the live docs are the authority on current semantics).

- [ ] **Step 2: Resolve every `[VERIFY: …]` flag** against live docs; `grep -rn "VERIFY" plugin/skills/swift-concurrency/references/` → empty.

- [ ] **Step 3: Add CONVENTIONS.md header blocks.**

- [ ] **Step 4: Write `SKILL.md`**

```markdown
---
name: swift-concurrency
description: Swift 6 concurrency correctness - actor isolation, Sendable conformance, structured concurrency, cancellation, and migrating GCD or Combine code to async/await. Use when writing or reviewing async Swift code, fixing strict-concurrency or Sendable errors, designing actor boundaries, or modernizing callback/Combine code.
---

# Swift concurrency

- Strict-concurrency errors, isolation design, Sendable → `references/strict-concurrency.md`
- Tasks, groups, cancellation, AsyncSequence → `references/structured-concurrency.md`
- Migrating GCD/Combine code → `references/migration.md`

Rules that always apply:
- A strict-concurrency error is a design signal. Diagnose which isolation
  domain the data belongs to BEFORE reaching for @unchecked Sendable,
  @preconcurrency, or nonisolated(unsafe) - those are documented last resorts.
- Every spawned Task needs an owner and a cancellation story.
- Never block an actor (or the main actor) on synchronous waiting.
```

- [ ] **Step 5: Write `evals/triggers.md`**

```markdown
# swift-concurrency trigger evals
## Should fire
- "Fix this 'capture of non-Sendable type' error"
- "Should this be an actor or a @MainActor class?"
- "Convert this Combine pipeline to async/await"
- "My async code deadlocks - help"
- "Design the concurrency for a sync engine that talks to CloudKit"
## Should NOT fire
- "Where should this state live?"     (swift-architecture)
- "Run the tests"                     (xcode-loop)
- "What does the HIG say about loading spinners?" (Phase 2)
```

- [ ] **Step 6: Consume-test.** Fresh session, prompt: "This class is `@unchecked Sendable` and I get random crashes. Fix it properly." with a 20-line class holding a mutable dictionary accessed from multiple Tasks (write the snippet inline in the prompt). Confirm skill fires, `strict-concurrency.md` is read, and the fix redesigns isolation instead of suppressing warnings.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/swift-concurrency && git commit -m "feat: swift-concurrency skill with distilled references"
```

---

### Task 5: `swift-testing` skill

**Files:**
- Create: `plugin/skills/swift-testing/SKILL.md`
- Create: `plugin/skills/swift-testing/references/swift-testing-framework.md` (@Test/@Suite, #expect/#require, parameterized tests, traits, migration notes from XCTest under a `## Maintaining older code:` heading)
- Create: `plugin/skills/swift-testing/references/what-to-test.md` (test targets per layer of a SwiftUI app: models/logic exhaustively, view models via behavior, views sparingly; what NOT to test)
- Create: `plugin/skills/swift-testing/references/test-doubles.md` (protocol-based doubles, no mocking frameworks, controlling time/network/persistence in tests)
- Create: `plugin/skills/swift-testing/evals/triggers.md`

**Interfaces:**
- Consumes: `pipeline/distill-prompt.md`, `pipeline/maps/swift-testing.md`.
- Produces: `references/` read by `swift-reviewer` (Task 6). TDD process itself stays with the superpowers TDD skill — SKILL.md must say so and carry only Swift/Xcode specifics.

- [ ] **Step 1: Dispatch distillation subagents** — one per reference file, slots from the chapter map. `swift-testing-framework.md`'s subagent additionally fetches `https://developer.apple.com/documentation/testing` (both books predate or barely cover Swift Testing; live docs are the authority).

- [ ] **Step 2: Resolve `[VERIFY: …]` flags**; grep → empty.

- [ ] **Step 3: Add CONVENTIONS.md header blocks.**

- [ ] **Step 4: Write `SKILL.md`**

```markdown
---
name: swift-testing
description: Swift Testing framework usage and test design for Apple-platform apps - what to test at each layer of a SwiftUI app, protocol-based test doubles without mocking frameworks, and parameterized tests with #expect. Use when writing or restructuring Swift tests, deciding what deserves a test, reviewing test quality, or migrating XCTest code.
---

# Swift testing

For the TDD process itself (red-green-refactor discipline), the superpowers
TDD skill governs; this skill carries the Swift specifics:
- Swift Testing syntax, suites, traits, parameterization → `references/swift-testing-framework.md`
- What to test per layer, and what not to → `references/what-to-test.md`
- Doubles, controlling time/network/storage → `references/test-doubles.md`

Rules:
- New tests use Swift Testing (@Test), never XCTest, unless the target already
  standardizes on XCTest.
- Run tests via the xcode-loop skill's verified commands.
- A test that cannot fail for a real reason gets deleted, not kept.
```

- [ ] **Step 5: Write `evals/triggers.md`**

```markdown
# swift-testing trigger evals
## Should fire
- "Write tests for this view model"
- "How do I fake the network layer in tests?"
- "Convert these XCTest cases to Swift Testing"
- "Is it worth testing this SwiftUI view?"
- "Parameterize this test over several inputs"
## Should NOT fire
- "Run the test suite"                (xcode-loop - running, not writing)
- "Fix this data race"                (swift-concurrency)
- "Design the app's module layout"    (swift-architecture)
```

- [ ] **Step 6: Consume-test.** Fresh session, prompt: "Add a `StreakCalculator` (given a list of completion dates, compute current streak) to StudioFixture with tests first." Confirm the skill fires alongside TDD discipline, tests use `@Test`/`#expect`, and they run green via xcode-loop commands.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/swift-testing && git commit -m "feat: swift-testing skill with distilled references"
```

---

### Task 6: `swift-reviewer` agent

**Files:**
- Create: `plugin/agents/swift-reviewer.md`
- Create: `pipeline/fixtures/flawed/FlawedFeature.swift` (seeded review fixture, dev-time only)

**Interfaces:**
- Consumes: the three `references/` directories from Tasks 3–5 (exact paths in the agent body below).
- Produces: `apple-studio:swift-reviewer` agent, invoked after implementing Swift code.

- [ ] **Step 1: Write `plugin/agents/swift-reviewer.md`**

```markdown
---
name: swift-reviewer
description: Reviews Swift diffs or modules against apple-studio standards - architecture boundaries, Swift 6 concurrency safety, and test coverage. Use after implementing or changing Swift code, before committing Apple-platform work, or when the user asks for a Swift code review.
tools: Read, Grep, Glob, Bash
---

You are a senior Apple-platform reviewer. You review against written standards,
not taste.

Process:
1. Identify the review target: the diff (`git diff` / `git diff --staged`) or
   the files named in your prompt. Read every changed file fully.
2. Load the standards. Read ALL files in:
   - ${CLAUDE_PLUGIN_ROOT}/skills/swift-architecture/references/
   - ${CLAUDE_PLUGIN_ROOT}/skills/swift-concurrency/references/
   - ${CLAUDE_PLUGIN_ROOT}/skills/swift-testing/references/
3. Review three dimensions:
   - Architecture: state ownership, layer violations (e.g. networking or
     persistence in views), module boundary breaks, needless ceremony.
   - Concurrency: isolation correctness, Sendable suppressions
     (@unchecked, nonisolated(unsafe), @preconcurrency) without justification,
     unowned Tasks, missing cancellation, main-actor blocking.
   - Testing: changed behavior without a covering test; tests that assert
     nothing real; XCTest in new code.
4. Verify each finding against the code before reporting - no speculative
   findings. If unsure a finding is real, say so explicitly.

Output (your final message is the deliverable):
- Findings ranked [BLOCKER] > [MAJOR] > [MINOR] > [NIT], each with
  `file:line`, what is wrong, why (cite the reference file), and a concrete fix.
- End with: verdict (APPROVE / APPROVE WITH CHANGES / REQUEST CHANGES) and a
  one-line summary.
- If the code is clean, say so and stop. Never invent findings.
```

- [ ] **Step 2: Write the seeded fixture `pipeline/fixtures/flawed/FlawedFeature.swift`** containing exactly three planted flaws:

```swift
import SwiftUI

// Flaw 1 (architecture): view performs networking + parsing inline.
struct ProfileView: View {
    @State private var name = ""
    var body: some View {
        Text(name).task {
            let (data, _) = try! await URLSession.shared.data(
                from: URL(string: "https://api.example.com/profile")!)
            name = String(data: data, encoding: .utf8) ?? ""
        }
    }
}

// Flaw 2 (concurrency): mutable shared state, data race suppressed.
final class SessionCache: @unchecked Sendable {
    static let shared = SessionCache()
    var entries: [String: String] = [:]
    func store(_ key: String, _ value: String) { entries[key] = value }
}

// Flaw 3 (testing): behavior-bearing logic, no test anywhere in the fixture.
struct DiscountEngine {
    func discount(for total: Double) -> Double {
        if total > 100 { return total * 0.9 }
        return total
    }
}
```

- [ ] **Step 3: Verify the reviewer finds all three.** Fresh session: `claude --plugin-dir ./plugin -p "Use the swift-reviewer agent to review pipeline/fixtures/flawed/FlawedFeature.swift"`. Expected: findings cover (1) networking in view [architecture], (2) `@unchecked Sendable` data race [concurrency, BLOCKER], (3) untested `DiscountEngine` [testing]; each cites a reference file. If any flaw is missed, strengthen the corresponding reference (the gap is knowledge, not prompt) and re-run.

- [ ] **Step 4: Commit**

```bash
git add plugin/agents pipeline/fixtures && git commit -m "feat: swift-reviewer agent + seeded review fixture"
```

---

### Task 7: Stop-gate build hook

**Files:**
- Create: `plugin/hooks/hooks.json`
- Create: `plugin/hooks/scripts/track_swift_edits.sh`
- Create: `plugin/hooks/scripts/stop_gate.sh`

**Interfaces:**
- Consumes: BUILD_CMD pattern from Task 1; fixture app from Task 0.
- Produces: session-scoped edit markers in `${CLAUDE_PLUGIN_DATA}/stop-gate/<session>.edited`.

- [ ] **Step 1: Write `plugin/hooks/hooks.json`**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/track_swift_edits.sh\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/stop_gate.sh\"", "timeout": 180 }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Write `plugin/hooks/scripts/track_swift_edits.sh`** (fail-open everywhere)

```bash
#!/usr/bin/env bash
# Record Swift edits per session so the Stop gate knows a build check is due.
set -u
INPUT="$(cat)" || exit 0
command -v jq >/dev/null 2>&1 || exit 0
FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)" || exit 0
case "$FILE" in *.swift) ;; *) exit 0 ;; esac
SESSION="$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)" || exit 0
DATA="${CLAUDE_PLUGIN_DATA:-/tmp}/stop-gate"
mkdir -p "$DATA" 2>/dev/null || exit 0
printf '%s\n' "$FILE" >> "$DATA/$SESSION.edited" 2>/dev/null
exit 0
```

- [ ] **Step 3: Write `plugin/hooks/scripts/stop_gate.sh`** (fail-open everywhere; blocks only on a real red build)

```bash
#!/usr/bin/env bash
# Stop gate: if Swift files were edited this session, require a green build.
set -u
INPUT="$(cat)" || exit 0
command -v jq >/dev/null 2>&1 || exit 0
[ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && exit 0
SESSION="$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)" || exit 0
DATA="${CLAUDE_PLUGIN_DATA:-/tmp}/stop-gate"
MARKER="$DATA/$SESSION.edited"
[ -f "$MARKER" ] || exit 0
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)" || exit 0
[ -d "$CWD" ] || exit 0
DIR="$CWD"; PROJDIR=""
for _ in 1 2 3; do
  if find "$DIR" -maxdepth 1 \( -name '*.xcworkspace' -o -name '*.xcodeproj' \) -print -quit 2>/dev/null | grep -q .; then
    PROJDIR="$DIR"; break
  fi
  DIR="$(dirname "$DIR")"
done
[ -n "$PROJDIR" ] || exit 0
SCHEME="$( (cd "$PROJDIR" && xcodebuild -list -json 2>/dev/null) | jq -r '(.project.schemes // .workspace.schemes // [])[0] // empty' 2>/dev/null)" || exit 0
[ -n "$SCHEME" ] || exit 0
LOG="$DATA/$SESSION.build.log"
build_with() {
  (cd "$PROJDIR" && xcodebuild build -scheme "$SCHEME" -destination "$1" -quiet >"$LOG" 2>&1)
}
if build_with 'generic/platform=iOS Simulator'; then rm -f "$MARKER"; exit 0; fi
# A destination mismatch (macOS-only project) is not a code failure - retry macOS.
if grep -qiE 'unavailable|no destinations|does not support' "$LOG" 2>/dev/null; then
  if build_with 'platform=macOS'; then rm -f "$MARKER"; exit 0; fi
  # Neither platform applies to this project: fail open rather than false-block.
  grep -qiE 'unavailable|no destinations|does not support' "$LOG" 2>/dev/null && exit 0
fi
ERRS="$(grep -m 5 'error:' "$LOG" 2>/dev/null | tr '\n' ' ')"
jq -n --arg r "Stop gate: build failed after Swift edits. Fix before finishing. Errors: $ERRS" \
  '{decision: "block", reason: $r}' 2>/dev/null || exit 0
exit 0
```

- [ ] **Step 4: Make scripts executable + validate**

```bash
chmod +x plugin/hooks/scripts/*.sh
bash -n plugin/hooks/scripts/track_swift_edits.sh && bash -n plugin/hooks/scripts/stop_gate.sh
claude plugin validate . --strict
```
Expected: no syntax errors; validation passes (a malformed hooks.json stops the whole plugin loading).

- [ ] **Step 5: Red-build test.** In `~/Projects/StudioFixture`, run `claude --plugin-dir ~/Projects/apple-studio/plugin -p "Append '// touched' to ContentView.swift, then introduce the syntax error 'let x: = 5' at the top of the same file, and finish."` Expected: the Stop is blocked with the gate's reason containing the compile error. Then remove the bad line manually and confirm a follow-up session with a clean edit stops normally.

- [ ] **Step 6: Fail-open test.** Temporarily `chmod -x plugin/hooks/scripts/stop_gate.sh`, repeat a clean-edit session, confirm the session finishes without blocking; restore with `chmod +x`.

- [ ] **Step 7: Commit**

```bash
git add plugin/hooks && git commit -m "feat: stop-gate build hook (fail-open)"
```

---

### Task 8: `apple-frameworks` skill (catalog + primers)

**Files:**
- Create: `pipeline/generate_catalog.sh`
- Create: `plugin/skills/apple-frameworks/SKILL.md`
- Create: `plugin/skills/apple-frameworks/references/framework-catalog.md` (generated)
- Create: `plugin/skills/apple-frameworks/references/primers/<name>.md` × 16: `swiftdata`, `cloudkit`, `networking-urlsession`, `oslog`, `backgroundtasks`, `usernotifications`, `widgetkit`, `app-intents`, `activitykit`, `tipkit`, `storekit2`, `core-location`, `mapkit`, `photokit`, `swift-charts`, `foundation-models`
- Create: `plugin/skills/apple-frameworks/evals/triggers.md`

**Interfaces:**
- Consumes: live `https://developer.apple.com/tutorials/data/documentation/technologies.json`.
- Produces: catalog + primers; regeneration entry point `pipeline/generate_catalog.sh` (rerun each phase / after WWDC).

- [ ] **Step 1: Inspect the technologies JSON shape** (it is not guaranteed to match assumptions):

```bash
curl -fsSL https://developer.apple.com/tutorials/data/documentation/technologies.json -o /tmp/tech.json
jq 'keys' /tmp/tech.json
jq '[.references[] | select(.title != null)] | length' /tmp/tech.json 2>/dev/null || jq '.' /tmp/tech.json | head -50
```
Identify where the framework entries live (title + abstract + url per entry). Adjust the jq selector in Step 2 accordingly.

- [ ] **Step 2: Write `pipeline/generate_catalog.sh`** (selector adjusted to the real shape found in Step 1):

```bash
#!/usr/bin/env bash
# Regenerate the Apple framework catalog from the live Technologies index.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO_ROOT/plugin/skills/apple-frameworks/references/framework-catalog.md"
TMP="$(mktemp)"
curl -fsSL "https://developer.apple.com/tutorials/data/documentation/technologies.json" -o "$TMP"
{
  echo "# Apple framework catalog"
  echo
  echo "> generated: $(date +%Y-%m-%d) from the developer.apple.com Technologies index"
  echo "> regenerate: pipeline/generate_catalog.sh (rerun each phase and after WWDC)"
  echo
  jq -r '
    .references | to_entries[] | .value
    | select((.title // "") != "" and (.url // "") != "")
    | "- **\(.title)** — \((.abstract // []) | map(.text // "") | join("")) — https://developer.apple.com\(.url)"
  ' "$TMP" | sort -fu
} > "$OUT"
rm -f "$TMP"
echo "Wrote $OUT: $(grep -c '^- ' "$OUT") entries"
```

- [ ] **Step 3: Run and sanity-check**

Run: `pipeline/generate_catalog.sh && grep -iE "AlarmKit|Foundation Models|WeatherKit|TipKit" plugin/skills/apple-frameworks/references/framework-catalog.md`
Expected: several hundred entries; all four spot-check frameworks present (proves post-training frameworks are captured). If the count is wildly off (<200), the selector is wrong — return to Step 1.

- [ ] **Step 4: Generate the 16 primers via subagent fan-out.** One subagent per framework, prompt:

```
Write plugin/skills/apple-frameworks/references/primers/{NAME}.md for {FRAMEWORK}.
Fetch these live pages first: https://developer.apple.com/documentation/{DOCPATH}
(follow 1-2 obvious child pages for capabilities/entitlements if linked).
100-150 lines, durable judgment ONLY:
  ## What it is / when to reach for it   (vs. the obvious alternatives)
  ## Architecture integration            (where it sits in an app; testability)
  ## Privacy, entitlements, review       (Info.plist keys, capabilities, App Review implications)
  ## Availability                        (OS floors as stated by current docs)
  ## Classic pitfalls                    (the mistakes that cost days)
  ## Current docs                        (the URLs to fetch when implementing)
NO API walkthroughs, no code longer than 5 lines, no version-specific minutiae.
Start with the CONVENTIONS.md header block (verified: 2026-08 against the URLs you fetched; sources: live docs).
```
DOCPATH per primer: `swiftdata`, `cloudkit`, `foundation/urlsession`, `os/logging` (OSLog), `backgroundtasks`, `usernotifications`, `widgetkit`, `appintents`, `activitykit`, `tipkit`, `storekit`, `corelocation`, `mapkit`, `photokit`, `charts` (Swift Charts), `foundationmodels`.

- [ ] **Step 5: Write `SKILL.md`**

```markdown
---
name: apple-frameworks
description: Map of Apple's first-party frameworks - what exists, what each is for, and planning-grade guidance (privacy costs, entitlements, availability, pitfalls) for the frameworks most apps use. Use when designing a feature ("does Apple already ship this?"), choosing between a first-party framework and building custom, or assessing what adopting a framework will cost.
---

# Apple frameworks

1. Feature design starts with: does Apple already ship this? Check
   `references/framework-catalog.md` (generated from the live Technologies
   index - includes frameworks newer than model training data).
2. If a primer exists in `references/primers/`, read it before deciding to
   adopt - it carries the privacy/entitlement/review costs and pitfalls.
3. For implementation detail, ALWAYS fetch the framework's current
   developer.apple.com pages (live-docs-first rule, CONVENTIONS.md).
   The catalog answers "what exists"; primers answer "should I";
   live docs answer "how".
```

- [ ] **Step 6: Write `evals/triggers.md`**

```markdown
# apple-frameworks trigger evals
## Should fire
- "Does Apple have a native way to show tips/onboarding hints?"
- "Should I use WeatherKit or a third-party weather API?"
- "What will adopting HealthKit cost me in review/privacy terms?"
- "I need a live countdown on the lock screen - what's the right API?"
- "Add on-device AI text generation to my app"
## Should NOT fire
- "Fix this Sendable error"           (swift-concurrency)
- "Where should my models live?"      (swift-architecture)
- "Build the app"                     (xcode-loop)
```

- [ ] **Step 7: Consume-test.** Fresh session: "I want my habit app to show the current streak on the lock screen and in a home-screen widget. What's the right approach?" Expected: skill fires; answer routes through ActivityKit + WidgetKit primers, mentions their entitlement/availability constraints, and points to live docs for implementation.

- [ ] **Step 8: Commit**

```bash
git add pipeline/generate_catalog.sh plugin/skills/apple-frameworks && git commit -m "feat: apple-frameworks skill - generated catalog + 16 primers"
```

---

### Task 9: Integration verification + 0.2.0 release

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (version 0.1.0 → 0.2.0)
- Modify: `docs/specs/2026-08-03-apple-studio-design.md` (append a `## Phase 1 verification results` section recording outcomes)

**Interfaces:**
- Consumes: everything from Tasks 0–8.

- [ ] **Step 1: Run trigger-eval sampling.** For each of the five skills, run 3 "should fire" and 2 "should NOT fire" prompts from its `evals/triggers.md` via `claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2`, checking whether the skill was invoked. Record pass/fail per prompt. Any misfire → tighten that skill's `description` and re-run the failing prompt.

- [ ] **Step 2: Full validation**

Run: `claude plugin validate . --strict`
Expected: pass, zero warnings.

- [ ] **Step 3: End-to-end consume-test (spec item 6).** Fresh session in `~/Projects/StudioFixture` with the plugin loaded: "Add a settings screen with a daily-reminder toggle that persists, tests first." Expected observed behavior: swift-architecture consulted for persistence choice, swift-testing + TDD for tests, xcode-loop runs them, stop-gate passes on the green build, swift-reviewer approves the diff.

- [ ] **Step 4: Xcode Claude Agent install (spec item 7, user-assisted).** Ask the user to: open Xcode → Settings → Intelligence → Agents → Plug-ins → Add Plug-in → point at `~/Projects/apple-studio` (marketplace) or the plugin directory, then in an Xcode Claude Agent conversation type `/` and report which apple-studio skills appear, and whether the stop-gate hook fires there. Record the results (including "not supported") in the spec's verification section.

- [ ] **Step 5: Bump version + update docs**

In `plugin/.claude-plugin/plugin.json`: `"version": "0.2.0"`. Append `## Phase 1 verification results` to the spec with the outcomes of Steps 1–4 and the Task 6/7 tests (dated, one line per spec verification item 1–8).

- [ ] **Step 6: Final commit + tag + reinstall**

```bash
git add -A && git commit -m "release: apple-studio 0.2.0 - Phase 1 (architecture + testing)"
git tag v0.2.0
claude plugin update apple-studio
claude plugin list | grep -A2 apple-studio   # expect Version: 0.2.0, enabled
```

---

## Self-review notes (kept for the record)

- Spec coverage: verification items 1–8 map to Task 1 (item 3), Task 6 (item 4), Task 7 (item 5), Task 8 (item 8), Task 9 (items 1, 2, 6, 7). Persistence reference → Task 3; framework catalog + primers → Task 8; mcpbridge → Tasks 0–1; Xcode 27 baseline → Task 0 and Global Constraints.
- Known deliberate deviation: spec says "one real feature in a real project"; the user chose a fixture app (Task 0) as the standing verification target — recorded as user-approved.
- The stop-gate builds `generic/platform=iOS Simulator` first (compile-only, no simulator boot) and falls back to `platform=macOS` on destination mismatch, failing open when neither applies. The fixture is Multiplatform so both paths are verified. macOS-specific *guidance* (AppKit interop, menus/windows) remains Phase 4.
