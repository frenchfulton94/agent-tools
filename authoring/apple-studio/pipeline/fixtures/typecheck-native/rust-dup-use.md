> typecheck-rust: objc2 = "=0.6.5"

```rust
use std::fmt::Debug;
pub fn a() -> u32 { 1 }
```

```rust
use std::fmt::Debug;
pub fn b() -> u32 { 2 }
```

```rust
pub fn c() -> u32 { a() + b() }
```
