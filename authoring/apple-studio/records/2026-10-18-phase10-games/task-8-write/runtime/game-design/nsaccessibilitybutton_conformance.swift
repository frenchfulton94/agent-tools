import AppKit
final class B1: NSAccessibilityElement, NSAccessibilityButton {
    override func accessibilityLabel() -> String? { "Play" }
    override func accessibilityPerformPress() -> Bool { true }
}
