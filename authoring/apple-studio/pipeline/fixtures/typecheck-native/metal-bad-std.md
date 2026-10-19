> typecheck-metal: metal9.9

```metal
kernel void scale(device float *data [[buffer(0)]],
                  uint tid [[thread_position_in_grid]]) {
    data[tid] *= 2.0f;
}
```
