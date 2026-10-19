import Metal
// Drives compute-and-gpu-driven.md's encodeUploadThenFilter and makeFilterPipeline, copied
// verbatim from the reference into snippet.swift, against the reference's filterTile kernel.
// Mode "pinned": pipeline from makeFilterPipeline (descriptor pin). Mode "attr-only": the
// same kernel with no descriptor pin, which must stop at the precondition.
setvbuf(stdout, nil, _IONBF, 0)
let mode = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "pinned"
let device = MTLCreateSystemDefaultDevice()!
let source = try String(contentsOfFile: CommandLine.arguments[2], encoding: .utf8)
let library = try device.makeLibrary(source: "#include <metal_stdlib>\nusing namespace metal;\n" + source,
                                     options: nil)
let pipeline: any MTLComputePipelineState
if mode == "pinned" {
    pipeline = try makeFilterPipeline(device: device, library: library)
} else {
    let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
    let function = MTL4LibraryFunctionDescriptor()
    function.library = library
    function.name = "filterTile"
    let descriptor = MTL4ComputePipelineDescriptor()
    descriptor.computeFunctionDescriptor = function
    pipeline = try compiler.makeComputePipelineState(descriptor: descriptor)
}
let r = pipeline.requiredThreadsPerThreadgroup
print(mode, "requiredThreadsPerThreadgroup", r.width, r.height, r.depth,
      "maxTotal", pipeline.maxTotalThreadsPerThreadgroup)

let side = 64
let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba16Float, width: side, height: side, mipmapped: false)
td.usage = [.shaderRead, .shaderWrite]
td.storageMode = .shared
let src = device.makeTexture(descriptor: td)!
let dst = device.makeTexture(descriptor: td)!
var pixels = [UInt16](repeating: 0, count: side * side * 4)
for i in 0..<pixels.count { pixels[i] = UInt16(0x3C00 + (i % 7)) }   // distinct half values
src.replace(region: MTLRegionMake2D(0, 0, side, side), mipmapLevel: 0, withBytes: pixels, bytesPerRow: side * 8)
let staging = device.makeBuffer(length: 16, options: .storageModeShared)!
let params = device.makeBuffer(length: 16, options: .storageModeShared)!

let queue = device.makeMTL4CommandQueue()!
let set = try device.makeResidencySet(descriptor: MTLResidencySetDescriptor())
for a in [src, dst, staging, params] as [any MTLAllocation] { set.addAllocation(a) }
set.commit()
queue.addResidencySet(set)
let tableDescriptor = MTL4ArgumentTableDescriptor()
tableDescriptor.maxTextureBindCount = 2
tableDescriptor.maxBufferBindCount = 1
let table = try device.makeArgumentTable(descriptor: tableDescriptor)
let commandBuffer = device.makeCommandBuffer()!
let allocator = device.makeCommandAllocator()!
let event = device.makeSharedEvent()!

commandBuffer.beginCommandBuffer(allocator: allocator)
encodeUploadThenFilter(commandBuffer: commandBuffer, pipeline: pipeline, table: table,
                       staging: staging, params: params, source: src, destination: dst)
commandBuffer.endCommandBuffer()
queue.commit([commandBuffer])
queue.signalEvent(event, value: 1)
_ = event.wait(untilSignaledValue: 1, timeoutMS: 2000)
var out = [UInt16](repeating: 0, count: pixels.count)
dst.getBytes(&out, bytesPerRow: side * 8, from: MTLRegionMake2D(0, 0, side, side), mipmapLevel: 0)
print(mode, "destination equals source:", out == pixels)
