> verified: 2026-10 against nothing (probe fixture for deferred item 39)
> sources: none
> typecheck: macos 26.0, ios 26.0

Block 1 holds a type error inside `#if os(iOS)`. Block 2 holds the same error,
unwrapped. A gate that checks each block on its real platform fails both.

```swift
#if os(iOS)
let broken: Int = "a type error the iOS compile must catch"
#endif
```

```swift
let alsoBroken: Int = "the same error, unwrapped"
```
