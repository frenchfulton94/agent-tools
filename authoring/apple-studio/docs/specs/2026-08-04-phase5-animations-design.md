# apple-studio Phase 5: Animations & motion — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`, "Phase 4 — Long tail",
second slice). Decisions taken 2026-08-04 in brainstorming; this doc is the
input to the Phase 5 implementation plan.

## Goal

Ship the animations slice: one new skill, `apple-animations`, covering
modern SwiftUI animation implementation mechanics — fundamentals, keyframe
and phase animators, transitions and matched geometry, scroll and visual
effects — built to charter quality. Version bump to 0.6.0.

Phase 5 direction chosen from the charter's unscheduled long-tail list:
animations, chosen over a real-world consume phase, a Combine/async-interop
skill, and a live-docs ML skill.

**Shape decision (differs from Phases 1–4):** the iOS Animations book's
durable judgment was already fully harvested in Phase 2 into
`apple-design/references/animation-taste.md`; the Phase 2 map explicitly
SKIPped the book's remainder as dated UIKit/CALayer mechanics with no
transferable judgment. There is no books map this phase.
`apple-animations` is therefore **live-docs-sourced implementation
mechanics**, with `animation-taste.md` staying in `apple-design` as the
judgment layer, cross-referenced both ways — mirroring the HIG-only scope
split (design owns when/why/how much motion; animations owns how).

## Deliverables

**New skill `plugin/skills/apple-animations/`** — lean SKILL.md (triggers,
routing, implementation judgment) + `evals/triggers.md` + four references:

1. `animation-fundamentals.md` — `withAnimation`/`.animation`, the
   `Animatable` protocol, the modern spring API, timing curves,
   `Transaction`, `contentTransition`.
2. `keyframe-and-phase-animators.md` — `PhaseAnimator`, `KeyframeAnimator`,
   `TimelineView`; when each fits (multi-step vs keyframed vs time-driven).
3. `transitions-and-matched-geometry.md` — the transition API,
   `matchedGeometryEffect`, zoom/navigation transitions.
4. `scroll-and-visual-effects.md` — `scrollTransition`, `visualEffect`,
   and the shader effects (`colorEffect`/`layerEffect`/`distortionEffect`).

**Routing discipline (cross-refs, no duplication):** `apple-design` keeps
motion judgment (`animation-taste.md` stays where it is; both SKILL.md
files gain a cross-reference); reduce-motion/accessibility stays in
`apple-design/references/accessibility.md` and is cross-referenced, not
duplicated. `apple-frameworks` primers keep API-catalog duty.

**No new agent this phase** (agent gate: two consecutive zero
measurements; see opening task).

## Sources and pipeline

**No book conversion** — first phase with no books map. One map:
`pipeline/maps/apple-animations-live.md` (live-doc endpoints → target
reference), written as a **seed list** under the convention codified this
phase (see opening task): the map is a dispatch-time seed, not an
exhaustive registry; distillers may follow narrower pages under enumerated
parents when pre-verified live, and reference headers remain the citation
record.

**Staleness stance:** everything is API-specific and distilled from live
SwiftUI DocC pages, cited per the live-docs-first rule. Mandatory here:
Xcode 27 / macOS 27 are post-training-data, so no animation API claim
ships un-probed.

**Endpoint probing (binding):** every live endpoint assumed by the map is
probed (actually fetched) during planning before any distillation task is
written against it. Expected-but-missing pages are recorded in the map
with `MISSING:`.

## Opening task: Phase 4 sweep + kill-switch decision

Task 0 of the plan, in this order (the kill-switch outcome changes the
plugin surface, so it goes first):

1. **Kill-switch measurement — the grace trigger fires.** Re-run the
   Phase 3 Task 0 structural scan (JSON-parse `Agent`/`Task` tool_use
   blocks for `input.subagent_type` containing "reviewer" across
   `~/.claude/projects` transcripts; exclude scratchpad/fixture-harness
   sessions and `brand-studio`'s same-named `design-reviewer`), scoped to
   sessions since the 2026-08-04 measurement. **Decision (taken in
   brainstorming): on another zero genuine non-fixture invocation, cut
   both agent definitions (`swift-reviewer`, `design-reviewer`) and keep
   all skills/references.** Record measurement + decision in
   `docs/deferred.md` with a restore pointer (both agents recoverable from
   the v0.5.0 tag; restore trigger: the first real workflow that needs
   one), and note the changed Xcode import surface (the "2 subagent
   definitions" line disappears from the import dialog —
   `docs/deferred.md` item 3 updated accordingly). If a genuine invocation
   has occurred, record it and keep both agents, closing the grace item.
2. **`mac-app-structure.md:128`** — remove the dangling "(both snippets
   below)" self-reference (Phase 4 final-review minor).
3. **CONVENTIONS.md** — codify "map = seed list, not exhaustive registry"
   (Phase 4 Task 3 controller ruling): distillers may follow narrower
   pages under enumerated parents when pre-verified 200; reference headers
   are the citation record.
4. **Back-references** — add the optional apple-design/xcode-loop →
   apple-macos cross-references flagged in the Phase 4 final review.
5. **Manual items (Michael, classifier-blocked or Xcode-side):** Xcode
   re-import of 0.5.0 (pending); delete stale `phase-3`/`phase-4` branches
   local+remote (content preserved in squashes + tags). Listed for
   hand-off, not automated.

## Verification (free-tier, definition of done)

- Trigger evals for `apple-animations`: fires on animation-implementation
  requests (springs, keyframes, transitions, matched geometry, scroll
  effects, shaders); silent on motion-judgment/look-and-feel prompts
  (`apple-design`), architecture, and build/run prompts. One should-fire +
  one should-NOT regression sample per prior skill, as in Phases 3–4.
  Eval-harness caveats carried forward: `--allowedTools "Skill Read"`,
  fixture cwd where needed, avoid "build X" phrasing (superpowers
  preemption, documented in Phase 3 verification results).
- Consume tests with captured logs; every consume-test prompt validated
  against actual reference coverage before it enters the plan. Evidence
  pointers as `<file>:<line-range>`.
- Real exercise where free: StudioFixture — insert two documented surfaces
  verbatim (e.g., a `PhaseAnimator` sequence and a `matchedGeometryEffect`
  pairing exactly as the references document them), build headless, run
  and capture screenshot/recording evidence where the surface is visible,
  then revert (Phase 3 Task-7 pattern: documented code executed as
  written, failures indict the docs). Animation motion itself is
  time-based; evidence standard is build-success plus a visible end-state
  screenshot, not frame-by-frame capture.
- `claude plugin validate . --strict` passes at every commit touching
  `plugin/`; version bump to 0.6.0 in the final task only; re-import into
  Xcode after merge (operational rule, `docs/deferred.md` item 3).

## Out of scope

- Motion judgment — when/why/how much to animate (`apple-design`'s
  `animation-taste.md` owns it; cross-referenced).
- Reduce-motion/accessibility policy (`apple-design`'s `accessibility.md`
  owns it; cross-referenced).
- UIKit/Core Animation mechanics (`CALayer`, `UIViewPropertyAnimator`,
  VC transitions) — judged non-durable in the Phase 2 map SKIP record;
  legacy-only context per the modern-only baseline.
- Metal shader authoring depth (the shader *effect modifiers* are in
  scope; writing nontrivial MSL is not).
- The rest of the long-tail list (ML, Combine interop, Advanced Git,
  Flight School guides) — each waits for its own demand.

## Phase 5 verification results (2026-08-05)

**Kill-switch measurement + action.** Re-ran the Phase 3 Task 0 structural-scan
method at the Phase 5 opening per the Phase 4 grace decision's trigger
("the kill-switch rule fires for real at the Phase 5 opening measurement
unless a genuine non-fixture invocation has occurred by then," recorded in
`docs/deferred.md`). Result: 7 hits, all either out-of-scope
(`brand-studio:design-reviewer`, unrelated plugin) or the same 4 known
fixture sessions already recorded from Phase 3/4 — **zero new genuine
invocations**, the second consecutive zero measurement. Kill-switch fired:
`plugin/agents/swift-reviewer.md` and `plugin/agents/design-reviewer.md`
deleted (`git rm`), all skills/references kept untouched, restore pointer to
the `v0.5.0` tag recorded in `docs/deferred.md` item 1. Raw scan + full
triage: `task-0-killswitch.log`; narrative: `task-0-report.md`. Commit
`2056b4a`.

**Phase 4 sweep items.** `mac-app-structure.md:128` dangling
"(both snippets below)" self-reference reworded; `CONVENTIONS.md` "Distillation
maps" section added codifying "map = seed list, not exhaustive registry";
back-references added at `plugin/skills/apple-design/SKILL.md` and
`plugin/skills/xcode-loop/SKILL.md` pointing to `apple-macos`. Two
brief-list-external dangling references to the deleted agents were also
found and fixed as a disclosed deviation
(`plugin/skills/apple-design/SKILL.md:27`,
`plugin/skills/xcode-loop/evals/triggers.md:10`). Commit `2056b4a`.

**Live map, zero MISSING.** `pipeline/maps/apple-animations-live.md` (180
lines): 26 seed endpoints re-curled 2026-08-05, all 200 (no drift since the
2026-08-04 planning probe); one index (`swiftui/animations`) enumerated,
walking all 13 `topicSections`, 55 children individually curled (all 200),
53 added to the map across the four reference files, 2 deliberately excluded
(a deprecated type already superseded, and a watchOS-only tutorial —
reasoning recorded inline in the map). Zero `MISSING:` entries. No books map
this phase — the iOS Animations book's durable judgment was already fully
harvested into `apple-design/references/animation-taste.md` in Phase 2; the
map's preamble states this and cross-references it both ways. Commit
`fe98cb2`.

**Four references, verified headers.** Each carries a
`> verified: ... \n> sources: ...` header at lines 1-2:
`plugin/skills/apple-animations/references/animation-fundamentals.md` (166
lines), `keyframe-and-phase-animators.md` (103 lines),
`transitions-and-matched-geometry.md` (194 lines),
`scroll-and-visual-effects.md` (112 lines) — all within the 100–250 line
target band. 12 `[VERIFY:]` flags across all four files were resolved
independently against live DocC JSON (not trusted from the distillers'
claims); `grep -rn "VERIFY" plugin/skills/apple-animations/` returns no
matches post-resolution. Two of the twelve resolutions were genuine
corrections rather than confirmations: `CrossFadeNavigationTransition` is
Mac Catalyst-only, not native macOS as originally drafted
(`transitions-and-matched-geometry.md`), and `ScrollTransitionPhase.value`'s
exact signed domain (-1.0/0/1.0) was pinned down from the property's own
declaration page rather than left as a vague "purpose only" placeholder
(`scroll-and-visual-effects.md`). Sibling-consistency greps (taste
vocabulary, reduce-motion terms, build/run commands) confirmed no judgment
or policy restatement — one path-consistency fix applied
(`scroll-and-visual-effects.md`'s accessibility cross-ref corrected to the
full `apple-design/references/accessibility.md` path). Commits `a3039af`
(fundamentals + keyframe/phase), `7eac58f` (transitions/matched-geometry +
scroll/visual-effects).

**Hard-deliverable snippets, `swiftc -typecheck` evidence.** Both minimal
compiling snippets required by the spec were independently re-verified by
extracting them programmatically from the final committed files (not
trusted from the distillers' own copies): the `PhaseAnimator` "minimal
compiling example" (`keyframe-and-phase-animators.md`) and the
`matchedGeometryEffect` "Minimal Correct Pairing Pattern"
(`transitions-and-matched-geometry.md`). Both typechecked clean —
`swiftc -typecheck -parse-as-library -sdk <macosx SDK> -target
arm64-apple-macos14`, empty output, exit code 0 — on Xcode 27.0 (beta),
Apple Swift 6.4.

**Skill consume-test.** `plugin/skills/apple-animations/SKILL.md:1-32`
(frontmatter + routing), `plugin/skills/apple-animations/evals/triggers.md:1-14`
(7 should-fire / 4 should-NOT). Consume-test log
`task-4-consume-test.log` (37 JSONL lines), run from `~/Projects/StudioFixture`
cwd: skill invocation at line 13 (`apple-studio:apple-animations`), reference
`transitions-and-matched-geometry.md` read in full at line 20, final answer
at lines 36-37 visibly applies the reference's `isSource` single-source
invariant, the "defaults to `true`" gotcha, and the namespace-threading
discipline to diagnose a matched-geometry jump bug. No retries needed —
correct skill and correct reference on the first attempt. Fixture tree
verified clean before and after
(`git -C ~/Projects/StudioFixture status --porcelain` empty both times).
Commit `fd4d329`.

**Free-tier exercise, both screenshots.** `task-5-macbuild.log` (baseline mac
build, `** BUILD SUCCEEDED **` on the unmodified fixture); `task-5-rebuild.log`
(both snippets — the `PhaseAnimator` pulse view and the `matchedGeometryEffect`
pairing — inserted verbatim into `StudioFixture/ContentView.swift`, only the
containing struct names renamed to carry a "StudioFixture Phase 5" label,
rebuilt, `** BUILD SUCCEEDED **` on the first attempt, no reference defect);
`task-5-phase.png` (pre-toggle: pulsing circle, collapsed matched-geometry
card, "Expand" button) and `task-5-matched.png` (post-toggle: expanded card,
"Collapse" button) confirm both surfaces live and correctly resolved. Fixture
reverted clean (`git -C ~/Projects/StudioFixture status --porcelain` empty
before and after; no commits). Honest caveat, carried verbatim from the Task
5 report: "this machine had a live human user actively working on it during
the exercise... This made simple coordinate-based `osascript`/System Events
clicks against the fixture unreliable — not because of an automation-
permission block, but because of a genuine focus/Space race against real
concurrent activity." Per the brief's explicit fallback for this scenario,
an `.onAppear`-delayed toggle (reusing the identical
`withAnimation(.spring()) { isExpanded.toggle() }` expression already in the
`Button`'s own action) replaced the flaky coordinate click — no snippet
animation code was modified to make this adaptation. No corrections were
folded back into `plugin/skills/apple-animations`; the animation surfaces
compiled and ran exactly as documented.

**Eval table (27/27 pass after diagnosis, zero description changes).** All 7
`apple-animations` should-fire and all 4 should-NOT prompts, plus a 1-fire/1-
should-NOT regression sample for each of the 8 prior skills
(`apple-design`, `apple-frameworks`, `apple-macos`, `app-release`,
`swift-architecture`, `swift-concurrency`, `swift-testing`, `xcode-loop`) —
prompts reused from the Phase 4 eval table (rows 1, 8, 12-25), each already
carrying its own fire/silent label from that table. `apple-design`'s own
fire prompt used the Phase 3 substitution ("Does this screen feel native?"),
run from `~/Projects/StudioFixture` cwd, per precedent. Method:
`claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2
--output-format stream-json --verbose --allowedTools "Skill Read"`, one log
per prompt (`task-6-eval-<skill>-<fire|nofire>-<n>.log`, 27 primary logs +
4 diagnostic retries), verdict by grep for
`"name":"Skill","input":{"skill":"apple-studio:<skill>"`.

| # | Prompt | cwd | Expected | Invoked | Verdict |
|---|---|---|---|---|---|
| 1 | My spring animation feels too bouncy - how do I tune the damping? | repo | apple-animations fires | apple-animations | PASS |
| 2 | Animate this heart icon through three pulsing phases in a loop | repo | apple-animations fires | apple-animations | PASS |
| 3 | How do I keyframe a bounce where scale and offset move on different timing? | repo | apple-animations fires | apple-animations | PASS |
| 4 | This view's transition jumps instead of animating when it appears | repo | apple-animations fires | apple-animations | PASS |
| 5 | Expand the tapped thumbnail into the detail card with a hero animation | repo | apple-animations fires | apple-animations | PASS |
| 6 | Fade and scale list rows as they scroll off the top of the screen | repo | apple-animations fires | apple-animations | PASS |
| 7 | Add a ripple distortion to this view when tapped - shader effect? | repo | apple-animations fires | apple-animations | PASS |
| 8 | Is this screen using too much animation? Does it feel Apple-like? | repo | apple-animations silent (apple-design) | apple-design | PASS |
| 9 | Fix this Sendable warning | repo | apple-animations silent (swift-concurrency) | swift-concurrency | PASS |
| 10 | Run the mac target and screenshot it | repo | apple-animations silent (xcode-loop) | xcode-loop | PASS |
| 11 | Where should this view's state live? | repo | apple-animations silent (swift-architecture) | swift-architecture | PASS |
| 12 | Does this screen feel native? | StudioFixture | apple-design fires | apple-design | PASS |
| 13 | Fix this Sendable warning | repo | apple-design silent (swift-concurrency) | swift-concurrency | PASS |
| 14 | Does Apple have a native way to show tips/onboarding hints? | repo | apple-frameworks fires | apple-frameworks | PASS |
| 15 | Fix this Sendable error | repo | apple-frameworks silent (swift-concurrency) | swift-concurrency | PASS |
| 16 | Add a Settings window with Cmd-comma to my Mac app | repo | apple-macos fires | apple-macos | PASS |
| 17 | Does this Mac window layout feel native? | repo → StudioFixture (retry) | apple-macos silent (apple-design) | inconclusive (confound) → apple-design | PASS* |
| 18 | Set up TestFlight so external testers can try the beta | repo | app-release fires | app-release | PASS |
| 19 | Build and run the app on the simulator | repo | app-release silent (xcode-loop) | xcode-loop | PASS |
| 20 | Where should this view's state live? | repo | swift-architecture fires | swift-architecture | PASS |
| 21 | Fix this Sendable warning | repo | swift-architecture silent (swift-concurrency) | swift-concurrency | PASS |
| 22 | Fix this 'capture of non-Sendable type' error | repo | swift-concurrency fires | swift-concurrency | PASS |
| 23 | Where should this state live? | repo | swift-concurrency silent (swift-architecture) | swift-architecture | PASS |
| 24 | Write tests for this view model | repo → StudioFixture (retry) | swift-testing fires | inconclusive (confound) → swift-testing | PASS* |
| 25 | Run the test suite | repo (×2) → StudioFixture (retry2) | swift-testing silent (xcode-loop) | inconclusive (confound, ×2) → xcode-loop | PASS* |
| 26 | Build the app and make sure it compiles | repo | xcode-loop fires | xcode-loop | PASS |
| 27 | Explain actor isolation in Swift 6 | repo | xcode-loop silent (swift-concurrency) | swift-concurrency | PASS |

27/27 PASS after diagnosis (24/27 clean on the first attempt from repo cwd;
3/27 — rows 17, 24, 25, marked PASS* — required one diagnostic re-run each).
**No skill description was tightened anywhere** — every miss diagnosed as a
harness confound, not a routing defect, and none involved the wrong skill
firing. `error_max_turns` exits (the 2-turn cap) occurred on all 27 final
runs, expected per the brief; no `"name":"Agent"` tool invocation appears in
any of the 31 logs (27 primary + 4 diagnostic), confirming the Task 0
agent cut holds under `--allowedTools "Skill Read"` — `swift-reviewer` and
`design-reviewer` are absent from the plugin surface and were never reached
for or referenced.

**Misfire diagnosis (rows 17, 24, 25).** All three initial attempts ran from
the repo root (`~/Projects/apple-studio`) and burned their full 2-turn budget
on Bash tool calls (mostly rejected — Bash is outside `--allowedTools "Skill
Read"`) trying to locate the prompt's implicit referent ("this Mac window
layout," "this view model," "the test suite") before ever calling the Skill
tool — `error_max_turns` fired with zero Skill invocation logged. This is the
same confound family as the Phase 3/4-documented "avoid 'build X' phrasing"
rule (superpowers process-skill preemption pushing the model toward direct
action/exploration instead of skill-first routing), generalized here: the
apple-studio repo itself is a skills/docs-authoring project, not a runnable
app, so any prompt implying a concrete app artifact ("this screen," "this
view model," "the test suite") that isn't actually present in this cwd risks
the same turn-budget exhaustion. Diagnosis confirmed by remedy, not
assertion: re-running the identical, unmodified prompt from
`~/Projects/StudioFixture` (a real, buildable, testable app) resolved all
three on the first retry (row 25 needed a same-cwd retry first, to rule out
plain non-determinism, before the cwd-substitution retry) — the correct
skill fired every time once given a cwd where its implicit referent actually
exists. This is the established Phase 3/4 fixture-cwd precedent (previously
applied only to `apple-design`'s own fire prompt), generalized here to any
regression prompt that hits the same confound. Since the fault traces to
harness/cwd context, not to any skill's `description` frontmatter, **no
description was tightened** — the brief's misfire protocol reserves that
remedy for genuine routing misses (the wrong skill firing), which did not
occur here. Diagnostic logs: `task-6-eval-apple-macos-nofire-1.log` (initial,
inconclusive) + `task-6-eval-apple-macos-nofire-1-retry.log` (fixture cwd,
apple-design fires); `task-6-eval-swift-testing-fire-1.log` +
`-retry.log`; `task-6-eval-swift-testing-nofire-1.log` +
`-retry.log` + `-retry2.log`.

**Strict validation.** `claude plugin validate . --strict` → "✔ Validation
passed", zero warnings, captured to `task-6-validate.log`. This run reflects
the Task 0 agent cut — no `plugin/agents/` directory exists on this branch,
confirmed absent both by `ls` and by the zero `"name":"Agent"` finding across
all 31 eval logs above.
