// swift-tools-version: 6.2
// Probe for direct-distribution.md: which architectures does Xcode build for a
// generic macOS destination at a given MACOSX_DEPLOYMENT_TARGET? See run.sh.
import PackageDescription

let package = Package(
    name: "ArchsProbe",
    platforms: [.macOS(.v26)],
    targets: [.executableTarget(name: "ArchsProbe")]
)
