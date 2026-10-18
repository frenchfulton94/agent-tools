import Metal
import Foundation

setvbuf(stdout, nil, _IONBF, 0)
let device = MTLCreateSystemDefaultDevice()!
let src = """
#include <metal_stdlib>
using namespace metal;
constant bool use_red [[function_constant(0)]];
vertex float4 vs(uint vid [[vertex_id]]) {
  float2 p[3] = { float2(-1,-1), float2(3,-1), float2(-1,3) };
  return float4(p[vid], 0.25, 1);
}
fragment float4 fs() { return use_red ? float4(1,0,0,1) : float4(0,1,0,1); }
"""
let serializerDesc = MTL4PipelineDataSetSerializerDescriptor()
print("default serializer configuration rawValue:", serializerDesc.configuration.rawValue)
serializerDesc.configuration = [.captureDescriptors, .captureBinaries]
let serializer = device.makePipelineDataSetSerializer(descriptor: serializerDesc)
let cdesc = MTL4CompilerDescriptor()
cdesc.pipelineDataSetSerializer = serializer
let compiler = try device.makeCompiler(descriptor: cdesc)
let ld = MTL4LibraryDescriptor(); ld.source = src
let lib = try compiler.makeLibrary(descriptor: ld)
func fn(_ n: String) -> MTL4LibraryFunctionDescriptor { let f = MTL4LibraryFunctionDescriptor(); f.name = n; f.library = lib; return f }
func spec(_ n: String, red: Bool) -> MTL4SpecializedFunctionDescriptor {
  let s = MTL4SpecializedFunctionDescriptor()
  s.functionDescriptor = fn(n)
  let cv = MTLFunctionConstantValues(); var r = red
  cv.setConstantValue(&r, type: .bool, index: 0)
  s.constantValues = cv
  return s
}

// 1. Unspecialized color format, then specialize.
let d = MTL4RenderPipelineDescriptor()
d.label = "flex"
d.vertexFunctionDescriptor = fn("vs")
d.fragmentFunctionDescriptor = spec("fs", red: true)
d.colorAttachments[0].pixelFormat = .unspecialized
let flexible = try compiler.makeRenderPipelineState(descriptor: d)
print("flexible created")
let sd = flexible.makeRenderPipelineDescriptorForSpecialization()
print("specialization descriptor type:", type(of: sd))
if let rsd = sd as? MTL4RenderPipelineDescriptor {
  rsd.colorAttachments[0].pixelFormat = .bgra8Unorm
  let concrete = try compiler.makeRenderPipelineStateBySpecialization(descriptor: rsd, pipeline: flexible)
  print("specialized ok", concrete)
  do { _ = try compiler.makeRenderPipelineStateBySpecialization(descriptor: rsd, pipeline: concrete); print("re-specialize unexpectedly ok") } catch { print("re-specialize error:", error.localizedDescription) }
}
// 2. A plain pipeline, async.
let d2 = MTL4RenderPipelineDescriptor()
d2.label = "plain"
d2.vertexFunctionDescriptor = fn("vs")
d2.fragmentFunctionDescriptor = spec("fs", red: false)
d2.colorAttachments[0].pixelFormat = .rgba8Unorm
let sem = DispatchSemaphore(value: 0)
Task {
  do { _ = try await compiler.makeRenderPipelineState(descriptor: d2); print("async plain ok") } catch { print("async error", error) }
  sem.signal()
}
sem.wait()
// 3. Serialize, reload, hit and miss.
let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("probe-\(getpid()).mtl4archive")
do { try serializer.serializeAsArchiveAndFlush(url: url); print("serialized to", url.path, (try? FileManager.default.attributesOfItem(atPath: url.path)[.size]) ?? "?") } catch { print("serialize error:", error) }
let script = try serializer.serializeAsPipelinesScript()
print("pipelines script bytes:", script.count)
let archive: any MTL4Archive
do { archive = try device.makeArchive(url: url) } catch { print("makeArchive error:", error.localizedDescription, "exists:", FileManager.default.fileExists(atPath: url.path)); var isDir: ObjCBool = false; _ = FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir); print("isDir", isDir.boolValue); exit(1) }
do { _ = try archive.makeRenderPipelineState(descriptor: d2); print("archive hit ok") } catch { print("archive hit error:", error.localizedDescription) }
let d3 = MTL4RenderPipelineDescriptor()
d3.vertexFunctionDescriptor = fn("vs")
d3.fragmentFunctionDescriptor = spec("fs", red: false)
d3.colorAttachments[0].pixelFormat = .rgba16Float
do { _ = try archive.makeRenderPipelineState(descriptor: d3); print("archive miss returned a pipeline") } catch { print("archive miss error:", error.localizedDescription) }
let opts = MTL4CompilerTaskOptions(); opts.lookupArchives = [archive]
let plainCompiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
do { _ = try plainCompiler.makeRenderPipelineState(descriptor: d3, compilerTaskOptions: opts); print("compiler with lookupArchives on a miss: compiled") } catch { print("compiler miss error", error) }
// 4. Serializer default config: can it write an archive?
let s2 = device.makePipelineDataSetSerializer(descriptor: MTL4PipelineDataSetSerializerDescriptor())
let c2d = MTL4CompilerDescriptor(); c2d.pipelineDataSetSerializer = s2
let c2 = try device.makeCompiler(descriptor: c2d)
_ = try c2.makeRenderPipelineState(descriptor: d2)
let url2 = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("probe2-\(getpid()).mtl4archive")
do { try s2.serializeAsArchiveAndFlush(url: url2); print("default-config archive serialized") } catch { print("default-config archive error:", error.localizedDescription) }
try? FileManager.default.removeItem(at: url); try? FileManager.default.removeItem(at: url2)
