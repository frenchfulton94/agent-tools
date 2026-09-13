# apple-studio Phase 6: On-device intelligence + performance — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`, "Phase 4 — Long tail",
third and fourth slices). Decisions taken 2026-09-02; this doc is the input
to the Phase 6 implementation plan.

## Goal

Ship two new skills and close the plugin's standing staleness debt:

- `apple-intelligence` — on-device generative AI implementation mechanics
  (Foundation Models: sessions, guided generation, tool calling, safety and
  availability) plus the App Intents path that exposes an app to Siri,
  Spotlight, and Apple Intelligence. Scoped to generative AI; classical ML is
  deliberately deferred (see Out of scope).
- `apple-performance` — profiling and instrumentation: why an app is slow
  and how to measure it, the counterpart to `xcode-loop`'s build/test/run
  duty.

Version bump to 0.7.0.

**Direction.** `ML` is the charter's last unclaimed long-tail slice with real
demand; `Advanced Git` and `Flight School guides` are dropped from the charter
list (see Out of scope). Performance is not on the charter list at all — it was
identified as the plugin's largest uncovered surface during Phase 6 scoping and
is added deliberately.

**Size note (differs from Phases 1–5).** Every prior phase shipped exactly one
skill. Phase 6 ships two, so it is roughly double the largest phase to date
(expect ~12–14 tasks against Phase 5's 7, and 8 reference files against 4). The
two halves are independent — different sources, different references, no shared
files beyond the version bump and cross-refs. If the phase runs long, the seam
is clean: ship `apple-intelligence` as 0.7.0 and carry `apple-performance` to a
Phase 7 at 0.8.0. That is a scheduling fallback, not the plan.

Scope was trimmed once already to hold this line: the enumerated Foundation
Models surface would support six references, and it is capped at four (see Out
of scope for what was cut and why).

## Deliverables

### New skill `plugin/skills/apple-intelligence/`

Lean SKILL.md (triggers, routing, adoption judgment) + `evals/triggers.md` +
four references. Contents below are drawn from the **actual live surface
enumerated 2026-09-02** (see Sources), not from the 2026-08 primer, which
predates several of these sections.

1. `foundation-models-sessions.md` — `SystemLanguageModel`, `LanguageModelSession`,
   `Instructions` vs `Prompt`, `GenerationOptions`/`ContextOptions`, context-window
   management, session transcripts, multimodal prompt attachments (image input),
   language and locale support, and updating prompts across model versions.
2. `guided-generation-and-tools.md` — `Generable`/`Guide`, `GenerationSchema` and
   `DynamicGenerationSchema`, `GeneratedContent` and its conversion protocols, and
   the `Tool` protocol. Merged because Apple documents and demonstrates them
   together. Includes the first-party tools Vision ships for this protocol
   (`Vision/OCRTool`, `Vision/BarcodeReaderTool`) — reaching for a supplied tool
   before hand-rolling one is exactly the Apple-specific judgment a reference
   exists to carry.
3. `safety-availability-and-errors.md` — the safety guidance page, `LanguageModelError`,
   designing for the unavailable case, and the Private Cloud Compute path including
   its entitlement.
4. `app-intents-implementation.md` — intents, entities, enums, common data types,
   the extension target, App Shortcuts, Spotlight, the Apple Intelligence/Siri
   path, donations and discovery, and intent testing.

**Adoption gate stays in `apple-frameworks`.** The existing
`primers/foundation-models.md` and `primers/app-intents.md` (152 and 151 lines,
verified 2026-08) own the planning-grade question — *should this feature use this
framework at all*, and what it costs. They are not duplicated or absorbed;
`apple-intelligence` owns implementation only, and both primers gain a one-line
forward reference. Same split `apple-animations` uses against
`apple-design/animation-taste.md`.

**Primer refresh obligation.** The probe found the primers materially behind the
live surface — multimodal attachments, dynamic profiles, a custom-model-provider
path, and an evaluation surface all postdate them. Refreshing
`primers/foundation-models.md` against the current index is a task in this phase,
not a later cleanup. This is the first observed case of a primer going stale
inside one phase cycle, and it is evidence for how fast this surface moves.

### New skill `plugin/skills/apple-performance/`

Lean SKILL.md + `evals/triggers.md` + four references, structured to follow
Apple's own `Xcode/performance-and-metrics` hub:

1. `profiling-workflow.md` — the Instruments tutorial surface, diagnosing issues
   early, analyzing a shipping app, reading CPU profiles with call-tree views,
   processor trace, addressing CPU bottlenecks, and custom instrumentation with
   signposts. Carries the measurement discipline that makes numbers mean
   anything: release configuration, real device over simulator, warm vs cold runs,
   measure before optimizing.
2. `responsiveness-hangs-and-hitches.md` — the UI responsiveness model, hangs,
   hitches, launch time, terminations, and field metrics via MetricKit and the
   Xcode Organizer.
3. `swiftui-performance.md` — built on Apple's own
   `understanding-and-improving-swiftui-performance`, extended with view-update
   diagnosis, structural identity misuse, expensive body computation, observation
   granularity, and lazy-container behavior in long lists.
4. `memory-power-and-size.md` — memory use and leaks, battery and the power
   profiler, disk writes and storage metrics, and app size.

**Naming.** `apple-performance`, not `swift-performance`: CONVENTIONS.md reserves
the `swift-` prefix for code-level skills and gives platform/tooling skills plain
names. The subject is Apple's profiling toolchain and platform behavior, not the
Swift language.

**Routing.** `xcode-loop` owns "does it build, test, and run";
`apple-performance` owns "why is it slow and how do I measure it" — both SKILL.md
files gain a one-line cross-reference. Performance *test authoring*
(`Xcode/writing-and-running-performance-tests`) routes to `swift-testing`. The
`oslog` primer keeps logging-API duty and is cross-referenced, not restated.

**Two cross-skill bridges found during the probe**, both to be wired as one-line
cross-refs rather than duplicated content:
`FoundationModels/analyzing-the-runtime-performance-of-your-foundation-models-app`
connects `apple-intelligence` → `apple-performance`, and
`Xcode/writing-and-running-performance-tests` connects `apple-performance` →
`swift-testing`.

**No new agent.** The agent gate has failed twice (`docs/deferred.md` item 1);
nothing this phase changes that.

## Sources and pipeline

**No book conversion — and the corpus is now spent.** Phase 5 harvested the last
durable book judgment; nothing in `corpus/` covers on-device generative AI (every
book predates the framework) or profiling. Phase 6 is the second consecutive
live-docs-only phase and the first with no book input waiting for any future
phase. Record in the phase report: the pipeline's book half is now dormant, and
`pipeline/convert.sh` earns its keep only if new books arrive.

Two maps, both written as **seed lists** under the CONVENTIONS.md rule:

- `pipeline/maps/apple-intelligence-live.md`
- `pipeline/maps/apple-performance-live.md`

**Endpoint probe — done at spec time, 2026-09-02.** Seeds were enumerated from
the three live hub indexes (`FoundationModels`, `AppIntents`,
`Xcode/performance-and-metrics`) rather than guessed, then every seed was
fetched:

| Surface | Seeds | Result |
|---|---|---|
| Foundation Models (in-scope sections) | 37 | all 200 |
| App Intents | 23 | all 200 |
| Xcode performance + visionOS/Foundation children | 26 | all 200 |
| `MetricKit`, `os/OSSignposter`, `os/logging`, PCC entitlement, `Evaluations` | 5 | all 200 |
| Vision tool types + `CoreMLRequest` (added on the 2026-09-02 correction) | 3 | all 200 |
| **Total** | **94** | **all 200, zero MISSING** |

`tutorials/instruments` (a tutorial, not a documentation path) also returns 200
and is seeded for `profiling-workflow.md`. Three paths guessed before the hubs
were read — `swiftui/view-performance`, `instruments`,
`xcode/gaining-insight-into-your-app-with-instruments` — returned 404 and are
**not** in the maps; they are recorded here only as evidence that hub enumeration
beats symbol guessing on a post-cutoff surface.

**Staleness stance — elevated this phase.** Foundation Models is the newest and
fastest-moving surface the plugin has documented, and it is entirely
post-training-data. Two rules bind harder than usual:

- No symbol name, type name, or signature ships from model memory. If it is not
  in a fetched page, it does not go in a reference. The probe already caught one
  such error in scoping: the error type is `LanguageModelError`, not the
  plausible-sounding `GenerationError` assumed before the index was read.
- Reference headers cite the exact endpoints consulted, per CONVENTIONS.md.

The Instruments half carries the opposite risk: much of it is GUI workflow that
does not reduce cleanly to text. Where a step is only doable in the Instruments
UI, the reference says so plainly and describes the path rather than inventing a
command-line equivalent.

## Opening task: Phase 5 sweep + staleness debt

Task 0 of the plan, in this order.

### 1. Kill-switch measurement — the rule needs a definition for skills

The rule (`CONVENTIONS.md`, "The kill-switch rule") has only ever been applied
to agents, using a structural transcript scan for `input.subagent_type`. Both
agents are now cut, so Phase 6 is the first time the rule points at skills.

**Measurement.** Adapt the Phase 3/5 structural scan: JSON-parse `Skill` tool_use
blocks across `~/.claude/projects` transcripts for an `apple-studio:*` skill
name, excluding scratchpad and fixture-harness sessions and the plugin's own
verification runs, scoped to sessions since 2026-08-05. Record per-skill genuine
invocation counts.

**Decision rule, taken now rather than at measurement time** (the Phase 4 grace
was granted ad hoc and drifted a full phase; this one gets its trigger written
first):

> A skill is cut or merged only after it has been available during **real
> feature work on a real project** and still not fired. Charter verification
> item 6 is still a PARTIAL PASS — no real feature has shipped through this
> plugin — so the precondition is unmet and the skill gate does not fire in
> Phase 6. The measurement is still run and recorded.
>
> **Hard trigger:** the skill gate fires at the opening sweep of the first
> phase that follows a shipped real feature. It does not renew again on
> "not yet needed" grounds.

This is deliberately not a second open-ended grace. If the honest reading at
that point is that the plugin has grown eight skills nobody loads, the rule
says deletion is a feature, and it should be applied.

### 2. Regenerate the framework catalog

`plugin/skills/apple-frameworks/references/framework-catalog.md` is stamped
`generated: 2026-08-04`; its own header says "rerun each phase and after WWDC",
and the charter requires per-phase regeneration. Rerun
`pipeline/generate_catalog.sh`, diff against the committed catalog, and record
added and removed frameworks in the task report. A framework that disappears
from the index is a signal worth reading, not just a diff line.

### 3. Verified-header refresh across all 48 references

Every reference in the plugin reads `verified: 2026-08`. Full re-distillation is
not affordable and is not proposed. Instead, a cheap two-stage sweep:

- **Stage 1 — link liveness (automated).** 975 unique `developer.apple.com`
  URLs are cited across the references. Probe every one; classify as live,
  redirected, or gone. This is a script, not a judgment call.
- **Stage 2 — targeted re-read (judgment).** Only where Stage 1 reports a
  redirect or a 404 does anyone open a page. A moved page usually means a
  renamed symbol or a reorganized topic — exactly the claims most likely to
  have gone stale. Fix the affected claim and re-stamp only the files touched.

Files that pass Stage 1 clean keep their existing `verified:` date. Re-stamping
an untouched file to 2026-09 would assert a re-verification that never happened,
which is precisely the failure the header exists to prevent.

## Verification (free-tier, definition of done)

- **Trigger evals per new skill.** `apple-intelligence` fires on on-device model
  and App Intents implementation requests; silent on cloud-LLM API work, on
  "should we use AI here" adoption questions (`apple-frameworks` primer), and on
  general architecture. `apple-performance` fires on slowness, profiling, and
  memory-growth requests; silent on build/test/run (`xcode-loop`), on test
  authoring (`swift-testing`), and on animation *implementation*
  (`apple-animations`). One should-fire plus one should-NOT regression sample
  per prior skill, as in Phases 3–5. Eval-harness caveats carry forward:
  `--allowedTools "Skill Read"`, fixture cwd where needed, and no "build X"
  phrasing (superpowers preemption, documented in Phase 3 verification results).
- **Consume tests with captured logs**, every prompt pre-validated against
  actual reference coverage before it enters the plan. Evidence pointers as
  `<file>:<line-range>`.
- **Real exercise, `apple-performance` — full.** StudioFixture gets a
  deliberately slow surface (a blocking main-thread computation in a scrolling
  list), then the documented workflow runs against it end to end: capture a
  trace headlessly, identify the cost from the trace, fix it, re-capture, show
  the difference. Both traces are kept as evidence. This is the strongest
  verification available this phase and the reference stands or falls on it.
- **Real exercise, `apple-intelligence` — full, precondition resolved at spec
  time.** The spec made device availability a planning precondition rather than a
  task-time assumption; it was checked on 2026-09-02 and **passed**, so the
  compile-only fallback is dropped and the phase commits to full runtime
  verification. Evidence:
  `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/spec-fm-availability.log`
  — on macOS 27.0 (build 26A5416b, Swift 6.4), `SystemLanguageModel.default`
  reports `isAvailable: true`, `availability: available`, and a live
  `LanguageModelSession.respond(to:)` call returned a real completion.
  The plan therefore builds and runs a documented guided-generation snippet and
  a tool-calling snippet verbatim in StudioFixture, captures output, and
  additionally exercises the unavailable code path by construction (the
  `Availability` enum's unavailable cases) since this host cannot produce it
  naturally. App Intents snippets verify independently of Apple Intelligence
  eligibility.

  **Finding already produced by this check, and the reason the primer refresh is
  a phase task rather than a cleanup:** the host reports `contextSize: 8192`,
  while `apple-frameworks/references/primers/foundation-models.md` states a
  "4,096-token on-device context window" (verified 2026-08). One of the two is
  wrong or version-dependent. Task 0 resolves it against the live docs and the
  measured value before any reference repeats either number. Treat this as
  confirmation that the elevated staleness stance is warranted, not as a
  settled correction — the discrepancy is recorded, not yet explained.

- `claude plugin validate . --strict` passes at every commit touching
  `plugin/`; version bump to 0.7.0 in the final task only; re-import into Xcode
  after merge (operational rule, `docs/deferred.md` item 3).

## Out of scope

- **Adoption judgment for the AI frameworks** — whether a feature should use
  Foundation Models at all, and what it costs, stays in the `apple-frameworks`
  primers; cross-referenced, not duplicated.
- **Cloud LLM integration** (Anthropic, OpenAI, any HTTP model API) — the
  primer already owns the on-device-vs-cloud decision; calling a cloud API is
  ordinary networking and needs no Apple-specific reference.
- **Classical on-device ML — Vision, Speech, Core ML, Create ML — deferred for
  size, not for value. Corrected 2026-09-02.** The original rationale here was
  the CONVENTIONS.md worth-it rule: that these frameworks are old and stable, so
  model priors are reliable and a reference earns little. **Probing them showed
  that is false**, and the claim is withdrawn:
  - **Vision** is now a Swift-native request API — `DetectBarcodesRequest`,
    `ClassifyImageRequest`, `GenerateForegroundInstanceMaskRequest`, protocols
    `ImageProcessingRequest` / `VisionObservation`. The `VN`-prefixed types that
    dominate model priors, existing code, and every tutorial are the *previous*
    API.
  - **Speech** is now module-based — `SpeechAnalyzer`, `SpeechTranscriber`,
    `DictationTranscriber`, `AssetInventory`. The framework's own index files
    `SFSpeechRecognizer`-era material under a **"Legacy API"** heading, which is
    precisely where priors will land.

  Both are therefore the *same* stale-priors condition that justifies a
  reference for Foundation Models, not the opposite of it. The deferral stands
  only on phase size — this phase is already double any prior one — and the
  honest label is **cut for capacity**. That makes classical ML the strongest
  Phase 7 candidate rather than a someday item, and it should not be re-argued
  on "the model already knows it" grounds.

- **Not deferred: the Vision–Foundation Models integration.** The same probe
  found `Vision/OCRTool` and `Vision/BarcodeReaderTool` — first-party Vision
  types conforming to the Foundation Models `Tool` protocol. They sit inside
  this phase's tool-calling scope, not outside it, and are seeded to
  `guided-generation-and-tools.md`. `Vision/CoreMLRequest` (custom Core ML
  models through Vision) is probed and recorded but stays deferred with the
  rest of the classical surface.
- **Foundation Models sections cut from scope this phase** — *Dynamic profiles*
  (`DynamicInstructions`, session profiles), *Custom language model provider*
  (`LanguageModel`, `LanguageModelExecutor`, KV-cache tuning, running a Core AI
  model in a session), and *Custom session properties*. All three are live and
  documented; all three serve advanced cases well past first adoption. Named
  here so the omission is a decision on record, not an oversight — each is a
  clean later addition to an existing skill, not a new phase.
- **Widgets, Controls, and Live Activities implementation** — App Intents is
  scoped this phase to the Siri/Spotlight/Apple Intelligence path only. The live
  index carries `AppIntents/widgets-live-activities-and-controls` as its own
  child, so the seam is Apple's, not one we invented. That surface is a coherent
  future phase and keeps its `widgetkit` and `activitykit` primers meanwhile.
  Also out: `app-schema-domains`, `visual-intelligence`, `hardware-interactions`,
  and `focus` — enumerated during the probe, deferred with the widget slice.
- **Instruments UI depth beyond the documented workflows** — custom instrument
  authoring, and any GUI walkthrough that text cannot carry honestly.
- **Server-side and CI performance budgeting** — regression gating in CI is a
  release-engineering concern; revisit in `app-release` on demand.
- **Dropped from the charter long-tail: `Advanced Git`** (not Apple-specific;
  dilutes the plugin's scope boundary and duplicates general tooling) and
  **`Flight School guides`** (Swift language depth already owned by
  `swift-architecture` and `swift-concurrency`; fold anything durable in on
  demand rather than as a phase). The charter's long-tail list is amended
  accordingly — deliberately, per CONVENTIONS.md.

---

## Verification results (appended 2026-09-02, Phase 6 Task 10)

Evidence root: `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/`.
Pointers are `<file>:<line-range>` per CONVENTIONS.md.

### 1. Skill kill-switch measured, gate correctly did NOT fire — **PASS**
3,440 transcripts across 596 project directories; 128 distinct
(session, skill, date) invocations naming an `apple-studio:*` skill; **0 genuine
non-fixture invocations** since 2026-08-05. All 128 came from exactly two
directories — the plugin repo (101) and `StudioFixture` (27). All nine shipped
skills did fire in-harness, 8–28× each, so this measures "never used on real
work", not "does not trigger". The pre-taken rule applied unchanged: no skill
cut, hard trigger recorded.
Evidence: `task-0-killswitch.log:44-70`; rule and trigger in
`docs/deferred.md:59-98`.

### 2. Framework catalog regenerated — **PASS**
398 → 400 entries (+Apple Ads Platform API, +Apple TV Feed), **0 removed**.
The signal the plan asked to watch for did not fire. 738 of 742 changed lines
are Apple's index switching to lowercase URLs; both cases resolve 200, so no
existing citation is invalidated.
Evidence: `task-0-catalog-diff.log:1-66`.

### 3. Link-liveness sweep — **PASS**, with a correction to the plan's method
913 URLs: **903 LIVE / 6 REDIRECT / 4 GONE**. Stage 2 opened all 10 flags and
found **no stale claim in any reference**. Eight of ten were DocC disambiguation
suffixes, not rot. One genuine reorganization in the whole corpus (the
photos-picker article moved PhotosUI → PhotoKit). 5 files fixed and re-stamped
`verified: 2026-09`; **43 kept 2026-08**, because a clean liveness pass is not a
re-reading.

**The plan's own extraction command was wrong and was replaced.**
`grep -o "https://developer\.apple\.com[^ ,)]*"` excludes `)`, truncating every
Swift symbol URL at its closing paren; run as written it reported **108 GONE**,
of which 104 were its own artifacts.
Evidence: `task-0-linksweep.tsv:1-18` (method note), `task-0-linksweep-stage2.md:1-84`.

### 4. Context-window discrepancy resolved — **PASS**
**Verdict: version-dependent; the documentation lags the shipped OS.** Not
stale, not always wrong. Apple's prose says 4096 in two places; this host
measures `contextSize: 8192`; both checked 2026-09-02 and confirmed to describe
the same quantity. The primer now reads the value at runtime and asserts neither
number. Collateral finding: `SystemLanguageModel.variant` is documented
("macOS 27.0 BETA") and **absent from the shipped SDK** — so the docs run behind
the OS and ahead of the SDK simultaneously.
Evidence: `task-0-contextwindow.md:1-90`.

### 5. Charter long-tail amended — **PASS**
`Advanced Git` and `Flight School guides` struck with dated rationale; ML
recorded as the only outstanding long-tail item.
Evidence: `docs/specs/2026-08-03-apple-studio-design.md:163-188`.

### 6. Trigger evals — **PASS, 28/28**
3 should-fire + 2 should-NOT per new skill, plus 1+1 regression per prior skill.
**No skill description was changed.** Every should-NOT prompt routed to the
correct alternative skill rather than merely staying silent, which is the
stronger result. Two harness defects were found and are recorded as harness
defects, not misfires: a stdin leak that fed one prompt the entire eval dataset,
and turn exhaustion at `--max-turns 2`; all 28 were re-run at 6 turns so every
result comes from identical conditions.
Evidence: `task-10-evals/results.tsv:1-29`, `task-10-evals/README.md:1-70`.

### 7. Consume tests — **PASS**
`apple-intelligence`: fired and read exactly the two references its two-part
prompt needed; the answer's `Availability` switch was extracted and **compiled
clean**, so the skill taught API that exists rather than API that sounds right.
`apple-performance`: fired and read all three relevant references; classified
the symptom as a hitch rather than a hang, chose Animation Hitches over Time
Profiler, and split commit from render hitches.
The first `apple-intelligence` run omitted `--plugin-dir`, loaded nothing, and
is recorded as an invalid run and discarded.
Evidence: `task-4-report.md:60-95`, `task-8-consume-test.log`.

### 8. Real exercise, `apple-intelligence` — **PASS (full runtime)**
All five documented snippets inserted **verbatim** into StudioFixture;
`** BUILD SUCCEEDED **`; **no snippet required correction**. Live on-device
model output captured:

    [GUIDED] name=Whiskers age=3
    [STREAM] tick 1: name=Optional("Wh")       age=nil
    [STREAM] tick 3: name=Optional("Whiskers") age=nil
    [STREAM] tick 6: name=Optional("Whiskers") age=Optional(3)
    [TOOL] tool-call entries in transcript: 1

The streaming trace is direct runtime confirmation of the reference's
partial-value claim: properties fill in progressively and out of step. Tool
calling ran the documented tool and the model handled its empty result. The
unavailable path was exercised by construction only (this host reports
`.available`) and is recorded as explicitly weaker evidence.
Fixture reverted; `git status --porcelain` empty.
Evidence: `task-5-exercise.log:1-101`, `task-5-availability.log`.

### 9. Real exercise, `apple-performance` — **PARTIAL**
The documented Time Profiler loop was verified end to end with real numbers.
The cost was identified **from the trace** — the heaviest-self ranking named the
planted function unprompted — then fixed and re-measured:

    BEFORE  4965 ms total, 4961 ms (99.9%) in RowCost.checksum(for:)
    AFTER   1251 ms total, 1246 ms (99.6%) in RowCost.checksum(for:)
    4961 ms -> 1246 ms: 4.0x reduction

**Not verified:** the SwiftUI-specific half. The fixture's SwiftUI scene never
activated in this session — `RowView.body` instrumented to log every invocation
recorded **zero**, process at **0.0% CPU**, across four launch methods — so a
scrolling-list hitch could not be produced. The **Animation Hitches** template,
the commit/render hitch split, and the **SwiftUI** instrument's update lanes are
untested, and `swiftui-performance.md` therefore ships on doc fidelity and
snippet compilation alone. Recorded rather than approximated.

Also found here: a real bug in the trace aggregator (repeated backtraces are
`ref`-referenced and were not dereferenced, silently erasing the hot path). It
had already produced a wrong figure in an earlier evidence log, which was
corrected in place rather than quietly edited.
Evidence: `task-9-report.md:1-111`, `task-9-before.log`, `task-9-after.log`,
`task-9-prep-trace-toolchain.log:112-148` (the correction).

### 10. Snippets typecheck — **PASS, 22/22**
Every Swift snippet in all eight new references compiled against the Xcode 27.0
(27A5228h) SDK. This was the highest-yield rule in the phase: it caught
`resolved(in:)` vs `resolve(in:)`, **two non-compiling samples in Apple's own
documentation**, `toolCallingMode`'s default being `nil` rather than a named
case, and `AppEntity`'s `typeDisplayRepresentation` requirement.
Evidence: `task-2-typecheck.log`, `task-3-typecheck.log`, `task-7-typecheck.log`.

### 11. `claude plugin validate . --strict` — **PASS**
Clean at every commit touching `plugin/`. Version bumped to 0.7.0 in
`plugin/.claude-plugin/plugin.json` only; the marketplace entry carries no
version. The plugin description, stale since it predated two skills, was
updated in both files identically.
Evidence: `task-10-validate.log`.

### Carried forward
- **Verification item 6 of the charter (one real feature in a real project)
  remains PARTIAL**, and is now the binding precondition on the skill
  kill-switch gate. Every phase shipping without it raises the stakes of the
  eventual measurement.
- **The corpus is spent.** `pipeline/convert.sh` is dormant until new books
  arrive; there is no books map for either new skill and there will not be one.
- **Classical ML (Vision, Speech, Core ML) is cut for capacity, not value** —
  the "model priors are reliable" rationale was withdrawn as false. Strongest
  Phase 7 candidate.
- **The one untested claim in the phase** is the SwiftUI/Animation-Hitches
  instrument path (item 9). It needs an interactive GUI session.
