---
name: swift-testing
description: Swift Testing framework usage and test design for Apple-platform apps - what to test at each layer of a SwiftUI app, protocol-based test doubles without mocking frameworks, and parameterized tests with #expect. Use when writing or restructuring Swift tests, deciding what deserves a test, reviewing test quality, or migrating XCTest code.
---

# Swift testing

For the TDD process itself (red-green-refactor discipline), the superpowers
TDD skill governs; this skill carries the Swift specifics:
- Swift Testing syntax, suites, traits, parameterization → `references/swift-testing-framework.md`
- What to test per layer, and what not to → `references/what-to-test.md`
- Doubles, controlling time/network/storage → `references/test-doubles.md`

Rules:
- New tests use Swift Testing (@Test), never XCTest, unless the target already
  standardizes on XCTest.
- Run tests via the xcode-loop skill's verified commands.
- A test that cannot fail for a real reason gets deleted, not kept.
- Performance tests are authored here, but diagnosing *why* the code is slow is the
  `apple-performance` skill; note that Swift Testing has no measurement API, so
  performance tests stay on `XCTestCase` (see `references/swift-testing-framework.md`).
