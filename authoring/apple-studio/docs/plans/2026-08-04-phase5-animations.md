# apple-studio Phase 5: Animations & Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the Phase 4 opening sweep (kill-switch measurement with the cut decision pre-taken, mac-app-structure one-liner, seed-list convention, back-references), then ship the animations slice: an `apple-animations` skill with four live-docs-sourced references covering modern SwiftUI animation implementation. Version bump to 0.6.0.

**Architecture:** Same two-layer pattern as Phases 1–4 with one structural difference: **no books map** — the iOS Animations book's durable judgment already lives in `apple-design/references/animation-taste.md` (Phase 2), and the Phase 2 map SKIPped the book's remainder as non-durable UIKit mechanics. `apple-animations` owns *how* (implementation mechanics, live-docs-sourced); `apple-design` keeps *when/why/how much* (`animation-taste.md`, cross-referenced both ways). Spec: `docs/specs/2026-08-04-phase5-animations-design.md`.

**Tech Stack:** Claude Code plugin components, existing `pipeline/` (distill-prompt.md adapted; no convert.sh run this phase), DocC JSON endpoints (probed 2026-08-04 — **all 26 seeded endpoints returned 200, zero MISSING**; see Task 1), `xcodebuild -destination 'platform=macOS'`, `screencapture`, `osascript`.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-5` (create from `main` at start). All paths relative to repo root unless absolute.
- Toolchain: Xcode 27.0 beta active; fixture app `~/Projects/StudioFixture` (Multiplatform, scheme `StudioFixture`; leave its git tree clean after any test).
- Spec boundary (verbatim): `apple-animations` is "live-docs-sourced implementation mechanics"; motion judgment stays in `apple-design`'s `animation-taste.md`; reduce-motion/accessibility stays in `apple-design`'s `accessibility.md` (cross-referenced, not duplicated); "the shader *effect modifiers* are in scope; writing nontrivial MSL is not"; UIKit/Core Animation mechanics out of scope. **No new agent this phase.**
- Live-docs-first, mandatory here: Xcode 27 / macOS 27 are post-training-data — **no animation API claim ships un-probed**. Fetch via DocC JSON endpoints `https://developer.apple.com/tutorials/data/documentation/<path>.json`; cite canonical human URLs in reference headers.
- **Map = seed list (new convention, codified in Task 0):** the live map is a dispatch-time seed, not an exhaustive registry; distillers may follow narrower pages under enumerated parents when the fetch returns 200; reference headers remain the citation record.
- Reference files: CONVENTIONS.md header block, decision-grade only, ~100–250 lines, no copied doc prose (own words; short attributed quotes with quotation marks OK), no remaining `[VERIFY` markers at commit.
- Evidence standard (standing): every consume-test/verification claim is backed by a captured log under `.superpowers/sdd/2026-08-04-phase5-animations/`, with quoted lines in the report; verification tables use `file:line-range` evidence pointers.
- **Implementer-brief template text (copy VERBATIM into every subagent brief that runs nested sessions):** "Run nested `claude` sessions synchronously in the foreground and wait for completion — never background-and-wait. When the nested session must write files, use `--permission-mode auto`."
- Consume-test prompts: before running any consume-test, re-validate the prompt's topic against the ACTUAL shipped reference content (grep the reference for the topic); if coverage is missing, adjust the prompt to a covered topic and record the adjustment in the task report. From-scratch prompts get a fixture cwd and `--max-turns` ≥ 25.
- **Eval-harness rules (Phase 3 lessons, binding):** headless eval/consume commands include `--allowedTools "Skill Read"`; eval prompts avoid "build X" phrasing (superpowers brainstorming preemption, documented in the Phase 3 verification results); from-scratch prompts run from a fixture cwd, not the plugin repo.
- Commit after every task minimum. Version bump to 0.6.0 only in Task 6.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Branch + kill-switch measurement/decision + Phase 4 sweep

**Files:**
- Delete (conditional on measurement): `plugin/agents/swift-reviewer.md`, `plugin/agents/design-reviewer.md`
- Modify: `docs/deferred.md` (measurement + decision appended to item 1; item 3 Xcode-import note updated if agents cut)
- Modify: `plugin/skills/apple-macos/references/mac-app-structure.md` (~line 128)
- Modify: `CONVENTIONS.md` (seed-list rule)
- Modify: `plugin/skills/apple-design/SKILL.md`, `plugin/skills/xcode-loop/SKILL.md` (one-line back-refs to apple-macos)

**Interfaces:**
- Consumes: `docs/deferred.md` item 1 (the Phase 3 measurement method + the 4 known fixture-only invocations and their session IDs; the Phase 4 grace decision with its trigger); the Phase 4 ledger (`.superpowers/sdd/2026-08-04-phase4-macos/progress.md`).
- Produces: the measured kill-switch outcome Task 6's spec-append cites; a plugin surface that every later `validate --strict` run sees; the seed-list convention Task 1's map is written under.

- [ ] **Step 1: Create the branch**

```bash
cd ~/Projects/apple-studio && git checkout -b phase-5
```

- [ ] **Step 2: Re-run the kill-switch measurement** (the grace trigger fires — this goes first because its outcome changes the plugin surface). Method is the Phase 3 Task 0 structural scan, recorded in `docs/deferred.md` item 1:

```bash
grep -rlE 'swift-reviewer|design-reviewer' ~/.claude/projects --include='*.jsonl' > /tmp/ks-candidates.txt
python3 - <<'EOF'
import json, sys
hits = []
for path in open('/tmp/ks-candidates.txt'):
    path = path.strip()
    if '-scratchpad-' in path or '-private-tmp-' in path:
        continue  # fixture-harness/scratchpad sessions, excluded per the recorded method
    for line in open(path, errors='replace'):
        if '"subagent_type"' not in line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        def walk(o):
            if isinstance(o, dict):
                if o.get('type') == 'tool_use' and o.get('name') in ('Agent', 'Task'):
                    st = (o.get('input') or {}).get('subagent_type', '')
                    if 'reviewer' in st:
                        hits.append((path, st))
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(obj)
for h in sorted(set(hits)):
    print(h)
EOF
```

Triage every hit: discard `brand-studio` invocations (same-named unrelated agent — out of scope per the recorded method); discard the 4 known fixture runs already recorded in `docs/deferred.md` item 1 (sessions `7144207a…`, `3ef371c5…`, `e1f504a9…`, `dd71bab2…`). For any NEW hit, open the transcript and check the invoking user message: fixture/verification runs (StudioFixture, `pipeline/fixtures/flawed/`) do not count as genuine.

- [ ] **Step 3: Act on the measurement.**
  - **If zero new genuine non-fixture invocations (expected):** delete both agent definitions — `git rm plugin/agents/swift-reviewer.md plugin/agents/design-reviewer.md`. Keep every skill and reference. Append to `docs/deferred.md` item 1:

> **Phase 5 decision (2026-08-04): kill-switch fired — agents cut.** Re-measurement found <N> hits, all fixture/out-of-scope (evidence: `.superpowers/sdd/2026-08-04-phase5-animations/task-0-killswitch.log`). Two consecutive zero measurements; the Phase 4 grace trigger fired as written. Both agent definitions deleted; all skills/references kept. **Restore pointer: both agents recoverable from the v0.5.0 tag (`git show v0.5.0:plugin/agents/<name>.md`). Restore trigger: the first real workflow that needs one.**

  Also update `docs/deferred.md` item 3 (Xcode plug-in surface): note that the import dialog's "2 subagent definitions" line will disappear at the next re-import.
  - **If a genuine invocation exists:** keep both agents, record the invocation (session, project, prompt) in `docs/deferred.md` item 1, and close the grace item as satisfied.
  - Either way: save the scan output to `.superpowers/sdd/2026-08-04-phase5-animations/task-0-killswitch.log`.

- [ ] **Step 4: Fix the mac-app-structure self-reference.** `grep -n "both snippets below" plugin/skills/apple-macos/references/mac-app-structure.md` (Phase 4 final review located it at line 128). The parenthetical "(verified by compiling both snippets below with `swiftc -typecheck -parse-as-library`)" dangles — the file does not carry both snippet variants below that line. Reword to drop the positional claim, e.g. "(both forms verified with `swiftc -typecheck -parse-as-library`)".

- [ ] **Step 5: Codify the seed-list convention.** In `CONVENTIONS.md`, find the maps/pipeline section (`grep -n -i "map" CONVENTIONS.md`) and add:

> **Maps are seed lists, not exhaustive registries.** A distillation map enumerates the dispatch-time starting points. Distillers may follow narrower pages under an enumerated parent when the fetch actually succeeds (DocC JSON 200) — the reference file's header citations, not the map, are the citation record. Expected-but-missing pages are still recorded in the map as `MISSING:`. (Codified Phase 5 from the Phase 4 Task 3 controller ruling.)

- [ ] **Step 6: Add the back-references** flagged in the Phase 4 final review: in `plugin/skills/apple-design/SKILL.md`, one line in the scope/routing text pointing Mac *structure/mechanics* questions to `apple-macos`; in `plugin/skills/xcode-loop/SKILL.md`, one line noting mac-target destinations are covered by `apple-macos` (`grep -n "macOS" plugin/skills/xcode-loop/SKILL.md` first to place it without duplication). Keep both to a single sentence — routing, not content.

- [ ] **Step 7: Record the manual hand-off items** in the task report (NOT automated — classifier-blocked or Xcode-side, Michael runs them): (a) Xcode re-import of 0.5.0 still pending, and this phase will supersede it with 0.6.0 — one re-import after the Phase 5 merge covers both; (b) delete stale `phase-3`/`phase-4` branches local+remote (content preserved in squash merges + tags v0.4.0/v0.5.0).

- [ ] **Step 8: Validate + commit**

```bash
claude plugin validate . --strict
git add -A && git commit -m "chore: Phase 4 sweep + kill-switch fired (agents cut, skills kept)"
```

---

### Task 1: Build the live distillation map

**Files:**
- Create: `pipeline/maps/apple-animations-live.md`

**Interfaces:**
- Consumes: the endpoints pre-probed during planning (2026-08-04; **all 26 below returned 200**, zero MISSING); the seed-list convention codified in Task 0.
- Produces: the map Tasks 2–3 dispatch from. Format: `## <reference file>` sections listing `- <canonical human URL> → <DocC JSON endpoint>`; index endpoints marked `(index — enumerate)`.

- [ ] **Step 1: Write `pipeline/maps/apple-animations-live.md`.** Open with a two-line preamble: first phase with no books map (judgment already in `apple-design/animation-taste.md` per the Phase 2 map; remainder SKIPped as non-durable) and a note that this map is a **seed list** per the CONVENTIONS.md rule. Seed sections (DocC JSON prefix `https://developer.apple.com/tutorials/data/documentation/`):
  - → `animation-fundamentals.md`: `swiftui/animations` (index — enumerate), `swiftui/animation`, `swiftui/withanimation(_:_:)`, `swiftui/view/animation(_:value:)`, `swiftui/animatable`, `swiftui/spring`, `swiftui/transaction`, `swiftui/contenttransition`.
  - → `keyframe-and-phase-animators.md`: `swiftui/phaseanimator`, `swiftui/keyframeanimator`, `swiftui/keyframetrack`, `swiftui/timelineview`.
  - → `transitions-and-matched-geometry.md`: `swiftui/anytransition`, `swiftui/transition`, `swiftui/view/matchedgeometryeffect(id:in:properties:anchor:issource:)`, `swiftui/navigationtransition`, `swiftui/view/navigationtransition(_:)`, `swiftui/view/matchedtransitionsource(id:in:)`.
  - → `scroll-and-visual-effects.md`: `swiftui/view/scrolltransition(_:axis:transition:)`, `swiftui/scrolltransitionconfiguration`, `swiftui/view/visualeffect(_:)`, `swiftui/view/coloreffect(_:isenabled:)`, `swiftui/view/layereffect(_:maxsampleoffset:isenabled:)`, `swiftui/view/distortioneffect(_:maxsampleoffset:isenabled:)`, `swiftui/shader`, `swiftui/shaderlibrary`.
  - Fetch each index endpoint (`swiftui/animations` is the main one), enumerate its child topics, and add relevant children under the owning reference. Every added endpoint must have returned JSON when actually fetched — no invented endpoints; record expected-but-missing pages as `MISSING:`.
  - Add a cross-map note: judgment ranges for animation live in `pipeline/maps/apple-design-books.md` (the Phase 2 `animation-taste.md` entries) — distillers read `animation-taste.md` itself for tone/boundary, never re-distill the book.

- [ ] **Step 2: Commit**

```bash
git add pipeline/maps && git commit -m "feat: Phase 5 live distillation map (apple-animations, seed list)"
```

---

### Task 2: Distill `animation-fundamentals.md` + `keyframe-and-phase-animators.md`

**Files:**
- Create: `plugin/skills/apple-animations/references/animation-fundamentals.md`
- Create: `plugin/skills/apple-animations/references/keyframe-and-phase-animators.md`

**Interfaces:**
- Consumes: `pipeline/maps/apple-animations-live.md`; `pipeline/distill-prompt.md` (adapted as in Phases 2–4: corpus-lines input becomes "Fetch these DocC JSON endpoints: <the map's list for your file>"; currency rule becomes "cite the canonical human URL per claim cluster; `[VERIFY: ...]` for anything inferred beyond fetched text"); sibling to read before writing: `plugin/skills/apple-design/references/animation-taste.md` (the judgment boundary — mechanics only here, no taste restatement).
- Produces: the two references (exact filenames above) read by SKILL.md (Task 4); `keyframe-and-phase-animators.md` must include a minimal `PhaseAnimator` snippet Task 5 executes verbatim.

- [ ] **Step 1: Dispatch two distiller subagents** (parallel, model sonnet), one per file, with the adapted pipeline prompt. Include the implementer-brief template text from Global Constraints verbatim. Content requirements from the spec:
  - `animation-fundamentals.md`: `withAnimation` vs the `.animation(_:value:)` modifier (which to reach for and why; the `value:` discipline), the `Animation` type and timing curves, the modern `Spring` API (duration/bounce and response/dampingFraction forms, judgment on parameterization), the `Animatable` protocol (when a custom `animatableData` is actually needed), `Transaction` (overriding/disabling animation in a scope), `contentTransition` (including numeric text rolling). Cross-ref `animation-taste.md` for all when/why/how-much judgment — this file is mechanics.
  - `keyframe-and-phase-animators.md`: `PhaseAnimator` (discrete phase sequences, trigger-driven vs continuous), `KeyframeAnimator` + `KeyframeTrack` (per-property independent timing, the keyframe types), `TimelineView` (time-driven redraw, schedules), and a decision block: phases vs keyframes vs timeline (map the choice, one paragraph each). **Must include a minimal correct `PhaseAnimator` snippet that compiles as written when pasted into a SwiftUI `View` body — Task 5 executes it verbatim.**
  - No UIKit/Core Animation content (spec out-of-scope); anything the live docs don't state gets `[VERIFY:]`, resolved or dropped before commit.

- [ ] **Step 2: Resolve `[VERIFY:]` flags** (fetch the relevant endpoint; drop unverifiable inferences). `grep -rn "VERIFY" plugin/skills/apple-animations/` → empty.

- [ ] **Step 3: Add CONVENTIONS.md headers** (`> verified: 2026-08 against <human URLs checked>` / `> sources: live Apple docs (no book input; judgment layer: apple-design/animation-taste.md)`).

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-animations && git commit -m "feat: apple-animations fundamentals + keyframe/phase references"
```

---

### Task 3: Distill `transitions-and-matched-geometry.md` + `scroll-and-visual-effects.md`

**Files:**
- Create: `plugin/skills/apple-animations/references/transitions-and-matched-geometry.md`
- Create: `plugin/skills/apple-animations/references/scroll-and-visual-effects.md`

**Interfaces:**
- Consumes: the map; adapted distill prompt as in Task 2; siblings to read before writing: `animation-taste.md` (judgment boundary) and `plugin/skills/apple-design/references/accessibility.md` (reduce-motion policy lives there — cross-ref only).
- Produces: the two references (exact filenames) for Tasks 4–5; `transitions-and-matched-geometry.md` must include a minimal `matchedGeometryEffect` pairing snippet Task 5 executes verbatim.

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet; brief template text verbatim). Content requirements:
  - `transitions-and-matched-geometry.md`: the transition API (`transition(_:)`, `AnyTransition`, the `Transition` protocol for custom transitions, asymmetric/combined), insertion/removal mechanics (why both views in the hierarchy at once breaks it), `matchedGeometryEffect` end-to-end (namespace, `id`, `isSource` discipline, the common jump-instead-of-animate failure modes), zoom/navigation transitions (`navigationTransition(_:)` + `matchedTransitionSource(id:in:)`). **Must include a minimal correct `matchedGeometryEffect` pairing snippet (two views, one namespace, toggled by state) that compiles as written — Task 5 executes it verbatim.**
  - `scroll-and-visual-effects.md`: `scrollTransition(_:axis:transition:)` + `ScrollTransitionConfiguration` (phase-based row effects), `visualEffect` (geometry-reading effects without GeometryReader), the shader effect modifiers `colorEffect`/`layerEffect`/`distortionEffect` + `Shader`/`ShaderLibrary` wiring (in scope: the modifier surface, parameter passing, when each applies; out of scope per spec: authoring nontrivial MSL — say so and stop).
  - Reduce-motion: one cross-ref line to `apple-design`'s `accessibility.md`, no policy restatement.

- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Headers as in Task 2 Step 3.

- [ ] **Step 3: Sibling-consistency check.** Grep both new files for restatements: motion taste/judgment ("feels", "purposeful", "restraint" — belongs to `animation-taste.md`), reduce-motion policy (`accessibility.md`), build/run commands (`xcode-loop`). Replace any restatement with a one-line cross-ref.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/apple-animations && git commit -m "feat: apple-animations transitions/matched-geometry + scroll/visual-effects references"
```

---

### Task 4: `apple-animations` SKILL.md + evals + cross-refs + consume-test

**Files:**
- Create: `plugin/skills/apple-animations/SKILL.md`
- Create: `plugin/skills/apple-animations/evals/triggers.md`
- Modify: `plugin/skills/apple-design/SKILL.md` (one-line cross-ref: implementation mechanics → apple-animations)
- Modify: `plugin/skills/apple-design/references/animation-taste.md` (one-line cross-ref near the top: implementation mechanics → apple-animations)

**Interfaces:**
- Consumes: the four references from Tasks 2–3 (exact filenames as listed there).
- Produces: the complete skill for Tasks 5–6.

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: apple-animations
description: Implementing animations and motion in SwiftUI - withAnimation and the animation modifier, the Animatable protocol, springs and timing curves, Transaction, contentTransition, PhaseAnimator, KeyframeAnimator, TimelineView, view transitions, matchedGeometryEffect, zoom navigation transitions, scrollTransition scroll effects, visualEffect, and the Metal shader effect modifiers (colorEffect, layerEffect, distortionEffect). Use when writing, tuning, or debugging animation code - springs that feel wrong, transitions that jump instead of animating, keyframed or phased sequences, scroll-driven effects, shader effects. Not for whether or how much to animate or motion taste (apple-design), reduce-motion policy (apple-design), general layout and styling (apple-design), or the build/run loop (xcode-loop).
---

# Animations & motion (implementation)

Scope: how animation code is written. Whether/when/how much to animate is
judgment and belongs to apple-design (`references/animation-taste.md`);
reduce-motion policy to apple-design (`references/accessibility.md`); the
build/run loop to xcode-loop.

Read the reference for the decision at hand:
- withAnimation vs .animation, springs, timing, Transaction, contentTransition → `references/animation-fundamentals.md`
- Multi-step sequences: PhaseAnimator, KeyframeAnimator, TimelineView → `references/keyframe-and-phase-animators.md`
- Transitions, matchedGeometryEffect, zoom navigation transitions → `references/transitions-and-matched-geometry.md`
- scrollTransition, visualEffect, shader effect modifiers → `references/scroll-and-visual-effects.md`

Rules that always apply:
- Animate state, not side effects: drive every animation from a state
  change the framework can interpolate; imperative timers are the last
  resort (TimelineView exists for the time-driven cases).
- Scope animations with the value: prefer `.animation(_:value:)` bound to
  the changing value, or `withAnimation` at the mutation site - unscoped
  animation modifiers animate things you did not intend.
- Springs are the default feel on Apple platforms; tune with the modern
  parameterization (duration/bounce) before reaching for custom curves.
- One namespace, one source: most matchedGeometryEffect failures are two
  active sources or mismatched identity - check `isSource` and view
  identity before rewriting the layout.
- Taste questions (is this too much motion?) → apple-design; this skill
  answers how, not whether.
```

- [ ] **Step 2: Write `evals/triggers.md`** (no "build X" phrasing — Global Constraints eval-harness rule)

```markdown
# apple-animations trigger evals
## Should fire
- "My spring animation feels too bouncy - how do I tune the damping?"
- "Animate this heart icon through three pulsing phases in a loop"
- "How do I keyframe a bounce where scale and offset move on different timing?"
- "This view's transition jumps instead of animating when it appears"
- "Expand the tapped thumbnail into the detail card with a hero animation"
- "Fade and scale list rows as they scroll off the top of the screen"
- "Add a ripple distortion to this view when tapped - shader effect?"
## Should NOT fire
- "Is this screen using too much animation? Does it feel Apple-like?"  (apple-design)
- "Fix this Sendable warning"                                          (swift-concurrency)
- "Run the mac target and screenshot it"                               (xcode-loop)
- "Where should this view's state live?"                               (swift-architecture)
```

- [ ] **Step 3: Add the judgment-layer cross-refs.** In `plugin/skills/apple-design/SKILL.md`, one line in the routing text: animation *implementation* (springs, keyframes, transitions API, shader effects) → `apple-animations`. In `plugin/skills/apple-design/references/animation-taste.md`, one line near the top (after the header block): "Implementation mechanics (the APIs) live in the apple-animations skill; this file owns judgment." Keep both to a single sentence.

- [ ] **Step 4: Pre-validate the consume-test prompt** (Global Constraints rule): `grep -in "isSource\|namespace\|jump" plugin/skills/apple-animations/references/transitions-and-matched-geometry.md` — confirm the reference actually covers the matched-geometry jump failure modes. If not covered, pick a covered topic from the file and adjust the Step 5 prompt; record the adjustment.

- [ ] **Step 5: Consume-test with captured evidence.** From `~/Projects/StudioFixture`:

```bash
claude --plugin-dir ~/Projects/apple-studio/plugin -p "My photo grid uses matchedGeometryEffect to expand a tapped thumbnail into a detail card, but the change jumps instead of animating smoothly. Both views are in the hierarchy at the same time. Explain what's wrong and exactly how to fix it. Answer now, no clarifying questions." --output-format stream-json --verbose --max-turns 15 --allowedTools "Skill Read"
```

Save to the SDD workspace as `task-4-consume-test.log`. Evidence required: skill invocation (`apple-studio:apple-animations`), ≥1 reference Read (expect `transitions-and-matched-geometry.md`), answer visibly applying its content (`isSource` discipline / single-active-source, view identity, namespace). Fixture tree stays clean (read-only prompt; verify `git -C ~/Projects/StudioFixture status --porcelain` is empty).

- [ ] **Step 6: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/skills/apple-animations plugin/skills/apple-design && git commit -m "feat: apple-animations skill (SKILL.md + evals + judgment-layer cross-refs)"
```

---

### Task 5: Free-tier exercise — PhaseAnimator + matchedGeometryEffect end-to-end

**Files:**
- Create (SDD workspace only, not committed to plugin): `task-5-macbuild.log`, `task-5-exercise.log`, screenshots `task-5-phase.png`, `task-5-matched.png`

**Interfaces:**
- Consumes: `keyframe-and-phase-animators.md`'s `PhaseAnimator` snippet (Task 2) and `transitions-and-matched-geometry.md`'s `matchedGeometryEffect` pairing snippet (Task 3) — this task executes what the references claim, verbatim.
- Produces: captured evidence for Task 6's verification table; corrections back into the references if any documented snippet fails as written.

- [ ] **Step 1: Baseline mac build** of the unmodified fixture (mac target: headless-buildable and screenshottable, the Phase 4 pattern):

```bash
cd ~/Projects/StudioFixture && xcodebuild build -scheme StudioFixture \
  -destination 'platform=macOS' -derivedDataPath /tmp/StudioFixture-mac 2>&1 | tail -5
```

Expected: `** BUILD SUCCEEDED **`. Save output → `task-5-macbuild.log`.

- [ ] **Step 2: Temporarily modify the fixture's `ContentView.swift`:** insert (a) the `PhaseAnimator` snippet from `keyframe-and-phase-animators.md` and (b) the `matchedGeometryEffect` pairing snippet from `transitions-and-matched-geometry.md`, **copied verbatim** (adjusting only identifier names/labels to say "StudioFixture Phase 5"; the matched pairing keeps its state toggle). If a snippet does not compile as written, that is a reference defect: fix the reference first, then use the fixed snippet, and record the correction. Rebuild with the Step 1 command → `** BUILD SUCCEEDED **`.

- [ ] **Step 3: Launch + capture evidence.** Animation motion is time-based; the evidence standard (per spec) is build-success plus visible end-state screenshots, not frame-by-frame capture.

```bash
open /tmp/StudioFixture-mac/Build/Products/Debug/StudioFixture.app && sleep 3
screencapture -x /tmp/task-5-phase.png     # PhaseAnimator surface visible (any phase)
osascript -e 'tell application "StudioFixture" to activate' \
  -e 'tell application "System Events" to click at {600, 400}' && sleep 2 || true
screencapture -x /tmp/task-5-matched.png   # matched-geometry pairing after toggle (or initial state if the click needs the fallback)
```

**CHECKPOINT (user-assisted fallback, only if needed):** if `osascript`/System Events is blocked by an automation-permission prompt, ask the user to either grant it or manually toggle the matched-geometry state in the running app, then re-capture. Verify both screenshots show the expected surfaces (Read the PNGs); copy them + a command log to the SDD workspace as `task-5-phase.png`, `task-5-matched.png`, `task-5-exercise.log`. Quit the app (`osascript -e 'quit app "StudioFixture"'`).

- [ ] **Step 4: Revert the fixture.** `git -C ~/Projects/StudioFixture restore .` then `git -C ~/Projects/StudioFixture status --porcelain` → empty.

- [ ] **Step 5: Fold corrections back.** If Steps 1–3 revealed any reference claim that didn't survive contact, the reference is fixed in this task and committed:

```bash
cd ~/Projects/apple-studio && git add plugin/skills/apple-animations && git commit -m "fix: apple-animations reference corrections from free-tier exercise" || echo "no corrections needed"
```

---

### Task 6: Integration verification + 0.6.0 release

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (0.5.0 → 0.6.0)
- Modify: `docs/specs/2026-08-04-phase5-animations-design.md` (append `## Phase 5 verification results (<date>)`)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Trigger-eval sampling.** For `apple-animations`: all 7 should-fire + all 4 should-NOT prompts. For each prior skill (apple-design, apple-frameworks, apple-macos, app-release, swift-architecture, swift-concurrency, swift-testing, xcode-loop): 1 should-fire + 1 should-NOT prompt (regression sample) — for apple-design use "Does this screen feel native?" (the Phase 3 substitution), run from `~/Projects/StudioFixture` cwd. 27 prompts total. Method per prompt:

```bash
claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2 --output-format stream-json --verbose --allowedTools "Skill Read"
```

One log per prompt in the SDD workspace (`task-6-eval-<name>.log`). Verdict = grep for `"name":"Skill","input":{"skill":"apple-studio:<skill>"`; `error_max_turns` exits on fire-prompts are expected and not failures. Record the pass/fail table. Misfire → diagnose first (harness confound vs description defect — Phase 3 precedent); the closest routing boundary this phase is apple-animations vs apple-design's animation-taste ("feels too bouncy" = fire on apple-animations; "too much animation?" = apple-design) — only tighten a description for genuine routing misses, re-run that prompt, record old → new.

- [ ] **Step 2: `claude plugin validate . --strict`** — pass, zero warnings, captured to `task-6-validate.log`. (This run must reflect the Task 0 agent cut — the plugin manifest surface has no agents if the kill-switch fired.)

- [ ] **Step 3: Append `## Phase 5 verification results (<date>)`** to the Phase 5 spec: one entry per deliverable (kill-switch measurement + action; sweep items; live map with zero MISSING; 4 references with verified headers; skill consume-test; free-tier exercise incl. both screenshots; eval table; strict validation) — with `file:line-range` evidence pointers, honest caveats verbatim where things were partial.

- [ ] **Step 4: Bump version to 0.6.0, commit, tag**

```bash
git add -A && git commit -m "release: apple-studio 0.6.0 - Phase 5 (animations & motion)"
git tag v0.6.0
claude plugin validate . --strict
```

(Installed-plugin update happens post-merge, controller-handled, as in Phases 1–4. Xcode re-import after merge — one re-import covers the pending 0.5.0 and this 0.6.0, per Task 0 Step 7.)

---

## Self-review notes

- Spec coverage: deliverables (4 refs → Tasks 2–3; SKILL.md + evals + both-ways cross-refs → Task 4; routing discipline → Task 3 Step 3 + Task 4 Step 3; no new agent → Global Constraints) ✓; sources/pipeline (no books map — first phase without one, stated in map preamble; seed-list convention → Task 0 Step 5 + Task 1; endpoint probing done at planning 2026-08-04, all 26 endpoints 200, zero MISSING → Task 1) ✓; opening task (kill-switch measurement first with decision pre-taken in brainstorming, verbatim record text → Task 0 Steps 2–3; mac-app-structure fix → Step 4; convention → Step 5; back-refs → Step 6; manual hand-offs → Step 7) ✓; verification (evals with harness rules + the animations/design routing boundary called out → Task 6; consume test → Task 4; StudioFixture exercise with the spec's build-success + end-state-screenshot evidence standard → Task 5; validate/bump/re-import → Task 6) ✓; out-of-scope respected (no UIKit/CALayer, no MSL depth, no reduce-motion restatement, no taste restatement) ✓.
- Deliberate scope cuts (YAGNI): no additions to apple-design beyond two one-line cross-refs; no StudioFixture buildout beyond the two documented snippets; shader coverage stops at the modifier surface per spec.
- Task 5's snippets-executed-verbatim rule carries the Phase 3/4 "failures indict the docs" principle; the two snippets are declared as hard deliverables in Tasks 2–3 so the distillers know Task 5 will execute them.
- Kill-switch: the *decision* was taken in brainstorming (cut on zero) and is recorded in the spec — Task 0 executes a measurement, not a judgment call; the genuine-invocation branch is still specified so a surprise finding doesn't derail the task.
- Line numbers are approximate by design (standing convention) — every edit step verifies with grep first.
