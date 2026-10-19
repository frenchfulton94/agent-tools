> verified: 2026-10 against https://developer.apple.com/documentation/xcode/improving-your-app-s-performance.md, https://developer.apple.com/tutorials/instruments, https://developer.apple.com/tutorials/instruments/getting-started-with-hang-analysis, https://developer.apple.com/tutorials/instruments/identifying-a-hang, https://developer.apple.com/tutorials/instruments/analyzing-main-thread-activity, https://developer.apple.com/documentation/xcode/diagnosing-performance-issues-early.md, https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-shipping-app.md, https://developer.apple.com/documentation/xcode/analyzing-cpu-profiles-with-call-tree-views.md, https://developer.apple.com/documentation/xcode/analyzing-cpu-usage-with-processor-trace.md, https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks.md, https://developer.apple.com/documentation/os/ossignposter.md, https://developer.apple.com/documentation/os/logging.md, https://developer.apple.com/documentation/os/recording-performance-data.md, https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app.md, https://developer.apple.com/documentation/foundationmodels/managing-the-context-window.md, https://developer.apple.com/documentation/xcode/improving-app-responsiveness.md, https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app.md, https://developer.apple.com/documentation/xcode/analyzing-the-memory-usage-of-your-metal-app.md, https://developer.apple.com/documentation/metal/improving-your-games-graphics-performance-and-settings.md, https://developer.apple.com/documentation/xcode/gathering-information-about-memory-use.md, https://developer.apple.com/documentation/xcode/building-your-app-to-include-debugging-information.md, https://developer.apple.com/documentation/xcode/organizing-tests-to-improve-feedback.md, https://developer.apple.com/documentation/os/generating-log-messages-from-your-code.md, https://developer.apple.com/documentation/os/legacy-signpost-symbols.md, https://developer.apple.com/documentation/apple-silicon/cpu-optimization-guide.md, the shipped `os/signpost.h` in the Xcode 27.1 macOS 27.0 SDK
> sources: live Apple docs (no book input — the corpus predates these frameworks)
> typecheck: macos 26.0
> typecheck-cpp: metal-cpp 26.4

# Profiling Workflow: Instruments, Call Trees, and Custom Instrumentation

Contents:
- The one rule that makes any of this mean anything
- Choosing an Instruments template for a symptom
- Capturing a trace
- Reading call trees
- Processor Trace: what sampling can't give you
- Addressing CPU bottlenecks
- Custom instrumentation with `OSSignposter`
- Profiling a game's frame
- Analyzing the performance of your shipping app
- Foundation Models profiling
- Diagnosing before you open Instruments
- Classic pitfalls
- Where else to look

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

Verified against this machine's Instruments 27 (`xcrun xctrace list templates`, Xcode 27.1).

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
| A game's slow frame: CPU or GPU? | **Game Performance** | GPU side: `apple-metal`. CPU side: "Profiling a game's frame." |
| Which function makes one simulation tick slow | **Time Profiler** under a `tick` signpost, then **Processor Trace** | See "Profiling a game's frame." |
| Memory that grows across level loads | **Game Memory**, or **Allocations** with generations | See "Profiling a game's frame." |

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

Three things observed on this machine (Xcode 27.1). In each case,
`xctrace export --input out.trace --toc` is the check:

- **The exit status of `record` reports how the target ended, not whether the
  capture worked.** It was 0 when the target exited 0. It was 54 when the target
  exited non-zero (`/usr/bin/false`), and when xctrace killed the target at
  `--time-limit` (Metal System Trace). Under Processor Trace, the time limit ended
  the recording but not the target (see "Profiling a game's frame"). The
  completion lines were the same for `/usr/bin/true` and
  `/usr/bin/false`. So read the toc's `<process>` element whose `type` is
  `launched`: `return-exit-status` and `termination-reason` (`exit(1)`,
  `SIGKILL`) are the only record of how the target ended.
- **A Processor Trace recording without its system setting exited 2, and still
  saved a bundle.** That is the one cause of a failed recording logged here (see
  "Profiling a game's frame"). It printed `Recording failed with errors` and
  wrote a 484K bundle. The target's `--target-stdout` file was empty, and
  `export --toc` on that bundle exited 10: "Trace is malformed - run data is
  missing."
- **`--launch` resolves by bundle ID through LaunchServices**, so it can silently
  profile a different registered build than the path you gave. Check the recorded
  process's actual path in the toc.

Pass `--target-stdout <file>` to keep the target's output. Without it, xctrace
showed neither the target's stdout nor its stderr. With it, the file received
both. `xctrace symbolicate --input in.trace --output out.trace --dsym Path.dSYM`
(exact form from `xctrace help symbolicate`) resymbolicates a trace against dSYMs. None of
the analysis below — reading a call tree, the Heaviest Stack Trace, setting an inspection
range, Charge/Prune/Flatten — has a CLI form; those are Instruments-window interactions
only, so don't invent a flag for any of them. What a script can do is read the exported
tables itself: see "Finding the function that makes a tick slow."

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

## Profiling a game's frame

A game draws every frame, so the CPU question is narrow: which work in one frame, or in
one simulation tick, goes over the budget. This section covers the CPU side. The GPU
tracks, Metal System Trace, and the Metal debugger are in
`apple-metal/references/gpu-debugging-and-profiling.md`. Frame pacing and how the loop
is built are in `apple-games/references/game-loop-and-threading.md`.

### The budget

- **Continuous work must finish inside one refresh interval:** 8.3 ms at 120 Hz, 16.7 ms
  at 60 Hz. Apple says that main-thread frame work under about 5 ms is usually on time.
  A renderer that cannot reliably finish its frame in about 5 ms should adapt to a
  variable refresh rate (*Improving app responsiveness*).
- **The CPU and GPU timelines overlap, so each one gets the full frame budget.** A long
  task that does not run every frame, such as an asset or shader load, delays encoding.
  The previous frame then stays on screen for twice its time. Split that task across
  frames, or move it off the render thread (*Improving your game's graphics performance
  and settings*).
- **Never log at Error or Fault level per frame.** Those levels go to the on-disk store
  and cost the most. A per-frame breadcrumb belongs at Debug level, or in a signpost
  (*Generating log messages from your code*).

### Templates for a game

Xcode 27.1 lists these templates for a game's frame: **Game Performance**, **Game
Performance Overview**, **Game Memory**, and **Metal System Trace**. For CPU work, it
lists **Processor Trace**, **CPU Counters**, **CPU Profiler**, and **System Trace**.

- **Game Performance** puts Thread State Trace, System Load, and Thermal State beside the
  Metal and Display tracks. Use it first, to decide whether a slow frame is CPU or GPU
  work. GPU limiter counters need **Recording Options > Counter Set > Performance
  Limiters**. Reading its GPU tracks is `apple-metal`'s job.
- **Game Memory** is the memory template for a Metal game; `apple-metal` covers its
  instruments. For level-load growth, use Allocations' generations: mark a generation at
  the menu, load a level, go back to the menu, and mark again. Do several round trips.
  What survives each round trip is the level's growth. The Simulator's memory gauge stays
  green, because macOS sends no memory warnings. A level that fits there can still be
  killed on a device (*Gathering information about memory use*).
- **Symbols:** a Release build puts its debug symbols in a separate dSYM per binary. A
  dSYM matches only the binary with the same build UUID, so a rebuild "the same" does not
  symbolicate an older trace. Set Debug Information Format to "DWARF with dSYM File" for
  the configuration you profile. Keep the archive of every build you ship (*Building your
  app to include debugging information*).

### Per-frame and per-tick signposts

Mark each frame and each simulation tick as a signpost interval. Then any template can
show where one frame's time went:

```swift
import os

let frameSignposter = OSSignposter(subsystem: "com.example.game", category: .pointsOfInterest)

func runFrame(simulate: () -> Void, encode: () -> Void) {
    let frame = frameSignposter.beginInterval("frame", id: frameSignposter.makeSignpostID())
    defer { frameSignposter.endInterval("frame", frame) }
    let tick = frameSignposter.beginInterval("tick", id: frameSignposter.makeSignpostID())
    simulate()
    frameSignposter.endInterval("tick", tick)
    encode()
}
```

- **Points of Interest shows by default** in Instruments (SDK header). The probe's
  Processor Trace recordings exported its intervals with the category
  `PointsOfInterest`, in their `OSSignpostIntervals` table (runtime-checked).
- **Select one `frame` span to isolate one slow frame.** The selection filters every
  call-tree view to that span. The slow frame's work is then not averaged into the rest
  (*Analyzing CPU profiles with call tree views*).
- **One lane per subsystem and category.** The `os_signpost` instrument draws one row for
  each pair. Give the simulation, render-encode, streaming, and audio threads their own
  categories (*Recording performance data*).
- **Field data:** MetricKit's `mxSignpost` reports the same intervals from users'
  devices; see `responsiveness-hangs-and-hitches.md`.

A C or C++ engine uses `<os/signpost.h>`. Swift's `os_signpost` functions are legacy,
and the C macros are current (*Legacy signpost symbols*, *Logging*):

```cpp
#include <os/log.h>
#include <os/signpost.h>

static os_log_t frameLog = os_log_create("com.example.engine", OS_LOG_CATEGORY_POINTS_OF_INTEREST);

void runFrame(void (*simulate)(), void (*encode)()) {
    os_signpost_id_t frame = os_signpost_id_generate(frameLog);
    os_signpost_interval_begin(frameLog, frame, "frame");
    os_signpost_id_t tick = os_signpost_id_generate(frameLog);
    os_signpost_interval_begin(frameLog, tick, "tick");
    simulate();
    os_signpost_interval_end(frameLog, tick, "tick");
    encode();
    os_signpost_interval_end(frameLog, frame, "frame");
}
```

The SDK header gives these rules. The name and the format must be string literals.
`os_signpost_id_generate` returns `OS_SIGNPOST_ID_NULL` when signposts are disabled.
Guard expensive argument work with `os_signpost_enabled(log)`. The category
`OS_LOG_CATEGORY_DYNAMIC_TRACING` keeps signposts disabled, and `os_signpost_enabled`
false, unless a tool such as Instruments is recording. That makes per-frame signposts
almost free in normal play. This file has not runtime-checked that category.

### Finding the function that makes a tick slow

Start with Time Profiler. Select a slow `tick` span, then read **Self Weight** or invert
the call tree (see "Reading call trees"). From the command line, export the intervals and
the samples, and join them by time and thread:

```bash
xcrun xctrace record --template 'Time Profiler' --time-limit 10s --output game.trace \
  --target-stdout game.out --launch -- ./MyGame
xcrun xctrace export --input game.trace --output intervals.xml \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="OSSignpostIntervals"]'
xcrun xctrace export --input game.trace --output samples.xml \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]'
```

Each `OSSignpostIntervals` row has `start` and `duration` in nanoseconds, `name`,
`subsystem`, and `start-thread`. Each `time-profile` row has `time`, `thread`, `weight`,
and a backtrace with the leaf frame first. Keep the `tick` rows of your subsystem. Then
charge each sample on the same thread, inside a tick, to its leaf function. Two things
in the export need care (runtime-checked on a probe whose slow tick runs one
`@inline(never)` function):

- **Resolve `ref` attributes.** xctrace writes a repeated value once, with an `id`.
  After that, the value appears only as an empty element that carries a `ref`
  attribute and no content.
  Resolve each `ref` to the element with that `id`.
- **Group inlined frames with their function.** Code inlined into a function appears as
  extra frames at the function's own address. In the probe, the raw leaf frame was
  `specialized IndexingIterator.next()` for 47.95% of the tick's samples. After the
  frames at one address were grouped and charged to the outermost frame, the slow
  function had 99.32%.

Then use Processor Trace for exact call counts on that tick. Apple's Processor Trace
page documents these views, which suit one slow frame:

- The process track shows Average IPC, Total Instructions, and Total Cycles. Low IPC
  points at cache misses and atomics, such as a contended job-queue counter.
- Expand the process to see each thread's functions in time order. **View > Selected
  Track > Size to Fit** makes one frame's simulation and render-thread calls readable,
  call by call.
- In **Function Calls**, Control-click a call's Duration and choose **Set Inspection
  Range**. Every view then covers only that one call, such as one `update()` of one
  frame.
- **Input filter**, or **Add to Detail Filter**, limits the views to one function,
  process, or thread. The template also records a Thread State Trace track. Analysis
  needs Instruments 16.3 or later.

Recording needs the Processor Trace setting in **System Settings > Privacy & Security >
Developer Tools**. Without it, `xctrace record` exited 2. It printed "The target device
is not configured for tracing" (see "Capturing a trace"). A recording made after
the setting was turned on, but before a restart, failed in the same way. After a
restart, it recorded.

The same join works on a Processor Trace export (runtime-checked on an M4 Pro, macOS
27.0.1, Xcode 27.1):

- **`xctrace record --template 'Processor Trace' --launch` records a command-line
  target.** It exited 0, and the toc's launched `<process>` showed `exit(0)`.
- **The time limit ends the recording, not the target.** The `--slow` run reached
  its 10 s limit. The target still finished all 100,000 ticks and exited 0, but the
  trace holds only 53,644 of them. Its bundle was 390M. The control run ended when
  its target exited, and its bundle was 767M.
- **Look for a stopped copy of the target after each recording.** Each of the two
  recordings left a second process from the `.app` bundle, not from the path given
  to `--launch`. It was in state `T` (stopped), had parent 1, and used no CPU. Its
  PID was one below the traced process's PID. After recording, check for it with
  `pgrep -fl` and end it.
- **Use the `processor-trace-intervals` table.** It has one row for each function
  call: `start`, `duration`, `thread`, `depth`, `name` (the function),
  `self-instructions`, `self-cycles`, `self-duration`, and `backtrace`. The trace also
  holds `processor-trace-gaps`, `-points`, and `-threads`, and a `time-profile` table
  of samples.
- **Charge time to the innermost open call.** Calls on one thread nest. Between two
  call boundaries, the call that opened last and has not ended is the one that runs.
  Charge that time, clipped to the `tick` intervals, to its `name`. In the probe this
  named the slow function at 99.89% of the ticks' self time. A control run without the
  slow step named the normal simulation function at 38.84%.
- **The interval table is large.** The control run's table had 58,598,788 rows, so
  stream the XML export rather than load it whole.

### Apple-silicon guidance from *Addressing CPU bottlenecks*

- **Cut algorithmic cost and redundant ARC traffic first.** Processor Trace shows both.
  Chase microarchitecture only after that.
- **CPU Bottlenecks mode splits throughput into four categories.** **Useful** is work
  that completes. **Instruction Delivery** means that fetch is slower than completion,
  for example code that branches and jumps a lot. **Instruction Processing** means that
  completion is slower than fetch, usually long memory loads. In a simulation update, that
  is the mark of an entity or component layout that does not suit the cache.
  **Discarded** is work from mispredicted branches. Bracket the hot update with signposts,
  so that you find the same region in each recording.
- **Prefer dynamic task allocation to static thread pools.** The scheduler puts threads
  on cores of different types and speeds, so work that is split evenly finishes unevenly.
  For a game, use small jobs with work stealing, or Dispatch or Swift concurrency, not one
  fixed slice for each worker in each frame. The job-system design is in
  `apple-games/references/game-loop-and-threading.md`.
- **The Apple silicon CPU Optimization Guide is a gated download.** It needs a developer
  account and a separate agreement. It has the core and cache topology, the latency
  tables, and the CPU Counters events. Point to it, and do not quote its numbers from
  memory.

Keep frame-time performance tests in their own test plan. Its configuration keeps the
sanitizers, Main Thread Checker, and the malloc debugging options off. Run the plan with
`xcodebuild -scheme <S> test -testPlan <Plan>`. Choose configurations with
`-only-test-configuration` or `-skip-test-configuration`. `xcodebuild -help` spells both
with one dash. Apple's test-plan page spells them with two (*Organizing tests to improve
feedback*). Writing the tests is `swift-testing`'s
job.

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
- **Reading `xctrace record`'s exit status, or its completion lines, as the target's
  result.** 0 and 54 report the target's exit, and a time-limit kill under Metal System
  Trace also gave 54. A recording that failed exited 2 and still saved a bundle. Read the launched `<process>`
  element in the toc (see "Capturing a trace").
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
