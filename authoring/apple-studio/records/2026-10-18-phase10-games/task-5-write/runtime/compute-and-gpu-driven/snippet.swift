import Metal

/// One compute pass: upload parameters with a copy, then run a kernel that reads them.
/// The barrier is required: copies and dispatches in one Metal 4 pass overlap.
/// The kernel tiles a fixed threadgroup size, so the pipeline must pin that size on its
/// descriptor (see `makeFilterPipeline` below). A size pinned only by the MSL attribute reads
/// back as zero, and a computed fallback would then dispatch the wrong shape without any error.
func encodeUploadThenFilter(commandBuffer: any MTL4CommandBuffer,
                            pipeline: any MTLComputePipelineState,
                            table: any MTL4ArgumentTable,
                            staging: any MTLBuffer, params: any MTLBuffer,
                            source: any MTLTexture, destination: any MTLTexture) {
    guard let pass = commandBuffer.makeComputeCommandEncoder() else { return }
    pass.copy(sourceBuffer: staging, sourceOffset: 0,
              destinationBuffer: params, destinationOffset: 0, size: staging.length)
    pass.barrier(afterEncoderStages: .blit, beforeEncoderStages: .dispatch,
                 visibilityOptions: .device)

    table.setTexture(source.gpuResourceID, index: 0)
    table.setTexture(destination.gpuResourceID, index: 1)
    table.setAddress(params.gpuAddress, index: 0)
    pass.setComputePipelineState(pipeline)
    pass.setArgumentTable(table)
    // Only a descriptor pin reads back here. Stop rather than guess a shape.
    let group = pipeline.requiredThreadsPerThreadgroup
    precondition(group.width > 0,
                 "Pin requiredThreadsPerThreadgroup on the pipeline descriptor for this kernel")
    pass.dispatchThreads(threadsPerGrid: MTLSize(width: destination.width,
                                                 height: destination.height, depth: 1),
                         threadsPerThreadgroup: group)
    pass.endEncoding()
}

/// Compile a compute pipeline whose kernel assumes 16 x 16 groups.
func makeFilterPipeline(device: any MTLDevice, library: any MTLLibrary) throws
    -> any MTLComputePipelineState {
    let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
    let function = MTL4LibraryFunctionDescriptor()
    function.library = library
    function.name = "filterTile"
    let descriptor = MTL4ComputePipelineDescriptor()
    descriptor.computeFunctionDescriptor = function
    descriptor.requiredThreadsPerThreadgroup = MTLSize(width: 16, height: 16, depth: 1)
    return try compiler.makeComputePipelineState(descriptor: descriptor,
                                                 dynamicLinkingDescriptor: nil,
                                                 compilerTaskOptions: nil)
}

/// Only for kernels that pin nothing, in the MSL attribute or on the descriptor.
/// For a kernel pinned only by the attribute this returns the wrong shape, silently.
func widestGroup(for pipeline: any MTLComputePipelineState) -> MTLSize {
    let w = pipeline.threadExecutionWidth
    return MTLSize(width: w, height: pipeline.maxTotalThreadsPerThreadgroup / w, depth: 1)
}
