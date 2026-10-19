---
name: apple-metal
description: Writing and debugging a game or engine renderer on Metal for Apple silicon - the Metal 4 command model (command allocators, argument tables, residency sets, barriers), pipeline compilation without hitches, render and compute passes, TBDR tile memory, MSL versions and precision, heaps and memory budgets, indirect command buffers, mesh shaders and ray tracing, drawables and CAMetalDisplayLink, HDR, MetalFX upscaling and frame interpolation, GPU capture, the Metal debugger, gpudebug, API and Shader Validation, Metal System Trace, and Metal from C++ through metal-cpp or from Rust through objc2-metal. Use when GPU frame time is too high, a frame renders wrong, a Metal resource or shader faults, a pipeline compile hitches, or when writing, porting, or reviewing Metal host or shader code. Not for SwiftUI shader modifiers (apple-animations), CPU-side and app-level slowness (apple-performance), or frame pacing, input, audio, and Game Center (apple-games).
---

# Metal (rendering and GPU work)

Scope: **how a game or engine drives an Apple GPU, and why a frame is wrong or
slow on the GPU.** Apple silicon only. Intel Macs, discrete GPUs, SpriteKit,
SceneKit, RealityKit, third-party engines, visionOS, and general rendering
theory are out of scope.

Read the reference for the decision at hand:
- Building the frame: queue, command buffers and allocators, argument tables,
  residency, barriers, fences, events, frames in flight, GPU errors →
  `references/command-model.md` (its `## Frame structure` is the whole frame)
- Making pipelines with `MTL4Compiler`, function constants, binary archives
  that stop compile hitches, render pass attachments, depth, stencil, MSAA,
  forward against deferred → `references/pipelines-and-render-passes.md`
- Why an Apple GPU differs from a discrete one: tile memory, pass merging,
  memoryless targets, imageblocks and tile shaders, porting a desktop renderer
  → `references/apple-gpu-tbdr.md`
- Storage modes, uploads, heaps, residency sets, sparse textures, the IO
  command queue, the unified-memory budget → `references/resources-and-memory.md`
- Compute dispatch sizing, indirect arguments, indirect command buffers,
  object and mesh shaders, ray tracing, MPS and machine-learning passes →
  `references/compute-and-gpu-driven.md`
- The shader source: MSL 4.0 against 4.1, address spaces, struct layout, fast
  math, `half`, SIMD-groups, threadgroup memory and atomics →
  `references/shading-language.md`
- Getting a frame to the screen: `MTKView` against `CAMetalLayer` against
  `CAMetalDisplayLink`, drawables, the present sequence, HDR and EDR, MetalFX
  → `references/display-and-upscaling.md`
- The frame is wrong or slow on the GPU: capture, `gpudebug`, validation,
  shader logging, GPU timing, the Metal Performance HUD, Metal System Trace →
  `references/gpu-debugging-and-profiling.md`
- The engine is C++ or Rust: metal-cpp and objc2-metal names and ownership,
  compiling shaders outside Xcode, hosting the build so that capture attaches
  → `references/cpp-and-rust.md`

Name the symptom before you pick the skill:
- **GPU frame time, wrong pixels, and GPU faults are here.** Examples are a
  pass that costs too much and a draw that writes the wrong value. A resource
  that is not resident and a pipeline compile that stalls a frame are here too.
- **CPU tick cost goes to apple-performance.** Time Profiler, call trees,
  signposts, hangs, launch time, and app-level stutter are its job. In the Game
  Performance timeline, a long display interval with a busy GPU track is GPU
  work and stays here. A long interval with GPU gaps and little blocked render
  thread time is CPU work and goes there.
- **Frame pacing policy goes to apple-games,** with input, audio, and Game
  Center. Fixed or variable step, frame budgets, and render-thread QoS belong
  to its game loop. Drawable acquisition, present, and the
  `CAMetalDisplayLink` mechanics stay here.
- **SwiftUI shader modifiers go to apple-animations.** `colorEffect`,
  `layerEffect`, and `distortionEffect` are SwiftUI. A shader in an engine's
  render or compute pipeline is here.

Metal 4 or Metal 3:
- **Metal 4 is the default.** It needs an Apple7 or later GPU and macOS 26.0
  or iOS 26.0. Apple7 starts at A14 and M1. Every Apple silicon Mac is Apple7
  or later.
- **Use the Metal 3 path for older hardware or OS releases:** an iPhone or iPad
  with A13 or earlier, or any device before OS 26. Each reference has a
  `## Maintaining older code: Metal 3` section.
- **Gate once, at launch, and build one renderer per path.** Check both
  conditions: `#available(macOS 26.0, iOS 26.0, *)` for the OS, and
  `device.supportsFamily(.metal4)` for the GPU. The `MTL4` types are separate
  protocols, not subclasses of the Metal 3 types.
- MPS image kernels and `MPSMatrixMultiplication` encode only onto a Metal 3
  command buffer. A Metal 4 renderer that needs them keeps a Metal 3 queue
  beside its `MTL4CommandQueue`.

Rules that always apply:
- **Metal 4 moves duties onto the engine.** A command buffer does not retain
  its resources, nothing is hazard-tracked, and encoders bind nothing directly.
  Keep each resource alive until its frame signals completion. Put a barrier,
  fence, or event before every dependent read. Put every resource that the GPU
  touches in a residency set.
- **Spell names from the references or the SDK, not from memory.** The common
  prior is Metal 3: `setVertexBuffer`, a pipeline made by the device, a blit
  encoder. Metal 4 has an argument table, an `MTL4Compiler`, and copies on the
  compute encoder.
- **The SDK headers win over a doc page.** On which GPU family a feature
  needs, the Metal Feature Set Tables win over a doc page or a family doc
  comment. The references record each disagreement they found.
- **Gate a feature with `supportsFamily(_:)`,** using the family that the
  Feature Set Tables give. Do not infer capability from the storage mode a
  resource came back with. MetalFX effects have their own `supportsDevice(_:)` and
  `supportsMetal4FX(_:)` checks.
- **Turn on validation for every development run.** `MTL_DEBUG_LAYER=1` is API
  Validation, for CPU-side misuse. `MTL_SHADER_VALIDATION=1` is Shader
  Validation, for GPU-side faults. Shader Validation reports to the unified log
  unless `MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1` is also set, so set both.
  Set the variables at launch, because Metal reads them when it makes the first
  device. Shader Validation catches what API
  Validation does not. API Validation did not report a Metal 4 render target
  that was missing from every residency set. Its unretained-resource check
  covers only the Metal 3 command buffer.
- **On an Apple GPU, the render pass is the unit of cost.** Merge passes that
  share render targets, choose each load and store action on purpose, and keep
  attachments that a pass makes and uses itself memoryless.
- **Pin the shading language version.** MSL 4.0 and 4.1 are not
  ABI-compatible, and a runtime compile or an external build that omits
  `-std=` can produce 4.1 code. Use one version across every library.
- **Label every queue, resource, pipeline descriptor, and encoder, and push
  debug groups.** A trace of an unlabelled engine shows only numbered objects.
- **Where a workflow is GUI-only, it is GUI-only.** The shader debugger, the
  shader cost graph, and per-line costs have no command-line form. Neither do
  the Metal debugger's views or the analysis of an Instruments trace.
  `gpudebug` reads a captured trace; `xctrace` records and exports. Do not invent a flag. Give
  the user the exact menu path.
- **Measured claims come from one machine.** The references label each one
  as measured or runtime-checked. The machine was an M4 Pro (Apple9) with
  macOS 27.0.1 installed. Measure again on a new OS or GPU family before you depend on
  such a claim.
