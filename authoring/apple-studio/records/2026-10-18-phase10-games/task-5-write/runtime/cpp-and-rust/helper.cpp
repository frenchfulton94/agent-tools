// main.cpp: the one translation unit that defines the private implementation.
#define NS_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#include <Foundation/Foundation.hpp>
#include <Metal/Metal.hpp>

#include <cstdint>
#include <cstdio>

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
    MTL::CaptureScope* scope = startTrace(device, "/private/tmp/claude-501/-Users-michaelfrenchfultonjr-Projects-agent-tools/a781b2ce-4de5-48ed-828f-2ed56e8461f6/scratchpad/cpphost/helper.gputrace");
    std::fprintf(stderr, "capturing %d\n", scope != nullptr);
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

    if (scope) { scope->endScope(); scope->release(); }
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
