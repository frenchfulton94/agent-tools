import SwiftUI

// Flaw 1 (architecture): view performs networking + parsing inline.
struct ProfileView: View {
    @State private var name = ""
    var body: some View {
        Text(name).task {
            let (data, _) = try! await URLSession.shared.data(
                from: URL(string: "https://api.example.com/profile")!)
            name = String(data: data, encoding: .utf8) ?? ""
        }
    }
}

// Flaw 2 (concurrency): mutable shared state, data race suppressed.
final class SessionCache: @unchecked Sendable {
    static let shared = SessionCache()
    var entries: [String: String] = [:]
    func store(_ key: String, _ value: String) { entries[key] = value }
}

// Flaw 3 (testing): behavior-bearing logic, no test anywhere in the fixture.
struct DiscountEngine {
    func discount(for total: Double) -> Double {
        if total > 100 { return total * 0.9 }
        return total
    }
}
