import Metal
import Foundation
setvbuf(stdout, nil, _IONBF, 0)
let device = MTLCreateSystemDefaultDevice()!
let lib = try! device.makeLibrary(URL: URL(fileURLWithPath: CommandLine.arguments[1]))
let mode = CommandLine.arguments[2]
let v = MTL4LibraryFunctionDescriptor(); v.name = "vs"; v.library = lib
let f = MTL4LibraryFunctionDescriptor(); f.name = "fs"; f.library = lib
let d = MTL4RenderPipelineDescriptor(); d.label = "probe.plain"
d.vertexFunctionDescriptor = v; d.fragmentFunctionDescriptor = f
d.colorAttachments[0].pixelFormat = .rgba8Unorm
if mode == "harvest" {
  let sd = MTL4PipelineDataSetSerializerDescriptor(); sd.configuration = .captureDescriptors
  let ser = device.makePipelineDataSetSerializer(descriptor: sd)
  let cd = MTL4CompilerDescriptor(); cd.pipelineDataSetSerializer = ser
  let compiler = try! device.makeCompiler(descriptor: cd)
  _ = try! compiler.makeRenderPipelineState(descriptor: d)
  let data = try! ser.serializeAsPipelinesScript()
  try! data.write(to: URL(fileURLWithPath: CommandLine.arguments[3]))
  print("wrote script")
} else {
  let a = try! device.makeArchive(url: URL(fileURLWithPath: CommandLine.arguments[3]))
  do { _ = try a.makeRenderPipelineState(descriptor: d); print("offline archive hit ok") } catch { print("offline archive error:", error.localizedDescription.prefix(120)) }
}
