# apple-studio Phase 7: Fluid Interfaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `plugin/skills/apple-animations/references/fluid-interfaces.md`, one reference on Apple's fluid-interface principles for SwiftUI gesture motion; correct three existing references that name no API for behavior they describe; add two judgment rules to `animation-taste.md`; move classical ML to Phase 8. Version bump to 0.8.0.

**Architecture:** One reference into an existing skill, no new skill and no new agent. The reference is organised around what SwiftUI already provides rather than around how to build a gesture, because the supporting probe found five of twelve principles already free in the framework. Its centre is two traps: SwiftUI's built-in momentum prediction travels half as far as scroll deceleration, and `interpolatingSpring`'s `initialVelocity` is not in points per second. Spec: `docs/specs/2026-09-12-phase7-fluid-interfaces-design.md`.

**Tech Stack:** Claude Code plugin components; existing `pipeline/` (`docc.py` for live DocC JSON, `typecheck_snippets.py` as the ship gate, `run_evals.py` for the trigger sweep); the shipped `SwiftUI.swiftinterface` as a third verification surface; `swiftc -typecheck`; Xcode 27 / iPhoneOS27.0.sdk; iOS 27.0 simulator and one physical device.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-7`, already created from `main` at `de9dfc7`. Spec and probe evidence committed at `c0cb375`. All paths relative to repo root unless absolute.
- Toolchain: Xcode 27 beta, `iPhoneOS27.0.sdk`, macOS 27, Swift 6.4. Fixture app `~/Projects/StudioFixture` (scheme `StudioFixture`). **Leave its git tree clean after any run** — `git -C ~/Projects/StudioFixture status --porcelain` empty at task close.
- **Leave no simulator booted.** Task 3 boots one; shut it down in the same task.
- Live-docs-first (CONVENTIONS.md). A 200 on a doc page is not evidence a symbol exists. **Compilation is the ship gate for every API-specific claim.**
- Three verification moves, in increasing strength: `docc.py` confirms a symbol is documented; `typecheck_snippets.py` confirms it exists in the shipped SDK; reading the `.swiftinterface` answers *how* it behaves. The third is new this phase.
- Probe evidence: `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/probe/` — six command logs, `probe.md` (nine blocks, 9/9 typecheck clean), and `FINDINGS.md`.
- **Binding fact 1 (spec Finding 1).** `DragGesture.Value.velocity` is `4.0 * (predictedEndLocation - location)`, so `predictedEndTranslation` projects **0.25 s** of travel. Apple's *Designing Fluid Interfaces* projection `(v/1000) * d / (1 - d)` at `d = 0.998` projects **0.499 s**, which is **1.996×** further (0.499 / 0.25 exactly — an earlier 2.00× in this plan was a rounded figure stated as an exact one; Task 3a measured 1.996000 over 48 flicks). The reference MUST record the measured constants (`normal` 0.998, `fast` 0.99, measured on iOS 27.0), not the WWDC slide — Apple's current docs no longer publish them.
- **Binding fact 2 (spec Finding 2).** `Animation.interpolatingSpring(_:initialVelocity:)` takes velocity in units of the from-to distance per second. A gesture velocity in points per second MUST be divided by the remaining distance.
- **Binding fact 3 (spec Finding 3).** No public SwiftUI API rubber-bands a custom `DragGesture`. `.scrollBounceBehavior(_:axes:)` covers `ScrollView` only.
- **Sourcing quarantine.** The two judgment rules in Task 2 come from Emil Kowalski's design-engineering writing, not from Apple. `animation-taste.md`'s header MUST name that source separately from its Apple sources so a later reader can tell which claims Apple backs.
- Reference files: CONVENTIONS.md header block (`> verified:` / `> sources:`), decision-grade only, target 120–160 lines for the new file, own words, no remaining `[VERIFY` markers at commit.
- Eval-harness rules (binding): run the sweep through `pipeline/run_evals.py`, never a fresh loop. It guards the fixture, sets stdin to `/dev/null`, and defaults to `--max-turns 6`. Eval prompts avoid "build X" phrasing (superpowers brainstorming preemption).
- Evidence standard: every verification claim is backed by a captured log under `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/`, with quoted lines in the task report. Verification tables use `file:line-range` pointers.
- Out of scope, verbatim from the spec: the other six `design-engineering` skills; the `design-engineering` skill itself beyond the two judgment rules; Emil's duration budgets and the 0.11 flick threshold (web-measured); `materials-and-type.md` (already covered at `apple-design/references/hig-foundations.md:31-154`); new skills; new agents; classical ML.
- **Typecheck baseline, measured 2026-09-12: 28/48 clean across all shipped references.** The 20 failures are all in Phase 1-5 files and are untriaged (`docs/deferred.md` item 7). Phase 7 fixes exactly one of them — the `@State` fragment in `animation-taste.md`, because Task 2 edits that file. Any other pre-existing failure is out of scope; **do not treat a red file you did not touch as this phase's problem.**
- `pipeline/typecheck_snippets.py` gained a `CoreGraphics` hint and gesture/animation additions to the SwiftUI hint during planning. Without them a `CGFloat`-only helper failed with "cannot find type 'CGFloat'", which reads like an invented symbol. The 28/48 baseline is unchanged by the fix.
- Commit after every task minimum. Version bump to 0.8.0 in Task 4 only.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Phase 6 sweep + charter amendment

**Files:**
- Modify: `docs/deferred.md` (item 1 measurement; item 5 status after Task 3 — leave a pointer here, fill it in Task 3)
- Modify: `docs/specs/2026-08-03-apple-studio-design.md:186-187` (ML moves to Phase 8)

**Interfaces:**
- Consumes: `docs/deferred.md` item 1's recorded scan method; the charter's long-tail note.
- Produces: the recorded skill-gate measurement Task 4's spec-append cites.

- [ ] **Step 1: Confirm the branch.** Run `git branch --show-current` → expect `phase-7`. Run `git merge-base --is-ancestor de9dfc7 HEAD` → expect exit 0.
- [ ] **Step 2: Run the skill kill-switch measurement.** Use the method recorded in `docs/deferred.md` item 1's Phase 6 paragraph: JSON-parse every `Skill` tool_use block across `~/.claude/projects/**/*.jsonl` for an `input.skill` naming an `apple-studio:*` skill. Exclude sessions whose project path contains `-scratchpad-`, `-private-tmp-`, `apple-studio`, or `StudioFixture`. Scope to sessions since 2026-09-02. Write the raw scan to `task-0-killswitch.log`.
- [ ] **Step 3: Apply the pre-taken decision rule — do NOT improvise.** Item 1 states the gate fires only "at the opening sweep of the first phase following a shipped real feature". No real feature has shipped through this plugin, so **no skill is cut this phase whatever the count**. Append the measurement and this reasoning to item 1. If the count is non-zero, record it as the first evidence the plugin is earning its keep — that is a finding, not a trigger.
- [ ] **Step 4: Amend the charter.** Edit `docs/specs/2026-08-03-apple-studio-design.md:186-187`. The line currently reads that classical ML "is the strongest Phase 7 candidate". Change it to name Phase 8, with a dated note: `> **Amended 2026-09-12 (Phase 7).** ML moves to Phase 8. Phase 7 ships the fluid-interfaces reference instead — see docs/specs/2026-09-12-phase7-fluid-interfaces-design.md. ML is deferred for sequencing, not for value; the Phase 6 withdrawal of the "old and stable" rationale stands.` CONVENTIONS.md says amend deliberately, never silently.
- [ ] **Step 5: Check the two `verified:` headers this phase will touch.** Read the header lines of `plugin/skills/apple-design/references/animation-taste.md` and `plugin/skills/apple-animations/references/animation-fundamentals.md`. Record their current dates in the task report. They are re-stamped in Task 2 **only because Task 2 edits them** — an untouched file keeps its date.
- [ ] **Step 6: Commit.** `git add docs/ && git commit -m "Phase 7 Task 0: Phase 6 sweep + charter amendment"`

---

### Task 1: Distillation map + `fluid-interfaces.md`

**Files:**
- Create: `pipeline/maps/fluid-interfaces-live.md`
- Create: `plugin/skills/apple-animations/references/fluid-interfaces.md`
- Modify: `plugin/skills/apple-animations/SKILL.md` (one routing line)

**Interfaces:**
- Consumes: the probe logs under `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/probe/`; the spec's twelve-row table.
- Produces: the reference Task 3 exercises and Task 4 evaluates.

- [ ] **Step 1: Write the distillation map.** `pipeline/maps/fluid-interfaces-live.md`, DocC JSON prefix `https://developer.apple.com/tutorials/data/documentation/`. Seeds, all confirmed 200 during the probe: `SwiftUI/DragGesture/Value` (and children `velocity`, `predictedEndTranslation`, `predictedEndLocation`), `SwiftUI/GestureState`, `SwiftUI/ButtonStyleConfiguration/isPressed`, `SwiftUI/Spring` (all four initialisers and the state/force children), `SwiftUI/Animation` spring family (`spring(response:dampingFraction:blendDuration:)`, `interactiveSpring`, `interpolatingSpring(_:initialVelocity:)`), `SwiftUI/ScrollTargetBehavior`, `SwiftUI/ScrollTargetBehaviorContext`, `SwiftUI/ScrollBounceBehavior`, `SwiftUI/View/sensoryFeedback(_:trigger:)`. Record `OUT OF SCOPE (Phase 7):` for `UIKit/UIScrollView` beyond the deceleration constants, and for Metal/graphics smoothness. Add a `NON-DOC SOURCE:` line naming the `.swiftinterface` path, since Finding 1 has no doc page behind it.
- [ ] **Step 2: Re-probe the seeds.** The probe is days old by execution. Re-run `python3 pipeline/docc.py --children` over the seed list and diff against the probe logs. Any endpoint that changed class becomes a `MISSING:` line in the map.
> **Corrected 2026-09-12 after Task 1 review.** The `DismissableCard` snippet
> below is the reference's shipped version, mirrored back here. The original
> plan text divided `initialVelocity` by `max(abs(target - offset), 1)` and
> assigned raw `translation` in `.onChanged`. Both were wrong: `abs()` mis-signs
> the normalizer on any upward flick, and raw translation re-bases the card to
> ~0 on the second drag. Ledger: Task 1 fix round 1/5.

- [ ] **Step 3: Write the reference.** Target 120–160 lines. Header per CONVENTIONS.md: `> verified: 2026-09 against <the human doc URLs for the seeds above>; iPhoneOS27.0.sdk SwiftUI.swiftinterface; deceleration constants measured on iOS 27.0 simulator` and `> sources: live Apple docs; Designing Fluid Interfaces (WWDC 2018); shipped SDK interface`. Five sections, in this order:

  **1. What SwiftUI already does.** One to three lines each, each naming the symbol. A reader who does not know these are free will hand-roll them.
  - Touch-down feedback: `ButtonStyleConfiguration.isPressed` in a `ButtonStyle`.
  - 1:1 tracking: `@GestureState` with `.updating`, setting `transaction.disablesAnimations = true` so the spring does not smooth the finger.
  - Interrupt without a jump: spring animations retarget from the presentation value by construction.
  - Grab and reverse mid-flight: the same mechanism; do not build interruption logic.
  - Velocity blending on reversal: `blendDuration` interpolates the response value between successive springs.

  **2. Momentum projection and the 0.25 s prediction.** Binding fact 1, in full. Both formulas, the measured constants, and the decision it drives: `predictedEndTranslation` for a modest snap, compute from `.velocity` for scroll feel. Include this snippet, which typechecks (probe block 1):

  ```swift
  /// Apple's projection from Designing Fluid Interfaces (WWDC 2018).
  /// decelerationRate 0.998 matches UIScrollView.DecelerationRate.normal,
  /// measured on iOS 27.0; 0.99 (.fast) is snappier.
  func project(initialVelocity: CGFloat, decelerationRate: CGFloat = 0.998) -> CGFloat {
      (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate)
  }
  ```

  **3. Velocity handoff.** Binding fact 2. Show the division that makes `initialVelocity` correct, and say what happens without it (large silent overshoot):

  ```swift
  struct DismissableCard: View {
      @State private var committed: CGFloat = 0
      @GestureState private var drag: CGFloat = 0
      let snapPoints: [CGFloat] = [0, 200, 400]

      var body: some View {
          Color.clear
              .offset(y: committed + drag)
              .gesture(
                  DragGesture()
                      .updating($drag) { value, state, transaction in
                          transaction.disablesAnimations = true
                          state = value.translation.height
                      }
                      .onEnded { value in
                          // translation is measured from this drag's start.
                          let released = committed + value.translation.height
                          let projected = released + project(initialVelocity: value.velocity.height)
                          let target = snapPoints.min {
                              abs($0 - projected) < abs($1 - projected)
                          } ?? 0
                          // SIGNED — abs() here inverts the normalized velocity.
                          let delta = target - released
                          guard abs(delta) > 0.5 else {
                              withAnimation(.snappy) { committed = target }
                              return
                          }
                          withAnimation(.interpolatingSpring(
                              .snappy, initialVelocity: value.velocity.height / delta
                          )) { committed = target }
                      }
              )
      }
  }
  ```

  **4. Boundaries.** Binding fact 3. `.scrollBounceBehavior(_:axes:)` for a `ScrollView`; nothing for a custom drag. Ship the rubber-band function and say to apply it while tracking, before the value reaches the spring:

  ```swift
  /// The further past the bound, the less the element follows.
  func rubberband(overshoot: CGFloat, dimension: CGFloat, constant: CGFloat = 0.55) -> CGFloat {
      (overshoot * dimension * constant) / (dimension + constant * abs(overshoot))
  }
  ```

  **5. Technique with no API.** Four rules, no code: decompose 2D motion into independent X and Y springs, because one spring on a 2D distance desyncs when the axes have different velocities; make intermediate frames point at the outcome rather than interpolating blindly to it; keep the per-frame positional change below the perception threshold; and add bounce only when the gesture itself carried momentum, since overshoot on a menu that merely faded in reads as wrong.

- [ ] **Step 4: Resolve any `[VERIFY` markers.** `grep -rn "VERIFY" plugin/skills/apple-animations/` → expect empty.
- [ ] **Step 5: Typecheck.** `python3 pipeline/typecheck_snippets.py plugin/skills/apple-animations/references/fluid-interfaces.md`. Expected: exit 0, every block PASS. A block that fails is a reference defect — fix the reference, not the test. One caveat: `typecheck_snippets.py` tries several framings, and a bare `.onEnded { }` fragment can fail on missing context rather than on a bad symbol. The fix is to make the snippet self-contained by showing its enclosing `View`, never to weaken the claim or drop the block. Log to `task-1-typecheck.log`.
- [ ] **Step 6: Add the routing line.** In `plugin/skills/apple-animations/SKILL.md`, add to the reference list: `- Gesture-driven motion — drags, sheets, carousels, flick-to-dismiss → references/fluid-interfaces.md`.
- [ ] **Step 7: Validate and commit.** `claude plugin validate . --strict`; `git commit -m "Phase 7 Task 1: fluid-interfaces reference + distillation map"`

---

### Task 2: Three corrections + two judgment additions

**Files:**
- Modify: `plugin/skills/apple-design/references/swiftui-design-implementation.md` (the `ButtonStyle` section, near line 13)
- Modify: `plugin/skills/apple-design/references/hig-patterns.md:76` (the layered-feedback line)
- Modify: `plugin/skills/apple-animations/references/animation-fundamentals.md:77` (the `blendDuration` mention)
- Modify: `plugin/skills/apple-design/references/animation-taste.md` (header + two rules)

**Interfaces:**
- Consumes: the probe's grep results — `sensoryFeedback` and `personality` each returned zero hits across `plugin/skills/**/*.md`. **The third term did not.** `isPressed` was written into this plan and into the spec as a zero-hit claim and it is false; `swiftui-design-implementation.md:15,17` has named `configuration.isPressed` since Phase 1. Corrected 2026-09-12 during Task 2 — the dated note in `docs/specs/2026-09-12-phase7-fluid-interfaces-design.md`, Deliverables section 2, carries the root cause and the reason the deliverable survives. Read it before working Step 2.
- Produces: nothing later tasks depend on. This task is independently revertible.

- [ ] **Step 1: Re-confirm all three gaps before editing — one grep per term, never an alternation.** Run `grep -rn "isPressed" plugin/skills --include='*.md'`, then the same for `sensoryFeedback` and `personality`. Expected: zero hits for `sensoryFeedback` and `personality`; **`isPressed` has hits** at `plugin/skills/apple-design/references/swiftui-design-implementation.md:15,17`, present since Phase 1. Step 2 is therefore a review-and-extend of existing text, not an addition. An alternation cannot tell you which branch matched, and reading one as if it could is exactly how this plan came to carry a false zero-hit claim — see the dated correction note in `docs/specs/2026-09-12-phase7-fluid-interfaces-design.md`, Deliverables section 2. If either remaining term now has a hit, its edit becomes a review too — record which in the task report.
- [ ] **Step 2: `swiftui-design-implementation.md`.** In the `ButtonStyle` section, add: a custom `ButtonStyle` receives `configuration.isPressed`, and that is the hook for touch-down feedback. Feedback on release reads as dead, because the press is the moment the person is watching. Keep the scale subtle — 0.95 to 0.98 — and note that `scaleEffect` scales the label and any icon with it, which is what makes it read as physical.
- [ ] **Step 3: `hig-patterns.md:76`.** Beside the existing layered-feedback line, name the SwiftUI mechanism: `.sensoryFeedback(_:trigger:)` (iOS 17), which fires haptic or audio feedback off an `Equatable` value change. The HIG principle already sits here; it has named no API until now.
- [ ] **Step 4: `animation-fundamentals.md:77`.** `blendDuration` is mentioned twice in this file and never explained. Add one sentence: it is the time over which a new spring interpolates its *response* value from the outgoing spring's, which keeps a reversal from reading as a velocity discontinuity. Velocity itself is preserved regardless; `blendDuration` smooths the stiffness change.
- [ ] **Step 5: `animation-taste.md` — the sourcing quarantine first.** Edit the header `> sources:` line to name the new source separately, for example: `> sources: HIG: Motion; iOS Animations by Tutorials v7.0.0 (Kodeco); live SwiftUI DocC (API verification); Emil Kowalski's design-engineering writing (emilkowal.ski, MIT-licensed skills — the Cohesion and Worth-it rules only, not Apple-sourced)`. Do this **before** adding the rules, so the file is never in a state where unattributed non-Apple guidance sits under an Apple-only header.
- [ ] **Step 6: `animation-taste.md` — add the two rules.** Under a new `## Cohesion and Worth-It` heading: (a) motion should match the component's personality and the rest of the product — playful can be bouncier, a professional dashboard stays crisp, and one bouncy component in an otherwise crisp app reads as a defect rather than as character; (b) a detail earns its place when its absence would be *felt* rather than *seen*, so decoration on frequently-used UI is a cost, not a bonus.
- [ ] **Step 7: Re-stamp only the touched headers.** Set `verified:` to `2026-09` on the four files edited in this task, appending what was actually checked. Do not touch any other file's date.
- [ ] **Step 8: Fix the one pre-existing failure in `animation-taste.md`.** Snippet #1 is `@State private var committedOffset: CGFloat = 0` at top level. It fails as `'nonmutating' is only valid on methods` because the fragment has no enclosing `View` — a framing artifact, not an invented symbol. Wrap it in the `struct` it belongs to so the snippet stands alone. Fix this one only; the other 19 failures in the corpus belong to `docs/deferred.md` item 7.
- [ ] **Step 9: Typecheck the edited references.** `python3 pipeline/typecheck_snippets.py plugin/skills/apple-design/references/swiftui-design-implementation.md plugin/skills/apple-design/references/animation-taste.md plugin/skills/apple-animations/references/animation-fundamentals.md plugin/skills/apple-design/references/hig-patterns.md`. Expected exit 0 — these four files must be fully clean after Step 8. If a file you edited went from passing to failing, the edit is the cause.
- [ ] **Step 10: Validate and commit.** `claude plugin validate . --strict`; `git commit -m "Phase 7 Task 2: name isPressed, sensoryFeedback, blendDuration; add cohesion and worth-it rules"`

---

### Task 3: Real exercise — confirm the 1.996× ratio on a device

**Files:** none committed (fixture reverted). Evidence only. **This is the phase's strongest verification and `fluid-interfaces.md` stands or falls on it.**

**Interfaces:**
- Consumes: `fluid-interfaces.md` sections 2 and 3 as written in Task 1.
- Produces: the measurement Task 4's spec-append cites; the closure (or re-deferral) of `docs/deferred.md` item 5.

- [ ] **Step 1: Confirm the fixture is clean before starting.** `git -C ~/Projects/StudioFixture status --porcelain` → expect empty. A dirty tree makes any write un-attributable; stop and restore if it is not empty.
- [ ] **Step 2: Build a drag-to-dismiss sheet in StudioFixture.** A card with three snap points, a `DragGesture` tracking 1:1 via `@GestureState`, and a release handler. Copy the release handler from `fluid-interfaces.md` section 3 verbatim — if the reference's code does not work here, the reference is wrong.
- [ ] **Step 3: Instrument both projections.** On release, log both landing points for the same gesture: `value.predictedEndTranslation.height`, and `offset + project(initialVelocity: value.velocity.height)`. Log the raw `value.velocity.height` alongside them.
- [ ] **Step 4: Run on a physical device and flick the card ten times.** A gesture is felt, not read; the simulator's pointer does not produce representative velocities. Capture the log.
- [ ] **Step 5: Check the ratio.** For each flick, divide the Apple projection by `predictedEndTranslation`. Expected: **1.996**, the exact closed form, since both are linear in velocity. `0.499 / 0.25` is 1.996 exactly — the 0.2 % gap from 2.00 is a deterministic constant, not floating-point noise, so a reading of 1.996 is the reference **confirmed**, not a rounding miss. **The gate is a tight band, not an equality test: a per-flick ratio outside 1.995–1.997 means the reference's central claim is wrong** — stop, record the real ratio, and correct section 2 before proceeding. The band is set by what Task 3a actually saw in the Simulator: 1.996000 across 48 flicks, min 1.995999, max 1.996000, a spread of one part in a million. A device reading anywhere near the edge of the band therefore passes the gate but is still worth recording, because 3a's spread predicts it should not happen. (Stop-gate corrected 2026-09-12 after Task 3a; it previously demanded 2.00 and would have failed a correct measurement.) Write the table to `task-3-projection.tsv`.
- [ ] **Step 6: Judge the feel, and record it as judgment.** Flick the card under each projection and note which lands where the gesture was going. This is subjective and the report MUST label it as such. The arithmetic is the claim; the feel is the reason anyone cares.
- [ ] **Step 7: Close deferred item 5.** Its trigger is "the next time anyone runs Xcode interactively on a SwiftUI project", which this task is. Product > Profile with the **SwiftUI** template, with the scheme's Profile action set to **Debug** — that is the untested explanation recorded against the item (Profile builds Release by default). If the instrument now records data, update `docs/deferred.md` item 5 and add the Debug requirement to `plugin/skills/apple-performance/references/swiftui-performance.md`. If it still records nothing, record that and leave the item open with the new evidence.
- [ ] **Step 8: Restore the fixture and the simulator.** `git -C ~/Projects/StudioFixture clean -fd && git -C ~/Projects/StudioFixture restore .`, then confirm `status --porcelain` is empty. Shut down any booted simulator (`xcrun simctl shutdown <udid>`).
- [ ] **Step 9: Commit the evidence.** `git add .superpowers/ docs/deferred.md && git commit -m "Phase 7 Task 3: device exercise — projection ratio measured, deferred item 5"`

---

### Task 4: Eval sweep + validate + version bump + spec append

**Files:**
- Modify: `plugin/skills/apple-animations/evals/triggers.md`
- Modify: `plugin/.claude-plugin/plugin.json` (0.7.1 → 0.8.0)
- Modify: `docs/specs/2026-09-12-phase7-fluid-interfaces-design.md` (verification results appended)
- Modify: `CONVENTIONS.md` (conditional — see Step 6)

**Interfaces:**
- Consumes: every prior task's captured log.
- Produces: the shipped 0.8.0 plugin and the phase's verification record.

- [ ] **Step 1: Add trigger-eval prompts.** In `plugin/skills/apple-animations/evals/triggers.md`, add to **Should fire**: "This sheet snaps back instead of following my finger"; "Make this card fling to the nearest snap point like a scroll view"; "My drag-to-dismiss overshoots wildly when I release". Add to **Should NOT fire**: `- "Why does my ScrollView stutter when I scroll fast?"  (apple-performance)`. This is the sharper discrimination test — the existing file already covers the `apple-design` boundary, and the new reference's risk is pulling scroll-*performance* questions toward gesture *motion*. Avoid "build X" phrasing — it preempts to superpowers brainstorming.
- [ ] **Step 2: Run the full sweep.** Build the prompts TSV from every skill's `evals/triggers.md`, then `python3 pipeline/run_evals.py <prompts.tsv> .superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-4-evals/`. Expected: every should-fire row invokes its named skill, every should-NOT row does not. The driver refuses to start on a dirty fixture and exits non-zero on any write — both are pass conditions, not obstacles to work around.
- [ ] **Step 3: Consume test.** One prompt whose answer requires `fluid-interfaces.md`, run from the fixture cwd with `--allowedTools "Skill Read"`. Pre-validate the prompt against the shipped file by grepping it for the topic first. Suggested: "I have a drag-to-dismiss card. When I flick it, it lands short of where it feels like it should go." Expected: the session reaches section 2 and distinguishes the two projections. Capture the log.
- [ ] **Step 4: Validate and bump.** `claude plugin validate . --strict` → expect pass. Edit `plugin/.claude-plugin/plugin.json` version to `0.8.0`. Re-run validate. The version lives here only, never in the marketplace entry.
- [ ] **Step 5: Append verification results to the spec.** Follow the Phase 6 shape (`docs/specs/2026-09-02-phase6-intelligence-performance-design.md:349`): one numbered subsection per verification item from the spec's definition of done, each with a **PASS** / **PARTIAL** / **FAIL** verdict and a `file:line-range` evidence pointer. Include the kill-switch count from Task 0 and the measured projection ratio from Task 3.
- [ ] **Step 6: Decide the `.swiftinterface` convention — a real decision, not a formality.** The spec says this technique SHOULD go into CONVENTIONS.md "once this phase confirms it generalises". It generalised here if, and only if, reading the interface answered a question `docc.py` and `typecheck_snippets.py` could not. It did for Finding 1. Add it to CONVENTIONS.md's pipeline-tooling section as a third named move, with the Finding 1 example as its justification. If Task 1's re-probe showed the interface path has moved or the property bodies are no longer inlinable, record that instead and do not add it.
- [ ] **Step 7: Record the manual hand-off items** in the task report (Michael runs these, not automated): Xcode re-import after the Phase 7 merge, per `docs/deferred.md` item 3; and deletion of the stale `phase-3` through `phase-6` remote branches, whose content is preserved in the squash merges and tags.
- [ ] **Step 8: Final fixture check.** `git -C ~/Projects/StudioFixture status --porcelain` → expect empty. Phase 6 left nine files behind by skipping exactly this closing check.
- [ ] **Step 9: Commit and open the PR.** `git commit -m "Phase 7 Task 4: evals, validate, v0.8.0, spec verification append"`, then one PR titled `Phase 7: Fluid interfaces — apple-animations reference, v0.8.0`, and tag `v0.8.0` after merge.

---

## Deferred to the phase report (not steps)

- Whether a custom `ScrollTargetBehavior` example belongs in `fluid-interfaces.md` or nearer `swiftui-performance.md`. `ScrollTargetBehaviorContext.velocity` is the one place SwiftUI hands over release velocity for a scroll view, and it compiled clean in the probe. The spec left this open for the plan; the plan leaves it open for the implementer, who will know after writing section 2 whether the file has room. Record the decision either way.
