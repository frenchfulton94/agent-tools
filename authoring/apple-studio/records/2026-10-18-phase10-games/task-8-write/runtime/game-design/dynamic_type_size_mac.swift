// Does SwiftUI text on macOS respond to a DynamicTypeSize set by the app,
// although macOS has no system Dynamic Type setting?
// Renders the same Text at several sizes offscreen with ImageRenderer (no window,
// no GUI session needed) and prints the rendered height in points.
import SwiftUI

@MainActor
func renderedHeight(_ size: DynamicTypeSize?, style: Font.TextStyle) -> CGFloat {
    let base = Text("Continue").font(.system(style))
    let view: AnyView
    if let size {
        view = AnyView(base.dynamicTypeSize(size).fixedSize())
    } else {
        view = AnyView(base.fixedSize())
    }
    let renderer = ImageRenderer(content: view)
    renderer.scale = 1
    guard let image = renderer.cgImage else { return -1 }
    return CGFloat(image.height)
}

@MainActor
func run() {
    let sizes: [(String, DynamicTypeSize?)] = [
        ("environment default", nil),
        ("xSmall", .xSmall),
        ("large", .large),
        ("xxxLarge", .xxxLarge),
        ("accessibility5", .accessibility5),
    ]
    for style in [Font.TextStyle.body, .title] {
        for (name, size) in sizes {
            print("style=\(style) size=\(name) heightPt=\(renderedHeight(size, style: style))")
        }
    }
    // The fixed-size font must not move.
    let fixed = ImageRenderer(content: Text("Continue").font(.system(size: 13)).dynamicTypeSize(.accessibility5).fixedSize())
    fixed.scale = 1
    print("fixed13pt size=accessibility5 heightPt=\(fixed.cgImage.map { CGFloat($0.height) } ?? -1)")
    let fixedDefault = ImageRenderer(content: Text("Continue").font(.system(size: 13)).fixedSize())
    fixedDefault.scale = 1
    print("fixed13pt size=default heightPt=\(fixedDefault.cgImage.map { CGFloat($0.height) } ?? -1)")
    // The alternative a Mac game can use: scale the point size itself.
    for multiplier in [1.0, 1.5, 2.0] as [CGFloat] {
        let r = ImageRenderer(content: Text("Continue").font(.system(size: 13 * multiplier)).fixedSize())
        r.scale = 1
        print("explicit size=\(13 * multiplier)pt heightPt=\(r.cgImage.map { CGFloat($0.height) } ?? -1)")
    }
}

MainActor.assumeIsolated { run() }
