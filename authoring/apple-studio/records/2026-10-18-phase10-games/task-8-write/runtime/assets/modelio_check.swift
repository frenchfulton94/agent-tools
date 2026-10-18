// Runtime check for assets.md, Model I/O section.
// Run: swiftc -O modelio_check.swift -o modelio_check && ./modelio_check
// Which extensions Model I/O imports and exports on this OS.
import ModelIO

for ext in ["usd", "usda", "usdc", "usdz", "obj", "abc", "ply", "stl", "gltf", "glb", "fbx", "dae"] {
    print(ext.padding(toLength: 5, withPad: " ", startingAt: 0),
          "import=\(MDLAsset.canImportFileExtension(ext))",
          "export=\(MDLAsset.canExportFileExtension(ext))")
}
