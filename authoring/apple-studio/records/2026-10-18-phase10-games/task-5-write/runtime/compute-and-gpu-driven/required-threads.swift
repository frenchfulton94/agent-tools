import Metal
// What MTLComputePipelineState.requiredThreadsPerThreadgroup reads when nothing pins it.
let device = MTLCreateSystemDefaultDevice()!
let src = """
#include <metal_stdlib>
using namespace metal;
kernel void free_size(device float* o [[buffer(0)]], uint i [[thread_position_in_grid]]) { o[i] = 1; }
[[kernel, required_threads_per_threadgroup(16, 16, 1)]]
void pinned(device float* o [[buffer(0)]], uint2 i [[thread_position_in_grid]]) { o[i.x] = 1; }
"""
let library = try device.makeLibrary(source: src, options: nil)
let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
for (name, pin) in [("free_size", false), ("pinned", false), ("pinned", true), ("free_size", true)] {
    let function = MTL4LibraryFunctionDescriptor()
    function.library = library
    function.name = name
    let descriptor = MTL4ComputePipelineDescriptor()
    descriptor.computeFunctionDescriptor = function
    if pin { descriptor.requiredThreadsPerThreadgroup = MTLSize(width: 16, height: 16, depth: 1) }
    let pipeline = try compiler.makeComputePipelineState(descriptor: descriptor)
    let r = pipeline.requiredThreadsPerThreadgroup
    print(name, "descriptorPin", pin, "required", r.width, r.height, r.depth,
          "execWidth", pipeline.threadExecutionWidth,
          "maxTotal", pipeline.maxTotalThreadsPerThreadgroup)
}
