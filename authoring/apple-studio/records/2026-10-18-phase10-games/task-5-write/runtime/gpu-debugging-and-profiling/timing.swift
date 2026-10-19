import Metal
import Foundation

let device = MTLCreateSystemDefaultDevice()!
let queue = device.makeMTL4CommandQueue()!
let allocator = device.makeCommandAllocator()!
let commandBuffer = device.makeCommandBuffer()!

let src = """
#include <metal_stdlib>
#include <metal_logging>
using namespace metal;
constant os_log logger("com.example.engine", "gpu");
kernel void busy(uint i [[thread_position_in_grid]]) {
    float x = float(i);
    for (int k = 0; k < 2000; ++k) { x = sin(x) * 1.0001f + 0.5f; }
    if (i == 0) { logger.log_info("thread 0 says %f", x); }
}
"""
let opts = MTLCompileOptions()
opts.enableLogging = true
let library = try! device.makeLibrary(source: src, options: opts)
let compiler = try! device.makeCompiler(descriptor: MTL4CompilerDescriptor())
let fd = MTL4LibraryFunctionDescriptor()
fd.name = "busy"
fd.library = library
let cpd = MTL4ComputePipelineDescriptor()
cpd.computeFunctionDescriptor = fd
let pso = try! compiler.makeComputePipelineState(descriptor: cpd)

let logDesc = MTLLogStateDescriptor()
logDesc.level = .debug
logDesc.bufferSize = 64 * 1024
let logState = try! device.makeLogState(descriptor: logDesc)
logState.addLogHandler { subsystem, category, level, message in
    print("[GPU log] \(subsystem ?? "-")/\(category ?? "-") \(level.rawValue): \(message)")
}
let cbOptions = MTL4CommandBufferOptions()
cbOptions.logState = logState

let heapDesc = MTL4CounterHeapDescriptor()
heapDesc.type = .timestamp
heapDesc.count = 2
let timestamps = try! device.makeCounterHeap(descriptor: heapDesc)
print("entry size:", device.size(ofCounterHeapEntry: .timestamp), "freq:", device.queryTimestampFrequency())

let event = device.makeSharedEvent()!
commandBuffer.beginCommandBuffer(allocator: allocator, options: cbOptions)
commandBuffer.pushDebugGroup("Timed compute")
let enc = commandBuffer.makeComputeCommandEncoder()!
enc.writeTimestamp(granularity: .precise, counterHeap: timestamps, index: 0)
enc.setComputePipelineState(pso)
enc.dispatchThreads(threadsPerGrid: MTLSize(width: 1 << 20, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: 256, height: 1, depth: 1))
enc.writeTimestamp(granularity: .precise, counterHeap: timestamps, index: 1)
enc.endEncoding()
commandBuffer.popDebugGroup()
commandBuffer.endCommandBuffer()

let commitOptions = MTL4CommitOptions()
commitOptions.addFeedbackHandler { feedback in
    if let error = feedback.error { print("GPU error:", error) }
    print("feedback GPU ms:", (feedback.gpuEndTime - feedback.gpuStartTime) * 1000)
}
queue.commit([commandBuffer], options: commitOptions)
queue.signalEvent(event, value: 1)
_ = event.wait(untilSignaledValue: 1, timeoutMS: 5000)

if let data = try! timestamps.resolveCounterRange(0..<2) {
    let ticks = data.withUnsafeBytes { Array($0.bindMemory(to: MTL4TimestampHeapEntry.self)) }
    print("bytes:", data.count, "ticks:", ticks.map { $0.timestamp })
    let ms = Double(ticks[1].timestamp &- ticks[0].timestamp) / Double(device.queryTimestampFrequency()) * 1000
    print("heap GPU ms:", ms)
}
Thread.sleep(forTimeInterval: 0.5)
