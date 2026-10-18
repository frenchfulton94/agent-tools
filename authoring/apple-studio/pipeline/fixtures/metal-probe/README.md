# metal-probe

Runtime checks for the `apple-metal` references (Phase 10, Task 6: claims R1,
R2, R3, and R5). The probe runs reference code as the references print it, on a
real GPU. Where the probe and a reference disagree, the probe wins, and the
reference changes. The evidence is in
`authoring/apple-studio/records/2026-10-18-phase10-games/task-6-probe/`.

Requirements: an Apple-silicon Mac with a Metal 4 GPU, macOS 26 or later,
Xcode, and rustup's cargo. CMake is not used. Nothing here is installed.

## What is here

| Path | What it is |
|---|---|
| `Package.swift`, `Sources/MetalProbe/` | `MetalProbe`, a SwiftPM executable for macOS 26.0 |
| `Sources/MetalProbe/Reference/` | Swift blocks from `command-model.md` and `gpu-debugging-and-profiling.md` |
| `cpp/main.cpp`, `cpp/capture.cpp`, `cpp/build.sh` | The metal-cpp host, `cpp-host`, from `cpp-and-rust.md` |
| `rust/` | The objc2-metal host, `rust-host`, from `cpp-and-rust.md`, with its `Cargo.lock` |
| `ExternalHosts.xcodeproj` | Two External Build System (`PBXLegacyTarget`) targets: `CppHost` runs `build.sh`, and `RustHost` runs `xcode-cargo.sh` |
| `check_verbatim.py` | Checks that the pasted blocks still match the references |
| `run.sh` | Runs one claim and prints its log |

## Pasted blocks

Each file under `Sources/MetalProbe/Reference/`, `cpp/main.cpp`,
`cpp/capture.cpp`, `rust/Cargo.toml`, `rust/src/`, and `rust/xcode-cargo.sh`
holds exactly one fenced block from a reference. The lines that the probe adds
end with `// probe` or `# probe`: imports that the compile gate supplies, the
command-line options, and the one `drawOpaque` hook that fills the
"Opaque draws go here" placeholder in `encodeLabelledFrame`.

```bash
python3 check_verbatim.py    # exit 0: every pasted block matches its reference
```

Run it after any edit to a reference. A `DRIFT` line means that the probe no
longer tests what the reference says. Copy the block again, keep the probe
lines, and run the claim again.

## MetalProbe

```bash
swift build -c release
.build/release/MetalProbe render --frames 120        # "frame <i> ok" per frame, then "pixel r g b a"
.build/release/MetalProbe compute --count 1048576    # "compute ok <n>" when sum == a + b everywhere
MTL_CAPTURE_ENABLED=1 .build/release/MetalProbe capture --out "$PWD/../../tmp/probe.gputrace"
.build/release/MetalProbe sim --ticks 1000 [--slow]  # CPU only; OSSignposter "frame" and "tick" intervals
```

- `render` runs `renderOffscreen` from `command-model.md` § Frame structure
  into a 64 × 64 `.rgba8Unorm` shared target, and reads back the center
  pixel. It exits 1 if the pixel is not the color that the last frame sets.
- `capture` makes the reference's device capture scope (`FrameCapture`), and
  records three `encodeLabelledFrame` frames and one compute dispatch between
  `begin()` and `end()`. The compute pipeline is compiled before the capture
  starts. `--compile-in-capture` compiles it inside the capture instead, which
  makes `gpudebug`'s `profile run` hang (see the Task 6 report).
  `--no-compute` leaves the dispatch out.
- `sim` is the CPU workload for Task 9. Each frame is one `frame` interval
  that holds one `tick` interval, under the subsystem
  `dev.frenchfultonjr.apple-studio.metal-probe` and the Points of Interest
  category. `--slow` sends every tick through `plantedSlowStep()`, which is
  quadratic in the particle count and is marked `@inline(never)`.

## The hosts

```bash
sh cpp/build.sh                                          # build/cpp-host, with clang++ -std=c++20
(cd rust && cargo build --release)                       # target/release/rust-host
xcodebuild -project ExternalHosts.xcodeproj -target CppHost build
xcodebuild -project ExternalHosts.xcodeproj -target RustHost build
MTL_CAPTURE_ENABLED=1 cpp/build/cpp-host --capture "$PWD/frame.gputrace"
```

Each host renders one offscreen frame and prints `pixel …`. With
`--capture <path>`, a host wraps the frame in the reference's device-scope
capture helper. Without `MTL_CAPTURE_ENABLED=1`, it prints
`capture unavailable` and writes nothing.

`build.sh` reads metal-cpp 26.4 from `authoring/apple-studio/pipeline/tmp/`.
When the headers are missing, it runs `fetch_metal_cpp.sh 26.4`, which is a
pinned, hash-checked download.

## Running the claims

```bash
swift build -c release && sh cpp/build.sh && (cd rust && cargo build --release)
./run.sh r1    # Frame structure, 120 frames, with and without validation
./run.sh r2    # programmatic capture, then the gpudebug blocks, verbatim
./run.sh r3    # xctrace, Metal System Trace and Game Performance
./run.sh r5    # External Build System targets, both hosts, capture, xctrace
```

Traces go to `authoring/apple-studio/pipeline/tmp/`, which is gitignored.
`.build/`, `build/`, `target/`, `*.gputrace/`, and `*.trace/` are ignored here
as well.

The one step that no script can run is attaching Xcode's GPU debugger to a
binary that Xcode did not build. The Task 6 report gives the manual steps.
