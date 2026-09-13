> verified: 2026-08 against https://developer.apple.com/documentation/testing.md (framework's UI-testing scope checked via its DocC topic index — no UI-testing page exists there)
> sources: Testing Swift, iOS Test-Driven Development by Tutorials

# What to Test: A Layered Strategy for SwiftUI Apps

Testing posture should follow from where a piece of code sits in the app, not from a blanket
policy ("test everything" or "100% coverage"). The deciding factors are determinism, cost to
write and run, and how much risk the code actually carries. This file assumes the DI and
persistence seams described elsewhere in this skill set already exist — protocol-boundary
injection for dependencies, a repository protocol in front of persistence — and gives the
per-layer decision for what to point tests at, not how to wire the seams themselves.

## The pyramid shape, briefly

Tests naturally stratify into unit, integration, and UI/end-to-end layers, from fastest/most
numerous at the bottom to slowest/least numerous at the top (Testing Swift, ch. 1). Good unit
tests are Fast, Isolated, Repeatable, Self-verifying, and Timely (the FIRST criteria) — all five
matter together, since a test that's fast but flaky, or isolated but ambiguous about pass/fail,
isn't actually useful. Integration tests relax Fast and Timely (they exercise real components
together, so they're inherently slower and usually written after the fact) but should still be
Isolated and Repeatable. UI tests relax further still and trade determinism for realism. The
practical consequence: put your testing effort where the pyramid is wide — pure logic and view
models — and treat the tip as a deliberately small, curated set (Testing Swift, ch. 1 and ch. 4).

## Pure model / domain logic — test exhaustively

This is the layer with the best cost/value ratio: deterministic, synchronous where possible, no
rendering pipeline or view-lifecycle noise to fight. Cover it thoroughly — edge cases, boundary
values, invariants, every branch of custom validation or calculation logic, every state
transition a domain type can undergo. Because these tests are cheap to write and run in
milliseconds, there's little excuse not to be exhaustive here, and this is where TDD's
write-test-first cycle pays off most directly.

What counts as "yours to test": any method, computed property, or transformation you wrote by
hand. What doesn't:

- Compiler-synthesized conformances (`Codable`, `Equatable`, `Hashable` the compiler derives
  for you) — you didn't write the logic, so you're not responsible for verifying it (iOS
  Test-Driven Development, ch. 1).
- Anything the compiler already catches — a type mismatch or missing `case` isn't a test's job.
- Framework/dependency internals (Foundation, SwiftData, SwiftUI's own machinery) — the
  framework author owns those tests, not you. The one exception is a throwaway exploratory test
  written purely to confirm how an unfamiliar API behaves; delete it once you've learned what
  you needed, don't keep it as permanent suite weight. A second, narrower exception is a
  deliberate "sanity test" against a third-party library you don't fully trust — if you find
  yourself writing many of these, that's a signal to re-evaluate the dependency itself, not to
  keep padding the suite (iOS Test-Driven Development, ch. 1).

Classic mistake at this layer: writing a test that only proves a computed property returns what
you just assigned to it. That isn't testing a decision or a risk — it's testing that Swift
assignment works.

## View models / observable state holders — test through observable behavior

A view model's job is to turn inputs (user actions, data arriving from a repository or service)
into observable state a view can render. Test exactly that contract: given these inputs and
these injected fakes, does the observable state end up where it should. Don't test *how* it gets
there.

```swift
// Prefer: assert on the observable surface after driving a real input.
@Test func loadFailureSurfacesAnErrorState() async throws {
    let sut = LibraryViewModel(catalog: FailingCatalogFake())
    await sut.load()
    #expect(sut.state == .error("Couldn't load your library"))
}

// Avoid: reaching into private state or calling an internal step directly —
// this couples the test to today's implementation, not the behavior a view relies on.
```

Because DI is already protocol-shaped at this layer, inject a fake or stub conforming to the
same protocol the real dependency uses, drive the view model's public API, and assert on its
published/observable properties. If you find yourself wanting to test a private method or
private state directly, that's the same signal as at the model layer: either the logic is a real
decision that deserves to be extracted into its own separately-testable type, or it's plumbing
that doesn't need a dedicated test at all (iOS Test-Driven Development, ch. 1, on why private
code generally shouldn't be tested directly).

Don't write tests whose only purpose is to confirm that the observation framework itself works —
that toggling a tracked property notifies observers, or that setting a `@Published`/`@Observable`
property causes *a* re-render. That's Apple's contract to guarantee, the same way you don't test
that `Foundation` decodes JSON correctly.

## Views — test sparingly, and only real logic

A SwiftUI view's `body` is a declarative description consumed by the framework; the framework is
responsible for turning that description into pixels. Unit-testing that a view's body produces a
particular hierarchy for a given state is, in effect, re-testing SwiftUI's rendering contract —
low value, high churn, and exactly the kind of "dependency code" the exhaustive-testing default
excludes.

What *is* worth testing at this layer is real logic that happens to live in a view: a computed
property that picks between several display states, a formatting or validation function, any
branch that isn't purely "which SwiftUI view do I hand back." The fix, in order of preference:

1. **Extract it.** Move the logic into a plain function, computed property on a non-view type,
   or into the view model, and test it directly at the model/view-model layer where it's cheap
   and deterministic.
2. **If it truly can't be extracted** (it's inseparable from layout, gesture state, or other
   view-local mechanics), exercise it sparingly through a UI or snapshot test. Treat this as
   top-of-pyramid: slower, more brittle, and deliberately kept to a small, high-value set rather
   than grown to match your unit-test count.

When you do write UI-layer tests, key element lookup to explicit accessibility identifiers
rather than to display text or a derived value (a slider's percentage label, a title that gets
localized or A/B tested) — identifiers are a stable seam that doesn't break on cosmetic or
copy changes, which matters because this layer is already the most fragile one in the suite
(Testing Swift, ch. 4).

Swift Testing (`import Testing`, `@Test`/`#expect`) has no UI-automation surface — driving and
querying app UI still goes through XCTest's `XCUIApplication`/XCUIElement APIs (see
"Maintaining older code" below).

## Integration points (networking, persistence) — test at the seam

Given the repository/protocol seam already sits in front of persistence and networking, most of
the value comes from testing business logic and view models against fakes of that protocol —
fast, deterministic, no real I/O. Reserve a smaller set of true integration tests for the
concrete implementation behind the seam itself: does this fetch predicate actually return the
right rows against a real (in-memory) store, does this network layer actually decode a real
response shape. These tests intentionally give up some of Fast/Isolated/Timely in exchange for
confidence that the real implementation, not just the fake, behaves — keep them fewer in number
and don't expect them to run on every keystroke the way unit tests do (Testing Swift, ch. 1).

## What NOT to test — anti-pattern checklist

- Compiler-synthesized code, and anything a compile error or warning would already catch.
- Framework or third-party dependency internals — not your code, not your responsibility, with
  the narrow exploratory/sanity-test exceptions above.
- Private implementation details reached into just to make them "testable" — extract instead, or
  accept that plumbing doesn't need its own test.
- A getter/computed property that only echoes back what a test just set — no decision, no risk.
- SwiftUI's own rendering guarantees — a `@State` change updating the view that reads it, a
  `Text` showing the string you handed it. Trust that contract the way you trust `Foundation`.
- Chasing coverage percentage as a goal in itself. Coverage measures lines executed, not whether
  an assertion exercises real risk; automated tests can only confirm the behavior you thought to
  specify; they don't discover bugs you didn't anticipate (Testing Swift, ch. 1). A suite can hit
  high coverage and still fail at its actual job — giving you confidence to make bold changes.
- Tests wired to internal structure instead of observable behavior. This is how teams end up with
  hundreds of tests, heavy duplication, and a codebase they're afraid to refactor — the opposite
  of what tests are for. Review and maintain test code with the same care as production code
  (Testing Swift, ch. 1).

## Scoping effort: durability and risk, not layer alone

Layer sets the *default* posture above, but how much effort any given layer actually gets should
still track the code's expected lifetime and complexity. Code meant to last months or years
across multiple releases earns full, exhaustive coverage at the model/view-model layers;
short-lived throwaway or prototype work can skip most of it, reserving tests for its riskiest or
most complex parts only (iOS Test-Driven Development, ch. 1). A blunt but useful filter when
scoping: weigh each part by what actually breaks if it's wrong — a crash, corrupted data, a
visibly wrong result — and spend test effort there first, ahead of low-stakes paths whose
failure would barely register (Testing Swift, ch. 1). Apply that per-feature, not as a reason to
skip the model layer wholesale.

## Maintaining older code: UI testing still runs on XCTest

Because Swift Testing has no UI-testing support today, the sparse UI-layer tests described above
are written against `XCTestCase`-based XCUITest (`XCUIApplication`, element queries,
`XCTAssert*`) rather than `#expect`. This is purely a mechanical/API difference — the judgment
above (extract real logic instead of testing rendering, use accessibility identifiers as the
lookup seam, keep this layer small and expect it to be the most flaky) applies the same way
regardless of which framework executes the test.
