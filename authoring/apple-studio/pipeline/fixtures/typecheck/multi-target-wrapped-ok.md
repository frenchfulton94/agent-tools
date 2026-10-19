> typecheck: macos 26.0, ios 26.0

```swift
#if os(iOS)
func backingScale(of view: UIView) -> CGFloat {
    view.traitCollection.displayScale
}
#elseif os(macOS)
func backingScale(of view: NSView) -> CGFloat {
    view.window?.backingScaleFactor ?? 1
}
#endif
```
