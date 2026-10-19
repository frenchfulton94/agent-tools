> verified: 2026-10 against https://developer.apple.com/documentation/compression.md, https://developer.apple.com/documentation/compression/compression_algorithm.md, https://developer.apple.com/documentation/compression/compression_lzmesh.md, https://developer.apple.com/documentation/compression/compression_lzraven.md, https://developer.apple.com/documentation/compression/compression_lzfse.md, https://developer.apple.com/documentation/compression/compression_lzbitmap.md, https://developer.apple.com/documentation/compression/compression_lz4_raw.md, https://developer.apple.com/documentation/compression/compression_encode_buffer(_:_:_:_:_:_:).md, https://developer.apple.com/documentation/compression/compression_decode_buffer(_:_:_:_:_:_:).md, https://developer.apple.com/documentation/accelerate/compressing-and-decompressing-data-with-buffer-compression.md, https://developer.apple.com/documentation/accelerate/compressing-and-decompressing-files-with-stream-compression.md, https://developer.apple.com/documentation/accelerate/compressing-and-decompressing-data-with-input-and-output-filters.md, https://developer.apple.com/documentation/accelerate/decompressing-and-parsing-an-archived-string.md, https://developer.apple.com/documentation/accelerate/compressing-file-system-directories.md, https://developer.apple.com/documentation/accelerate/decompressing-and-extracting-an-archived-directory.md, https://developer.apple.com/documentation/modelio/mdlasset.md, https://developer.apple.com/documentation/modelio/mdlasset/init(url:vertexdescriptor:bufferallocator:preservetopology:error:)-510xi.md, https://developer.apple.com/documentation/modelio/mdlasset/canimportfileextension(_:).md, https://developer.apple.com/documentation/metalkit/conversion-functions.md, https://developer.apple.com/documentation/metalkit/mtkmodeliovertexdescriptorfrommetalwitherror.md, https://developer.apple.com/documentation/metalkit/mtkmesh/newmeshes(asset:device:).md, https://developer.apple.com/documentation/xcode/creating-build-rules-for-custom-file-types.md, https://developer.apple.com/documentation/accelerate/applying-geometric-transforms-to-images.md, https://developer.apple.com/documentation/accelerate/reducing-artifacts-with-custom-resampling-filters.md, https://developer.apple.com/documentation/accelerate/improving-the-quality-of-quantized-images-with-dithering.md, https://developer.apple.com/documentation/accelerate/adjusting-the-brightness-and-contrast-of-an-image.md, https://developer.apple.com/documentation/accelerate/converting-bitmap-data-between-core-graphics-images-and-vimage-buffers.md, https://developer.apple.com/documentation/accelerate/finding-the-sharpest-image-in-a-sequence-of-captured-images.md, https://developer.apple.com/documentation/accelerate/functions-that-add-an-alpha-channel-to-three-channel-buffers.md, https://developer.apple.com/documentation/uniformtypeidentifiers/defining-file-and-data-types-for-your-app.md, https://developer.apple.com/documentation/uniformtypeidentifiers/uttype-swift.struct/init(exportedas:conformingto:).md, https://developer.apple.com/documentation/uniformtypeidentifiers/uttype-swift.struct/init(importedas:conformingto:).md, https://developer.apple.com/documentation/uniformtypeidentifiers/uttype-swift.struct/init(filenameextension:conformingto:).md, https://developer.apple.com/documentation/backgroundassets.md, https://developer.apple.com/documentation/backgroundassets/creating-managed-asset-packs.md, https://developer.apple.com/documentation/backgroundassets/downloading-apple-hosted-asset-packs.md, https://developer.apple.com/documentation/backgroundassets/reducing-download-and-storage-demands-with-localized-asset-packs.md, https://developer.apple.com/documentation/backgroundassets/testing-asset-packs-locally.md, https://developer.apple.com/documentation/backgroundassets/configuring-an-unmanaged-background-assets-project.md, https://developer.apple.com/documentation/gamekit/improving-the-player-experience-for-games-with-large-downloads.md, https://developer.apple.com/documentation/foundation/optimizing-your-app-s-data-for-icloud-backup.md, https://developer.apple.com/documentation/xcode/addressing-watchdog-terminations.md
> typecheck: macos 26.0

# Assets: Compression, Model I/O, Texture Bakes, File Types, Background Assets

Contents:
- Compression: the API shape decides before the algorithm does
- Pak files: buffer-compressed chunks and a size table
- Streams and archives: LZFSE, AppleArchive, and the length you must keep
- Model I/O and USD: import at bake time
- Texture bakes: what this file owns and what apple-metal owns
- Custom asset and save types (UTIs)
- Background Assets: getting a large game onto the device
- Where downloaded and generated files live
- Classic pitfalls

Scope: how a game's content gets from source art to bytes the engine reads, and from
a server to the device. GPU-side decisions (texture formats, block compression,
lossless and lossy compression, mip streaming, the IO command queue) are
`apple-metal/references/resources-and-memory.md`. Save syncing is
`game-center-and-online.md` (`## Saves across devices`). Signing and Developer ID
distribution are `app-release`; `app-release/references/direct-distribution.md`
covers shipping outside the App Store.

All measured numbers below come from one Mac (Apple M4 Pro, macOS 27.0.1, Xcode 27.1)
and are logged in the phase record's `task-8-write/runtime/assets/runs.txt`.

## Compression: the API shape decides before the algorithm does

The Compression library has two APIs. The **buffer** API (`compression_encode_buffer`,
`compression_decode_buffer`) handles one whole block in one call. The **stream** API
(`compression_stream_*`, or Swift's `InputFilter` / `OutputFilter`) works through data in
steps. The two newest Apple codecs exist **only in the buffer API**, so choose the API
first.

| Algorithm | Stream API | OS | Use it for |
|---|---|---|---|
| `COMPRESSION_LZMESH` | no | macOS / iOS 27 | Apple-only data that you hold whole. It replaces LZFSE and zlib. |
| `COMPRESSION_LZRAVEN` | no | macOS / iOS 27 | Apple-only data where size matters most. It replaces LZMA. |
| `COMPRESSION_LZFSE` | yes | all | Apple-only data that you stream, and any data that a 26 device must decode. |
| `COMPRESSION_LZBITMAP` | no | macOS 12 / iOS 15 | The fastest Apple decode at a ratio between LZ4 and LZMESH. |
| `COMPRESSION_LZ4` / `_LZ4_RAW` | LZ4 yes, RAW no | all | Speed first. Use RAW only when a non-Apple LZ4 decoder reads the bytes. |
| `COMPRESSION_ZLIB` | yes | all | Interoperability. The output is raw DEFLATE (RFC 1951) at level 5. |
| `COMPRESSION_LZMA` | yes | all | Interoperability when size matters most. On Apple-only paths that can require OS 27, LZRAVEN is better. |

- **Buffer-only is enforced.** `compression_stream_init` returned
  `COMPRESSION_STATUS_ERROR` for LZMESH, LZRAVEN, LZBITMAP and LZ4_RAW, for both encode
  and decode, and `COMPRESSION_STATUS_OK` for the other five (runtime-checked).
- **The compiler does not gate LZMESH or LZRAVEN.** In `compression.h`, the OS 27
  availability is a comment on each enum value, not an availability attribute. Swift and
  clang both compiled `COMPRESSION_LZMESH` and `COMPRESSION_LZRAVEN` at a 26.0 deployment
  target with no warning (checked). Nothing stops that code from running on a 26 device,
  where the header says the algorithms do not exist. Gate them with `#available` yourself.
- **The Swift wrappers do not have these codecs.** Swift's `Algorithm` enum (used by
  `InputFilter` and `OutputFilter`) has `.lzfse`, `.zlib`, `.lz4`, `.lzma`, `.lzbitmap`
  and `.brotli`. `NSData.CompressionAlgorithm` has the first four. `MTLIOCompressionMethod`
  has zlib, LZFSE, LZ4, LZMA and LZBitmap. AppleArchive's `ArchiveCompression` adds
  `.lzraven` (OS 27) but has no LZMESH. To use LZMESH from Swift, call the C buffer
  functions.
- **Docs that disagree.** The stream sample and the filters article still name LZFSE as
  the Apple-only choice. They are right about streams. For a whole buffer on OS 27, the
  symbol pages and the header prefer LZMESH. The `compression_algorithm` overview says
  LZRAVEN is "an order of magnitude slower". The header says that about LZMA, and the
  LZRAVEN page says LZRAVEN decodes 3x faster than LZMA. Measured, both are partly right:

| Payload | Metric | LZ4 | LZBITMAP | LZFSE | LZMESH | ZLIB | LZMA | LZRAVEN |
|---|---|---|---|---|---|---|---|---|
| Mach-O binary, 7.4 MB | ratio | 2.02 | 2.99 | 2.86 | 3.58 | 3.09 | 4.67 | 5.21 |
| | encode MB/s | 1575 | 489 | 201 | 417 | 86 | 9.7 | 12.1 |
| | decode MB/s | 6528 | 5041 | 2277 | 2404 | 734 | 146 | 395 |
| SDK headers (text), 0.96 MB | ratio | 3.48 | 4.11 | 6.07 | 6.28 | 5.74 | 8.15 | 8.07 |
| | encode MB/s | 993 | 505 | 205 | 529 | 117 | 9.5 | 11.3 |
| | decode MB/s | 4440 | 6513 | 3363 | 3103 | 1237 | 357 | 946 |

  These are single-thread, best-of-3 timings with a reused scratch buffer. LZRAVEN
  encodes at about LZMA's speed, which suits a bake step but not a runtime save. It
  decodes 2.6 to 2.7 times faster than LZMA. LZMESH decodes within 10% of LZFSE's speed,
  compresses better, and encodes 2 to 2.6 times faster. Measure your own content before
  you pick a codec from a table.

## Pak files: buffer-compressed chunks and a size table

Apple recommends the buffer API for inputs under 8 MB uncompressed or 1 MB compressed
(the Compression framework page). A pak made of chunks of that size, each compressed
independently, supports random access, lets worker threads decompress in parallel, and
can use LZMESH. Keep a table of chunks:

```swift
import Compression
import Foundation

/// One row of a pak's chunk table. The codec does not record the decoded size, so the table must.
struct ChunkRecord {
    var offset: UInt64
    var storedSize: UInt32
    var rawSize: UInt32
    var algorithm: UInt32     // compression_algorithm.rawValue; 0 = stored uncompressed
}

/// The codec for data this device writes and reads itself (saves, caches).
func localChunkAlgorithm() -> compression_algorithm {
    if #available(macOS 27, iOS 27, *) {
        return COMPRESSION_LZMESH       // buffer API only
    }
    return COMPRESSION_LZFSE
}

func encodeChunk(_ raw: [UInt8], using algorithm: compression_algorithm) -> (bytes: [UInt8], algorithm: UInt32) {
    var out = [UInt8](repeating: 0, count: raw.count)
    let n = compression_encode_buffer(&out, out.count, raw, raw.count, nil, algorithm)
    if n == 0 { return (raw, 0) }        // didn't shrink, or failed: store it raw
    return (Array(out.prefix(n)), algorithm.rawValue)
}

func decodeChunk(_ stored: [UInt8], _ record: ChunkRecord) throws -> [UInt8] {
    guard record.algorithm != 0 else { return stored }
    var out = [UInt8](repeating: 0, count: Int(record.rawSize))
    let n = compression_decode_buffer(&out, out.count, stored, stored.count, nil,
                                      compression_algorithm(rawValue: record.algorithm))
    guard n == out.count else { throw CocoaError(.fileReadCorruptFile) }
    return out
}
```

- **Choose the codec for shipped content by your deployment target, not by the build
  machine.** Paks are baked on a Mac running 27. If the game supports OS 26, those paks
  must use LZFSE, or you must ship a second set. A 26 device cannot decode LZMESH. The
  `#available` check above applies only to data the device both writes and reads. The
  per-chunk algorithm field lets one reader handle both kinds of pak.
- **`compression_encode_buffer` returns 0** when the output does not fit or encoding
  fails. With a destination as large as the input, every algorithm returned 0 for 16
  incompressible bytes (runtime-checked). Store such chunks raw, as above.
- **The return value of `compression_decode_buffer` does not show truncation.** The
  symbol page and the header both say that when the destination is too small, the
  function fills it and returns its size. The buffer-compression article says it returns
  zero. The SDK is correct, and the behaviour differs by codec. With a destination 100
  bytes too small, LZ4, LZ4_RAW, zlib, LZFSE, LZBITMAP and LZMESH returned the
  destination size, and LZMA, Brotli and LZRAVEN returned 0 (runtime-checked). Size the
  destination from your table and compare the result with that size. Neither check
  detects corrupt data. Hash anything you downloaded or anything a player can edit.
- **Decompressing a whole file on the CPU before you upload it to the GPU is often the
  wrong design.** `MTLIOCommandQueue` reads compressed pack files straight into buffers
  and textures. Its codecs are the `MTLIOCompressionMethod` list above, which does not
  include LZMESH. See `apple-metal/references/resources-and-memory.md`
  (`## Streaming from disk: the IO command queue`).

## Streams and archives: LZFSE, AppleArchive, and the length you must keep

Use the stream API when the data does not fit in memory, arrives over time, or is too
large for one buffer call: a level downloaded over a socket, or a large save written
as the game produces it. Use LZFSE for Apple-only streams. `OutputFilter` hands you
each compressed or decompressed page through a closure. `InputFilter` pulls pages from
a closure that you supply. Either class can compress or decompress. Smaller pages give
more frequent progress reports, and larger pages take fewer steps.

For a directory of files, or one file plus metadata, use **AppleArchive** instead of a
custom container. `ArchiveStream.writeDirectoryContents(archiveFrom:keySet:)` packs a
folder (the full signature also takes an entry filter, flags and a thread count).
`extractStream(extractingTo:flags:)` together with `ArchiveStream.process(readingFrom:writingTo:)`
unpacks one. `ArchiveByteStream.decompressionStream(readingFrom:)` takes no algorithm
argument: one reader opened both the `.lzfse` and the `.lzraven` archives below
(runtime-checked).

**Apple's two read samples over-read their buffers.** The AppleArchive sample builds its
result with `String(cString:)` from a buffer of exactly `byteCount` bytes, with no NUL
terminator. The buffer-compression sample does the same with an uninitialized 8 MB
buffer. Both read past the data, and both cut binary data at its first zero byte. Decode
using the length that the archive header gives you:

```swift
import AppleArchive
import System

/// Reads the DAT blob of the first entry in an .aar, sized from its own header.
func readSaveBlob(from path: FilePath) throws -> [UInt8] {
    guard let file = ArchiveByteStream.fileStream(path: path, mode: .readOnly, options: [],
                                                  permissions: FilePermissions(rawValue: 0o644)),
          let decompress = ArchiveByteStream.decompressionStream(readingFrom: file),
          let decode = ArchiveStream.decodeStream(readingFrom: decompress)
    else { throw Errno.ioError }
    defer { try? decode.close(); try? decompress.close(); try? file.close() }

    guard let header = try decode.readHeader(),
          case .blob(_, let size, _)? = header.field(forKey: ArchiveHeader.FieldKey("DAT"))
    else { throw Errno.badFileTypeOrFormat }
    var bytes = [UInt8](repeating: 0, count: Int(size))
    try bytes.withUnsafeMutableBytes {
        try decode.readBlob(key: ArchiveHeader.FieldKey("DAT"), into: $0)
    }
    return bytes   // text: String(decoding: bytes, as: UTF8.self), never String(cString:)
}
```

To write an archive, pass `.lzfse`, or `.lzraven` on OS 27, to
`ArchiveByteStream.compressionStream(using:writingTo:)`. The samples write to
Downloads, and on macOS that needs a file-access entitlement. Saves and unpacked
content belong in the app container, which needs none.

## Model I/O and USD: import at bake time

Model I/O loads USD (`.usd`, `.usda`, `.usdc`, `.usdz`), OBJ, Alembic, PLY and STL. On
macOS 27, `MDLAsset.canImportFileExtension(_:)` returned false for `gltf`, `glb`, `fbx`
and `dae`, and `canExportFileExtension(_:)` returned false for `usdz`
(runtime-checked). A glTF pipeline needs its own importer or a conversion to USD at
bake time.

Parsing a scene format at load time costs launch time on every run. On iPhone and iPad,
processing a 3D model on the main thread is also one of Apple's named causes of watchdog
terminations. Import in a build tool or at first launch, write a packed engine format, and load that
format. When you do import with Model I/O, load straight into the layout your pipeline
uses:

```swift
import MetalKit
import ModelIO

/// Position, normal, UV interleaved in buffer 0, the layout the render pipeline declares.
func importModel(at url: URL, device: any MTLDevice) throws -> [MTKMesh] {
    let layout = MTLVertexDescriptor()
    layout.attributes[0].format = .float3; layout.attributes[0].offset = 0
    layout.attributes[1].format = .float3; layout.attributes[1].offset = 12
    layout.attributes[2].format = .float2; layout.attributes[2].offset = 24
    for i in 0..<3 { layout.attributes[i].bufferIndex = 0 }
    layout.layouts[0].stride = 32

    let modelIO = try MTKModelIOVertexDescriptorFromMetalWithError(layout)
    // The conversion copies formats, offsets and strides but no names. Model I/O fills only named attributes.
    let names = [MDLVertexAttributePosition, MDLVertexAttributeNormal, MDLVertexAttributeTextureCoordinate]
    for (i, name) in names.enumerated() {
        (modelIO.attributes[i] as? MDLVertexAttribute)?.name = name
    }
    var error: NSError?
    let asset = MDLAsset(url: url, vertexDescriptor: modelIO,
                         bufferAllocator: MTKMeshBufferAllocator(device: device),
                         preserveTopology: false, error: &error)
    if let error { throw error }
    asset.loadTextures()
    return try MTKMesh.newMeshes(asset: asset, device: device).metalKitMeshes
}
```

- **Use the `WithError` converters.** `MTKModelIOVertexDescriptorFromMetal` and
  `MTKMetalVertexDescriptorFromModelIO` convert descriptors only partly, and they do not
  report what failed. The `WithError` forms report it. Their documentation pages show the
  C form with an `NSError` pointer, but the MetalKit Swift overlay imports both as
  throwing functions, so call them with `try`.
- **Pass `MTKMeshBufferAllocator`.** The `MTKMesh` header says that `MTKMesh` raises an
  exception if Model I/O did not allocate the mesh's buffers through that allocator.
  With `preserveTopology: false`, Model I/O converts the index data to triangles.
- **Draw every submesh at its own offset.** One `MTKMesh` holds one vertex pool and one
  `MTKSubmesh` per material group. The submeshes often share one `MTLBuffer`, each at its
  own `offset`. A Metal 4 draw takes a GPU address, so add the offset to the address:

```swift
import Metal
import MetalKit

func drawSubmeshes(of mesh: MTKMesh, with encoder: any MTL4RenderCommandEncoder) {
    for submesh in mesh.submeshes {
        let index = submesh.indexBuffer
        let indexSize = submesh.indexType == .uint16 ? 2 : 4
        encoder.drawIndexedPrimitives(primitiveType: submesh.primitiveType,
                                      indexCount: submesh.indexCount,
                                      indexType: submesh.indexType,
                                      indexBuffer: index.buffer.gpuAddress + UInt64(index.offset),
                                      indexBufferLength: submesh.indexCount * indexSize)
    }
}
```

  Vertex buffers bind the same way (address plus offset) through the argument table,
  and every buffer must be in a residency set. See
  `apple-metal/references/command-model.md` (`## Argument tables`, `## Residency`).
- Model I/O loads USD textures as linear `.rgba8Unorm`, base color included. The fix is
  in `apple-metal/references/resources-and-memory.md` (`## Texture views and view pools`).
- Model I/O can also generate content at bake time: normals and tangent bases on
  `MDLMesh`, light probes from `MDLAsset.placeLightProbes(withDensity:heuristic:using:)`,
  and procedural textures such as `MDLSkyCubeTexture`. Bake their output into files and
  ship the files. Do not regenerate them per frame or at every launch.

## Texture bakes: what this file owns and what apple-metal owns

Which format a texture uses (ASTC for iPhone and iPad, BC on the Mac, family gates,
lossy compression, mip budgets) belongs to
`apple-metal/references/resources-and-memory.md` (`## Texture formats and compression`).
This file covers the bake step that produces those files.

**Bake with Xcode's `TextureConverter`, from a build rule.** Xcode 27.1 includes
`xcrun TextureConverter` (version 5.0). Its `--help` lists ASTC (LDR and HDR), BC1 to BC7,
ETC2 and EAC encoders. It reads PNG, EXR, HEIC, KTX, KTX2 and other formats, and writes
KTX, KTX2, DDS and EXR. It can generate mips with a choice of filter, build cube maps,
convert sRGB gamma, flip images, and swizzle channels for normal maps. Run it from an
Xcode build rule, not from a Run Script phase. A build rule runs one task per file in
parallel and rebuilds only when the source is newer than the declared outputs. Write the
output to `$(DERIVED_FILE_DIR)`:

```sh
xcrun TextureConverter --compression_format=ASTC4x4 --compression_quality=Production \
    --srgb_format --output="$DERIVED_FILE_DIR/$INPUT_FILE_BASE.ktx" "$SCRIPT_INPUT_FILE"
```

Choose the container with care. `MTKTextureLoader` treats KTX and KTX2 differently
(runtime-checked, with files that the command above made at `--compression_quality=Normal`
instead of `Production`):

| File | `newTexture(URL:options:)` returned |
|---|---|
| ASTC 4x4 `.ktx`, 9 mips | `.astc_4x4_ldr`, 9 mips: the file as written |
| ASTC 4x4 `.ktx` with `--srgb_format`, or loaded with `.SRGB: true` | `.astc_4x4_srgb`, 9 mips |
| ASTC 4x4 or BC7 `.ktx2`, 9 mips | `.bgra8Unorm_srgb`, **1 mip**: decoded to RGBA8, no error |
| any `.ktx` with `.origin: .bottomLeft` | error: "Vertical flip is not supported for block texture formats" |

- **A KTX2 file loses its compression and its mips in `MTKTextureLoader`, with no
  warning.** Either ship KTX (version 1) to `MTKTextureLoader`, or parse KTX2 yourself
  and upload the blocks yourself, as in `apple-metal/references/resources-and-memory.md`
  (`## Uploading in Metal 4: copies live on the compute encoder`).
- **Flip at bake time, not at load time.** `.origin` cannot flip block-compressed data.
  The header says so, and the loader returns an error. If your UV convention needs a
  flip, pass `--flip_y` to the converter.

**vImage handles CPU-side preparation before the encoder runs.** Some of its rules are
counterintuitive:

- **Unpremultiply before you scale.** Apple's geometric-transform article says that
  premultiplied input can show artifacts in high-frequency regions. Call
  `vImageUnpremultiplyData_ARGB8888`, resample, then call
  `vImagePremultiplyData_ARGB8888`. This contradicts the usual advice to always filter
  premultiplied data. It applies to vImage's Lanczos kernels, which ring near hard edges.
- **`kvImageHighQualityResampling` does not remove ringing.** It switches the kernel from
  Lanczos-3 to Lanczos-5. For line art, UI glyphs and pixel art, build a custom linear
  filter with `vImageNewResamplingFilterForFunctionUsingBuffer` and apply it in two 1D
  shears through an intermediate buffer. The geometry functions never work in place.
- **Linearize sRGB before you scale or build mips.** Apple says convolution and scaling
  give the best results on linear data. Convert, process, then re-encode. Normal maps and
  masks are already linear.
- **Use `kvImageConvert_DitherOrderedReproducible` when you reduce bit depth in a build.**
  It uses the same blue-noise offset on every call, so a rebuild produces identical
  bytes and content hashes stay stable. `kvImageConvert_DitherOrdered` does not.
- **Check the row stride.** vImage pads rows for speed: a 10-pixel, 8-bit buffer gets 16
  bytes per row. The padding is uninitialized. Pass `rowBytes` to every upload, and
  never hash or analyze the whole allocation.
- **Gray conversion uses Rec. 601 weights.** Converting to a gray `vImage_CGImageFormat`
  applies 0.299, 0.587 and 0.114. For Rec. 709 weights, use a matrix multiply.
- **Three-channel art needs a fourth channel for a normal 2D texture.** OS 27 adds
  `MTLPixelFormat.rgb8Unorm` and the other three-channel formats (RGB16 and RGB32), but
  the header limits them all to `textureType == .typeTextureBuffer` without `.shaderWrite`. A
  sampled, mipmapped 2D texture still needs RGBA. Use `vImageConvert_RGB888toRGBA8888`,
  which takes a constant alpha or a planar alpha buffer.

## Custom asset and save types (UTIs)

The system routes files to your app by type identifier. Declare a type for each file
format that your game or editor opens, saves, or receives by drag and drop.

- **Formats you own** (saves, levels, mod packages) go under
  `UTExportedTypeDeclarations`. Use a reverse-DNS identifier that does not start with
  `public`, `dyn` or `com.apple`. Conform to `public.data` for a single file, or to
  `com.apple.package` for a directory shown as one file. Without one of the two, Finder
  and Files cannot classify the file. Add `public.content` so players can send the file
  with AirDrop.
- **Formats someone else owns** go under `UTImportedTypeDeclarations`, with the owner's
  identifier, not one you invent. If both an exported and an imported declaration exist
  for one identifier, the exported declaration wins.
- **There is no `UTType` constant for glTF, KTX, KTX2, ASTC or DDS.** `UTCoreTypes.h` has
  USD, USDZ, `.realityFile`, `.sceneKitScene` and `.appleArchive`, and none of these.
  The identifiers do resolve on macOS 27, though (runtime-checked). CoreTypes imports
  `org.khronos.gltf` (it conforms to `public.3d-content` and `public.json`) and
  `org.khronos.glb`. Preview exports `org.khronos.ktx`, `org.khronos.ktx2`,
  `org.khronos.astc` and `com.microsoft.dds`, each conforming to `public.image`. If your
  tool opens these formats, import those exact identifiers. Do not count on another
  bundle declaring them on iPhone or iPad, which this phase did not check.

```plist
<key>UTExportedTypeDeclarations</key>
<array>
    <dict>
        <key>UTTypeIdentifier</key>
        <string>com.example.mygame.save</string>
        <key>UTTypeConformsTo</key>
        <array>
            <string>com.apple.package</string>
            <string>public.content</string>
        </array>
        <key>UTTypeDescription</key>
        <string>MyGame Save</string>
        <key>UTTypeTagSpecification</key>
        <dict>
            <key>public.filename-extension</key>
            <array><string>mygamesave</string></array>
        </dict>
    </dict>
</array>
<key>UTImportedTypeDeclarations</key>
<array>
    <dict>
        <key>UTTypeIdentifier</key>
        <string>org.khronos.ktx2</string>
        <key>UTTypeConformsTo</key>
        <array><string>public.image</string></array>
        <key>UTTypeDescription</key>
        <string>KTX2 texture</string>
        <key>UTTypeTagSpecification</key>
        <dict>
            <key>public.filename-extension</key>
            <array><string>ktx2</string></array>
        </dict>
    </dict>
</array>
```

```swift
import UniformTypeIdentifiers

extension UTType {
    /// Must match the UTExportedTypeDeclarations entry.
    static let myGameSave = UTType(exportedAs: "com.example.mygame.save", conformingTo: .package)
    /// Khronos owns this one: reuse its identifier and declare it as imported.
    static let ktx2Texture = UTType(importedAs: "org.khronos.ktx2", conformingTo: .image)
}
```

- **`isDeclared` does not prove the plist is right.** In a process with no plist
  entry, `UTType(exportedAs:)` returned a type with `isDeclared == true` and
  `preferredFilenameExtension == nil` (runtime-checked). Test the extension, for
  example `UTType(filenameExtension: "mygamesave") == .myGameSave`.
- `UTType(filenameExtension:conformingTo:)` can return a dynamic `dyn.` type when nothing
  is declared for the extension. A dynamic type is a sign that a declaration is missing.
- A save that may sync through iCloud works best as a versioned file package; the sync
  mechanics are in `game-center-and-online.md`. A Mac level editor that wants Finder
  integration also lists the type under Document Types. General AppKit document
  architecture is `apple-macos`.

## Background Assets: getting a large game onto the device

**Gates. Where the SDK and the docs disagree, the SDK is correct.** The framework page
lists iOS 16 and macOS 13, which is when the original unmanaged API arrived. The
managed Swift API (`AssetPackManager`, `AssetPack`, `ManagedDownloaderExtension`)
arrived in iOS, macOS, tvOS and visionOS 26 and is unavailable on watchOS
(`BackgroundAssets.swiftinterface`). On-demand resources (`NSBundleResourceRequest`,
`Bundle.setPreservationPriority(_:forTags:)`) are **unavailable on macOS** and
**deprecated in iOS and tvOS 27** with the message "Use Background Assets instead"
(`NSBundle.h`). Apple's large-downloads article for GameKit still recommends on-demand
resources. Do not start new work on them.

**Bundle-size limits apply to iPhone, iPad and Apple TV only.** That article gives 2 GB
for an iOS or iPadOS 17-or-earlier deployment target, and 4 GB for 18 and any tvOS. It gives
on-demand-resource limits too. It states nothing for the Mac, so do not apply those
figures to a Mac build.

Choose a mode:

| Mode | Who hosts | Distribution | You write |
|---|---|---|---|
| Apple-hosted, managed | App Store Connect, up to 200 GB compressed | App Store and TestFlight only | Manifests and the app-side calls. The extension template works as it is |
| Self-hosted, managed | Your server or CDN, with a download manifest (`ba-package download-manifest`) | Not limited to the App Store by the pages read | The same app code. The system still schedules downloads, applies updates and handles compression |
| Self-hosted, unmanaged | Your server | Not limited to the App Store by the pages read | `BADownloaderExtension`, your own manifest format, `BADownloadManager` |
| Background `URLSession` | Your server | Any | Everything else, and the content cannot join the install progress bar |

Apple hosting needs the App Store or TestFlight, so a Mac game distributed with Developer
ID must host its own packs. This phase did not test Background Assets in a Developer ID
build.

**Project setup.** Add a Background Download extension target and choose its type in the
template. Put the app and the extension in one app group. An Apple-hosted app needs
exactly three Info.plist keys: `BAAppGroupID`, `BAHasManagedAssetPacks` = YES and
`BAUsesAppleHosting` = YES, with no other `BA` key. An unmanaged Mac app also needs App
Sandbox on both targets. Its size keys come in two kinds. `BADownloadAllowance` and
`BAEssentialDownloadAllowance` are compressed download totals. `BAEssentialMaxInstallSize`
and `BAMaxInstallSize` are uncompressed totals on disk.

**Packaging and testing** use command-line tools that ship with Xcode (`ba-package` 2.0 in
Xcode 27.1):

```sh
xcrun ba-package template -o Manifest.json          # assetPackID, downloadPolicy, fileSelectors, platforms
xcrun ba-package evaluate Manifest.json              # validates and lists the files the selectors match
xcrun ba-package Manifest.json -o Tutorial.aar       # paths are relative to the current directory
xcrun ba-package convert steam_build.vdf --asset-pack-id Levels --on-demand   # a Steam build script to a manifest
xcrun ba-serve --host localhost Tutorial.aar         # local HTTPS mock server
xcrun ba-serve url-override https://localhost        # macOS: point Xcode-run builds at it
```

The download policies are `essential` (part of the install, and counted in its
progress), `prefetch` (starts during install and finishes in the background), and
`onDemand` (only when you ask). Pick `essential` with `installationEventTypes:
["firstInstallation"]` for a tutorial, so updates do not fetch it again. Every download
is HTTPS, so local testing needs a root CA and a leaf certificate made in Keychain
Access. On iPhone and iPad the override is in Settings > Developer. The testing page
describes the override for builds that you build and run from Xcode.

**App code.** `ensureLocalAvailability` returns quickly when the pack is present. Call it
even for essential packs, because a network failure can leave an essential pack missing.
Two of the article's calls have newer spellings in the SDK: `assetPack(withID:)` is
deprecated in 27 in favour of the manifest, and the one-argument
`ensureLocalAvailability(of:)` is deprecated in 26.4. With a 26.0 floor, you need all
three paths:

```swift
import BackgroundAssets

func ensurePack(_ id: String) async throws {
    let manager = AssetPackManager.shared
    if #available(macOS 27, iOS 27, *) {
        guard let pack = try await manager.manifest.assetPack(withID: id) else {
            throw ManagedBackgroundAssetsError.assetPackNotFound(withID: id)
        }
        try await manager.ensureLocalAvailability(of: pack, requireLatestVersion: false)
    } else if #available(macOS 26.4, iOS 26.4, *) {
        let pack = try await manager.assetPack(withID: id)                    // deprecated in 27
        try await manager.ensureLocalAvailability(of: pack, requireLatestVersion: false)
    } else {
        let pack = try await manager.assetPack(withID: id)
        try await manager.ensureLocalAvailability(of: pack)                   // deprecated in 26.4
    }
}

/// The article's switch omits the leading dots and `@unknown default`, so it does not compile.
func trackPack(_ id: String, progress report: @Sendable (Double) -> Void) async throws {
    for await update in AssetPackManager.shared.statusUpdates(forAssetPackWithID: id) {
        switch update {
        case .began, .paused: continue
        case .downloading(_, let progress): report(progress.fractionCompleted)
        case .finished: return
        case .failed(_, let error): throw error
        @unknown default: continue      // the enum is not frozen; Swift 6 requires this
        }
    }
}
```

- **Read files by path, without copying them.** All packs merge into one namespace that
  recreates the folder where you ran `ba-package`. `contents(at:)` returns `Data` that is
  memory-mapped by default (`.mappedIfSafe`). `descriptor(for:)` returns a
  `FileDescriptor` that you must close. To cancel a download, call `Progress.cancel()`.
- **Packs stay until you remove them.** The system updates downloaded packs in the
  background and never deletes them while the app is installed. Call
  `remove(assetPackWithID:)` when a tutorial or level is done, and call
  `ensureLocalAvailability` again to bring it back. Other calls on OS 26.4:
  `status(relativeTo:)` replaces `status(ofAssetPackWithID:)`, and
  `assetPackIsAvailableLocally(withID:)` is synchronous. `checkForUpdates()` returns
  the IDs being updated and the IDs removed.
- **On OS 27, fetch several packs in one batch.** `ensureLocalAvailability(of:requireLatestVersions:)`
  takes a set and downloads it in one batch, which Apple says is faster than one call
  per pack. It throws `AssetPackManager.LocalAvailabilityError` with `successes` and
  `failures`. Localized packs, described for Apple-hosted packs, carry a `language` key
  limited to language, region and script, such as `ja` or `zh-Hant`. Setting
  `resolvedLanguage` for an in-game language picker downloads nothing. Call
  `reconcilePreferredLanguages()` afterwards. When several language packs share a path,
  read it with the `asLocalizedFor:` variants.
- Apple allows the framework only for downloading the app's own content, with no user or
  device identification and no advertising measurement.

## Where downloaded and generated files live

- **Content you can rebuild** (transcoded textures, caches, unpacked copies of
  downloads) goes in `Library/Caches` or `tmp`. iCloud Backup skips both, and the system
  may purge them. For unmanaged downloads, Apple's GameKit article says to extract into
  a `Caches` subfolder, never into `Documents`, and then delete the downloaded file.
- **Content you can download again but must keep** goes in a directory under `Library`
  named for your bundle ID, with `isExcludedFromBackup = true`. Set the flag again after
  each save, because some file operations reset resource values. The flag is advisory.
- **Save games are player data.** Never exclude them from backup, and never put them in
  a purgeable directory.
- If a failed essential download is skipped, the install continues without it. Schedule
  it again with `copyAsNonEssential()` and `BADownloadManager.shared.scheduleDownload(_:)`.

## Classic pitfalls

1. LZMESH chosen through a runtime `#available` for paks baked on a 27 Mac. The paks
   ship to 26 devices that cannot decode them.
2. LZMESH or LZRAVEN passed to `compression_stream_init`, `InputFilter` or
   `MTLIOCompressionMethod`. They are buffer-only, or missing from those APIs.
3. `compression_decode_buffer`'s return value treated as proof that the data was
   decoded completely.
4. `String(cString:)` over a decoded buffer, copied from Apple's samples.
5. KTX2 loaded through `MTKTextureLoader`, which silently decodes it to RGBA8 with one
   mip.
6. A Model I/O vertex descriptor converted from Metal without names, so normals and UVs
   are not loaded, or only `submeshes.first` drawn.
7. A made-up `com.mygame.gltf` identifier instead of an import of `org.khronos.gltf`.
8. On-demand resources in new code, or the iOS bundle-size limits applied to a Mac build.
9. The Background Assets article's samples pasted as printed. The switch does not
   compile, and two of its calls are deprecated.
