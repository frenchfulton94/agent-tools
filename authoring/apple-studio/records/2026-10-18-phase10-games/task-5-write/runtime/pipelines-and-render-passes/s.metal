#include <metal_stdlib>
using namespace metal;
vertex float4 vs(uint vid [[vertex_id]]) { float2 p[3] = { float2(-1,-1), float2(3,-1), float2(-1,3) }; return float4(p[vid], 0.25, 1); }
fragment float4 fs() { return float4(0,1,0,1); }
