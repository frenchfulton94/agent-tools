# Live endpoint map: apple-performance

Targets (Tasks 6–7): `profiling-workflow.md`, `responsiveness-hangs-and-hitches.md`,
`swiftui-performance.md`, `memory-power-and-size.md`.

**No books map, and there will not be one.** The corpus is spent and
`pipeline/convert.sh` is dormant until new books arrive. This skill is 100%
live-docs. A future phase should not go looking for `apple-performance-books.md`.

This map is a **seed list, not an exhaustive registry**, per the CONVENTIONS.md
"Distillation maps" rule: it enumerates dispatch-time starting points, distillers may
follow narrower pages under an enumerated parent when the fetch actually succeeds
(DocC JSON 200), and the reference files' own header citations — not this map — are
the citation record. Expected-but-missing pages are recorded below as `MISSING:`.

Sectioning below follows **Apple's own** `Xcode/performance-and-metrics` topic
sections, so the seam between references is Apple's rather than one we invented.

## Endpoint pattern

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

**Exception — the Instruments tutorial is not under `/documentation/`.** It is a
DocC *tutorial*, served from a different data prefix:

```
MISSING: documentation/instruments            -> 404
correct: https://developer.apple.com/tutorials/data/tutorials/instruments.json   -> 200
human:   https://developer.apple.com/tutorials/instruments                       -> 200
```

Recorded because the obvious guess 404s and looks like a dead page.

## Probe status

94 seeds probed at spec time (2026-09-02) — all 200, zero MISSING — and
**re-probed at Task 1 execution time: all 94 unchanged, still 200.**
Evidence: `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/spec-endpoint-probe.tsv`.

---

## ⚠️ BINDING CONSTRAINTS FOR DISTILLERS

1. **The Instruments honesty rule (spec-mandated).** Where a step is only doable in
   the Instruments GUI, **say so and describe the UI path**. Never invent a
   command-line equivalent for a GUI-only workflow. A plausible-looking `xctrace`
   incantation that does not exist is worse than an honest "this is a GUI step",
   because the reader will burn time proving it wrong.

2. **Every command-line invocation gets executed before it ships.** Task 6 Step 2
   runs every `xctrace` command in `profiling-workflow.md` against StudioFixture and
   records real output. Commands that cannot run as written are corrected or removed
   — the same standard `xcode-loop`'s `headless-commands.md` was held to in Phase 1.

3. **Scope split with `xcode-loop`.** `xcode-loop` owns *does it build / test / run*.
   This skill owns *why is it slow and how do I measure it*. Do not restate build
   or test invocation mechanics; cross-ref.

4. **Measurement discipline is the content, not a preamble.** Release configuration,
   real device over simulator, warm vs cold, measure before optimizing, one variable
   at a time. A number produced without these is not evidence, and the reference
   should say so where it matters rather than once at the top.

---

## `profiling-workflow.md`

Apple's *Essentials* and *Processor usage* sections plus the signposting API.

- `Xcode/improving-your-app-s-performance`
- `tutorials/instruments` — **note the endpoint exception above**
- `Xcode/diagnosing-performance-issues-early`
- `Xcode/analyzing-the-performance-of-your-shipping-app`
- `Xcode/analyzing-cpu-profiles-with-call-tree-views`
- `Xcode/analyzing-cpu-usage-with-processor-trace`
- `Xcode/addressing-cpu-bottlenecks`
- `os/OSSignposter`
- `os/logging`

**Required content:** choosing an Instruments template for a symptom, capturing a
trace (GUI **and** `xctrace` where it genuinely applies — see BINDING CONSTRAINT 1),
reading call trees, processor trace, addressing CPU bottlenecks, custom
instrumentation with `OSSignposter`, and the measurement discipline that makes
numbers mean anything.

**Incoming cross-ref to place here:**
`FoundationModels/analyzing-the-runtime-performance-of-your-foundation-models-app`
— Xcode ships a **Foundation Models instrument** with a token-usage timeline
(named in `FoundationModels/managing-the-context-window`). One line routing
Foundation Models profiling into this file; the *implementation* of on-device
generation stays in `apple-intelligence`.

---

## `responsiveness-hangs-and-hitches.md`

Apple's *Responsiveness* section, minus the SwiftUI page (its own file below).

- `Xcode/understanding-user-interface-responsiveness`
- `Xcode/understanding-hangs-in-your-app`
- `Xcode/understanding-hitches-in-your-app`
- `Xcode/improving-app-responsiveness`
- `Xcode/analyzing-responsiveness-issues-in-your-shipping-app`
- `Xcode/reducing-your-app-s-launch-time`
- `Xcode/reduce-terminations-in-your-app`
- `MetricKit`

**Required content:** the responsiveness model, hangs vs hitches and why the
distinction drives *different* fixes, the render loop, launch phases and what moves
each, terminations, and field metrics via MetricKit and the Organizer.

---

## `swiftui-performance.md`

- `Xcode/understanding-and-improving-swiftui-performance` (+ children followed live)

Sits under Apple's *Responsiveness* section but earns its own file: SwiftUI update
diagnosis is a distinct skill from hang/hitch triage, and it is the question most
likely to be asked.

**Required content:** diagnosing excessive view updates, structural identity and
`.id()` misuse, expensive `body` computation, observation granularity, lazy-container
behaviour in long lists, and which Instruments template answers which SwiftUI
question.

**Do not restate:** animation *implementation* (`apple-animations`), main-actor rules
(`swift-concurrency`), state ownership and architecture (`swift-architecture`).
Cross-ref instead.

---

## `memory-power-and-size.md`

Apple's *Memory and size*, *Power*, and *Disk usage* sections.

- `Xcode/reducing-your-app-s-memory-use`
- `Xcode/reducing-your-app-s-size`
- `Xcode/analyzing-your-app-s-battery-use`
- `Xcode/measuring-your-app-s-power-use-with-power-profiler`
- `Xcode/reducing-your-app-s-battery-use`
- `Xcode/reducing-disk-writes`
- `Xcode/reducing-your-app-s-disk-usage`
- `Xcode/monitoring-your-app-s-storage-metrics`

**Required content:** leaks vs abandoned memory (and why the distinction changes the
tool you reach for), retain-cycle diagnosis, memory limits and termination, battery
use and the Power Profiler, disk writes and storage metrics, app size.

---

## OUT OF SCOPE (Phase 6)

All live and returning 200; none cut for being stale.

`OUT OF SCOPE (Phase 6): Graphics / Metal`
- `Xcode/analyzing-the-performance-of-your-metal-app`
- `Xcode/analyzing-the-memory-usage-of-your-metal-app`

`OUT OF SCOPE (Phase 6): custom instrument authoring`
- `Xcode/creating-custom-modelers-for-intelligent-instruments`

`OUT OF SCOPE (Phase 6): platform-specific performance planning`
- `visionOS/creating-a-performance-plan-for-visionos-app`

`OUT OF SCOPE (Phase 6): network tracing`
- `Foundation/analyzing-http-traffic-with-instruments`

`OUT OF SCOPE (Phase 6): CI performance gating.` Regression gating in CI is a
release-engineering concern; revisit in `app-release` on demand.

---

## CROSS-REF (not distilled here)

- `Xcode/writing-and-running-performance-tests` → **`swift-testing`**. Performance
  *test authoring* belongs with test authoring. `apple-performance` answers why the
  code is slow; `swift-testing` answers how to assert it stays fast. One line each
  way, no duplicated content.
- `FoundationModels/analyzing-the-runtime-performance-of-your-foundation-models-app`
  → **`apple-performance`**, placed in `profiling-workflow.md` (see above). This is
  the inbound half of the bridge whose outbound half is recorded in
  `apple-intelligence-live.md`.
