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
| `apple-gpu-tbdr.md` | 672 | 7 | 3 | `-std=metal4.0` |
| `command-model.md` | 764 | 8 | 1 | `-std=metal4.0` |
| `compute-and-gpu-driven.md` | 886 | 9 | 4 | `-std=metal4.0` |
| `cpp-and-rust.md` | 773 | 0 | 6 | metal-cpp 26.4 with `-std=c++20`; cargo check with objc2 0.6.5, objc2-foundation 0.3.2, objc2-metal 0.3.2 |
| `display-and-upscaling.md` | 658 | 6 | 1 | `-std=metal4.0` |
| `gpu-debugging-and-profiling.md` | 780 | 9 | 1 | `-std=metal4.0` |
| `pipelines-and-render-passes.md` | 845 | 10 | 2 | `-std=metal4.0` |
| `resources-and-memory.md` | 667 | 9 | 2 | `-std=metal4.0` |
| `shading-language.md` | 666 | 4 | 7 | `-std=metal4.1` |
| **Total** | **6,711** | **62** | **27** | |

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

## Task review and fix round 1

The opus task review traced 27 claims: 25 were supported and 2 misstated,
with none unsupported. It checked 16 symbols named in prose against the SDK,
and all 16 exist. It found no invented API. Fix round 1 (`df65d1a`) made these
changes:

- **Shader Validation claims.** Two claims said Shader Validation stayed
  silent when an attachment was missing from every residency set. It does not
  stay silent: it reports to the unified log, and also to stderr when
  `MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1` is set. All files now agree, and
  pair the two environment variables. The probes were re-run before the text
  changed.
- **No pointers to an unshipped skill** (ruling P29). The description and
  body name no skill for frame pacing, input, audio, or Game Center. The SDD
  ledger lists each location, so that Task 8 can restore the `apple-games`
  pointers.
- **Contradictions resolved:**
  - Gate on Apple GPU families (`.apple7` and later), `.metal4`, and per-feature properties, not on the Mac family: the SDK deprecates `.mac2` in favor of `.apple7`.
  - Drawable and present mechanics belong to `display-and-upscaling.md`.
    Frame pacing policy is outside this skill.
- **Cross-skill pointers** use the form `<skill>/references/<file>.md`
  (ruling P30).
- **About 70 lines of duplication and generic material cut.**
- **Four snippets corrected** (ruling P31):
  - a renderer that committed a command buffer it never began;
  - an early return that left a debug group pushed;
  - dispatch sizing that depended on a pinned value. That value reads back
    as zero when only the MSL attribute pins it (measured).
  - OS 27-only pipeline properties, now gated.
- **Runtime evidence** for every "Measured" claim is now in
  `runtime/<stem>/runs.txt`: commands, key output, machine, and OS (ruling
  P32).

## Fix round 2

Commit `9792a9f` fixed two more problems:

- **Silent wrong dispatch size.** The dispatch helper's fallback sized a
  threadgroup as 32×8 for a kernel that the MSL attribute pins to 16×16, and
  neither validation layer reported it (measured). The helper now requires
  the pin on the pipeline descriptor, and calls `precondition` when it is
  missing. Kernels that pin nothing keep the fallback; the docs label it for
  that case only.
- **Unreadable log.** The guidance said to read Shader Validation reports
  with `log stream`, but the log replaces the report text with `<private>`.
  The guidance now says to set `MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1`.

The evidence is in `runtime/compute-and-gpu-driven/runs.txt`.
