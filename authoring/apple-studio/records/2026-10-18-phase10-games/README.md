# Phase 10 record: game development on Metal

Evidence for `docs/specs/2026-10-18-phase10-games-design.md` and
`docs/plans/2026-10-18-phase10-games.md`. One directory per task, each with its
report. `survey/` holds the pre-plan measurements. `task-0-sweep/` holds the
opening kill-switch scan, the catalog regeneration, and the header check.

## What is not committed, and where it is

### Task 6 traces

The Task 6 runtime probe (`authoring/apple-studio/pipeline/fixtures/metal-probe/`)
keeps its traces in `authoring/apple-studio/pipeline/tmp/`, which is gitignored.
They exist only on the machine that recorded them: an Apple M4 Pro with macOS
27.0.1 and Xcode 27.1. `run.sh` in the fixture records them again. The logs in
`task-6-probe/` cite them as `$TMP/<name>`.

| Trace or output | Claim | Made by |
|---|---|---|
| `probe.gputrace` | R2 | `MetalProbe capture`. The profiling block's `profile run --embed` writes a profile into it. |
| `probe-compile-in-capture.gputrace` | R2 | `MetalProbe capture --compile-in-capture`. `profile run` hangs on it. |
| `r2/` (`draw0.png`, `cost.png`, `draw0_fragment_cost_top100.json`, `compile-in-capture-draw0.png`, the scripts run) | R2 | The `gpudebug` blocks and `fetch` commands |
| `r3-1.trace` | R3 | Metal System Trace, 100,000 frames. `xctrace export` crashes on it. |
| `r3-2.trace` | R3 | Game Performance, 100,000 frames |
| `r3-3.trace` | R3 | Metal System Trace, ended by `--time-limit 1s` |
| `r3-true.trace`, `r3-false.trace` | R3 | Time Profiler on `/usr/bin/true` and `/usr/bin/false`: the exit-status check |
| `r3-streams/` | R3 | Time Profiler on a shell that writes to stdout and stderr, with and without `--target-stdout` |
| `r3-*.toc.xml`, `r3-*.submissions.xml`, `r3-*.stdout` | R3 | `xctrace export` and `--target-stdout` output |
| `r5-cpp-host.gputrace`, `r5-rust-host.gputrace` | R5 | Each host's `--capture` |
| `r5-pre-fix/` | R5 | Copies of the project with the pre-fix argument string, unquoted and quoted |
| `r5-cpp-host.trace`, `r5-rust-host.trace`, `r5-*.toc.xml`, `r5-*.submissions.xml` | R5 | Metal System Trace on each host |

The crash reports that R2 and R3 cite (`GPUToolsReplayService`,
`GPUToolsDebugService`, `xctrace`) are in `~/Library/Logs/DiagnosticReports/` on
that machine. They are not copied here, because they carry the machine's
environment.
