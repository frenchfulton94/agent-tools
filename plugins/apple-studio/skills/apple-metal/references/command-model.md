> verified: 2026-10 against https://developer.apple.com/documentation/metal/understanding-the-metal-4-core-api.md, https://developer.apple.com/documentation/metal/drawing-a-triangle-with-metal-4.md, https://developer.apple.com/documentation/metal/resource-synchronization.md, https://developer.apple.com/documentation/metal/synchronizing-stages-within-a-pass.md, https://developer.apple.com/documentation/metal/synchronizing-passes-with-a-fence.md, https://developer.apple.com/documentation/metal/synchronizing-passes-with-consumer-barriers.md, https://developer.apple.com/documentation/metal/synchronizing-passes-with-producer-barriers.md, https://developer.apple.com/documentation/metal/simplifying-gpu-resource-management-with-residency-sets.md, https://developer.apple.com/documentation/metal/about-synchronization-events.md, https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work.md, https://developer.apple.com/documentation/metal/mtl4commandqueue.md, https://developer.apple.com/documentation/metal/mtl4commandqueue/commit(_:options:).md, https://developer.apple.com/documentation/metal/mtl4commandqueue/commit:count:.md, https://developer.apple.com/documentation/metal/mtl4commandqueue/waitfordrawable(_:).md, https://developer.apple.com/documentation/metal/mtl4commandqueue/signaldrawable(_:).md, https://developer.apple.com/documentation/metal/mtl4commandqueue/signalevent(_:value:).md, https://developer.apple.com/documentation/metal/mtl4commandqueue/waitforevent(_:value:).md, https://developer.apple.com/documentation/metal/mtl4commandqueue/addresidencyset(_:).md, https://developer.apple.com/documentation/metal/mtl4commandqueuedescriptor/feedbackqueue.md, https://developer.apple.com/documentation/metal/mtl4commandqueueerror-swift.struct/code.md, https://developer.apple.com/documentation/metal/mtl4commandbuffer.md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/begincommandbuffer(allocator:).md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/endcommandbuffer().md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/makerendercommandencoder(descriptor:options:).md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/useresidencyset(_:).md, https://developer.apple.com/documentation/metal/mtl4commandallocator.md, https://developer.apple.com/documentation/metal/mtl4commandallocator/reset().md, https://developer.apple.com/documentation/metal/mtl4renderencoderoptions.md, https://developer.apple.com/documentation/metal/mtl4commandencoder.md, https://developer.apple.com/documentation/metal/mtl4commandencoder/barrier(afterencoderstages:beforeencoderstages:visibilityoptions:).md, https://developer.apple.com/documentation/metal/mtl4commandencoder/barrier(afterqueuestages:beforestages:visibilityoptions:).md, https://developer.apple.com/documentation/metal/mtl4commandencoder/barrier(afterstages:beforequeuestages:visibilityoptions:).md, https://developer.apple.com/documentation/metal/mtl4commandencoder/updatefence(_:afterencoderstages:).md, https://developer.apple.com/documentation/metal/mtl4commandencoder/waitforfence(_:beforeencoderstages:).md, https://developer.apple.com/documentation/metal/mtl4visibilityoptions.md, https://developer.apple.com/documentation/metal/mtlstages.md, https://developer.apple.com/documentation/metal/mtlfence.md, https://developer.apple.com/documentation/metal/mtlevent.md, https://developer.apple.com/documentation/metal/mtlsharedevent.md, https://developer.apple.com/documentation/metal/mtlsharedevent/signaledvalue.md, https://developer.apple.com/documentation/metal/mtlsharedevent/wait(untilsignaledvalue:timeoutms:).md, https://developer.apple.com/documentation/metal/mtlsharedevent/valuesignaled(_:).md, https://developer.apple.com/documentation/metal/mtl4argumenttable.md, https://developer.apple.com/documentation/metal/mtl4argumenttabledescriptor.md, https://developer.apple.com/documentation/metal/mtl4argumenttabledescriptor/initializebindings.md, https://developer.apple.com/documentation/metal/mtl4argumenttabledescriptor/maxbufferbindcount.md, https://developer.apple.com/documentation/metal/mtl4argumenttabledescriptor/maxtexturebindcount.md, https://developer.apple.com/documentation/metal/mtl4argumenttable/setaddress(_:index:).md, https://developer.apple.com/documentation/metal/mtl4argumenttable/settexture(_:index:).md, https://developer.apple.com/documentation/metal/mtl4rendercommandencoder.md, https://developer.apple.com/documentation/metal/mtl4rendercommandencoder/setargumenttable(_:stages:).md, https://developer.apple.com/documentation/metal/mtl4renderpassdescriptor.md, https://developer.apple.com/documentation/metal/mtlresidencyset.md, https://developer.apple.com/documentation/metal/mtlresidencyset/requestresidency().md, https://developer.apple.com/documentation/metal/mtlresidencyset/endresidency().md, https://developer.apple.com/documentation/metal/mtldevice/makeresidencyset(descriptor:).md, https://developer.apple.com/documentation/metal/mtl4commitoptions.md, https://developer.apple.com/documentation/metal/mtl4commitfeedback.md, https://developer.apple.com/documentation/metal/mtl4commitfeedbackhandler.md, https://developer.apple.com/documentation/metal/mtl4compiler/makerenderpipelinestate(descriptor:dynamiclinkingdescriptor:compilertaskoptions:)-84kox.md, https://developer.apple.com/documentation/metal/mtlgpufamily.md, https://developer.apple.com/documentation/metal/mtlcommandbuffer/addcompletedhandler(_:).md, https://developer.apple.com/documentation/metal/mtlcommandqueue/makecommandbuffer().md, https://developer.apple.com/documentation/metal/mtlcommandbuffer/encodesignalevent(_:value:).md, https://developer.apple.com/documentation/metalkit/mtkview/currentmtl4renderpassdescriptor.md, https://developer.apple.com/documentation/quartzcore/cametallayer/residencyset.md
> sources: metal-by-tutorials-5e, metal-feature-set-tables-2026-05
> typecheck: macos 26.0
> typecheck-metal: metal4.0

# Command Model: Queues, Allocators, Argument Tables, Residency, and Sync

Contents:
- What a Metal 4 frame holds, and how long each piece lives
- Frame structure
- Command buffers, allocators, and threads
- Argument tables
- Residency
- Synchronization
- Errors and GPU time
- Device and family facts that matter here
- Maintaining older code: Metal 3
- Where else to look

Scope: how work gets from the CPU to an Apple GPU under Metal 4. That covers the
device, the queue, command buffers and their allocators, argument tables,
residency sets, every synchronization primitive, and frames in flight.
Building pipelines is `pipelines-and-render-passes.md`. Drawables, `MTKView`,
`CAMetalLayer`, `CAMetalDisplayLink`, and present are `display-and-upscaling.md`.
Frame pacing policy (fixed or variable step, frame budgets) is outside this
skill. Heaps, storage modes,
and memory budgets are `resources-and-memory.md`. What a compute pass contains is
`compute-and-gpu-driven.md`.

Metal 4 is the default here. It needs an Apple7-or-later GPU (A14, M1, and later)
and OS 26. The runtime gate and the older path are in the last section,
`## Maintaining older code: Metal 3`.

## What a Metal 4 frame holds, and how long each piece lives

A strong engineer's prior is the Metal 3 shape: the queue makes a fresh command
buffer each frame, the command buffer retains what it touches, the encoder binds
resources one by one, and Metal tracks hazards. Metal 4 changes all four, and
each change moves a duty onto the engine.

| Object | Make it | Lifetime | One per |
| --- | --- | --- | --- |
| `MTL4CommandQueue` | `device.makeMTL4CommandQueue()` | App | Independent stream of work |
| `MTL4CommandBuffer` | `device.makeCommandBuffer()`, from the **device** | App; reused every frame | Encoding thread |
| `MTL4CommandAllocator` | `device.makeCommandAllocator()` | App; `reset()` per use | Frame in flight, per encoding thread |
| `MTL4ArgumentTable` | `device.makeArgumentTable(descriptor:)` | App; edited freely | Kind of work |
| `MTLResidencySet` | `device.makeResidencySet(descriptor:)` | Level or app | Group of allocations that live and die together |
| `MTLSharedEvent` | `device.makeSharedEvent()` | App | CPU-visible frame timeline |

What changed, and what it costs you:

- **The command buffer is reusable; the allocator is not.** You may begin a
  command buffer again as soon as you commit it, because the allocator holds
  the encoded commands. The allocator holds them until the GPU finishes, so
  `reset()` it only after that. The symbol page puts the duty on you: every
  command buffer that drew memory from the allocator must be complete before
  the reset. Nothing checks this for you.
- **The command buffer does not retain resources.** It behaves like a Metal 3
  command buffer made with `makeCommandBufferWithUnretainedReferences()`. Keep
  every buffer, texture, and pipeline alive until the frame that uses it has
  signalled completion. Defer releases to the frame timeline in the frame
  structure below. API Validation's unretained-resource check covers only
  `MTLCommandBuffer`, so a Metal 4 use-after-free gets no validation error.
- **Encoders bind nothing directly.** No `setVertexBuffer`, `setFragmentTexture`,
  `setVertexBytes`, `useResource`, or `useHeap`. Bindings go in an
  `MTL4ArgumentTable`. Residency goes in an `MTLResidencySet` that you attach to
  the queue or the command buffer.
- **Nothing is hazard-tracked.** A resource's `hazardTrackingMode` has no effect
  on work submitted to an `MTL4CommandQueue`. Every write that another pass, or
  another stage of the same pass, can read needs a barrier, fence, or event.
  The "Synchronization" section below covers them.
- **There is no blit encoder.** `MTL4ComputeCommandEncoder` takes copies,
  dispatches, and acceleration-structure builds in one pass. They run in its
  `.blit`, `.dispatch`, and `.accelerationStructure` stages. The other encoders
  are `MTL4RenderCommandEncoder` and `MTL4MachineLearningCommandEncoder`. One
  command buffer can hold passes of all three kinds.

A command buffer can go to any `MTL4CommandQueue` of the same device. It has no
`commit()` of its own: the queue commits it.

## Frame structure

This is the Metal 4 frame of Apple's *Drawing a triangle with Metal 4* sample,
rewritten in Swift. One defect in the sample is fixed (see the notes after the
code). The frame is split into encode and submit, and it renders to any
`MTLTexture`, so the same code drives an offscreen target and a drawable. The first block is setup: a pipeline that fills the target with a
colour read from a per-frame buffer. A frame that renders the expected colour
proves that the argument table binding and the buffer rotation work. Run it
with `MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1` to
prove residency as well (see "Residency").
Pipeline compilation choices belong to `pipelines-and-render-passes.md`.

```swift
import Metal

/// The MSL the frame's pipeline compiles. It is the same source as the
/// metal block below, which the gate compiles under -std=metal4.0.
let flatColorShaderSource = """
#include <metal_stdlib>
using namespace metal;

struct FrameUniforms { float4 color; };
struct VertexOut { float4 position [[position]]; };

vertex VertexOut fullscreenVertex(uint vid [[vertex_id]]) {
    float2 p = float2((vid << 1) & 2, vid & 2);
    VertexOut out;
    out.position = float4(p * 2.0 - 1.0, 0.0, 1.0);
    return out;
}

fragment float4 flatColorFragment(constant FrameUniforms& uniforms [[buffer(0)]]) {
    return uniforms.color;
}
"""

/// Builds the pipeline once, at load time, never inside the frame.
func makeFlatColorPipeline(device: any MTLDevice,
                           pixelFormat: MTLPixelFormat) throws -> any MTLRenderPipelineState {
    let library = try device.makeLibrary(source: flatColorShaderSource, options: nil)
    let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())

    let vertexFunction = MTL4LibraryFunctionDescriptor()
    vertexFunction.library = library
    vertexFunction.name = "fullscreenVertex"
    let fragmentFunction = MTL4LibraryFunctionDescriptor()
    fragmentFunction.library = library
    fragmentFunction.name = "flatColorFragment"

    let descriptor = MTL4RenderPipelineDescriptor()
    descriptor.vertexFunctionDescriptor = vertexFunction
    descriptor.fragmentFunctionDescriptor = fragmentFunction
    descriptor.colorAttachments[0].pixelFormat = pixelFormat
    return try compiler.makeRenderPipelineState(descriptor: descriptor)
}
```

```metal
#include <metal_stdlib>
using namespace metal;

struct FrameUniforms { float4 color; };
struct VertexOut { float4 position [[position]]; };

vertex VertexOut fullscreenVertex(uint vid [[vertex_id]]) {
    float2 p = float2((vid << 1) & 2, vid & 2);
    VertexOut out;
    out.position = float4(p * 2.0 - 1.0, 0.0, 1.0);
    return out;
}

fragment float4 flatColorFragment(constant FrameUniforms& uniforms [[buffer(0)]]) {
    return uniforms.color;
}
```

The core frame. The numbered comments are the order that matters.

```swift
import Metal

/// How many frames the CPU may encode ahead of the GPU.
let maxFramesInFlight = 3

/// Matches `FrameUniforms` in the shader source.
struct FrameUniforms {
    var color: SIMD4<Float>
}

enum FrameLoopError: Error {
    case creationFailed(String)
    case gpuTimeout(waitingForFrame: UInt64)
}

final class FrameLoop {
    let device: any MTLDevice
    let queue: any MTL4CommandQueue
    let commandBuffer: any MTL4CommandBuffer      // one, reused every frame
    let allocators: [any MTL4CommandAllocator]   // one per frame in flight
    let uniformBuffers: [any MTLBuffer]          // one per frame in flight
    let argumentTable: any MTL4ArgumentTable     // one, re-pointed every frame
    let residencySet: any MTLResidencySet        // long-lived allocations
    let frameEvent: any MTLSharedEvent           // the CPU-visible frame timeline
    let pipeline: any MTLRenderPipelineState
    private(set) var frameNumber: UInt64 = 0

    init(device: any MTLDevice, pipeline: any MTLRenderPipelineState) throws {
        guard let queue = device.makeMTL4CommandQueue(),
              let commandBuffer = device.makeCommandBuffer(),
              let frameEvent = device.makeSharedEvent() else {
            throw FrameLoopError.creationFailed("queue, command buffer, or shared event")
        }
        var allocators: [any MTL4CommandAllocator] = []
        var uniformBuffers: [any MTLBuffer] = []
        for _ in 0..<maxFramesInFlight {
            guard let allocator = device.makeCommandAllocator(),
                  let buffer = device.makeBuffer(length: MemoryLayout<FrameUniforms>.stride,
                                                 options: .storageModeShared) else {
                throw FrameLoopError.creationFailed("allocator or uniform buffer")
            }
            allocators.append(allocator)
            uniformBuffers.append(buffer)
        }

        let tableDescriptor = MTL4ArgumentTableDescriptor()
        tableDescriptor.maxBufferBindCount = 1   // size to what one draw binds
        let argumentTable = try device.makeArgumentTable(descriptor: tableDescriptor)

        let setDescriptor = MTLResidencySetDescriptor()
        setDescriptor.label = "FrameLoop long-lived"
        setDescriptor.initialCapacity = maxFramesInFlight
        let residencySet = try device.makeResidencySet(descriptor: setDescriptor)
        for buffer in uniformBuffers {
            residencySet.addAllocation(buffer)
        }
        residencySet.commit()                 // staged adds take effect only here
        queue.addResidencySet(residencySet)   // applied to every commit on this queue

        frameEvent.signaledValue = 0

        self.device = device
        self.queue = queue
        self.commandBuffer = commandBuffer
        self.allocators = allocators
        self.uniformBuffers = uniformBuffers
        self.argumentTable = argumentTable
        self.residencySet = residencySet
        self.frameEvent = frameEvent
        self.pipeline = pipeline
    }

    /// Adds a long-lived allocation (an offscreen render target, a mesh buffer)
    /// to the queue's residency set. Call it outside the frame.
    func makeResident(_ allocation: any MTLAllocation) {
        residencySet.addAllocation(allocation)
        residencySet.commit()
    }

    /// Encodes one frame into `target`. Follow it with exactly one submit.
    func encodeFrame(into target: any MTLTexture, color: SIMD4<Float>) throws {
        frameNumber += 1
        let slot = Int(frameNumber % UInt64(maxFramesInFlight))

        // 1. Frames-in-flight wait. The frame that last used this slot is
        //    `frameNumber - maxFramesInFlight`. Block until the GPU is done
        //    with it, and treat a timeout as a hung GPU, never as "go ahead".
        if frameNumber > UInt64(maxFramesInFlight) {
            let previousUser = frameNumber - UInt64(maxFramesInFlight)
            guard frameEvent.wait(untilSignaledValue: previousUser, timeoutMS: 1_000) else {
                throw FrameLoopError.gpuTimeout(waitingForFrame: previousUser)
            }
        }

        // 2. Per-frame allocator reset. Legal only after the wait above.
        let allocator = allocators[slot]
        allocator.reset()

        // 3. CPU writes to this slot's buffer, also only after the wait.
        let uniforms = uniformBuffers[slot]
        uniforms.contents().storeBytes(of: FrameUniforms(color: color), as: FrameUniforms.self)

        // 4. Begin. This also clears any useResidencySet calls from last frame.
        commandBuffer.beginCommandBuffer(allocator: allocator)
        commandBuffer.label = "Frame \(frameNumber)"

        // 5. One render pass.
        let pass = MTL4RenderPassDescriptor()
        pass.colorAttachments[0].texture = target
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
        pass.colorAttachments[0].storeAction = .store
        guard let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: pass, options: []) else {
            commandBuffer.endCommandBuffer()
            queue.signalEvent(frameEvent, value: frameNumber)   // keep the timeline whole
            throw FrameLoopError.creationFailed("render encoder")
        }
        encoder.setRenderPipelineState(pipeline)

        // 6. Argument table binding. Metal snapshots the table at each draw,
        //    so one table serves every frame in flight.
        argumentTable.setAddress(uniforms.gpuAddress, index: 0)
        encoder.setArgumentTable(argumentTable, stages: .fragment)
        encoder.drawPrimitives(primitiveType: .triangle, vertexStart: 0, vertexCount: 3)
        encoder.endEncoding()

        // 7. End. Committing a command buffer that was not ended is an error.
        commandBuffer.endCommandBuffer()
    }

    /// Offscreen submit: commit, then put this frame's number on the timeline.
    func submitFrame() {
        queue.commit([commandBuffer], options: nil)
        queue.signalEvent(frameEvent, value: frameNumber)
    }

    /// Blocks until the GPU has finished every submitted frame. Call it before
    /// reading a render target on the CPU, or before releasing resources.
    func waitUntilIdle(timeoutMS: UInt64 = 5_000) throws {
        guard frameEvent.wait(untilSignaledValue: frameNumber, timeoutMS: timeoutMS) else {
            throw FrameLoopError.gpuTimeout(waitingForFrame: frameNumber)
        }
    }
}
```

An offscreen driver is three calls per frame. Make the target resident once.
`CAMetalLayer`'s header says that whatever you render into must be resident.
On this M4 Pro (macOS 27.0.1), an offscreen attachment left out of every set
still rendered the right pixel. Shader Validation reported the fault: with
`MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1`, every
commit printed "Resource residency error - MTLTexture is not resident at the
time of commit". API Validation reported nothing. A correct image does not make
skipping residency safe.

```swift
func renderOffscreen(device: any MTLDevice, target: any MTLTexture, frames: Int) throws {
    let pipeline = try makeFlatColorPipeline(device: device, pixelFormat: target.pixelFormat)
    let loop = try FrameLoop(device: device, pipeline: pipeline)
    loop.makeResident(target)
    for frame in 0..<frames {
        let shade = Float(frame % 256) / 255
        try loop.encodeFrame(into: target, color: SIMD4<Float>(shade, 0.5, 0.25, 1))
        loop.submitFrame()
    }
    try loop.waitUntilIdle()
}
```

**On-screen drawable only.** These lines replace `submitFrame()` when the
target is a drawable. They are not part of the core frame.

```swift
import MetalKit

extension FrameLoop {
    /// Once, after init. Drawable textures live in the layer's own residency
    /// set, which Core Animation keeps current. Never modify that set.
    func attachDrawableResidency(of layer: CAMetalLayer) {
        queue.addResidencySet(layer.residencySet)
    }

    @MainActor   // MTKView's properties are main-actor isolated
    func drawFrame(in metalView: MTKView, color: SIMD4<Float>) throws {
        // Return before encodeFrame, so a skipped frame never takes a slot.
        guard let drawable = metalView.currentDrawable else { return }
        try encodeFrame(into: drawable.texture, color: color)
        queue.waitForDrawable(drawable)   // GPU timeline: display has released it
        queue.commit([commandBuffer], options: nil)
        queue.signalDrawable(drawable)    // after the last commit that targets it
        drawable.present()                // after signalDrawable, never before
        queue.signalEvent(frameEvent, value: frameNumber)
    }
}
```

Why the code differs from Apple's sample, and the gotchas behind each step:

- **The sample's wait gives up after 10 ms and carries on.** It calls
  `wait(untilSignaledValue:timeoutMS:)` with 10 ms, logs a timeout, and then
  resets the allocator anyway. Resetting an allocator the GPU still reads
  breaks the one rule the allocator page states. Above, a timeout throws.
- **The sample's first wait is a no-op.** It starts waiting at frame
  `maxFramesInFlight`, for frame 0, which was never submitted. The value 0 is
  signalled from the start, so the wait returns at once. The code above starts
  at the first frame whose slot was used before.
- **Signal every frame number, including failed frames.**
  `wait(untilSignaledValue:)` is satisfied by any value at or above the target.
  A skipped signal is therefore covered by the next one, but only once the next
  frame is submitted. Signalling on the failure path keeps `waitUntilIdle()`
  honest.
- **`signalEvent(_:value:)` is a queue operation.** It fires after all work
  committed to the queue before it has finished. Call it after the commit,
  never before.
- **`beginCommandBuffer(allocator:)` drops the command buffer's residency
  sets.** Per-frame sets attached with `useResidencySet(_:)` must be attached
  again after every begin. Queue sets persist, which is why long-lived data
  goes there.
- **`commit(_:options:)` with an array is the Swift spelling.** Apple's
  Objective-C `commit:count:` takes a C array. Order in the array is
  significant (see the next section).
- **In `async` code, `wait(untilSignaledValue:timeoutMS:)` will not compile
  in Swift 6 mode.** Swift 5 mode only warns. The SDK marks the method
  `NS_SWIFT_UNAVAILABLE_FROM_ASYNC`. In `async` code, use
  `await frameEvent.valueSignaled(n)`. It has no timeout, so pair it with your
  own watchdog.
- **Frames in flight on screen.** Apple's rule is to keep no more copies than
  the drawable count. `CAMetalLayer.maximumDrawableCount` accepts only 2 or 3,
  and the default is 3. Offscreen, the count is a latency and memory choice.
- **Submit early, present late.** Put shadow, G-buffer, and compute work in a
  command buffer that you commit as soon as it is encoded. Call
  `waitForDrawable(_:)` only before the last commit, the one that touches the
  drawable. A held drawable is a scarce swap-chain image. `signalDrawable(_:)`
  fails if you call it twice or after `present()`.
- **`MTKView` depth and MSAA textures.** From macOS 26.4 and iOS 26.4,
  `metalView.residencySet` holds the textures the view creates. Add it beside
  the layer's set. On 26.0 to 26.3 that property does not exist, so create
  those textures yourself and put them in your own set.
  `currentMTL4RenderPassDescriptor` is compiled out of Simulator builds.

## Command buffers, allocators, and threads

- **Parallel encoding means one command buffer and one allocator per thread.**
  An allocator serves one command buffer at a time. Each worker therefore needs
  its own set of `maxFramesInFlight` allocators. Commit the workers' buffers
  together in one `commit(_:options:)` array. That replaces
  `MTLParallelRenderCommandEncoder`, and it works for any pass kind.
- **One render pass across several command buffers.** Use
  `MTL4RenderEncoderOptions.suspending` and `.resuming`. Inside the commit
  array, the first buffer's pass only suspends, the last only resumes, and
  every buffer between does both. No compute or machine-learning pass may sit
  between them in submission order. A buffer must not open a suspending pass
  if it already holds a resuming one.
- **`endCommandBuffer()` frees the allocator for another command buffer. It
  does not free its memory.** You can encode several command buffers in turn
  through one allocator. `reset()` still waits until the GPU has finished all
  of them.
- **Commit from any thread.** The queue sends work to the GPU at commit. An
  `MTL4CommitOptions` instance is not thread-safe, so don't share one between
  committing threads without a lock.
- **Measure command memory.** `allocator.allocatedSize()` reports the bytes in
  the allocator's internal heaps. Read it after a heavy frame to see what your
  encoding costs per frame in flight.

## Argument tables

- **Limits come from the SDK header:** `maxBufferBindCount` at most 31,
  `maxTextureBindCount` at most 128, `maxSamplerStateBindCount` at most 16.
  These match the per-stage limits in the Feature Set Tables for Apple6 and
  later. Inline `constexpr` samplers in MSL count against the 16.
- **Size the table to the largest binding set you use.** A table costs memory
  for every slot it declares.
- **Slots are not initialized by default.** `initializeBindings` defaults to
  `false`. Set it to `true` to start every slot at nil, for example while you
  debug a shader that reads a slot you forgot to fill.
- **There is no `setBytes`.** Per-frame constants live in a buffer, or a range
  of one, per frame in flight, bound with `setAddress(buffer.gpuAddress + offset,
  index:)`. The book's `setVertexBytes` habit has no port.
- **Textures and samplers bind by `gpuResourceID`.** Use
  `setTexture(texture.gpuResourceID, index:)` and
  `setSamplerState(sampler.gpuResourceID, index:)`. `setResource(_:bufferIndex:)`
  puts a resource ID into a buffer slot.
- **Metal snapshots the table when you encode a draw, dispatch, or
  execute.** Change a slot between two draws and each draw sees its own value.
  That is why one table per kind of work is enough. Apple's tip is the same:
  keep separate tables for unlike work, each holding that work's shared
  resources.
- **Binding is per stage.** On a render encoder, `setArgumentTable(_:stages:)`
  takes `MTLRenderStages`, so bind only where shaders read. Compute and
  machine-learning encoders take `setArgumentTable(_:)`.
- **Keep binding indices in one shared header** that both the Swift side and
  the `.metal` side include. They are table slots now, not encoder slots. The
  convention carries over unchanged.

## Residency

A resource the GPU touches must be in a residency set attached to the command
buffer or its queue. In Metal 4 no other route exists. Shader Validation
reports a "resource not resident" error for a resource outside every attached
set. Without validation, skipping residency often compiles and may even render
for a while. Then it shows up as pink or missing textures, GPU memory faults, or
a hang.

Shader Validation reports to the unified log unless
`MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1` is set. In the log, the reports sit
under subsystem `com.apple.Metal`, category `GPUDebug`, and `log stream` shows
their text as `<private>`. Set both variables to read the report.

Runtime check, on this M4 Pro under macOS 27.0.1: the frame structure above
ran with its uniform buffers left out of the residency set. Without
validation, it rendered the right colour. With `MTL_SHADER_VALIDATION=1`, the
target stayed all zeros and stderr stayed empty. With
`MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1` added, it printed "Invalid load in
'device' or 'constant' address space" for the fragment function and named the
buffer as `resident:No`. Treat "renders fine" as no evidence of correct
residency. Treat a frame that goes blank only under validation as a residency
bug until you rule it out.

- **Queue sets** (`addResidencySet(_:)`) apply to every command buffer at
  commit. Put app-lifetime and level-lifetime data there.
- **Command-buffer sets** (`useResidencySet(_:)`) apply to one commit and are
  cleared by the next begin. Use them for data that varies frame to frame.
- **At most 32 sets** per queue and 32 per command buffer. The header and the
  Feature Set Tables agree, and both list residency sets from Apple6.
- **Edits are staged.** `addAllocation(_:)` and `removeAllocation(_:)` do
  nothing until `commit()` on the set. Duplicates are ignored. Residency is
  the union of every attached set, so an allocation held by two sets stays
  resident when one set drops it.
- **One resource from a heap makes the whole heap resident.** Budget for that
  (`resources-and-memory.md`).
- **The set's methods are not thread-safe**, and sets don't take sparse heaps
  or sparse textures.
- **Removing a set from a queue does not detach it** from command buffers that
  were already committed.
- **Move the residency cost off the frame.** By default Metal does the CPU work
  of making a set resident at the first commit that uses it, which delays that
  submission. Call `requestResidency()` at a calm moment instead. Under memory
  pressure from other apps, Metal may postpone part of that work.
  `endResidency()` hands the memory back. For level streaming, keep one set per
  zone, call `requestResidency()` on the next zone while the current one plays,
  and call `endResidency()` on the zone you leave.

## Synchronization

Pick the smallest scope that resolves the conflict. A wider scope holds back
more GPU work.

| Scope | Primitive | Call |
| --- | --- | --- |
| Stages within one pass | Intrapass barrier | `barrier(afterEncoderStages:beforeEncoderStages:visibilityOptions:)` |
| Pass to pass, same queue, precise | `MTLFence` | `updateFence(_:afterEncoderStages:)` then `waitForFence(_:beforeEncoderStages:)` |
| Many earlier passes feed this one | Consumer queue barrier | `barrier(afterQueueStages:beforeStages:visibilityOptions:)` |
| This pass feeds many later ones | Producer queue barrier (Metal 4 encoders only) | `barrier(afterStages:beforeQueueStages:visibilityOptions:)` |
| Across queues, one device | `MTLEvent` | `queue.signalEvent(_:value:)` / `queue.waitForEvent(_:value:)` |
| CPU, other devices, other processes | `MTLSharedEvent` | the same calls, plus `signaledValue`, `wait(untilSignaledValue:timeoutMS:)`, `notify(_:atValue:block:)` |

What a port from Metal 3, or from another API, gets wrong:

- **A conflict is any write that can overlap another access**, through table
  bindings, argument buffers, or attachments. An attachment loads implicitly at
  pass start when `loadAction == .load`, and stores at pass end when
  `storeAction == .store`. Concurrent reads never conflict. Atomics, attachment
  accesses in primitive order, raster-order-group accesses, and tile-shader
  accesses in tile-dispatch order are already ordered.
- **Dispatches in one Metal 4 compute pass run concurrently**, and so do its
  copies and its dispatches. A Metal 3 compute encoder ran them serially unless
  you asked for `.concurrent`. A port needs an intrapass barrier wherever the
  old code relied on serial order.
- **Name only the stage that consumes.** A compute pass writes particle data and
  the next render pass reads it in the vertex stage. Barrier `.dispatch`
  before `.vertex` and nothing more. Over-broad masks cost GPU time.
- **On Apple GPUs, an intrapass barrier cannot wait on `.fragment` or
  `.tile`.** A draw that needs another pixel's result from an earlier draw in
  the same pass must start a new pass. Synchronize the two passes with a queue
  barrier or a fence. A draw that reads only its own pixel needs no barrier.
- **Fences:** encode the update and the wait as close to the conflicting
  commands as you can. Submit the producer before the consumer. To reuse a fence
  in one pass, encode the wait first and the update second. Encoding the update
  and then the wait on the same fence in one pass can deadlock the GPU. The
  Feature Set Tables cap fences at 32,768.
- **A Metal 4 fence works on one queue only.** The fence article says so. The
  `MTLFence` symbol page says fences work across `MTL4CommandQueue` and
  `MTLCommandQueue`. The SDK settles it: the header for
  `waitForFence(_:beforeEncoderStages:)` requires the update and the wait to be
  on the same command queue. The SDK wins, so use an `MTLEvent` across queues.
- **Events are monotonic 64-bit counters that start at 0.** A smaller signal is
  ignored. Several producers cannot share one event the way they would share a
  semaphore, so give each producer its own event and make consumers wait on
  each one. `MTLSharedEvent` costs more than `MTLEvent`, so use it only when
  the CPU or another device is involved.
- **A Metal 4 GPU wait that times out lets the queue continue.** In Metal 3 the
  same timeout ends the command buffer with a timeout error. A missing
  `signalEvent` in Metal 4 can therefore surface as a data race instead of an
  error. Keep each signal close to its wait.
- **Visibility options.** `.device` (the default) flushes caches to the GPU
  coherence point. Add `.resourceAlias` when the two sides reach the same memory
  through aliased virtual addresses (`resources-and-memory.md`).
- **Doc error:** the parameter descriptions on the intrapass-barrier symbol
  page are swapped. Its discussion and the SDK header have it right:
  `afterEncoderStages` is the earlier work waited on, and `beforeEncoderStages`
  is the later work that waits.

The particle case as code:

```swift
func encodeSimulateThenDraw(commandBuffer: any MTL4CommandBuffer,
                            pass: MTL4RenderPassDescriptor,
                            simulate: any MTLComputePipelineState,
                            draw: any MTLRenderPipelineState,
                            table: any MTL4ArgumentTable,
                            particles: any MTLBuffer,
                            count: Int) {
    table.setAddress(particles.gpuAddress, index: 0)

    guard let compute = commandBuffer.makeComputeCommandEncoder() else { return }
    compute.setComputePipelineState(simulate)
    compute.setArgumentTable(table)
    compute.dispatchThreads(threadsPerGrid: MTLSize(width: count, height: 1, depth: 1),
                            threadsPerThreadgroup: MTLSize(width: 64, height: 1, depth: 1))
    compute.endEncoding()

    guard let render = commandBuffer.makeRenderCommandEncoder(descriptor: pass, options: []) else { return }
    // Consumer barrier: this pass's vertex stage, and every later pass's,
    // waits for the dispatch stage of every earlier pass on the queue.
    // The fragment stage is left free to overlap.
    render.barrier(afterQueueStages: .dispatch, beforeStages: .vertex, visibilityOptions: .device)
    render.setRenderPipelineState(draw)
    render.setArgumentTable(table, stages: .vertex)
    render.drawPrimitives(primitiveType: .point, vertexStart: 0, vertexCount: count)
    render.endEncoding()
}
```

## Errors and GPU time

An `MTL4CommandBuffer` has no `status`, no `error`, no completed handler, and
no `waitUntilCompleted()`. Results come back through the commit instead.

```swift
func commitWithFeedback(queue: any MTL4CommandQueue,
                        commandBuffer: any MTL4CommandBuffer,
                        frame: UInt64) {
    let options = MTL4CommitOptions()
    options.addFeedbackHandler { feedback in
        if let error = feedback.error {
            print("frame \(frame) failed on the GPU: \(error)")
        }
        let gpuMilliseconds = (feedback.gpuEndTime - feedback.gpuStartTime) * 1_000
        _ = gpuMilliseconds   // feed the frame-time HUD or the adaptive-quality loop
    }
    queue.commit([commandBuffer], options: options)
}
```

- The handler is `@Sendable` and runs on a dispatch queue. By default that is
  an internal queue. To pick it, set `MTL4CommandQueueDescriptor.feedbackQueue`
  to a **serial** queue and create the queue with
  `makeMTL4CommandQueue(descriptor:)`.
- The queue's error codes (`MTL4CommandQueueError.Code`) are `.timeout`,
  `.notPermitted`, `.outOfMemory`, `.accessRevoked` (too many hangs or
  timeouts), and `.internal`. The docs also list `.deviceRemoved`, but the SDK
  deprecates it because it cannot occur on Apple silicon, and the SDK wins.
  Don't handle it.
- On Apple GPUs an out-of-bounds device or threadgroup access can fault the
  hardware and end the command buffer, where a discrete GPU might tolerate it.
  Shader Validation finds these (`gpu-debugging-and-profiling.md`).
- GPU start and end times arrive per commit, not per pass. For pass timing, use
  counter heaps (`gpu-debugging-and-profiling.md`).

## Device and family facts that matter here

- On Apple silicon there is one GPU, and `MTLCreateSystemDefaultDevice()`
  returns it. Device enumeration, eGPU hot-plug, and display-to-GPU matching
  are Intel-Mac concerns and outside this skill.
- Gate on Apple families, `.metal4`, and per-feature properties. The SDK
  deprecates `MTLGPUFamily.mac2` in macOS and iOS 27 and names `.apple7` as
  its replacement (`MTLDevice.h`). Where a feature has its own device property,
  query the property. Never infer anything from `device.name`.
- Family map, from the Feature Set Tables (May 2026): A13 is Apple6 (Metal 3
  model only); A14 and M1 are Apple7; A15, A16, and M2 are Apple8; A17 Pro, A18,
  M3, and M4 are Apple9; A19 and M5 are Apple10. The tables now list Apple
  families only. Where the `MTLGPUFamily` doc comments disagree, the tables win.
- Metal-4-only capabilities in the tables (all Apple7+): argument tables,
  command allocators, decoupled queues and command buffers, command barriers,
  compilation contexts, pipeline dataset serialization, flexible render pipeline
  state, machine-learning encoding, tensors, and counter heaps (32 per process).

## Maintaining older code: Metal 3

Snippets in this section compile at the file's macOS 26.0 floor; they are not compile-checked against earlier OS releases.

**When the Metal 3 path applies.** Two cases:

- The GPU is below Apple7, so it fails `supportsFamily(.metal4)` whatever the
  OS. On iPhone and iPad that means A13 and earlier. Every Apple silicon Mac is
  Apple7 or later.
- The OS is before 26.0 on any device: the `MTL4` types do not exist there.

A third case reaches Metal 4 apps too. MPS image kernels and
`MPSMatrixMultiplication` encode only onto a Metal 3 `MTLCommandBuffer`. A
Metal 4 renderer that needs them keeps a Metal 3 queue beside its
`MTL4CommandQueue`. Events order work across any mix of the two queue kinds.

**How to gate.** Decide once, at launch, and build one renderer per path.
Apple's own triangle sample ships two complete renderers and picks one with
the family check. Both conditions are needed: `#available` for the OS, and the
family for the GPU.

```swift
enum CommandModel {
    case metal4(any MTL4CommandQueue)
    case metal3(any MTLCommandQueue)
}

func chooseCommandModel(device: any MTLDevice) -> CommandModel? {
    if #available(macOS 26.0, iOS 26.0, *), device.supportsFamily(.metal4),
       let queue = device.makeMTL4CommandQueue() {
        return .metal4(queue)
    }
    return device.makeCommandQueue().map { CommandModel.metal3($0) }
}
```

The queue kind you create decides which type family the rest of the renderer
uses. The `MTL4` types are separate protocols, not subclasses of the Metal 3
ones: an `MTL4CommandBuffer` is not an `MTLCommandBuffer`. Resources, pipeline
states, events, and residency sets are shared by both paths. Residency sets exist from macOS 15 and iOS 18.

**The Metal 3 frame**, for comparison. A fresh command buffer comes from the
queue each frame and retains what it uses. A semaphore bounds frames in flight.
The completed handler releases a slot.

```swift
import MetalKit

final class Metal3FrameLoop {
    let queue: any MTLCommandQueue
    let inFlight = DispatchSemaphore(value: 3)

    init(queue: any MTLCommandQueue) {
        self.queue = queue
    }

    @MainActor
    func drawFrame(in metalView: MTKView, encode: (any MTLRenderCommandEncoder) -> Void) {
        // Take the drawable and descriptor first: an early return after the
        // semaphore wait would leak a slot and stall rendering for good.
        guard let drawable = metalView.currentDrawable,
              let pass = metalView.currentRenderPassDescriptor else { return }
        inFlight.wait()
        guard let commandBuffer = queue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: pass) else {
            inFlight.signal()
            return
        }
        encode(encoder)
        encoder.endEncoding()
        commandBuffer.present(drawable)
        let semaphore = inFlight
        commandBuffer.addCompletedHandler { _ in semaphore.signal() }
        commandBuffer.commit()
    }
}
```

**How each Metal 3 concept maps to Metal 4.**

| Metal 3 | Metal 4 | What the port must add |
| --- | --- | --- |
| `queue.makeCommandBuffer()` per frame | one `device.makeCommandBuffer()`, `beginCommandBuffer(allocator:)` per frame | an allocator per frame in flight, reset only after the GPU finishes |
| command buffer retains resources | retains nothing | explicit lifetime until the frame's event value signals |
| `commandBuffer.commit()` | `queue.commit(_:options:)` | an `endCommandBuffer()` before it |
| `addCompletedHandler` + `DispatchSemaphore` | `queue.signalEvent(_:value:)` + `MTLSharedEvent.wait(untilSignaledValue:timeoutMS:)` | a frame counter as the event value |
| `waitUntilCompleted()`, `status`, `error` | shared-event wait; `MTL4CommitFeedback` | a feedback handler for errors and GPU time |
| `commandBuffer.present(drawable)` | `waitForDrawable`, commit, `signalDrawable`, `present()` | the four calls in that order |
| `encodeSignalEvent` / `encodeWaitForEvent` on the buffer | `signalEvent` / `waitForEvent` on the queue | nothing beyond the move |
| `setVertexBuffer`, `setFragmentTexture`, `setVertexBytes` | `MTL4ArgumentTable` slots by `gpuAddress` / `gpuResourceID` | a buffer for every former bytes binding |
| `useResource`, `useHeap` per encoder | residency sets on the queue or command buffer | the sets, filled ahead of time |
| automatic hazard tracking for tracked resources | none; `hazardTrackingMode` ignored | a barrier, fence, or event at every write-then-read |
| serial compute dispatches by default | concurrent dispatches | intrapass barriers where order mattered |
| `MTLBlitCommandEncoder`, `MTLAccelerationStructureCommandEncoder` | `MTL4ComputeCommandEncoder` stages `.blit`, `.accelerationStructure` | nothing beyond the move |
| `MTLParallelRenderCommandEncoder` | suspending and resuming passes across command buffers | one allocator per thread |
| fence across queues on one device | fence on one queue only | an event where a fence crossed queues |
| GPU wait timeout ends the command buffer | GPU wait timeout lets the queue continue | signals placed close to their waits |
| `MTLStoreActionOptions`, tessellation | removed | mesh shaders in place of tessellation (`compute-and-gpu-driven.md`) |

The *Metal by Tutorials* book (5th edition) teaches the Metal 3 column
throughout: per-frame command buffers, `setVertexBytes` for anything under
4 KB, and `useResource` for argument buffers. Its techniques port, but its API
spellings do not.

## Where else to look

- `pipelines-and-render-passes.md`: compiling pipelines without hitches, render
  pass load and store choices, and attachments.
- `display-and-upscaling.md`: `MTKView` against `CAMetalLayer` against
  `CAMetalDisplayLink`, drawable acquisition, and present.
- `resources-and-memory.md`: heaps, storage modes, placement and sparse
  resources, and the memory budget behind residency.
- `compute-and-gpu-driven.md`: what goes in a compute pass, indirect command
  buffers, and GPU-driven submission.
- `apple-gpu-tbdr.md`: why fragment-stage barriers are restricted on Apple GPUs.
- `gpu-debugging-and-profiling.md`: API and Shader Validation, capture scoped to
  an `MTL4CommandQueue`, and counter heaps.
- `cpp-and-rust.md`: the same frame in metal-cpp and objc2-metal.
