import Metal
import Foundation
setvbuf(stdout, nil, _IONBF, 0)
let device = MTLCreateSystemDefaultDevice()!
let src = """
#include <metal_stdlib>
using namespace metal;
vertex float4 vs(uint vid [[vertex_id]]) { float2 p[3] = { float2(-1,-1), float2(3,-1), float2(-1,3) }; return float4(p[vid], 0.5, 1); }
fragment float4 fs() { return float4(0,0,1,1); }
"""
let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
let ld = MTL4LibraryDescriptor(); ld.source = src
let lib = try compiler.makeLibrary(descriptor: ld)
let v = MTL4LibraryFunctionDescriptor(); v.name = "vs"; v.library = lib
let f = MTL4LibraryFunctionDescriptor(); f.name = "fs"; f.library = lib
let pd = MTL4RenderPipelineDescriptor(); pd.vertexFunctionDescriptor = v; pd.fragmentFunctionDescriptor = f
pd.colorAttachments[0].pixelFormat = .rgba8Unorm
pd.rasterSampleCount = 4
let pso = try compiler.makeRenderPipelineState(descriptor: pd)
let rd = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 16, height: 16, mipmapped: false)
rd.usage = [.renderTarget]; rd.storageMode = .shared
let resolve = device.makeTexture(descriptor: rd)!
let md = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 16, height: 16, mipmapped: false)
md.textureType = .type2DMultisample; md.sampleCount = 4; md.usage = .renderTarget; md.storageMode = .memoryless
let msaa = device.makeTexture(descriptor: md)!
let dd = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .depth32Float, width: 16, height: 16, mipmapped: false)
dd.textureType = .type2DMultisample; dd.sampleCount = 4; dd.usage = .renderTarget; dd.storageMode = .memoryless
let depth = device.makeTexture(descriptor: dd)!
let dsd = MTLDepthStencilDescriptor(); dsd.depthCompareFunction = .less; dsd.isDepthWriteEnabled = true
let dss = device.makeDepthStencilState(descriptor: dsd)!
let queue = device.makeMTL4CommandQueue()!
let rs = try device.makeResidencySet(descriptor: MTLResidencySetDescriptor())
rs.addAllocation(resolve)
if CommandLine.arguments.contains("residentMemoryless") { rs.addAllocation(msaa); rs.addAllocation(depth) }
rs.commit(); queue.addResidencySet(rs)
let alloc = device.makeCommandAllocator()!
let cb = device.makeCommandBuffer()!
cb.beginCommandBuffer(allocator: alloc)
let pass = MTL4RenderPassDescriptor()
pass.colorAttachments[0].texture = msaa
pass.colorAttachments[0].loadAction = .clear
pass.colorAttachments[0].clearColor = MTLClearColor(red: 1, green: 0, blue: 0, alpha: 1)
pass.colorAttachments[0].storeAction = .multisampleResolve
pass.colorAttachments[0].resolveTexture = resolve
pass.depthAttachment.texture = depth
pass.depthAttachment.loadAction = .clear
pass.depthAttachment.clearDepth = 1.0
pass.depthAttachment.storeAction = .dontCare
let enc = cb.makeRenderCommandEncoder(descriptor: pass, options: [])!
enc.setRenderPipelineState(pso); enc.setDepthStencilState(dss)
enc.drawPrimitives(primitiveType: .triangle, vertexStart: 0, vertexCount: 3)
enc.endEncoding()
cb.endCommandBuffer()
let ev = device.makeSharedEvent()!
queue.commit([cb]); queue.signalEvent(ev, value: 1)
print("wait:", ev.wait(untilSignaledValue: 1, timeoutMS: 2000))
var px: [UInt8] = [0,0,0,0]
resolve.getBytes(&px, bytesPerRow: 64, from: MTLRegionMake2D(8, 8, 1, 1), mipmapLevel: 0)
print("resolved pixel:", px)
