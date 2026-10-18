import Metal

/// The MSL the frame's pipeline compiles. It is the same source as the
/// metal block below, which the gate compiles under -std=metal4.0.
let flatColorShaderSource = """
#include <metal_stdlib>
using namespace metal;

struct FrameUniforms { float4 color; };
struct VertexOut { float4 position [[position]]; };

vertex VertexOut fullscreenVertex(uint vid [[vertex_id]]) {
    float2 p = float2((vid << 1) & 2, vid & 2);
    VertexOut out;
    out.position = float4(p * 2.0 - 1.0, 0.0, 1.0);
    return out;
}

fragment float4 flatColorFragment(constant FrameUniforms& uniforms [[buffer(0)]]) {
    return uniforms.color;
}
"""

/// Builds the pipeline once, at load time, never inside the frame.
func makeFlatColorPipeline(device: any MTLDevice,
                           pixelFormat: MTLPixelFormat) throws -> any MTLRenderPipelineState {
    let library = try device.makeLibrary(source: flatColorShaderSource, options: nil)
    let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())

    let vertexFunction = MTL4LibraryFunctionDescriptor()
    vertexFunction.library = library
    vertexFunction.name = "fullscreenVertex"
    let fragmentFunction = MTL4LibraryFunctionDescriptor()
    fragmentFunction.library = library
    fragmentFunction.name = "flatColorFragment"

    let descriptor = MTL4RenderPipelineDescriptor()
    descriptor.vertexFunctionDescriptor = vertexFunction
    descriptor.fragmentFunctionDescriptor = fragmentFunction
    descriptor.colorAttachments[0].pixelFormat = pixelFormat
    return try compiler.makeRenderPipelineState(descriptor: descriptor)
}
