import Foundation // probe: the reference block relies on the gate's imports
import Metal // probe

@MainActor
final class FrameCapture {
    let scope: any MTLCaptureScope

    init(device: any MTLDevice) {
        scope = MTLCaptureManager.shared().makeCaptureScope(device: device)
        scope.label = "Engine frame"
        MTLCaptureManager.shared().defaultCaptureScope = scope
    }

    /// Call `scope.begin()` before the frame's first commit and `scope.end()`
    /// after its last one. A capture started here stops at the next `end()`.
    func captureNextFrame(to url: URL) throws {
        let descriptor = MTLCaptureDescriptor()
        descriptor.captureObject = scope
        descriptor.destination = .gpuTraceDocument
        descriptor.outputURL = url
        try MTLCaptureManager.shared().startCapture(with: descriptor)
    }
}
