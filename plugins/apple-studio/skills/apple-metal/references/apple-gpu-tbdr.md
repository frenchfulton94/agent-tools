> verified: 2026-10 against https://developer.apple.com/documentation/metal/tailor-your-apps-for-apple-gpus-and-tile-based-deferred-rendering.md, https://developer.apple.com/documentation/metal/synchronizing-stages-within-a-pass.md, https://developer.apple.com/documentation/metal/understanding-color-renderable-pixel-format-sizes.md, https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon.md, https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus.md, https://developer.apple.com/documentation/metal/setting-load-and-store-actions.md, https://developer.apple.com/documentation/metal/implementing-order-independent-transparency-with-image-blocks.md, https://developer.apple.com/documentation/metal/improving-edge-rendering-quality-with-multisample-antialiasing-msaa.md, https://developer.apple.com/documentation/metal/rendering-a-scene-with-deferred-lighting-in-swift.md, https://developer.apple.com/documentation/metal/rendering-a-scene-with-deferred-lighting-in-c++.md, https://developer.apple.com/documentation/metal/developing-metal-apps-that-run-in-simulator.md, https://developer.apple.com/documentation/metal/optimizing-texture-data.md, https://developer.apple.com/documentation/xcode/validating-your-apps-metal-api-usage.md, https://developer.apple.com/documentation/Metal/MTLStorageMode/memoryless.md, https://developer.apple.com/documentation/Metal/MTLLoadAction/dontCare.md, https://developer.apple.com/documentation/Metal/MTLLoadAction/clear.md, https://developer.apple.com/documentation/Metal/MTLLoadAction/load.md, https://developer.apple.com/documentation/Metal/MTLStoreAction/dontCare.md, https://developer.apple.com/documentation/Metal/MTLStoreAction/store.md, https://developer.apple.com/documentation/Metal/MTLStoreAction/multisampleResolve.md, https://developer.apple.com/documentation/Metal/MTLStoreAction/storeAndMultisampleResolve.md, https://developer.apple.com/documentation/Metal/MTLStoreAction/unknown.md, https://developer.apple.com/documentation/Metal/MTL4RenderPassDescriptor.md, https://developer.apple.com/documentation/Metal/MTL4RenderPassDescriptor/tileWidth.md, https://developer.apple.com/documentation/Metal/MTL4RenderPassDescriptor/tileHeight.md, https://developer.apple.com/documentation/Metal/MTL4RenderPassDescriptor/imageblockSampleLength.md, https://developer.apple.com/documentation/Metal/MTL4RenderPassDescriptor/threadgroupMemoryLength.md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder.md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/dispatchThreadsPerTile(_:).md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/setThreadgroupMemoryLength(_:offset:index:).md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/tileWidth.md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/tileHeight.md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/setArgumentTable(_:stages:).md, https://developer.apple.com/documentation/Metal/MTL4RenderCommandEncoder/setColorStoreAction(_:index:).md, https://developer.apple.com/documentation/Metal/MTL4TileRenderPipelineDescriptor.md, https://developer.apple.com/documentation/Metal/MTL4TileRenderPipelineDescriptor/threadgroupSizeMatchesTileSize.md, https://developer.apple.com/documentation/Metal/MTL4TileRenderPipelineDescriptor/tileFunctionDescriptor.md, https://developer.apple.com/documentation/Metal/MTL4TileRenderPipelineDescriptor/rasterSampleCount.md, https://developer.apple.com/documentation/Metal/MTL4TileRenderPipelineDescriptor/colorAttachments.md, https://developer.apple.com/documentation/Metal/MTL4Compiler/newRenderPipelineStateWithDescriptor:compilerTaskOptions:error:.md, https://developer.apple.com/documentation/Metal/MTL4CommandEncoder/barrier(afterEncoderStages:beforeEncoderStages:visibilityOptions:).md, https://developer.apple.com/documentation/Metal/MTL4CommandEncoder/barrier(afterQueueStages:beforeStages:visibilityOptions:).md, https://developer.apple.com/documentation/Metal/MTL4CommandEncoder/barrier(afterStages:beforeQueueStages:visibilityOptions:).md, https://developer.apple.com/documentation/Metal/MTL4CommandEncoder/updateFence(_:afterEncoderStages:).md, https://developer.apple.com/documentation/Metal/MTL4CommandEncoder/waitForFence(_:beforeEncoderStages:).md, https://developer.apple.com/documentation/Metal/MTLStages/tile.md, https://developer.apple.com/documentation/Metal/MTLStages/fragment.md, https://developer.apple.com/documentation/Metal/MTLRenderPipelineState/imageblockSampleLength.md, https://developer.apple.com/documentation/Metal/MTLRenderPipelineState/imageblockMemoryLength(forDimensions:).md, https://developer.apple.com/documentation/Metal/MTLDevice/areRasterOrderGroupsSupported.md, https://developer.apple.com/documentation/Metal/MTLDevice/isDepth24Stencil8PixelFormatSupported.md, https://developer.apple.com/documentation/Metal/MTLDevice/supportsTextureSampleCount(_:).md, https://developer.apple.com/documentation/Metal/MTLCompileOptions/preserveInvariance.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/apple2.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/apple4.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/apple5.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/apple7.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/metal4.md, https://developer.apple.com/documentation/Metal/MTLGPUFamily/mac2.md, https://developer.apple.com/documentation/Metal/MTLTextureUsage/renderTarget.md, https://developer.apple.com/documentation/Metal/MTLTileRenderPipelineDescriptor.md, https://developer.apple.com/documentation/Metal/MTLTileRenderPipelineDescriptor/tileFunction.md, https://developer.apple.com/documentation/Metal/MTLDevice/makeRenderPipelineState(tileDescriptor:options:reflection:).md, https://developer.apple.com/documentation/Metal/MTLRenderCommandEncoder/dispatchThreadsPerTile(_:).md, https://developer.apple.com/documentation/Metal/MTLRenderCommandEncoder/setTileBuffer(_:offset:index:).md, https://developer.apple.com/documentation/Metal/MTLRenderCommandEncoder/memoryBarrier(scope:after:before:).md, https://developer.apple.com/documentation/Metal/MTLRenderPassDescriptor/tileWidth.md, https://developer.apple.com/documentation/Metal/MTLRenderPassDescriptor/imageblockSampleLength.md, https://developer.apple.com/documentation/Metal/MTLRenderStages/tile.md
> sources: metal-by-tutorials-5e, msl-4.1, metal-feature-set-tables-2026-05
> typecheck: macos 26.0
> typecheck-metal: metal4.0

# Apple GPUs: Tile Memory, Pass Structure, and Porting From Discrete GPUs

Contents:
- The model, and the three habits it breaks
- Feature gates for tile work
- Attachments: load, store, and memoryless
- Merge passes: programmable blending and single-pass deferred
- The tile-memory budget
- Imageblocks and tile shaders
- Raster order groups
- MSAA on Apple GPUs
- Synchronizing inside a TBDR pass
- Porting code written for discrete GPUs
- Maintaining older code: Metal 3
- Where else to look

Scope: *how an Apple GPU differs from the discrete GPU most graphics habits were formed
on, and what an engine should do about it*. The command model (allocators, argument
tables, residency, frames in flight) is `command-model.md`. Compiling pipelines and the
general rules for load and store actions are `pipelines-and-render-passes.md`. Storage
modes, heaps, and budgets are `resources-and-memory.md`. The MSL syntax for every
attribute named here is `shading-language.md`. Intel Macs and discrete GPUs are out of
scope, except as the place ported code comes from.

## The model, and the three habits it breaks

Apple GPUs are tile-based deferred renderers (TBDR). For each render pass the GPU first
runs vertex work and bins every primitive into the screen tiles it touches. Then, tile by
tile, it resolves visibility, shades only the fragments that survive, and keeps every
attachment in on-chip *tile memory*. Each finished tile is written to system memory once.
Apple describes tile memory as many times faster and many times lower in latency than
device memory, at much lower energy. While one pass finishes its fragment work, the GPU
can already run the vertex stage of the next pass.

Three consequences matter more than any other, and each breaks a discrete-GPU habit:

1. **The render pass is the unit of cost.** A pass boundary means a store from tile memory
   to system memory and, usually, a load back. Many small passes each pay that, plus a
   fixed setup cost. On an immediate-mode GPU, splitting work into passes is nearly free.
   Here, merge consecutive passes that share render targets whenever the later work reads
   only the same pixel. Pass merging is the largest single lever this file offers.
2. **Load and store actions do real work.** `.dontCare` actually skips the copy into or out
   of tile memory. A wrong action that an Intel or AMD GPU silently forgave shows up here as
   garbage pixels. See "Attachments" below.
3. **Opaque draw order matters much less.** Hidden opaque fragments are rejected per tile
   before shading, so front-to-back sorting of opaque draws buys far less than it does on an
   immediate-mode GPU. Blended geometry is the exception: draw it after the opaques, sorted
   back to front, or use the imageblock OIT below. A fragment function that writes depth can
   switch off the early depth test, so write depth from the fragment stage only when you
   have to.

On an Apple silicon Mac, `MTLCreateSystemDefaultDevice()` is the only GPU, and it is this
kind of GPU. There is no discrete GPU to fall back to.

## Feature gates for tile work

Every gate below is from the Feature Set Tables (May 2026), which list Apple families only.
Where a sample page or the MSL spec gives a different floor, the tables win.

| Feature | Programming model | First family |
|---|---|---|
| Memoryless render targets, programmable blending, deferred store action | Metal 3 & 4 | Apple2 |
| Imageblocks, tile shaders, raster order groups (max 8 per fragment function), imageblock sample coverage control | Metal 3 & 4 | Apple4 (A11) |
| Nonsquare tile dispatch | Metal 3 & 4 | Apple5 (A12) |
| 8x MSAA (16x16 tiles at 8x) | Metal 3 & 4 | Apple10 (A19, M5) |
| Metal 4 itself | Metal 4 | Apple7 (A14, M1) |

The family map: A14 and M1 are Apple7. A15, A16, and M2 are Apple8. A17 Pro, A18, M3, and
M4 are Apple9. A19 and M5 are Apple10. The SDK also defines `MTLGPUFamily.apple11`, which the
May 2026 tables do not describe yet, so assume nothing about it.

**The consequence for a Metal 4 renderer:** the Metal 4 path needs Apple7, and Apple7 is
above every gate in the table except 8x MSAA. On a real device, a Metal 4 renderer can treat
memoryless targets, programmable blending, imageblocks, tile shaders, and raster order
groups as present. What still varies is the tile-memory budget (next sections) and the
Simulator.

**The Simulator is not an Apple GPU.** It runs on the host Mac's Metal, and Apple describes
it as roughly Apple2-class, yet it has no programmable blending, imageblocks, or tile shaders. The
programmable-blending gap has no runtime query, so gate it at compile time. Apple's Swift
deferred sample switches paths on `supportsFamily(.apple1)`, yet says its Simulator builds
take the two-pass path. Do not let a family check stand in for the Simulator test. Write the
gate explicitly:

```swift
struct TBDRCapabilities {
    let programmableBlending: Bool   // read [[color(n)]] in a fragment function
    let tileShading: Bool            // imageblocks, tile shaders
    let rasterOrderGroups: Bool
    let nonsquareTileDispatch: Bool
    let maxSampleCount: Int

    init(_ device: any MTLDevice) {
        #if targetEnvironment(simulator)
        programmableBlending = false
        tileShading = false
        #else
        programmableBlending = device.supportsFamily(.apple2)
        tileShading = device.supportsFamily(.apple4)
        #endif
        rasterOrderGroups = tileShading && device.areRasterOrderGroupsSupported
        nonsquareTileDispatch = tileShading && device.supportsFamily(.apple5)
        maxSampleCount = device.supportsTextureSampleCount(8) ? 8 : 4
    }
}
```

Every Apple GPU supports 4x MSAA, so 4 is the safe default. Probe 8 rather than assume it:
the `supportsTextureSampleCount(_:)` page says "some macOS devices", but the tables put 8x
on Apple10 only.

## Attachments: load, store, and memoryless

`pipelines-and-render-passes.md` has the full load and store table. These are the rules
that exist because of tile memory:

- **`.dontCare` is a promise, not a hint.** On a load it means "every pixel I read in this
  pass, I write first". On a store it means "nothing reads this after the pass". Break the
  promise and you read arbitrary data. Ported engines often carry these bugs latently.
  Under Rosetta, an app linked against macOS 10.15 or earlier has `.dontCare` loads turned
  into real loads, which hides the bug and costs performance.
- **Find these bugs with API Validation.** `MTL_DEBUG_LAYER_VALIDATE_LOAD_ACTIONS=1` turns
  every `.dontCare` load into a fuchsia clear. `MTL_DEBUG_LAYER_VALIDATE_STORE_ACTIONS=1`
  writes a red-and-white checkerboard into every `.dontCare` store. If either one changes
  the final image, some action is wrong. More in `gpu-debugging-and-profiling.md`.
- **`.load` is the expensive load.** Apple rates it significantly slower than `.clear` or
  `.dontCare`. Use `.clear` when the pass covers only part of the target; it writes the
  clear value into tile memory and reads nothing.
- **Memoryless textures live only in tile memory.** `MTLStorageMode.memoryless` allocates no
  system memory at all. It applies to textures only; there are no memoryless buffers. A
  memoryless attachment cannot use `.load`, `.store`, or `.storeAndMultisampleResolve`.
  Depth, stencil, MSAA color, and any intermediate that is produced and consumed inside one
  pass should be memoryless. The usual store action for depth and stencil is `.dontCare`.
- **Set `usage` to `.renderTarget` alone** on a memoryless target. You cannot sample it,
  so it needs no `.shaderRead`. Lossless framebuffer compression (Apple5 and later) is
  skipped for textures whose usage includes `.shaderWrite`, `.pixelFormatView`, or
  `.unknown`, so do not add those to render targets by habit.
- **The deferred store action still applies.** If the store choice depends on work you have
  not encoded yet, set `.unknown` in the descriptor, then call
  `setColorStoreAction(_:index:)` (or the depth and stencil variants) before
  `endEncoding()`. Ending a pass with `.unknown` still in place is an error.

```swift
/// A transient attachment that exists only in tile memory for the length of one pass.
func makeTransientTarget(on device: any MTLDevice, _ format: MTLPixelFormat,
                         width: Int, height: Int,
                         sampleCount: Int = 1) -> (any MTLTexture)? {
    let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: format,
                                                              width: width,
                                                              height: height,
                                                              mipmapped: false)
    if sampleCount > 1 {
        descriptor.textureType = .type2DMultisample
        descriptor.sampleCount = sampleCount
    }
    descriptor.usage = .renderTarget
    descriptor.storageMode = .memoryless
    return device.makeTexture(descriptor: descriptor)
}
```

Do not copy the snippet on Apple's storage-mode page: it creates a mipmapped `.r16Float`
texture and attaches it as depth. A depth attachment needs a depth format, and a transient
target needs no mipmaps.

## Merge passes: programmable blending and single-pass deferred

Programmable blending lets a fragment function read the current value of a color
attachment at its own pixel, by declaring a `[[color(n)]]` input. That one feature is
what makes pass merging possible. A deferred renderer writes its G-buffer and lights it in
the same render pass, and the G-buffer never leaves tile memory. A chain of post effects
on one target works the same way, as long as each effect reads only its own pixel.

The conversion from a two-pass deferred renderer, in order:

1. Make every G-buffer texture memoryless, with `.clear` (or a provably safe `.dontCare`)
   load and `.dontCare` store. Do the same for depth and stencil.
2. Stop binding G-buffer textures as shader inputs. A memoryless texture cannot be bound as
   a texture.
3. Lighting fragments take the G-buffer as `[[color(n)]]` inputs instead.
4. Encode G-buffer fill and lighting in one encoder, on one pass descriptor that names every
   attachment, including the drawable.
5. Give every pipeline used in that pass the identical color-format list, including stages
   that write only some attachments. Metal 4's `MTL4RenderPipelineDescriptor` carries color
   formats only; it has no depth or stencil format property.

Three validation errors mean a step was missed. "Memoryless attachment content cannot be
stored in memory" means a memoryless target still has `.store`. "Texture is Memoryless,
and cannot be assigned" means one is still bound as a texture. "Reads from a color
attachment whose pixel format is MTLPixelFormatInvalid" means a pipeline in the merged pass
is missing formats.

A fragment function cannot read the depth attachment this way, and the porting guide
forbids sampling a depth texture that the same pass writes. So Apple's samples store view
depth in a color attachment (`r32Float`) and reconstruct position from that.

```swift
/// One render pass: fill the G-buffer, then light it. Only the drawable is stored.
func makeSinglePassDeferredDescriptor(device: any MTLDevice, drawable: any MTLTexture,
                                      width: Int, height: Int) -> MTL4RenderPassDescriptor? {
    guard let albedo = makeTransientTarget(on: device, .rgba8Unorm, width: width, height: height),
          let normal = makeTransientTarget(on: device, .rgba16Float, width: width, height: height),
          let viewDepth = makeTransientTarget(on: device, .r32Float, width: width, height: height),
          let depthStencil = makeTransientTarget(on: device, .depth32Float_stencil8,
                                                 width: width, height: height)
    else { return nil }

    let pass = MTL4RenderPassDescriptor()
    pass.colorAttachments[0].texture = drawable          // lighting accumulates here
    pass.colorAttachments[0].loadAction = .clear
    pass.colorAttachments[0].storeAction = .store
    for (offset, target) in [albedo, normal, viewDepth].enumerated() {
        pass.colorAttachments[offset + 1].texture = target
        pass.colorAttachments[offset + 1].loadAction = .clear      // .load is illegal here
        pass.colorAttachments[offset + 1].storeAction = .dontCare  // .store is illegal here
    }
    pass.depthAttachment.texture = depthStencil
    pass.depthAttachment.loadAction = .clear
    pass.depthAttachment.storeAction = .dontCare
    pass.stencilAttachment.texture = depthStencil
    pass.stencilAttachment.loadAction = .clear
    pass.stencilAttachment.storeAction = .dontCare
    return pass
}

/// Every pipeline in the merged pass declares this exact list.
let singlePassDeferredFormats: [MTLPixelFormat] = [.bgra8Unorm, .rgba8Unorm, .rgba16Float, .r32Float]

func applySinglePassDeferredFormats(to descriptor: MTL4RenderPipelineDescriptor) {
    for (index, format) in singlePassDeferredFormats.enumerated() {
        descriptor.colorAttachments[index].pixelFormat = format
    }
}
```

Create the memoryless targets when the drawable size changes, as Apple's sample does, not
every frame.

The lighting side, with raster order groups (next-but-one section) so that lights overlap:

```metal
// The pass's attachments as a lighting fragment sees them.
struct GBufferIn {
    half4 lighting  [[color(0), raster_order_group(0)]];
    half4 albedo    [[color(1), raster_order_group(1)]];
    half4 normal    [[color(2), raster_order_group(1)]];
    float viewDepth [[color(3), raster_order_group(1)]];
};

struct LightOut {
    half4 lighting [[color(0), raster_order_group(0)]];
};

struct LightVaryings {
    float4 position [[position]];
    half3  lightColor;
};

fragment LightOut point_light_fragment(LightVaryings in [[stage_in]],
                                       GBufferIn gbuffer)
{
    half3 n = normalize(gbuffer.normal.xyz);
    half  ndotl = max(n.z, 0.0h);   // stand-in for real light math
    LightOut out;
    out.lighting = gbuffer.lighting + half4(gbuffer.albedo.rgb * in.lightColor * ndotl, 0.0h);
    return out;
}
```

**Two traps in this pattern.**

- **The drawable is held for the whole pass.** The single-pass renderer must acquire the
  drawable before the G-buffer stage, because lighting writes into it in the same pass. A
  two-pass renderer can acquire it later. This pattern is the exception to the
  drawable rules in `display-and-upscaling.md` ("Drawables: acquire late, hold briefly").
- **On an MSAA target, a `[[color(n)]]` input can make the fragment function run once per
  sample** rather than once per pixel. So can `[[sample_id]]` and the `sample_*`
  interpolation qualifiers. Programmable blending on a 4x target can quietly multiply
  lighting cost by four. Measure before you combine the two.

Apple's Swift deferred-lighting page shows `MTLStorageMode.private` in the snippet labelled
as the single-pass renderer. Its own prose, and the C++ version, say memoryless. Memoryless
is right.

## The tile-memory budget

The binding limit on Apple GPUs is often not the attachment count (8 color targets, the
same as anywhere) but **the combined per-pixel size of every color attachment in the
pass**. A G-buffer that a discrete GPU accepts can fail here. These are the limits, per
pixel and per sample, when a pass has several color targets:

| Limit (Feature Set Tables) | Apple2–3 | Apple4–6 | Apple7–8 | Apple9–10 |
|---|---|---|---|---|
| Implicit imageblock (the attachments), per pixel per sample | 32 B | 64 B | 128 B | 128 B |
| Explicit imageblock, per pixel per sample | none | 64 B | 64 B | 64 B |
| Implicit imageblock allocation | none | 128 KB | 128 KB | 256 KB |
| Explicit imageblock allocation | none | 32 KB | 32 KB | 32 KB |
| Threadgroup memory | 16,352 B / 16 KB | 32 KB | 32 KB | 32 KB |
| Max tile, no MSAA or 2x / 4x / 8x | 32x32 / 32x16 / none | same | same | 32x32 / 32x16 / 16x16 (Apple10) |

What the table means in practice:

- **The Metal 4 floor gives you 128 B per pixel.** The summed size of four `rgba16Float`
  targets is 32 B, so ordinary G-buffers fit. Eight `rgba32Float` targets total 128 B,
  exactly the limit. A format's footprint in tile memory can differ from its footprint in
  system memory, so do not budget to the byte. Leave headroom, and treat a pass that fails
  to create as a budget failure first.
- **Imageblocks and threadgroup memory share one pool.** Their combined allocation cannot
  exceed the imageblock limit. On Apple7 and Apple8, a 32x32 tile at 128 B per pixel is
  32 × 32 × 128 B = 128 KB, the whole allocation, with nothing left for threadgroup memory.
  Apple9 and later double the pool to 256 KB.
- **MSAA shrinks the tile.** 4x caps tiles at 32x16, and 8x at 16x16. More tiles means more
  per-tile overhead, so MSAA on Apple GPUs is cheap but not free.
- **`A8Unorm` cannot be part of an explicit-layout imageblock.** Use an `R8Unorm` view, or
  implicit layout.

When a pass uses an explicit imageblock, you must tell the pass how much each sample needs,
and you may choose the tile size. `tileWidth` and `tileHeight` default to `0`, which lets
Metal pick a size that fits. A larger tile has less per-tile overhead. If the attachments
and imageblock cannot fit at the size you ask for, creating the pass fails.

```swift
/// Reserve tile memory for a pipeline's explicit imageblock, and report what one tile costs.
func reserveImageblock(on pass: MTL4RenderPassDescriptor,
                       for pipeline: any MTLRenderPipelineState,
                       tileWidth: Int, tileHeight: Int) -> Int {
    pass.imageblockSampleLength = pipeline.imageblockSampleLength
    pass.tileWidth = tileWidth
    pass.tileHeight = tileHeight
    return pipeline.imageblockMemoryLength(forDimensions: MTLSize(width: tileWidth,
                                                                  height: tileHeight,
                                                                  depth: 1))
}
```

`imageblockMemoryLength(forDimensions:)` accepts only valid tile sizes (32x32, 32x16,
16x16). Compare its result, plus any `threadgroupMemoryLength` you reserve on the pass,
against the allocation row above for the lowest family you ship on.

## Imageblocks and tile shaders

An **imageblock** is the per-tile, per-pixel structure in tile memory. It persists for the
life of the tile, across every draw and tile dispatch in the pass. Every pass already has an
*implicit* imageblock made from its attachments, which is what `[[color(n)]]` reads. An
*explicit* imageblock is a struct you declare in MSL (scalars, vectors, packed pixel types
such as `rgba8unorm<half4>`, arrays, nested structs). It can hold data that has no
attachment at all. A fragment function sees only its own pixel's entry. A tile or compute
function sees the whole tile.

A **tile shader** is a kernel (or fragment) function dispatched inside a render pass with
`dispatchThreadsPerTile(_:)`. It replaces a render, compute, render sequence that would have
round-tripped device memory twice. Each tile dispatch is a barrier against the draws and
dispatches before it. A kernel-based tile function waits for all earlier access to the
whole tile. A fragment-based one waits only for earlier access to its own pixel. Apple's
uses: per-tile light culling (forward+), custom MSAA resolve, and initializing an explicit
imageblock at the start of a pass.

Rules that differ from compute habits:

- **One threadgroup runs per tile, and it may be smaller than the tile.** Do not assume each
  thread owns a pixel. Apple's samples dispatch one thread per tile pixel and address the
  imageblock with `[[thread_position_in_threadgroup]]`. Do not treat
  `thread_index_in_threadgroup` as row-major either; tile threads are packed as 2x2 quads.
- **Threadgroup memory in a tile function persists across the tile.** The tile's fragment
  functions see it too, which is how per-tile light lists stay on chip. Size it with
  `threadgroupMemoryLength` on the pass and
  `setThreadgroupMemoryLength(_:offset:index:)` on the encoder.
- **Explicit imageblocks are not covered by load and store actions.** Those act on
  attachments only. To keep explicit imageblock data, write it out from a tile function, with
  a `texture.write(imageblock.slice(...), coord)` issued after a
  `threadgroup_barrier(mem_flags::mem_threadgroup_imageblock)`. An out-of-bounds slice write
  is undefined, unlike an ordinary texture write, which is dropped.
- **Square dispatches only, before Apple5.** `dispatchThreadsPerTile(_:)` takes a width and
  height no larger than the encoder's `tileWidth` and `tileHeight`, and a depth of 1.
- **Layout comes from the type.** `imageblock<T>` deduces its layout from `T`: a struct
  whose members carry `[[color(n)]]` is implicit layout, and any other struct is explicit.
  You may also spell the layout out. The SDK header (`metal_imageblocks`) is the authority
  here; descriptions that call bare `imageblock<T>` "explicit" are wrong for attachment
  structs, as Apple's own MSAA resolve sample shows.

Build tile pipelines through the Metal 4 compiler, like any other render pipeline. Bind
tile-stage resources with an argument table set for `MTLRenderStages.tile`.

```swift
func makeTilePipeline(compiler: any MTL4Compiler, library: any MTLLibrary,
                      functionName: String, colorFormats: [MTLPixelFormat],
                      sampleCount: Int) throws -> any MTLRenderPipelineState {
    let function = MTL4LibraryFunctionDescriptor()
    function.library = library
    function.name = functionName

    let descriptor = MTL4TileRenderPipelineDescriptor()
    descriptor.tileFunctionDescriptor = function
    descriptor.rasterSampleCount = sampleCount
    descriptor.threadgroupSizeMatchesTileSize = true
    for (index, format) in colorFormats.enumerated() {
        descriptor.colorAttachments[index].pixelFormat = format
    }
    // One entry point builds render, tile, and mesh pipelines; the descriptor type decides.
    return try compiler.makeRenderPipelineState(descriptor: descriptor, compilerTaskOptions: nil)
}

func encodeTileDispatch(_ encoder: any MTL4RenderCommandEncoder,
                        pipeline: any MTLRenderPipelineState) {
    encoder.setRenderPipelineState(pipeline)
    encoder.dispatchThreadsPerTile(MTLSize(width: encoder.tileWidth,
                                           height: encoder.tileHeight,
                                           depth: 1))
}
```

**Order-independent transparency** is the canonical explicit-imageblock technique. Each
pixel keeps a small fixed array of (color, depth) layers in tile memory. A tile kernel
fills it with sentinels at the start of the pass. Transparent draws, with the pipeline's
color write mask set to none (`MTLColorWriteMaskNone`), insertion-sort into it. A full-screen draw then
blends the layers back to front over the opaque color it reads from the attachment.
Overflow drops the farthest layer, and the result still reads as plausible. Every
imageblock member a fragment function writes needs a raster order group:

```metal
struct OITLayers {
    rgba8unorm<half4> color [[raster_order_group(0)]] [4];   // packed: 4 B per layer
    half              depth [[raster_order_group(0)]] [4];
};

kernel void oit_clear_tile(imageblock<OITLayers, imageblock_layout_explicit> block,
                           ushort2 tid [[thread_position_in_threadgroup]])
{
    threadgroup_imageblock OITLayers *layers = block.data(tid);
    for (short i = 0; i < 4; ++i) {
        layers->color[i] = half4(0.0h);
        layers->depth[i] = half(INFINITY);
    }
}
```

Every layer adds to the pipeline's `imageblockSampleLength`, so the layer count trades
directly against tile size. Without Apple4 this technique blends wrongly rather than
failing. Ship a sorted or weighted-blended fallback for the Simulator and any pre-Apple4
device you support.

## Raster order groups

Fragments that overlap at one pixel run concurrently, and their read-modify-write of shared
memory races. Fixed-function blending is ordered for you; anything you do yourself is not.
Tagging memory with `[[raster_order_group(n)]]` makes the hardware hold a fragment's access
until older fragments at the same pixel (and sample, under per-sample shading) have
finished theirs. The tag can go on imageblock members, `[[color(n)]]` members, and device
buffer or texture arguments; `shading-language.md` has the exact placement rules.

The performance lever is **several groups**. Each group is ordered independently. In
single-pass deferred lighting, the G-buffer reads go in one group and the light
accumulator in another. A later light can then read the G-buffer while an earlier one is
still accumulating, and the two serialize only on the accumulate. Apple's article and its
samples number the groups in opposite orders (the article puts the G-buffer first, the
samples put lighting in group 0). The numbers carry no meaning; the split is what counts.
Apple's pipeline-statistics guidance also names raster order groups as the remedy for
"wait pixel" stalls, which blending usually causes.

Gate raster order groups with `areRasterOrderGroupsSupported` as well as the family check.
In kernels the attribute is ignored. If an explicit imageblock is written by a fragment
function, every member of its master struct must carry a group, either on a nested struct
or on each field, not both.

## MSAA on Apple GPUs

The hardware tracks, per pixel, whether an edge is present and how many *unique colors* the
samples hold. Interior pixels blend once. Since A11, a pixel blends once per unique color,
not once per covered sample. An opaque primitive that covers every sample collapses the
pixel back to a single color. This is why MSAA is cheaper here than on an immediate-mode GPU.

- **Make the MSAA color target memoryless, with usage `.renderTarget` only, and store with
  `.multisampleResolve`.** The samples never reach system memory; only the resolve texture
  is stored. `.storeAndMultisampleResolve` writes both, and a memoryless target cannot use it.
- **Resolve in the tile, not in a compute pass.** When the built-in average is wrong (for
  example, tone-map each HDR sample before averaging), a tile kernel can resolve before the
  tile is stored, saving both the MSAA texture and a pass. Iterate unique colors rather than
  samples, weight each by its coverage count, and write the result back to every sample.
  Apple's sample then lets `.multisampleResolve` store it.
- **A tile shader can also edit sample coverage.** For example, it can resolve the opaque
  geometry in-tile before transparent geometry blends on top, all in one pass.

```metal
struct ResolveColor {
    half4 color [[color(0)]];   // a [[color]] member makes this imageblock implicit layout
};

kernel void resolve_tile(imageblock<ResolveColor> block,
                         ushort2 tid [[thread_position_in_threadgroup]])
{
    const ushort colors = block.get_num_colors(tid);
    half4 sum = 0.0h;
    for (ushort i = 0; i < colors; ++i) {
        half4 c = block.read(tid, i, imageblock_data_rate::color).color;
        sum += c * half(popcount(block.get_color_coverage_mask(tid, i)));
    }
    const ushort samples = block.get_num_samples();
    sum /= half(samples);
    block.write(ResolveColor{sum}, tid, ushort((1u << samples) - 1u));
}
```

## Synchronizing inside a TBDR pass

Metal does not support an intrapass barrier that waits on the `.fragment` or `.tile` stage
on a TBDR GPU. That follows from the model: the next fragment's input may sit in a tile that
has not been shaded yet. Inside a pass you may depend on:

- earlier fragments at the **same pixel**, through programmable blending or raster order
  groups;
- earlier tile dispatches in the **same tile**.

Draw order, then primitive order, already orders per-fragment attachment access. Tile
dispatch order already orders tile-shader access. Neither needs any sync.

Anything that reads **another pixel or another tile** (blur, bloom, SSAO, a mip chain, a
reduction across the screen) needs a pass boundary. Store the producer's result, end the
pass, and order the consumer with a consumer barrier in the new pass. A producer barrier
before `endEncoding()`, or a fence updated in the old pass and waited on in the new one
(same command buffer), also works. Name only the stage that actually reads, so the
consumer's vertex work can still overlap.

```swift
/// A blur reads neighbouring pixels, so it cannot live inside the lighting pass.
/// The lighting pass must store the attachment the blur samples.
func beginBlurPass(after lighting: any MTL4RenderCommandEncoder,
                   commandBuffer: any MTL4CommandBuffer,
                   blurPass: MTL4RenderPassDescriptor) -> (any MTL4RenderCommandEncoder)? {
    lighting.endEncoding()
    guard let blur = commandBuffer.makeRenderCommandEncoder(descriptor: blurPass, options: [])
    else { return nil }
    blur.barrier(afterQueueStages: .fragment, beforeStages: .fragment, visibilityOptions: .device)
    return blur
}
```

The intrapass-barrier symbol page, `barrier(afterEncoderStages:beforeEncoderStages:visibilityOptions:)`,
swaps its two parameter descriptions. The SDK header and the page's own discussion agree:
the *after* stages belong to earlier commands, and the *before* stages to later ones. Trust
the header.

On the Performance timeline, Apple GPUs overlap vertex, fragment, and compute work from
independent passes. A timeline with no overlap usually means over-broad barriers, not a busy
GPU. The full barrier, fence, and event ladder is in `command-model.md`.

## Porting code written for discrete GPUs

Fix correctness first (items 1 to 7), then restructure for tile memory. Keep API Validation
and Shader Validation on throughout.

1. **Load and store actions.** Audit every attachment with the two
   `MTL_DEBUG_LAYER_VALIDATE_*_ACTIONS` variables. Engines that only ever ran on Intel or
   AMD Macs often carry these bugs.
2. **Reading what you write.** One texture bound to several arguments when any of them
   writes it is illegal; use one `access::read_write` binding. Sampling a depth texture that
   the same pass writes gives different results on different GPUs; split the pass or, on the
   TBDR path, keep depth in a color attachment as above.
3. **Depth-stencil format.** `depth24Unorm_stencil8` has never existed on Apple silicon.
   The porting guide still says to test `isDepth24Stencil8PixelFormatSupported`; the SDK
   marks that property deprecated with the note "Never supported on Apple Silicon". Use
   `depth32Float_stencil8`.
4. **Out-of-bounds access.** An Apple GPU may treat an out-of-bounds device or threadgroup
   access as a hardware fault and end the command buffer. A discrete GPU often tolerated it.
   Shader Validation finds these.
5. **Missing synchronization.** Apple GPUs exploit concurrent dispatch and untracked
   resources aggressively, so code that "worked" on Intel or AMD corrupts memory here.
   Metal 4 also needs explicit barriers wherever Metal 3 inferred an order; see
   `command-model.md`.
6. **SIMD width.** Do not hard-code it; read `threadExecutionWidth` or
   `[[threads_per_simdgroup]]` (`compute-and-gpu-driven.md`).
7. **Feature checks by family, not by name.** Never branch on `MTLDevice.name` or a
   hard-coded per-GPU value. The porting guide says to test the Mac 2 family for the
   baseline, and an Apple family for tile features. The SDK now deprecates
   `MTLGPUFamily.mac2` (macOS and iOS 27), naming `.apple7` as its replacement. On Apple
   silicon, gate on Apple families, `.metal4`, and per-feature properties.
8. **Restructure for tile memory:** merge passes, make transients memoryless (the Metal
   debugger's memory insights list textures that could be memoryless, with the bytes
   saved), move compute that sits between two render passes into tile shaders when it
   reads only its own tile, and recheck the G-buffer against the per-pixel budget.
9. **Re-plan GPU timing.** Apple GPUs sample counters at stage boundaries, while
   immediate-mode GPUs sample between draws and dispatches, so per-draw timing code needs
   rework. See `gpu-debugging-and-profiling.md`.

## Maintaining older code: Metal 3

Every tile feature in this file predates Metal 4. Apple4 devices have had imageblocks, tile
shaders, and raster order groups since A11. Only the API around them changed.

**When the Metal 3 path applies:**

- GPU families below Apple7: A11 (Apple4), A12 (Apple5), and A13 (Apple6) devices. They have
  every tile feature except those gated higher, but no Metal 4 API.
- Any device on an OS release before 26.0.
- Apple2 and Apple3 devices (A8 to A10), if you still ship there, have memoryless targets and
  programmable blending but no imageblocks or tile shaders, and a 32 B per-pixel budget.

**How to gate:** `#available` for the OS, then `supportsFamily(.metal4)` for the device. Pick
the path once at launch and keep two renderers that share the TBDR decisions (pass merging,
memoryless transients, budgets), not two copies of the guidance.

Snippets in this section compile at the file's macOS 26.0 floor; they are not compile-checked against earlier OS releases.

```swift
func usesMetal4Path(_ device: any MTLDevice) -> Bool {
    if #available(macOS 26.0, iOS 26.0, *) {
        return device.supportsFamily(.metal4)
    }
    return false
}

/// The Metal 3 spelling of the tile pipeline and dispatch shown earlier.
func encodeLegacyTileResolve(device: any MTLDevice, library: any MTLLibrary,
                             pass: MTLRenderPassDescriptor,
                             encoder: any MTLRenderCommandEncoder,
                             tileParameters: any MTLBuffer) throws {
    let descriptor = MTLTileRenderPipelineDescriptor()
    guard let function = library.makeFunction(name: "resolve_tile") else { return }
    descriptor.tileFunction = function
    descriptor.rasterSampleCount = 4
    descriptor.threadgroupSizeMatchesTileSize = true
    descriptor.colorAttachments[0].pixelFormat = .rgba16Float
    let pipeline = try device.makeRenderPipelineState(tileDescriptor: descriptor,
                                                      options: [], reflection: nil)
    // In a real renderer, build the pipeline at load and set tile size before
    // creating the encoder; both appear here only to show the spellings.
    pass.tileWidth = 32
    pass.tileHeight = 16
    pass.imageblockSampleLength = pipeline.imageblockSampleLength

    encoder.setRenderPipelineState(pipeline)
    encoder.setTileBuffer(tileParameters, offset: 0, index: 0)
    encoder.dispatchThreadsPerTile(MTLSize(width: encoder.tileWidth,
                                           height: encoder.tileHeight,
                                           depth: 1))
}
```

**How each concept maps:**

| Concept | Metal 3 | Metal 4 |
|---|---|---|
| Pass descriptor (tile size, imageblock length, threadgroup length) | `MTLRenderPassDescriptor` | `MTL4RenderPassDescriptor`, same property names |
| Tile pipeline descriptor | `MTLTileRenderPipelineDescriptor.tileFunction` (an `MTLFunction`) | `MTL4TileRenderPipelineDescriptor.tileFunctionDescriptor` (an `MTL4FunctionDescriptor`) |
| Building it | `MTLDevice.makeRenderPipelineState(tileDescriptor:options:reflection:)` | `MTL4Compiler.makeRenderPipelineState(descriptor:compilerTaskOptions:)` |
| Tile-stage bindings | `setTileBuffer(_:offset:index:)`, `setTileTexture(_:index:)` | an `MTL4ArgumentTable` set with `setArgumentTable(_:stages: .tile)` |
| Tile dispatch | `MTLRenderCommandEncoder.dispatchThreadsPerTile(_:)` | `MTL4RenderCommandEncoder.dispatchThreadsPerTile(_:)` |
| Ordering inside a render pass | `memoryBarrier(scope:after:before:)`; Apple3–Apple10 reject `.fragment` or `.tile` in `after` and the `.renderTargets` scope | `barrier(afterEncoderStages:beforeEncoderStages:visibilityOptions:)`, with the same no-fragment, no-tile rule |
| Ordering across passes | automatic for tracked resources; `updateFence(_:after:)` / `waitForFence(_:before:)` for untracked ones | always explicit: consumer or producer barriers, or `updateFence(_:afterEncoderStages:)` / `waitForFence(_:beforeEncoderStages:)` |
| Pipeline color formats | `MTLRenderPipelineDescriptor`, which also carries depth and stencil formats | `MTL4RenderPipelineDescriptor`, color formats only |

The ordering row is the porting trap. Metal 3 inferred the order between a pass that writes
a tracked attachment and a later pass that samples it. Metal 4 does not, so every pass
boundary this file tells you to keep needs an explicit barrier or fence when you move to
Metal 4.

## Where else to look

- `command-model.md`: the frame, barriers, fences, events, and residency.
- `pipelines-and-render-passes.md`: load and store tables, depth and stencil, MSAA setup,
  forward against deferred.
- `resources-and-memory.md`: storage modes, heaps and aliasing, lossless and lossy
  compression, memory budgets.
- `shading-language.md`: imageblock, raster-order-group, and tile-function syntax in full.
- `compute-and-gpu-driven.md`: compute passes, threadgroup sizing, SIMD groups.
- `display-and-upscaling.md`: drawable acquisition timing and MetalFX.
- `gpu-debugging-and-profiling.md`: API and shader validation, the dependency viewer,
  memory insights, counters, and the Performance timeline.
