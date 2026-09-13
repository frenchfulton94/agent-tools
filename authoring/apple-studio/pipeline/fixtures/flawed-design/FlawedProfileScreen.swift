import SwiftUI

// Seeded HIG-violation fixture for design-reviewer verification. Planted flaws:
// 1 (touch target): settings button tap area 24x24pt, below the 44x44 minimum.
// 2 (typography): hardcoded 11pt font ignores Dynamic Type.
// 3 (contrast): very light gray text on the default background.
// 4 (accessibility): icon-only button with no accessibility label.
// 5 (motion): infinite autoreversing animation with no Reduce Motion check.
struct FlawedProfileScreen: View {
    @State private var pulse = false
    var body: some View {
        VStack(spacing: 4) {
            Text("Profile")
                .font(.system(size: 11))
                .foregroundColor(Color(white: 0.85))
            Button(action: {}) {
                Image(systemName: "gearshape")
            }
            .frame(width: 24, height: 24)
            Circle()
                .fill(.blue)
                .frame(width: 44, height: 44)
                .scaleEffect(pulse ? 1.3 : 1.0)
                .animation(
                    .easeInOut(duration: 0.6).repeatForever(autoreverses: true),
                    value: pulse
                )
                .onAppear { pulse = true }
        }
    }
}
