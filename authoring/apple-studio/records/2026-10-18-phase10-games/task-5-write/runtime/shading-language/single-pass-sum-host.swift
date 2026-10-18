import Metal
let d = MTLCreateSystemDefaultDevice()!
let src = try! String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
let opts = MTLCompileOptions()
opts.languageVersion = .version4_1
let lib = try! d.makeLibrary(source: src, options: opts)
let ps = try! d.makeComputePipelineState(function: lib.makeFunction(name: "single_pass_sum")!)
let q = d.makeCommandQueue()!
var allOK = true
for trial in 0..<20 {
    let n = 1 << 20
    let tg = 256
    let groups = (n + tg - 1) / tg
    let input = d.makeBuffer(length: n * 4, options: .storageModeShared)!
    let p = input.contents().bindMemory(to: Float.self, capacity: n)
    for i in 0..<n { p[i] = 1 }
    let partials = d.makeBuffer(length: groups * 4, options: .storageModePrivate)!
    let finished = d.makeBuffer(length: 4, options: .storageModeShared)!
    finished.contents().storeBytes(of: UInt32(0), as: UInt32.self)
    let result = d.makeBuffer(length: 4, options: .storageModeShared)!
    var count = UInt32(n)
    let cb = q.makeCommandBuffer()!
    let e = cb.makeComputeCommandEncoder()!
    e.setComputePipelineState(ps)
    e.setBuffer(input, offset: 0, index: 0); e.setBuffer(partials, offset: 0, index: 1)
    e.setBuffer(finished, offset: 0, index: 2); e.setBuffer(result, offset: 0, index: 3)
    e.setBytes(&count, length: 4, index: 4)
    e.setThreadgroupMemoryLength(32 * 4, index: 0)
    e.dispatchThreads(MTLSize(width: n, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: tg, height: 1, depth: 1))
    e.endEncoding(); cb.commit(); cb.waitUntilCompleted()
    let r = result.contents().load(as: Float.self)
    if r != Float(n) { allOK = false; print("trial", trial, "got", r) }
}
print("all 20 trials exact:", allOK, "width", ps.threadExecutionWidth)
