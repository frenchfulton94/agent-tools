import Metal
import Foundation

let device = MTLCreateSystemDefaultDevice()!
let queue = device.makeMTL4CommandQueue()!
let allocator = device.makeCommandAllocator()!
let commandBuffer = device.makeCommandBuffer()!

let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 64, height: 64, mipmapped: false)
td.usage = [.renderTarget]
td.storageMode = .private
let target = device.makeTexture(descriptor: td)!
target.label = "Offscreen target"

let rsd = MTLResidencySetDescriptor()
let residency = try! device.makeResidencySet(descriptor: rsd)
residency.addAllocation(target)
residency.commit()
queue.addResidencySet(residency)

let event = device.makeSharedEvent()!
let mode = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "device"
let url = URL(fileURLWithPath: CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "probe.gputrace")

let manager = MTLCaptureManager.shared()
print("supports gpuTraceDocument:", manager.supportsDestination(.gpuTraceDocument))
let scope = (mode == "devscope") ? manager.makeCaptureScope(device: device) : manager.makeCaptureScope(commandQueue: queue)
scope.label = "Probe frame"

let desc = MTLCaptureDescriptor()
desc.captureObject = (mode == "scope" || mode == "devscope") ? scope : device
desc.destination = .gpuTraceDocument
desc.outputURL = url
do { try manager.startCapture(with: desc) } catch { print("startCapture failed:", error); exit(1) }
print("isCapturing:", manager.isCapturing)

for frame in 0..<3 {
    if mode == "scope" || mode == "devscope" { scope.begin() }
    allocator.reset()
    commandBuffer.beginCommandBuffer(allocator: allocator)
    commandBuffer.label = "Frame \(frame)"
    let rp = MTL4RenderPassDescriptor()
    rp.colorAttachments[0].texture = target
    rp.colorAttachments[0].loadAction = .clear
    rp.colorAttachments[0].storeAction = .store
    rp.colorAttachments[0].clearColor = MTLClearColor(red: 1, green: 0, blue: 0, alpha: 1)
    let enc = commandBuffer.makeRenderCommandEncoder(descriptor: rp)!
    enc.label = "Clear pass"
    enc.endEncoding()
    commandBuffer.endCommandBuffer()
    queue.commit([commandBuffer])
    queue.signalEvent(event, value: UInt64(frame + 1))
    _ = event.wait(untilSignaledValue: UInt64(frame + 1), timeoutMS: 5000)
    if mode == "scope" || mode == "devscope" { scope.end() }
}
if mode == "device" { manager.stopCapture() }
print("isCapturing after:", manager.isCapturing)
print("exists:", FileManager.default.fileExists(atPath: url.path))
