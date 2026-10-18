> typecheck-metal: metal4.0

```metal
kernel void scale(device float *data [[buffer(0)]],
                  uint tid [[thread_position_in_grid]]) {
    data[tid] = notARealHelper(data[tid]);
}
```
