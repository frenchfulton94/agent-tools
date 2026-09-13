# apple-studio Phase 2: Design/UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the Phase 1 debt, then ship the design/UX slice: an `apple-design` skill (six distilled references from the live HIG + two books) and a `design-reviewer` agent that critiques real simulator screenshots — native correctness only, branding out of scope.

**Architecture:** Same two-layer pattern as Phase 1: knowledge references distilled per the pipeline (this phase's primary source is the *live HIG* via DocC JSON endpoints, supplemented by SwiftUI by Tutorials and iOS Animations by Tutorials), consumed by a lean SKILL.md and the screenshot-driven reviewer agent. Verification reuses the StudioFixture app and a seeded HIG-violation screen.

**Tech Stack:** Claude Code plugin components, existing `pipeline/` (convert.sh, distill-prompt.md), pandoc, DocC JSON endpoints (`https://developer.apple.com/tutorials/data/documentation/design/human-interface-guidelines[.../<section>].json`), `xcodebuild`/`simctl` via the xcode-loop skill's verified commands.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-2` (create from `main` at start). All paths relative to repo root unless absolute.
- Toolchain: Xcode 27.0 beta active; fixture app `~/Projects/StudioFixture` (Multiplatform, scheme `StudioFixture`, keep its git tree clean after any test).
- Stack baseline and scope per CONVENTIONS.md and the spec: SwiftUI-first; **design scope is HIG conformance / native correctness ONLY — no brand/custom-visual guidance anywhere in this phase's output** (spec "Design scope" decision).
- Live-docs-first: HIG claims cite the HIG section URL; current HIG wins over book material. Human-facing pages are JS-rendered — use the DocC JSON endpoints (`https://developer.apple.com/tutorials/data/documentation/design/<page>.json`), citing the canonical human URL in headers.
- Reference files: CONVENTIONS.md header block, decision-grade only, ~100–250 lines, no copied book/HIG prose (own words; short attributed quotes with quotation marks are OK), no remaining `[VERIFY` markers at commit.
- Evidence standard (Phase 1 rule, now standing): every consume-test/verification claim is backed by a captured log under the SDD workspace, with quoted lines in the report. Nested sessions run synchronously in the foreground (`--permission-mode auto` when the session must write files); never background-and-wait.
- New this phase (from phase-1 debt): verification tables use `file:line-range` evidence pointers.
- Commit after every task minimum. Version bump to 0.3.0 only in Task 7.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Branch + Phase 1 debt clearance

**Files:**
- Modify: `plugin/skills/swift-concurrency/references/strict-concurrency.md` (~line 75)
- Modify: `plugin/skills/swift-architecture/references/architecture-patterns.md` (~line 63 + header line 1)
- Modify: `plugin/skills/xcode-loop/references/headless-commands.md` (§4 Build)
- Modify: `plugin/skills/apple-frameworks/references/framework-catalog.md` (regenerated)
- Modify: `plugin/skills/apple-frameworks/evals/triggers.md`
- Modify: `CONVENTIONS.md`
- Modify: `docs/specs/2026-08-03-apple-studio-design.md` (verification item 8 sentence)
- Delete: `docs/phase-1-debt.md` (cleared items removed; keep only the "before Phase 3" kill-switch note and stop-gate enhancement candidate, renamed `docs/deferred.md`)

**Interfaces:**
- Consumes: `docs/phase-1-debt.md` (the authoritative item list — read it first).
- Produces: a debt-free plugin tree later tasks build on.

- [ ] **Step 1: Create the branch**

```bash
cd ~/Projects/apple-studio && git checkout -b phase-2
```

- [ ] **Step 2: Fix the nonisolated stored-property overgeneralization.** Fetch `https://raw.githubusercontent.com/swiftlang/swift-evolution/main/proposals/0434-global-actor-isolated-types-usability.md` and the current TSPL concurrency chapter (raw: `https://raw.githubusercontent.com/swiftlang/swift-book/main/TSPL.docc/LanguageGuide/Concurrency.md`). Rewrite the false sentence in `strict-concurrency.md` (~line 75, "stored properties are not allowed — only methods and computed properties") to match what the sources actually state — at minimum: `nonisolated let` stored properties of `Sendable` type are legal on isolated types, and SE-0434 broadens nonisolated storage usability for global-actor-isolated types. Quote the deciding source sentences in your report next to the final wording (the Phase 1 Task 4 lesson: cited wording must match its citation).

- [ ] **Step 3: Flag the TCA claim's non-Apple source.** In `architecture-patterns.md`: append to the header block a line `> note: TCA currency claim (line ~63) sourced via web search 2026-08, not Apple docs` (adjust line ref to reality).

- [ ] **Step 4: Add the macOS derivedDataPath code block.** In `headless-commands.md` §4, convert the prose-only macOS variant into a second fenced command block mirroring the iOS one with `-destination 'platform=macOS'` (the command was already verified in Phase 1 — this is formatting, not new claims).

- [ ] **Step 5: Evidence catalog determinism while regenerating.**

```bash
pipeline/generate_catalog.sh
cp plugin/skills/apple-frameworks/references/framework-catalog.md /tmp/catalog-run1.md
pipeline/generate_catalog.sh
diff <(grep -v '^> generated:' /tmp/catalog-run1.md) <(grep -v '^> generated:' plugin/skills/apple-frameworks/references/framework-catalog.md) && echo DETERMINISTIC
```

Expected: `DETERMINISTIC`. Save the command + output in your report; if entry count changed vs the committed catalog (Apple added frameworks), that's fine — note the delta. If NOT deterministic, soften the spec's item 8 sentence to match reality instead ("stable modulo the generated date and upstream additions") and record why.

- [ ] **Step 6: CONVENTIONS.md amendments.** Add two entries: (a) under Reference files — "Generated reference files (e.g. framework-catalog.md) use a `> generated: <date>` / `> regenerate: <script>` header instead of the `verified:` block; the generator script is their verification."; (b) under a new `## Verification records` section — "Spec verification tables point at evidence as `<file>:<line-range>`, not bare filenames."

- [ ] **Step 7: Add the two-primer routing eval.** Append to `plugin/skills/apple-frameworks/evals/triggers.md` under Should fire: `- "I want a live delivery countdown on the lock screen AND a home-screen widget showing order status" (routing expectation: reads BOTH activitykit.md and widgetkit.md)`.

- [ ] **Step 8: Trim the debt file.** Move the two not-now items (kill-switch load-frequency check before Phase 3; stop-gate session-start baseline on observed pain; Xcode agent/hook evidence — closing THIS phase in Task 6) into `docs/deferred.md`; delete `docs/phase-1-debt.md`.

- [ ] **Step 9: Validate + commit**

```bash
claude plugin validate . --strict
git add -A && git commit -m "chore: clear Phase 1 debt (concurrency fix, sourcing flags, conventions, determinism evidence)"
```

---

### Task 1: Convert Phase 2 books + build the two distillation maps

**Files:**
- Create: `corpus/swiftui-by-tutorials-v5-0-0.md` (+ `.toc.md`) and `corpus/ios-animations-by-tutorials-v7-0-0.md` (+ `.toc.md`) — gitignored
- Create: `pipeline/maps/apple-design-books.md` (chapter map, both books)
- Create: `pipeline/maps/apple-design-hig.md` (HIG endpoint map)

**Interfaces:**
- Consumes: `pipeline/convert.sh`; the HIG DocC JSON index.
- Produces: maps that Tasks 2–4 dispatch from. Book-map format identical to Phase 1 (`- L<start>–L<end>: <chapter title> → <target reference file>`); HIG-map format: `## <reference file>` sections listing `- <human URL> → <DocC JSON endpoint>` per section to fetch.

- [ ] **Step 1: Convert the two books**

```bash
cd ~/Projects/apple-studio && pipeline/convert.sh \
  "/Users/michaelfrenchfultonjr/Documents/Apple Books/SwiftUI_by_Tutorials_v5.0.0.epub" \
  "/Users/michaelfrenchfultonjr/Documents/Apple Books/iOS_Animations_by_Tutorials_v7.0.0.epub"
```

Expected: two `.md` + two `.toc.md` files in `corpus/` (the SwiftUI epub is 188MB — conversion may take a few minutes; text output should be a few MB). Spot-check one mid-book heading per file via `sed -n '<line>p'`.

- [ ] **Step 2: Build `pipeline/maps/apple-design-books.md`.** From the TOCs, map chapters to targets — SwiftUI by Tutorials: ONLY chapters about layout system judgment, styling/view modifiers, custom components vs system components, adaptive/multiplatform layout → `swiftui-design-implementation.md`; accessibility chapters → `accessibility.md`. Skip tutorial walkthrough chapters with no durable judgment (most of them — be ruthless; this book is v5.0.0/2022-era, so API-specific content is presumptively stale). iOS Animations: chapters on animation principles, timing, transitions → `animation-taste.md`; skip UIKit-mechanics chapters except judgment that transfers (mark `## Maintaining older code:` candidates). Verify every range start with `sed -n '<start>p'`.

- [ ] **Step 3: Build `pipeline/maps/apple-design-hig.md`.** Fetch `https://developer.apple.com/tutorials/data/documentation/design/human-interface-guidelines.json`, enumerate its section topics, and assign endpoints:
  - → `hig-foundations.md`: layout, typography, color, materials, dark-mode, icons/SF Symbols, images
  - → `hig-patterns.md`: navigation-and-search, modality, feedback, entering-data/forms, onboarding, settings, loading, empty-states (as available in the index)
  - → `platform-idioms.md`: the iOS/iPadOS/macOS platform pages + windows/multitasking/pointer-and-keyboard topics
  - → `accessibility.md`: accessibility + inclusion pages, motion
  - → `animation-taste.md`: motion page (shared with accessibility's Reduce Motion)
  Adjust names to what the index actually contains (do not invent endpoints — every listed endpoint must have returned JSON when probed with a HEAD/fetch). Record any expected-but-missing section in the map with `MISSING:`.

- [ ] **Step 4: Commit**

```bash
git add pipeline/maps && git commit -m "feat: Phase 2 distillation maps (books + HIG endpoints)"
```

---

### Task 2: Distill `hig-foundations.md` + `hig-patterns.md`

**Files:**
- Create: `plugin/skills/apple-design/references/hig-foundations.md`
- Create: `plugin/skills/apple-design/references/hig-patterns.md`

**Interfaces:**
- Consumes: `pipeline/maps/apple-design-hig.md`; `pipeline/distill-prompt.md` (adapted — see Step 1).
- Produces: the two core HIG references (exact filenames above) read by the SKILL.md (Task 5) and design-reviewer (Task 6).

- [ ] **Step 1: Dispatch two distiller subagents** (parallel, model sonnet), one per file, with this adaptation of the pipeline prompt: replace the corpus-lines input with "Fetch these DocC JSON endpoints: <the map's list for your file>", and replace the currency rule with "cite the canonical HIG human URL per claim cluster; use `[VERIFY: ...]` only for claims you inferred beyond the fetched text". All other rules (worth-it, baseline, own-words, 100–250 lines, decision-grade) unchanged. For `hig-foundations.md` the worth-it bar is highest: skip anything any iOS developer knows ("use SF Symbols"); keep the judgment (when custom layout is justified, semantic-color decision rules, Dynamic Type layout consequences, materials vs flat color criteria).

- [ ] **Step 2: Resolve `[VERIFY:]` flags** (fetch the relevant endpoint; drop unverifiable inferences). `grep -rn "VERIFY" plugin/skills/apple-design/` → empty.

- [ ] **Step 3: Add CONVENTIONS.md headers** (`verified: 2026-08 against <human HIG URLs>` / `sources: live HIG (DocC JSON)`).

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-design && git commit -m "feat: apple-design HIG foundations + patterns references"
```

---

### Task 3: Distill `accessibility.md` + `platform-idioms.md`

**Files:**
- Create: `plugin/skills/apple-design/references/accessibility.md`
- Create: `plugin/skills/apple-design/references/platform-idioms.md`

**Interfaces:**
- Consumes: `pipeline/maps/apple-design-hig.md` (HIG endpoints) + `pipeline/maps/apple-design-books.md` (SwiftUI book accessibility chapters feed `accessibility.md`).
- Produces: the two references (exact filenames) for Tasks 5–6. `accessibility.md` must include a **reviewable checklist section** (`## Screen-review checklist`) the design-reviewer can apply mechanically: Dynamic Type behavior, VoiceOver labels/traits, 44×44pt targets, contrast, Reduce Motion, keyboard/pointer on macOS/iPadOS.

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet) — same adapted prompt as Task 2; `accessibility.md`'s distiller gets both the HIG endpoints AND the book chapter ranges from the books map; `platform-idioms.md`'s distiller is instructed to organize by *decision* ("shipping one SwiftUI codebase on iPhone + iPad + Mac: what must differ per platform") not by platform encyclopedia — and to stay within native-correctness scope.

- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty.

- [ ] **Step 3: Headers** (accessibility.md's `sources:` line lists both live HIG and the SwiftUI book).

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-design && git commit -m "feat: apple-design accessibility + platform-idioms references"
```

---

### Task 4: Distill `swiftui-design-implementation.md` + `animation-taste.md`

**Files:**
- Create: `plugin/skills/apple-design/references/swiftui-design-implementation.md`
- Create: `plugin/skills/apple-design/references/animation-taste.md`

**Interfaces:**
- Consumes: `pipeline/maps/apple-design-books.md` (primary) + the HIG motion endpoint (for animation-taste).
- Produces: the final two references (exact filenames) for Tasks 5–6.

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet) using the standard `pipeline/distill-prompt.md` with corpus ranges from the books map. Currency warning to both: the SwiftUI book is 2022-era — every API-specific claim gets `[VERIFY:]` and is checked against current SwiftUI docs (`https://developer.apple.com/tutorials/data/documentation/swiftui.json` + child pages); the Animations book is UIKit-heavy — only transferable judgment survives, UIKit mechanics only under `## Maintaining older code:` and only if genuinely useful for maintenance. `animation-taste.md` additionally distills the HIG motion endpoint and must cover: when NOT to animate, duration/easing judgment, purposeful vs decorative motion, and the Reduce Motion obligation (cross-referencing `accessibility.md`, not duplicating it).

- [ ] **Step 2: Resolve `[VERIFY:]` flags** against current SwiftUI DocC JSON; grep → empty.

- [ ] **Step 3: Headers** (honest sources: book + which live docs actually checked).

- [ ] **Step 4: Sibling-consistency check.** Skim `swift-architecture/references/state-and-di.md` and `architecture-patterns.md`: `swiftui-design-implementation.md` must not contradict their view-structure guidance (it covers visual/layout implementation, not state/architecture — if a topic overlaps, point to the sibling instead of restating).

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/apple-design && git commit -m "feat: apple-design SwiftUI implementation + animation references"
```

---

### Task 5: `apple-design` SKILL.md + evals + consume-test

**Files:**
- Create: `plugin/skills/apple-design/SKILL.md`
- Create: `plugin/skills/apple-design/evals/triggers.md`

**Interfaces:**
- Consumes: the six references from Tasks 2–4 (exact filenames as listed there).
- Produces: the complete skill; `design-reviewer` (Task 6) points at `${CLAUDE_PLUGIN_ROOT}/skills/apple-design/references/`.

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: apple-design
description: Apple Human Interface Guidelines conformance for iOS/iPadOS/macOS apps - layout, typography and Dynamic Type, color and materials, navigation and modality patterns, platform idioms, accessibility, and animation judgment. Use when designing or building UI, choosing a navigation or presentation pattern, styling views, making an app feel native, or fixing accessibility, Dynamic Type, or contrast issues. Not for brand identity or custom visual styling.
---

# Apple design (native correctness)

Scope: HIG conformance only. Brand identity, custom look-and-feel, and visual
distinctiveness belong to other tooling; this skill makes screens correctly
Apple.

Read the reference for the decision at hand:
- Layout, typography, color, materials, SF Symbols → `references/hig-foundations.md`
- Navigation, modality, feedback, forms, empty states → `references/hig-patterns.md`
- iPhone vs iPad vs Mac in one codebase → `references/platform-idioms.md`
- Accessibility (labels, targets, contrast, motion) → `references/accessibility.md`
- Implementing design correctly in SwiftUI → `references/swiftui-design-implementation.md`
- Whether and how to animate → `references/animation-taste.md`

Rules that always apply:
- System-provided first: text styles (never fixed point sizes), semantic
  colors, system components, SF Symbols. Custom only with a stated reason.
- Every screen ships accessible: Dynamic Type, VoiceOver labels, 44pt
  targets, sufficient contrast, Reduce Motion respected. The checklist lives
  in `references/accessibility.md`.
- After building UI, verify visually: capture screenshots via the xcode-loop
  skill and review them (the design-reviewer agent automates this).
- The current HIG wins over anything written here:
  https://developer.apple.com/design/human-interface-guidelines
```

- [ ] **Step 2: Write `evals/triggers.md`**

```markdown
# apple-design trigger evals
## Should fire
- "Build the settings screen UI"
- "Does this screen feel native?"
- "What's the right navigation pattern for a three-level hierarchy?"
- "My layout breaks at larger text sizes - fix it"
- "Add a confirmation flow before deleting"
- "Review this screen for accessibility"
## Should NOT fire
- "Design our brand color palette"        (branding - out of scope)
- "Fix this Sendable warning"             (swift-concurrency)
- "Run the app and screenshot it"         (xcode-loop)
- "Should I use SwiftData or Core Data?"  (swift-architecture)
```

- [ ] **Step 3: Consume-test with captured evidence.** From `~/Projects/StudioFixture`: `claude --plugin-dir ~/Projects/apple-studio/plugin --permission-mode auto -p "Add an empty-state view to ContentView for when there is no data yet. Make it feel native. Implement now, no clarifying questions." --output-format stream-json --verbose` → save to the SDD workspace as `task-5-consume-test.log`. Evidence required: skill invocation, ≥2 references Read (expect hig-patterns + hig-foundations or accessibility), answer visibly applying their criteria (e.g. ContentUnavailableView or equivalent-pattern judgment, text styles not fixed sizes). Revert the fixture (git checkout, clean status).

- [ ] **Step 4: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/skills/apple-design && git commit -m "feat: apple-design skill (SKILL.md + evals)"
```

---

### Task 6: `design-reviewer` agent + seeded-flaw verification

**Files:**
- Create: `plugin/agents/design-reviewer.md`
- Create: `pipeline/fixtures/flawed-design/FlawedProfileScreen.swift`

**Interfaces:**
- Consumes: `plugin/skills/apple-design/references/` (all six files); xcode-loop's verified screenshot flow (`references/headless-commands.md`).
- Produces: the `apple-studio:design-reviewer` agent.

- [ ] **Step 1: Write `plugin/agents/design-reviewer.md`**

```markdown
---
name: design-reviewer
description: Reviews app screens for Apple HIG conformance - native correctness, platform idioms, accessibility, Dynamic Type, touch targets, contrast, and motion. Use after building or changing UI, before shipping a screen, or when the user asks whether a screen looks right, feels native, or meets Apple guidelines. Reviews simulator/app screenshots plus, when available, the screen's SwiftUI source.
tools: Read, Grep, Glob, Bash
---

You are an Apple-platform design reviewer. You review for NATIVE CORRECTNESS
against written standards - never for brand identity or subjective taste
(branding is out of scope; other tooling owns it).

Process:
1. Inputs: screenshot path(s) - Read them (images render visually) - and,
   when given, the screen's SwiftUI source files. If no screenshot was
   provided, capture one via the xcode-loop skill's headless commands
   (build → boot → install → launch → `xcrun simctl io booted screenshot`).
2. Load the standards. Read ALL files in:
   - ${CLAUDE_PLUGIN_ROOT}/skills/apple-design/references/
3. Review dimensions: foundations (layout, typography/Dynamic Type,
   color/contrast, SF Symbols), patterns (navigation, modality, feedback),
   platform idioms (correct for THIS platform), accessibility (use the
   screen-review checklist in accessibility.md), motion.
4. Tie every visual finding to what is visible in the screenshot. Source
   findings (missing accessibilityLabel, fixed font sizes, repeatForever
   animation without a Reduce Motion check) cite file:line.
5. Verify each finding against a reference before reporting. No taste-only
   findings; no brand opinions.

Output (your final message is the deliverable):
- Findings ranked [BLOCKER] > [MAJOR] > [MINOR] > [NIT], each with
  what/where (screenshot region or file:line), the reference file that
  makes it a violation, and a concrete fix.
- End with verdict (APPROVE / APPROVE WITH CHANGES / REQUEST CHANGES) and a
  one-line summary. Clean screens get a clean verdict - never invent
  findings.
```

- [ ] **Step 2: Write the seeded fixture `pipeline/fixtures/flawed-design/FlawedProfileScreen.swift`** with exactly five planted HIG violations:

```swift
import SwiftUI

// Seeded HIG-violation fixture for design-reviewer verification. Planted flaws:
// 1 (touch target): settings button tap area 24x24pt, below the 44x44 minimum.
// 2 (typography): hardcoded 11pt font ignores Dynamic Type.
// 3 (contrast): very light gray text on the default background.
// 4 (accessibility): icon-only button with no accessibility label.
// 5 (motion): infinite autoreversing animation with no Reduce Motion check.
struct FlawedProfileScreen: View {
    @State private var pulse = false
    var body: some View {
        VStack(spacing: 4) {
            Text("Profile")
                .font(.system(size: 11))
                .foregroundColor(Color(white: 0.85))
            Button(action: {}) {
                Image(systemName: "gearshape")
            }
            .frame(width: 24, height: 24)
            Circle()
                .fill(.blue)
                .frame(width: 44, height: 44)
                .scaleEffect(pulse ? 1.3 : 1.0)
                .animation(
                    .easeInOut(duration: 0.6).repeatForever(autoreverses: true),
                    value: pulse
                )
                .onAppear { pulse = true }
        }
    }
}
```

- [ ] **Step 3: Verification run with captured evidence.** Temporarily add the fixture file to StudioFixture (make `ContentView` show `FlawedProfileScreen()`), then via the xcode-loop commands: build for iOS Simulator, boot, install, launch, screenshot to `/tmp/flawed-profile.png`. Then a fresh session: `claude --plugin-dir ~/Projects/apple-studio/plugin -p "Use the design-reviewer agent to review the screen in /tmp/flawed-profile.png; source file is <fixture path in StudioFixture>. Report its findings verbatim." --output-format stream-json --verbose` → `task-6-verify.log`. All five planted flaws must be found with reference citations (contrast + touch target + typography should be evident from the screenshot; the motion and a11y-label flaws from source). A missed flaw = strengthen the corresponding reference (knowledge gap, not agent prompt), re-run, document the iteration. Then REVERT StudioFixture to clean git status.

- [ ] **Step 4: Close the Xcode-surface question (docs/deferred.md item, user-assisted).** Ask the user to re-import the plugin in Xcode (Settings → Intelligence → Agents → Plug-ins — it's a copy, needs re-import) and check: do `swift-reviewer`/`design-reviewer` appear anywhere in the Xcode Claude Agent UI or its `/` menu? Record the answer (including "skills only") in `docs/deferred.md`, replacing the open question with the finding.

- [ ] **Step 5: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/agents pipeline/fixtures docs/deferred.md && git commit -m "feat: design-reviewer agent + seeded HIG-violation fixture"
```

---

### Task 7: Integration verification + 0.3.0 release

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (0.2.0 → 0.3.0)
- Modify: `docs/specs/2026-08-03-apple-studio-design.md` (append `## Phase 2 verification results (2026-08-04)`)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Trigger-eval sampling.** For `apple-design`: all 6 should-fire + all 4 should-NOT-fire prompts. For each Phase 1 skill: 1 should-fire + 1 should-NOT prompt (regression sample). Same method and logging as Phase 1's Task 9 (`claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2 --output-format stream-json`, one log per prompt). Record the pass/fail table. Misfire → tighten the description, re-run that prompt, record old → new.

- [ ] **Step 2: `claude plugin validate . --strict`** — pass, zero warnings, captured.

- [ ] **Step 3: Append `## Phase 2 verification results (2026-08-04)`** to the spec: one entry per Phase 2 deliverable (debt cleared incl. determinism evidence; 6 references with sources; skill consume-test; design-reviewer 5/5 flaws; Xcode surface finding; eval table) — with `file:line-range` evidence pointers (the new convention), honest caveats verbatim where things were partial.

- [ ] **Step 4: Bump version to 0.3.0, commit, tag**

```bash
git add -A && git commit -m "release: apple-studio 0.3.0 - Phase 2 (design/UX)"
git tag v0.3.0
claude plugin validate . --strict
```

(Installed-plugin update happens post-merge, controller-handled, as in Phase 1.)

---

## Self-review notes

- Spec coverage: Phase 2 charter (apple-design skill + design-reviewer via xcode-loop screenshots, HIG + 2 books, native-correctness scope) → Tasks 1–6; debt + process adoptions → Task 0; release discipline → Task 7. The spec's "design scope" boundary is restated in Global Constraints, the SKILL.md text, and the agent text.
- Deliberate scope cuts (YAGNI): no macOS-screenshot design review this phase (xcode-loop documents full-screen capture only; revisit when a real macOS screen needs review); no HIG coverage of platforms Michael doesn't ship (watchOS/tvOS/visionOS); no automated contrast-measurement tooling — the reviewer judges visually.
- The HIG endpoint map (Task 1 Step 3) deliberately requires probing real endpoints — Phase 1's Task 8 proved assumed-JSON-shapes wrong; same discipline here.
