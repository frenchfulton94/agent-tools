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
