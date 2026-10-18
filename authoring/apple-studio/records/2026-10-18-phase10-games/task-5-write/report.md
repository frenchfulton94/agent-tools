# Task 5 report: the apple-metal skill

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. The controller wrote
this file from the finisher's returned text, because the harness refused the
finisher's Write of it (SDD ruling P10).

Nine writers each wrote one reference and its claims sidecar
(`<stem>.sources.tsv`). Each writer read in full the symbol pages behind its
behavioral claims, and ran both gates on its own file until they were clean.
The finisher then added the skill files and the routing edits.

## References

There are nine files, as spec Deliverable 1 lists them. None was merged or
split. Line counts include the Contents lists described below.

| File | Lines | Swift blocks | Native blocks | Native target |
|---|---:|---:|---:|---|
| `apple-gpu-tbdr.md` | 678 | 7 | 3 | `-std=metal4.0` |
| `command-model.md` | 750 | 8 | 1 | `-std=metal4.0` |
| `compute-and-gpu-driven.md` | 893 | 9 | 4 | `-std=metal4.0` |
| `cpp-and-rust.md` | 767 | 0 | 6 | metal-cpp 26.4 with `-std=c++20`; cargo check with objc2 0.6.5, objc2-foundation 0.3.2, objc2-metal 0.3.2 |
| `display-and-upscaling.md` | 632 | 6 | 1 | `-std=metal4.0` |
| `gpu-debugging-and-profiling.md` | 787 | 9 | 1 | `-std=metal4.0` |
| `pipelines-and-render-passes.md` | 852 | 10 | 2 | `-std=metal4.0` |
| `resources-and-memory.md` | 680 | 9 | 2 | `-std=metal4.0` |
| `shading-language.md` | 676 | 4 | 7 | `-std=metal4.1` |
| **Total** | **6,715** | **62** | **27** | |

The Swift gate targets `macos 26.0` for every file. `display-and-upscaling.md`
targets `macos 26.0, ios 26.0`.

## Gates

- `typecheck.log`: `typecheck_snippets.py` over all nine files. Exit 0,
  `TOTAL: 62/62 snippets typecheck clean`.
- `native.log`: `typecheck_native.py` over all nine files. Exit 0,
  `TOTAL: 27/27 snippets compile clean`.

## Runtime checks the writers ran

The writers ran these themselves, beyond the compile gates, on an M4 Pro with
macOS 27.0.1. Each reference labels the results "Measured", or as an
inference where it is one.

- `command-model.md`:
  - The `## Frame structure` code, pasted verbatim, rendered 120 offscreen
    frames and read back the expected pixel.
  - Both API Validation and Shader Validation stayed clean during that run.
- `gpu-debugging-and-profiling.md`:
  - Every documented `gpudebug`, `gpucapture`, `xctrace`, and
    `metal-dsymutil` command ran here.
  - Passing a capture scope made from an `MTL4CommandQueue` to `startCapture`
    crashes (`-[MTLCaptureScope traceStream]: unrecognized selector`). A
    device scope works.
- `cpp-and-rust.md`:
  - The metal-cpp host and the objc2-metal host both render.
  - Both write a `.gputrace` that `gpudebug` opens.
  - Both reproduced the same capture-scope crash.
- `pipelines-and-render-passes.md`:
  - A depth-only pipeline needs rasterization left on, although the docs say
    to turn it off.
  - `MTL4PipelineDataSetSerializer` writes an archive only when
    `captureDescriptors` is exactly `.captureBinaries`.
  - An archive built for macOS 26.0 failed to open on macOS 27.0.1.
- `shading-language.md`: a fresh `MTLCompileOptions` reads `.fast`, where the
  doc page says `.relaxed`.
- `resources-and-memory.md`: placement sparse textures work, and
  `recommendedMaxWorkingSetSize` reads 37.4 GiB on a 48 GB machine.

## Contents lists (ruling P28)

All nine references are over 300 lines. Each now has a Contents list of its
`##` sections directly under its title, ending by line 25. Nothing else in the
references changed.

## Skill files

- `SKILL.md`, 112 lines: a scope line, one routing line per reference, the
  symptom split as rules, the Metal 4-or-3 rule, and ten "Rules that always
  apply". Each rule restates a finding from a reference.
- `evals/triggers.md`: 8 should-fire and 6 should-not rows, all phrased as
  how-to questions.

## Routing and catalog edits

- `apple-animations/SKILL.md`: one routing line. Shaders in an engine's Metal
  pipeline go to apple-metal; SwiftUI shader modifiers stay in
  apple-animations.
- The root `README.md` skills column and the `plugins/apple-studio/README.md`
  Components table now list `apple-metal`.
- `reviewing-code-security/evals/manifest.json` now lists `apple-metal` under
  `acknowledgedOmissions` (ruling P4).

## Whole-skill verification

- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: exit 0, 0 errors, 55 warnings, none of them about
  apple-metal.
- `claude plugin validate . --strict`: passed.

## Open items carried to the task review

- The description names `apple-games` in a form the
  catalog-integrity test does not match. `apple-games` does not exist yet.
  The controller has ruled that the description name no unshipped skill
  (ruling P29).
- Cross-skill paths are inconsistent. `display-and-upscaling.md` writes
  `apple-games/game-loop-and-threading.md`, while the catalog convention is
  `<skill>/references/<file>.md` (ruling P30).
- `command-model.md` says `display-and-upscaling.md` covers frame pacing,
  while `display-and-upscaling.md` gives frame pacing to apple-games.
