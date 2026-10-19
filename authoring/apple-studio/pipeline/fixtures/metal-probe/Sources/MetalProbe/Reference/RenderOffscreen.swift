import Metal // probe: the reference block relies on the gate's imports

func renderOffscreen(device: any MTLDevice, target: any MTLTexture, frames: Int) throws {
    let pipeline = try makeFlatColorPipeline(device: device, pixelFormat: target.pixelFormat)
    let loop = try FrameLoop(device: device, pipeline: pipeline)
    loop.makeResident(target)
    for frame in 0..<frames {
        let shade = Float(frame % 256) / 255
        try loop.encodeFrame(into: target, color: SIMD4<Float>(shade, 0.5, 0.25, 1))
        loop.submitFrame()
        print("frame \(frame) ok") // probe: one line per encoded and submitted frame
    }
    try loop.waitUntilIdle()
}
