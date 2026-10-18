> typecheck: macos 26.0, ios 26.0

```swift
func attachMetalLayer(to view: NSView) {
    view.wantsLayer = true
    view.layer = CAMetalLayerr()
}
```
