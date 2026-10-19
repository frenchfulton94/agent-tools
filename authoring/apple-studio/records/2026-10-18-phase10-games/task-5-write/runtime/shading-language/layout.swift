struct Light { var position: SIMD3<Float>; var color: SIMD3<Float>; var intensity: Float }
struct Packed { var x: Float; var y: Float; var z: Float }
print(MemoryLayout<SIMD3<Float>>.size, MemoryLayout<SIMD3<Float>>.stride, MemoryLayout<Light>.size, MemoryLayout<Light>.stride, MemoryLayout<Packed>.stride)
