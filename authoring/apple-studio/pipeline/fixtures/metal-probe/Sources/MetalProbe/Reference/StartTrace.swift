import Foundation // probe: the reference block relies on the gate's imports
import Metal // probe

enum TraceError: Error { case captureLayerMissing }

/// Records every command buffer any queue of `device` commits between
/// `startTrace` and `stopTrace` into a .gputrace bundle at `url`.
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
