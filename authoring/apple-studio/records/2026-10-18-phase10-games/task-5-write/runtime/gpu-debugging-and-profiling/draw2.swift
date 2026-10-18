import Metal
import Foundation

// ---- snippet under test (same text as the reference) ----
enum TraceError: Error { case captureLayerMissing }

/// Records every command buffer any queue of `device` commits between
/// `start` and `stop` into a .gputrace bundle at `url`.
func startTrace(device: any MTLDevice, url: URL) throws {
    let manager = MTLCaptureManager.shared()
    // False unless the process launched with MTL_CAPTURE_ENABLED=1
    // or carries MetalCaptureEnabled = YES in its Info.plist.
    guard manager.supportsDestination(.gpuTraceDocument) else {
        throw TraceError.captureLayerMissing
    }
    let descriptor = MTLCaptureDescriptor()
    descriptor.captureObject = device
    descriptor.destination = .gpuTraceDocument
    descriptor.outputURL = url          // must end in .gputrace
    try manager.startCapture(with: descriptor)
}

func stopTrace() {
    MTLCaptureManager.shared().stopCapture()
}
// ---- end snippet ----

let device = MTLCreateSystemDefaultDevice()!
let queue = device.makeMTL4CommandQueue()!
let allocator = device.makeCommandAllocator()!
let commandBuffer = device.makeCommandBuffer()!

let src = """
#include <metal_stdlib>
using namespace metal;
struct V { float4 p [[position]]; float4 c; };
vertex V tri_vertex(uint vid [[vertex_id]]) {
    float2 pos[3] = { float2(-0.8, -0.8), float2(0.8, -0.8), float2(0.0, 0.8) };
    V o; o.p = float4(pos[vid], 0, 1); o.c = float4(vid == 0, vid == 1, vid == 2, 1); return o;
}
fragment float4 tri_fragment(V in [[stage_in]]) { return in.c; }
"""
let library = try! device.makeLibrary(source: src, options: nil)
let compiler = try! device.makeCompiler(descriptor: MTL4CompilerDescriptor())
let vfd = MTL4LibraryFunctionDescriptor(); vfd.name = "tri_vertex"; vfd.library = library
let ffd = MTL4LibraryFunctionDescriptor(); ffd.name = "tri_fragment"; ffd.library = library
let rpd = MTL4RenderPipelineDescriptor()
rpd.label = "Triangle PSO"
rpd.vertexFunctionDescriptor = vfd
rpd.fragmentFunctionDescriptor = ffd
rpd.colorAttachments[0].pixelFormat = .rgba8Unorm
let pso = try! compiler.makeRenderPipelineState(descriptor: rpd)

let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 128, height: 128, mipmapped: false)
td.usage = [.renderTarget]
td.storageMode = .private
let target = device.makeTexture(descriptor: td)!
target.label = "Offscreen target"
let residency = try! device.makeResidencySet(descriptor: MTLResidencySetDescriptor())
residency.addAllocation(target)
residency.commit()
if ProcessInfo.processInfo.environment["SKIP_RESIDENCY"] == nil { queue.addResidencySet(residency) }
let event = device.makeSharedEvent()!

let url = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "draw.gputrace")
if ProcessInfo.processInfo.environment["MTL_CAPTURE_ENABLED"] != nil { try! startTrace(device: device, url: url) }
for frame in 0..<2 {
    allocator.reset()
    commandBuffer.beginCommandBuffer(allocator: allocator)
    commandBuffer.label = "Frame \(frame)"
    commandBuffer.pushDebugGroup("Frame \(frame)")
    let rp = MTL4RenderPassDescriptor()
    rp.colorAttachments[0].texture = target
    rp.colorAttachments[0].loadAction = .clear
    rp.colorAttachments[0].storeAction = .store
    let enc = commandBuffer.makeRenderCommandEncoder(descriptor: rp)!
    enc.label = "Forward pass"
    enc.pushDebugGroup("Opaque")
    enc.setRenderPipelineState(pso)
    enc.drawPrimitives(primitiveType: .triangle, vertexStart: 0, vertexCount: 3)
    enc.popDebugGroup()
    enc.endEncoding()
    commandBuffer.popDebugGroup()
    commandBuffer.endCommandBuffer()
    queue.commit([commandBuffer])
    queue.signalEvent(event, value: UInt64(frame + 1))
    _ = event.wait(untilSignaledValue: UInt64(frame + 1), timeoutMS: 5000)
}
if ProcessInfo.processInfo.environment["MTL_CAPTURE_ENABLED"] != nil { stopTrace() }
print("wrote", url.path, FileManager.default.fileExists(atPath: url.path))
