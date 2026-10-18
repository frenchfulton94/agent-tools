#include <metal_stdlib>
using namespace metal;
kernel void k(device float* o [[buffer(0)]]) {
  threadgroup atomic_float acc;
  atomic_fetch_add_explicit(&acc, 1.0f, memory_order_relaxed);
  o[0] = atomic_load_explicit(&acc, memory_order_relaxed);
}
