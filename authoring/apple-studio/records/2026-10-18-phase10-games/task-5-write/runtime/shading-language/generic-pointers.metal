#include <metal_stdlib>
using namespace metal;

void accumulate(float* total, const float* value) { *total += *value; }

void bump_max(int* p, int v) {
    if (device int* d = addrspace_cast<device int*>(p)) {
        *d = max(*d, v);
    } else if (is_threadgroup_addrspace(p)) {
        *static_cast<threadgroup int*>(p) = v;
    } else {
        *p = v;
    }
}

struct S { int x; };
kernel void k(device float* out [[buffer(0)]], uint tid [[thread_position_in_grid]]) {
    threadgroup float shared[32];
    float local = 1.0f;
    accumulate(&out[tid], &local);
    accumulate(&shared[0], &out[tid]);
    int i = 3;
    bump_max(&i, 2);
    device int* placed = reinterpret_cast<device int*>(out);
    new (placed) device int(7);
    ushort m = interleave(uchar(1), uchar(2));
    out[0] = m;
    threadgroup_barrier(mem_flags::mem_device, memory_order_seq_cst, thread_scope_threadgroup);
}
