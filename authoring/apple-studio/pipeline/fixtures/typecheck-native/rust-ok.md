> typecheck-rust: objc2 = "=0.6.5", objc2-metal = "=0.3.2"

```rust
use objc2::rc::Retained;
use objc2::runtime::ProtocolObject;
use objc2_metal::{MTLCommandQueue, MTLCreateSystemDefaultDevice, MTLDevice};

pub fn queue() -> Option<Retained<ProtocolObject<dyn MTLCommandQueue>>> {
    let device = MTLCreateSystemDefaultDevice()?;
    device.newCommandQueue()
}
```
