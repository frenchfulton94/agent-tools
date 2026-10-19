import Metal
import Foundation
setvbuf(stdout, nil, _IONBF, 0)
let device = MTLCreateSystemDefaultDevice()!
let args = CommandLine.arguments
// args[1]: path to a precompiled .metallib, or "source"
let lib: MTLLibrary
let srcText = """
#include <metal_stdlib>
using namespace metal;
vertex float4 vs(uint vid [[vertex_id]]) { float2 p[3] = { float2(-1,-1), float2(3,-1), float2(-1,3) }; return float4(p[vid], 0.25, 1); }
fragment float4 fs() { return float4(0,1,0,1); }
"""
func runOnce(config: MTL4PipelineDataSetSerializerConfiguration, ext: String, useFileLib: Bool) {
  let sd = MTL4PipelineDataSetSerializerDescriptor(); sd.configuration = config
  let ser = device.makePipelineDataSetSerializer(descriptor: sd)
  let cd = MTL4CompilerDescriptor(); cd.pipelineDataSetSerializer = ser
  let compiler = try! device.makeCompiler(descriptor: cd)
  let lib: MTLLibrary
  if useFileLib { lib = try! device.makeLibrary(URL: URL(fileURLWithPath: args[1])) }
  else { let ld = MTL4LibraryDescriptor(); ld.source = srcText; lib = try! compiler.makeLibrary(descriptor: ld) }
  func fn(_ n: String) -> MTL4LibraryFunctionDescriptor { let f = MTL4LibraryFunctionDescriptor(); f.name = n; f.library = lib; return f }
  let d = MTL4RenderPipelineDescriptor(); d.label = "plain"
  d.vertexFunctionDescriptor = fn("vs"); d.fragmentFunctionDescriptor = fn("fs")
  d.colorAttachments[0].pixelFormat = .rgba8Unorm
  _ = try! compiler.makeRenderPipelineState(descriptor: d)
  let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("p3-\(getpid())-\(config.rawValue)\(useFileLib ? "f" : "s")\(ext)")
  var msg = ""
  do { try ser.serializeAsArchiveAndFlush(url: url); msg = "serialized" } catch { msg = "serialize error: \(error)" }
  let exists = FileManager.default.fileExists(atPath: url.path)
  var hit = "-", miss = "-"
  if exists, let a = try? device.makeArchive(url: url) {
    do { _ = try a.makeRenderPipelineState(descriptor: d); hit = "hit ok" } catch { hit = "hit error: \(error.localizedDescription)" }
    let d3 = d.copy() as! MTL4RenderPipelineDescriptor
    d3.colorAttachments[0].pixelFormat = .rgba16Float
    do { _ = try a.makeRenderPipelineState(descriptor: d3); miss = "miss returned a pipeline" } catch { miss = "miss error: \(error.localizedDescription)" }
    let opts = MTL4CompilerTaskOptions(); opts.lookupArchives = [a]
    let plain = try! device.makeCompiler(descriptor: MTL4CompilerDescriptor())
    do { _ = try plain.makeRenderPipelineState(descriptor: d3, compilerTaskOptions: opts); miss += " | compiler+lookup on miss: compiled" } catch { miss += " | compiler+lookup error \(error)" }
  }
  print("config=\(config.rawValue) ext=\(ext) fileLib=\(useFileLib): \(msg); exists=\(exists); \(hit); \(miss)")
  try? FileManager.default.removeItem(at: url)
}
for useFile in [false, true] {
  for cfg: MTL4PipelineDataSetSerializerConfiguration in [[], [.captureBinaries], [.captureDescriptors, .captureBinaries]] {
    for ext in [".metallib", ".mtl4archive", ""] { runOnce(config: cfg, ext: ext, useFileLib: useFile) }
  }
}
