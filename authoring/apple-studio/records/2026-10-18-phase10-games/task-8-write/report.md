# Task 8 report: the apple-games skill

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Commits: `408b1df` (the skill), `911dc44` (this report, written by the controller), and `2c9f786` (fix round 1). The controller writes this file from the finisher's returned text (ruling P10).

Six writers each wrote one reference and its claims sidecar (`<stem>.sources.tsv`), ran the runtime checks they cite, and ran both gates on their own file until they were clean. The finisher then wrote the skill files, made the routing and catalog edits and the apple-metal restorations, gated, verified, and committed.

## References

There are six files, as spec Deliverable 2 lists them. None was merged or split. Line counts are after fix round 1.

| File | Lines | Swift blocks | Native blocks | Swift target | Native target |
|---|---:|---:|---:|---|---|
| `assets.md` | 583 | 6 | 0 | `macos 26.0` | — |
| `audio-and-haptics.md` | 910 | 7 | 3 | `macos 26.0, ios 26.0` | metal-cpp 26.4, `-std=c++20` |
| `game-center-and-online.md` | 678 | 9 | 1 | `macos 26.0` | metal-cpp 26.4, `-std=c++20` |
| `game-design.md` | 599 | 5 | 0 | `macos 26.0, ios 26.0` | — |
| `game-loop-and-threading.md` | 916 | 12 | 0 | `macos 26.0, ios 26.0` | — |
| `input.md` | 658 | 11 | 0 | `macos 26.0, ios 26.0` | — |
| **Total** | **4,344** | **50** | **4** | | |

As the brief requires, `game-loop-and-threading.md` and `input.md` declare `> typecheck: macos 26.0, ios 26.0`. Every file is over 300 lines and has a Contents list near its top.

## Gates

- `typecheck.log`: `typecheck_snippets.py` over all six files. Exit 0, `TOTAL: 50/50 snippets typecheck clean`. It was re-run after fix round 1.
- `native.log`: `typecheck_native.py` over all six files. Exit 0, `TOTAL: 4/4 snippets compile clean`. It was re-run after fix round 1.
- The edited apple-metal files (`display-and-upscaling.md`, `gpu-debugging-and-profiling.md`, `command-model.md`), re-gated:
  - Swift 23/23 clean, exit 0.
  - Native 3/3 clean, exit 0.
  - `pipeline/fixtures/metal-probe/check_verbatim.py` passes 12 of 12, exit 0.

## Runtime-check index

All runs used one Apple M4 Pro MacBook Pro (Mac16,8, with a Force Touch trackpad), macOS 27.0.1 (26A434), Xcode 27.1, and the MacOSX 27.0 SDK. No simulator was booted, no process was left running, and StudioFixture was not touched. Each log records its commands, the key output, and the machine.

- `runtime/game-loop-and-threading/runs.txt`:
  - §1 the mach timebase on native arm64 (125/3 ns per tick) and under Rosetta (1/1).
  - §2 the Metal 3 completed-handler thread and its QoS.
  - §3 raw priority 45 against QoS. A thread made with the priority-45 recipe reports `QOS_CLASS_UNSPECIFIED`.
  - §4 Foundation `Thread` QoS. A new `Thread` runs at `.default`; setting `.userInteractive` before `start()` holds.
  - §5 power, thermal, and performance-profile reads.
  - §6 the core-count sysctl keys. `hw.nperflevels` exists; `hw.perflevels` does not.
- `runtime/input/runs.txt`:
  - On macOS, `GCController.shouldMonitorBackgroundEvents` defaults to `false` at the 26.0 floor.
  - The Swift spelling `controller.input.unmapped` builds.
- `runtime/audio-and-haptics/runs.txt`, which `run.sh` reproduces:
  - §1 and §1b: vDSP real-FFT scaling (forward ×2, inverse ×n), and which DFT lengths are accepted.
  - §2–2g: `CA_REALTIME_API` violations are silent under the default flags and warn under `-Wfunction-effects`. The reference's `GainKernel` produces zero warnings.
  - §3: on the MacBook Pro, despite its Force Touch trackpad, `supportsHaptics=false`, and `CHHapticEngine()` throws -4809. A machine-model block (`system_profiler`) and a re-run of §3 were added in fix round 1.
- `runtime/game-center-and-online/runs.txt`: the GameKit party-code alphabet (20 characters) and the format validation.
- `runtime/assets/runs.txt`:
  - §1 Compression: which algorithms the stream API accepts, decode truncation, small-input encode, and ratio and throughput.
  - §2 the UTIs that game-asset extensions resolve to.
  - §3 KTX against KTX2 through `MTKTextureLoader`, at `--compression_quality=Normal`.
  - §4 AppleArchive.
  - §5 Model I/O import and export by extension.
  - §6 a read-only read of the Background Assets tool help.
  - §7 extra snippet compiles in Swift 6 mode.
- `runtime/game-design/runs.txt`:
  - On macOS, SwiftUI `.dynamicTypeSize(_:)` does not change how `.body` or `.title` renders.
  - Conforming an `NSAccessibilityElement` subclass to `NSAccessibilityButton` does not compile against the macOS 27 SDK.

GUI-only claims are labelled "not runtime-checked (GUI)" in the references: the Metal HUD's Game Mode indicator, a VoiceOver pass, and whether a live resize is a run-loop mode. So is the Developer ID column, because this machine has no Developer ID identity.

## Doc-vs-SDK disagreements resolved, per file

In every case the SDK or the runtime result wins, and the reference says so.

- **`game-loop-and-threading.md`:**
  - Apple's custom-view and Accelerate cube samples use the deprecated `CVDisplayLink`. The custom-view sample's claim that `CADisplayLink` is unavailable on macOS has been stale since macOS 14.
  - The Metal performance article recommends priority 45, and the Apple-silicon guide recommends QoS. The two are exclusive (runtime §3). The reference defaults to QoS.
  - The article names `hw.perflevels`; the SDK key is `hw.nperflevels`.
  - `GCSupportsGameMode` is the old key and `LSSupportsGameMode` is the current one. Xcode 27.1 writes only the old one.
- **`input.md`:** `GCDeviceHaptics.h` declares macOS 11. Apple's Core Haptics sample for controllers lists only iOS. The Mac does get controller haptics.
- **`audio-and-haptics.md`:**
  - The Audio Queue page's "all new development" line is stale.
  - `PHASEEngine.RenderingMode` is visionOS 26 only, although its page lists iOS.
  - The `vDSP.h` pseudocode is wrong about the inverse-FFT scale. The data-packing article and runtime §1 agree with each other.
  - The HIG pages, the article, the overview, and the headers disagree on which platforms have haptics. The headers settle it.
  - Two pages disagree on biquad filter form.
- **`game-center-and-online.md`:**
  - `GKGameCenterViewController`, `GKAccessPoint.showHighlights`, and the `.challenges` state are deprecated in the 26 SDKs, although pages and samples still use them.
  - `GKScore` (deprecated in iOS 14 and macOS 11) and the two old view controllers (deprecated in iOS 7 and macOS 10.10) are still in the SDK.
  - The Swift `DTLS` type is OS 27, not OS 26.
  - The class and instance `submitScore` behave differently on an occurrence that has ended.
  - The matchmaking articles have two errors: the thresholds array comes before the ages array, and the party-code rule uses the `/v1/gameCenterMatchmakingRules` endpoint.
- **`assets.md`:**
  - When the destination is too small, `compression_decode_buffer` returns `dst_size`, not 0 as the article says (runtime §1).
  - The `compression_algorithm` overview calls LZRAVEN "an order of magnitude slower"; the header says that of LZMA.
  - The stream sample and the filters article name LZFSE where the symbol pages and the header prefer LZMESH for whole buffers on OS 27.
  - The compiler does not gate LZMESH or LZRAVEN; their availability is only a header comment.
  - The managed Background Assets API is OS 26, although the framework page lists iOS 16 / macOS 13.
  - On-demand resources are deprecated in iOS 27, although the GameKit large-downloads article still recommends them.
- **`game-design.md`:**
  - macOS has no Dynamic Type, and the runtime check confirms it.
  - The Custom Controls guide's `NSAccessibilityButton` conformance does not compile; the SDK wins.
  - The HIG games page and the general Buttons page give different button sizes. This is a doc-vs-doc disagreement, and the reference notes it.

## Skill files

- **`SKILL.md`, 102 lines:**
  - A scope line: Mac first, then iPhone and iPad; Apple silicon; SpriteKit, SceneKit, RealityKit, GameplayKit, Unity, Unreal, Godot, visionOS, tvOS, Apple Arcade, and engine architecture are out of scope.
  - Six routing lines, one per reference.
  - The symptom split as five rules, mirroring apple-metal's: pacing, the fixed step, threads and QoS, input, audio, Game Center, saves, and assets are here. GPU frame time and display-link mechanics go to apple-metal, CPU tick cost to apple-performance, general HIG layout to apple-design, and signing and notarization to app-release.
  - The OS floor block: 26.0 holds, OS 27 symbols are gated, and the compiler does not gate LZMESH or LZRAVEN.
  - Ten rules that always apply. They include the Developer ID rule pointing to `references/game-center-and-online.md` and the GUI-only rule, which names `ba-package` and `ba-serve` as the real command-line tools.
- **The description (998 characters; the limit is `DESC_MAX = 1024` in `authoring-skills/scripts/validate_skill.ts`):**
  - It names every term the brief requires: the Metal game loop, `CAMetalDisplayLink`, fixed-step simulation, `os_workgroup`, Game Mode, Game Controller, Touch Controller, PHASE, AVAudioEngine, Core Haptics, GameKit / Game Center, game saves, Background Assets, and the HIG for games.
  - It ends: "Not for GPU frame time or Metal code (apple-metal), CPU profiling or launch time (apple-performance), general HIG layout (apple-design), signing and notarization (app-release), or SpriteKit and third-party engine questions."
- **`evals/triggers.md`:** 8 should-fire rows and 6 should-not rows, all how-to questions, none with "build X" wording. The should-not rows are the brief's six:
  - GPU frame time (apple-metal);
  - app launch time (apple-performance);
  - SpriteKit particles;
  - a Godot GDScript gamepad handler (gdscript);
  - an adaptive settings layout (apple-design);
  - notarization (app-release).

## P29 restorations in apple-metal

- **`SKILL.md:3`:** the description now ends "…or frame pacing, input, audio, and Game Center (apple-games)." The integrity test now guards that name. The description is 960 characters.
- **`SKILL.md:50–53`:** "Frame pacing policy goes to apple-games … Fixed or variable step, frame budgets, and render-thread QoS belong to its game loop."
- **`references/display-and-upscaling.md`:**
  - Scope paragraph (lines 23–27) → `apple-games/references/game-loop-and-threading.md`.
  - The iPhone Info.plist note (lines 47–48) → the same file.
  - The "Where else to look" entry (around line 651) now opens with that path, and adds render-thread QoS.
- **`references/gpu-debugging-and-profiling.md:691`:** render-thread setup, and the choice between priority 45 and QoS, → `apple-games/references/game-loop-and-threading.md`.
- **`references/command-model.md:25–26`** (the optional one): frame pacing policy → `apple-games/references/game-loop-and-threading.md`.
- **`evals/triggers.md:24`:** the routing note is now `(apple-games — controller input)`.

## The QoS fix (parked apple-metal defect)

In `display-and-upscaling.md`, `RenderLoopThread.init` now sets `name = "Render"` and `qualityOfService = .userInteractive` after `super.init()`. A comment says that a new `Thread` otherwise runs at `.default`, which `runtime/game-loop-and-threading/runs.txt` §4 observed. The snippet compiles on both targets. The metal probe does not paste this block, so the fixture is unchanged and `check_verbatim.py` still passes. Because of the fix, `game-loop-and-threading.md:494–496` was reworded: the thread "sets it in its initializer. Set it on every render thread you create." It now uses the `apple-metal/references/…` form (P30).

## Routing and catalog edits

- **`apple-design/SKILL.md`:** "Game-specific HIG (game controls, text on a game screen, pause, Game Center presentation) → `apple-games` skill, its `game-design.md`".
- **`apple-macos/SKILL.md`:** "Hosting a Metal view for a game, Game Mode, game full screen and cursor → `apple-games` skill".
- **Neither line uses the `apple-games/references/…` form.** The skill validator's referenced-path regex would read it as a local `references/` file that does not exist, and report an error. P30's form is used inside reference files only.
- **Root `README.md`:** the apple-studio skills column lists `apple-games`, in alphabetical order.
- **`plugins/apple-studio/README.md`:** a new `apple-games` component row after `apple-metal`. Task 13 rewrites the summary text.
- **`reviewing-code-security/evals/manifest.json`:** `apple-games` is added to `acknowledgedOmissions`, in alphabetical order (ruling P4).

## Whole-skill verification

- **Vale:** 0 errors over all 17 new and edited files.
  - `SKILL.md` and `evals/triggers.md` have 0 warnings.
  - Every edited apple-metal and catalog file keeps its HEAD warning count, except `plugins/apple-studio/README.md`: 7 → 8, the same sentence-length warning as the apple-metal row.
  - The six writer-authored references carry about 105 warnings, all sentence length or core-word choice. They were not rewritten.
- **`bun test --timeout 30000`:** 542 pass, 0 fail.
- **`bun run audit`:** exit 0, 0 errors, 55 warnings, none about apple-games or apple-metal.
- **`claude plugin validate . --strict`:** passed.
- **Clean state:** no probe processes, no booted simulator, and StudioFixture is clean.

## Fix round 1

The task review returned "Needs fixes" with 2 Important and 7 Minor findings. Commit `2c9f786` made these changes:

- **I1, the haptics machine was misnamed.** The record said "Mac mini". `system_profiler` shows a MacBook Pro (Mac16,8) with a Force Touch trackpad.
  - `audio-and-haptics.md`, `SKILL.md`, `runtime/audio-and-haptics/runs.txt`, `run.sh`, and the sidecar now name it correctly.
  - The false sentence "not checked on a laptop" is cut.
  - The text now says that Core Haptics reports no haptics support despite the trackpad, and that trackpad feedback goes through `NSHapticFeedbackManager`.
  - `runs.txt` gained the `system_profiler` model lines and a re-run of §3 with the same result (P34).
  - No other runtime log had the mislabel.
- **I2, the DTLS connection leaked (P31).** The OS 26 branch of `sendOverDTLS` now awaits its send through a checked continuation and cancels the connection with `defer`. Prose now says that game traffic keeps one connection per peer. The snippet compiles.
- **M1, cross-references to missing content.** Game Center artwork sizes now point to the HIG Game Center page, not to `assets.md` or `game-design.md`. visionOS access-point placement points to GameKit's "Adding an access point to your game".
- **M2, P30 form.** Pointers into apple-metal in `game-loop-and-threading.md`, prose and code comments, and into apple-design in `game-design.md`, now use `<skill>/references/<file>.md`.
- **M3:** declined by ruling P38.
- **M4:** removed a dead `definition.leaderboards` fetch from `hostParty`.
- **M5:** "the pre-26 types are gone" is now "deprecated, but still in the SDK", with the SDK versions.
- **M6:** cut the Unity Dynamic Type sentence.
- **M7:** the KTX lead-in now states `--compression_quality=Normal`, as the log does.
- **Verification after the round:** both gates re-run (Swift 50/50, native 4/4, exit 0). Vale shows 0 errors and no warning increase on any edited file. `bun test` 542/0. Audit 0 errors and 55 warnings. `claude plugin validate . --strict` passed.
