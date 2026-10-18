import Metal // probe: the reference block relies on the gate's imports

func encodeLabelledFrame(queue: any MTL4CommandQueue,
                         commandBuffer: any MTL4CommandBuffer,
                         allocator: any MTL4CommandAllocator,
                         pass: MTL4RenderPassDescriptor,
                         drawOpaque: (any MTL4RenderCommandEncoder) -> Void, // probe: fills the placeholder
                         frameIndex: Int) {
    commandBuffer.beginCommandBuffer(allocator: allocator)
    commandBuffer.pushDebugGroup("Frame \(frameIndex)")
    // No early return between begin and end: pop the group and end the buffer on every path.
    if let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: pass) {
        encoder.label = "Forward pass"
        encoder.pushDebugGroup("Opaque")
        // Opaque draws go here.
        drawOpaque(encoder) // probe
        encoder.popDebugGroup()
        encoder.insertDebugSignpost("Transparent begins")
        encoder.endEncoding()
    }
    commandBuffer.popDebugGroup()
    commandBuffer.endCommandBuffer()
    queue.commit([commandBuffer])
}
