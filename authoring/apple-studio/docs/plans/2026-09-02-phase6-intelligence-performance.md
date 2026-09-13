# apple-studio Phase 6: On-device Intelligence + Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the Phase 5 opening sweep and clear the plugin's staleness debt (skill kill-switch measurement with the decision rule pre-taken, catalog regeneration, a 975-URL link-liveness sweep, charter amendment), then ship two skills: `apple-intelligence` (four live-docs references on Foundation Models and App Intents) and `apple-performance` (four references on profiling and instrumentation). Version bump to 0.7.0.

**Architecture:** Same two-layer pattern as Phases 1–5, doubled: two independent skills, two maps, eight references, one version bump. `apple-intelligence` owns *how to implement* on-device generative AI; the `apple-frameworks` primers keep *whether to adopt it*. `apple-performance` owns *why it is slow and how to measure*; `xcode-loop` keeps *does it build/test/run*. Spec: `docs/specs/2026-09-02-phase6-intelligence-performance-design.md`.

**Tech Stack:** Claude Code plugin components, existing `pipeline/` (`distill-prompt.md` adapted; `generate_catalog.sh` rerun; no `convert.sh` this phase — the corpus is spent), DocC JSON endpoints (**94 seeds probed at spec time 2026-09-02, all 200, zero MISSING** — evidence `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/spec-endpoint-probe.tsv`), `swiftc -typecheck`, `xcodebuild -destination 'platform=macOS'`, `xctrace`, `screencapture`.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-6` (create from `main` at start — `main` is at the Phase 5 squash `78fb353`). All paths relative to repo root unless absolute.
- Toolchain: macOS 27.0 (build 26A5416b), Swift 6.4, Xcode 27; fixture app `~/Projects/StudioFixture` (Multiplatform, scheme `StudioFixture`; leave its git tree clean after any test).
- **Foundation Models precondition: RESOLVED at spec time — available.** `SystemLanguageModel.default` reports `isAvailable: true` / `availability: available` / `contextSize: 8192`, and a live `respond(to:)` returned a completion. Evidence: `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/spec-fm-availability.log`. Runtime verification is therefore required, not optional; the compile-only fallback is withdrawn. If this regresses mid-phase (OS update, model eviction), re-run `spec-fm-availability.log`'s two scripts and record the change before falling back.
- Spec boundary (verbatim): `apple-intelligence` is implementation mechanics only — adoption judgment stays in the `apple-frameworks` primers; scoped to *generative* AI, with Vision/Speech/Core ML deliberately deferred; Foundation Models' *Dynamic profiles*, *Custom language model provider*, and *Custom session properties* sections are cut; App Intents is scoped to the Siri/Spotlight/Apple Intelligence path, with `widgets-live-activities-and-controls`, `app-schema-domains`, `visual-intelligence`, `hardware-interactions`, and `focus` deferred. `apple-performance` excludes Metal graphics, custom instrument authoring, and CI performance gating. **No new agent this phase.**
- Live-docs-first, binding harder than usual: Foundation Models is entirely post-training-data. **No symbol name, type name, or signature ships from model memory** — if it is not in a fetched page, it does not go in a reference. The spec-time probe already caught one such error (`LanguageModelError`, not the plausible `GenerationError`); expect more.
- **Map = seed list** (CONVENTIONS.md): the maps are dispatch-time seeds, not exhaustive registries; distillers may follow narrower pages under enumerated parents when the fetch returns 200; reference headers remain the citation record.
- Reference files: CONVENTIONS.md header block, decision-grade only, ~100–250 lines, no copied doc prose (own words; short attributed quotes with quotation marks OK), no remaining `[VERIFY` markers at commit.
- **Instruments honesty rule (new, spec-mandated):** where a step is only doable in the Instruments GUI, the reference says so and describes the UI path. Never invent a command-line equivalent for a GUI-only workflow.
- Evidence standard (standing): every consume-test/verification claim is backed by a captured log under `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/`, with quoted lines in the report; verification tables use `file:line-range` evidence pointers.
- **Implementer-brief template text (copy VERBATIM into every subagent brief that runs nested sessions):** "Run nested `claude` sessions synchronously in the foreground and wait for completion — never background-and-wait. When the nested session must write files, use `--permission-mode auto`."
- Consume-test prompts: before running any consume-test, re-validate the prompt's topic against the ACTUAL shipped reference content (grep the reference for the topic); if coverage is missing, adjust the prompt to a covered topic and record the adjustment in the task report. From-scratch prompts get a fixture cwd and `--max-turns` ≥ 25.
- **Eval-harness rules (Phase 3 lessons, binding):** headless eval/consume commands include `--allowedTools "Skill Read"`; eval prompts avoid "build X" phrasing (superpowers brainstorming preemption); from-scratch prompts run from a fixture cwd, not the plugin repo.
- Commit after every task minimum. Version bump to 0.7.0 only in Task 10.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Branch + Phase 5 sweep + staleness debt

**Files:**
- Modify: `docs/deferred.md` (skill kill-switch measurement + the pre-taken decision rule appended to item 1)
- Modify: `docs/specs/2026-08-03-apple-studio-design.md` (charter long-tail amendment)
- Modify: `plugin/skills/apple-frameworks/references/framework-catalog.md` (regenerated)
- Modify (conditional on the liveness sweep): any reference whose cited URL moved
- Modify: `plugin/skills/apple-frameworks/references/primers/foundation-models.md` (context-window claim)

**Interfaces:**
- Consumes: `docs/deferred.md` item 1 (agent kill-switch history and its measurement method); the Phase 5 ledger (`.superpowers/sdd/2026-08-04-phase5-animations/progress.md`); the charter's long-tail list (`docs/specs/2026-08-03-apple-studio-design.md:163`).
- Produces: the recorded skill-gate measurement Task 10's spec-append cites; a catalog and a reference corpus whose `verified:` stamps are honest.

- [ ] **Step 1: Confirm the branch.** `phase-6` was created from `main` at `78fb353` when this plan and its spec were committed (deviation from Phases 1–5, which committed spec+plan to `main` first; branching first keeps `main` undiverged). Confirm with `git branch --show-current` → `phase-6` and `git merge-base --is-ancestor 78fb353 HEAD`.
- [ ] **Step 2: Run the skill kill-switch measurement.** Adapt the Phase 3/5 structural scan from agents to skills: JSON-parse every `Skill` tool_use block across `~/.claude/projects/**/*.jsonl` for an input naming an `apple-studio:*` skill. Exclude scratchpad/fixture sessions (`-scratchpad-`, `-private-tmp-` in the project path) and the plugin's own verification runs (project path contains `apple-studio` or `StudioFixture`). Scope to sessions since 2026-08-05. Record per-skill genuine invocation counts and the exclusion evidence in the task report.
- [ ] **Step 3: Apply the pre-taken decision rule — do NOT improvise.** The spec settled this in advance precisely so the measurement outcome cannot re-open it: a skill is cut only after it has been available during **real feature work on a real project** and still not fired. Charter verification item 6 is still a PARTIAL PASS, so the precondition is unmet and **no skill is cut this phase regardless of the count**. Append to `docs/deferred.md` item 1: the measurement, the rule, and the hard trigger — *the skill gate fires at the opening sweep of the first phase following a shipped real feature, and does not renew again on "not yet needed" grounds*. If the measurement shows genuine non-fixture skill use, record it as the first evidence the plugin is earning its keep.
- [ ] **Step 4: Regenerate the framework catalog.** Run `pipeline/generate_catalog.sh`. Diff against the committed `framework-catalog.md` (`generated: 2026-08-04`). Record added and removed frameworks in the task report — a framework *disappearing* from the Technologies index is a signal worth a sentence, not just a diff line. Confirm the new `generated:` date.
- [ ] **Step 5: Link-liveness sweep, stage 1 (automated).** Extract every unique `developer.apple.com` URL cited across `plugin/skills/*/references/` (975 at spec time: `grep -rho "https://developer\.apple\.com[^ ,)]*" plugin/skills/*/references/ | sed 's/[.,]$//' | sort -u`). Probe each; classify live / redirected / gone. Write the full result to `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/task-0-linksweep.tsv`. Report counts by class.
- [ ] **Step 6: Link-liveness sweep, stage 2 (judgment, only where stage 1 flagged).** For each redirect or 404, open the new location and check the claim the citation supports. A moved page usually means a renamed symbol or reorganized topic — the claims most likely stale. Fix the affected claim, then re-stamp **only** the files actually touched to `verified: 2026-09`. **Files that pass stage 1 clean keep their existing 2026-08 date** — re-stamping an untouched file would assert a re-verification that never happened, which is the exact failure the header exists to prevent.
- [ ] **Step 7: Resolve the context-window discrepancy.** `primers/foundation-models.md` claims a "4,096-token on-device context window"; this host measured `contextSize: 8192`. Fetch `foundationmodels/systemlanguagemodel/contextsize` and the context-window article, determine whether the primer is stale, version-dependent, or was always wrong, and correct it. Record which. **No reference written later in this phase may state either number until this step resolves it.**
- [ ] **Step 8: Amend the charter long-tail.** In `docs/specs/2026-08-03-apple-studio-design.md` (the "Phase 4 — Long tail" line), record that `Advanced Git` and `Flight School guides` are dropped, with the one-line rationale from the Phase 6 spec's Out of scope. CONVENTIONS.md says amend deliberately, never silently — so this is an explicit edit with a dated note, not a quiet deletion.
- [ ] **Step 9: Record the manual hand-off items** in the task report (NOT automated — Xcode-side, Michael runs them): (a) Xcode re-import of 0.6.0 after the Phase 5 merge is still pending and this phase will supersede it with 0.7.0 — one re-import after the Phase 6 merge covers both; (b) stale `phase-3`/`phase-4`/`phase-5` remote branches can be deleted (content preserved in squash merges + tags v0.4.0/v0.5.0/v0.6.0).
- [ ] **Step 10: Validate + commit.** `claude plugin validate . --strict`; commit.

---

### Task 1: Build both live distillation maps

**Files:**
- Create: `pipeline/maps/apple-intelligence-live.md`, `pipeline/maps/apple-performance-live.md`

**Interfaces:**
- Consumes: the spec-time probe (`spec-endpoint-probe.tsv`, 91 seeds all 200) and the three cached hub indexes (`index-foundationmodels.json`, `index-appintents.json`, `index-xcode-performance.json`).
- Produces: the dispatch lists Tasks 2–3 and 6–7 distill against.

- [ ] **Step 1: Re-probe before trusting the cache.** The spec-time probe is ~1 day old by execution; re-run it against `spec-endpoint-probe.tsv`'s URL column and diff. Any endpoint that changed class is recorded as `MISSING:` or re-pointed. Cheap insurance on a surface this volatile.
- [ ] **Step 2: Write `pipeline/maps/apple-intelligence-live.md`.** Open with a two-line preamble: no books map (corpus spent; see spec) and the seed-list convention note. DocC JSON prefix `https://developer.apple.com/tutorials/data/documentation/`. Seed sections mapped to target reference:
  - `foundation-models-sessions.md` ← FoundationModels *Essentials*, *Sessions and prompts*, *Session transcripts*, *Prompt attachments*, plus `supporting-languages-and-locales-with-foundation-models`, `SystemLanguageModel` and its children (`availability-swift.property`, `Availability-swift.enum`, `contextSize`, `supportedLanguages`, `tokenCount(for:)`, `variant-swift.property`, `UseCase`).
  - `guided-generation-and-tools.md` ← FoundationModels *Structured output* (all 9) + *Tools* (all 3) + `Vision/OCRTool` and `Vision/BarcodeReaderTool` (first-party `Tool` conformances; see the spec's 2026-09-02 correction). Record `Vision/CoreMLRequest` as `OUT OF SCOPE (Phase 6):` alongside the rest of the classical-ML surface.
  - `safety-availability-and-errors.md` ← *Safety*, `LanguageModelError`, `SystemLanguageModel/Error`, `SystemLanguageModel/Guardrails`, *Private Cloud Compute* (all 3, including the entitlement page).
  - `app-intents-implementation.md` ← AppIntents *Essentials*, *App-specific content*, *Testing*, *Errors*, plus `apple-intelligence-and-siri-ai`, `spotlight`, `app-shortcuts`, `donations-and-discovery`, `adopting-app-intents-to-support-system-experiences`, `visual-presentation`.
  - Record the cut sections explicitly as `OUT OF SCOPE (Phase 6):` lines — *Dynamic profiles*, *Custom language model provider*, *Custom session properties*, and the deferred App Intents children. A future phase should find them listed, not have to rediscover them.
- [ ] **Step 3: Write `pipeline/maps/apple-performance-live.md`.** Same preamble. Seeds follow Apple's own `Xcode/performance-and-metrics` sectioning:
  - `profiling-workflow.md` ← `tutorials/instruments`, `diagnosing-performance-issues-early`, `analyzing-the-performance-of-your-shipping-app`, `analyzing-cpu-profiles-with-call-tree-views`, `analyzing-cpu-usage-with-processor-trace`, `addressing-cpu-bottlenecks`, `os/OSSignposter`, `os/logging`, `improving-your-app-s-performance`.
  - `responsiveness-hangs-and-hitches.md` ← `understanding-user-interface-responsiveness`, `understanding-hangs-in-your-app`, `understanding-hitches-in-your-app`, `improving-app-responsiveness`, `analyzing-responsiveness-issues-in-your-shipping-app`, `reducing-your-app-s-launch-time`, `reduce-terminations-in-your-app`, `MetricKit`.
  - `swiftui-performance.md` ← `understanding-and-improving-swiftui-performance` (+ children followed live).
  - `memory-power-and-size.md` ← `reducing-your-app-s-memory-use`, `reducing-your-app-s-size`, `analyzing-your-app-s-battery-use`, `measuring-your-app-s-power-use-with-power-profiler`, `reducing-your-app-s-battery-use`, `reducing-disk-writes`, `reducing-your-app-s-disk-usage`, `monitoring-your-app-s-storage-metrics`.
  - Record `OUT OF SCOPE (Phase 6):` for the *Graphics* section (Metal), `creating-custom-modelers-for-intelligent-instruments`, `visionOS/creating-a-performance-plan-for-visionos-app`, and `Foundation/analyzing-http-traffic-with-instruments`.
  - Record the two cross-skill bridges as `CROSS-REF:` lines: `FoundationModels/analyzing-the-runtime-performance-of-your-foundation-models-app` → `apple-performance`, and `Xcode/writing-and-running-performance-tests` → `swift-testing`.
- [ ] **Step 4: Commit.**

---

### Task 2: Distill `foundation-models-sessions.md` + `guided-generation-and-tools.md`

**Files:**
- Create: `plugin/skills/apple-intelligence/references/foundation-models-sessions.md`, `plugin/skills/apple-intelligence/references/guided-generation-and-tools.md`

- [ ] **Step 1: Dispatch two distiller subagents** (parallel, model sonnet), one per file, with the adapted `pipeline/distill-prompt.md`. Include the implementer-brief template text from Global Constraints verbatim. Content requirements:
  - `foundation-models-sessions.md`: session lifecycle and reuse (single-turn vs multi-turn), `Instructions` vs `Prompt` and why the distinction matters for injection safety, the one-request-at-a-time constraint and `isResponding`, streaming responses, `GenerationOptions`/`ContextOptions`, context-window management and overflow behaviour, transcripts, multimodal attachments, locale support, prompt updates across model versions. Include the availability check as the entry point every integration needs.
  - `guided-generation-and-tools.md`: why typed generation beats parsing free text, `Generable`/`Guide`, static vs `DynamicGenerationSchema`, `GeneratedContent` and its conversion protocols, partial/streaming generated values, the `Tool` protocol and the call loop, error handling inside a tool, and the first-party Vision tools (`OCRTool`, `BarcodeReaderTool`) with the judgment to check for a supplied tool before writing one.
- [ ] **Step 2: Resolve `[VERIFY:]` flags** (fetch the endpoint; drop unverifiable inferences). `grep -rn "VERIFY" plugin/skills/apple-intelligence/` → empty.
- [ ] **Step 3: Typecheck every snippet.** Each Swift snippet is extracted and run through `swiftc -typecheck` (add `-parse-as-library` where the snippet is declaration-only). A snippet that does not compile is a reference defect — fix the reference, not the test. Log to `task-2-typecheck.log`. This is stricter than prior phases because the API is post-cutoff and cannot be sanity-checked from memory.
- [ ] **Step 4: Add CONVENTIONS.md headers** (`> verified: 2026-09 against <human URLs checked>` / `> sources: live Apple docs (no book input)`).
- [ ] **Step 5: Commit.**

---

### Task 3: Distill `safety-availability-and-errors.md` + `app-intents-implementation.md`

**Files:**
- Create: `plugin/skills/apple-intelligence/references/safety-availability-and-errors.md`, `plugin/skills/apple-intelligence/references/app-intents-implementation.md`

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet; brief template verbatim). Content requirements:
  - `safety-availability-and-errors.md`: the safety guidance page's design advice, `Guardrails`, guardrail-violation handling, the `LanguageModelError` / `SystemLanguageModel.Error` surface and what each case means for UI, designing the unavailable state (device ineligible, Apple Intelligence off, model not downloaded) as a first-class path rather than an afterthought, untrusted-input handling when app or user content reaches a prompt, and the Private Cloud Compute path with its entitlement.
  - `app-intents-implementation.md`: `AppIntent`, `AppEntity`, `AppEnum`, common data types, queries, `AppShortcutsProvider`, parameter summaries and visual presentation, donations and discovery, the App Intents extension target, `AppIntentError`, and testing via AppIntentsTesting. Stay on the Siri/Spotlight/Apple Intelligence path — route widgets/Controls/Live Activities to the deferred slice with a one-line pointer.
- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Headers as in Task 2 Step 4.
- [ ] **Step 3: Typecheck every snippet** as in Task 2 Step 3 → `task-3-typecheck.log`.
- [ ] **Step 4: Sibling-consistency check.** Grep all four references for restatements that belong elsewhere: adoption/cost judgment (`apple-frameworks` primers), architecture and state ownership (`swift-architecture`), concurrency rules (`swift-concurrency`), build/run commands (`xcode-loop`). Replace any restatement with a one-line cross-ref.
- [ ] **Step 5: Commit.**

---

### Task 4: `apple-intelligence` SKILL.md + evals + cross-refs + primer refresh

**Files:**
- Create: `plugin/skills/apple-intelligence/SKILL.md`, `plugin/skills/apple-intelligence/evals/triggers.md`
- Modify: `plugin/skills/apple-frameworks/references/primers/foundation-models.md`, `plugin/skills/apple-frameworks/references/primers/app-intents.md` (forward references + refresh)

- [ ] **Step 1: Write `SKILL.md`** — under ~150 lines per CONVENTIONS.md. Scope paragraph states the split: implementation here, adoption judgment in the `apple-frameworks` primers, classical ML out of scope. Routing lines, one per reference.
- [ ] **Step 2: Refresh `primers/foundation-models.md`.** The spec-time probe found it behind the live surface: multimodal attachments, dynamic profiles, a custom-model-provider path, and an evaluation surface all postdate it, and its context-window number is contested (Task 0 Step 7 resolves the number; this step applies the outcome). Update the primer to describe the current surface at planning grade, re-stamp its header, and add the forward reference to `apple-intelligence`. **Do not let the primer grow into an implementation guide** — it answers "should we, and what does it cost", nothing more.
- [ ] **Step 3: Add the forward reference to `primers/app-intents.md`** — one line routing implementation to `apple-intelligence`.
- [ ] **Step 4: Write `evals/triggers.md`** (no "build X" phrasing). Should fire: on-device model integration, guided/structured generation, tool calling, availability handling, App Intents/Siri/Spotlight exposure. Should NOT fire: cloud LLM API integration, "should this feature use AI at all" (adoption → primer), general architecture, general testing.
- [ ] **Step 5: Pre-validate the consume-test prompt** (Global Constraints rule): grep the shipped references for the topic before committing to the prompt; record any adjustment.
- [ ] **Step 6: Consume-test with captured evidence** from `~/Projects/StudioFixture`.
- [ ] **Step 7: Validate + commit.**

---

### Task 5: Free-tier exercise — Foundation Models + App Intents end-to-end

**Files:** none committed (fixture reverted). Evidence only.

- [ ] **Step 1: Re-confirm availability** — re-run `spec-fm-availability.log`'s two scripts; if the model has become unavailable, stop and record before proceeding (Global Constraints fallback clause).
- [ ] **Step 2: Baseline mac build** of the unmodified fixture: `xcodebuild -scheme StudioFixture -destination 'platform=macOS' build` → `** BUILD SUCCEEDED **`.
- [ ] **Step 3: Insert documented snippets verbatim** into the fixture — (a) a guided-generation example from `guided-generation-and-tools.md`, (b) a tool-calling example from the same file, (c) an `AppIntent` + `AppEntity` pair from `app-intents-implementation.md` — copied **verbatim**, adjusting only identifier names/labels. If a snippet does not compile as written, that is a reference defect: fix the reference first, then use the fixed snippet, and record the correction. Rebuild → `** BUILD SUCCEEDED **`.
- [ ] **Step 4: Run and capture real output.** Launch, trigger the generation paths, capture actual model output (not just build success — this is the phase's strongest available evidence and the reason the precondition was checked at spec time). Screenshot the App Intents surface in Shortcuts/Spotlight if it registers.
- [ ] **Step 5: Exercise the unavailable path by construction.** This host reports `available`, so the unavailable branch cannot occur naturally — write the `Availability` switch against the enum's unavailable cases and confirm it compiles and handles every case. Record that this is a compile-level check, explicitly weaker than the runtime evidence above.
- [ ] **Step 6: Revert the fixture.** `git -C ~/Projects/StudioFixture restore .` then `git -C ~/Projects/StudioFixture status --porcelain` → empty.

---

### Task 6: Distill `profiling-workflow.md` + `responsiveness-hangs-and-hitches.md`

**Files:**
- Create: `plugin/skills/apple-performance/references/profiling-workflow.md`, `plugin/skills/apple-performance/references/responsiveness-hangs-and-hitches.md`

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet; brief template verbatim). Content requirements:
  - `profiling-workflow.md`: choosing an Instruments template for a symptom, capturing a trace (GUI and `xctrace` where it genuinely applies — **Instruments honesty rule**), reading call trees, processor trace, addressing CPU bottlenecks, custom instrumentation with `OSSignposter`, and the measurement discipline that makes numbers mean anything (release config, real device over simulator, warm vs cold, measure before optimizing, one variable at a time).
  - `responsiveness-hangs-and-hitches.md`: the responsiveness model, hangs vs hitches and why the distinction drives different fixes, the render loop, launch phases and what moves each, terminations, and field metrics via MetricKit and the Organizer.
- [ ] **Step 2: Verify `xctrace` invocations actually run.** Every command-line invocation in `profiling-workflow.md` is executed against the fixture and its real output recorded (`task-6-xctrace.log`). Commands that cannot run as written are corrected or removed. Same standard `xcode-loop`'s `headless-commands.md` was held to in Phase 1.
- [ ] **Step 3: Resolve `[VERIFY:]` flags**; grep → empty. Add CONVENTIONS.md headers.
- [ ] **Step 4: Commit.**

---

### Task 7: Distill `swiftui-performance.md` + `memory-power-and-size.md`

**Files:**
- Create: `plugin/skills/apple-performance/references/swiftui-performance.md`, `plugin/skills/apple-performance/references/memory-power-and-size.md`

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet). Content requirements:
  - `swiftui-performance.md`: built on `understanding-and-improving-swiftui-performance`; diagnosing excessive view updates, structural identity and `.id()` misuse, expensive body computation, observation granularity, lazy-container behaviour in long lists, and which Instruments template answers which SwiftUI question.
  - `memory-power-and-size.md`: leaks vs abandoned memory, retain-cycle diagnosis, memory limits and termination, battery use and the power profiler, disk writes and storage metrics, app size.
- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Headers added.
- [ ] **Step 3: Sibling-consistency check** across all four performance references and against `apple-animations` (animation *implementation* is not performance), `swift-testing` (performance *test authoring* routes there), `swift-concurrency` (main-actor rules are not restated), and the `oslog` primer. Replace restatements with cross-refs.
- [ ] **Step 4: Commit.**

---

### Task 8: `apple-performance` SKILL.md + evals + cross-refs

**Files:**
- Create: `plugin/skills/apple-performance/SKILL.md`, `plugin/skills/apple-performance/evals/triggers.md`
- Modify: `plugin/skills/xcode-loop/SKILL.md` (one-line cross-ref), `plugin/skills/swift-testing/SKILL.md` (performance-test pointer), `plugin/skills/apple-intelligence/SKILL.md` (FM runtime-performance bridge)

- [ ] **Step 1: Write `SKILL.md`** — routing lines per reference; scope paragraph stating the `xcode-loop` split (build/test/run vs why-is-it-slow).
- [ ] **Step 2: Add the three cross-refs**, one sentence each — routing, not content.
- [ ] **Step 3: Write `evals/triggers.md`.** Should fire: slowness, profiling, hangs/hitches, launch time, memory growth, battery drain, app size. Should NOT fire: plain build/test/run (`xcode-loop`), test authoring (`swift-testing`), animation implementation (`apple-animations`), architecture (`swift-architecture`).
- [ ] **Step 4: Pre-validate + run the consume-test** with captured evidence.
- [ ] **Step 5: Validate + commit.**

---

### Task 9: Free-tier exercise — measure, fix, re-measure

**Files:** none committed (fixture reverted). Evidence only. This is the phase's strongest verification and `apple-performance` stands or falls on it.

- [ ] **Step 1: Introduce a deliberate regression** in StudioFixture — a blocking main-thread computation inside a scrolling list, chosen so the documented workflow should find it.
- [ ] **Step 2: Capture a trace following the shipped reference exactly**, using only steps `profiling-workflow.md` documents. Save the trace and the identification evidence (`task-9-before.trace`, `task-9-before.log`).
- [ ] **Step 3: Identify the cost from the trace, not from prior knowledge of the planted bug.** Record what the trace actually showed. If the documented workflow does not surface the planted cost, that is a reference defect — fix the reference and re-run. This is the honest form of the test; skipping to the known answer proves nothing.
- [ ] **Step 4: Fix, re-capture, and diff** (`task-9-after.trace`, `task-9-after.log`). Record the before/after numbers.
- [ ] **Step 5: Revert the fixture** and confirm `git status --porcelain` → empty.

---

### Task 10: Full eval sweep + validate + version bump + spec verification append

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (0.6.0 → 0.7.0)
- Modify: `docs/specs/2026-09-02-phase6-intelligence-performance-design.md` (verification results appended)

- [ ] **Step 1: Run the full eval sweep.** 3 should-fire + 2 should-NOT per new skill, plus one should-fire + one should-NOT regression sample per prior skill (9 prior skills). Harness rules from Global Constraints. Log every run to `task-10-evals/`; build `results.tsv`.
- [ ] **Step 2: Fix misfires by editing skill descriptions, not by weakening prompts.** Record every description change and re-run the affected prompts. A prompt changed to make a skill pass is recorded as such and does not count as a pass.
- [ ] **Step 3: `claude plugin validate . --strict`** → clean. Log it.
- [ ] **Step 4: Bump to 0.7.0** in `plugin/.claude-plugin/plugin.json` only (never duplicated in the marketplace entry).
- [ ] **Step 5: Append the verification section to the Phase 6 spec** — the standing format: numbered results, PASS/PARTIAL/FAIL, `file:line-range` evidence pointers. Include the skill kill-switch measurement and its deferred gate, the catalog diff, the link-sweep counts, the context-window resolution, and both real exercises.
- [ ] **Step 6: Commit + tag `v0.7.0` + open the PR** against `main`.

---

## Deferred to the phase report (not steps)

- The corpus is spent; `pipeline/convert.sh` is dormant until new books arrive. Note it in the report so a future phase does not look for a books map that will never exist.
- Verification item 6 (one real feature in a real project) remains PARTIAL and is now the binding precondition on the skill kill-switch gate. Every phase that ships without it raises the stakes of the eventual measurement.
