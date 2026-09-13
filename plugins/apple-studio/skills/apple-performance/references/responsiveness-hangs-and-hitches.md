> verified: 2026-09 against https://developer.apple.com/documentation/Xcode/understanding-user-interface-responsiveness, https://developer.apple.com/documentation/Xcode/understanding-hangs-in-your-app, https://developer.apple.com/documentation/Xcode/understanding-hitches-in-your-app, https://developer.apple.com/documentation/Xcode/improving-app-responsiveness, https://developer.apple.com/documentation/Xcode/analyzing-responsiveness-issues-in-your-shipping-app, https://developer.apple.com/documentation/Xcode/reducing-your-app-s-launch-time, https://developer.apple.com/documentation/Xcode/reduce-terminations-in-your-app, https://developer.apple.com/documentation/MetricKit, https://developer.apple.com/documentation/metrickit/monitoring-app-performance-with-metrickit, https://developer.apple.com/documentation/metrickit/analyzing-app-performance-with-metrickit, https://developer.apple.com/documentation/metrickit/track-performance-by-app-state-using-metrickit, https://developer.apple.com/documentation/metrickit/metricmanager, https://developer.apple.com/documentation/metrickit/hangtimemetric, https://developer.apple.com/documentation/metrickit/hitchtimemetric, https://developer.apple.com/documentation/metrickit/timetofirstdrawmetric, https://developer.apple.com/documentation/metrickit/optimizedtimetofirstdrawmetric, https://developer.apple.com/documentation/metrickit/applicationresumetimemetric, https://developer.apple.com/documentation/metrickit/extendedlaunchmetric, https://developer.apple.com/documentation/metrickit/foregroundterminationmetric, https://developer.apple.com/documentation/metrickit/backgroundterminationmetric, https://developer.apple.com/documentation/metrickit/hangdiagnostic, https://developer.apple.com/documentation/metrickit/applaunchdiagnostic
> sources: live Apple docs (no book input — the corpus predates these frameworks)

> gui-verified: 2026-09-12 against Instruments in Xcode 27.0, Animation Hitches template,
> iPhone 16 Pro Max on iOS 27.0. The hitch-labelling paragraph below comes from that
> session; the previous wording came from the doc and was wrong about it.

# Responsiveness, Hangs, and Hitches

An app feels responsive when it preserves two illusions: that a discrete action (a tap, a
keypress) causes an immediate reaction, and that continuous motion (a drag, a scroll, an
animation) stays fluid. Each illusion breaks differently, and Apple's tooling treats the
breaks as two different phenomena — a **hang** breaks the first, a **hitch** breaks the
second. Humans tolerate a longer *constant* delay far better than a shorter *inconsistent*
one: a steady 50 ms lag while dragging an icon is barely noticeable, but the same icon
freezing and then jumping ahead is jarring even at a shorter average delay — which is why
platforms optimize for smooth motion first and low latency second, except where both matter
at once (Apple Pencil-class input).

Every number below assumes release-configuration, real-device measurement — warm and cold,
across your supported device tier; see `profiling-workflow.md` for that discipline. A number
produced without it isn't evidence.

## The responsiveness model

A discrete interaction (button tap, keypress) has a noticeability threshold: delays "less
than 100 ms" are rarely perceived, and once main-thread work plus the rest of the pipeline
(event delivery, then render-server + display work — roughly 10–50 ms even when nothing is
wrong) crosses that line, users perceive a pause. Budget less than half the 100 ms for your
own main-thread work; fixed pipeline overhead eats the rest.

A continuous interaction (scroll, drag, animation) has a per-frame deadline instead: the
display's refresh interval, 16.7 ms at 60 Hz or 8.3 ms at 120 Hz (ProMotion). Apple's guidance
for main-thread UI-update work per frame is "less than 5 ms," leaving headroom for the render
server's own deadline in the same interval. Missing one frame deadline is enough to be
visible — an order of magnitude less slack than a discrete-interaction hang — which is why
hangs and hitches need different detection machinery, not just different fixes.

## Hangs vs hitches: the central judgment

**A hang** is a delay in a *discrete* interaction, almost always long-running or blocked work
on the main thread's run loop. Apple's tools start flagging it once the main run loop's busy
period exceeds **250 ms** (Instruments' Hangs instrument lets you set a lower threshold), and
at 1 second or longer of unresponsiveness the system also samples a backtrace — the data hang
*reports*, not just hang *rates*, are built from. Detection is purely run-loop unresponsiveness,
regardless of whether the user was touching the screen at that instant, so a reported hang is
really a *hang risk*: a condition that would have caused one had they interacted then.

**A hitch** is an interruption in *continuous* motion — the display fails to update at the
expected cadence, usually because a frame arrived late and got dropped or delayed. The
threshold is a single refresh interval, "generally between 8 ms and 16 ms," two orders of
magnitude tighter than a hang's. Unlike hangs, hitches can only be detected while something is
actively driving screen updates; with no update trigger, there's nothing to be late.

These are related — an unresponsive main thread can cause both — but they are not the same
failure with different severities. A hang's fix is almost always "get work off the main
thread or reduce its volume." A hitch's fix requires knowing *which side of the render loop*
missed its deadline, because the main thread committing on time but the render server still
missing its deadline is a different bug in a different place than the reverse. Treating a
hitch as "a smaller hang" and reaching for a CPU/Time Profiler trace instead of a render-loop
tool is the single most common misdiagnosis in this file's subject matter.

**Fix hangs first** — Apple's own stated ordering, and a practical one: hang diagnosis and
fixes are simpler (separate non-UI work from UI work, cut unnecessary main-thread work), and
because unresponsive-main-thread hangs are also a major source of commit hitches, fixing them
collapses part of your hitch rate for free. Only then turn to the render loop for what remains.

## The render loop, and where a hitch enters it

The render loop targets a future vsync (the **presentation time**) and works backward to two
earlier deadlines: the **begin time** (earliest the app can start this frame's work) and the
**commit deadline** (when it must hand its Core Animation commit to the render server). In
the common double-buffer case each stage — main-thread UI update, then render-server CPU
precompute + GPU render — gets one vsync interval, and the full path from "app starts work" to
"pixel updates onscreen" spans about three vsync intervals even when nothing is late.

A missed **commit deadline** — the CA commit isn't ready in time — is a **commit hitch**: the
app's problem, on the app's side of the boundary. A missed render deadline *after* a timely
commit — the render server's CPU/GPU work ran long — is a **render hitch**: usually still
caused by what the app asked to render (an overly complex view update), but diagnosed and
fixed on the rendering side, not by backgrounding app code (the commit itself must happen on
the main thread — that's not the slow part here). Distinguishing the two tells you where to
spend optimization effort.

The system can absorb some lateness with **triple-buffer mode**, giving the render server two
vsync intervals across two frames in flight instead of one, at the cost of one extra vsync of
latency. This isn't itself a hitch — the display still gets a new frame every vsync going
forward — only a frame that still misses its (now longer) deadline is. Instruments'
**Animation Hitches** template visualizes this pipeline, but **it does not label a hitch
"commit" or "render"** — verified against Xcode 27 on 2026-09-12. Each hitch's row in
**Summary: Hitches** carries Start, Duration, Process, Display, Swap ID, and a **Potential
Issue** narrative such as *Potentially expensive app update(s)*. The commit/render answer is
structural: expand the Hitches track and read which phase lane flags the frame — `updates`
(the app's side, a commit hitch), `renders` (the render server's side), plus `gpu` and
`framewait`. A planted per-row cost in a scrolling `List` flagged 73 frames in `updates`
against 1 in `renders`, which is how that split reads in practice.
`profiling-workflow.md` owns how to capture and read the trace itself.

## Launch

An **activation** (icon tap, or returning to the app) is either a **resume** — the process is
already alive, possibly suspended — or a full **launch**; resumes are categorically faster and
optimized differently, so know which one you're measuring. Launches range across a cold/warm
spectrum by device memory pressure: "warm" follows recent use with frameworks and daemons
still resident, "cold" follows eviction (yours or the OS's, e.g. after a memory-heavy game) and
pays disk-paging costs on top. Test the spectrum deliberately — post-boot, after force-quit,
after something memory-hungry, immediate re-entry — a single warm dev-machine run hides most
of what users experience.

Launch proceeds through phases, and your leverage differs sharply by phase:

- **Process load (`dyld`).** Loads your executable and every linked framework, resolving
  symbols. Each embedded third-party framework adds cost; built-in frameworks are nearly free,
  living in a shared cache other processes already warmed. Levers: fewer embedded third-party
  frameworks/dylibs, and mergeable libraries (Xcode 15+) for near-static-link launch
  performance without losing dynamic-linking debug-build times.
- **Static initializers**, run before `main()`: C++ static constructors, Objective-C `+load`,
  `__attribute__((constructor))` functions, anything in `__DATA,__mod_init_func`. Fully
  controllable — move the work to first use instead.
- **App-delegate launch callbacks**, synchronous on the main thread; the launch cycle doesn't
  complete until they return. Do only what the first screen needs — defer network sync and
  non-view subsystem setup (persistence, location) to first use, and prepare only the view
  state actually being restored or shown by default.
- **First-frame rendering** is main-thread work like any other; a simpler initial view
  hierarchy draws faster. Launch-time measurement ends here, at the first Core Animation
  commit — the moment the first frame reaches the display pipeline. A splash screen showing
  doesn't stop this clock; the first *real* frame does.
- **Everything after first frame but before the app is actually usable** (rendering a
  document, finishing a bootstrap) isn't in the launch-time metric, but it's very much in
  perceived launch time. Instrument it with `trackLaunchTask`/`ExtendedLaunchMetric` (Field
  Metrics below) or with signposts (`profiling-workflow.md` owns that API).

What's outside your control: the OS may prefetch — starting your process in the background
before the icon is tapped — and device memory state at activation time determines how much
paging a cold launch pays. iOS also enforces an **App Watchdog** launch-time limit, killing
apps stuck at launch (macOS has none) — a backstop for the phases above going wrong, not a
lever you tune directly.

## Terminations

Terminations are inherent to the platform, not a bug class to drive to zero — the system uses
them to keep the foreground experience fluid at everything else's expense. You control
*frequency*, and every termination has a lifecycle cost beyond itself: the next activation is
a full cold launch instead of a fast resume, so termination rate is a launch-time multiplier
as much as a stability metric.

The taxonomy, from Apple's own reason codes:

- **Aborts, Bad Access, Illegal Instruction** — crashes (`abort()`/uncaught exception, invalid
  memory access, an uninterpretable instruction). Diagnose via the Crashes Organizer and a
  call-stack trace; ordinary crash debugging, nothing responsiveness-specific.
- **App Watchdog** — launch took too long (see Launch above); the only lever is a faster
  launch, not the termination itself.
- **Memory Limit / Memory Pressure** — a foreground app used more memory than the system can
  give it, or a background app's memory got reclaimed for one that needed it. Shared edge with
  `memory-power-and-size.md`, which owns *diagnosing and reducing* footprint; this file's
  angle is that the termination forces a relaunch instead of a resume, so a lower
  suspended-memory footprint is a responsiveness lever too, and solid state restoration keeps
  the forced relaunch from reading as broken.
- **Task Timeout / File Lock** (background-only) — background work via a background-task API
  ran past its allotted time, or the app held a lock on a shared App Group file while
  backgrounded. Fixes: finish background work faster (or use a more appropriate API), and
  release file locks before suspension rather than relying on the system to wait.

## Field metrics: MetricKit and the Xcode Organizer

Local profiling, however disciplined, cannot reproduce the real population's device-model
spread, thermal states, memory pressure, network variance, and rare interaction sequences.
MetricKit and the Xcode Organizer close that gap with data sampled from real devices in the
field.

**Xcode Organizer** (Window ▸ Organizer, GUI-only — there is no command-line equivalent to
these views) surfaces:

- **Hitches pane** (iOS/iPadOS only — unavailable on tvOS and visionOS; visionOS should use
  the RealityKit Trace template instead) — hitch rate over time and by release, in
  milliseconds of pause per second across every animated interaction, not just scrolling. The
  bands: "a hitch rate at or below 10 ms/s is good; at or below 25 ms/s is a warning; at or
  below 50 ms/s is critical; and above 50 ms/s warrants immediate attention."
- **Hangs pane** (iOS, macOS, visionOS) — hang rate as seconds-per-hour unresponsive, counting
  only periods over 250 ms; shown as median and 90th-percentile experience, filterable by
  device. Individual reports group by common backtrace, ranked by share of total hang time.
- **Launches pane** (iOS/iPadOS) — launch time (median and 90th percentile) from icon tap to
  first frame past the splash, comparable release-over-release; ranks the longest-running
  startup functions by percent of launch time.
- **Termination reports.**

The Hangs and Launches report lists both offer **Generate Recommendations** on a selected
report — GUI-only, in the Inspector — which pastes the stack trace into Xcode's coding
assistant for triage; no scripted path exists.

**MetricKit**, as of iOS 27/macOS 27, centers on `MetricManager`: two `async` sequences,
`metricReports` (daily aggregated `MetricReport`) and `diagnosticReports` (per-event
`DiagnosticReport`), both `Codable`. Diagnostics arrive promptly; metric reports at most once
per day, covering the prior 24 hours. MetricKit **does not deliver payloads on Simulator** —
this data only exists on real devices. During development, trigger sample (not real) payloads
via Xcode's Debug ▸ Simulate MetricKit Payloads menu item (GUI-only) to exercise your handling
code without waiting for the daily schedule.

The payload types most relevant here: `HangTimeMetric` (histogram of unresponsive periods;
anything past 9 s collapses into the final bucket, so a 10 s and a 60 s hang look identical);
`HitchTimeMetric` (a perceptually-weighted hitch ratio normalized to total animation duration —
closer to what users actually experienced than a raw dropped-frame count); `TimeToFirstDrawMetric`
(ends at the first CA commit, Organizer's definition) vs. `OptimizedTimeToFirstDrawMetric`
(reflects OS prefetching — when it beats the former, that gap is time the system already hides
from the user); `ApplicationResumeTimeMetric` (the resume path, tracked separately from
cold-launch time); `ExtendedLaunchMetric` (ends at the *later* of first frame and completion of
any `trackLaunchTask` work, capturing post-first-frame launch that would otherwise stay
invisible); `ForegroundTerminationMetric`/`BackgroundTerminationMetric` (counts by category,
separating expected exits from unexpected ones — correlate via `terminationCategory`); and
`CrashDiagnostic`/`HangDiagnostic`/`AppLaunchDiagnostic` (each carries a `CallStackTree` plus a
duration, the same raw shape Organizer visualizes, for a backend Organizer doesn't offer).

For your own field instrumentation, `mxSignpost` (paired with `MetricManager.logHandle`) is
the field-metrics counterpart to `OSSignposter` (`profiling-workflow.md` owns that local API):
a plain `OSSignposter` interval does *not* populate `SignpostIntervalMetric`'s CPU-time,
memory, or hitch-ratio fields — only `mxSignpost` (or its animation-tagged sibling) does.

## Analyzing responsiveness issues in your shipping app

A different workflow from local profiling: you start from an aggregate symptom — a rate
moved — not a reproducible local repro, and the job is to turn one into the other.

1. Notice a regression in Organizer's Hitches, Hangs, or Launches rate for a release
   (release-over-release, directly in the graph), then filter by device/OS — code fine on one
   chipset can hang or hitch on another, and the aggregate rate hides that. Bisect by app
   version against your own version-control history to narrow where to look.
2. Read the ranked report list and its backtrace to identify the implicated function; use
   Generate Recommendations for assisted triage if useful.
3. Reproduce locally: on a real device, enable Settings ▸ Developer ▸ Hang Detection
   (GUI-only; works for dev-signed and TestFlight builds) to capture your own hang reports and
   import the resulting tailspin files into Instruments — or attach Instruments directly (Time
   Profiler for hangs, Animation Hitches for hitches) and reproduce the interaction manually.
4. Once reproduced, hand off to `profiling-workflow.md`'s call-tree and processor-trace
   mechanics — this file's job ends at "confirmed, reproducible cause," that file's is the
   line-level "why."

## Classic pitfalls

- **Diagnosing a hitch with a CPU profiler alone.** Time Profiler shows what the CPU is doing,
  not which side of the commit/render boundary missed its deadline — reach for Hitches data or
  the Animation Hitches template first, or you'll optimize the wrong stage.
- **"Just wrap it in a `Task`."** A `Task` created inside main-actor-isolated code inherits
  that context and still runs on the main thread — it defers the hang, not removes it. Getting
  isolation right is `swift-concurrency` territory; this file's tools only confirm the fix worked.
- **Treating every Memory Pressure/Memory Limit termination as a bug to eliminate.** Some are
  inherent to how the OS arbitrates foreground memory. The lever is lowering suspended-memory
  footprint (`memory-power-and-size.md`) and making the forced relaunch cheap, not chasing the
  termination itself.
- **Reading only the Organizer median, and confusing "first frame drawn" with "app usable."**
  The 90th percentile is often where a real, device-specific problem hides. Separately, the
  launch-time metric stops at the first CA commit — work after that (rendering a document,
  finishing a fetch) is invisible to Organizer but fully visible to the user; instrument it
  with `trackLaunchTask`/`ExtendedLaunchMetric` or signposts instead of trusting the headline
  number.
- **Profiling hitches or launch time on Simulator, and fixing hitches before hangs.** Simulator
  GPU/thermal/memory behavior doesn't match hardware and MetricKit delivers nothing there —
  this work needs real devices. And fix hangs first regardless: diagnosis is simpler, and a
  meaningful share of hitches share a hang's root cause, so fixing hangs collapses part of the
  hitch rate for free.
