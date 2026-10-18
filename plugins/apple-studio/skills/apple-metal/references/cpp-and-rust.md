> verified: 2026-10 against https://developer.apple.com/documentation/metal/understanding-the-metal-4-core-api.md, https://developer.apple.com/documentation/metal/mtl4commandqueue.md, https://developer.apple.com/documentation/metal/mtl4commandqueue/commit:count:.md, https://developer.apple.com/documentation/metal/mtl4commandbuffer.md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/begincommandbuffer(allocator:).md, https://developer.apple.com/documentation/metal/mtl4commandbuffer/endcommandbuffer().md, https://developer.apple.com/documentation/metal/mtl4commandallocator.md, https://developer.apple.com/documentation/metal/mtl4commandallocator/reset().md, https://developer.apple.com/documentation/metal/mtl4renderpassdescriptor.md, https://developer.apple.com/documentation/metal/mtlresidencyset.md, https://developer.apple.com/documentation/metal/mtlsharedevent/wait(untilsignaledvalue:timeoutms:).md, https://developer.apple.com/documentation/metal/mtlcreatesystemdefaultdevice().md, https://developer.apple.com/documentation/metal/mtlstoragemode/shared.md, https://developer.apple.com/documentation/metal/mtlgpufamily/metal4.md, https://developer.apple.com/documentation/metal/mtlcapturemanager.md, https://developer.apple.com/documentation/metal/mtlcapturemanager/makecapturescope(commandqueue:)-9wie3.md, https://developer.apple.com/documentation/metal/mtlcapturemanager/startcapture(with:).md, https://developer.apple.com/documentation/metal/mtlcapturedescriptor.md, https://developer.apple.com/documentation/metal/mtlcapturedescriptor/captureobject.md, https://developer.apple.com/documentation/metal/mtlcapturedescriptor/outputurl.md, https://developer.apple.com/documentation/metal/mtlcapturedestination.md, https://developer.apple.com/documentation/metal/mtlcapturescope/mtl4commandqueue.md, https://developer.apple.com/documentation/metal/building-a-shader-library-by-precompiling-source-files.md, https://developer.apple.com/documentation/metal/creating-a-3d-application-with-hydra-rendering.md, https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-programmatically.md, https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode.md, https://developer.apple.com/documentation/xcode/customizing-the-build-schemes-for-a-project.md, https://developer.apple.com/documentation/xcode/customizing-the-build-phases-of-a-target.md, https://developer.apple.com/documentation/xcode/configuring-a-new-target-in-your-project.md, https://developer.apple.com/documentation/xcode/running-custom-scripts-during-a-build.md, https://developer.apple.com/documentation/xcode/build-settings-reference.md, https://developer.apple.com/documentation/xcode/building-your-project-with-explicit-module-dependencies.md, https://developer.apple.com/documentation/xcode/understanding-build-product-layout-changes.md, https://developer.apple.com/documentation/xcode/validating-your-apps-metal-api-usage.md, https://developer.apple.com/documentation/xcode/validating-your-apps-metal-shader-usage.md, https://developer.apple.com/documentation/xcode/enabling-enhanced-security-for-your-app.md, https://developer.apple.com/documentation/metal/writing-reusable-gpu-functions-with-generic-pointers.md
> sources: msl-4.1, metal-feature-set-tables-2026-05
> typecheck: macos 26.0
> typecheck-cpp: metal-cpp 26.4
> typecheck-rust: objc2 = "=0.6.5", objc2-foundation = "=0.3.2", objc2-metal = "=0.3.2"

# Driving Metal 4 from C++ and Rust

Contents:
- Choosing a binding
- Names across the three bindings
- metal-cpp: setup and ownership
- The minimal metal-cpp host
- objc2-metal: types, unsafety, feature flags
- The minimal objc2-metal host
- Compiling shaders outside Xcode
- Hosting the build in Xcode
- Capturing outside Xcode
- Maintaining older code: Metal 3

Scope: the parts of a Metal 4 engine that change when the host language is C++
(metal-cpp) or Rust (objc2-metal) instead of Swift: setup, ownership, the
names, the unsafety, and how to get Xcode's GPU tools onto a binary that Xcode
did not build. The frame itself (allocators, argument tables, residency,
barriers, frames in flight) is the same object model in every language and is
owned by `command-model.md`. Capture analysis and `gpudebug` belong to
`gpu-debugging-and-profiling.md`.

Unless a line says otherwise, "runtime-checked" below means run on this
machine: an Apple M4 Pro, macOS 27.0.1, Xcode 27.1, Apple clang 21,
rustc 1.97.1.

## Choosing a binding

| Situation | Use | Why |
|---|---|---|
| Existing C++ engine, any size | metal-cpp | Header-only, one C++ class per Objective-C class, inlined message sends with no measured overhead, no wrapper allocations. No Objective-C++ shim. |
| Rust engine | objc2-metal 0.3.x | Generated from Apple's headers. It has the Metal 4 surface: 81 `MTL4*` items, including `MTL4CommandQueue` and `MTL4CommandAllocator`, plus `MTLResidencySet`. The older `metal` crate (0.33) has a README deprecation notice that points to `objc2` and `objc2-metal`. |
| Swift app shell over a C++ engine | Swift C++ interop, or a C API | `SWIFT_OBJC_INTEROP_MODE` lets Swift call C++ directly. Explicitly built modules, the Xcode 16 and later default, are not supported with C++ interop, so such a target builds without them. |
| Shaders | MSL in every case | The bindings only drive the API. Shader code is `.metal`, compiled offline or at runtime, as in Swift. |

metal-cpp is a separate download, not part of the SDK. Its version tracks the
SDK: 26.4 adds the macOS 26.4 and iOS 26.4 APIs, and 26 added Metal 4 and the
Apple10 family. Pin one version for the whole engine, as with any vendored
header library.

## Names across the three bindings

The object model is identical in every binding. Only the spelling changes, and
the spelling is the first thing a model gets wrong. The rules:

- Swift renames `new…` to `make…` and turns selectors into argument labels.
- metal-cpp keeps the Objective-C `new…` names, drops the `With…` parts, and
  overloads. `waitForEvent:value:` and `waitForDrawable:` both become `wait()`.
- objc2-metal keeps the full selector: inner colons become `_` and the
  trailing colon is dropped (`waitUntilSignaledValue:timeoutMS:` becomes
  `waitUntilSignaledValue_timeoutMS`). A trailing `error:` becomes a `Result`.
  Calls are marked `unsafe` where pointers or counts cross them.

| Swift (Metal 4) | metal-cpp 26.4 | objc2-metal 0.3.2 |
|---|---|---|
| `device.makeMTL4CommandQueue()` | `device->newMTL4CommandQueue()` | `device.newMTL4CommandQueue()` |
| `device.makeCommandAllocator()` | `device->newCommandAllocator()` | `device.newCommandAllocator()` |
| `device.makeCommandBuffer()` | `device->newCommandBuffer()` | `device.newCommandBuffer()` |
| `commandBuffer.beginCommandBuffer(allocator:)` | `beginCommandBuffer(allocator)` | `beginCommandBufferWithAllocator(&allocator)` |
| `makeRenderCommandEncoder(descriptor:)` | `renderCommandEncoder(desc)` | `renderCommandEncoderWithDescriptor(&desc)` |
| `queue.commit([cb], options: nil)` | `queue->commit(array, count)` | `unsafe { queue.commit_count(ptr, count) }` |
| `queue.signalEvent(_:value:)` | `queue->signalEvent(e, v)` | `queue.signalEvent_value(e, v)` |
| `queue.waitForEvent(_:value:)` | `queue->wait(e, v)` | `queue.waitForEvent_value(e, v)` |
| `queue.waitForDrawable(_:)` | `queue->wait(drawable)` | `queue.waitForDrawable(drawable)` |
| `event.wait(untilSignaledValue:timeoutMS:)` | `waitUntilSignaledValue(v, ms)` | `waitUntilSignaledValue_timeoutMS(v, ms)` |
| `pass.colorAttachments[0]` | `pass->colorAttachments()->object(0)` | `unsafe { pass.colorAttachments().objectAtIndexedSubscript(0) }` |
| `MTLClearColor(red:green:blue:alpha:)` | `MTL::ClearColor::Make(r, g, b, a)` | struct literal `MTLClearColor { red, green, blue, alpha }` |
| `MTLCaptureManager.shared()` | `MTL::CaptureManager::sharedCaptureManager()` | `unsafe { MTLCaptureManager::sharedCaptureManager() }` |
| `makeCaptureScope(device:)` | `newCaptureScope(device)` | `newCaptureScopeWithDevice(&device)` |
| `scope.begin()` / `end()` | `beginScope()` / `endScope()` | `beginScope()` / `endScope()` |

## metal-cpp: setup and ownership

**Setup.** Include `Metal/Metal.hpp` everywhere. In exactly one `.cpp`, define
`NS_PRIVATE_IMPLEMENTATION` and `MTL_PRIVATE_IMPLEMENTATION` before the
include. That file holds the selector and class symbols. Add
`CA_PRIVATE_IMPLEMENTATION` with `QuartzCore/QuartzCore.hpp` if you use the
`CA::MetalLayer` wrapper. The MetalFX headers use `MTLFX_PRIVATE_IMPLEMENTATION`
the same way; the README does not list it, but `MetalFX/MTLFXPrivate.hpp` checks
it. To hide metal-cpp's symbols from your engine's exported surface, define
`METALCPP_SYMBOL_VISIBILITY_HIDDEN`. To get one header, run
`SingleHeader/MakeSingleHeader.py`.

**Language standard.** metal-cpp needs C++17. The default standard is lower in
both places that pick one silently:

- Xcode's "Compiler Default" for `CLANG_CXX_LANGUAGE_STANDARD` is documented as
  GNU++98.
- Plain `clang++` with no `-std` reports `__cplusplus == 201402L` (C++14) here.
  Including `Metal/Metal.hpp` then fails with
  `no template named 'is_convertible_v' in namespace 'std'` from
  `NSSharedPtr.hpp`. Runtime-checked.

The build-settings page and the shipped compiler disagree on the default. The
compiler wins, and both values are too low. Set `c++20` explicitly in Xcode and
on every command line.

**Ownership.** These are Cocoa's manual rules, with no ARC:

- You own what comes from a method whose name starts with `alloc`, `new`,
  `copy`, `mutableCopy`, or `Create`. You `release()` it.
- Anything else is autoreleased and belongs to the innermost pool.
- `retain()` extends a borrowed object past its pool.

Applied to the Metal 4 frame objects:

| Call | You own it? |
|---|---|
| `MTL::CreateSystemDefaultDevice()`, `newMTL4CommandQueue()`, `newCommandAllocator()`, `newCommandBuffer()`, `newSharedEvent()`, `newTexture(…)`, `newResidencySet(…)`, `newCaptureScope(…)` | Yes. Release each one. |
| `MTL4::RenderPassDescriptor::alloc()->init()`, `MTL::ResidencySetDescriptor::alloc()->init()`, `MTL::CaptureDescriptor::alloc()->init()` | Yes. |
| `renderCommandEncoder(…)`, `computeCommandEncoder()`, `MTL::TextureDescriptor::texture2DDescriptor(…)`, `NS::String::string(…)`, `NS::URL::fileURLWithPath(…)` | No. Autoreleased. |
| `colorAttachments()->object(0)`, `MTL::CaptureManager::sharedCaptureManager()` | No. Borrowed from their parent. |

Three consequences that bite engine code:

- **Pools are mandatory.** An autoreleased object with no enclosing pool
  leaks. Create an `NS::AutoreleasePool` in `main` and in the entry function of
  every thread you start. Use a per-frame pool on the render thread so that
  encoders and descriptors drain every frame rather than at exit. Set
  `OBJC_DEBUG_MISSING_POOLS=YES` to get a warning for each leak.
  `leaks --autoreleasePools <pid or memgraph>` lists the pools and their
  contents.
- **Messaging `nullptr` is a silent no-op.** That includes `retain()` and
  `release()`. A failed `newMTL4CommandQueue()` does not crash at the next
  call; the frame simply does nothing. Check every `new…` result.
- **`MTL4CommandBuffer` does not retain the resources it references.** This is
  the Metal 4 default, the same as an unretained-references `MTLCommandBuffer`.
  In Swift, ARC keeps your properties alive. In C++, a `release()` on a texture
  that an in-flight frame still samples frees it under the GPU. API Validation
  will not catch this, because its unretained-resource check covers only
  `MTLCommandBuffer`. Defer each release until the frame's shared-event value
  has passed, as in the frames-in-flight ring in `command-model.md`.

`NS::SharedPtr<T>` is the optional RAII path. Its destructor always calls
`release()`. Wrap owned (`new…`, `alloc`) results with `NS::TransferPtr`, which
does not add a retain. Wrap borrowed results with `NS::RetainPtr`, which does.
Using `RetainPtr` on a `new…` result leaks one reference per object.

**Feature checks.** Every `bool MTL::Device::supports…()` returns `false` when
the running OS lacks its selector. String constants such as error domains are
weak-linked and are `nullptr` when missing. Use `MTLSTR("literal")` for
`NS::String` constants; the older `MakeConstantString` is deprecated.

**Enhanced Security.** Adding the Enhanced Security capability sets
`ENABLE_CPLUSPLUS_BOUNDS_SAFE_BUFFERS` to YES on the target. Beyond libc++
hardening, that setting makes indexing a raw pointer or doing arithmetic on one
a compile error, and the two-argument `std::span` constructor too. Walking
`buffer->contents()` as a `float*` is exactly that, so wrapping it in a span is
no escape. If you adopt the capability, set the setting to No on the engine
target.

## The minimal metal-cpp host

One offscreen frame: a Metal 4 render pass that clears a 64×64 shared texture,
then a CPU readback of one pixel. Storage mode `.shared` is the default for
textures on Apple silicon, so the readback needs no blit. The target texture
goes into a residency set even though no shader reads it. In Metal 4,
residency sets are the only residency mechanism, and Shader Validation counts
any resource that a Metal 4 command touches outside every attached set as not
resident. Runtime-checked caution: with the set removed, this clear-only frame
still produced the right pixel, and API and Shader Validation stayed silent.
A frame that works is not evidence that residency is right. The frame wait is
a queue-signalled shared event, because `MTL4CommandBuffer` has no completion
handler and no `waitUntilCompleted()`.

```cpp
// main.cpp: the one translation unit that defines the private implementation.
#define NS_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#include <Foundation/Foundation.hpp>
#include <Metal/Metal.hpp>

#include <cstdint>
#include <cstdio>

int main()
{
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();

    MTL::Device* device = MTL::CreateSystemDefaultDevice();
    if (!device || !device->supportsFamily(MTL::GPUFamilyMetal4)) {
        std::fprintf(stderr, "no Metal 4 GPU\n");
        pool->release();
        return 1;
    }

    // new... calls return objects you own: release each one.
    MTL4::CommandQueue*     queue     = device->newMTL4CommandQueue();
    MTL4::CommandAllocator* allocator = device->newCommandAllocator();
    MTL4::CommandBuffer*    commands  = device->newCommandBuffer();
    MTL::SharedEvent*       frameDone = device->newSharedEvent();

    // A class factory, not new...: autoreleased, so the pool owns it.
    MTL::TextureDescriptor* textureDesc = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatRGBA8Unorm, 64, 64, false);
    textureDesc->setUsage(MTL::TextureUsageRenderTarget);
    textureDesc->setStorageMode(MTL::StorageModeShared);
    MTL::Texture* target = device->newTexture(textureDesc);

    MTL::ResidencySetDescriptor* residencyDesc = MTL::ResidencySetDescriptor::alloc()->init();
    NS::Error* error = nullptr;
    MTL::ResidencySet* residency = device->newResidencySet(residencyDesc, &error);
    residencyDesc->release();
    if (!residency) {
        std::fprintf(stderr, "%s\n", error->localizedDescription()->utf8String());
        return 1;
    }
    residency->addAllocation(target);
    residency->commit();
    queue->addResidencySet(residency);

    // One frame: reset, begin, one render pass, end, commit, signal, wait.
    allocator->reset();
    commands->beginCommandBuffer(allocator);

    MTL4::RenderPassDescriptor* pass = MTL4::RenderPassDescriptor::alloc()->init();
    MTL::RenderPassColorAttachmentDescriptor* color = pass->colorAttachments()->object(0);
    color->setTexture(target);
    color->setLoadAction(MTL::LoadActionClear);
    color->setStoreAction(MTL::StoreActionStore);
    color->setClearColor(MTL::ClearColor::Make(1.0, 0.0, 0.0, 1.0));

    MTL4::RenderCommandEncoder* encoder = commands->renderCommandEncoder(pass);
    encoder->endEncoding();
    pass->release();
    commands->endCommandBuffer();

    const MTL4::CommandBuffer* submit[] = { commands };
    queue->commit(submit, 1);
    queue->signalEvent(frameDone, 1);
    if (!frameDone->waitUntilSignaledValue(1, 1000)) {
        std::fprintf(stderr, "frame timed out\n");
        return 1;
    }

    std::uint8_t pixel[4] = {};
    target->getBytes(pixel, 4, MTL::Region::Make2D(0, 0, 1, 1), 0);
    std::printf("pixel %u %u %u %u\n", pixel[0], pixel[1], pixel[2], pixel[3]);

    residency->release();
    target->release();
    frameDone->release();
    commands->release();
    allocator->release();
    queue->release();
    device->release();
    pool->release();
    return 0;
}
```

```bash
clang++ -std=c++20 -I /path/to/metal-cpp main.cpp \
  -framework Foundation -framework Metal -framework CoreGraphics -o host
./host                 # prints: pixel 255 0 0 255
MTL_DEBUG_LAYER=1 ./host
```

Runtime-checked: both runs print `pixel 255 0 0 255`, and the second also logs
"Metal API Validation Enabled". The `MTLCreateSystemDefaultDevice()` page says
a macOS command-line tool must link CoreGraphics to get a default device. A
build here without `-framework CoreGraphics` still got the device. Link it
anyway: it costs nothing, and the requirement is documented.

## objc2-metal: types, unsafety, feature flags

**Types.** A Metal protocol object is `Retained<ProtocolObject<dyn MTLDevice>>`.
`Retained` is the owning pointer: dropping it calls `release`. Metal methods
are trait methods, so import the trait that declares each one. For example,
`endEncoding` lives on `MTL4CommandEncoder`, not on `MTL4RenderCommandEncoder`.
Upcast between protocols with `ProtocolObject::from_ref`:

- a texture to `&ProtocolObject<dyn MTLAllocation>` for `addAllocation`;
- a shared event to `&ProtocolObject<dyn MTLEvent>` for `signalEvent_value`.

Classes such as `MTL4RenderPassDescriptor` are ordinary types with `new()`.

**What is `unsafe`.** The crate treats GPU memory safety the same as CPU memory
safety. Creating objects, `begin`/`end`, signalling, and residency commits are
safe calls. These are `unsafe`, each for its own stated reason:

- **Raw pointer plus count:** `commit_count`, `addResidencySets_count`,
  `useResidencySets_count`. You pass a `NonNull` to an array of `NonNull`
  command buffers, and the count is not bounds-checked.
- **Unchecked index:** `objectAtIndexedSubscript` on attachment arrays.
- **CPU access to resource memory:** `getBytes_bytesPerRow_fromRegion_mipmapLevel`
  and the `replaceRegion_…` texture calls. `MTLBuffer::contents()` is itself
  safe, but it returns a `NonNull<c_void>`, so every read or write through it
  is your own `unsafe` block. Synchronizing with the GPU is your job.
- **Class factories and `id` setters:**
  `texture2DDescriptorWithPixelFormat_width_height_mipmapped`,
  `sharedCaptureManager`, and `MTLCaptureDescriptor::setCaptureObject`, which
  takes `AnyObject`. Use the safe helper `set_capture_scope` (or
  `set_capture_device`) instead. The crate has no helper for an
  `MTL4CommandQueue`; see "Capturing outside Xcode" for why that is the right
  gap.
- **Calling a shader is unsafe in principle.** The crate's docs say loading a
  library and getting an `MTLFunction` are safe, but running one is like
  calling an `unsafe fn` pointer.

**C inline helpers are not bound.** `MTLClearColorMake`, `MTLRegionMake2D`,
`MTLSizeMake`, and `MTLOriginMake` are `TODO` comments in the generated source.
Write the struct literals instead.

**Threads.** `MTLDevice`, `MTL4CommandQueue`, and `MTLEvent` are declared
`Send + Sync`. `MTL4CommandBuffer`, `MTL4CommandAllocator`, and
`MTLResidencySet` are not, and Apple documents residency-set methods as not
thread-safe. The compiler therefore stops you from encoding a command buffer
on a worker and moving it to the submitting thread. Each worker must create
and own its allocator and command buffer, from the shared `Sync` device. A
multi-buffer `commit_count` from one thread then needs an `unsafe` hand-off
that you justify yourself. (This last point is an inference from the trait
bounds, not something the crate documents.)

**Lifetimes.** The crate states that resources used by an `MTL4CommandBuffer`
must be kept alive for as long as the GPU uses them. A `Retained` texture that
goes out of scope is released immediately. Keep each frame's resources in a
per-frame ring that you clear only after that frame's event value has
signalled.

**Autorelease pools.** The rule is the same as in C++, because it is the same
runtime. A returned object becomes a `Retained` that you own. Objects that the
framework autoreleases internally still need a pool. Wrap `main` and each
thread's loop body in `objc2::rc::autoreleasepool`.

**Feature flags.** objc2-metal has one cargo feature per Metal header, plus
`bitflags`, `block2`, `dispatch2`, and `objc2-core-foundation`. The default
enables all of them. For an application that is fine. A library should set
`default-features = false` and list only the headers it uses. Runtime-checked,
debug builds from a cold target directory: the host below took 83 s with all
three crates at their defaults, and 15 s with `objc2-foundation` dropped and
objc2-metal trimmed to this list:

```toml
objc2-metal = { version = "=0.3.2", default-features = false, features = [
    "std",
    "MTL4CommandAllocator",
    "MTL4CommandBuffer",
    "MTL4CommandEncoder",
    "MTL4CommandQueue",
    "MTL4RenderCommandEncoder",
    "MTL4RenderPass",
    "MTLAllocation",
    "MTLDevice",
    "MTLEvent",
    "MTLPixelFormat",
    "MTLRenderPass",
    "MTLResidencySet",
    "MTLResource",
    "MTLTexture",
    "MTLTypes",
] }
```

The bindings are generated from a fixed SDK. An API newer than that SDK is
missing from the crate, with no error until you look for it. Check
`src/generated/<Header>.rs` in the pinned version before you plan around a new
symbol.

## The minimal objc2-metal host

The same frame as the C++ host. `Cargo.toml`:

```toml
[package]
name = "metal4-host"
version = "0.1.0"
edition = "2024"

[dependencies]
objc2 = "=0.6.5"
objc2-foundation = "=0.3.2"
objc2-metal = "=0.3.2"
```

`src/main.rs`. `objc2-foundation` is listed for the capture helper later in
this file; the host itself does not need it.

```rust
use core::ptr::NonNull;

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
```

Runtime-checked: the built binary prints `pixel [255, 0, 0, 255]`. It prints the
same with `MTL_DEBUG_LAYER=1`, and with `OBJC_DEBUG_MISSING_POOLS=YES` it
reports no missing pools.

One trap in both hosts: `beginCommandBuffer` clears any residency sets that
were attached to that command buffer with `useResidencySet`. Re-attach them
after every begin, or attach long-lived sets to the queue with
`addResidencySet`, as both hosts do.

## Compiling shaders outside Xcode

An external build compiles `.metal` itself. In Xcode 27 the Metal compiler is
a separate component: run `xcodebuild -downloadComponent MetalToolchain` once
per machine, or `xcrun metal` is missing. Pin the language version with
`-std=`, so that the toolchain cannot change it under you, and use one version
across the whole build, because MSL 4.0 and 4.1 are not ABI-compatible.
Runtime-checked:

```bash
xcrun -sdk macosx metal -std=metal4.0 -c shaders.metal -o shaders.air
xcrun -sdk macosx metal -o shaders.metallib shaders.air
```

Apple's pages name the intermediate file `.ir` in one place and `.air` in
another. The extension is just whatever `-o` says. `metal-ar -q` bundles
intermediates into an archive. Load the `.metallib` at runtime from the
device, as in Swift. A cargo `build.rs` or a CMake custom command can run the
two lines above.

## Hosting the build in Xcode

Instruments, the Metal debugger, and the scheme's Metal diagnostics all attach
to a Run or Profile action. Pick a route by what the binary is:

| Binary | Route |
|---|---|
| Already built, one-off capture | **Debug > Debug Executable**, choose the binary, set GPU Frame Capture on the Options tab, then **Product > Run**. No project is needed. Apple's page describes choosing an app bundle; a bare executable is not runtime-checked here. |
| cargo, make, or CMake builds the whole executable | An **External Build System** target plus a scheme whose Executable is the built binary. |
| The engine is a static library inside a Swift/ObjC app | A Run Script phase, or a dependent target, in the app's project. Link the library explicitly. |
| CMake project that you want as a real Xcode project | Generate one with CMake (not runtime-checked; see below). |

**External Build System target.** This is the External Build System
template, under Other. It makes a "legacy" target: the installed Xcode 27.1
template runs a build tool (default `/usr/bin/make`) with the argument string
`$(ACTION)`, so Xcode's build and clean become `make build` and `make clean`.
The argument string expands build settings, as that default shows, so
`$(CONFIGURATION)` passes Debug or Release. Apple's build-phases page
calls these "External Build Tool" targets. Such a target cannot have a Compile
Sources phase or a Link Binary With Libraries phase, so it builds the artifact
and nothing else.

For cargo, set Build Tool to `/bin/sh` and Arguments to
`xcode-cargo.sh $(ACTION) $(CONFIGURATION)`, with the working directory at the
crate root:

```sh
#!/bin/sh
# Build Tool: /bin/sh   Arguments: xcode-cargo.sh $(ACTION) $(CONFIGURATION)
set -eu
CARGO="${CARGO:-$(command -v cargo || true)}"
if [ -z "$CARGO" ]; then
  echo "error: cargo is not on this build's PATH; set CARGO to an absolute path"
  exit 1
fi
action="${1:-build}"
config="${2:-Debug}"
case "$action" in
  "" | build)
    if [ "$config" = "Release" ]; then exec "$CARGO" build --release; fi
    exec "$CARGO" build ;;
  clean)
    exec "$CARGO" clean ;;
  *)
    echo "error: xcode-cargo.sh does not handle the action '$action'"
    exit 1 ;;
esac
```

Runtime-checked from a shell, not yet inside Xcode: the script builds, cleans,
and exits 1 with a message on an unknown action or a PATH without cargo. Do not
hardcode `~/.cargo/bin/cargo`: on this machine cargo is a Homebrew rustup
install at `/opt/homebrew/opt/rustup/bin/cargo`, and the guessed path would
fail.

Then set up the scheme (Edit Scheme):

- **Run > Info > Executable:** the built binary (`target/debug/<name>`). Xcode
  launches it after a successful build, and the debugger attaches.
- **Run > Options > GPU Frame Capture:** choose **Metal**, not Automatically.
  Automatically decides from whether the target links Metal, and Xcode does not
  consider this target to link anything. That reasoning is an inference;
  runtime probe R5 checks it.
- **Run > Diagnostics:** API Validation and Shader Validation are Run-only
  options, so they apply to whatever the Run action launches.
- **Profile > Executable:** the same binary, so that **Product > Profile** opens
  Instruments on it. Profile a `--release` build, for the reasons in
  `apple-performance`'s `profiling-workflow.md`.

**Run Script route, for a Rust or C++ static library inside an app.**

- **Declare the script's inputs and outputs.** A script with none declared
  runs on every build.
- **User Script Sandboxing** (`ENABLE_USER_SCRIPT_SANDBOXING`) blocks undeclared
  file access. cargo and CMake read the whole source tree, so either declare
  inputs (an `.xcfilelist` works) or turn the setting off for that target only.
- **Link the `.a` explicitly** in Link Binary With Libraries. Xcode links Apple
  frameworks automatically for Swift, and for C, C++, and ObjC when
  `CLANG_MODULES_AUTOLINK` is on, but never your own libraries.
- **Add the target dependency by hand.** Implicit dependency detection cannot
  see files that a script in another target produces.
- **Report errors in Xcode's format.** Lines of the form
  `/abs/path:line: error: message` reach the Issue navigator, and a nonzero
  exit fails the build.
- **Check the debug dylib.** Debug builds of a Swift app target move the app's
  code into `<App>.debug.dylib`, behind a stub executable
  (`ENABLE_DEBUG_DYLIB`). A crate that registers items through linker sections
  (`inventory`, `linkme`) may stop finding them. That is an inference; set
  `ENABLE_DEBUG_DYLIB=NO` on that target if it happens.
- **A Rust `cdylib`** needs a Copy Files phase (destination Frameworks, which
  also signs it) and a matching `LD_RUNPATH_SEARCH_PATHS` entry for `@rpath`.

**CMake. Not runtime-checked: CMake is not installed here.** Apple's Hydra
sample builds its dependency with `build_usd.py --generator Xcode` and then
generates its own project with `cmake -S <source> -B <build>`. Next it opens
that project and selects the app's scheme, after which every Xcode tool works
as on a native project. The page's `cmake` line has no `-G` option. If the
output is not an `.xcodeproj`, pass `-G Xcode`. The other route is an External
Build System target whose build tool is `cmake --build`.

## Capturing outside Xcode

Programmatic capture to a `.gputrace` works on any binary, so a cargo or
CMake build never has to touch Xcode. That trace is what `gpudebug -t` opens;
see `gpu-debugging-and-profiling.md`.

- **Enable capture.** A bare executable has no Info.plist for
  `MetalCaptureEnabled`, so launch it with `MTL_CAPTURE_ENABLED=1` (macOS 14 and
  later). Without the variable, `supportsDestination(.gpuTraceDocument)`
  returned `false` here. Check that call and log the result, or a missing
  trace looks like a capture bug. Keep the variable out of shipping launches,
  because capture costs CPU time.
- **Capture through a device scope.** The descriptor's `captureObject` is
  documented to take a device, an `MTLCommandQueue`, or an `MTLCaptureScope`.
  An `MTL4CommandQueue` is not on that list. The SDK does offer
  `newCaptureScopeWithMTL4CommandQueue:`
  (`makeCaptureScope(commandQueue: any MTL4CommandQueue)` in Swift). With that
  scope as the capture object, though, `startCapture` here throws
  `-[MTLCaptureScope traceStream]: unrecognized selector`, from both Swift and
  C++. A scope made from the device works. Passing the `MTL4CommandQueue`
  itself as `captureObject` also produced a trace here, but it is
  undocumented. Use the device scope.
- **What gets recorded.** Apple's pages say a capture records command buffers
  created after it starts. That wording was written for `MTLCommandBuffer`. A
  reused `MTL4CommandBuffer` that was created at startup was still recorded
  when its begin-to-commit ran inside the scope (`gpudebug` listed 1 command
  buffer, 1 encoder). With a device scope, `endScope()` also ended the capture:
  `isCapturing` read false afterwards.

```cpp
// Call before the frame's beginCommandBuffer; after the frame-done wait,
// call endScope() and release() on the scope. Needs MTL_CAPTURE_ENABLED=1.
MTL::CaptureScope* startTrace(MTL::Device* device, const char* path)
{
    MTL::CaptureManager* manager = MTL::CaptureManager::sharedCaptureManager();
    if (!manager->supportsDestination(MTL::CaptureDestinationGPUTraceDocument))
        return nullptr;

    MTL::CaptureScope* scope = manager->newCaptureScope(device);
    MTL::CaptureDescriptor* desc = MTL::CaptureDescriptor::alloc()->init();
    desc->setCaptureObject(scope);
    desc->setDestination(MTL::CaptureDestinationGPUTraceDocument);
    desc->setOutputURL(NS::URL::fileURLWithPath(NS::String::string(path, NS::UTF8StringEncoding)));

    NS::Error* error = nullptr;
    bool started = manager->startCapture(desc, &error);
    desc->release();
    if (!started) {
        scope->release();
        return nullptr;
    }
    scope->beginScope();
    return scope;
}
```

```rust
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
```

Runtime-checked: both helpers, called around the hosts' frames, wrote a trace with
`MTL_CAPTURE_ENABLED=1`, and wrote nothing (with `supportsDestination` false)
without it.

```bash
MTL_CAPTURE_ENABLED=1 ./host
gpudebug --oneshot -t frame.gputrace -c "list"
```

Validation needs no Xcode either. `MTL_DEBUG_LAYER=1` and
`MTL_SHADER_VALIDATION=1` work on a plain binary; the hosts log "Metal API
Validation Enabled" and "Metal GPU Validation Enabled". The full variable list
is in `gpu-debugging-and-profiling.md`. Remember the gap from the ownership
section: API Validation does not flag a resource that is freed while an
`MTL4CommandBuffer` still uses it, and in C++ and Rust that is your bug to
prevent.

## Maintaining older code: Metal 3

Snippets in this section compile at the file's macOS 26.0 floor; they are not compile-checked against earlier OS releases.

**When it applies.**

- GPUs below Apple7. The Feature Set Tables start the Metal 4 model at Apple7
  (A14 and M1). A13 is Apple6, which has the Metal 3 model only.
- Any OS before 26.0, where no `MTL4*` type exists.

**Gating at runtime.** Call `supportsFamily(MTL::GPUFamilyMetal4)` in C++, or
`supportsFamily(MTLGPUFamily::Metal4)` in Rust, once at startup, and choose the
renderer from the result. Neither binding checks availability at compile time.
Both resolve classes and selectors through the Objective-C runtime, so no
`MTL4` code runs until you call it. On an older OS, metal-cpp's `supports…()`
calls return `false` when the selector is missing. A direct call to an `MTL4`
method on such an OS would fail at runtime, from the missing selector or
class. These older-OS behaviours are an inference; they are not
runtime-checked here.

**How the concepts map in the bindings.**

| Metal 3 (metal-cpp / objc2-metal) | Metal 4 |
|---|---|
| `queue->commandBuffer()` / `queue.commandBuffer()`, new every frame, autoreleased, and it retains its resources | `device->newCommandBuffer()`, created once, owned, reused, retains nothing |
| `commandBuffer->commit()` | `queue->commit(array, count)` / `unsafe commit_count` |
| `addCompletedHandler(…)` (a `std::function` overload in metal-cpp; an `unsafe` block in Rust), `waitUntilCompleted()` | `queue->signalEvent(e, n)` plus `waitUntilSignaledValue(n, ms)` |
| Encoder `useResource` / `useHeap` | Residency sets on the queue or the command buffer |
| `set…Buffer` / `set…Texture` on the encoder | `MTL4::ArgumentTable` |
| `MTL::BlitCommandEncoder` | Copy commands on `MTL4::ComputeCommandEncoder` |
| Capture scope from `MTL::CommandQueue` | Capture scope from the device (see above) |

The Metal 3 command buffer is autoreleased, so in C++ the per-frame pool is
what frees it. Forget the pool and every frame leaks one command buffer and
everything it retains.

```cpp
void encodeFrameMetal3(MTL::CommandQueue* queue, MTL::RenderPassDescriptor* pass)
{
    NS::AutoreleasePool* framePool = NS::AutoreleasePool::alloc()->init();
    MTL::CommandBuffer* commands = queue->commandBuffer();  // autoreleased
    MTL::RenderCommandEncoder* encoder = commands->renderCommandEncoder(pass);
    encoder->endEncoding();
    commands->commit();
    framePool->release();
}
```

```rust
use objc2::rc::autoreleasepool;
use objc2::runtime::ProtocolObject;
use objc2_metal::{
    MTLCommandBuffer, MTLCommandEncoder, MTLCommandQueue, MTLRenderPassDescriptor,
};

pub fn encode_frame_metal3(queue: &ProtocolObject<dyn MTLCommandQueue>, pass: &MTLRenderPassDescriptor) {
    autoreleasepool(|_| {
        let commands = queue.commandBuffer().expect("command buffer");
        let encoder = commands.renderCommandEncoderWithDescriptor(pass).expect("encoder");
        encoder.endEncoding();
        commands.commit();
    });
}
```

Apple's C++ deferred-lighting sample is written against this Metal 3 encoder
API through metal-cpp. Its string helper `AAPLSTR` is the sample's own macro;
in your code, use `MTLSTR`.
