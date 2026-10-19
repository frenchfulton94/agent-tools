// Runtime check for assets.md, texture bake hand-off.
// Usage:
//   ktx_check make-png <out.png>          writes a 256x256 RGBA gradient
//   ktx_check load <file> [<file> ...]    loads each with MTKTextureLoader, with and without .origin
import CoreGraphics
import Foundation
import ImageIO
import Metal
import MetalKit
import UniformTypeIdentifiers

let args = CommandLine.arguments
if args.count >= 3, args[1] == "make-png" {
    let w = 256, h = 256
    var px = [UInt8](repeating: 0, count: w * h * 4)
    for y in 0..<h { for x in 0..<w {
        let i = (y * w + x) * 4
        px[i] = UInt8(x); px[i + 1] = UInt8(y); px[i + 2] = UInt8((x ^ y) & 0xFF); px[i + 3] = 255
    } }
    let ctx = CGContext(data: &px, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                        space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    let img = ctx.makeImage()!
    let dst = CGImageDestinationCreateWithURL(URL(fileURLWithPath: args[2]) as CFURL,
                                              UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dst, img, nil)
    print("png written:", CGImageDestinationFinalize(dst))
    exit(0)
}

guard args.count >= 3, args[1] == "load", let device = MTLCreateSystemDefaultDevice() else {
    print("usage: ktx_check make-png <out> | load <files...>"); exit(2)
}
print("device:", device.name)
let loader = MTKTextureLoader(device: device)
for path in args.dropFirst(2) {
    let url = URL(fileURLWithPath: path)
    let cases: [(String, [MTKTextureLoader.Option: Any])] = [
        ("no options   ", [:]),
        ("origin=bottom", [.origin: MTKTextureLoader.Origin.bottomLeft]),
        ("SRGB=true    ", [.SRGB: true]),
    ]
    for (label, opts) in cases {
        do {
            let t = try loader.newTexture(URL: url, options: opts)
            print(url.lastPathComponent, label, "OK pixelFormat=\(t.pixelFormat.rawValue)",
                  "mips=\(t.mipmapLevelCount)", "\(t.width)x\(t.height)")
        } catch {
            print(url.lastPathComponent, label, "ERROR", error.localizedDescription)
        }
    }
}
