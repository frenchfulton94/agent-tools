> typecheck-metal: metal4.0

An Objective-C block is not compiled by this gate, so it cannot ship unchecked.

```objc
id<MTLDevice> device = MTLCreateSystemDefaultDevice();
```
