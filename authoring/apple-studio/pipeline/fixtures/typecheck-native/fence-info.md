> typecheck-metal: metal4.0

A fence with text after the language is not the exact opener, so it exits 2.

```metal title="scale.metal"
kernel void scale(device float *data [[buffer(0)]],
                  uint tid [[thread_position_in_grid]]) {
    data[tid] = notARealHelper(data[tid]);
}
```
