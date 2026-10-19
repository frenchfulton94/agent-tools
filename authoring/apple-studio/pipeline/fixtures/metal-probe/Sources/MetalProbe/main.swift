import Foundation
import Metal

// MetalProbe: runtime checks for the apple-metal references. See README.md.
//
//   MetalProbe render  --frames <n>
//   MetalProbe compute --count <n>
//   MetalProbe capture --out <path.gputrace> [--no-compute] [--compile-in-capture]
//                                     (needs MTL_CAPTURE_ENABLED=1)
//   MetalProbe sim     --ticks <n> [--slow]

/// Reports to stderr, and to stdout as well: `xctrace record --target-stdout`
/// relays only stdout, and a failure under Instruments is otherwise silent.
func fail(_ message: String, code: Int32 = 1) -> Never {
    FileHandle.standardError.write(Data("MetalProbe: \(message)\n".utf8))
    print("MetalProbe: error: \(message)")
    exit(code)
}

func usage() -> Never {
    fail("""
    usage: MetalProbe render --frames <n>
           MetalProbe compute --count <n>
           MetalProbe capture --out <path.gputrace>
           MetalProbe sim --ticks <n> [--slow]
    """, code: 2)
}

let arguments = Array(CommandLine.arguments.dropFirst())

func option(_ name: String) -> String? {
    guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count else { return nil }
    return arguments[i + 1]
}

func positiveInt(_ name: String) -> Int {
    guard let text = option(name), let value = Int(text), value > 0 else { usage() }
    return value
}

func metal4Device() -> any MTLDevice {
    guard let device = MTLCreateSystemDefaultDevice() else { fail("no Metal device") }
    guard device.supportsFamily(.metal4) else { fail("\(device.name) does not support Metal 4") }
    return device
}

/// A 64 x 64 shared render target, so the CPU can read it back with no blit.
func makeOffscreenTarget(device: any MTLDevice) throws -> any MTLTexture {
    let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm,
                                                              width: 64, height: 64,
                                                              mipmapped: false)
    descriptor.usage = [.renderTarget]
    descriptor.storageMode = .shared
    guard let texture = device.makeTexture(descriptor: descriptor) else {
        throw CaptureProbeError.creationFailed("offscreen target")
    }
    texture.label = "Offscreen target"
    return texture
}

do {
    switch arguments.first {
    case "render":
        let frames = positiveInt("--frames")
        let device = metal4Device()
        let target = try makeOffscreenTarget(device: device)
        try renderOffscreen(device: device, target: target, frames: frames)
        var pixel = [UInt8](repeating: 0, count: 4)
        target.getBytes(&pixel, bytesPerRow: target.width * 4,
                        from: MTLRegionMake2D(target.width / 2, target.height / 2, 1, 1),
                        mipmapLevel: 0)
        print("pixel \(pixel[0]) \(pixel[1]) \(pixel[2]) \(pixel[3])")
        // renderOffscreen's last frame sets SIMD4(shade, 0.5, 0.25, 1).
        let shade = Float((frames - 1) % 256) / 255
        let expected = [shade, 0.5, 0.25, 1].map { UInt8(($0 * 255).rounded()) }
        guard pixel == expected else { fail("pixel \(pixel) is not the color the frame set, \(expected)") }

    case "compute":
        let count = positiveInt("--count")
        let device = metal4Device()
        guard let queue = device.makeMTL4CommandQueue() else { fail("no MTL4CommandQueue") }
        let pipeline = try makeAddArraysPipeline(device: device)
        let matches = try runAddArrays(device: device, queue: queue, pipeline: pipeline, count: count)
        guard matches == count else { fail("\(count - matches) of \(count) elements differ from a + b") }
        print("compute ok \(count)")

    case "capture":
        guard let path = option("--out") else { usage() }
        try runCapture(device: metal4Device(), url: URL(fileURLWithPath: path),
                       compute: !arguments.contains("--no-compute"),
                       compileInCapture: arguments.contains("--compile-in-capture"))

    case "sim":
        let ticks = positiveInt("--ticks")
        let slow = arguments.contains("--slow")
        let checksum = runSim(ticks: ticks, slow: slow)
        print("sim ok \(ticks) ticks\(slow ? " slow" : "") checksum \(checksum)")

    default:
        usage()
    }
} catch {
    fail("\(error)")
}
