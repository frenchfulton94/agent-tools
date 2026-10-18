> typecheck-metal: metal4.0

A compute kernel that doubles each element.

```metal
kernel void scale(device float *data [[buffer(0)]],
                  uint tid [[thread_position_in_grid]]) {
    data[tid] *= 2.0f;
}
```
