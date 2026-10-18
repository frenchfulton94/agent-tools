# Task 6 report: runtime probe R1, R2, R3, R5

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Machine: Apple M4 Pro,
macOS 27.0.1 (26A434), Xcode 27.1. The controller wrote this file from the
implementer's returned text, because the harness refused the implementer's
Write of it (SDD ruling P10). Fix round 1 corrected it (ruling P35). The probe
commit is `15e4ca8`, and the fix round is `65e1692`.

The fixture is `authoring/apple-studio/pipeline/fixtures/metal-probe/`.
`run.sh r1|r2|r3|r5` reproduces each log in this directory. `check_verbatim.py`
diffs every pasted block against its reference. It removes the lines that the
probe adds, which are marked `// probe` or `# probe`. It exits 0 at this commit.

Ruling P34 applies: each runtime-checked claim in an edited reference appears,
at the stated value, in one of these logs. The "as previously written" sections
of `r2.log` and `r5.log` run the reference text from `6c6d834`, the last commit
before Task 6. They log the failure behind each fix.

## Claims

| R | Claim | Verdict | Evidence |
|---|---|---|---|
| R1 | `command-model.md` § Frame structure runs as written | **Pass.** `render --frames 120` exits 0 with 120 `frame <i> ok` lines and `pixel 119 128 64 255`, which is the last frame's `SIMD4(119/255, 0.5, 0.25, 1)`. The run is the same with `MTL_DEBUG_LAYER=1 MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1`: only the two "Validation Enabled" lines, and no report. | `r1.log` |
| R2 | Programmatic capture writes a trace that `gpudebug` can open and query | **Fails as written. Passes after a reference fix.** `MTL_CAPTURE_ENABLED=1 MetalProbe capture --out $TMP/probe.gputrace` exits 0. Without the variable it exits 1 with "Capture layer is not inserted." The Sessions block, run verbatim, lists cb0 to cb3, `find opaque` finds the three groups, the draw path resolves, and `fetch` writes `draw0.png`. The pre-fix profiling block leaves every `/performance` list `(empty)`. The fixed block ranks `draw0` to `draw2` and `disp0`, and the heatmap `fetch` writes `cost.png` and the JSON. `find add arrays` reaches `commands/cb3/grp0/ce0/disp0`. | `r2.log` |
| R3 | `xctrace` records the probe with Metal System Trace and Game Performance | **Game Performance passes as specified. Metal System Trace fails as specified, and passes for short recordings. The reference is amended.** Game Performance with the brief's command: `record` exits 0, the target ends `exit(0)` after all 100,000 frames, the toc lists 48 GPU and Metal tables, and the submission rows belong to MetalProbe. Metal System Trace with the brief's command: the recording completes, then `xctrace export --toc` crashes with SIGBUS (exit 138), on both attempts. With `--time-limit 1s`, `record` exits 54, the toc shows the target `SIGKILL`ed, and it lists 48 tables. | `r3-toc.log` |
| R5 | The external hosts build from Xcode and capture outside it | **The command-line parts pass after a reference fix. Attaching Xcode's GPU debugger: not runtime-checked (GUI).** `xcodebuild -list` shows CppHost and RustHost. Clean and build succeed for both `PBXLegacyTarget`s (`/bin/sh build.sh`, `/bin/sh xcode-cargo.sh Release`). The pre-fix argument string fails, unquoted and quoted. Both hosts print `pixel 255 0 0 255` and stay clean under both validation layers. `--capture` writes a `.gputrace` only with `MTL_CAPTURE_ENABLED=1`, and `gpudebug` lists cb0/re0 in it. Metal System Trace records each host: the target ends `exit(0)`, the toc lists 48 tables, and there is one submission row. | `r5.log` |

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
  - The `gpudebug` blocks are read at run time, from the reference and, for the
    pre-fix block, from git, and run with `bash -v`. Only the trace name is
    changed.
- **R3.** The brief's commands, plus `--target-stdout`, so that the probe's
  output reaches the log. A failed export gets a second attempt. A third run
  uses `--time-limit 1s` on a render too long to finish. Time Profiler runs on
  `/usr/bin/true` and `/usr/bin/false`, and on a shell that writes one line to
  stdout and one to stderr, check the exit status and the output streams.
- **R5.** The hosts are the reference's `main.cpp` and `main.rs` with marked
  probe lines: `--capture` parsing, plus the reference's `startTrace` and
  `start_trace` helpers, called where their comments say. `Cargo.toml` is the
  reference's plus a `[[bin]] name = "rust-host"`. `Cargo.lock` is committed.
  The C++ host builds with `clang++ -std=c++20` against `$TMP/metal-cpp/26.4`,
  with no CMake. The pre-fix check runs throwaway copies of the project, under
  `$TMP/r5-pre-fix/`, with the `6c6d834` script and argument string.

## Reference changes

All changes are minimal. Both gates exit 0 on each edited file and on all nine
references: Swift 62/62 and native 27/27 (`typecheck.log` and `native.log`).

`gpu-debugging-and-profiling.md`:

1. **Profiling from the terminal.** The block now runs `profile run --embed`,
   ends the session, opens a new one, and runs `profile load` before the
   `/performance` commands. Its comments no longer carry timings.
   - `r2.log`, pre-fix section: after a plain `profile run` ("Profile data
     collected"), every `go` into `/performance` prints `'commands' has no info`,
     and the lists are `(empty)`. A same-session `profile load` answers "Profile
     data already loaded.", and the lists stay `(empty)`.
   - Unlogged observations: the same empty lists came from the Task 5 writers'
     `draw.swift` probe, rebuilt from `task-5-write/runtime/`, from a draw-only
     capture, and after `--embed` within the same session.
2. **Trap replaced.** "Under `/performance`, go one level at a time" was a
   misreading. `'commands' has no info` means that no profile is loaded. In
   `r2.log`, one-step `go /performance/commands` fails before a profile is
   loaded and lists the draws and the dispatch after one is loaded.
3. **New trap: compile pipelines before the capture starts.**
   - `r2.log`, last sections: when the capture recorded an `MTL4Compiler`
     compute-pipeline compile, `list`, `find`, `info`, and `fetch` still worked.
     `profile run` had not returned after 120 s, and a new GPUToolsReplayService
     crash report shows `EXC_BAD_ACCESS` in
     `MakeMTL4PipelineStageDynamicLinkingDescriptor`.
   - With the pipeline compiled before the capture starts, the same frames
     profile normally (the fixed block in the same log). The reference states no
     timing.
   - Unlogged observation: the hang also occurred with the compiler overload
     that takes no `dynamicLinkingDescriptor`.
4. **Instruments.** Three new points, each in `r3-toc.log`:
   - Keep Metal System Trace recordings short. Export of a 100,000-frame
     Metal System Trace recording crashed with SIGBUS twice. A 1 s
     Metal System Trace recording and a 100,000-frame Game Performance recording
     exported. The reference states no sizes.
   - Exit 54 does not mean that the target succeeded. `record` returned 54 when
     xctrace killed the target at the time limit (`SIGKILL` in the toc) and when
     the target exited non-zero (`/usr/bin/false`, `exit(1)`). It returned 0 when
     the target exited 0. Read the launched `<process>` element in the toc.
   - Pass `--target-stdout <file>` to keep the target's output. Without it,
     xctrace showed neither the target's stdout nor its stderr. With it, the file
     received both. This corrects the earlier text, which said that stderr is
     never passed through.
   - The pointer to `apple-performance` no longer cites exit 54.
5. **`:d` link trap.** `/performance/commands/draw0` links to
   `/commands/cb2/.../draw0` in this three-frame trace (`r2.log`). The text said
   `cb1`.

`cpp-and-rust.md`:

6. **External Build System arguments.** `r5.log` shows the following.
   - `xcodebuild build` exports `ACTION` as empty, and `clean` exports
     `ACTION=clean`.
   - The pre-fix `xcode-cargo.sh $(ACTION) $(CONFIGURATION)`, unquoted and with
     `\"$(ACTION)\"`, ran `/bin/sh …/xcode-cargo.sh Release` and failed with
     "does not handle the action 'Release'". So the empty value drops out even
     when quoted.
   - The arguments are now `xcode-cargo.sh $(CONFIGURATION) $(ACTION)`, and the
     script reads `config` from `$1` and `action` from `$2`. The template
     sentence now says that a build runs plain `make`, not `make build`.
7. **Verification sentence.** `xcodebuild` builds and cleans through the target
   (`r5.log`). From a shell, `xcode-cargo.sh Release install` and a run with no
   cargo on PATH each exit 1 with their message (`r5.log`).
8. **GPU Frame Capture.** "That reasoning is an inference; runtime probe R5
   checks it" now says that the inference is not runtime-checked, because the
   check needs Xcode's GUI. If the user runs the GUI step, update this line with
   the result.

## Findings for other tasks

- **Task 9 (`apple-performance`).** `SKILL.md:37` and
  `references/profiling-workflow.md:67,233` say that `xctrace record` exits 54
  on success, and advise trusting the printed completion line instead.
  `r3-toc.log` shows `/usr/bin/false` giving exit 54 with the same completion
  lines as `/usr/bin/true`: "Target app exited, ending recording...",
  "Recording completed. Saving output file...". It also shows a time-limit run
  giving 54 because xctrace killed the target. The launched-process element in
  `export --toc` is the reliable verdict.
  - The `15e4ca8` version of `r3-toc.log` also has a Game Performance run that
    printed "Reached specified time limit" and still exited 0, with the target
    ending `exit(0)`.
  - These files are outside this task's scope, so they were not edited.
- **Task 9 (`sim`).** `sim --ticks <n> [--slow]` is built to the brief's
  interface:
  - one `frame` interval per iteration, holding one `tick` interval;
  - signposter subsystem `dev.frenchfultonjr.apple-studio.metal-probe`,
    category `.pointsOfInterest`;
  - `plantedSlowStep` is `@inline(never)` and quadratic over 512 particles.
  - `r1.log` shows 200 slow ticks in 0.03 s wall time, 2,000 normal ticks in
    under 0.01 s, and the symbol in the release binary.
- **An unexplained failure (unlogged).** In one R3 pass, whose log was later
  overwritten, both recordings returned 54, and the Game Performance toc showed
  MetalProbe ending with `exit(1)`. That run had no `--target-stdout`, so the
  probe's message was lost. Seven later runs ended `exit(0)`. Every R3 run now
  uses `--target-stdout`, and the probe also writes its errors to stdout.
- **The capture-scope crash** (an `MTL4CommandQueue` scope as `captureObject`)
  was not re-run. The probe follows the reference's recommended device-scope
  code.
- **Reused command buffers.** The three `encodeLabelledFrame` command buffers
  appear in the trace as "MTL4CommandBuffer 1" and the compute one as
  "MTL4CommandBuffer 2" (`r2.log`). This agrees with the reference's advice to
  put the frame number in a debug group.

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
