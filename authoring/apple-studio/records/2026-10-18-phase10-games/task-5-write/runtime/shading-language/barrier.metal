#include <metal_stdlib>
using namespace metal;
kernel void k(device int* o [[buffer(0)]]) { threadgroup_barrier(mem_device); simd_barrier(); o[0]=1; }
