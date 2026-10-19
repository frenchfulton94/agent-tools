import Metal

/// The probe's own compute workload: `sum[i] = a[i] + b[i]` in one Metal 4
/// compute pass. It is not from a reference; it gives the capture a dispatch.
let addArraysSource = """
#include <metal_stdlib>
using namespace metal;

kernel void addArrays(device const float* a   [[buffer(0)]],
                      device const float* b   [[buffer(1)]],
                      device float*       sum [[buffer(2)]],
                      uint i [[thread_position_in_grid]]) {
    sum[i] = a[i] + b[i];
}
"""

enum ComputeError: Error {
    case creationFailed(String)
    case gpuTimeout
}

/// Compiles the add kernel. Engines build pipelines at load time; a capture
/// that also records this compile is a different trace (see `runCapture`).
func makeAddArraysPipeline(device: any MTLDevice) throws -> any MTLComputePipelineState {
    let library = try device.makeLibrary(source: addArraysSource, options: nil)
    let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
    let function = MTL4LibraryFunctionDescriptor()
    function.library = library
    function.name = "addArrays"
    let descriptor = MTL4ComputePipelineDescriptor()
    descriptor.computeFunctionDescriptor = function
    return try compiler.makeComputePipelineState(descriptor: descriptor,
                                                 dynamicLinkingDescriptor: nil,
                                                 compilerTaskOptions: nil)
}

/// Runs the add on `queue` and returns how many elements equal `a + b`.
func runAddArrays(device: any MTLDevice, queue: any MTL4CommandQueue,
                  pipeline: any MTLComputePipelineState, count: Int) throws -> Int {
    let length = count * MemoryLayout<Float>.stride
    guard let a = device.makeBuffer(length: length, options: .storageModeShared),
          let b = device.makeBuffer(length: length, options: .storageModeShared),
          let sum = device.makeBuffer(length: length, options: .storageModeShared),
          let allocator = device.makeCommandAllocator(),
          let commandBuffer = device.makeCommandBuffer(),
          let done = device.makeSharedEvent() else {
        throw ComputeError.creationFailed("buffers, allocator, command buffer, or event")
    }
    a.label = "a"
    b.label = "b"
    sum.label = "sum"
    let pa = a.contents().bindMemory(to: Float.self, capacity: count)
    let pb = b.contents().bindMemory(to: Float.self, capacity: count)
    for i in 0..<count {
        pa[i] = Float(i)
        pb[i] = Float(2 * i + 1)
    }

    let residency = try device.makeResidencySet(descriptor: MTLResidencySetDescriptor())
    residency.addAllocations([a, b, sum])
    residency.commit()

    let tableDescriptor = MTL4ArgumentTableDescriptor()
    tableDescriptor.maxBufferBindCount = 3
    let table = try device.makeArgumentTable(descriptor: tableDescriptor)
    table.setAddress(a.gpuAddress, index: 0)
    table.setAddress(b.gpuAddress, index: 1)
    table.setAddress(sum.gpuAddress, index: 2)

    commandBuffer.beginCommandBuffer(allocator: allocator)
    commandBuffer.useResidencySet(residency)   // after begin, which clears it
    commandBuffer.pushDebugGroup("Compute")
    guard let pass = commandBuffer.makeComputeCommandEncoder() else {
        commandBuffer.popDebugGroup()
        commandBuffer.endCommandBuffer()
        throw ComputeError.creationFailed("compute encoder")
    }
    pass.label = "Add arrays"
    pass.setComputePipelineState(pipeline)
    pass.setArgumentTable(table)
    // A 1D group: the widest the pipeline allows, a multiple of the SIMD width.
    let width = pipeline.maxTotalThreadsPerThreadgroup
    pass.dispatchThreads(threadsPerGrid: MTLSize(width: count, height: 1, depth: 1),
                         threadsPerThreadgroup: MTLSize(width: width, height: 1, depth: 1))
    pass.endEncoding()
    commandBuffer.popDebugGroup()
    commandBuffer.endCommandBuffer()
    queue.commit([commandBuffer], options: nil)
    queue.signalEvent(done, value: 1)
    guard done.wait(untilSignaledValue: 1, timeoutMS: 5_000) else { throw ComputeError.gpuTimeout }

    let ps = sum.contents().bindMemory(to: Float.self, capacity: count)
    var matches = 0
    for i in 0..<count where ps[i] == pa[i] + pb[i] {
        matches += 1
    }
    return matches
}
