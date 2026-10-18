> typecheck-rust: objc2 = "=0.6.5"

```rust
use std::fmt::Debug;
pub fn a() -> u32 { 1 }
```

```rust
use std::fmt::Debug;
pub fn b() -> u32 { a() + 1 }
```

```rust
pub fn c() -> u32 { b() + 1 }
```
