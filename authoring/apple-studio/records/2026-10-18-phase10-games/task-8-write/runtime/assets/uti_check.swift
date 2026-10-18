// Runtime check for assets.md, "Custom asset and save types".
// Run: swift uti_check.swift
// Asks LaunchServices what type each game-asset extension resolves to on this Mac.
import UniformTypeIdentifiers

for ext in ["gltf", "glb", "ktx", "ktx2", "astc", "dds", "usdz", "usda", "aar", "obj"] {
    if let t = UTType(filenameExtension: ext) {
        print(ext.padding(toLength: 5, withPad: " ", startingAt: 0),
              t.identifier,
              "declared=\(t.isDeclared)",
              "dynamic=\(t.isDynamic)",
              "conformsToData=\(t.conforms(to: .data))")
    } else {
        print(ext, "nil")
    }
}

// An exported type the running process does not declare in its Info.plist.
let mine = UTType(exportedAs: "com.example.mygame.save", conformingTo: .data)
print("exportedAs (undeclared):", mine.identifier, "declared=\(mine.isDeclared)",
      "preferredFilenameExtension=\(mine.preferredFilenameExtension ?? "nil")")
