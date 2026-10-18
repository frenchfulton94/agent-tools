use objc2::rc::Retained;
use objc2::runtime::ProtocolObject;
use objc2_foundation::{NSString, NSURL};
use objc2_metal::{
    MTLCaptureDescriptor, MTLCaptureDestination, MTLCaptureManager, MTLCaptureScope, MTLDevice,
};

/// Call before the frame's begin; call `endScope()` on the result after the
/// frame-done wait. Needs MTL_CAPTURE_ENABLED=1.
pub fn start_trace(
    device: &ProtocolObject<dyn MTLDevice>,
    path: &str,
) -> Option<Retained<ProtocolObject<dyn MTLCaptureScope>>> {
    let manager = unsafe { MTLCaptureManager::sharedCaptureManager() };
    if !manager.supportsDestination(MTLCaptureDestination::GPUTraceDocument) {
        return None;
    }
    let scope = manager.newCaptureScopeWithDevice(device);
    let desc = MTLCaptureDescriptor::new();
    desc.set_capture_scope(&scope);
    desc.setDestination(MTLCaptureDestination::GPUTraceDocument);
    desc.setOutputURL(Some(&NSURL::fileURLWithPath(&NSString::from_str(path))));
    manager.startCaptureWithDescriptor_error(&desc).ok()?;
    scope.beginScope();
    Some(scope)
}
