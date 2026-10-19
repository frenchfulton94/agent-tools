import Metal
let d = MTLCreateSystemDefaultDevice()!
let src = """
#include <metal_stdlib>
using namespace metal;
vertex float4 vs(uint vid [[vertex_id]]) { return float4(0, 0, 0.5, 1); }
vertex void vsVoid(uint vid [[vertex_id]], device float* out [[buffer(0)]]) { out[vid] = 1; }
"""
let lib = try! d.makeLibrary(source: src, options: nil)
let compiler = try! d.makeCompiler(descriptor: MTL4CompilerDescriptor())
for (name, raster) in [("vs", false), ("vs", true), ("vsVoid", false)] {
    let f = MTL4LibraryFunctionDescriptor()
    f.library = lib
    f.name = name
    let desc = MTL4RenderPipelineDescriptor()
    desc.vertexFunctionDescriptor = f
    desc.isRasterizationEnabled = raster
    do {
        _ = try compiler.makeRenderPipelineState(descriptor: desc)
        print(name, "raster", raster, "OK")
    } catch {
        print(name, "raster", raster, "ERROR", error.localizedDescription)
    }
}
let fresh = MTLCompileOptions()
print("fresh mathMode", fresh.mathMode.rawValue, "lang", String(fresh.languageVersion.rawValue, radix: 16))
let sd = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 256, height: 256, mipmapped: true)
sd.storageMode = .private
let sa = d.heapTextureSizeAndAlign(descriptor: sd)
print("heap size", sa.size, "align", sa.align, "levels", sd.mipmapLevelCount)
print("ts freq", d.queryTimestampFrequency())
