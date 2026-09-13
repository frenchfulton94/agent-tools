# apple-studio Phase 4: Native macOS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sweep the Phase 3 deferred minors, record the kill-switch grace decision, then ship the native-Mac slice: an `apple-macos` skill (four references distilled from live Apple docs + one judgment-only book) covering Mac app/scene structure, windows/menus/commands, AppKit interop, and sandbox/file access. Version bump to 0.5.0.

**Architecture:** Same two-layer pattern as Phases 1–3: knowledge references distilled per the pipeline, consumed by a lean SKILL.md. Primary truth is live docs (the book is v1.0.0 ~2022 — durable judgment only). Verification is free-tier: mac-target build of StudioFixture plus end-to-end exercise of two documented surfaces (`Settings` scene + `MenuBarExtra`), trigger evals, consume test. Spec: `docs/specs/2026-08-04-phase4-macos-design.md`.

**Tech Stack:** Claude Code plugin components, existing `pipeline/` (convert.sh, distill-prompt.md), pandoc, DocC JSON endpoints (probed 2026-08-04 — all listed endpoints returned 200, one recorded MISSING; see Task 1), `xcodebuild -destination 'platform=macOS'`, `screencapture`, `osascript`.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-4` (create from `main` at start). All paths relative to repo root unless absolute.
- Toolchain: Xcode 27.0 beta active; fixture app `~/Projects/StudioFixture` (Multiplatform, scheme `StudioFixture`; leave its git tree clean after any test).
- Spec boundary (verbatim): the skill serves "building proper native Mac apps (not iOS→Mac porting)"; "Catalyst at judgment level only, live-doc-sourced"; "the Catalyst book is **not converted at all**". No new agent this phase.
- Live-docs-first: `macOS_by_Tutorials_v1.0.0.epub` (~2022) contributes durable judgment ONLY (Mac app anatomy, Mac-user expectations, menu/window/document mental models); every API-specific claim is distilled from live docs and cited (canonical human URL in headers; fetch via DocC JSON endpoints `https://developer.apple.com/tutorials/data/documentation/<path>.json` — use dash forms, e.g. `security/app-sandbox`; underscore forms 301-redirect).
- Reference files: CONVENTIONS.md header block, decision-grade only, ~100–250 lines, no copied book/doc prose (own words; short attributed quotes with quotation marks OK), no remaining `[VERIFY` markers at commit.
- Evidence standard (standing): every consume-test/verification claim is backed by a captured log under the SDD workspace, with quoted lines in the report; verification tables use `file:line-range` evidence pointers.
- **Implementer-brief template text (copy VERBATIM into every subagent brief that runs nested sessions):** "Run nested `claude` sessions synchronously in the foreground and wait for completion — never background-and-wait. When the nested session must write files, use `--permission-mode auto`."
- Consume-test prompts: before running any consume-test, re-validate the prompt's topic against the ACTUAL shipped reference content (grep the reference for the topic); if coverage is missing, adjust the prompt to a covered topic and record the adjustment in the task report. From-scratch prompts get a fixture cwd and `--max-turns` ≥ 25.
- **Eval-harness rules (Phase 3 lessons, binding):** headless eval/consume commands include `--allowedTools "Skill Read"`; eval prompts avoid "build X" phrasing (the user-level superpowers plugin routes "build X" to its brainstorming skill, which ends a headless session before any implementation skill can fire — documented in the Phase 3 verification results); from-scratch prompts run from a fixture cwd, not the plugin repo.
- Commit after every task minimum. Version bump to 0.5.0 only in Task 6.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Branch + Phase 3 deferred-minors sweep + kill-switch grace

**Files:**
- Modify: `plugin/skills/apple-design/SKILL.md` (empty-states annotation wording, ~line 14)
- Modify: `pipeline/maps/app-release-books.md` (subheader format)
- Modify: `plugin/skills/app-release/references/app-store-submission.md` (~line 78, attribution note)
- Modify: `docs/deferred.md` (kill-switch grace decision + accepted-minors record)

**Interfaces:**
- Consumes: the Phase 3 ledger (`.superpowers/sdd/2026-08-04-phase3-release-ops/progress.md`) — the authoritative minors list; `docs/deferred.md` item 1 (the Phase 3 measurement).
- Produces: a minors-free tree and the recorded grace decision Task 6's spec-append cites.

- [ ] **Step 1: Create the branch**

```bash
cd ~/Projects/apple-studio && git checkout -b phase-4
```

- [ ] **Step 2: Fix the empty-states annotation wording.** `apple-design/SKILL.md` ~line 14 (verify: `grep -n "SwiftUI conventions" plugin/skills/apple-design/SKILL.md`) says the empty-states coverage comes "from SwiftUI conventions"; the actual hig-patterns.md content is a HIG-sourced Tab Bars bullet. Reword the annotation to say the pattern is HIG-sourced (read the hig-patterns.md empty-state passage first and make the SKILL.md line truthful to it).

- [ ] **Step 3: Flatten the books-map subheaders.** `pipeline/maps/app-release-books.md` uses `###` per-target-file subheaders under each book section — a cosmetic deviation from the Phase 2 flat-bullet precedent. Convert each subheadered group to flat bullets of the form `- L<start>–L<end>: <chapter title> → <target reference file>` (the Phase 1–2 map format), preserving every mapping unchanged.

- [ ] **Step 4: Attribute the five-principle taxonomy.** `app-store-submission.md` ~line 78 (verify: `grep -n "five" plugin/skills/app-release/references/app-store-submission.md | head`) uses the book's five-principle taxonomy labels without attribution. Add a short attribution — either quotation marks on the labels or an inline "(the distribution book's framing)" note — matching the file's existing citation style.

- [ ] **Step 5: Record the two accepted flag-only minors** in `docs/deferred.md` as a short "Accepted (no action)" note appended to the deferred list: (a) `testflight-and-versioning.md` is 80 lines, under the ~100 floor — reviewer confirmed no missing depth (cross-ref discipline); (b) `push-notifications.md:214-220` Push Notification Console + curl/openssl debugging exceeds the spec's named examples — accurate and useful, accepted as a deliberate scope expansion, file at 240/250 lines.

- [ ] **Step 6: Record the kill-switch grace decision** in `docs/deferred.md`, appended to item 1 (keep the Phase 3 measurement text intact):

> **Phase 4 decision (2026-08-04): one-phase grace.** Both reviewer agents (`swift-reviewer`, `design-reviewer`) are kept unchanged despite the 0-genuine-use measurement. Rationale: no real feature work has happened yet for them to be used in — the measurement cannot distinguish "not useful" from "not yet needed". **Trigger: the kill-switch rule fires for real at the Phase 5 opening measurement unless a genuine non-fixture invocation has occurred by then.**

- [ ] **Step 7: Validate + commit**

```bash
claude plugin validate . --strict
git add -A && git commit -m "chore: Phase 3 deferred-minors sweep + kill-switch grace decision"
```

---

### Task 1: Convert the macOS book + build the two distillation maps

**Files:**
- Create: `corpus/macos-by-tutorials-v1-0-0.md` (+ `.toc.md`) — gitignored
- Create: `pipeline/maps/apple-macos-books.md` (chapter map, flat-bullet format)
- Create: `pipeline/maps/apple-macos-live.md` (live-doc endpoint map)

**Interfaces:**
- Consumes: `pipeline/convert.sh`; the endpoints pre-probed during planning (probed 2026-08-04; all listed below returned 200 except the one recorded MISSING).
- Produces: maps that Tasks 2–3 dispatch from. Book-map format: `- L<start>–L<end>: <chapter title> → <target reference file>`. Live-map format: `## <reference file>` sections listing `- <canonical human URL> → <DocC JSON endpoint>`.

- [ ] **Step 1: Convert the book**

```bash
cd ~/Projects/apple-studio && pipeline/convert.sh \
  "/Users/michaelfrenchfultonjr/Documents/Apple Books/macOS_by_Tutorials_v1.0.0.epub"
```

Expected: one `.md` + one `.toc.md` in `corpus/`. Spot-check a mid-book heading via `sed -n '<line>p'`.

- [ ] **Step 2: Build `pipeline/maps/apple-macos-books.md`.** From the TOC, map chapters to targets — the book is **judgment-only** (see Global Constraints):
  - → `mac-app-structure.md`: chapters on Mac app anatomy, scenes/windows/documents mental models, menu-bar-app concepts.
  - → `mac-windows-menus-commands.md`: chapters on menus, toolbars, keyboard-driven workflows, window behavior expectations.
  - → `appkit-interop.md`: chapters demonstrating AppKit integration (the *when and why*, not the ~2022 API specifics).
  - → `mac-sandbox-and-files.md`: chapters on sandboxing, file access, persistence UX on the Mac.
  - Skip pure walkthrough chapters carrying no durable judgment, and any distribution chapters (`app-release` territory). Verify every range start with `sed -n '<start>p'`. Chapters that fit no target get no mapping — do not force them.

- [ ] **Step 3: Build `pipeline/maps/apple-macos-live.md`.** Seed with the endpoints probed during planning (2026-08-04; DocC JSON prefix `https://developer.apple.com/tutorials/data/documentation/`):
  - → `mac-app-structure.md`: `swiftui/app-organization` (index — enumerate), `swiftui/scenes` (index — enumerate), `swiftui/windowgroup`, `swiftui/window`, `swiftui/settings`, `swiftui/documentgroup`, `swiftui/documents` (index — enumerate), `swiftui/menubarextra`, `uikit/mac-catalyst` (judgment section only).
  - → `mac-windows-menus-commands.md`: `swiftui/windows` (index — enumerate), `swiftui/commands`, `swiftui/commandmenu`, `swiftui/commandgroup`, `swiftui/toolbars` (index — enumerate), `swiftui/focus` (index — enumerate), `swiftui/view/keyboardshortcut(_:modifiers:)`.
  - → `appkit-interop.md`: `swiftui/appkit-integration` (index — enumerate), `swiftui/nsviewrepresentable`, `swiftui/nsviewcontrollerrepresentable`, `appkit` (index — for gap-checking only, not for distilling AppKit depth).
  - → `mac-sandbox-and-files.md`: `security/app-sandbox` (index — enumerate; dash form, underscore 301s), `security/hardened-runtime`, `bundleresources/entitlements` (index — enumerate the sandbox/file entitlement children), `foundation/nsurl/bookmarkdata(options:includingresourcevaluesforkeys:relativeto:)`, `swiftui/view/fileimporter(ispresented:allowedcontenttypes:oncompletion:)`.
  - Record now-known gaps: `MISSING: swiftui/scene-restoration (404 at planning probe — restoration coverage comes from the windows/scenes index children instead)`.
  - Fetch each index endpoint, enumerate its child topics, and add relevant children under the owning reference. Every endpoint listed must have returned JSON when actually fetched — no invented endpoints; record expected-but-missing pages as `MISSING:`.

- [ ] **Step 4: Commit**

```bash
git add pipeline/maps && git commit -m "feat: Phase 4 distillation maps (macOS book + live mac endpoints)"
```

---

### Task 2: Distill `mac-app-structure.md` + `mac-windows-menus-commands.md`

**Files:**
- Create: `plugin/skills/apple-macos/references/mac-app-structure.md`
- Create: `plugin/skills/apple-macos/references/mac-windows-menus-commands.md`

**Interfaces:**
- Consumes: `pipeline/maps/apple-macos-live.md` (primary) + `pipeline/maps/apple-macos-books.md` (judgment ranges); `pipeline/distill-prompt.md` (adapted as in Phases 2–3: corpus-lines input becomes "Fetch these DocC JSON endpoints: <the map's list for your file>" plus "…and these corpus line ranges for judgment only"; currency rule becomes "cite the canonical human URL per claim cluster; `[VERIFY: ...]` for anything inferred beyond fetched text").
- Produces: the two references (exact filenames above) read by SKILL.md (Task 4) and exercised by Task 5.

- [ ] **Step 1: Dispatch two distiller subagents** (parallel, model sonnet), one per file, with the adapted pipeline prompt. Include the implementer-brief template text from Global Constraints verbatim. Content requirements from the spec:
  - `mac-app-structure.md`: which-Mac-path judgment (native SwiftUI vs Catalyst vs iPad-on-Apple-Silicon vs multiplatform target — Catalyst from `uikit/mac-catalyst` live page only, judgment level, one section max); the scene types `WindowGroup`, `Window`, `Settings`, `DocumentGroup`, `MenuBarExtra` with when-to-use judgment and minimal correct declarations; document-based and menu-bar app shapes; Mac app lifecycle vs iOS habits (no scene phases the iOS way, apps live without windows, termination judgment). **Must include a minimal correct `Settings` scene snippet and a minimal correct `MenuBarExtra` snippet — Task 5 executes both verbatim; they must compile as written when pasted into a SwiftUI `App`.**
  - `mac-windows-menus-commands.md`: window management and restoration (what restores for free, what the app owns), the menu/commands system (`Commands`, `CommandMenu`, `CommandGroup` placements, replacing/extending standard menus), keyboard shortcuts discipline, toolbars on Mac, the focus system (`@FocusState`/focused values at judgment level).
  - Book input is judgment-only: any book claim about API mechanics gets `[VERIFY:]` and is checked against the live pages (the book is ~2022 — `MenuBarExtra` and current windowing APIs postdate it; assume its mechanics are stale).

- [ ] **Step 2: Resolve `[VERIFY:]` flags** (fetch the relevant endpoint; drop unverifiable inferences). `grep -rn "VERIFY" plugin/skills/apple-macos/` → empty.

- [ ] **Step 3: Add CONVENTIONS.md headers** (`> verified: 2026-08 against <human URLs checked>` / `> sources: macOS by Tutorials v1.0.0 (judgment only), live Apple docs`).

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-macos && git commit -m "feat: apple-macos structure + windows/menus/commands references"
```

---

### Task 3: Distill `appkit-interop.md` + `mac-sandbox-and-files.md`

**Files:**
- Create: `plugin/skills/apple-macos/references/appkit-interop.md`
- Create: `plugin/skills/apple-macos/references/mac-sandbox-and-files.md`

**Interfaces:**
- Consumes: both maps; adapted distill prompt as in Task 2; siblings to read before writing: `plugin/skills/apple-design/references/platform-idioms.md` (mac look/feel stays there) and `plugin/skills/app-release/references/signing-and-provisioning.md` (entitlement *signing* mechanics stay there).
- Produces: the two references (exact filenames) for Tasks 4–5.

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet; brief template text verbatim). Content requirements:
  - `appkit-interop.md`: when SwiftUI-on-Mac genuinely falls short and the decision framework (interop vs redesign vs wait — with the instruction to verify current gaps against live docs, since the gap list shrinks); `NSViewRepresentable`/`NSViewControllerRepresentable` mechanics (make/update lifecycle, `Coordinator` for delegates/targets, sizing), passing data both directions, common escape hatches at judgment level (rich text, advanced tables/outlines, custom drawing/event handling). AppKit itself is NOT distilled in depth — the `appkit` index is for gap-checking claims only.
  - `mac-sandbox-and-files.md`: App Sandbox model and why MAS requires it; entitlements for file access (`user-selected`, downloads/pictures/music/movies containers, network client/server) — what each grants, judgment on minimal sets; security-scoped bookmarks end-to-end (obtain via `fileImporter`/`NSOpenPanel` → `bookmarkData(options: .withSecurityScope …)` → resolve + `startAccessingSecurityScopedResource`/stop discipline); file-access UX patterns (asking once, remembering access, graceful degradation); hardened runtime and its relationship to the sandbox. Entitlement *signing/provisioning* mechanics cross-ref `app-release`'s `signing-and-provisioning.md` rather than restating.
  - Book input judgment-only, `[VERIFY:]` discipline as in Task 2.

- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Headers as in Task 2 Step 3.

- [ ] **Step 3: Sibling-consistency check.** Grep both new files for restatements: mac HIG/idiom guidance (belongs to `apple-design` — cross-ref), signing mechanics (belongs to `app-release` — cross-ref), build/run commands (belong to `xcode-loop`). Replace any restatement with a one-line cross-ref.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-macos && git commit -m "feat: apple-macos appkit-interop + sandbox/files references"
```

---

### Task 4: `apple-macos` SKILL.md + evals + consume-test

**Files:**
- Create: `plugin/skills/apple-macos/SKILL.md`
- Create: `plugin/skills/apple-macos/evals/triggers.md`

**Interfaces:**
- Consumes: the four references from Tasks 2–3 (exact filenames as listed there).
- Produces: the complete skill for Tasks 5–6.

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: apple-macos
description: Building proper native Mac apps with SwiftUI - app and scene structure (WindowGroup, Window, Settings, DocumentGroup, MenuBarExtra), document-based and menu bar apps, window management and restoration, the menu and commands system, keyboard shortcuts, toolbars, focus, AppKit interop via NSViewRepresentable and coordinators, App Sandbox, entitlements, security-scoped bookmarks, and file-access patterns. Also owns which-Mac-path judgment (native SwiftUI vs Mac Catalyst vs iPad app on Apple silicon). Use when structuring a Mac app, adding scenes, menus, commands, or shortcuts, wrapping AppKit views, or debugging sandbox and file-access behavior. Not for look-and-feel or HIG judgment (apple-design), distribution and signing (app-release), or iOS-only work.
---

# Native macOS (structure and mechanics)

Scope: how a proper Mac app is built. Look/feel/HIG judgment belongs to
apple-design; distribution and signing to app-release; the build/run loop
to xcode-loop.

Read the reference for the decision at hand:
- Which Mac path, scene types, document/menu-bar app shapes, lifecycle → `references/mac-app-structure.md`
- Windows, menus, commands, shortcuts, toolbars, focus → `references/mac-windows-menus-commands.md`
- SwiftUI falls short on Mac, AppKit escape hatches → `references/appkit-interop.md`
- Sandbox, entitlements, scoped bookmarks, file access → `references/mac-sandbox-and-files.md`

Rules that always apply:
- A Mac app is judged by its menus, shortcuts, and windows - wire the
  commands system early, not as polish.
- Design with the sandbox on from day one: retrofitting entitlements and
  scoped bookmarks onto an existing file model is rework.
- Reach for AppKit interop only after checking the current SwiftUI surface
  (appkit-interop.md's decision framework) - the gap list shrinks; verify
  against live docs before wrapping.
- Mac users expect restoration - windows, sizes, state. If it vanishes on
  relaunch, that is a bug, not a nicety.
- Look/feel and idiom questions → apple-design; shipping and signing →
  app-release.
```

- [ ] **Step 2: Write `evals/triggers.md`** (note: no "build X" phrasing — Global Constraints eval-harness rule)

```markdown
# apple-macos trigger evals
## Should fire
- "Add a Settings window with Cmd-comma to my Mac app"
- "My Mac app needs a menu bar extra with a popover"
- "How do I add custom menus and keyboard shortcuts on macOS?"
- "Make this a document-based Mac app"
- "I need NSTableView features SwiftUI lacks - how do I wrap it?"
- "My sandboxed Mac app can't reopen the folder the user picked last launch"
- "Should this be a native Mac app, Catalyst, or just the iPad app on Mac?"
## Should NOT fire
- "Does this Mac window layout feel native?"   (apple-design)
- "Set up TestFlight for the Mac beta"         (app-release)
- "Fix this Sendable warning"                  (swift-concurrency)
- "Run the mac target and screenshot it"       (xcode-loop)
```

- [ ] **Step 3: Pre-validate the consume-test prompt** (Global Constraints rule): `grep -in "security-scoped\|bookmark" plugin/skills/apple-macos/references/mac-sandbox-and-files.md` — confirm the reference actually covers scoped-bookmark persistence across relaunch. If not covered, pick a covered sandbox topic from the file and adjust the Step 4 prompt; record the adjustment.

- [ ] **Step 4: Consume-test with captured evidence.** From `~/Projects/StudioFixture`:

```bash
claude --plugin-dir ~/Projects/apple-studio/plugin -p "My sandboxed Mac app lets the user pick a folder with fileImporter, but after relaunch it can't read that folder anymore. Explain what's wrong and exactly how to fix it. Answer now, no clarifying questions." --output-format stream-json --verbose --max-turns 15 --allowedTools "Skill Read"
```

Save to the SDD workspace as `task-4-consume-test.log`. Evidence required: skill invocation (`apple-studio:apple-macos`), ≥1 reference Read (expect `mac-sandbox-and-files.md`), answer visibly applying its content (security-scoped bookmarks, `.withSecurityScope`, start/stop accessing discipline). Fixture tree stays clean (read-only prompt; verify `git -C ~/Projects/StudioFixture status --porcelain` is empty).

- [ ] **Step 5: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/skills/apple-macos && git commit -m "feat: apple-macos skill (SKILL.md + evals)"
```

---

### Task 5: Free-tier exercise — mac build + Settings/MenuBarExtra end-to-end

**Files:**
- Create (SDD workspace only, not committed to plugin): `task-5-macbuild.log`, `task-5-exercise.log`, screenshots `task-5-menubar.png`, `task-5-settings.png`

**Interfaces:**
- Consumes: `mac-app-structure.md`'s `Settings` and `MenuBarExtra` snippets (Task 2) — this task executes what the reference claims, verbatim.
- Produces: captured evidence for Task 6's verification table; corrections back into the references if any documented snippet fails as written.

- [ ] **Step 1: Baseline mac build** of the unmodified fixture:

```bash
cd ~/Projects/StudioFixture && xcodebuild build -scheme StudioFixture \
  -destination 'platform=macOS' -derivedDataPath /tmp/StudioFixture-mac 2>&1 | tail -5
```

Expected: `** BUILD SUCCEEDED **`. Save output → `task-5-macbuild.log`. If the Multiplatform fixture has no mac destination, record the exact error, add the mac destination in Xcode-project terms as a fixture-only change (not plugin content), and note it in the report.

- [ ] **Step 2: Temporarily modify `StudioFixture/StudioFixtureApp.swift`:** add a `Settings` scene and a `MenuBarExtra` scene **copied verbatim from `mac-app-structure.md`'s snippets** (adjusting only identifier names/labels to say "StudioFixture Phase 4"). If a snippet does not compile as written, that is a reference defect: fix the reference first, then use the fixed snippet, and record the correction. Rebuild with the Step 1 command → `** BUILD SUCCEEDED **`.

- [ ] **Step 3: Launch + capture evidence.**

```bash
open /tmp/StudioFixture-mac/Build/Products/Debug/StudioFixture.app && sleep 3
screencapture -x /tmp/task-5-menubar.png   # menu bar extra visible in the bar
osascript -e 'tell application "StudioFixture" to activate' \
  -e 'tell application "System Events" to keystroke "," using command down' && sleep 2
screencapture -x /tmp/task-5-settings.png  # Settings window open
```

**CHECKPOINT (user-assisted fallback, only if needed):** if `osascript`/System Events is blocked by an automation-permission prompt, ask the user to either grant it or manually press Cmd-, in the running app (and confirm the menu bar extra is visible), then re-capture. Verify both screenshots show the expected surfaces (Read the PNGs); copy them + a command log to the SDD workspace as `task-5-menubar.png`, `task-5-settings.png`, `task-5-exercise.log`. Quit the app (`osascript -e 'quit app "StudioFixture"'`).

- [ ] **Step 4: Revert the fixture.** `git -C ~/Projects/StudioFixture restore StudioFixture/StudioFixtureApp.swift` (plus any Step-1 project change if it was made temporary — if the mac destination was added as a permanent fixture improvement, commit it to StudioFixture instead and say so in the report). `git -C ~/Projects/StudioFixture status --porcelain` → empty (or only the intended fixture commit).

- [ ] **Step 5: Fold corrections back.** If Steps 1–3 revealed any reference claim that didn't survive contact, the reference is fixed in this task and committed:

```bash
cd ~/Projects/apple-studio && git add plugin/skills/apple-macos && git commit -m "fix: apple-macos reference corrections from free-tier exercise" || echo "no corrections needed"
```

---

### Task 6: Integration verification + 0.5.0 release

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (0.4.0 → 0.5.0)
- Modify: `docs/specs/2026-08-04-phase4-macos-design.md` (append `## Phase 4 verification results (<date>)`)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Trigger-eval sampling.** For `apple-macos`: all 7 should-fire + all 4 should-NOT prompts. For each prior skill (apple-design, apple-frameworks, app-release, swift-architecture, swift-concurrency, swift-testing, xcode-loop): 1 should-fire + 1 should-NOT prompt (regression sample) — for apple-design use "Does this screen feel native?" (the Phase 3 substitution; its "Build the settings screen UI" prompt is headless-unevaluable per Global Constraints). Method per prompt:

```bash
claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2 --output-format stream-json --verbose --allowedTools "Skill Read"
```

One log per prompt in the SDD workspace (`task-6-eval-<name>.log`). Verdict = grep for `"name":"Skill","input":{"skill":"apple-studio:<skill>"`; `error_max_turns` exits on fire-prompts are expected and not failures. Record the pass/fail table. Misfire → diagnose first (harness confound vs description defect — Phase 3 precedent); only tighten the description for genuine routing misses, re-run that prompt, record old → new.

- [ ] **Step 2: `claude plugin validate . --strict`** — pass, zero warnings, captured to `task-6-validate.log`.

- [ ] **Step 3: Append `## Phase 4 verification results (<date>)`** to the Phase 4 spec: one entry per deliverable (minors swept + grace recorded; 4 references with sources; skill consume-test; free-tier exercise incl. both screenshots; eval table; strict validation) — with `file:line-range` evidence pointers, honest caveats verbatim where things were partial.

- [ ] **Step 4: Bump version to 0.5.0, commit, tag**

```bash
git add -A && git commit -m "release: apple-studio 0.5.0 - Phase 4 (native macOS)"
git tag v0.5.0
claude plugin validate . --strict
```

(Installed-plugin update happens post-merge, controller-handled, as in Phases 1–3. Xcode re-import after merge — operational rule, `docs/deferred.md` item 3.)

---

## Self-review notes

- Spec coverage: deliverables (4 refs → Tasks 2–3; SKILL.md + evals → Task 4; routing discipline → Task 3 Step 3 + SKILL.md scope lines; no new agent + Catalyst-unconverted → Global Constraints) ✓; sources/pipeline + endpoint probing (probed at planning 2026-08-04, listed in Task 1, one MISSING recorded) ✓; opening task minors + kill-switch grace (Task 0, trigger text verbatim from spec) ✓; verification (evals with Phase 3 harness rules → Task 6; consume test → Task 4; mac build + Settings/MenuBarExtra exercise → Task 5; validate/bump/re-import → Global Constraints + Task 6) ✓; out-of-scope list respected (no Catalyst depth, no notarization, no AppKit-first, no porting workflows) ✓.
- Deliberate scope cuts (YAGNI): no mac-specific additions to apple-design or xcode-loop this phase (cross-refs only); no StudioFixture feature buildout beyond the two documented surfaces; the `appkit` index is gap-check-only so appkit-interop.md stays a SwiftUI-first document.
- Task 5's snippets-executed-verbatim rule mirrors Phase 3 Task 7's "failures indict the docs" principle — the references' own code must survive contact.
- Task 6's misfire remedy is diagnose-first (Phase 3 lesson): the superpowers harness confound is documented and must not trigger description churn.
- Line numbers in Task 0 are approximate by design (standing convention) — every step verifies with grep/sed before editing.
