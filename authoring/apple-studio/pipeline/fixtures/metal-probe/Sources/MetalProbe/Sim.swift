import os

/// `sim`: a CPU-only simulation loop for CPU profiling (Task 9, R4). Each loop
/// iteration is one `frame` interval that holds one `tick` interval. `--slow`
/// routes every tick through `plantedSlowStep`, so a profiler must find it as
/// the heaviest symbol under `tick`.
let probeSignposter = OSSignposter(subsystem: "dev.frenchfultonjr.apple-studio.metal-probe",
                                   category: .pointsOfInterest)

struct Particle {
    var position: SIMD2<Float>
    var velocity: SIMD2<Float>
}

/// The normal tick: integrate and wrap. Linear in the particle count.
@inline(never)
func simulationStep(_ particles: inout [Particle], dt: Float) {
    for i in particles.indices {
        particles[i].position += particles[i].velocity * dt
        particles[i].position -= particles[i].position.rounded(.down)
    }
}

/// The planted hot spot: the same integration plus an all-pairs repulsion
/// pass. It is quadratic in the particle count, so it dominates every tick.
@inline(never)
func plantedSlowStep(_ particles: inout [Particle], dt: Float) {
    let n = particles.count
    for i in 0..<n {
        var push = SIMD2<Float>(0, 0)
        let p = particles[i].position
        for j in 0..<n where j != i {
            let d = p - particles[j].position
            push += d / (1e-3 + (d * d).sum())
        }
        particles[i].velocity += push * (dt * 1e-6)
    }
    for i in particles.indices {
        particles[i].position += particles[i].velocity * dt
        particles[i].position -= particles[i].position.rounded(.down)
    }
}

/// The rest of a frame: reduce the state to what a renderer would upload.
@inline(never)
func buildFrameSummary(_ particles: [Particle]) -> Float {
    var total = SIMD2<Float>(0, 0)
    for particle in particles {
        total += particle.position
    }
    return total.sum() / Float(max(particles.count, 1))
}

/// Runs `ticks` frames and returns a checksum, so the work cannot be optimized away.
func runSim(ticks: Int, slow: Bool) -> Float {
    var particles = (0..<512).map { i -> Particle in
        let f = Float(i)
        return Particle(position: SIMD2((f * 0.618).truncatingRemainder(dividingBy: 1),
                                        (f * 0.414).truncatingRemainder(dividingBy: 1)),
                        velocity: SIMD2(0.01 * (f.truncatingRemainder(dividingBy: 7) - 3),
                                        0.01 * (f.truncatingRemainder(dividingBy: 5) - 2)))
    }
    let dt: Float = 1.0 / 60.0
    var checksum: Float = 0
    for _ in 0..<ticks {
        let frame = probeSignposter.beginInterval("frame", id: probeSignposter.makeSignpostID())
        let tick = probeSignposter.beginInterval("tick", id: probeSignposter.makeSignpostID())
        if slow {
            plantedSlowStep(&particles, dt: dt)
        } else {
            simulationStep(&particles, dt: dt)
        }
        probeSignposter.endInterval("tick", tick)
        checksum += buildFrameSummary(particles)
        probeSignposter.endInterval("frame", frame)
    }
    return checksum
}
