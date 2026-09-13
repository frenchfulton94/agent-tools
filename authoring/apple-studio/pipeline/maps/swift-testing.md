# Chapter map: swift-testing

Targets (Task 5): `swift-testing-framework.md`, `what-to-test.md`, `test-doubles.md`.

Note: chapters covering the TDD red/green/refactor process itself are skipped — per
Task 5's interface note, that process is owned by the superpowers TDD skill; this
skill carries only Swift/Xcode-specific testing material.

## ios-test-driven-development-by-tutorials-v2-0-0.md

- L157–L258: Chapter 1: What Is TDD? ("what should you test", "when should you use TDD") → what-to-test.md
- L703–L1230: Chapter 3: TDD App Setup (test target structure, XCTestCase — maintaining-older-code / XCTest baseline) → swift-testing-framework.md
- L1231–L1860: Chapter 4: Test Expressions (assertions, error testing, code coverage, debugging tests) → swift-testing-framework.md
- L1861–L2594: Chapter 5: Test Expectations (async testing via XCTestExpectation — migration notes to Swift Testing's async support) → swift-testing-framework.md
- L2595–L3254: Chapter 6: Dependency Injection & Mocks (fakes/mocks/stubs, injecting dependencies, time dependencies) → test-doubles.md
- L3313–L4412: Chapter 8: RESTful Networking (mocking URLSession, TDD-ing a networking call) → test-doubles.md
- L4413–L4952: Chapter 9: Using the Network Client (network client protocol, mock network client) → test-doubles.md
- L4953–L6076: Chapter 10: ImageClient (image client protocol, caching, mocking) → test-doubles.md
- L6085–L6752: Chapter 11: Legacy Problems (finding a test point and a seam in untested legacy code) → test-doubles.md
- L6753–L7020: Chapter 12: Dependency Maps (mapping direct/secondary dependencies before breaking them) → test-doubles.md
- L7021–L7476: Chapter 13: Breaking Up Dependencies (introducing protocol seams into legacy code) → test-doubles.md
- L7477–L7964: Chapter 14: Modularizing Dependencies → test-doubles.md
- L7965–L8438: Chapter 15: Adding Features to Existing Classes (sprouting method, passing around dependencies) → test-doubles.md
- SKIP: Chapter 2: The TDD Cycle (L259–L702) — the red/green/refactor process itself, out of scope (superpowers TDD skill). Chapter 7: Introducing Dog Patch (L3255–L3312) — project intro only, no decision-grade content. Front matter/license/forums, Conclusion.

## testing-swift-2025-05-15-pdf.txt

(PDF text; headings verified with `sed -n '<line>p'` — "Chapter N" line, title on the
following line.)

- L278–L1030: Chapter 1: The Basics of Testing (why test, anatomy of a test, testing pyramid) → what-to-test.md
- L1031–L3967: Chapter 2: Unit Testing (organizing tests, setup/teardown, assertions, @Test, suites/tags, testing Swift concurrency, performance/parallel testing) → swift-testing-framework.md
- L3968–L5949: Chapter 3: Test Doubles (DI, interfaces not implementations, mocking, partial vs. full mocks, mocking networking, what not to mock) → test-doubles.md
- L5950–L6783: Chapter 4: User Interface Testing (what's worth testing at the UI layer) → what-to-test.md
- L8372–L9118: Chapter 6: Tips (upgrading legacy code to have tests, writing testable code) → test-doubles.md
- SKIP: Chapter 5: Test-Driven Development (L6784–L8371) — the TDD process itself, out of scope (superpowers TDD skill). Preface, Afterword.
