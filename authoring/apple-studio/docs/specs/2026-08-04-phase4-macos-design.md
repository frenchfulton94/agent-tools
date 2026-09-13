# apple-studio Phase 4: Native macOS — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`, "Phase 4 — Long tail").
Decisions taken 2026-08-04 in brainstorming; this doc is the input to the
Phase 4 implementation plan.

## Goal

Ship the native-Mac slice: one new skill, `apple-macos`, covering how to
build a proper Mac app with SwiftUI — app/scene structure, windows, menus
and commands, AppKit interop, sandbox and file access — built to charter
quality, toolkit-completing (no imminent Mac app driving it). Version bump
to 0.5.0.

Phase 4 direction chosen from the charter's unscheduled long-tail list:
the macOS slice, aimed at building proper native Mac apps (not iOS→Mac
porting — that goal was considered and not chosen).

## Deliverables

**New skill `plugin/skills/apple-macos/`** — lean SKILL.md (triggers,
routing, mac-development judgment) + `evals/triggers.md` + four references:

1. `mac-app-structure.md` — which-Mac-path judgment (native SwiftUI vs
   Catalyst vs iPad-on-Apple-Silicon vs multiplatform target — Catalyst at
   judgment level only, live-doc-sourced); scene types (`WindowGroup`,
   `Window`, `Settings`, `DocumentGroup`, `MenuBarExtra`); document-based
   and menu-bar app shapes; Mac app lifecycle vs iOS habits.
2. `mac-windows-menus-commands.md` — window management and restoration,
   the menu/commands system, keyboard shortcuts, toolbars, focus — the
   mechanics Mac users judge an app by.
3. `appkit-interop.md` — when SwiftUI-on-Mac falls short and what to do:
   `NSViewRepresentable`/`NSViewControllerRepresentable`, coordinators,
   the common escape hatches, judgment on interop vs waiting vs
   redesigning.
4. `mac-sandbox-and-files.md` — App Sandbox, entitlements,
   security-scoped bookmarks, file-access UX patterns, hardened runtime —
   the parts needed for Mac App Store apps anyway.

**Routing discipline (cross-refs, no duplication):** `apple-design` keeps
look/feel/HIG judgment (its existing mac HIG content stays where it is);
`apple-macos` owns structure and mechanics. `app-release` keeps all
distribution; Developer ID/notarization stays deferred with its existing
trigger (shipping outside the Mac App Store). `apple-frameworks` primers
keep API-catalog duty.

**No new agent this phase** (the Phase 3 agent-gate verdict stands as
measured). The Catalyst book is **not converted at all** — it serves the
porting goal that was not chosen, and the judgment residue about when
Catalyst is the right path comes from live docs.

## Sources and pipeline

Same pipeline as Phases 1–3: `pipeline/convert.sh` on
`macOS_by_Tutorials_v1.0.0.epub` only (present in
`~/Documents/Apple Books/`) → gitignored `corpus/`; two maps under
`pipeline/maps/`: `apple-macos-books.md` (chapter → target reference) and
`apple-macos-live.md` (live-doc endpoints → target reference).

**Staleness stance:** the book is v1.0.0 (~2022) — it contributes
**durable judgment only** (Mac app anatomy, Mac-user expectations,
menu/window/document mental models). Everything API-specific is distilled
from live docs: SwiftUI macOS scene/commands/Settings DocC pages, AppKit
interop pages, App Sandbox/entitlements pages, cited per the
live-docs-first rule.

**Endpoint probing (binding):** every live endpoint assumed by the maps is
probed (actually fetched) during planning before any distillation task is
written against it. Expected-but-missing pages are recorded in the map
with `MISSING:`.

## Opening task: Phase 3 debt + kill-switch grace

Task 0 of the plan:

1. Sweep the five Phase 3 ledger-deferred minors
   (`.superpowers/sdd/2026-08-04-phase3-release-ops/progress.md`): fix the
   actionable ones (Task 0's SKILL.md annotation wording, Task 1's
   books-map subheader format, Task 2's submission-reference attribution
   note); record the flag-only ones (Task 3's testflight file length,
   Task 4's push-notifications scope note) as accepted, with rationale.
2. Record the kill-switch grace decision in `docs/deferred.md`: both
   reviewer agents (`swift-reviewer`, `design-reviewer`) keep one-phase
   grace despite the Phase 3 measurement (0 genuine non-fixture
   invocations). Rationale: no real feature work has happened yet for them
   to be used in — the measurement cannot distinguish "not useful" from
   "not yet needed". **Explicit trigger: the kill-switch rule fires for
   real at the Phase 5 opening measurement unless a genuine non-fixture
   invocation has occurred by then.**

## Verification (free-tier, definition of done)

- Trigger evals for `apple-macos`: fires on Mac-structure / menus /
  interop / sandbox requests; silent on iOS-only, look-and-feel
  (`apple-design`), and distribution (`app-release`) prompts. One
  should-fire + one should-NOT regression sample per prior skill, as in
  Phase 3. Eval-harness caveats carried forward from Phase 3: run with
  `--allowedTools "Skill Read"`, use a fixture cwd for from-scratch
  prompts, and avoid "build X" phrasing in eval prompts (superpowers
  process-skill preemption, documented in the Phase 3 verification
  results).
- Consume tests with captured logs; every consume-test prompt validated
  against actual reference coverage before it enters the plan. Evidence
  pointers as `<file>:<line-range>`.
- Real exercise where free: StudioFixture is Multiplatform — build and
  run the mac target headless (`xcodebuild -destination 'platform=macOS'`),
  then temporarily exercise two documented surfaces end-to-end — a
  `Settings` scene and a `MenuBarExtra` — exactly as the references
  document them, with screenshot evidence, then revert (the Phase 3
  Task-7 pattern: documented commands and code executed as written,
  failures indict the docs).
- `claude plugin validate . --strict` passes at every commit touching
  `plugin/`; version bump to 0.5.0 in the final task only; re-import into
  Xcode after merge (operational rule, `docs/deferred.md` item 3).

## Out of scope

- Catalyst depth (book unconverted; judgment-level section only, in
  `mac-app-structure.md`).
- Developer ID / notarization / distribution outside the Mac App Store
  (existing deferred trigger stands: revisit when shipping outside MAS).
- AppKit-first development (SwiftUI-first baseline; AppKit appears only
  as interop).
- iOS→Mac porting workflows beyond the which-path judgment section.
- watchOS/tvOS/visionOS.
- The rest of the long-tail list (ML, animations depth, Advanced Git,
  Flight School guides) — each waits for its own demand.

## Phase 4 verification results (2026-08-04)

**Minors swept + kill-switch grace recorded.** Three actionable Phase 3
ledger minors fixed (`plugin/skills/apple-design/SKILL.md:14` empty-states
wording; `pipeline/maps/app-release-books.md` flat-bullet sweep, with a
disclosed judgment call leaving the `### SKIP` headers as-is;
`plugin/skills/app-release/references/app-store-submission.md:59`
five-principle attribution note); two flag-only minors recorded as accepted
at `docs/deferred.md:72-82` (`## Accepted (no action)`). Commit `0141f45`.
Kill-switch grace decision recorded at `docs/deferred.md:42-48`, trigger
verbatim: "the kill-switch rule fires for real at the Phase 5 opening
measurement unless a genuine non-fixture invocation has occurred by then."

**Sources/pipeline + four references with verified headers.** Book
converted, maps built: `pipeline/maps/apple-macos-books.md` (18 ranges
across 4 targets, `:1-38`) and `pipeline/maps/apple-macos-live.md` (72
verified endpoints; 1 `MISSING:` entry at `:88` —
`swiftui/scene-restoration`, 404 at both the planning probe and this
task's re-confirmation — substitute
`swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos`
fetched 200 and folded into `mac-windows-menus-commands.md`). Commit
`47b906f`. Four references shipped, each with a verified header
(`> verified: ... \n> sources: ...`) at lines 1-2:
`plugin/skills/apple-macos/references/mac-app-structure.md` (198 lines),
`mac-windows-menus-commands.md` (194 lines), `appkit-interop.md` (106
lines), `mac-sandbox-and-files.md` (105 lines). Commits `6769598`
(structure + windows/menus/commands), `10db2b1` (citation-folding fix —
MenuBarExtra auto-termination citation separated from this file's own
no-combine-scene-types inference, `mac-app-structure.md:184`), `1769463`
(appkit-interop + sandbox/files).

**Skill consume-test.** `plugin/skills/apple-macos/SKILL.md:1-29`
(frontmatter + routing), `plugin/skills/apple-macos/evals/triggers.md:1-14`
(7 should-fire / 4 should-NOT). Consume-test log
`task-4-consume-test.log`: skill invocation at line 13, reference
`mac-sandbox-and-files.md` read in full at lines 20-21 (106 lines
returned), final answer visibly applies the reference's bookmark
persistence and start/stop discipline at lines 23-24. Commit `9487cdc`.

**Free-tier exercise, both screenshots.** `task-5-macbuild.log` (baseline
mac build, `** BUILD SUCCEEDED **` on the unmodified fixture);
`task-5-exercise.log` + `task-5-rebuild.log` (Settings and MenuBarExtra
scenes from `mac-app-structure.md` inserted verbatim, rebuilt, `**
BUILD SUCCEEDED **` on the first attempt); `task-5-menubar.png` (hammer
glyph confirmed live in the menu bar); `task-5-settings.png` (Settings
window opened via Cmd-, showing General/Advanced tabs with the
`Tab(_:systemImage:content:)` view-builder form rendered). Fixture
reverted clean (`git -C ~/Projects/StudioFixture status --porcelain`
empty before and after; no commits). Honest caveat, carried verbatim from
the Task 5 report: "the reference's `.tabItem` fallback path for pre-15.0
deployment targets was not exercised end-to-end in this task, since
StudioFixture's deployment target (27.0) never triggers it. That fallback
remains verified only via the Task 2 implementer's standalone `swiftc
-typecheck` check noted inline in the reference, not via a full app
build/run."

**Eval table (25/25 pass, zero misfires).** All 7 apple-macos should-fire
and all 4 should-NOT prompts, plus a 1-fire/1-should-NOT regression sample
per prior skill (apple-design's fire prompt substituted per the Phase 3
precedent: "Does this screen feel native?", run from `~/Projects/StudioFixture`
cwd). Method: `claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2
--output-format stream-json --verbose --allowedTools "Skill Read"`, one
log per prompt (`task-6-eval-<skill>-<fire|nofire>-<n>.log`, 25 files),
verdict by grep for `"name":"Skill","input":{"skill":"apple-studio:<skill>"`.

| # | Prompt | Expected | Invoked | Verdict |
|---|---|---|---|---|
| 1 | Add a Settings window with Cmd-comma to my Mac app | apple-macos fires | apple-macos | PASS |
| 2 | My Mac app needs a menu bar extra with a popover | apple-macos fires | apple-macos | PASS |
| 3 | How do I add custom menus and keyboard shortcuts on macOS? | apple-macos fires | apple-macos | PASS |
| 4 | Make this a document-based Mac app | apple-macos fires | apple-macos | PASS |
| 5 | I need NSTableView features SwiftUI lacks - how do I wrap it? | apple-macos fires | apple-macos | PASS |
| 6 | My sandboxed Mac app can't reopen the folder the user picked last launch | apple-macos fires | apple-macos | PASS |
| 7 | Should this be a native Mac app, Catalyst, or just the iPad app on Mac? | apple-macos fires | apple-macos | PASS |
| 8 | Does this Mac window layout feel native? | apple-macos silent (apple-design) | apple-design | PASS |
| 9 | Set up TestFlight for the Mac beta | apple-macos silent (app-release) | app-release | PASS |
| 10 | Fix this Sendable warning | apple-macos silent (swift-concurrency) | swift-concurrency | PASS |
| 11 | Run the mac target and screenshot it | apple-macos silent (xcode-loop) | xcode-loop | PASS |
| 12 | Set up TestFlight so external testers can try the beta | app-release fires | app-release | PASS |
| 13 | Build and run the app on the simulator | app-release silent (xcode-loop) | xcode-loop | PASS |
| 14 | Does this screen feel native? (cwd StudioFixture) | apple-design fires | apple-design | PASS |
| 15 | Fix this Sendable warning | apple-design silent (swift-concurrency) | swift-concurrency | PASS |
| 16 | Does Apple have a native way to show tips/onboarding hints? | apple-frameworks fires | apple-frameworks | PASS |
| 17 | Fix this Sendable error | apple-frameworks silent (swift-concurrency) | swift-concurrency | PASS |
| 18 | Where should this view's state live? | swift-architecture fires | swift-architecture | PASS |
| 19 | Fix this Sendable warning | swift-architecture silent (swift-concurrency) | swift-concurrency | PASS |
| 20 | Fix this 'capture of non-Sendable type' error | swift-concurrency fires | swift-concurrency | PASS |
| 21 | Where should this state live? | swift-concurrency silent (swift-architecture) | swift-architecture | PASS |
| 22 | Write tests for this view model | swift-testing fires | swift-testing | PASS |
| 23 | Run the test suite | swift-testing silent (xcode-loop) | xcode-loop | PASS |
| 24 | Build the app and make sure it compiles | xcode-loop fires | xcode-loop | PASS |
| 25 | Explain actor isolation in Swift 6 | xcode-loop silent (swift-concurrency) | swift-concurrency | PASS |

25/25 PASS, zero misfires diagnosed, zero description changes made.
`error_max_turns` exits (the 2-turn cap) occurred on 22/25 prompts as
expected per the brief and were not treated as failures; 3/25 — rows 15
(`apple-design-nofire-1`), 17 (`apple-frameworks-nofire-1`), and 19
(`swift-architecture-nofire-1`) — completed within the turn budget
(`success`) since those particular no-fire answers resolved faster than a
skill-launch path.

**Strict validation.** `claude plugin validate . --strict` → "✔ Validation
passed", zero warnings, captured to `task-6-validate.log`.
