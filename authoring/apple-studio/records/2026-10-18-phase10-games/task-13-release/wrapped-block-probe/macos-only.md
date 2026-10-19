> verified: 2026-10 against nothing (probe fixture for deferred item 39)
> sources: none
> typecheck: macos 26.0

The block holds a type error inside `#if os(iOS)`. No listed target is iOS, so
no compile ever sees the error.

```swift
#if os(iOS)
let broken: Int = "never compiled on any target"
#endif
```
