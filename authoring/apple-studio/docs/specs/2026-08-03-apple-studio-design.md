# apple-studio — Design Spec

**Date:** 2026-08-03
**Status:** Approved (brainstormed and approved section-by-section)
**Repo:** `~/Projects/apple-studio` — installed as `apple-studio@apple-studio` (user scope)

## Purpose

Claude Code tooling that helps a solo developer ship Apple-platform apps
(iOS/iPadOS/macOS) at the quality of a full studio, across four dimensions:
architecture & code quality, testing discipline, design/UX polish, and
release & operations. Serves both shipped apps under maintenance and new
projects from zero.

Knowledge is grounded in ~25 Apple/Swift books (2017–2025, in
`~/Documents/Apple Books`) distilled against current Apple documentation.
Current docs are authoritative on any conflict:

- https://docs.swift.org/swift-book/
- https://developer.apple.com/documentation/
- https://developer.apple.com/design/human-interface-guidelines

## Decisions (user-approved)

| Decision | Choice |
|---|---|
| Overall approach | One plugin, built in vertical slices (domain-by-domain), not knowledge-first big bang |
| First increment | Architecture + testing |
| Packaging | Private git repo = plugin + its own single-entry marketplace |
| Book usage | Distilled per-skill references, demand-driven per phase; raw text gitignored |
| Stack baseline | SwiftUI-first, Swift 6 strict concurrency, async/await, SPM, Swift Testing; legacy as marked context only |
| Toolchain | Xcode 27 on macOS 27 (Michael's environment). Newer than model training data — all Xcode/OS-specific behavior is verified against live docs and release notes, never memory. Skill guidance must not assume Xcode 26-era UI or flags |
| Build loop | Apple-only tooling: `xcrun mcpbridge` (Xcode's first-party MCP server) when Xcode has the project open; headless `xcodebuild` + `xcrun simctl` otherwise. No third-party build MCP |
| Design scope | HIG conformance / native correctness ONLY. Custom visual design & branding out of scope — owned by separate tooling (e.g. brand-studio) |

## Repo layout

```
apple-studio/
├── .claude-plugin/marketplace.json   # single-entry, source: "./plugin"
├── plugin/                           # the shipped plugin — nothing else gets installed
│   ├── .claude-plugin/plugin.json
│   ├── skills/<name>/{SKILL.md, references/}
│   ├── agents/<name>.md
│   └── hooks/{hooks.json, scripts/}
├── pipeline/                         # dev-time: book conversion + distillation
├── corpus/                           # converted book text — GITIGNORED
├── docs/specs/                       # this document and successors
└── CONVENTIONS.md                    # authoring standards, binding on all phases
```

The plugin lives in a subdirectory so the marketplace install copies only shipped
components — never the corpus or pipeline. Distilled knowledge lives inside its
consuming skill (`references/`), giving every distilled page a consumer by
construction. Raw book text never enters git (copyright); committed references are
distilled guidance in our own words.

## Distillation pipeline (per phase)

1. **Convert** — `pipeline/convert.sh`: EPUB→markdown via pandoc (+ heading TOC),
   PDF→text via pdftotext, into `corpus/`.
2. **Map** — per consuming skill, a reviewable chapter-map of relevant material.
3. **Distill** — subagent fan-out extracting decision-grade guidance under three
   rules: **currency** (checked against live docs, docs win, `verified:` header),
   **baseline** (modern stack voice; legacy only in marked sections), **worth-it**
   (skip what Claude already knows; keep judgment and Apple-specific depth).
4. **Consume-test** — exercise the skill on a real task in a real project; cut
   references that never load or don't change behavior.

Target: 3–6 reference files per skill, a few hundred lines each.

## Framework and API coverage (decided during spec review, 2026-08-03)

Apple ships hundreds of frameworks and the catalog grows every WWDC — including
frameworks newer than any model's training data. The plugin handles this breadth
with awareness + live depth, not pre-distillation:

- **Framework catalog index:** `pipeline/` script regenerates a compact index
  (framework name → one-line purpose → doc URL) from the live
  developer.apple.com Technologies page, shipped as
  `swift-architecture/references/framework-catalog.md`. Feature design starts
  with "does Apple already ship this?" answered from a current catalog.
  Regenerated each phase and after WWDC.
- **Live-docs-first rule:** when working with any Apple framework, current
  developer.apple.com documentation is fetched and consulted — never trusted
  from memory. (Also recorded in CONVENTIONS.md.)
- **No per-framework pre-distillation:** deep framework guidance stays live;
  distilled references are reserved for durable judgment (architecture,
  concurrency, testing, HIG). New vertical slices for specific frameworks are
  created only when a real project needs one.
- Frameworks already slotted: persistence (Phase 1, swift-architecture), push
  notifications and StoreKit/App Store machinery (Phase 3), ML (Phase 4).

**Framework primers (decided during spec review):** the catalog + primers are
promoted to their own skill, `apple-frameworks`, built at the end of Phase 1:

- **Tier 1 — catalog index:** the full generated framework list (as above).
- **Tier 2 — primers:** ~16 one-page references (~100–150 lines each) for the
  frameworks common apps touch, covering only durable judgment: what it's for,
  when to choose it over alternatives, architecture integration, privacy and
  entitlement requirements, OS availability floors, classic pitfalls. API
  detail stays live-fetched. Distilled from current docs with `verified:`
  headers; regenerated cheaply per phase.
- Starter set (all five groups, user-approved): **essentials** — SwiftData,
  CloudKit, URLSession/Network, OSLog, BackgroundTasks; **engagement** —
  UserNotifications, WidgetKit, App Intents, ActivityKit, TipKit;
  **monetization** — StoreKit 2; **platform** — Core Location, MapKit,
  PhotoKit/PhotosUI, Swift Charts; **on-device AI** — Foundation Models.

## Xcode integration (added during spec review, 2026-08-03)

Michael also uses Claude from inside Xcode (Xcode 26 coding intelligence), which
affects two things:

- **The plugin should work in Xcode's Claude Agent.** Xcode can launch the
  Claude Agent with custom skills and installed plug-ins (Intelligence settings
  → Agents → Plug-ins; per-agent config at
  `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig`). Installing
  apple-studio there — and confirming which components (skills, agents, hooks)
  actually load — is a Phase 1 verification item, not an assumption. Guidance
  in skills must not assume a terminal-only session.
- **`xcode-loop` uses Apple's own MCP bridge when available.** With "Allow
  external agents to use Xcode tools" enabled and the project open,
  `claude mcp add --transport stdio xcode -- xcrun mcpbridge` gives project-aware
  build/actions; headless `xcodebuild`/`simctl` remains the fallback and the CI
  path. Both modes are first-party Apple tooling.

## Phases

**Phase 0 — Bootstrap (this spec's own phase):** repo, manifests, CONVENTIONS.md,
convert.sh validated on the Phase 1 books, this spec, install + validate loop.

**Phase 1 — Architecture + testing (first usable increment):**

| Component | Job |
|---|---|
| Skill `swift-architecture` | Architecture choice for SwiftUI apps, state management, DI, module boundaries, pattern-vs-ceremony judgment, working in existing code. Includes a `persistence` reference (SwiftData vs Core Data vs CloudKit sync vs files — distilled mainly from current docs) and the generated `framework-catalog` reference (below) |
| Skill `swift-concurrency` | Actor isolation, Sendable, structured concurrency, Swift 6 strict-concurrency errors, Combine→async migration |
| Skill `swift-testing` | Swift Testing specifics, what to test per layer, test doubles without heavy mocking, TDD rhythm in Xcode (complements superpowers TDD) |
| Skill `xcode-loop` | Two drive modes: Xcode's MCP bridge (`xcrun mcpbridge`, project-aware, when Xcode is open) and headless xcodebuild/simctl (build, test + result parsing, simulators, screenshots). Foundation for verification |
| Agent `swift-reviewer` | Severity-ranked review of diffs/modules against the three knowledge skills' standards; reads the same references |
| Hook: stop-gate | On Swift edits, fast build (+cheap targeted tests) before completion claims; blocks on red; always fails open |

Source books: Advanced iOS App Architecture, App Architecture, Design Patterns by
Tutorials, Thinking in SwiftUI, Modern Concurrency in Swift, Concurrency by
Tutorials, Swift Concurrency by Example, Combine (legacy context), iOS TDD,
Testing Swift.

Build order: xcode-loop → distill + knowledge skills → swift-reviewer → hook.

Cut from Phase 1 (revisit only on proven pain): lint/format hook, scaffolding
skill, Xcode project-file machinery.

**Phase 2 — Design/UX:** live HIG + SwiftUI by Tutorials + iOS Animations →
`apple-design` skill (HIG compliance, platform idioms, accessibility, animation
taste) + `design-reviewer` agent critiquing simulator screenshots from
`xcode-loop`. Native correctness only; branding out of scope.

**Phase 3 — Release & ops:** iOS App Distribution + Push Notifications + current
App Store docs → `app-release` skill (signing, TestFlight, submission, rejection
avoidance, versioning), push-notifications reference, CI guidance.

**Phase 4 — Long tail (unscheduled, on demand):** ML, macOS/Catalyst, animations
depth, ~~Advanced Git~~, ~~Flight School guides~~.

> **Amended 2026-09-02 (Phase 6).** Two items are struck from the long tail
> deliberately, per CONVENTIONS.md ("Amend deliberately, never silently"):
>
> - **Advanced Git — dropped.** Not Apple-specific. It dilutes the scope
>   boundary this charter sets ("native correctness"; branding and general
>   tooling out of scope) and duplicates general-purpose tooling that has
>   nothing to do with whether an app is correctly Apple.
> - **Flight School guides — dropped.** Swift language depth is already owned
>   by `swift-architecture` and `swift-concurrency`. Anything durable from
>   that material gets folded into those skills on demand, rather than
>   standing as a phase of its own.
>
> The remaining long-tail items are unaffected, and their status changed:
> **macOS/Catalyst shipped as Phase 4** (`apple-macos`) and **animations depth
> shipped as Phase 5** (`apple-animations`). **ML is the only long-tail item
> still outstanding**, and Phase 6 sharpened it rather than deferring it
> quietly — see the Phase 6 spec's Out of scope, which withdraws the original
> "model priors are reliable for old stable frameworks" rationale as false
> (Vision is now a Swift-native request API and Speech is module-based; the
> `VN`-prefixed and `SFSpeechRecognizer`-era types that dominate priors are
> the *previous* APIs). Classical ML is cut from Phase 6 for capacity, not for
> value, and is the strongest Phase 8 candidate.
>
> **Amended 2026-09-12 (Phase 7).** ML moves to Phase 8. Phase 7 ships the
> fluid-interfaces reference instead — see
> docs/specs/2026-09-12-phase7-fluid-interfaces-design.md. ML is deferred for
> sequencing, not for value; the Phase 6 withdrawal of the "old and stable"
> rationale stands.
>
> **Amended 2026-09-30 (Phase 9).** Phase 8 shipped the catalog migration,
> not ML, and did not amend the line above. ML remains the one outstanding
> long-tail item. Phase 9 is on-demand work: adaptive layout and iPhone Duo —
> see docs/specs/2026-09-30-phase9-adaptive-layout-design.md.

Each phase gets its own plan cycle; this spec is the standing charter.

## Quality rules for the tooling itself

- Trigger evals per skill (fires when it should, silent when it shouldn't).
- Hooks validated before commit; always fail open.
- `claude plugin validate --strict` before any version bump; bump per phase.
- Kill-switch: components that haven't earned their context cost by the next
  phase get cut or merged.

## Verification (Phase 0+1 definition of done)

1. Validator passes on the repo; plugin installs from the local marketplace.
2. Each Phase 1 skill triggers on matching natural requests, stays quiet
   otherwise (trigger evals).
3. `xcode-loop` builds + tests + screenshots a real app.
4. `swift-reviewer` finds seeded flaws (architecture violation, data race,
   missing test) in a deliberately-flawed diff.
5. Stop-gate blocks a completion claim on a red build; a broken hook script
   does not block normal work.
6. One real feature shipped in a real project using the Phase 1 skills.
7. apple-studio installed into Xcode's Claude Agent (Plug-ins UI); record which
   components load and adjust guidance accordingly.
8. `apple-frameworks` skill: catalog regenerates from the live Technologies
   page; primers exist for the approved starter set with `verified:` headers.

## Phase 1 verification results (2026-08-03)

1. **Validator + local install — PASS.** `claude plugin validate . --strict` passed with zero
   warnings, both mid-development (re-run after every task) and again after the 0.2.0 version
   bump. Evidence: `task-9-validate.log`.
2. **Trigger evals — PASS, 25/25.** 3 "should fire" + 2 "should NOT fire" prompts per skill
   (all 5 skills), run via `claude --plugin-dir ./plugin -p ... --output-format stream-json`;
   every skill fired only on its own prompts and stayed silent on excluded ones. No misfires, no
   description edits needed. Evidence: `task-9-evals/*.log`, `task-9-evals/results.tsv`,
   `task-9-report.md` Step 1 table.
3. **`xcode-loop` build+test+screenshot — PASS.** All headless commands (build for iOS Simulator
   and macOS, `xcodebuild test` with result-bundle parsing via `xcresulttool`, run+install+launch,
   `xcrun simctl io booted screenshot`) verified against the real `StudioFixture` fixture on both
   platforms, exit 0 throughout. Evidence: `task-1-report.md`.
4. **`swift-reviewer` seeded-flaw detection — PASS, 3/3.** Given the deliberately-flawed
   `FlawedFeature.swift` fixture, the agent caught all three seeded flaws in a single pass — the
   inline-networking view (BLOCKER), the `@unchecked Sendable` unsynchronized `SessionCache` data
   race (BLOCKER), and the untested `DiscountEngine` boundary logic (MAJOR) — each with
   file:line, rationale, reference citation, and fix, ending in REQUEST CHANGES. No missed-flaw
   iteration was needed. Evidence: `task-6-report.md`, `task-6-verify.log`.
5. **Stop-gate red-build block + fail-open — PASS.** End-to-end: a real Swift compile error
   after an edit produced `"Stop hook feedback: Stop gate: build failed after Swift edits. Fix
   before finishing. Errors: ...ContentView.swift:10:8: error: Expected type..."` fed verbatim
   back into the session, forcing a fix before the turn could end. With `stop_gate.sh` made
   non-executable, the session finished cleanly with no block (fail-open confirmed). Evidence:
   `task-7-report.md`, `task-7-redbuild-e2e.log`, `task-7-failopen.log`.
6. **One real feature via the Phase 1 skills — PARTIAL PASS.** End-to-end consume-test
   ("Add a settings screen with a daily-reminder toggle that persists, tests first") against the
   `StudioFixture` fixture, retried with `--permission-mode auto` after a first attempt showed the
   plugin's design phase working but hit a harness-level headless-permission wall before any file
   write (harness-level block, not a plugin defect — see below). The retry confirmed: skills
   `superpowers:test-driven-development` → `apple-studio:swift-testing` →
   `apple-studio:xcode-loop` formally invoked in that order; a real red→green TDD cycle via
   `xcodebuild test` (`cannot find 'SettingsStore' in scope` → 6/6 tests passing); a real iOS
   Simulator build (`** BUILD SUCCEEDED **`), install, launch, and screenshot; and the stop-gate
   hook firing and passing cleanly on the green build (corroborated via its data-directory build
   log and consumed edit-marker, since this CLI's `-p --output-format stream-json` does not
   surface `PostToolUse`/`Stop` as system events). Not confirmed in this run: `swift-architecture`
   was never formally invoked via the `Skill` tool — the design reasoning (an `@Observable` store
   backed by injectable `UserDefaults`) was consistent with its guidance but arrived through
   general reasoning, not a formal consult (component itself is independently verified in
   `task-3-report.md`'s own trigger evals and consume-test). `swift-reviewer` never ran in this
   e2e session — the `-p` turn ended mid-task while the model waited on a UI-test result it had
   backgrounded itself, before reaching a review step (component itself is independently verified
   under item 4 above / `task-6-report.md`). Fixture reverted to a clean git tree after every
   attempt. Evidence: `task-9-report.md` Step 3 (including the retry section),
   `task-9-e2e.log`, `task-9-e2e-retry.log`.
7. **Xcode Claude Agent install — PASS (skills only; agent/hook not evidenced).**
   User-assisted: Xcode 27 Settings → Intelligence → Agents → Plug-ins successfully imported
   apple-studio (dialog: "Imported August 3, 2026"). All five skills listed by name in the
   plug-in's Skills section: `apple-frameworks`, `swift-architecture`, `swift-concurrency`,
   `swift-testing`, `xcode-loop`. Operational note: Xcode imports the plug-in as a **copy** into
   `~/Library/…/AgentPlugins/apple-studio` — repo changes require re-importing; relevant for
   later-phase guidance. The Plug-ins UI surfaces skills only: the `swift-reviewer` agent and the
   stop-gate hook are not shown in that UI, and their behavior inside Xcode's Claude Agent was
   not exercised either way — recorded as **not evidenced in the Xcode surface**, not as
   working or broken.
8. **`apple-frameworks` catalog + primers — PASS.** Catalog regenerated deterministically from
   the live Technologies index (398 `"topic"` entries, well above the >200 threshold; two
   back-to-back runs produced identical output). 16 primers written for the approved starter set,
   each carrying a `> verified: 2026-08 against <urls>` / `> sources: live docs` header on a
   single blockquote line. The identical-output claim was flagged unevidenced in the Phase 1
   whole-branch review (no saved diff) and re-verified with a captured diff in Phase 2 Task 0:
   two back-to-back `pipeline/generate_catalog.sh` runs produced byte-identical output modulo the
   `> generated:` date line, 398 entries both times, no delta vs. the previously committed
   catalog. Evidence: `.superpowers/sdd/2026-08-04-phase2-design-ux/task-0-report.md:117-137`.

**Net:** 7/8 items fully PASS; item 6 is a partial pass with two named, honestly-recorded gaps
(swift-architecture and swift-reviewer not formally invoked in that specific e2e run, though both
are independently verified elsewhere) and one harness-level environmental caveat that does not
reflect a plugin defect.

## Phase 2 verification results (2026-08-04)

1. **Debt cleared + determinism evidence — PASS, 5/5.** All five Phase 1 debt items closed:
   `nonisolated` stored-properties fix backed by verbatim SE-0313/SE-0434 quotes
   (`plugin/skills/swift-concurrency/references/strict-concurrency.md:75-82`); TCA sourcing
   flagged as web-search-derived, not Apple docs
   (`plugin/skills/swift-architecture/references/architecture-patterns.md:3,64`); macOS
   `-derivedDataPath` build block added, output path reconciled with the file's own §8 reference
   (`plugin/skills/xcode-loop/references/headless-commands.md:105-106`); catalog-generator
   determinism reproduced with a captured diff (two runs, 398 entries both times, `DETERMINISTIC`)
   (`.superpowers/sdd/2026-08-04-phase2-design-ux/task-0-report.md:117-137`); CONVENTIONS.md
   amended with the generated-header convention and the new file:line-range verification-record
   rule (`CONVENTIONS.md:59-61,63-65`). `docs/phase-1-debt.md` deleted, superseded by
   `docs/deferred.md` (below). Evidence: `.superpowers/sdd/2026-08-04-phase2-design-ux/task-0-report.md`.
2. **Six `apple-design` references, all live-verified — PASS.** `hig-foundations.md` (214 lines),
   `hig-patterns.md` (146 lines), `platform-idioms.md` (111 lines), `accessibility.md` (137 lines),
   `swiftui-design-implementation.md` (91 lines), `animation-taste.md` (114 lines) — every claim
   sourced against live HIG DocC JSON and/or live SwiftUI DocC JSON, with book material
   (SwiftUI by Tutorials v5.0.0, iOS Animations by Tutorials v7.0.0) distilled and cross-checked
   rather than paraphrased (n-gram overlap check found zero verbatim lifts, per
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-3-report.md:201-205`). Two stale-claim
   catches, both fixed in review loops before this section was written:
   - **`@ViewBuilder` 10-child-limit claim.** First draft asserted the historical (2022-book-era)
     10-child `buildBlock` arity cap was "confirmed live... still capped at arity 10" — wrong, and
     self-contradicting against the very endpoint it cited. Corrected after re-fetching
     `.../swiftui/viewbuilder.json` directly and confirming the fixed-arity overload ladder is gone
     since Swift 5.9/Xcode 15, replaced by a parameter-pack-generic `buildBlock(_:)`. Fixed text:
     `plugin/skills/apple-design/references/swiftui-design-implementation.md:53`. Commit `acbe1df`.
     Evidence: `.superpowers/sdd/2026-08-04-phase2-design-ux/task-4-report.md:122-156`.
   - **Accessibility header's Reduce Motion sourcing.** Header `note:` line originally implied the
     Reduce Motion obligation text came from the `motion` endpoint; it actually comes from the
     Accessibility page (only the visionOS motion-comfort material is `motion.json`-sourced).
     Fixed wording: `plugin/skills/apple-design/references/accessibility.md:3`. Commit `1bce3cf`.
     Evidence: `.superpowers/sdd/2026-08-04-phase2-design-ux/task-3-report.md:269-287`.
   Endpoint/routing corrections along the way (documented, not silent): the real HIG JSON pattern
   is `data/design/...`, not the brief's assumed `data/documentation/design/...`
   (`.superpowers/sdd/2026-08-04-phase2-design-ux/task-1-report.md:107-126`); `empty-states` does
   not exist anywhere in the current HIG (confirmed via 4 direct 404s on slug variants), recorded
   as a gap rather than invented (`task-1-report.md:205-213`, `task-2-report.md:74-78`).
3. **`apple-design` skill consume-test — PASS, with an honestly-recorded plan defect.** SKILL.md
   (`plugin/skills/apple-design/SKILL.md`) and `evals/triggers.md` written byte-verbatim from the
   brief. **Plan-defect deviation:** the plan's original consume-test prompt (an empty-state
   prompt) targets a documented HIG gap — `hig-patterns.md` explicitly discloses "HIG has no
   dedicated empty-states page as of 2026-08" — so that prompt cannot structurally produce
   reference-informed evidence no matter how the skill or references are written; the one run
   against it is preserved as-is at `task-5-consume-test.log` specifically as evidence of this
   plan defect, not deleted or treated as the accepted evidence. The **accepted evidence** run
   used a different, coordinator-specified, equally in-scope prompt instead (a Settings-screen
   redesign: grouped sections, destructive sign-out with confirmation, Dynamic Type) — log
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-5-consume-test-2.log`. That run shows 4 full
   reference `Read`s (`hig-patterns.md`, `swiftui-design-implementation.md`, `hig-foundations.md`,
   `accessibility.md` — well past the ≥2 bar) and two criteria traceable to specific reference
   file:line citations absent from SKILL.md and not generic pretrained knowledge: the
   "don't duplicate a systemwide setting" rule
   (`plugin/skills/apple-design/references/hig-patterns.md:138`) landed as an actual code comment
   before the final answer was written, and the "truncation is a last resort... never truncate a
   value with no escape hatch" rule
   (`plugin/skills/apple-design/references/hig-foundations.md:46-48`) matched the answer's
   wrap-instead-of-truncate reasoning almost exactly. Fixture reverted clean after both runs.
   Evidence: `.superpowers/sdd/2026-08-04-phase2-design-ux/task-5-report.md`.
4. **`design-reviewer` agent + seeded-flaw verification — PASS, 5/5.** Given the deliberately
   flawed `pipeline/fixtures/flawed-design/FlawedProfileScreen.swift` (built, installed, launched,
   screenshotted via the real headless `xcode-loop` sequence, screenshot visually confirmed before
   dispatch), the agent found all five planted flaws in a single pass, each with a file:line and a
   reference citation: 24×24pt touch target (BLOCKER, `accessibility.md` § Tap targets); ~1.3:1
   text contrast (BLOCKER, `hig-foundations.md` § Color); missing VoiceOver label on an icon-only
   button (MAJOR, `accessibility.md` § VoiceOver); fixed-point-size text defeating Dynamic Type
   (MAJOR, `hig-foundations.md` § Typography); ungated infinite pulse animation ignoring Reduce
   Motion (MAJOR, `accessibility.md` § Reduce Motion). Verdict: REQUEST CHANGES. No missed-flaw
   iteration was needed. Fixture reverted clean. Evidence:
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-6-verify.log`,
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-6-report.md:113-152`.
5. **Xcode plug-in surface finding — PASS (import confirmed; runtime still open).** Re-import of
   apple-studio into Xcode 27 succeeded; the import dialog explicitly lists "2 subagent
   definitions, hooks" alongside the skills, confirming Xcode detects and imports agents
   (`swift-reviewer`, `design-reviewer`) and hooks — resolving the Phase 1 open question at the
   import layer. The post-import detail view still enumerates skills only (all six, correct
   version at import time). Recorded in `docs/deferred.md:16-27`. **Honest caveat, not closed by
   Phase 2:** runtime behavior of the agents/hook inside an actual Xcode Claude Agent conversation
   remains unexercised — import is confirmed, invocation inside Xcode's own agent UI is not.
   Tracked as `docs/deferred.md` item 4 (`docs/deferred.md:28-32`), explicitly left open rather
   than claimed done.
6. **Trigger evals — PASS, 19/20.** `apple-design`: all 6 should-fire + all 4 should-NOT-fire
   prompts. Each Phase 1 skill (`xcode-loop`, `swift-architecture`, `swift-concurrency`,
   `swift-testing`, `apple-frameworks`): 1 should-fire + 1 should-NOT-fire regression prompt. Run
   via `claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2 --output-format stream-json`, one
   log per prompt, synchronous. Evidence:
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-7-evals/*.log`,
   `.superpowers/sdd/2026-08-04-phase2-design-ux/task-7-evals/results.tsv`.

   | Skill | Prompt | Expected | Result |
   |---|---|---|---|
   | apple-design | "Build the settings screen UI" | fire | **FAIL** (see below) |
   | apple-design | "Does this screen feel native?" | fire | PASS |
   | apple-design | "What's the right navigation pattern for a three-level hierarchy?" | fire | PASS |
   | apple-design | "My layout breaks at larger text sizes - fix it" | fire | PASS |
   | apple-design | "Add a confirmation flow before deleting" | fire | PASS |
   | apple-design | "Review this screen for accessibility" | fire | PASS |
   | apple-design | "Design our brand color palette" | silent | PASS |
   | apple-design | "Fix this Sendable warning" | silent | PASS (swift-concurrency fired instead) |
   | apple-design | "Run the app and screenshot it" | silent | PASS (xcode-loop fired instead) |
   | apple-design | "Should I use SwiftData or Core Data?" | silent | PASS (swift-architecture fired instead) |
   | xcode-loop | "Build the app and make sure it compiles" | fire | PASS |
   | xcode-loop | "Explain actor isolation in Swift 6" | silent | PASS (swift-concurrency fired instead) |
   | swift-architecture | "Where should this view's state live?" | fire | PASS |
   | swift-architecture | "Fix this Sendable warning" | silent | PASS (swift-concurrency fired instead) |
   | swift-concurrency | "Fix this 'capture of non-Sendable type' error" | fire | PASS |
   | swift-concurrency | "Where should this state live?" | silent | PASS |
   | swift-testing | "Write tests for this view model" | fire | PASS |
   | swift-testing | "Run the test suite" | silent | PASS |
   | apple-frameworks | "Does Apple have a native way to show tips/onboarding hints?" | fire | PASS |
   | apple-frameworks | "Fix this Sendable error" | silent | PASS (swift-concurrency fired instead) |

   **The one FAIL, diagnosed rather than papered over.** "Build the settings screen UI" did not
   invoke `apple-design` within the 2-turn budget
   (`task-7-evals/apple-design-fire-01.log`). Root-caused with three supplementary runs, not
   assumed: (1) same prompt, repo cwd, 6 turns — still no `apple-design` invocation
   (`task-7-evals/apple-design-fire-01-supplement.log`); (2) same prompt, run from the
   `StudioFixture` app fixture (the correct environment for a "build UI" request) at the original
   2-turn budget — still `error_max_turns`
   (`task-7-evals/apple-design-fire-01-fixture.log`); (3) same prompt, fixture, 10 turns,
   `--permission-mode auto` — session completes successfully (`num_turns: 8`, no error) but still
   never invokes `apple-design`
   (`task-7-evals/apple-design-fire-01-fixture-longer.log`). All three runs show the identical
   pattern: the model opens with `superpowers:brainstorming` — a separately-installed,
   globally-enabled plugin (`claude plugin list` confirms `superpowers@claude-plugins-official`,
   user scope, enabled) whose own description states "You MUST use this before any creative work"
   — and stays inside that skill's own requirements-gathering flow (exploring the repo, reading
   `ContentView.swift`, asking a clarifying question about target platform/scope) for the entire
   run. This is not an `apple-design` description defect: the routing collision is decided by the
   *competing* skill's own imperative gate, before `apple-design`'s description is ever in
   contention, and a single non-interactive `-p` session cannot answer brainstorming's clarifying
   question and hand off to implementation — so no edit to `apple-design/SKILL.md`'s frontmatter
   `description` was made, since three independent supplementary runs already show it would not
   change the outcome. **`apple-design`'s description is unchanged from Task 5** (verbatim from
   the brief, per `task-5-report.md`); this finding is recorded as an eval-methodology caveat for
   "Build X" (from-scratch, imperative) style prompts under headless single-shot sessions in an
   environment with `superpowers` also installed, not as a defect fix. This from-scratch-"Build X"
   specificity is corroborated within the same eval batch: `apple-design-fire-05` — "Add a
   confirmation flow before deleting," itself an "adding functionality" prompt that could plausibly
   collide with the same brainstorming gate — invokes `apple-design` directly with no
   brainstorming detour (`task-7-evals/apple-design-fire-05.log`), the same clean-fire pattern as
   the other four passing `apple-design` should-fire prompts. The collision is specific to a
   from-scratch "Build X [screen/UI]" phrasing, not to "build/add" verbs in general. Every other
   should-fire
   prompt across all six skills (including four other `apple-design` should-fire prompts and five
   Phase 1 regression should-fire prompts) invoked its target skill cleanly within budget, and
   every should-NOT-fire prompt across all six skills correctly stayed silent (routing instead to
   the actually-relevant skill where one applied). Net: 19/20 pass.

**Net:** items 1–4 full PASS; item 5 PASS on the scope Phase 2 owned (import), with the
already-tracked runtime-exercise gap left open in `docs/deferred.md` rather than claimed closed;
item 6 (trigger evals) 19/20, with the one miss root-caused to a cross-plugin routing interaction
external to this plugin's own trigger descriptions, not a design or distillation defect.
