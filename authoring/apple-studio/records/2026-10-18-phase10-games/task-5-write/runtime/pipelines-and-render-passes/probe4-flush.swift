import Metal
import Foundation
setvbuf(stdout, nil, _IONBF, 0)
let device = MTLCreateSystemDefaultDevice()!
let lib = try! device.makeLibrary(URL: URL(fileURLWithPath: CommandLine.arguments[1]))
for raw: UInt in [0, 1, 2, 3] {
  let sd = MTL4PipelineDataSetSerializerDescriptor(); sd.configuration = MTL4PipelineDataSetSerializerConfiguration(rawValue: raw)
  let ser = device.makePipelineDataSetSerializer(descriptor: sd)
  let cd = MTL4CompilerDescriptor(); cd.pipelineDataSetSerializer = ser
  let compiler = try! device.makeCompiler(descriptor: cd)
  let v = MTL4LibraryFunctionDescriptor(); v.name = "vs"; v.library = lib
  let f = MTL4LibraryFunctionDescriptor(); f.name = "fs"; f.library = lib
  let d = MTL4RenderPipelineDescriptor(); d.vertexFunctionDescriptor = v; d.fragmentFunctionDescriptor = f
  d.colorAttachments[0].pixelFormat = .rgba8Unorm
  _ = try! compiler.makeRenderPipelineState(descriptor: d)
  var s = ""
  do { let data = try ser.serializeAsPipelinesScript(); s = "script \(data.count) bytes" } catch { s = "script error \(error)" }
  let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("p4-\(getpid())-\(raw)")
  var a = ""
  do { try ser.serializeAsArchiveAndFlush(url: url); a = "archive ok" } catch { a = "archive error \(error)" }
  // second call after a successful flush
  var a2 = ""
  if a == "archive ok" { do { try ser.serializeAsArchiveAndFlush(url: url.appendingPathExtension("b")); a2 = "second flush ok" } catch { a2 = "second flush error \(error)" } }
  print("config \(raw): \(s); \(a); \(a2)")
  try? FileManager.default.removeItem(at: url); try? FileManager.default.removeItem(at: url.appendingPathExtension("b"))
}
