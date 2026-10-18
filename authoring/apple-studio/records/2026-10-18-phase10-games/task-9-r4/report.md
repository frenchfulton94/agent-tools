# Task 9 report: game-frame profiling in apple-performance, and R4

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Machine: Apple M4 Pro, macOS 27.0.1 (26A434), Xcode 27.1. The controller wrote this file from the implementer's returned text (ruling P10). The task commit is `88887c8`.

## Status

The section, the exit-status corrections, the R4 script, and the gates are done. **R4 is pending. It needs Processor Trace enabled and a restart.** Turning the setting on did not take effect in this session, and the user has deferred the restart.

## R4

Pass criterion (brief): the heaviest symbol under `tick` intervals is `plantedSlowStep`, found from the export, not from knowing where it was planted.

`run.sh r4` runs this command, from `authoring/apple-studio/pipeline/fixtures/metal-probe/`:

    xcrun xctrace record --template 'Processor Trace' --time-limit 10s --output $TMP/r4.trace --target-stdout $TMP/r4.stdout --launch -- .build/release/MetalProbe sim --ticks 100000 --slow

It then exports the toc and prints the launched `<process>` element. Next it records a control run: the same command without `--slow`, written to `$TMP/r4-control.trace`. If `record` exits 2, `r4` stops after the first run.

`run.sh r4-finding` runs `heaviest_under_interval.py` on both traces, with `--subsystem dev.frenchfultonjr.apple-studio.metal-probe --interval tick`. Its output goes to `r4-finding.log`, and the output of `r4` goes to `r4-toc.log`.

### Attempts so far (`r4-attempt-1.log`)

Two recordings ran by hand. The first used the brief's command plus `--target-stdout`. The second was a 2 s check of `sim --ticks 1000 --slow`, made after the user turned the setting on and before a restart. Each one:
- exited 2;
- printed "Run issues were detected (trace is still ready to be viewed): * [Error] The target device is not configured for tracing. Enable Processor Trace in System Settings → Privacy & Security → Developer Tools to capture traces." and then "Recording failed with errors. Saving output file...";
- still saved a 484K bundle;
- left the `--target-stdout` file at 0 bytes.

`xctrace export --toc` on each saved bundle exited 10 with "Export failed: Trace is malformed - run data is missing."

### The analysis, and its self-test (`r4-selftest.log`, not R4)

`heaviest_under_interval.py` receives only the signpost's subsystem and interval name. It never searches for a function name. It does these steps:
1. It exports the toc and the `OSSignpostIntervals` table. The matching `tick` rows give time ranges per thread. Start and duration are in ns: the first row reads `216500 (fmt 216.50 µs)`.
2. It exports each `processor-trace-*`, `time-profile` or `cpu-profile` table present, and prints its columns.
3. It charges cost inside the ranges, on the same thread:
   - Sample rows: the row's weight goes to the leaf function. Frames that share the leaf's address are code inlined into one function, so they count as the outermost frame of that group.
   - Interval rows: time goes to the innermost open call.

`run.sh r4-selftest` checks the analysis on Time Profiler recordings:
- `sim --ticks 5000 --slow`: 5000 tick intervals. Heaviest under `tick`: `plantedSlowStep(_:dt:)`, at 99.32% of tick self weight.
  - Without grouping inlined frames, the raw leaf frame is `specialized IndexingIterator.next()` (47.95%), then `specialized Array._checkSubscript` (35.16%).
  - The first backtrace shows `IndexingIterator.next()` and `plantedSlowStep` at the same address.
- `sim --ticks 200000`, the control: heaviest under `tick`: `simulationStep(_:dt:)`, at 65.52%.

So the analysis names a different function for each workload, and it names the planted one only when the planted one runs. The Processor Trace branch has not run on real data. Schema names from the shipped Instruments bundle (`ProcessorTraceFramework.xcplugindata`, not logged): `processor-trace-intervals`, `-points`, `-threads`, `-gaps`. If R4's export has no rows that carry a symbol, `r4-finding` exits 1 and prints each table's columns.

## Reference changes

`SKILL.md`:
- The out-of-scope line no longer names Metal graphics. A routing line sends GPU work to `apple-metal` and frame pacing to `apple-games`.
- The profiling-workflow pointer now names a game's frame and tick on the CPU.
- The exit-54 rule is replaced. The exit status reports how the target ended: 0 when the target exited 0, and 54 when it exited non-zero or `--time-limit` killed it. A recording that could not trace exited 2 and still saved a bundle. Read the launched `<process>` element.
- The description is unchanged.

`references/profiling-workflow.md`:
- Re-stamped `verified: 2026-10`, with the added pages and the SDK's `os/signpost.h`. Added `> typecheck: macos 26.0` and `> typecheck-cpp: metal-cpp 26.4`, and a Contents list (P28).
- **Capturing a trace** (was line 67): replaced "exits non-zero (54) even on full success" with three observations:
  - The exit status follows the target. `/usr/bin/true` gave 0. `/usr/bin/false` and the time-limit SIGKILL gave 54. The completion lines were identical. Read `return-exit-status` and `termination-reason` (r3-toc.log).
  - A recording that cannot trace exits 2, saves a 484K bundle, and leaves an empty `--target-stdout` file. `export --toc` on that bundle exits 10 (r4-attempt-1.log).
  - `--launch` resolves by bundle ID. Also: `--target-stdout` keeps the target's stdout and stderr (r3-toc.log), and the exported tables can be read by a script.
- **Classic pitfalls** (was line 233): the exit-54 bullet now says that 0 and 54 report the target's exit, that a time-limit kill gives 54, and that a failed recording gives 2.
- **Template table:** three game rows, for Game Performance, Time Profiler then Processor Trace under `tick`, and Game Memory or Allocations. The template list is logged in `templates.log`.
- **New `## Profiling a game's frame`:**
  - The budget: refresh interval, about 5 ms of main-thread work, CPU/GPU overlap, and no Error or Fault logs per frame.
  - Templates for a game, Allocations generations across level loads, and dSYM matching.
  - Per-frame and per-tick signposts, with a Swift `OSSignposter` block and a C++ `<os/signpost.h>` block, and the header's rules (literals, `OS_SIGNPOST_ID_NULL`, `os_signpost_enabled`, `OS_LOG_CATEGORY_DYNAMIC_TRACING`, marked not runtime-checked).
  - Finding the function that makes a tick slow: the Time Profiler export join, its `ref` and inlined-frame traps with the self-test values, Processor Trace's documented views, and the enablement facts. It ends with "**R4 pending: not yet runtime-checked.**" covering CLI recording and export ranking.
  - Apple-silicon guidance from *Addressing CPU bottlenecks*: the four bottleneck categories with their game reading, cutting algorithmic and ARC cost first, dynamic task allocation (pointing to apple-games), and the gated CPU Optimization Guide.
  - Frame-time test plans: `-only-test-configuration` and `-skip-test-configuration` with one dash (`xcodebuild-help.log`), against the page's two dashes.

Values from task-7 item 37 that are not stated: p01:6's "10 s capture", the template list beyond `templates.log`, and "no Energy Log template". `templates.log` has no Energy Log entry, but the reference does not make that claim.

## Fixture

- `run.sh`: new targets `r4`, `r4-finding` and `r4-selftest`, with the helpers `record_sim` and `heaviest`.
- `heaviest_under_interval.py`: new.
- `README.md`: documents the new targets and the setting.

## Gates

- `typecheck_snippets.py` on profiling-workflow.md: 1/1, exit 0 (`typecheck.log`). `catalog-before.log` line 3285 lists 0 Swift blocks for this file, so there is no PASS→FAIL.
- `typecheck_native.py`: 1/1, exit 0 (`native.log`).
- Vale on SKILL.md and profiling-workflow.md: 0 errors, 33 warnings (35 before). On the fixture README: 0 errors, 3 warnings, the same as before.
- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: 0 errors, 54 warnings.
- `claude plugin validate . --strict`: passed.
- `check_verbatim.py`: exit 0.

## Clean state

- No MetalProbe, xctrace or host process is running.
- No simulator is booted.
- Traces are only in the gitignored `$TMP`.
- StudioFixture was not touched. The session's worktree guard refused the `git -C` status check.

## Open after the restart

1. Run `./run.sh r4 > $REC/task-9-r4/r4-toc.log` and `./run.sh r4-finding > $REC/task-9-r4/r4-finding.log`.
2. Record the verdict here.
3. Replace the "R4 pending" paragraph in profiling-workflow.md with the result (a P36-sized fix if R4 passes). If R4 contradicts the section, the section changes.
