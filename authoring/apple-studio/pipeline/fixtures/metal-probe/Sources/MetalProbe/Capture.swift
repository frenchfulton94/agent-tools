import Foundation
import Metal

enum CaptureProbeError: Error {
    case creationFailed(String)
    case gpuTimeout(frame: Int)
    case computeMismatch(matches: Int, count: Int)
    case traceMissing(String)
}

/// `capture`: three labelled frames and one compute dispatch, all inside one
/// `begin()`...`end()` span of the reference's device capture scope
/// (`FrameCapture`). The frames use the reference's `encodeLabelledFrame`, so
/// the trace has the grouping that the reference's `gpudebug` paths assume.
@MainActor
func runCapture(device: any MTLDevice, url: URL, compute: Bool, compileInCapture: Bool) throws {
    let manager = MTLCaptureManager.shared()
    print("supports gpuTraceDocument: \(manager.supportsDestination(.gpuTraceDocument))")

    let target = try makeOffscreenTarget(device: device)
    let pipeline = try makeFlatColorPipeline(device: device, pixelFormat: target.pixelFormat)
    guard let queue = device.makeMTL4CommandQueue(),
          let commandBuffer = device.makeCommandBuffer(),
          let allocator = device.makeCommandAllocator(),
          let frameDone = device.makeSharedEvent(),
          let uniforms = device.makeBuffer(length: MemoryLayout<FrameUniforms>.stride,
                                           options: .storageModeShared) else {
        throw CaptureProbeError.creationFailed("queue, command buffer, allocator, event, or buffer")
    }
    uniforms.label = "Frame uniforms"
    let residency = try device.makeResidencySet(descriptor: MTLResidencySetDescriptor())
    residency.addAllocation(target)
    residency.addAllocation(uniforms)
    residency.commit()
    queue.addResidencySet(residency)
    let tableDescriptor = MTL4ArgumentTableDescriptor()
    tableDescriptor.maxBufferBindCount = 1
    let table = try device.makeArgumentTable(descriptor: tableDescriptor)

    // Compiled before the capture starts, as an engine compiles at load time.
    // `--compile-in-capture` moves the compile inside the capture instead.
    var addPipeline = compute && !compileInCapture ? try makeAddArraysPipeline(device: device) : nil

    let capture = FrameCapture(device: device)
    try capture.captureNextFrame(to: url)
    capture.scope.begin()
    for frame in 0..<3 {
        // One frame in flight: the wait at the end of the previous frame makes
        // this reset and this CPU write safe.
        allocator.reset()
        uniforms.contents().storeBytes(of: FrameUniforms(color: SIMD4<Float>(1, 0.5, 0.25, 1)),
                                       as: FrameUniforms.self)
        let pass = MTL4RenderPassDescriptor()
        pass.colorAttachments[0].texture = target
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
        pass.colorAttachments[0].storeAction = .store
        encodeLabelledFrame(queue: queue, commandBuffer: commandBuffer, allocator: allocator,
                            pass: pass,
                            drawOpaque: { encoder in
                                encoder.setRenderPipelineState(pipeline)
                                table.setAddress(uniforms.gpuAddress, index: 0)
                                encoder.setArgumentTable(table, stages: .fragment)
                                encoder.drawPrimitives(primitiveType: .triangle,
                                                       vertexStart: 0, vertexCount: 3)
                            },
                            frameIndex: frame)
        let value = UInt64(frame + 1)
        queue.signalEvent(frameDone, value: value)
        guard frameDone.wait(untilSignaledValue: value, timeoutMS: 5_000) else {
            throw CaptureProbeError.gpuTimeout(frame: frame)
        }
        print("frame \(frame) ok")
    }
    if compute {
        let count = 4096
        if addPipeline == nil {
            addPipeline = try makeAddArraysPipeline(device: device)
        }
        let matches = try runAddArrays(device: device, queue: queue, pipeline: addPipeline!, count: count)
        guard matches == count else { throw CaptureProbeError.computeMismatch(matches: matches, count: count) }
        print("compute ok \(count)")
    }
    capture.scope.end()
    print("isCapturing after end: \(manager.isCapturing)")

    guard FileManager.default.fileExists(atPath: url.path) else {
        throw CaptureProbeError.traceMissing(url.path)
    }
    print("wrote \(url.path)")
}
