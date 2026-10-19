#include <metal_stdlib>
using namespace metal;
kernel void k(device atomic_int* a [[buffer(0)]]) { atomic_store_explicit(a, 1, memory_order_release); }
