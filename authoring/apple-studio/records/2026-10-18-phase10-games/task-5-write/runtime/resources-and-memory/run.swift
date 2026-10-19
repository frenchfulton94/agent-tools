import Metal

let device = MTLCreateSystemDefaultDevice()!
print("name", device.name, "metal4", device.supportsFamily(.metal4), "apple8", device.supportsFamily(.apple8), "apple9", device.supportsFamily(.apple9), "apple10", device.supportsFamily(.apple10))
if #available(macOS 26.4, *) { print("supportsPlacementSparse", device.supportsPlacementSparse) }
print("sparseTileSizeInBytes", device.sparseTileSizeInBytes, "for64", device.sparseTileSizeInBytes(sparsePageSize: .size64))
print("recommendedMaxWorkingSetSize", device.recommendedMaxWorkingSetSize, "hasUnifiedMemory", device.hasUnifiedMemory)

let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 4096, height: 4096, mipmapped: true)
td.storageMode = .private
td.usage = [.shaderRead]
td.placementSparsePageSize = .size64
let t = device.makeTexture(descriptor: td)
print("placement sparse texture from device:", t != nil, t.map { "tier=\($0.sparseTextureTier.rawValue) tail=\($0.firstMipmapInTail) mips=\($0.mipmapLevelCount) alloc=\($0.allocatedSize)" } ?? "nil")
print("tile size", device.sparseTileSize(textureType: .type2D, pixelFormat: .rgba8Unorm, sampleCount: 1, sparsePageSize: .size64))

let hd = MTLHeapDescriptor()
hd.type = .placement
hd.storageMode = .private
hd.size = 16 << 20
hd.maxCompatiblePlacementSparsePageSize = .size64
let heap = device.makeHeap(descriptor: hd)
print("placement heap", heap != nil)

// Does a residency set accept the placement heap?
let rd = MTLResidencySetDescriptor()
let set = try! device.makeResidencySet(descriptor: rd)
set.addAllocation(heap!)
set.commit()
print("set allocatedSize", set.allocatedSize, "count", set.allocationCount)

// Mip count: full chain for 256
let d2 = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 256, height: 256, mipmapped: true)
print("256 mipmapped levels", d2.mipmapLevelCount)
// allocatedSize vs length
let b = device.makeBuffer(length: 4, options: .storageModeShared)!
print("buffer length 4 allocatedSize", b.allocatedSize)
let sa = device.heapTextureSizeAndAlign(descriptor: d2)
print("heap size/align 256 rgba8 mipped", sa.size, sa.align)
