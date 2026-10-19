#include <metal_stdlib>
using namespace metal;
kernel void single_pass_sum(device const float* input [[buffer(0)]],
                            coherent(device) device float* partials [[buffer(1)]],
                            device atomic_uint* finished [[buffer(2)]],
                            device float* result [[buffer(3)]],
                            constant uint& count [[buffer(4)]],
                            threadgroup float* scratch [[threadgroup(0)]],
                            uint gid [[thread_position_in_grid]],
                            uint group [[threadgroup_position_in_grid]],
                            uint groups [[threadgroups_per_grid]],
                            ushort lane [[thread_index_in_simdgroup]],
                            ushort simd_id [[simdgroup_index_in_threadgroup]],
                            ushort simds [[simdgroups_per_threadgroup]]) {
    // Out-of-range threads contribute zero instead of returning before the barrier.
    float v = simd_sum(gid < count ? input[gid] : 0.0f);
    if (lane == 0) scratch[simd_id] = v;
    threadgroup_barrier(mem_flags::mem_threadgroup);
    if (simd_id != 0) return;
    float group_sum = simd_sum(lane < simds ? scratch[lane] : 0.0f);
    if (lane != 0) return;
    partials[group] = group_sum;
    // Release this group's partial; the last arrival acquires everyone else's.
    uint done = atomic_fetch_add_explicit(finished, 1u, memory_order_acq_rel,
                                          mem_flags::mem_device);
    if (done == groups - 1) {
        float total = 0.0f;
        for (uint i = 0; i < groups; ++i) total += partials[i];
        *result = total;
    }
}
