// Runtime check for assets.md, AppleArchive section.
// Run: swiftc -O archive_check.swift -o archive_check && ./archive_check <scratch-dir>
// 1. Writes one DAT blob with .lzfse and (OS 27) .lzraven, reads it back with a length-based decode.
// 2. Shows that decompressionStream(readingFrom:) needs no algorithm argument.
import AppleArchive
import Foundation
import System

func write(_ bytes: [UInt8], to path: FilePath, using algorithm: ArchiveCompression) throws {
    guard let file = ArchiveByteStream.fileStream(path: path, mode: .writeOnly,
                                                  options: [.create, .truncate],
                                                  permissions: FilePermissions(rawValue: 0o644)),
          let compress = ArchiveByteStream.compressionStream(using: algorithm, writingTo: file),
          let encode = ArchiveStream.encodeStream(writingTo: compress)
    else { throw Errno.ioError }
    defer { try? encode.close(); try? compress.close(); try? file.close() }
    let header = ArchiveHeader()
    header.append(.string(key: ArchiveHeader.FieldKey("PAT"), value: "save.bin"))
    header.append(.uint(key: ArchiveHeader.FieldKey("TYP"),
                        value: UInt64(ArchiveHeader.EntryType.regularFile.rawValue)))
    header.append(.blob(key: ArchiveHeader.FieldKey("DAT"), size: UInt64(bytes.count)))
    try encode.writeHeader(header)
    try bytes.withUnsafeBytes { try encode.writeBlob(key: ArchiveHeader.FieldKey("DAT"), from: $0) }
}

func read(from path: FilePath) throws -> [UInt8] {
    guard let file = ArchiveByteStream.fileStream(path: path, mode: .readOnly, options: [],
                                                  permissions: FilePermissions(rawValue: 0o644)),
          let decompress = ArchiveByteStream.decompressionStream(readingFrom: file),
          let decode = ArchiveStream.decodeStream(readingFrom: decompress)
    else { throw Errno.ioError }
    defer { try? decode.close(); try? decompress.close(); try? file.close() }
    guard let header = try decode.readHeader(),
          case .blob(_, let size, _)? = header.field(forKey: ArchiveHeader.FieldKey("DAT"))
    else { throw Errno.badFileTypeOrFormat }
    var out = [UInt8](repeating: 0, count: Int(size))
    try out.withUnsafeMutableBytes { try decode.readBlob(key: ArchiveHeader.FieldKey("DAT"), into: $0) }
    return out
}

let dir = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : NSTemporaryDirectory()
// A payload with no NUL terminator and an embedded NUL, so String(cString:) would be wrong twice.
var payload = Array("level=3;hp=87;".utf8) + [0] + Array("inventory=sword,shield".utf8)
payload += [UInt8](repeating: 0x41, count: 4096)

var algorithms: [(String, ArchiveCompression)] = [("lzfse", .lzfse)]
if #available(macOS 27, *) { algorithms.append(("lzraven", .lzraven)) }
for (name, alg) in algorithms {
    let path = FilePath(dir + "/check-\(name).aar")
    do {
        try write(payload, to: path, using: alg)
        let back = try read(from: path)
        let size = (try? FileManager.default.attributesOfItem(atPath: path.string)[.size]) as? Int ?? -1
        print(name, "archive bytes=\(size)", "roundtrip=\(back == payload)", "count=\(back.count)",
              "decoded-with-length prefix=\(String(decoding: back.prefix(14), as: UTF8.self))")
    } catch {
        print(name, "ERROR", error)
    }
}
