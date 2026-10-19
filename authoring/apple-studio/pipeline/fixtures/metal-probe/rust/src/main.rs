use core::ptr::NonNull;
mod capture; // probe: capture.rs is the reference's start_trace
use objc2_metal::MTLCaptureScope; // probe: endScope

use objc2::rc::autoreleasepool;
use objc2::runtime::ProtocolObject;
use objc2_metal::{
    MTL4CommandAllocator, MTL4CommandBuffer, MTL4CommandEncoder, MTL4CommandQueue,
    MTL4RenderPassDescriptor, MTLClearColor, MTLCreateSystemDefaultDevice, MTLDevice,
    MTLGPUFamily, MTLLoadAction, MTLOrigin, MTLPixelFormat, MTLRegion, MTLResidencySet,
    MTLResidencySetDescriptor, MTLSharedEvent, MTLSize, MTLStorageMode, MTLStoreAction,
    MTLTexture, MTLTextureDescriptor, MTLTextureUsage,
};

// Apple and objc2-metal both say MTLCreateSystemDefaultDevice needs CoreGraphics linked.
#[link(name = "CoreGraphics", kind = "framework")]
unsafe extern "C" {}

fn main() {
    autoreleasepool(|_| {
        let device = MTLCreateSystemDefaultDevice().expect("no Metal device");
        assert!(device.supportsFamily(MTLGPUFamily::Metal4), "no Metal 4 GPU");

        let queue = device.newMTL4CommandQueue().unwrap();
        let allocator = device.newCommandAllocator().unwrap();
        let commands = device.newCommandBuffer().unwrap();
        let frame_done = device.newSharedEvent().unwrap();

        let texture_desc = unsafe {
            MTLTextureDescriptor::texture2DDescriptorWithPixelFormat_width_height_mipmapped(
                MTLPixelFormat::RGBA8Unorm,
                64,
                64,
                false,
            )
        };
        texture_desc.setUsage(MTLTextureUsage::RenderTarget);
        texture_desc.setStorageMode(MTLStorageMode::Shared);
        let target = device.newTextureWithDescriptor(&texture_desc).unwrap();

        let residency = device
            .newResidencySetWithDescriptor_error(&MTLResidencySetDescriptor::new())
            .expect("residency set");
        residency.addAllocation(ProtocolObject::from_ref(&*target));
        residency.commit();
        queue.addResidencySet(&residency);

        let capture_path = std::env::args().skip_while(|a| a != "--capture").nth(1); // probe
        let scope = capture_path.as_deref().and_then(|p| capture::start_trace(&device, p)); // probe: before begin
        if capture_path.is_some() { println!("capture {}", if scope.is_some() { "started" } else { "unavailable" }); } // probe
        // One frame: reset, begin, one render pass, end, commit, signal, wait.
        allocator.reset();
        commands.beginCommandBufferWithAllocator(&allocator);

        let pass = MTL4RenderPassDescriptor::new();
        let color = unsafe { pass.colorAttachments().objectAtIndexedSubscript(0) };
        color.setTexture(Some(&*target));
        color.setLoadAction(MTLLoadAction::Clear);
        color.setStoreAction(MTLStoreAction::Store);
        color.setClearColor(MTLClearColor { red: 1.0, green: 0.0, blue: 0.0, alpha: 1.0 });

        let encoder = commands.renderCommandEncoderWithDescriptor(&pass).unwrap();
        encoder.endEncoding();
        commands.endCommandBuffer();

        let mut submit = [NonNull::from(&*commands)];
        unsafe { queue.commit_count(NonNull::new(submit.as_mut_ptr()).unwrap(), 1) };
        queue.signalEvent_value(ProtocolObject::from_ref(&*frame_done), 1);
        assert!(frame_done.waitUntilSignaledValue_timeoutMS(1, 1000), "frame timed out");
        if let Some(scope) = &scope { scope.endScope(); } // probe: after the frame-done wait

        let mut pixel = [0u8; 4];
        let region = MTLRegion {
            origin: MTLOrigin { x: 0, y: 0, z: 0 },
            size: MTLSize { width: 1, height: 1, depth: 1 },
        };
        unsafe {
            target.getBytes_bytesPerRow_fromRegion_mipmapLevel(
                NonNull::new(pixel.as_mut_ptr().cast()).unwrap(),
                4,
                region,
                0,
            )
        };
        println!("pixel {pixel:?}");
    });
}
