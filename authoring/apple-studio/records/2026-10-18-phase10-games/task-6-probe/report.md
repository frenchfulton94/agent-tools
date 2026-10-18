# Task 6 report: runtime probe R1, R2, R3, R5

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Machine: Apple M4 Pro,
macOS 27.0.1 (26A434), Xcode 27.1. The controller wrote this file from the
implementer's returned text, because the harness refused the implementer's
Write of it (SDD ruling P10).

The fixture is `authoring/apple-studio/pipeline/fixtures/metal-probe/`.
`run.sh r1|r2|r3|r5` reproduces each log in this directory. `check_verbatim.py`
diffs every pasted block against its reference. It removes the lines that the
probe adds, which are marked `// probe` or `# probe`. It exits 0 at this commit.

## Claims

| R | Claim | Verdict | Evidence |
|---|---|---|---|
| R1 | `command-model.md` § Frame structure runs as written | **Pass.** `render --frames 120` exits 0 with 120 `frame <i> ok` lines and `pixel 119 128 64 255`, which is the last frame's `SIMD4(119/255, 0.5, 0.25, 1)`. The run is the same with `MTL_DEBUG_LAYER=1 MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1`: only the two "Validation Enabled" lines, and no report. The code compiled in Swift 6 mode with no change. | `r1.log` |
| R2 | Programmatic capture writes a trace that `gpudebug` can open and query | **Pass after a reference fix.** `MTL_CAPTURE_ENABLED=1 MetalProbe capture --out $TMP/probe.gputrace` exits 0. Without the variable it exits 1 with "Capture layer is not inserted." The Sessions block, run verbatim, lists cb0 to cb3, `find opaque` finds the three groups, the draw path resolves, and `fetch` writes `draw0.png`. The profiling block failed as written. After the fix, `/performance/commands` ranks `disp0` and `draw0` to `draw2`, and the heatmap `fetch` writes `cost.png` and the JSON. `find add arrays` reaches `commands/cb3/grp0/ce0/disp0`. | `r2.log` |
| R3 | `xctrace` records the probe with Metal System Trace and Game Performance | **Pass after a reference fix. Metal System Trace passes only for short recordings.** Game Performance, as the brief specifies: the target ends `exit(0)` (100,000 frames take about 5 s, so the 10 s limit is not reached), the toc lists 48 GPU and Metal tables, and the submission rows belong to MetalProbe. Metal System Trace, as the brief specifies: it records 520 MB, then `xctrace export` crashes with SIGBUS (exit 138), which reproduces every time. With `--time-limit 1s`, `record` exits 54, xctrace SIGKILLs the target, and the toc lists 48 tables. | `r3-toc.log` |
| R5 | The external hosts build from Xcode and capture outside it | **Pass after a reference fix, except the GUI step, which is not runtime-checked.** `xcodebuild -list` shows CppHost and RustHost. Clean and build succeed for both `PBXLegacyTarget`s (`/bin/sh build.sh`, `/bin/sh xcode-cargo.sh Release`). Both hosts print `pixel 255 0 0 255` and stay clean under both validation layers. `--capture` writes a `.gputrace` only with `MTL_CAPTURE_ENABLED=1`, and `gpudebug` lists cb0/re0 in it. Metal System Trace records each host, with the target ending `exit(0)`, 48 tables, and one submission row. Attaching Xcode's GPU debugger to the external binary: not runtime-checked (GUI). | `r5.log` |

## How the probe ran each reference

- **R1.** `Sources/MetalProbe/Reference/` holds `makeFlatColorPipeline`,
  `FrameLoop`, and `renderOffscreen`, exactly as printed. The only probe lines
  are `import Metal` and one `print("frame \(frame) ok")` after `submitFrame()`.
  The target is a 64 × 64 `.rgba8Unorm` shared texture, read back at its center.
- **R2.** `capture` uses `FrameCapture`: a device scope, `captureNextFrame(to:)`,
  then `begin()`, three frames and one compute dispatch, and `end()`.
  `isCapturing` reads false afterwards.
  - The frames use the reference's `encodeLabelledFrame`. Its "Opaque draws go
    here" placeholder is filled through one marked `drawOpaque` hook, so the
    trace has the grouping that the reference's paths assume.
  - The dispatch is the probe's own `sum = a + b` kernel, which `compute
    --count 1048576` checks on all elements.
  - The `gpudebug` blocks are read from the reference at run time and run with
    `bash -v`. Only the trace name is changed.
- **R3.** The brief's commands, plus `--target-stdout` so that the probe's
  output and any error reach the log. A third run uses `--time-limit 1s` to
  exercise exit 54. Time Profiler runs on `/usr/bin/true` and `/usr/bin/false`
  check the exit status.
- **R5.** The hosts are the reference's `main.cpp` and `main.rs` with marked
  probe lines: `--capture` parsing, plus the reference's `startTrace` and
  `start_trace` helpers, called where their comments say. `Cargo.toml` is the
  reference's plus a `[[bin]] name = "rust-host"`. `Cargo.lock` is committed.
  The C++ host builds with `clang++ -std=c++20` against `$TMP/metal-cpp/26.4`,
  with no CMake.

## Reference changes

All changes are minimal, and the probe confirmed each one before the text
changed. Both gates exit 0 on each edited file and on all nine references:
Swift 62/62 and native 27/27 (`typecheck.log` and `native.log`).

`gpu-debugging-and-profiling.md`:

1. **Profiling from the terminal.** The block now runs `profile run --embed`,
   ends the session, opens a new one, and runs `profile load` before the
   `/performance` commands.
   - Measured: after a plain `profile run` ("Profile data collected"), every
     `/performance` list is `(empty)`. A `profile load` in the same session does
     not fill them, and neither does `--embed` in the same session.
   - The same result came from the writers' own `draw.swift` probe, rebuilt from
     `task-5-write/runtime/`, and from a draw-only capture. It is not specific to
     this probe.
2. **Trap replaced.** "Under `/performance`, go one level at a time" was a
   misreading. `'commands' has no info` is what every `go` into `/performance`
   prints when no profile is loaded. With a profile loaded, `go
   /performance/commands` works in one step.
3. **New trap: compile pipelines before the capture starts.**
   - When the capture recorded an `MTL4Compiler` compute-pipeline compile,
     `profile run` never returned. The replay service crashed with
     `EXC_BAD_ACCESS` in `MakeMTL4PipelineStageDynamicLinkingDescriptor`.
   - This happened with both compiler overloads, the one with
     `dynamicLinkingDescriptor: nil` and the one without it.
   - `list`, `find`, `info`, and `fetch` still worked on that trace.
   - With the pipeline compiled before the capture starts, the same frames
     profile in 6.7 s.
   - `MetalProbe capture --compile-in-capture` reproduces the hang (`r2.log`,
     last section).
4. **Instruments.** Two new points:
   - Keep Metal System Trace recordings short. Export crashed with SIGBUS on
     recordings of 50,000 and 100,000 frames (280 and 520 MB). Recordings of
     20,000 frames (142 MB) and of 1 s (112 MB) exported. A Game Performance
     recording of 100,000 frames (380 MB) also exported.
   - Exit 54 does not mean the target succeeded: `/usr/bin/false` also gives 54.
     Read `return-exit-status` and `termination-reason` from the launched
     `<process>` element. `--target-stdout` is the only way to get the target's
     stdout, and stderr is never passed through.
   - The pointer to `apple-performance` no longer cites exit 54.

`cpp-and-rust.md`:

5. **External Build System arguments.**
   - `xcodebuild build` exported `ACTION` as empty, and an empty `$(ACTION)`
     drops out of the argument list, even when quoted.
   - So the documented `xcode-cargo.sh $(ACTION) $(CONFIGURATION)` ran
     `/bin/sh xcode-cargo.sh Release`, and every Xcode build failed with "does
     not handle the action 'Release'".
   - The arguments are now `xcode-cargo.sh $(CONFIGURATION) $(ACTION)`, and the
     script reads `config` from `$1` and `action` from `$2`.
   - The template sentence now says that clean runs `make clean` and a build
     runs plain `make`, not `make build`.
6. **Verification sentence.** "Runtime-checked from a shell, not yet inside
   Xcode" now says that `xcodebuild` builds and cleans through the target, and
   that the unknown-action and missing-cargo exits were checked from a shell.
7. **GPU Frame Capture.** "That reasoning is an inference; runtime probe R5
   checks it" now says the inference is not runtime-checked, because the check
   needs Xcode's GUI. If the user runs the GUI step, update this line with the
   result.

## Findings for other tasks

- **Task 9 (`apple-performance`).** `SKILL.md:37` and
  `references/profiling-workflow.md:67,233` say that `xctrace record` exits 54
  on success, and advise trusting the printed completion line instead. A target
  that exits non-zero also produces exit 54 and the same completion lines
  ("Target app exited, ending recording... Recording completed."). The
  launched-process element in `export --toc` is the reliable verdict. These
  files are outside this task's scope, so they were not edited.
- **Task 9 (`sim`).** `sim --ticks <n> [--slow]` is built to the brief's
  interface:
  - one `frame` interval per iteration, holding one `tick` interval;
  - signposter subsystem `dev.frenchfultonjr.apple-studio.metal-probe`,
    category `.pointsOfInterest`;
  - `plantedSlowStep` is `@inline(never)`, quadratic over 512 particles, about
    0.2 ms per tick, and present in the release binary's symbols.
- **An unexplained failure.** In one R3 pass, both recordings returned 54, and
  the Game Performance toc showed MetalProbe ending with `exit(1)`. The cause is
  not known, because xctrace does not pass stderr through. Seven later runs,
  with and without `--target-stdout`, ended `exit(0)` with all 100,000 frames
  and the right pixel. The probe now reports its errors on stdout as well.
- **The capture-scope crash** (an `MTL4CommandQueue` scope as `captureObject`)
  was not re-run. The probe follows the reference's recommended device-scope
  code.
- **Reused command buffers.** The three `encodeLabelledFrame` command buffers
  appear in the trace as "MTL4CommandBuffer 1" and the compute one as
  "MTL4CommandBuffer 2". This agrees with the reference's advice to put the
  frame number in a debug group.

## The GUI step (not runtime-checked)

This tests the reference's inference that GPU Frame Capture must be set to
Metal, not Automatically, for an External Build System target. It also attaches
Xcode's GPU tools to a binary that Xcode did not compile. The hosts render one
frame and exit, so the test uses the host's own `--capture` report rather than
the Capture button.

1. Open `authoring/apple-studio/pipeline/fixtures/metal-probe/ExternalHosts.xcodeproj` in Xcode 27.1.
2. Select the **RustHost** scheme, then **Product > Scheme > Edit Scheme…**.
3. **Run > Info > Executable**: choose **Other…**, then
   `rust/target/debug/rust-host`. The Run action builds Debug, so
   `xcode-cargo.sh Debug` runs `cargo build`. Product > Build once first, so
   that the file exists.
4. **Run > Arguments > Arguments Passed On Launch**: add `--capture` and
   `/tmp/xcode-gui-check.gputrace`, as two entries. Make sure that
   `MTL_CAPTURE_ENABLED` is not set under Environment Variables.
5. **Run > Options > GPU Frame Capture**: choose **Automatically**. Click
   **Product > Run**. In the console, note whether the host prints
   `capture started` or `capture unavailable`.
6. Set **GPU Frame Capture** to **Metal**. Delete
   `/tmp/xcode-gui-check.gputrace` and run again. Note the line again, and
   whether the debugger attached (the Debug navigator shows the process).
7. Open `/tmp/xcode-gui-check.gputrace` in Xcode, and check that the Metal
   debugger shows one command buffer with one render encoder.
8. Optional: repeat steps 2 to 6 with the **CppHost** scheme and
   `cpp/build/cpp-host`.

`capture started` with Metal and `capture unavailable` with Automatically would
confirm the reference's inference. Any other result means that
`cpp-and-rust.md` § Hosting the build in Xcode must change. If the user does
not run these steps, the claim ships as now worded: not runtime-checked (GUI).

## Clean state

- `pgrep -fl 'MetalProbe|cpp-host|rust-host'` prints nothing. No `gpudebug` or
  `GPUToolsDebugService` process remains.
- `git -C ~/Projects/StudioFixture status --porcelain` is empty.
- `xcrun simctl list devices booted` lists no device.
- The traces kept under `$TMP` are listed in `../README.md`.

## Verification

- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: exit 0, 0 errors, 55 warnings, none about apple-metal.
- `claude plugin validate . --strict`: passed.
- `check_verbatim.py`: all 12 pasted blocks match.
