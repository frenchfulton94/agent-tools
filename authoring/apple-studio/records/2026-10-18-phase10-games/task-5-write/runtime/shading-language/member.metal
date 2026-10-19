#include <metal_stdlib>
using namespace metal;
struct Acc { int x; int get() { return x; } };
kernel void k(device int* o [[buffer(0)]]) { Acc a{1}; o[0] = a.get(); }
