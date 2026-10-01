> typecheck: ios 27.0

```swift
struct OverflowProbe: View {
    var body: some View {
        Text("Body")
            .toolbar {
                ToolbarOverflowMenu {
                    Button("Print", systemImage: "printer") {}
                }
            }
    }
}
```
