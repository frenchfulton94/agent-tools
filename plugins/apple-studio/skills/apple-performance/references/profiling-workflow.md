> verified: 2026-09 against https://developer.apple.com/documentation/xcode/improving-your-app-s-performance, https://developer.apple.com/tutorials/instruments, https://developer.apple.com/tutorials/instruments/getting-started-with-hang-analysis, https://developer.apple.com/tutorials/instruments/identifying-a-hang, https://developer.apple.com/tutorials/instruments/analyzing-main-thread-activity, https://developer.apple.com/documentation/xcode/diagnosing-performance-issues-early, https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-shipping-app, https://developer.apple.com/documentation/xcode/analyzing-cpu-profiles-with-call-tree-views, https://developer.apple.com/documentation/xcode/analyzing-cpu-usage-with-processor-trace, https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks, https://developer.apple.com/documentation/os/ossignposter, https://developer.apple.com/documentation/os/logging, https://developer.apple.com/documentation/os/recording-performance-data, https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app, https://developer.apple.com/documentation/foundationmodels/managing-the-context-window
> sources: live Apple docs (no book input — the corpus predates these frameworks)

# Profiling Workflow: Instruments, Call Trees, and Custom Instrumentation

Scope: *why is the code slow and how do you measure it*. Whether the app builds, tests, or
runs headlessly is `xcode-loop`'s territory (`headless-commands.md`); this file starts
after you already have a running app and a symptom.

## The one rule that makes any of this mean anything

A number from a Debug build, the simulator, a cold-cache first run, or a session with no
prior baseline is not evidence — it's a guess with a decimal point.

- **Profile Release.** Use **Product > Profile** (⌘I) — it always builds Release regardless
  of the active scheme, unlike **Run**. A Debug build's disabled optimizations and extra
  runtime checks (see Thread Performance Checker below) change both timing and call shape.
- **Profile a physical device**, not the simulator, for timing questions — the simulator
  runs on your Mac's scheduler and silicon, not the target's.
- **Distinguish cold from warm.** First launch, first tap, first cache-filling run are
  different measurements from the fifth. State which one you captured.
- **Change one variable, then re-measure the same interval** against a kept baseline —
  that's what Run Comparison (below) is built around. A "faster" build you can't diff
  against a prior trace is an anecdote.
- **Quiesce the device first.** Thermal throttling and background load skew everything
  downstream; Apple's own Foundation Models profiling guidance explicitly calls out
  checking for thermal pressure before recording, and the same applies everywhere else.

## Choosing an Instruments template for a symptom

Verified against this machine's Instruments 27 (`xcrun xctrace list templates`).

| Symptom | Template | Notes |
|---|---|---|
| No idea yet, general sluggishness | **Time Profiler** | Default instrument set already includes a Hangs track. |
| UI freezes / unresponsive taps | **Time Profiler** (Hangs track); **Animation Hitches** for scroll/animation stutter specifically | Full hang-vs-hitch triage: `responsiveness-hangs-and-hitches.md`. |
| CPU busy, cause unclear | **Time Profiler** → call tree / flame graph | See "Reading call trees." |
| CPU% looks fine but work still feels inefficient (stalls, cache misses) | **CPU Counters** (CPU Bottlenecks mode), then **Processor Trace** | Microarchitectural, not algorithmic. |
| Memory growth, leaks | **Allocations**, **Leaks** | Leak vs. abandoned-memory distinction: `memory-power-and-size.md`. |
| Excessive SwiftUI view updates | **SwiftUI** | Diagnosis owned by `swiftui-performance.md`. |
| Task explosion, actor contention | **Swift Concurrency** | Fix-side judgment: `swift-concurrency`. |
| On-device model latency / token spend | **Foundation Models** | See dedicated section below. |
| Disk writes, storage growth | **File Activity**, **Data Persistence** | Owned by `memory-power-and-size.md`. |
| Battery drain | **Power Profiler** | Owned by `memory-power-and-size.md`. |
| Launch time | **App Launch** | Owned by `responsiveness-hangs-and-hitches.md`. |
| Your own timeline regions | Any template + the `os_signpost` instrument | See "Custom instrumentation." |

## Capturing a trace

**GUI (the normal path):** **Product > Profile** (⌘I) — always Release. Instruments opens
its template chooser; pick a template, **Choose**, confirm the target, click **Record**.
Reproduce the symptom, click **Stop**.

**`xctrace` — real, and verified by execution** against a Release build of the
StudioFixture fixture app on this machine, producing a working `.trace` bundle:

```bash
xcrun xctrace record --template 'Time Profiler' --time-limit 5s \
  --output out.trace --launch -- /path/to/YourApp.app
```

Other real, help-verified forms (`xcrun xctrace help record`): `--attach <pid|name>` for a
process already running, `--all-processes` for a system-wide capture, `--device <name|UDID>`
for another Mac or connected device.

Two surprises, both directly observed on this machine (full detail in "Classic pitfalls"):
the recording above **exits non-zero (54) even on full success**, and **`--launch`
resolves by bundle ID through LaunchServices**, so it can silently profile a different
registered build than the path you gave — `xctrace export --input out.trace --toc` (run
and confirmed) is how you catch that, by checking the recorded process's actual path in the
dumped XML. `xctrace symbolicate --input in.trace --output out.trace --dsym Path.dSYM`
(exact form from `xctrace help symbolicate`) resymbolicates a trace against dSYMs. None of
the analysis below — reading a call tree, the Heaviest Stack Trace, setting an inspection
range, Charge/Prune/Flatten — has a CLI form; those are Instruments-window interactions
only, so don't invent a flag for any of them.

## Reading call trees

The detail area's top-right segmented control switches between three views of the same
samples:

- **Call Tree** — full hierarchy, heaviest-branch-first; click a header to reverse sort.
  Best for navigating a path you already suspect.
- **Flame Graph** — same data as stacked blocks; width = share of samples, depth =
  call-stack position. Best first glance at a large profile — wide blocks are hotspots.
- **Top Functions** — collapses a function called from many callers into one row with all
  samples combined, catching a function that's cheap per-caller but expensive in aggregate.

**Weight vs. Self Weight:** Weight is total time including callees; Self Weight is time in
the function's own code only. High Weight / low Self Weight means look at its children;
high Self Weight is where the CPU is actually executing. **Invert Call Tree** (a toolbar
checkbox) roots the tree at leaf frames instead of `main`, so every hot leaf becomes a
root with its callers as children — usually faster than drilling through the same launch
boilerplate every time.

**Heaviest Stack Trace** (inspector, right side) is a *computed* single stack, not another
view of the whole tree: from the root, it recursively picks the heaviest child at each
level (constrained to pass through your current selection, if any). Collapsed by default
to frames where CPU usage changed significantly between parent and child — click the
top-right button to expand every frame. Default-colored frames are symbolicated from your
own code; gray frames are unattributed system/library code. Hover a colored frame for
file/line and click through to Xcode.

Two more tools once you have a candidate frame: **Charge / Prune / Flatten**
(Control-click a symbol) — Charge folds a function's cost into its callers while removing
it from view, Prune removes it and its callees entirely, Flatten collapses a library's
internals to its boundary frames — and **Run Comparison** (⌘K or the ⇆ button), which
diffs two recordings' call trees in one document (red = regression, green = improvement,
percentages are relative change, not share of total). Filter both runs to the same
`OSSignposter` interval first so you compare the same operation, not ambient noise.

## Processor Trace: what sampling can't give you

Time Profiler samples periodically, so brief or rare paths can fall between samples.
**Processor Trace** instead captures the CPU's hardware branch-tracing stream, reconstructing
*every* function call including compiler-generated code (ARC traffic, synthesized C++
constructors) a sampler would miss or misattribute.

**Hardware/OS requirement:** recording needs an iPhone 16/16 Pro+, an iPad Pro with M4+, or
a Mac with M4+, on iOS/iPadOS 18.4+ or macOS 15.4+. Any Mac can *analyze* an already-saved
trace regardless of its own hardware. Recording overhead alone is under 1%, though
Instruments' other concurrent tracing can push total overhead higher.

Capture: **Product > Profile** → **Processor Trace** template → Record → interact → Stop.
For a stripped/shipping build, load dSYMs via **File > Symbols > Add Symbols > Add Folder
of dSYMs** — without them, compiler-generated branch-island addresses show as raw pointers
even with everything else symbolicated. Charge/Prune/Flatten carry over, plus a
Call Tree/flame-graph toggle and separate Summary: Function Calls and Function Calls views
for aggregate vs. per-invocation inspection. Reach for it once Time Profiler has pointed at
a hot region and you need exact call counts — it's a follow-up, not a replacement.

## Addressing CPU bottlenecks

A "bottleneck" here is microarchitectural — pipeline stalls, cache misses — distinct from
raw CPU usage. Low CPU% with heavy bottleneck activity means the processor is busy
stalling, not busy computing.

Detection: **CPU Counters** template, set its mode to **CPU Bottlenecks**, Record,
reproduce, Stop. The track adds lanes showing what fraction of maximum sustainable
bandwidth falls into each bottleneck category; click it for a Summary: Metrics view, or
switch to Remarks for Instruments' own annotated explanation and suggested fixes.
Control-click a bottleneck and choose **Suggested Next** for a follow-up recording
pre-tuned to that category.

Judgment the docs recommend: prefer system frameworks over hand-rolled equivalents (already
tuned for the microarchitecture); prefer dynamic scheduling (Background Tasks, QoS'd GCD
queues) over static thread pools, which leave cores idle while others queue — the
QoS/priority-inversion mechanics themselves are `swift-concurrency`'s scope, this file only
tells you CPU Counters is where you'd notice the effect; and set a numeric target, held by
a performance test (`XCTCPUMetric`, `XCTClockMetric`) — authoring those is
`swift-testing`'s scope.

No detected bottleneck doesn't mean optimal code — it only rules out this failure mode.

## Custom instrumentation with `OSSignposter`

A log line (`Logger` — covered in `apple-frameworks`'s OSLog primer, not restated here)
answers "did this happen." A signpost answers "how long, and where on the timeline" — a
structured begin/end (or single-point) event Instruments renders as a span, not narrative
text.

Three shapes: an **interval** (`beginInterval(_:id:)`, retain the returned
`OSSignpostIntervalState`, `endInterval(_:_:)` right after — exactly one begin and one end,
enforced at runtime), a **closure-wrapped interval** (`withIntervalSignpost(_:id:around:)`,
for a region that's already one expression), and a **point event** (`emitEvent(_:id:)`,
an instant with no duration — don't force a zero-width interval for something that isn't
one).

Construct with an explicit `subsystem`/`category` (matching your `Logger` convention), or
wrap an existing `Logger` via `OSSignposter(logger:)`. **Always call `makeSignpostID()`**
when more than one instance of the same named interval can overlap (concurrent requests,
overlapping animations) — without a distinguishing ID, Instruments can't tell them apart.

Viewing: any template plus the **`os_signpost`** instrument (exact name confirmed via
`xcrun xctrace list instruments`; Apple's prose sometimes writes "os_signposts"). Fastest
path to just signposts: **Product > Profile** → **Blank** template → **+** (Instrument
library) → double-click **os_signposts** → Record. Selecting a signpost span filters every
call-tree view in the document to that interval — the same mechanism Run Comparison uses.

## Analyzing the performance of your shipping app

Everything above is local: one device, one reproducible run. Field performance is a
different question: **Window > Organizer**, which aggregates anonymized real-user metrics
— launch time, responsiveness, memory, energy, disk writes (full MetricKit/field-metrics
coverage: `responsiveness-hangs-and-hitches.md`).

Organizer opens to an **Insights** overview surfacing regressions and goal-based
recommendations without hunting individual metric pages. Enable regression notifications
(bell icon) for alerts when a shipped version regresses 75%+ against the trailing
four-version average, capped at one per app version. Charts compare against similar-app
goals (comparable peers) and historical goals (your own past versions), with a margin of
error that narrows as more data arrives — a single day post-release isn't a verdict.

Local profiling tells you *why* one run was slow; Organizer tells you whether real users
are affected, and at what percentile. Treat a local win as a hypothesis until Organizer
confirms it moved the field distribution.

## Foundation Models profiling

Xcode ships a **Foundation Models** instrument (confirmed via `xctrace list
templates`/`list instruments`) with a token-usage timeline: per-request
instructions/prompt/response, tool-call latency and output, and a per-step token breakdown
(cache-hit rate, input vs. output count). Capture like any template — **Product > Profile**
→ **Foundation Models** → Record → interact → Stop — but the recording captures prompts
and responses **unencrypted**; Instruments warns you on record start, so handle the
resulting trace file like any file containing users' raw input.

This file only routes you to the instrument. Reducing what you find there — trimming
prompts, dropping `includeSchemaInPrompt` once a schema's established, splitting a task
across sessions before the context window fills — is implementation, and belongs to
`apple-intelligence`.

## Diagnosing before you open Instruments

Xcode's **Thread Performance Checker** runs automatically on **Run** (not **Profile**) and
flags priority inversions and non-UI main-thread work as they happen, no profiling session
required — findings appear in the Issue navigator with an expandable backtrace. Its own
overhead can leak into a profile if you attach to an app Xcode already launched; use
**Profile** (which excludes it), or disable it via **Product > Scheme > Edit Scheme > Run >
Diagnostics**, when you need a clean trace. Fixing what it reports (QoS mismatches,
`dispatch_semaphore_wait` misuse) is `swift-concurrency` material — this is only the early
warning telling you to go look.

## Classic pitfalls

- **Profiling a Debug build.** Optimizations off, extra runtime checks on — timings and
  even which functions appear can differ from what ships. Always **Product > Profile**.
- **Trusting the simulator for timing questions.** Fine for correctness, wrong for speed.
- **No baseline.** One trace shows what happened once, not whether a change helped.
- **Changing more than one variable between measurements** — a delta then tells you
  nothing about which change mattered.
- **Trusting `xctrace`'s exit code** instead of its printed completion line and the trace
  file itself — a successful `--time-limit` capture still exits 54 on this machine (see
  "Capturing a trace").
- **Assuming `--launch` profiled the exact binary you pointed at.** LaunchServices resolves
  by bundle ID and can silently substitute another registered build — verify with `xctrace
  export --toc` (see above).
- **Reading the collapsed Heaviest Stack Trace as the whole story** — expand to all frames
  before concluding nothing else is relevant.
- **Ignoring gray, unsymbolicated frames** instead of loading dSYMs — you may be
  attributing cost to the wrong caller entirely.
- **Recording under thermal pressure or background CPU load** — the trace faithfully shows
  a real bottleneck, just not the one users see under normal conditions.

## Where else to look

- `swiftui-performance.md` — view updates, structural identity, `.id()`, observation granularity.
- `responsiveness-hangs-and-hitches.md` — hangs vs. hitches, launch phases, MetricKit, terminations.
- `memory-power-and-size.md` — Allocations/Leaks, retain cycles, Power Profiler, disk/size.
- `swift-concurrency` — actor isolation, QoS, priority-inversion fixes.
- `swift-testing` — writing `XCTCPUMetric`/`XCTClockMetric` performance tests.
- `apple-animations` / `apple-intelligence` — implementing the fix once Instruments names the expense, on-device generation implementation.
- `xcode-loop` — build/test/run mechanics this file assumes already work.
