---
name: apple-performance
description: Diagnosing why an Apple app is slow, and measuring it - choosing an Instruments template for a symptom, capturing traces with xctrace and the Instruments GUI, reading call trees and processor traces, OSSignposter instrumentation, hangs versus hitches, the render loop, launch time, terminations, MetricKit and Organizer field data, SwiftUI view-update diagnosis, structural identity and body cost, observation granularity, leaks versus abandoned memory, memory limits and jetsam, battery and Power Profiler, disk writes, and app size. Use when something is slow, janky, stuttering, hanging, leaking, draining battery, launching slowly, or growing on disk, and when deciding how to measure any of it. Not for whether the build succeeds or how to run tests (xcode-loop), authoring performance tests (swift-testing), writing animations (apple-animations), or implementing on-device AI (apple-intelligence).
---

# Performance (diagnosis and measurement)

Scope: **why is it slow, and how do I measure it.** Whether it builds, runs, or
passes tests is xcode-loop. Authoring a performance *test* is swift-testing.
Writing the animation is apple-animations — its *cost* is here. Metal graphics,
custom instrument authoring, and CI performance gating are out of scope.

Read the reference for the decision at hand:
- Picking an Instruments template for a symptom, capturing traces, call trees, processor trace, OSSignposter, measurement discipline → `references/profiling-workflow.md`
- Hangs vs hitches, the render loop, launch time, terminations, MetricKit and Organizer → `references/responsiveness-hangs-and-hitches.md`
- Excessive view updates, structural identity and `.id()`, expensive `body`, observation granularity, lazy containers → `references/swiftui-performance.md`
- Leaks vs abandoned memory, retain cycles, memory limits, battery, disk writes, app size → `references/memory-power-and-size.md`

Rules that always apply:
- **Measure before optimizing, and change one variable at a time.** A number
  produced without a baseline is not evidence. Neither is a second number
  produced after three simultaneous changes.
- **Profile a release build on a real device.** A Debug build measures the
  optimizer being off; the Simulator measures your Mac. macOS does not enforce
  memory pressure or jetsam the way iOS does, so a green Simulator gauge proves
  nothing about a device.
- **Name the symptom before picking a tool.** "The app is slow" is not a
  diagnosis. A hang and a hitch have different causes, different instruments,
  and different fixes; reaching for Time Profiler by reflex answers the wrong
  question about half the time.
- **"No leaks" is not "no memory problem."** Leaks finds unreachable cycles.
  A growing cache or an accumulating subscription list is fully reachable,
  entirely intentional-looking, and invisible to it.
- **Where a workflow is GUI-only, it is GUI-only.** Call-tree analysis has no
  command-line form. `xctrace` records and exports; it does not read a trace
  for you. Do not go looking for a flag that does not exist.
- **`xctrace record` exits 54 on success** when `--time-limit` ends the
  capture, and `--launch` resolves through LaunchServices by bundle ID rather
  than the path you passed — verify what you actually profiled with
  `xctrace export --toc` before trusting a trace.
- Profiling a Foundation Models app: Xcode ships a **Foundation Models**
  instrument with a token-usage timeline. Implementation of on-device
  generation is apple-intelligence; its runtime cost is here.
