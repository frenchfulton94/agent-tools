#include <Metal/Metal.hpp> // probe: the reference block relies on the gate's include

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
