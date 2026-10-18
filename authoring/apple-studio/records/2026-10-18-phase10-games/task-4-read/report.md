# Task 4 report: apple-metal corpus read in full

Date: 2026-10-18. Eight readers (m01 to m08) each wrote one ledger and one
notes file. A finisher ran verification and committed. The controller wrote
this file from the finisher's returned text, because the harness refused the
finisher's Write of it (SDD ruling P10).

## Result

- `check_ledger.py … --only m01,m02,m03,m04,m05,m06,m07,m08` exits 0.
- There are 322 ledger rows. 321 are `read_in_full=yes`, and one is
  unfetchable (see below).
- The field check found 0 violations. The 12-word copy check found 1 hit, a
  list of option names (see below). No notes were reworded.
- All eight readers were stopped once, mid-slice, by an API usage limit. Each
  was resumed from its own transcript. Each confirmed that every page it had
  loaded before the stop had been read to its last line (its copyright
  footer), and wrote ledger rows page by page from then on.

## Slices, pages, words

Words come from the ledgers. `field_check.py` proves they equal the manifest
and sources values.

| Slice | Pages | Words | Read in full | Unfetchable |
| ----- | ----: | ----: | -----------: | ----------: |
| m01 | 67 | 50,877 | 67 | 0 |
| m02 | 59 | 51,317 | 59 | 0 |
| m03 | 53 | 51,443 | 53 | 0 |
| m04 | 52 | 58,177 | 52 | 0 |
| m05 | 46 | 52,909 | 45 | 1 |
| m06 | 5 | 48,917 | 5 | 0 |
| m07 | 6 | 53,791 | 6 | 0 |
| m08 | 34 | 53,338 | 34 | 0 |
| Total | 322 | 420,769 | 321 | 1 |

- m06 holds MSL 4.1 chapters 1–5.
- m07 holds MSL chapters 6–9, the Feature Set Tables, and book chapter 1.
- m08 holds the rest of the *Metal by Tutorials* book skill.
- m01–m05 hold cached Apple pages. m05 also holds the MSL front matter.

## Unfetchable rows

There is one, in m05:
`/documentation/metal/compute_passes/creating_threads_and_threadgroups`.

- The `.md` URL returns HTTP 404. The bare URL redirects (301) to
  `/documentation/metal/creating-threads-and-threadgroups`, an m01 row that
  was read in full.
- The underscore spelling is a broken figure link inside Apple's own
  article, so no content is lost.
- Its ledger value is `no-unfetchable:404:deferred-19` (item 19 in
  `docs/deferred.md`).

## Bullets per destination section

The slices hold 875 bullets in destination sections. A further 11 sit in
`(none)` sections, which list pages that fed nothing.

| Destination | m01 | m02 | m03 | m04 | m05 | m06 | m07 | m08 | Total |
| ----------- | --: | --: | --: | --: | --: | --: | --: | --: | ----: |
| command-model.md | 23 | 16 | 33 | 1 | 8 | 0 | 11 | 10 | 102 |
| pipelines-and-render-passes.md | 15 | 23 | 21 | 2 | 7 | 18 | 10 | 21 | 117 |
| apple-gpu-tbdr.md | 3 | 12 | 8 | 0 | 2 | 12 | 7 | 7 | 51 |
| resources-and-memory.md | 18 | 16 | 19 | 0 | 5 | 4 | 7 | 8 | 77 |
| shading-language.md | 3 | 11 | 6 | 4 | 5 | 61 | 50 | 23 | 163 |
| compute-and-gpu-driven.md | 13 | 14 | 13 | 14 | 4 | 26 | 23 | 19 | 126 |
| display-and-upscaling.md | 8 | 9 | 5 | 5 | 4 | 0 | 3 | 3 | 37 |
| gpu-debugging-and-profiling.md | 9 | 7 | 3 | 32 | 17 | 3 | 3 | 11 | 85 |
| cpp-and-rust.md | 5 | 1 | 1 | 9 | 16 | 1 | 0 | 0 | 33 |
| apple-games/game-loop-and-threading.md | 2 | 12 | 2 | 10 | 3 | 0 | 0 | 3 | 32 |
| apple-games/input.md | 1 | 2 | 0 | 2 | 0 | 0 | 0 | 4 | 9 |
| apple-games/assets.md | 2 | 0 | 1 | 2 | 2 | 0 | 1 | 10 | 18 |
| apple-games/game-design.md | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| apple-games/game-center-and-online.md | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 3 |
| apple-performance/profiling-workflow.md | 0 | 2 | 0 | 0 | 2 | 0 | 0 | 1 | 5 |
| app-release/direct-distribution.md | 4 | 0 | 0 | 6 | 4 | 0 | 0 | 0 | 14 |
| (none) | 1 | 3 | 1 | 2 | 1 | 1 | 1 | 1 | 11 |

## Book marks

Book rows sit in m07 (chapter 1) and m08 (all other chapters). Counted by
script: 32 `differs` marks (m07 6, m08 26) and 23 `agrees`.

Nearly all `differs` marks are a Metal 3 spelling that Metal 4 replaces:

| Book (Metal 3) | Metal 4 |
| --- | --- |
| a fresh `MTLCommandBuffer` per frame | a reusable `MTL4CommandBuffer` with an `MTL4CommandAllocator` |
| `setVertexBuffer` | `MTL4ArgumentTable` |
| `useResource` | residency sets |
| `MTLRenderPipelineDescriptor` | `MTL4RenderPipelineDescriptor`, compiled by `MTL4Compiler` |
| the blit encoder | copies on `MTL4ComputeCommandEncoder` |
| tessellation | removed; mesh shaders replace it |

Three marks are limit disagreements with the Feature Set Tables (findings
23–25 below).

## Copy check

`copy_check.py` looks for runs of 12 or more consecutive words shared between
the notes and the slice's sources (`copy_check.log`). It found 1 hit and
excluded 1 run.

- **The hit** is `m04.md` line 61: the 19-word list of valid
  `MTL_HUD_ELEMENTS` values. These are exact option names, which count as
  facts. No change.
- **The excluded run** is `m07.md` line 80, a code signature.
- **Sensitivity:** at an 8-word threshold the check reports 44 overlaps.
  They are headings, sample titles, and short technical phrases.

## Field check

`field_check.py` checked 322 rows and found 0 violations (`field_check.log`).

- Every ledger `words` value equals its manifest or sources value.
- Every `fed` value is either `nothing: <reason>` or names known
  destination files.

## Findings the readers flagged for writers

Deduplicated, each with its source path. A writer must not copy the wrong
form.

### Documentation errors and stale claims

1. `/documentation/Metal/managing-groups-of-resources-with-argument-buffers`
   (m02): the prose names `MTLArgumentBufferEncoder`, but the type is
   `MTLArgumentEncoder`. It names a `gpuHandle`, but the property is
   `MTLBuffer.gpuAddress`.
2. `/documentation/Metal/manipulating-metal-binary-archives` (m02): the page
   builds `shaders.binary.metallib` and then inspects
   `render.binary.metallib`.
3. `/documentation/Metal/rendering-reflections-with-fewer-render-passes`
   (m02): the page gates with the deprecated
   `supportsFeatureSet:MTLFeatureSet_iOS_GPUFamily5_v1` and calls that check
   ICB support. Use `supportsFamily:`.
4. `/documentation/Metal/rendering-a-scene-with-deferred-lighting-in-swift`
   (m02): the single-pass snippet shows `.private`, but its own prose says
   `.memoryless`. The page also says "depth value of 128" where it means the
   stencil value.
5. `/documentation/Metal/managing-your-metal-app-window-in-ipados` (m02):
   the plist key `MyCustomSceneDelegateClass` should be
   `UISceneDelegateClassName`.
6. `/documentation/Metal/converting-between-pixel-regions-and-sparse-tile-regions`
   (m01): the page gives 128×196 where the correct value is 128×192.
7. `/documentation/Metal/encoding-indirect-command-buffers-on-the-gpu`
   (m01): the page names `executeIndirectCommandBuffer`, which does not
   exist. The method is `executeCommandsInBuffer`.
8. `/documentation/Metal/generating-and-loading-a-metal-library-symbol-file`
   (m01): the page's `-c` step produces `.air` files, but an earlier page
   calls them `.ir`.
9. `/documentation/MetalPerformanceShaders/image-filters` (m04): the
   Objective-C sample does not compile as written.
10. `/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon`
    (m05): the page's code has three errors against MSL 4.1:
    - `simd_barrier` should be `simdgroup_barrier`;
    - `mem_device` should be `mem_flags::mem_device`;
    - the MSL section cited as §6.8.1 is §6.10.1 in 4.1.
11. `/documentation/Metal/compute-passes` (m01): the page says a resource
    must be `.shared` or `.managed` to be resident for argument-buffer use.
    Check this against the `useResource` symbol page before repeating it.
12. The heaps-and-fences and terrain samples (m02, m03) still say Metal is
    unsupported in the iOS Simulator. This is stale; do not repeat it.
13. `/documentation/Metal/creating-a-custom-metal-view` (m01): the page says
    `CADisplayLink` is unavailable on macOS. Its symbol page lists macOS
    14.0+.
14. Several pages label Objective-C code as Swift, write `.familyMac2` for
    `MTLGPUFamily.mac2`, or use `fn` and a nonexistent `MTLComputePipeline`
    type in Swift (the dynamic-library and binary-archive pages, m01). The
    memoryless snippet uses `.r16Float` as a depth format, and a mip-count
    formula comes out one level short.

### Contradictions between pages and the SDK

15. `/documentation/Xcode/Reducing-shader-bottlenecks` with
    `/documentation/Xcode/build-settings-reference` (m04): the article says
    to opt in to fast math, but `MTL_FAST_MATH` already defaults to `YES`
    (`MTL_MATH_MODE = FAST`). The real choice is SAFE or PRECISE.
16. `CALayer.h` and `CAMetalLayer.h` (m04): `CALayer`'s
    `wantsExtendedDynamicRangeContent` is deprecated at OS 26 in favor of
    `preferredDynamicRange`. `CAMetalLayer`'s own property is not
    deprecated.
17. `/documentation/metalfx` (m05): availability differs between the
    framework page and the symbol pages. Gate MetalFX per symbol.
18. API Validation's unretained-resource check covers `MTLCommandBuffer`
    only, not `MTL4CommandBuffer` (m05). The programmatic-capture page shows
    Metal 3 types only, but `makeCaptureScope(commandQueue:)` has an
    `MTL4CommandQueue` overload (m04, m05).
19. MPS image kernels and `MPSMatrixMultiplication` encode only onto a
    Metal 3 `MTLCommandBuffer`. Only the `MPSNDArray` kernels take an
    `MTL4ComputeCommandEncoder`, and MPSGraph runs on an `MTL4CommandQueue`
    (m04, m08). A Metal 4 renderer that needs MPS image filters needs a
    Metal 3 queue synchronized with events.

### MSL 4.1 specification errata (m06, m07)

20. In ch5, `requiredThreadsPerThreadgroup` is placed on `MTLDevice`. It is
    on `MTLComputePipelineDescriptor` and `MTL4ComputePipelineDescriptor`,
    and on the tile descriptors. The spec also writes "MTLCompilerOptions"
    for `MTLCompileOptions`.
21. ch7 misspells `matmul2d` as `matmuld2d`, and `is_compatible_as_left_input`
    as `is_compatiable_as_left_input`. The SDK header spells both correctly.
22. The ch9 appendix has no "New in Metal 4.1" section. Collect the 4.1 delta
    from the tags in the body. The spec also calls cube-texture atomics and
    ICB raster/depth-stencil state plain "Metal 4", but the Feature Set
    Tables require Apple10 for both.

### Book against the Feature Set Tables or Metal 4 (m08)

23. ch15: the book's Apple3 floor for tiled reads is stricter than the
    tables' Apple2.
24. ch19: the book gates tessellation factor 64 at Apple5; the tables say
    Apple4. Metal 4 removes tessellation in any case.
25. ch28: the book's 1,024 mesh-threadgroup limit holds only for Apple7 and
    Apple8.
26. ch07: `MTL4RenderPipelineDescriptor` has no depth or stencil pixel
    format.
27. ch24: `MTL4CommandBuffer` has no `waitUntilCompleted()`. Wait on an
    `MTLSharedEvent` instead.
28. `MTL4ArgumentTable` has no setBytes call, so the book's `setVertexBytes`
    habit has no direct port. `supportIndirectCommandBuffers` is now
    `MTL4IndirectCommandBufferSupportState`, not a Bool.

The finisher built findings 1–19 and 23–28 from keyword searches of the
notes. The controller added items from the readers' own reports: in 4, 14,
18, 19, 20, 21, 22, and 28. A flag worded differently could be missing from
this list. The notes files are the complete record.

## Bullet sampling

The task review sampled 10 bullets against their sources. Its result is in
the SDD ledger.
