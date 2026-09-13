# apple-studio Phase 7: Fluid interfaces — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`). Decisions taken 2026-09-12;
this doc is the input to the Phase 7 implementation plan.

Register: spec prose (engineer audience). No project glossary exists; terms
follow CONVENTIONS.md.

## Goal

Ship one new reference covering Apple's fluid-interface principles for
SwiftUI gesture-driven motion. Correct three places in existing references
that the probe exposed. Add two judgment rules the probe did not reach. Move
classical ML to Phase 8.

Version bump to 0.8.0.

**No new skill.** `apple-animations` gains depth; no skill changes shape and
no agent returns. `docs/deferred.md` item 1 records zero genuine non-fixture
invocations of any shipped skill. Adding a twelfth skill against that record
would invert the kill-switch rule. Phase 7 deepens what exists instead.

### Origin

Phase 7 did not come from the charter's long tail. It came from evaluating
the `design-engineering` plugin for integration into apple-studio on
2026-09-12. That plugin lives at
`~/Projects/agent-tools/plugins/design-engineering` and covers interface
craft on the Svelte stack. It is adapted from `emilkowalski/skills` under the
MIT licence.

The merge does not work. Six of its seven skills are bound to CSS and Svelte
mechanics, and the seventh collides by name with this plugin's
`apple-design`. One slice survived the stack strip: that seventh skill
distills Apple's *Designing Fluid Interfaces* (WWDC 2018), and none of that
material appears anywhere under `plugin/`.

A probe on 2026-09-12 measured how much of it SwiftUI already provides. The
probe result, not the source plugin, determines the shape of this phase.

### Charter amendment

The charter names classical ML "the strongest Phase 7 candidate"
(`docs/specs/2026-08-03-apple-studio-design.md:186-187`). ML moves to Phase
8. Amending that line is a task in this phase, not a side effect of writing
this spec.

ML is deferred for sequencing, not for value. The Phase 6 spec already
withdrew the claim that classical ML frameworks are stable enough to skip
(`docs/specs/2026-09-02-phase6-intelligence-performance-design.md:293-314`).
That withdrawal stands.

## What the probe established

Evidence:
`.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/probe/` — six command
logs, the nine-block probe file, and a findings summary, captured 2026-09-12.

The probe checked twelve principles against the shipped SDK. Nine probe
snippets typecheck clean under `pipeline/typecheck_snippets.py`, which compiles
for `arm64-apple-macosx27.0.0` against the macOS platform frameworks — every
symbol the probe used is cross-platform SwiftUI, available on both iOS and
macOS, so the gate is as strong as it reads. (Attribution corrected 2026-09-12;
this line first said `iPhoneOS27.0.sdk`. See item 5 of the verification append.)

| # | Principle | SwiftUI provides | Verdict |
|---|---|---|---|
| 1 | Respond on touch-down | `ButtonStyleConfiguration.isPressed` | free |
| 2 | 1:1 tracking | `@GestureState` + `.updating` | free |
| 3 | Animate from the presentation value | springs retarget by construction | free |
| 4 | Grab and reverse mid-flight | same | free, documented |
| 5 | Blend velocity on reversal | `blendDuration` | free, unexplained |
| 6 | Independent X/Y springs | nothing | technique |
| 7 | Velocity handoff | `.velocity` + `interpolatingSpring` | trap |
| 8 | Momentum projection | `predictedEndTranslation` | trap |
| 9 | Rubber-banding | `.scrollBounceBehavior`, ScrollView only | gap |
| 10 | Damping-and-response pair | `Spring`, already covered | rule only |
| 11 | Hint in the gesture's direction | nothing | technique |
| 12 | Frame-level smoothness | nothing | technique |

The reference exists for the four rows that are not "free". Five free rows
get one-line pointers, because a reader who does not know the behavior is
free will hand-roll it.

### Finding 1 — SwiftUI projects half as far as scroll deceleration

The shipped `arm64e-apple-ios.swiftinterface` exposes the body of
`DragGesture.Value.velocity`, not only its signature:

```swift
velocity = CGSize(width:  4.0 * (predictedEndLocation.x - location.x),
                  height: 4.0 * (predictedEndLocation.y - location.y))
```

Inverting it gives `predictedEndLocation = location + velocity * 0.25`.
SwiftUI projects 0.25 s of travel.

Apple's *Designing Fluid Interfaces* projection is `(v/1000) * d / (1 - d)`,
where `d` is `UIScrollView.DecelerationRate`. The rates were measured at
runtime on an iOS 27.0 simulator. `normal` is 0.998 and `fast` is 0.99. At
0.998 the formula projects 0.499 s of travel. That is **1.996×** SwiftUI's own
prediction.

**Corrected 2026-09-12 after Task 3a measured it.** This spec first said 2.00×.
That was a rounded figure presented as an exact one. 0.499 / 0.25 = 1.996
exactly, and the plan compounded the error by telling the implementer to expect
"2.00 ± floating-point noise". The 0.2% gap is a deterministic constant, not
noise. Task 3a measured 1.996000 across 48 flicks, min 1.995999, max 1.996000,
with `predictedEndTranslation` implying exactly 0.250000 s of travel every time.

Consequence: `predictedEndTranslation` is a real projection, but a weaker one
than scroll deceleration. Snapping to the point nearest it lands a flick
short of where the gesture was going.

Apple's current documentation no longer publishes the deceleration
constants. Measuring beat citing, and the reference MUST record the
measurement rather than the WWDC slide.

### Finding 2 — `initialVelocity` is not points per second

`Animation.interpolatingSpring(_:initialVelocity:)` takes velocity in units
of the from-to distance per second. A gesture velocity in points per second
MUST be divided by the remaining distance first. Passing it raw produces a
large silent overshoot.

### Finding 3 — no rubber-banding API for a custom drag

`ScrollView` bounces for free through `.scrollBounceBehavior(_:axes:)`. A
`DragGesture` does not. A search of the shipped interface for `rubber`,
`resistance`, and `overscroll` returns no public API.

## Deliverables

### 1. New reference `plugin/skills/apple-animations/references/fluid-interfaces.md`

Target 120–160 lines. **Retired — this number no longer binds.** It yielded
three times during Task 1 and was retired at the third; the file shipped at 218
lines, inside CONVENTIONS.md's "a few hundred lines" and outside only this
number. Ruling and reasoning: item 4 of the verification append below, and
`progress.md:143-148`, `:243-251`. Sections, in this order:

1. **What SwiftUI already does** — rows 1 to 5 of the probe table, one to
   three lines each, each naming the symbol that provides it. This section
   exists to stop a reader reimplementing free behavior.
2. **Momentum projection and the 0.25 s prediction** — Finding 1, with both
   formulas and the measured constants. The decision it drives: use
   `predictedEndTranslation` for a modest snap, compute from `.velocity` for
   scroll feel.
3. **Velocity handoff** — Finding 2, with the division that makes
   `initialVelocity` correct.
4. **Boundaries** — Finding 3, with the rubber-band formula for the custom
   case and the pointer to `.scrollBounceBehavior` for the free one.
5. **Technique with no API** — rows 6, 11, and 12, plus the rule from row 10:
   add bounce only when the gesture itself carried momentum.

**Placement.** `apple-animations`, not `apple-design`. The probe pushed the
material implementation-heavy, and CONVENTIONS.md routes implementation
mechanics to `apple-animations`. The existing split holds:
`apple-design/references/animation-taste.md` owns whether to animate, and
this file owns how gesture-driven motion is wired.

**Routing.** `apple-animations/SKILL.md` gains one line pointing at the new
reference for drags, sheets, carousels, and flick-to-dismiss.

### 2. Three corrections in existing references

Each is one to three lines. Each closes a gap the probe found by grep over
`plugin/skills/**/*.md`. All three name an API that exists and is unmentioned.

| File | Gap | Fix |
|---|---|---|
| `apple-design/references/swiftui-design-implementation.md` | ~~`isPressed` has zero hits~~ **wrong, see correction below**; the file names `isPressed` but not the touch-down-vs-release argument | Add the release-reads-as-dead framing, the 0.95-0.98 range, and that `scaleEffect` carries the label and icon |
| `apple-design/references/hig-patterns.md` | The layered-feedback principle names no SwiftUI modifier | Name `.sensoryFeedback(_:trigger:)` (iOS 17) beside it |
| `apple-animations/references/animation-fundamentals.md` | `blendDuration` appears twice and is never explained | State what it does: interpolate the response value between springs |

**Correction, 2026-09-12, made during Task 2.** The row above originally
claimed `isPressed` had zero hits across `plugin/skills/**/*.md`. It is wrong.
`swiftui-design-implementation.md:15,17` has named `configuration.isPressed`
since Phase 1. It already carries the argument, quoted verbatim here: a
`ButtonStyle` ignoring `isPressed` "looks identical whether or not the user is
actually pressing it".

The error came from reading a single alternation grep —
`grep -rniE "predictedEnd|GestureState|isPressed|ButtonStyle"` — and attributing
its hits to `ButtonStyle` alone. An alternation cannot tell you which branch
matched. Per-term greps, which the other two claims in this table used, would
have caught it.

The deliverable survives the correction. Three pieces were genuinely missing.
The first is the touch-down-versus-release argument. The second is the
0.95-0.98 scale range. The third is that `scaleEffect` carries the label and
the icon with it. The `sensoryFeedback`
and `personality` zero-hit claims were re-verified against `main`. Both hold.

### 3. Two judgment additions to `animation-taste.md`

Neither came from the probe. Both came from comparing the two plugins, and
`personality` has zero hits across `plugin/skills/**/*.md`.

Both are stack-agnostic and both come from Emil Kowalski's design-engineering
writing rather than from Apple. The file header MUST name that source
separately from its Apple sources, so a later reader can tell which claims
Apple backs.

- **Cohesion.** Motion should match the component's personality and the rest
  of the product. One bouncy component in an otherwise crisp app reads as a
  defect, not as character.
- **Is this detail worth it?** A detail earns its place when its absence
  would be felt rather than seen. Decoration on frequently-used UI is a cost.

### 4. Charter amendment and version bump

Amend `docs/specs/2026-08-03-apple-studio-design.md` so ML reads as the Phase
8 candidate. Bump `plugin/.claude-plugin/plugin.json` to 0.8.0 in the final
task only.

## Sources and pipeline

Live-docs-only, as in Phases 5 and 6. The corpus is spent and holds nothing
on gesture physics.

Three verification moves, in increasing strength:

- **`pipeline/docc.py`** — confirms a symbol is documented. `DragGesture.Value`,
  `Spring`, `ScrollTargetBehavior`, `ScrollTargetBehaviorContext`, and the
  `Animation` spring family were enumerated this way.
- **`pipeline/typecheck_snippets.py`** — confirms a symbol exists in the
  shipped SDK. This is the ship gate for every API claim, per CONVENTIONS.md.
- **The shipped `.swiftinterface`** — new this phase. Reading
  `SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface`
  produced Finding 1, which neither of the other two moves could reach. The
  interface ships the bodies of some declarations — `velocity` is
  `@export(implementation)`, not `@inlinable` — so it answers *how* an API
  behaves, not only whether it exists. (Attribute name corrected 2026-09-12;
  this line and the shipped reference both said "inlinable".)

The third move SHOULD be added to CONVENTIONS.md as a named technique once
this phase confirms it generalises. That is a Task 0 judgment, not a
commitment made here.

Where a constant no longer appears in Apple's documentation, measure it. The
deceleration rates were read at runtime on an iOS 27.0 simulator. The phase
MUST leave no simulator booted and MUST leave `~/Projects/StudioFixture` with
a clean git tree.

## Opening task: Phase 6 sweep

Standard phase-opening sweep, plus two items that come due here.

1. **Kill-switch measurement.** Re-run the `input.skill` scan over
   `~/.claude/projects`, per the method recorded in `docs/deferred.md` item 1.
   The gate's precondition is still unmet: no real feature has shipped through
   this plugin, so no skill is cut whatever the count. Record the number.
2. **Deferred item 5 — the SwiftUI instrument.** Its trigger is "the next time
   anyone runs Xcode interactively on a SwiftUI project". This phase's real
   exercise is exactly that. Run the SwiftUI template once with the scheme's
   Profile action set to Debug, which is the untested explanation recorded
   against the item.
3. **Verified-header check** on the two files this phase edits most,
   `animation-taste.md` and `animation-fundamentals.md`.

## Verification (definition of done)

- **Every Swift block in the new reference typechecks.** The probe's 9 of 9
  is the floor, not the target.
- **Trigger evals**, run through `pipeline/run_evals.py` so the fixture guard
  applies. `apple-animations` fires on drag, sheet, carousel, and
  flick-to-dismiss requests. It stays silent on whether-to-animate
  (`apple-design`) and on build-and-run (`xcode-loop`). One should-fire and
  one should-not sample per prior skill, as in Phases 3 to 6.
- **Real exercise, full.** A gesture is felt, not read. Build a
  drag-to-dismiss sheet in StudioFixture. Implement both projections. Measure
  the landing point of an identical flick under each, and confirm the 1.996×
  ratio on a device rather than in arithmetic. Both measurements are kept as
  evidence. Finding 1 is this phase's central claim and it stands or falls
  here.
- **Consume test** with captured logs, every prompt pre-validated against
  actual reference coverage before it enters the plan. Evidence pointers as
  `<file>:<line-range>`.
- `claude plugin validate . --strict` passes at every commit touching
  `plugin/`. Re-import into Xcode after merge, per `docs/deferred.md` item 3.

## Out of scope

- **The other six `design-engineering` skills.** `animating-interfaces`,
  `reviewing-animations`, `improving-animations`,
  `finding-animation-opportunities`, and `animation-vocabulary` carry CSS and
  Svelte mechanics that do not survive the stack strip. Their judgment layer
  duplicates `animation-taste.md`.
- **The `design-engineering` skill itself.** Taste, defaults over options, and
  component API design are stack-agnostic and good. CONVENTIONS.md scopes this
  plugin to "is it correctly Apple" and hands visual distinctiveness to other
  tooling. Two items are taken as judgment additions above; the rest is not.
- **Emil Kowalski's duration budgets and the 0.11 flick threshold.** These are
  web-measured, not Apple-sourced. Importing them under a `verified:` header
  that cites the HIG would misattribute them. They can return if someone
  measures the Apple equivalents.
- **`materials-and-type.md` from the source plugin.** Materials, vibrancy, and
  type scales are already covered at
  `apple-design/references/hig-foundations.md:31-154`, from Apple directly.
- **New skills and new agents.** See Goal.
- **Classical ML.** Phase 8.

## Waiver

**G-X1 — CEE.CoreWords, "amend", 2026-09-12.** The controlled-English
dictionary prefers "change". This repo uses "amend" as a term of art for a
deliberate edit to a standing document. CONVENTIONS.md states "Amend
deliberately, never silently", and the charter carries "Amended 2026-09-02
(Phase 6)". Substituting "change" would break term consistency with both.

## Open question for the plan

Whether the new reference also needs a `SnapBehavior`-style custom
`ScrollTargetBehavior` example. `ScrollTargetBehaviorContext.velocity` is the
one place SwiftUI hands over release velocity for a scroll view, and it
compiled clean in the probe. It may belong in `swiftui-performance.md`'s
neighbourhood instead. The plan decides; this spec does not.

---

## Verification results (appended 2026-09-12, Phase 7 Task 4)

Evidence root: `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/`.
Pointers are `<file>:<line-range>` per CONVENTIONS.md. Where this phase found one
of its own claims to be wrong, the correction is recorded in place beside the
claim rather than substituted for it — the Phase 6 precedent, used three times
below.

### 1. Skill kill-switch measured, gate correctly did NOT fire — **PASS**
3,153 transcripts across 425 project directories; **80** distinct
(session, skill, date) invocations naming an `apple-studio:*` skill; **0 genuine
non-fixture invocations** since 2026-09-02. All 80 came from a single directory,
`StudioFixture` — the `apple-studio` repo itself contributed zero this time, and
that absence was confirmed by direct grep of the repo's own transcripts rather
than trusted from the classifier. Two skills absent from the Phase 6 tally now
show hits (`apple-intelligence` 15, `apple-performance` 24), so all eleven
shipped skills have now fired in the harness and none outside it. The
precondition stated at spec time — one real feature shipped through this plugin
— is still unmet, so **no skill is cut, regardless of the count**; this is the
second consecutive zero and it is a repeat of the prior finding, not a new
reason for the outcome.
Evidence: `task-0-killswitch.log:22-30` (raw numbers and exclusion tally),
`:50-64` (reading and result); rule, trigger and both measurements in
`docs/deferred.md:8-124`.

### 2. Charter amended — ML reads as the Phase 8 candidate — **PASS**
`docs/specs/2026-08-03-apple-studio-design.md:187-193`. The pre-existing
"strongest Phase 7 candidate" sentence was changed to Phase 8 in the same
blockquote as the new dated note, because leaving it would have contradicted the
note sitting four lines below it. The amendment states that ML moves for
sequencing, not for value, and that Phase 6's withdrawal of the
"model priors are reliable" rationale stands.
Evidence: `task-0-report.md:112-149` (before/after quoted verbatim).

### 3. `verified:` header check on the two most-edited files — **PASS**
Both `apple-design/references/animation-taste.md` and
`apple-animations/references/animation-fundamentals.md` read `2026-08` at the
opening sweep and were left unmodified there, because a header check is not a
re-reading. Task 2 then edited both and re-stamped each to `2026-09` with a
statement of what was re-verified: `animation-taste.md:1` records that the two
new judgment rules carry no API claim so no additional DocC check was owed, and
names Emil Kowalski's writing as a source separate from the Apple ones at `:2`;
`animation-fundamentals.md:1` records the re-check of
`Animation.spring(response:dampingFraction:blendDuration:)` that closed the
forward reference from the new reference.
Evidence: `task-0-report.md:150-160` (opening state),
`plugin/skills/apple-design/references/animation-taste.md:1-2`,
`plugin/skills/apple-animations/references/animation-fundamentals.md:1`.

### 4. New reference `fluid-interfaces.md` shipped — **PASS**
`plugin/skills/apple-animations/references/fluid-interfaces.md`, **218 lines**,
all five sections in the order this spec set: what SwiftUI already does
(`:13-48`), momentum projection and the 0.25 s prediction (`:50-97`), velocity
handoff (`:99-176`), boundaries (`:178-198`), technique with no API (`:200-218`).
It was 191 at Task 4; the final fix wave added the `presentationDetents` lead-in
that closes section 1 (`:37-48`) and a scope note on the drag example (`:165-176`),
and every line range in this append was re-derived against the file afterwards
rather than carried forward.
Routing added at `plugin/skills/apple-animations/SKILL.md:18`. Placement is
`apple-animations`, not `apple-design`, as specified.

**This spec set the 120–160 line target, at `:137`, and the controller ruled it
yielded — three times, before retiring it.** (An earlier draft of this paragraph
blamed the plan; that was wrong, and the target predates the plan. Corrected
2026-09-12. The outcome is unchanged: the target yielded, and the ruling stands,
and `:137` now carries a pointer here so the Deliverables section stops binding a
number this phase retired.) CONVENTIONS.md puts references at a few hundred lines
and Phase 6 shipped 100–250, so 191 at Task 4 — and 218 after the final fix wave —
is inside the standing convention and outside only a number this spec invented for
this one file. Task 4's +14 was the release-boundary warning from item 9 below,
which exists nowhere else in the plugin; the fix wave's +27 is the
`presentationDetents` lead-in and the drag example's scope note, and the first of
those is the line most likely to stop a reader writing any of the code around it. Splitting the file at the 1–2 / 3–5 seam was rejected because it would
break the typechecker's with-prior chaining that keeps block 2 compiling against
block 1 — it would have cost ship-gate coverage to buy a number.
Evidence: `progress.md:143-151`, `:243-251`.

### 5. Every Swift block in the new reference typechecks — **PASS, 3/3**
The spec set the probe's 9 of 9 as the floor; the shipped file carries three
blocks and all three compile clean — the projection function, `DismissableCard`,
and the rubber-band function, the third chained with-prior against the second.
Re-run at Task 4 over the file as shipped, after all three fix rounds, rather
than quoted from Task 1.

**The gate compiles for macOS, not for iOS, and this spec said otherwise twice.**
`pipeline/typecheck_snippets.py:75-77` passes `-F .../MacOSX.platform/...` and no
`-target`, so `swiftc` uses its host default and the compile triple is
`arm64-apple-macosx27.0.0`. Corrected here and at `:61` on 2026-09-12. **The
verification is not weakened by the correction**: every symbol in all three
blocks — `DragGesture`, `withTransaction`, `interpolatingSpring`, `CGFloat` —
is cross-platform SwiftUI and CoreGraphics, available on iOS and macOS alike, so
a clean macOS typecheck still establishes that nothing here is invented. What it
does not establish is iOS-only availability, and nothing in the file claims any.
The reference's own `verified:` header is untouched by this and stays correct: it
cites the iOS `.swiftinterface` for the `velocity` body, which is a claim about a
shipped iOS binary rather than about the compile target. This was recorded as a
Task 1 deferred minor (`progress.md:165-166`) and never propagated, which is how
a known-loose attribution hardened into a false verification claim in the binding
document — the same failure mode as items 6 and 8 below, one document further on.
Evidence: `task-4-typecheck-repowide.log:21-24`, `task-1-typecheck.log:1-8`,
`pipeline/typecheck_snippets.py:75-77`.

**Repo-wide, the gate now stands at 32/51, not the 28/48 recorded when this phase
was planned.** Task 1 added three passing blocks (48 → 51, 28 → 31) and Task 2
converted the one pre-existing failure this phase was authorized to touch
(31 → 32). 19 failures remain, across 12 files rather than 13, every one authored
in Phases 1–5 and none triaged. `docs/deferred.md` item 7 carries the corrected
baseline and the arithmetic; its trigger is unchanged.
Evidence: `task-4-typecheck-repowide.log:4627` (`TOTAL: 32/51`),
`task-4-typecheck-summary.txt:1-18`, `docs/deferred.md:441-465`.

### 6. Three corrections in existing references — **PASS, and one of this spec's own claims was false**
All three landed: the touch-down-versus-release argument, the 0.95–0.98 scale
range and the label-carries-the-icon point at
`apple-design/references/swiftui-design-implementation.md:19`;
`.sensoryFeedback(_:trigger:)` named beside the layered-feedback principle at
`apple-design/references/hig-patterns.md:76`; `blendDuration` explained as the
interpolation of the *response* value, with the explicit note that velocity is
preserved across the handoff regardless of it, at
`apple-animations/references/animation-fundamentals.md:79`.

**The `isPressed` zero-hit claim in this spec's own table was wrong**, found by
Task 2's implementer and corrected in place above (see "Correction, 2026-09-12,
made during Task 2"). The root cause is worth more than the correction: the claim
came from a single alternation grep,
`grep -rniE "predictedEnd|GestureState|isPressed|ButtonStyle"`, whose hits were
all attributed to one branch. **An alternation cannot tell you which branch
matched.** The other two claims in that table used per-term greps and both
re-verified clean against `main`.
Evidence: `task-2-report.md:11-30` (the corrected grep and its result),
`task-2-step1-grep.log:1-4` (the raw hits); correction text at this spec's Deliverables section 2.

### 7. Two judgment additions to `animation-taste.md` — **PASS**
Cohesion and "is this detail worth it?" at
`plugin/skills/apple-design/references/animation-taste.md:106-111`, under their
own heading. The file's `sources:` line names Emil Kowalski's design-engineering
writing separately from its Apple sources (`:2`), which is what the spec required
so a later reader can tell which claims Apple backs. Both rules are stated as
judgment, not as API, and carry no symbol that would need a DocC check.

### 8. Finding 1 — confirmed at runtime, with a precision correction — **PASS**
The phase's central claim stands. A drag-to-dismiss surface in StudioFixture
logged both projections for the same release: **ratio 1.996000 across 48 flicks**,
four sweeps, both directions, 201–2125 pt/s, min 1.995999, max 1.996000, no
outliers. `predictedEndTranslation` implied **exactly 0.250000 s** of travel on
48 of 48 — no jitter, no velocity dependence — which confirms the
`.swiftinterface` inversion in a running framework rather than on paper.

**The spec's own "2.00×" was wrong and the plan compounded it.** `0.499 / 0.25`
is `1.996` exactly; the 2.00 came from a `.2f` format string, and the plan then
told the implementer to expect "2.00 ± floating-point noise". The 0.2 % gap is a
deterministic constant, not noise. Corrected here (Finding 1, dated note), in the
plan, and in the shipped reference, which now says 1.996x and adds
"call it double when you talk about it".
Evidence: `task-3a-report.md:9-13` (headline), `:129-142` (per-flick table),
`:153-172` (ratio and the 0.250000 s result), `task-3a-analysis.log:19`, `:54`,
`:89`, `:124`, `task-3a-projection.tsv:1-13`.

### 9. The reference's own drag example jumped at release — found, and fixed before ship — **PASS (as a defect caught by the exercise)**
Recorded as its own item because it is the strongest argument in this phase for
running the exercise at all. The `@GestureState` formulation that survived two
review rounds **does not hand off continuously**: at release the composed offset
renders at the pre-drag committed position for one frame — 191–210 pt of
snap-back on a 210 pt drag, on **12 of 12 flicks in both directions** — and the
spring starts from there, with `initialVelocity` normalized against a distance
the animation no longer covers. Confirmed in screen-recorded pixels, not inferred
from logs; a single-`@State` + `lastOffset` control measured 0 of 12. Removing
`transaction.disablesAnimations` changed nothing, so `disablesAnimations` was kept
via `withTransaction` in `.onChanged` — only `@GestureState` is gone.

This overturned a controller ruling made during the Task 1 loop. The re-reviewer
had flagged the release frame as unsettled by the docs and the `.swiftinterface`
alike and recommended exactly this test; the ruling accepted the `@GestureState`
form on a reading instead. **The reading was wrong and the measurement was
right.** The reference now teaches the single-stored-value form and states why
(`fluid-interfaces.md:155-163`), and the spring-to-spring guarantee in section 1
is qualified so it no longer claims more than it can (`:26-29`).
Evidence: `task-3a-report.md:243-296`, `task-3a-trace-run4-verbatim.log:31-37`
(the falsifying frame: `committed` already at 400 while the rendered value is
0.0000), `task-3a-harness.log:168-175` (the clean control),
`task-3a-video-frames.log:1-91`.

### 10. Real exercise — **PARTIAL**
The spec asked for the full exercise: build the surface, implement both
projections, measure an identical flick under each, **and confirm the ratio on a
device rather than in arithmetic**. Half of that ran.

**Settled by Task 3a, in the Simulator.** The surface exists and was driven; both
projections were computed from the same release; the ratio is measured, not
derived — 1.996000 over 48 flicks with `predictedEndTranslation` at 0.250000 s
every time; and the exercise found a real defect in the shipped example (item 9)
that no amount of reading would have found. The ratio is linear in velocity, so
its arithmetic is provable at any velocity and does not need a real finger.

**Still owed by Task 3b, which needs a human.** Three things, none of which a
headless simulator run can substitute for:
1. **Flicks on a physical device** at representative velocities, to confirm the
   ratio survives real touch input rather than synthesized events.
2. **The feel judgment** — the spec's own words are "a gesture is felt, not
   read". Nobody has yet felt the difference between the two projections. The
   reference's central recommendation (use `project(initialVelocity:)` for
   anything that should feel like scrolling) is measured but not experienced.
   Task 3a flagged one item specifically for this attention: whether the Step A
   snap-back is visible to the eye.
3. **The Instruments SwiftUI-template run** that would close `docs/deferred.md`
   item 5 — see item 11.

Items 1 and 2 are tracked as `docs/deferred.md` item 10, added at this phase's
close with its own trigger; item 3 stays `docs/deferred.md` item 5. Item 10 carries
a third owed piece this list did not have: **confirm or refute the mid-flight-grab
limitation** that the final fix wave added to `fluid-interfaces.md:165-176` as a
labelled-unmeasured reading. It is a second reading of the same release boundary
that already defeated two readers before Task 3a measured it, so it is tracked
rather than left to stand — controller ruling, 2026-09-12.

**No verdict is written here for work nobody did.** Phase 6 shipped a PARTIAL on
the same honest basis (item 9 of its verification append) and that is the
precedent followed.
Evidence: `task-3a-report.md:1-20`, `:344-366` (including the item flagged for
3b), `task-3a-commands.log:15-21`, `progress.md:53-62` (the 3a/3b split ruling, taken
before Task 3 started rather than improvised when it stalled), `:198-231`.

### 11. Deferred item 5 — the SwiftUI instrument — **NOT ADDRESSED, and the item stays open**
This spec's opening-task section named Phase 7's real exercise as the occasion to
run the Instruments **SwiftUI** template with the scheme's Profile action set to
Debug, which is the untested explanation recorded against the item. **That run did
not happen.** Task 3a ran no Instruments session at all, deliberately: the
template's failure is a GUI-and-device symptom, and a headless simulator run can
neither reproduce nor refute it. Task 3b is outstanding.

`docs/deferred.md` item 5 therefore stays open with its trigger **unchanged** —
one run, Profile action set to Debug. It is not renewed on new grounds, extended,
or weakened by having been named in a phase spec and not reached. A note recording
exactly that was added to the item at this phase's close, so a later reader cannot
mistake "named in the Phase 7 spec" for "done in Phase 7".
Evidence: `docs/deferred.md:265-278`, `task-3a-commands.log:1-61`.

### 12. Trigger evals — **PARTIAL, 31/35 (17/20 should-fire, 14/15 should-NOT)**
Every criterion this spec set for `apple-animations` passed. The verdict is
PARTIAL rather than PASS because one of the four failures is a real, reproduced
routing defect between two Phase 6 skills, and this phase does not fix it — a
clean-sounding verdict would bury it.

35 prompts through `pipeline/run_evals.py`, so the fixture guard, the
`/dev/null` stdin and the `--max-turns 6` default all applied. `apple-animations`
is the skill this phase deepened, so its **full** set ran — 10 should-fire and 5
should-NOT, including the four prompts Task 4 added; every other shipped skill
contributed one should-fire and one should-NOT regression sample, the Phase 3–6
shape. **No skill description was changed in response to any result.**

Of the 15 should-NOT prompts, 14 passed, and **12 of those passes routed** to the
correct neighbour rather than merely staying silent — the stronger result and the
Phase 6 standard. The claim is scoped deliberately: `test-not` and `xcode-not` fired
**nothing at all** — zero `Skill` blocks in either transcript — and they did so
for the same fixture-mismatch reason diagnosed below, because the fixture holds
no "data race" and no "parser". Those two are silence, not demonstrated routing,
and counting them as routing would have inflated the result using the very
mechanism this item uses elsewhere to excuse failures. All five `anim-not-*`
prompts — the ones that test this phase's own boundary — did route.

The new discrimination test the spec implied is clean in both directions:
`anim-not-5` ("Why does my ScrollView stutter when I scroll fast?") routes to
`apple-performance`, and `perf-not` ("Make this card flip with a spring
animation") routes to `apple-animations`. The new reference does not pull
scroll-*performance* questions toward gesture *motion*.

**The four failures were diagnosed, not absorbed**, in two follow-up runs that do
not re-score the sweep:

- **Three are a corpus/fixture mismatch, not routing defects.** `anim-fire-8`
  ("this sheet"), `test-fire` ("this view model") and `xcode-fire` ("BreeziTip")
  each name code the bare-template fixture does not contain. All three
  **reproduce at `--max-turns 12`**, so turn exhaustion is excluded.

  **The mechanism is not "the session never reached the answering step".** That
  was the first reading, and `anim-fire-8` — the prompt this phase added for the
  new reference — contradicts it: in both runs it returned `success` (7 turns at
  the 6-cap, 8 at the 12-cap) and delivered three to four ranked hypotheses drawn
  from priors **without ever loading the skill**. `xcode-fire` at 12 turns also
  answered, in the wrong repository. Only `test-fire` matches the original
  description, ending "I'd need to know what it should do rather than invent
  behavior to test". The accurate mechanism is that **a missing referent shifts
  the session into answering blind from priors rather than into loading the
  skill** — a worse failure than turn exhaustion, because the output reads as a
  confident answer rather than as a session that gave up.

  All three **pass** when the same question is asked in how-to form:
  `diag-sheet` → `apple-animations`, `diag-test` → `swift-testing`, `diag-xcode`
  → `xcode-loop`, 3/3, same skills and settings. **None of the three is a clean
  single-variable control.** `diag-sheet` also introduces "drag-to-dismiss" and
  `diag-test` also introduces the literal skill name "Swift Testing", so those two
  move referent and vocabulary together. `diag-xcode` was written up here as
  swapping the referent alone, and **that was wrong** — corrected 2026-09-12 by
  diffing the two prompt files rather than re-reading the sentence. The sweep asks
  "Run the test suite for BreeziTip" (`task-4-evals/prompts.tsv:38`); the probe asks
  "Run the test suite for this project **and show me the failures**"
  (`task-4-evals-diagnostic/prompts.tsv:9`), appending a clause as well as swapping
  the referent. It is the closest of the three and still not clean, so the
  conclusion rests on the transcripts — `anim-fire-8` answering blind without ever
  loading the skill — and not on any probe; the probes are weaker evidence than a
  3/3 suggests. `anim-fire-8` stays in the corpus as written, because in a project
  that has a sheet the expectation is correct and deleting the prompt would hide
  the result.
- **One is a genuine boundary bleed.** `apple-intelligence` fires on
  "Why is my Foundation Models feature so slow?", which its own corpus assigns to
  `apple-performance`. Reproduced at 12 turns. Not caused by this phase, which
  changed neither skill. Left unfixed on purpose — one prompt is thin evidence for
  a description edit, and that edit is the Phase 6 failure mode. Recorded as
  `docs/deferred.md` item 9 with a three-prompt trigger for the next sweep.

**Against the spec's own criterion**, `apple-animations` fires on drag
(`anim-fire-10`), carousel-style snapping (`anim-fire-9`) and flick-to-dismiss,
and on sheets in how-to form (`diag-sheet`); the sheet *bug-report* form is the
one miss and is accounted for above. It stays silent on whether-to-animate
(`anim-not-1` → `apple-design`) and on build-and-run (`anim-not-3` →
`xcode-loop`), as required.

**The harness wrote to the fixture 8 times and the guard caught all 8**,
attributing each to its prompt, restoring the tree and exiting non-zero — the
behavior `docs/deferred.md` item 6 was closed with, working as designed rather
than a failed run. The sweep also found the *cause*: `--allowedTools "Skill Read"`
does not restrict tool use at all — `Bash` ran in essentially every session.

With `Bash` unrestricted, `xcode-fire` left the fixture and reached
`~/BreeziTip/Projects/breezitip_new`, an unrelated real project. **Two
corrections to the first write-up of this, both made in the same pass.** First,
the escape completed in the `--max-turns 12` rerun, not in the sweep: at 6 turns
it exhausted them on reconnaissance and executed nothing, and only at 12 did it
`cd` in, run `bun run db:migrate` and then `bun run test`. **The escape scales
with the turn budget** — raising the cap enlarges the blast radius, which is a
direct argument against loosening it to chase harness failures. Second, the
claim that "nothing was damaged" was **false**: writes landed at 18:30:06–18:30:18
— miniflare D1 state, `.svelte-kit/generated/*`, and regenerated sources inside
the source tree at `src/lib/paraglide/messages/*`. They are benign build
artifacts and local dev state with no remote writes, but the check that cleared
them was `git status`, and **every one of those paths is gitignored**, confirmed
with `git check-ignore`. An empty `git status` in a repo with a real `.gitignore`
is not evidence that nothing was written, and presenting it as a verified
afterwards-check was the error. Item 6 carries both corrections and a corpus-walk
trigger.
Evidence: `task-4-evals/results.tsv:1-36`, `task-4-evals/README.md:1-110`,
`task-4-evals-rerun/results.tsv:1-5`,
`task-4-evals-diagnostic/results.tsv:1-4`, `docs/deferred.md:321-404` (item 6
amendment, including the corpus swap and the clean-control correction), `:513-539`
(item 9). Line ranges re-derived 2026-09-12 after the same pass edited that file.

### 13. Consume test — **PASS**
Prompt pre-validated against the shipped file before it ran, per this spec's rule:
`fluid-interfaces.md:89-90` carries the exact symptom ("the flick that stops one
item early") and `:82-90` carries the decision the answer had to reach.
Run from the fixture with `--allowedTools "Skill Read"`, prompt: "I have a
drag-to-dismiss card. When I flick it, it lands short of where it feels like it
should go."

The session invoked `apple-studio:apple-animations`, read
`references/fluid-interfaces.md`, and **distinguished the two projections** — the
spec's expectation. It went further, and every addition is traceable to the file
rather than to model priors: the flat 0.25 s from the shipped interface, the
**1.996×** ratio in its corrected form, the `project(initialVelocity:)` function
verbatim, the signed-delta normalization for `interpolatingSpring` with the
explicit warning that `abs()` inverts it, and — unprompted — the release-boundary
finding from item 9 above, which is three days old and exists in no training data.
Evidence: `task-4-consume-test.log:1-44` (the `Skill` and `Read` tool_use blocks
and the final `result`), `task-4-consume-prevalidation.log:1-20`.

### 14. `claude plugin validate . --strict` and the version bump — **PASS**
Clean before and after the bump. Version moved 0.7.1 → 0.8.0 in
`plugin/.claude-plugin/plugin.json` only; `.claude-plugin/marketplace.json`
contains no `version` key at all, which was checked rather than assumed. Every
commit in this phase that touched `plugin/` ran validate: Task 1
(`task-1-validate.log:1-3`), Task 2 (`task-2-validate.log:1-3`), Task 4
(`task-4-validate.log:1-58`). Tasks 0 and 3a touched no `plugin/` file and ran it
anyway.

**The other half of this line is a human step and is not done.** Re-import into
Xcode after the merge is the standing operational rule from `docs/deferred.md`
item 3 — Xcode imports a *copy* of the plugin, so an installed Xcode still has
0.7.1 until someone re-imports. Recorded in the Task 4 report's hand-off list.
Evidence: `task-4-validate.log:1-20`, `docs/deferred.md:130-146`.

### 15. The `.swiftinterface` technique — **ADOPTED into CONVENTIONS.md, ranked third of four**
This spec left the decision open: the technique goes in "once this phase confirms
it generalises". It did, and it is now a named move at `CONVENTIONS.md:91-118`.

**Why it earned the place.** It answered a question neither other move could
reach. `predictedEndTranslation`'s documentation never states how far it
projects, so `docc.py` could only confirm the page exists; the question is about
behavior rather than existence, so `typecheck_snippets.py` could not reach it
either. The shipped interface carries the body of `DragGesture.Value.velocity`,
and inverting it gives the 0.25 s projection — Finding 1, the phase's central
claim. Re-read independently three times over the phase (implementer,
re-reviewer, and again at Task 4) at
`.../iPhoneOS27.0.sdk/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface`
lines 4629-4636 and 4672-4679, identical across both `$TildeSendable` branches.
The phase also used it a second, different way: an exhaustive negative search for
`rubber`, `resistance`, and `overscroll` is what establishes Finding 3, and
absence in a complete interface is evidence in a way absence from documentation
is not.

**Why it is ranked third and not simply "the strongest move we have".** The
honest framing is *third strongest, still below runtime measurement*, and this
phase earned that qualifier rather than assuming it:

- **Bodies are partial.** `velocity` ships one; `predictedEndLocation` ships
  `get` with nothing in it. The 0.25 s figure was therefore an inference from an
  identity until Task 3a put it at 0.250000 s on 48 of 48 flicks.
- **A reading that goes past the literal body can be flatly wrong.** This phase
  read the interface as implying that a `@GestureState` reset and a
  `withAnimation` on a separately committed offset hand off inside one graph
  update. The running framework disagreed on 12 of 12 flicks (item 9). The
  interface states what a body computes; it says nothing about when the view
  graph schedules it.

So the four moves rank in increasing strength — documented, exists in the shipped
SDK, computes this, does this at runtime — and where two disagree the later one
wins. The convention also carries the practical cautions the phase paid for: a
shipped body is an implementation detail rather than contract, re-read it per SDK
instead of trusting a remembered line number, and cite it in a `verified:` header
by SDK and architecture rather than as a machine-specific absolute path (a Task 1
review finding — the first draft shipped an `/Applications/Xcode-beta.app/...`
path to users).
Evidence: `CONVENTIONS.md:91-118`, `probe/FINDINGS.md:22-45` (Finding 1),
`plugin/skills/apple-animations/references/fluid-interfaces.md:1` (header),
`:57-63` (Finding 1 in the shipped file), `:184-186` (Finding 3).

### Open question from this spec, now decided
**A custom `ScrollTargetBehavior` example does not go in.** This spec left open
whether the new reference also needed a `SnapBehavior`-style example, or whether
it belonged nearer `swiftui-performance.md`. Decision, taken at Task 1 once
section 2 existed: keep a **one-sentence pointer** at the end of section 2
(`fluid-interfaces.md:96-97`) and ship no example. Without the sentence,
section 2's "hand-compute from `.velocity`" is silently wrong inside a
`ScrollView`, which is a correctness gap rather than scope creep; with a full
example the file would have grown a sixth topic it does not otherwise carry.
`ScrollTargetBehaviorContext.velocity` re-probed live and compiled clean, so the
pointer is verified even though nothing demonstrates it.
Evidence: `progress.md:100-104`, `task-1-reprobe.log:362-369` (the
`ScrollTargetBehaviorContext.velocity` probe).

### Carried forward
- **Task 3b is outstanding and is a human's** — device flicks, the feel judgment,
  and the Instruments SwiftUI-template run. Items 10 and 11 above are PARTIAL and
  NOT ADDRESSED respectively because of it. **All three now have a home in
  `docs/deferred.md`, which they did not at first**: the device flicks and the feel
  judgment are new item 10, with their own trigger; the Instruments run stays item
  5, whose trigger is unchanged and deliberately unrenewed. Until that was fixed at
  this phase's close, two thirds of the largest known-incomplete item existed only
  in this list and in the ledger, which is not where this repo keeps not-now work.
- **Verification item 6 of the charter (one real feature in a real project)
  remains PARTIAL**, and is still the binding precondition on the skill
  kill-switch gate. This is the second consecutive zero measurement. Every phase
  that ships without it raises the stakes of the eventual measurement.
- **19 untriaged snippet failures across 12 files**, all authored in Phases 1–5.
  `docs/deferred.md` item 7 triggers a single triage pass in the phase after this
  one.
- **The SDD tooling silently reverts the evidence `.gitignore`**, and did so at
  least three times in this phase, once costing Task 0's evidence its commit.
  Recorded as `docs/deferred.md` item 8 with a standing close-of-phase check,
  because it is a hazard for every future phase and not a Phase 7 incident.
- **Two eval findings, both deferred with triggers rather than patched.** The
  sweep corpus contains prompts that cannot run in a bare-template fixture, which
  produce a FAIL indistinguishable from a skill miss (`docs/deferred.md` item 6,
  amended); and `apple-intelligence` takes a Foundation Models *performance*
  question its own corpus assigns to `apple-performance` (item 9). Neither was
  answered by editing a skill description, which is the Phase 6 failure mode.
- **`--allowedTools` is not an allow-list.** `Bash` ran in essentially every eval
  session despite `--allowedTools "Skill Read"`. The fixture guard contains the
  damage inside StudioFixture; it cannot contain a session that walks out of it,
  and one did. Anyone extending the harness should read `docs/deferred.md`
  item 6's amendment before adding prompts.
- **Classical ML is Phase 8.** The charter says so as of this phase; the Phase 6
  withdrawal of the "old and stable" rationale stands.
- **Three of this phase's own written claims were false and were corrected in
  place, not edited away**: the `isPressed` zero-hit row (item 6), the 2.00×
  ratio (item 8), and the controller's acceptance of the `@GestureState` drag
  example (item 9). Each was caught by an implementer or a reviewer refusing to
  take a written claim on trust, and each correction sits beside the original.
