> verified: 2026-08 against https://developer.apple.com/documentation/testing.md (human page did not render usable prose in fetch tooling; content below resolved via the framework's DocC JSON data endpoints instead — see task report for the exact endpoint list), https://developer.apple.com/documentation/swift/clock.md, https://developer.apple.com/documentation/foundation/urlsession.md
> sources: Testing Swift, iOS Test-Driven Development by Tutorials (both books predate or barely cover the Swift Testing framework itself; live docs are the primary authority for this file, books are cited only for XCTest-era material and testing judgment that still applies)

# Swift Testing Framework

Swift Testing is Apple's macro-based test framework (Swift 6.0+, Xcode 16.0+), positioned as the default for new test code. Tests are plain functions or methods marked `@Test` — no `XCTestCase` subclass required, and suite types can be `struct`, `class`, or `actor`. Prefer `struct`/`actor` suites over `class` so the compiler enforces the same concurrency discipline you use in production code.

## `#expect` vs `#require`

Both macros evaluate a Boolean condition (or an expression, via trailing-closure overloads for throwing/exit-testing checks). The distinction is what happens on failure:

- **`#expect(_:_:sourceLocation:)`** records a failure and lets the test keep running. Use it for every check that doesn't gate subsequent logic — this is what most assertions should be, because you want to see every failure in one run, not just the first.
- **`#require(_:_:sourceLocation:)`** throws on failure and stops the test immediately. Use it when continuing would be meaningless or would crash — unwrapping an optional you need, or checking a precondition the rest of the test depends on. A `#require`-using test function must be marked `throws`.
- `#require` has a second overload that unwraps an optional directly: `try #require(someOptional)` — fail-and-stop instead of force-unwrapping.

Both macros participate in Swift's macro expansion to capture the actual subexpression, not just a pass/fail bit: a failed `#expect(calculator.total(of: [3, 3]) == 7)` reports the literal expression and the computed value on each side (e.g. `Expectation failed: calculator.total(of: [3, 3]) == 7` with the actual result shown). This is the practical shift from XCTest: with `XCTAssertEqual(a, b)` you relied on the framework showing you two values; with `#expect(a == b)` you write ordinary Swift expressions and get the same diagnostic for free, so there's no need for a large family of specialized assert-flavor functions (`XCTAssertGreaterThan`, `XCTAssertNil`, etc.) — one boolean expression covers them all.

`#expect` and `#require` both accept a trailing `sourceLocation:` parameter, defaulted to `#_sourceLocation` (a compiler macro that expands to the caller's file/line at the call site — the actual declaration is `sourceLocation: SourceLocation = #_sourceLocation`, doc-confirmed). Forward it through your own helper/verification functions so a failure inside a shared assertion helper reports the *caller's* line, not the helper's:

```swift
func verifyDivision(_ result: (quotient: Int, remainder: Int),
                     expectedQuotient: Int, expectedRemainder: Int,
                     sourceLocation: SourceLocation = #_sourceLocation) {
    #expect(result.quotient == expectedQuotient, sourceLocation: sourceLocation)
    #expect(result.remainder == expectedRemainder, sourceLocation: sourceLocation)
}
```
(Testing Swift, ch. 2)

For errors, prefer asserting the specific error over a catch-all: `#expect(throws: GameError.notInstalled) { try game.play() }` beats `#expect(throws: Error.self) { ... }`, which only proves *something* threw. Use `#expect(throws: Never.self)` to assert a call does not throw. For cases needing custom pass/fail logic mid-test (e.g., after a `do`/`catch` where no error arrived when one was expected), call `Issue.record(...)` directly rather than contorting a boolean into `#expect`.

Swift Testing has no built-in floating-point tolerance parameter equivalent to XCTest's `accuracy:` argument — confirmed against the current expectations documentation, which covers only boolean/error/exit-code/async expectations with no approximate-equality API. For float/double comparisons, either bring in swift-numerics' `isApproximatelyEqual(to:absoluteTolerance:)` or write the tolerance check by hand. Don't assert exact equality on computed floating-point values; the underlying binary representation will drift under refactors even when the value is behaviorally identical.

## Organizing tests: suites

A type becomes a suite implicitly just by containing `@Test` functions; `@Suite` is optional and only needed to attach a display name or suite-level traits (which every test inside inherits automatically — tags, `.disabled`, time limits, etc. all cascade down). Suites can nest (a suite type declared inside another suite type). Suite types run their tests **in parallel by default** — that's a default flip from XCTest, so anything relying on shared mutable state across tests needs deliberate handling (see traits below).

Setup/teardown moves from `setUp()`/`tearDown()` to the type's own `init()`/`deinit()`. A suite type with `@Test` instance methods must have a callable zero-argument initializer (implicit, or explicit — sync/async/throwing, any access level are all fine); a type with only static/class `@Test` members isn't bound by this. Suite types (and anything containing them) cannot carry `@available` annotations — that's a compile error, not a runtime skip. (doc-confirmed: developer.apple.com/documentation/testing/organizingtests)

Because `init()` runs fresh per test method (one instance per test case, not shared across the suite), state stored as instance properties is naturally isolated between tests without an explicit teardown step — this is a meaningful behavior change from `XCTestCase`, where the instance persisted for the whole run and stale state was a classic bug source (Testing Swift, ch. 2; iOS Test-Driven Development, ch. 3).

## Traits

Traits are values attached to `@Test`/`@Suite` via variadic trailing arguments; suite-level traits apply to every contained test. Built-ins worth reaching for by default:

- **`.disabled(_:)`** / **`.disabled(if:)`** — unconditionally or conditionally skip a test.
- **`.enabled(if:)`** — inverse; always requires a condition (bare "enabled" would be redundant with the default).
- **`.bug(_:_:)`** — attach a tracked bug (URL or numeric/string ID) with an optional comment, for context on a known-failing or workaround test.
- **`.tags(...)`** — apply one or more `Tag` values (declared as `static var` extensions on `Tag` in the test target, never production code) for cross-cutting grouping independent of suite structure — e.g. tag everything that should run in a smoke-test subset regardless of which suite it lives in.
- **`.timeLimit(.minutes(_:))`** — fail a test that runs too long; if both a suite and a test specify a limit, the shorter one wins. On a parameterized test, the limit applies per test case, not to the whole batch.
- **`.serialized`** — force a suite's tests (or a parameterized test's cases) to run one at a time instead of in parallel. Reach for this only when shared external state (a server connection limit, a singleton) makes parallel execution actually unsafe — don't serialize by default, since parallelism is the framework's main speed advantage over XCTest.

(all doc-confirmed: developer.apple.com/documentation/testing/traits)

For deeper customization — injecting a task-local value or otherwise wrapping a test's execution in custom setup/teardown that regular `init`/`deinit` can't express — implement a custom trait conforming to `TestTrait` and `TestScoping`, providing a `provideScope(for:testCase:performing:)` method that wraps the call to the test closure (mechanism and method name confirmed against the current Traits documentation; the exact parameter list wasn't independently re-verified line-by-line — treat it as directionally correct and check current Xcode's autocomplete/docs before relying on the precise signature). This is the mechanism for per-test environment isolation under Swift Testing's default parallel execution — reach for it before reaching for `.serialized` if the actual goal is "this test needs its own state," not "this test can't run concurrently with others." (Testing Swift, ch. 2)

## Parameterized tests

`@Test(arguments:)` runs the same test function once per element of a collection; each element becomes its own reportable test case in the IDE/CLI output, with its own pass/fail and its own diagnostic on failure — this is not a loop inside one test, it's N independent tests generated from one function body. `CaseIterable` enums pair naturally with `Food.allCases` — new cases get test coverage automatically without touching the test. Integer ranges work directly as an arguments collection, but avoid unbounded/huge ranges (e.g., `0..<Int.max`); the framework doesn't guard against combinatorial explosion for you. (doc-confirmed: developer.apple.com/documentation/testing/parameterizedtesting)

Two collections can be supplied at once, generating either their cartesian product (independent collections — 5 × 100 inputs yields 500 cases) or, via `zip(...)`, paired combinations (yields as many cases as the shorter sequence). This caps at two argument collections: the macro only ships overloads for one collection or two (`Test(_:_:arguments:)` and `Test(_:_:arguments:_:)`, the latter taking exactly `collection1`/`collection2`) — there is no three-or-more-collection overload, confirmed against the macro's declaration. Past two independent inputs, pack values into a tuple or custom struct and pass one collection of those.

Test cases of a parameterized test run in parallel by default, same as suite-level tests; add `.serialized` if execution order or shared state matters. Argument expressions can be `try`/`await` — they're evaluated lazily, only if the test actually runs, so gating an expensive argument-fetch behind a disabled/skipped test costs nothing. To let a CI/IDE re-run one specific failing case in isolation, every argument type must conform to one of (in priority order) `CustomTestArgumentEncodable`, `RawRepresentable` (with `Encodable` raw value), `Encodable`, or `Identifiable` (with `Encodable` ID) — arguments that don't satisfy one of these can still parameterize the test, they just can't be re-run individually.

## Async and concurrency testing

`@Test` functions can be `async`, `throws`, or both, with zero ceremony — mark the function `async` and `await` inside it like any other Swift code. This replaces the entire XCTestExpectation dance (`expectation(description:)` / `fulfill()` / `wait(for:timeout:)`) that XCTest required for anything asynchronous (see "Maintaining older code" below). Because `await` is a real suspension point, the test runner may interleave other tests during the suspension — don't assume anything about ordering or timing around an `await` inside a test.

For asserting an async event happened (or happened a specific number of times), use `confirmation(expectedCount:) { confirm in ... }`: call `confirm()` each time the awaited event fires, and the test fails if the final count doesn't match `expectedCount` (default 1; accepts a fixed number, `0` for "never," or a range like `5...10` or `5...`; open-ended ranges without a lower bound are disallowed). The confirmation body must have finished all its expected work by the time the closure returns — it does not itself wait on anything, unlike an XCTestExpectation. (Testing Swift, ch. 2; mechanics doc-adjacent, not independently confirmed against live docs)

Swift Testing doesn't pin tests to the main actor the way XCTest pinned synchronous test methods by default — if a test needs main-thread execution, mark it (or its suite) `@MainActor` explicitly, or isolate just the sensitive block with `await MainActor.run { ... }`. `confirmation()` and `withKnownIssue()` closures can take their own actor isolation independent of the enclosing test.

For legacy completion-handler APIs that haven't been converted to `async`, bridge with `withCheckedContinuation` inside an `async` test rather than reintroducing an expectation-style wait.

## Known issues and error handling

`withKnownIssue("reason") { ... }` marks a block as expected to fail without failing the overall test run — but if the block completes with **zero** issues, `withKnownIssue` itself now flags that as noteworthy (the known problem may be fixed, so the wrapper is stale and should be removed). Pass `isIntermittent: true` for flaky/non-deterministic known failures, which suppresses that "unexpectedly passed" signal. `when:` and `matching:` trailing closures let you scope which conditions or which specific recorded issues count as "known" rather than blanket-suppressing the whole block. (doc-confirmed: developer.apple.com/documentation/testing/known-issues)

## Maintaining older code: XCTest

Swift Testing and XCTest can coexist in the same target/file, and interoperate on shared assertion reporting; `SWIFT_TESTING_XCTEST_INTEROP_MODE` controls how cross-framework issues are surfaced (`none`, `limited`, `complete` — default from Swift 6.4 — or `strict`, which crashes on a cross-library XCTest issue). This makes incremental migration realistic: adopt `#expect`/`#require` inside existing `XCTestCase` subclasses first, then convert whole classes to `@Suite` structs over time, rather than a big-bang rewrite. (doc-confirmed: developer.apple.com/documentation/testing/migratingfromxctest)

Direct migration mapping (doc-confirmed):

| XCTest | Swift Testing |
|---|---|
| `XCTAssertTrue(x)` / `XCTAssert(x)` | `#expect(x)` |
| `XCTAssertFalse(x)` | `#expect(!x)` |
| `XCTAssertNil(x)` / `XCTAssertNotNil(x)` | `#expect(x == nil)` / `#expect(x != nil)` |
| `XCTAssertEqual(x, y)` / `NotEqual` | `#expect(x == y)` / `#expect(x != y)` |
| `XCTAssertIdentical` / `NotIdentical` | `#expect(x === y)` / `#expect(x !== y)` |
| `XCTAssertGreaterThan` / `LessThan` | `#expect(x > y)` / `#expect(x < y)` |
| `XCTAssertThrowsError(try f())` | `#expect(throws: (any Error).self) { try f() }` |
| `try XCTUnwrap(x)` | `try #require(x)` |
| `XCTFail("...")` | `Issue.record("...")` |
| `continueAfterFailure = false` + assert | `try #require(...)` (throws, halts test) |
| `XCTSkipIf` / `XCTSkipUnless` | `.disabled(if:)` / `.enabled(if:)` trait |
| `throw XCTSkip()` mid-test | `try Test.cancel("reason")` |
| `XCTExpectFailure { }` | `withKnownIssue { }` |
| `XCTestExpectation` + `wait(for:timeout:)` | `async`/`await` directly, or `confirmation()` |
| `XCTAttachment` | `Attachment.record(_:)` on an `Attachable`-conforming type |

Legacy XCTest structural facts worth knowing when reading old test code, since Swift Testing changes the defaults:

- **`XCTestCase` lifecycle** ran `setUpWithError()`/`tearDownWithError()` around each test method, but the *instance itself* persisted for the whole class run — unlike a Swift Testing suite, which gets a fresh instance per test via `init()`. This was the source of classic test-pollution bugs when developers assumed each test got a clean instance (iOS Test-Driven Development, ch. 3).
- **Test execution order was unspecified** and, in Xcode, could be explicitly randomized via a scheme setting — a useful lever for exposing hidden inter-test state dependencies, since a fixed default order can mask them for a long time (iOS Test-Driven Development, ch. 4).
- **`XCTestExpectation`** required manual `fulfill()` calls and a `wait(for:timeout:)`; `isInverted = true` asserted something did *not* happen within the timeout, and `expectedFulfillmentCount` distinguished "any one of these N expectations fires" from "this specific event must fire N times" — a common bug was expecting parallel/independent expectations to compose like a counter when they don't (iOS Test-Driven Development, ch. 5).
- **`XCTAssert*` produces a pass by default** if no assertion ever runs — a test body with no assertions silently passes in both XCTest and (in effect) Swift Testing, so an empty or accidentally-untriggered test is not caught by the framework itself; this is a discipline problem, not something either framework prevents (iOS Test-Driven Development, ch. 4).
- **Performance testing** (`XCTestCase.measure { }`, with baseline-setting and automatic 10x repeated runs) has no Swift Testing equivalent as of this writing — checked the current Swift Testing documentation topic list and found no performance/measurement API — so performance regression tests stay in an `XCTestCase` subclass even in an otherwise fully-migrated target (Testing Swift, ch. 2).
- **View controller / host-app testing**: XCTest test targets can specify a host application, giving tests access to the live `UIApplication`/window hierarchy instead of a manually instantiated, not-yet-loaded controller — relevant when porting UIKit-era tests that depended on `viewDidLoad` having actually run (iOS Test-Driven Development, ch. 4).
- **Code coverage caveat carries over unchanged**: coverage percentage measures *lines executed*, not *behavior verified* — a getter/initializer can hit 100% coverage from tests that never assert on the values it produces. Don't treat a coverage number as a proxy for test quality in either framework (Testing Swift, ch. 2; iOS Test-Driven Development, ch. 4).

## Maintaining older code: UI testing stays on XCTest

Swift Testing has no UI-automation surface today — driving and querying app UI (`XCUIApplication`, element queries, `XCTAssert*` on UI elements) still runs on `XCTestCase`-based XCUITest, confirmed by the absence of any UI-testing topic in the current Swift Testing documentation. A mixed target commonly runs Swift Testing for unit/logic tests and XCTest/XCUITest for the UI test target side by side — this isn't a migration gap to close, just the current shape of the two frameworks' scopes.
