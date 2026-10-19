import Metal
let device = MTLCreateSystemDefaultDevice()!
let src = """
#include <metal_stdlib>
using namespace metal;
[[kernel, required_threads_per_threadgroup(16, 16, 1)]]
void pinned(device uint* o [[buffer(0)]], uint2 i [[thread_position_in_grid]],
            uint2 tpt [[threads_per_threadgroup]]) {
  if (i.x == 0 && i.y == 0) { o[4096] = tpt.x; o[4097] = tpt.y; }
  o[i.y * 64 + i.x] = 1;
}
"""
let library = try device.makeLibrary(source: src, options: nil)
let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())
let fd = MTL4LibraryFunctionDescriptor(); fd.library = library; fd.name = "pinned"
let d = MTL4ComputePipelineDescriptor(); d.computeFunctionDescriptor = fd
let pso = try compiler.makeComputePipelineState(descriptor: d)
// The snippet's sizing, verbatim.
let pinned = pso.requiredThreadsPerThreadgroup
let width = pso.threadExecutionWidth
let group = pinned.width > 0 ? pinned : MTLSize(width: width, height: pso.maxTotalThreadsPerThreadgroup / width, depth: 1)
print("group", group.width, group.height, group.depth)
let queue = device.makeMTL4CommandQueue()!
let cb = device.makeCommandBuffer()!
let alloc = device.makeCommandAllocator()!
let buf = device.makeBuffer(length: 4 * 4098, options: .storageModeShared)!
memset(buf.contents(), 0, 4 * 4098)
let rsd = MTLResidencySetDescriptor()
let rs = try device.makeResidencySet(descriptor: rsd)
rs.addAllocation(buf); rs.commit()
let atd = MTL4ArgumentTableDescriptor(); atd.maxBufferBindCount = 1
let table = try device.makeArgumentTable(descriptor: atd)
let ev = device.makeSharedEvent()!
cb.beginCommandBuffer(allocator: alloc)
cb.useResidencySet(rs)
let enc = cb.makeComputeCommandEncoder()!
enc.setComputePipelineState(pso)
table.setAddress(buf.gpuAddress, index: 0)
enc.setArgumentTable(table)
enc.dispatchThreads(threadsPerGrid: MTLSize(width: 64, height: 64, depth: 1), threadsPerThreadgroup: group)
enc.endEncoding()
cb.endCommandBuffer()
queue.commit([cb])
queue.signalEvent(ev, value: 1)
_ = ev.wait(untilSignaledValue: 1, timeoutMS: 2000)
let p = buf.contents().bindMemory(to: UInt32.self, capacity: 4098)
var n = 0; for k in 0..<4096 { n += Int(p[k]) }
print("written", n, "tpt", p[4096], p[4097])
