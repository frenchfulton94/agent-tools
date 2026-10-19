> typecheck: macos 26.0, ios 26.0

The macOS branch is correct. The iOS branch uses an invented property, so the
block must fail: the macOS compile sees only the macOS branch.

```swift
#if os(iOS)
func backingScale(of view: UIView) -> CGFloat {
    view.traitCollection.inventedDisplayScale
}
#elseif os(macOS)
func backingScale(of view: NSView) -> CGFloat {
    view.window?.backingScaleFactor ?? 1
}
#endif
```
