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
