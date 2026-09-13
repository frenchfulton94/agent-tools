> verified: 2026-08 against https://developer.apple.com/documentation/swift/clock, https://developer.apple.com/documentation/foundation/urlsession/data(for:delegate:)
> sources: iOS Test-Driven Development by Tutorials, Testing Swift

# Test Doubles: Fakes, Stubs, and Spies (No Mocking Frameworks)

Scope: protocol-based test doubles for isolating business logic from the network, disk, and
non-deterministic effects (time, randomness), and the house rule against mocking frameworks.
For DI mechanics (injection style, containers, environment vs. initializer injection), see
`swift-architecture/references/state-and-di.md`. For the repository-pattern persistence seam
and in-memory `ModelConfiguration`/Core Data stores, see
`swift-architecture/references/persistence.md` — this file builds on both rather than
repeating them.

## Terminology, briefly

A *test double* is the umbrella term (an object standing in for a real dependency so a test can
isolate its subject). The family, roughly food-chain order:

- **Dummy** — implements a protocol with empty/no-op methods, needed only to satisfy a
  parameter list so code compiles. Carries no behavior.
- **Stub** — returns fixed, canned values. Use when the test only needs the SUT to receive a
  particular input, not to exercise any real logic in the dependency.
- **Fake** — a real, working implementation that takes a shortcut unacceptable in production
  (an in-memory store instead of a database, a local array instead of a network round trip).
  Use when the SUT's logic depends on the dependency actually *doing* something (storing,
  filtering, computing), just not doing it for real.
- **Spy** — records what happened (call counts, arguments, ordering) so the test can assert on
  it afterward, while still doing real work.
- **Mock** — records expected interactions like a spy, but is generally pre-loaded with
  expectations and used purely to verify behavior, not to produce usable side effects — a
  "flight recorder" for calls (iOS Test-Driven Development, ch. 6; Testing Swift, ch. 3).

In practice the useful distinction is narrower than the taxonomy: ask whether the test needs
*canned data* (stub), *working-but-cheap behavior* (fake), or *proof a call happened with the
right arguments* (spy/mock) — and build only that much.

## House rule: no mocking frameworks

Test doubles here are always a hand-written `struct`/`class` conforming to the same protocol the
production dependency conforms to — never a runtime-generated or reflection-based mock from a
mocking library. Reasons this is a firm rule, not a style preference:

- Protocols are already cheap and idiomatic in Swift; a mocking framework mostly re-solves a
  problem Swift's type system already solves for free.
- A hand-written double is ordinary Swift: it compiles, participates in refactors (rename a
  protocol method and every double either updates or fails to compile — nothing is stringly
  typed or dynamically resolved), and is debuggable with the same tools as production code.
- Runtime mocking magic buys little here and costs discoverability — a `grep`-able,
  Cmd-click-able `struct FooFake: FooServicing` is easier for both a human and Claude to read
  than a DSL-configured mock object.

This is consistent with `state-and-di.md`'s "DI without a framework" stance: the same
plain-protocol-plus-injection posture that governs dependency injection governs test doubles.

## Building doubles: start small, name what they are

Start a double as a type nested inside the test that uses it — this avoids polluting other
tests and avoids designing a "reusable" double before you know what's actually reusable
(Testing Swift, ch. 3). Promote it to a top-level type only once more than one test needs it,
and when you do, encode its kind in the name and filename (`SessionStub`, `MockAnalyticsAPI`,
`FakeUserRepository`) — a reader should be able to tell what a double *is* without opening it.

Do the minimum work necessary for the double to satisfy the protocol and the test's assertions.
A double that grows extra logic, extra state, or defensive code the protocol never asked for is
a maintenance liability and a sign the test itself may not be isolated enough (Occam's razor
applies to test code too).

Prefer a full test double conforming to a protocol over a partial mock (subclassing a
production type and overriding one method). Partial mocks are occasionally necessary for
framework types you don't own and can't otherwise seam (e.g., an Apple SDK class marked
`open`), and only work on classes at all — never structs. Even then, treat subclass-and-override
as a fallback, not a first choice: it risks silently leaving some real behavior (caching, other
overridden methods) active, and it doesn't require or encourage narrowing the interface the way
extracting a protocol does (iOS Test-Driven Development, ch. 9).

## Controlling time in tests

Never call `Date()`/`Date.now`, start a real `Timer`, or `sleep` inside logic you want a
deterministic unit test for. Inject a time source instead:

```swift
protocol DateProviding {
    var now: Date { get }
}
```

or the closure equivalent, `let now: () -> Date = Date.init`, defaulted to the real clock so
production call sites need no changes. In tests, inject a fixed or stepped stand-in and assert
against known dates instead of "some time near when the test ran."

For durations/elapsed-time logic, Swift's standard-library `Clock` family (`ContinuousClock`,
`SuspendingClock`, both available since iOS 16/macOS 13) is the modern equivalent of a date
provider for measuring elapsed time rather than reading wall-clock time — inject the `Clock`
protocol the same way, and swap in a test clock when the logic under test needs deterministic
durations rather than deterministic dates.

For code driven by a real `Timer` or repeating scheduler, don't try to make the test wait out
real time or shrink the interval to milliseconds as a primary strategy — both are flaky and
slow. Prefer testing the *callback's effect* directly: extract the timer's handler into an
ordinary method and call it directly in the test, leaving the scheduling itself uncovered by
unit tests (verify scheduling, if at all, via a slower integration/UI test) — the correctness
that matters is almost always "what happens when the tick fires," not "did a real `Timer` fire
after exactly N seconds" (iOS Test-Driven Development, ch. 6).

## Controlling network in tests

Never let a unit test perform a real network request — real requests are slow, flaky, require
connectivity, and make error-path testing (timeouts, malformed JSON, specific HTTP statuses)
impractical to set up. The seam:

- Define a narrow protocol covering only the network operations your consumer actually needs
  (`func getDogs() async throws -> [Dog]`, not "everything `URLSession` can do"). The protocol
  is the contract; consumers depend on it, never on `URLSession` directly.
- Prefer wrapping `URLSession`'s async `data(from:)`/`data(for:)` methods — `func data(for
  request: URLRequest) async throws -> (Data, URLResponse)` — behind that protocol over
  subclassing `URLSession`/`URLSessionTask` directly. Both classes remain effectively
  unsubclassable for this purpose (their designated initializers and factory methods aren't
  meant to be overridden to fabricate fake network behavior), which is why the idiomatic seam is
  a hand-written protocol the real session conforms to via an extension, with a hand-written
  fake conforming to the same protocol for tests.
- The fake session/client returns canned `Data`/errors synchronously or via a controlled async
  path — no real I/O, no timing dependency.
- Keep the test double at the *client* level (a `NetworkClient`/`FooService` protocol) for
  business-logic tests; reserve a lower-level `URLSession`-adjacent fake for the rare test that's
  actually verifying the client implementation's own request-building/response-parsing behavior.
  Most call sites should never need to go that low.

This mirrors the "design to interfaces, not implementations" principle broadly (Testing Swift,
ch. 3) and the concrete networking-client pattern (iOS Test-Driven Development, ch. 8–9): a
`DogPatchService`-style protocol lets `ListingsViewController` depend on "something that can
fetch dogs," never on the concrete client or `URLSession`.

## Controlling persistence in tests

Persistence has its own dedicated guidance in `persistence.md` — this file does not repeat it,
only reaffirms the same posture: business logic depends on a repository *protocol*, and unit
tests substitute an in-memory fake repository (no real SwiftData/Core Data/CloudKit involved).
Separately, testing the persistence layer's own behavior (fetch descriptors, migrations, cascade
deletes) uses a real in-memory store (`ModelConfiguration(isStoredInMemoryOnly: true)` for
SwiftData, an `NSInMemoryStoreType`/`/dev/null`-backed description for Core Data) — that's a
fake in the "real behavior, cheap shortcut" sense, testing the store itself rather than doubling
it away. Both techniques are complementary, not competing choices.

## What NOT to mock

Mock as little, and as lightly, as possible — every mock is a bet that its behavior matches
production closely enough that a passing test still means something. The failure mode is tests
that are "green" because the mock is well-behaved, not because the production code actually
works: a test built around a mock mostly proves the mock does what you told it to, which says
nothing about whether the real collaboration holds up (Testing Swift, ch. 3). Concretely:

- **Don't mock a dependency-free value type.** A plain `struct` with no I/O, no singletons, and
  no hidden state (a `Game`/`User`-style model, a formatting helper, a pure function) should just
  be exercised for real — wrapping it in a protocol and a mock adds indirection without removing
  anything genuinely uncontrollable.
- **Don't mock what you don't own, if you can avoid it.** Reaching directly for a mock of a
  third-party or system type (`UIApplication`, an SDK client) means your test now depends on
  guessing that vendor's real behavior. Prefer defining your own narrow protocol seam in front of
  it (your shape, your contract) and mocking that instead.
- **Don't mock a type with no meaningful behavior of its own** (a dumb data holder) — there's
  nothing to verify by mocking it that a real instance wouldn't already give you for free.
- **Over-mocking couples tests to implementation, not behavior.** A test that asserts on *how
  many times* and *in what order* internal collaborators were called (rather than on the
  observable outcome) breaks on legitimate refactors and stops being a safety net. Assert on
  outcomes; use call-count/argument verification only when the interaction itself — not just its
  result — is the thing under test (e.g., "did we actually send this analytics report").

## Seam-finding in legacy or untested code

Michael Feathers' Legacy Code Change Algorithm (iOS Test-Driven Development, ch. 11, citing
*Working Effectively with Legacy Code*) gives the order of operations when a class has no
test-friendly seam yet:

1. **Identify the change point** — where the new behavior actually needs to live.
2. **Find a test point** — the smallest place you can observe the current behavior.
3. **Break dependencies** — introduce just enough of a seam to substitute a double there.
4. **Write tests** — first characterizing current behavior, then TDD-ing the new behavior.
5. **Make the change.**

**Characterization tests** capture what the code *actually* does today — bugs, quirks, and all —
as a safety net before touching it, not as a correctness judgment. The recipe: exercise the code
in a test, write an assertion you expect to fail, let the failure reveal the real behavior, then
pin the assertion to that behavior. If what you find looks wrong, that's a signal to go get
product/spec clarification, not license to "fix" it silently mid-refactor.

**Finding a seam** means finding the smallest edit that lets a test substitute a dependency,
without a full rewrite. Recurring techniques, roughly in order of how invasive they are:

- Change a hardcoded `let` dependency to an injectable `var`, or add an initializer/property
  parameter with a production default — often enough by itself to let a test swap in a double.
- Extract an inline chunk of a lifecycle callback (`viewWillAppear`, `viewDidLoad`) into its own
  method, so a test can call that method directly instead of driving the full view lifecycle.
- Replace a hardcoded callback into one specific concrete type with an event
  (`NotificationCenter`, a delegate, a Combine/async event) — this decouples the caller from
  needing to know the callee's concrete type at all, which is often what was making both sides
  hard to isolate (iOS Test-Driven Development, ch. 13).
- Replace a caller's hardcoded "call this other screen" behavior with an injected closure or a
  small command-style struct (`title` + `action: () -> Void`) passed in by whichever caller
  configures the view — this is what lets a generic error screen support a "Try Again" action
  without knowing about login, or any other specific caller, at all.

## Map dependencies before refactoring

Before breaking apart a tightly coupled type, map what it depends on directly, and what those
dependencies in turn depend on (secondary/transitive dependencies) — on paper, in a diagram tool,
or as a written list; the format doesn't matter (iOS Test-Driven Development, ch. 12). Then
triage each edge: is it on something structurally central (an app delegate, a singleton) that
can't be pulled along — a hard blocker, not an inconvenience? Is it circular, meaning one side
needs a notification/closure seam before anything can move? Does it drag a large secondary
footprint of its own, signaling the dependency should be simplified first? Does it actually
belong in the same module as what you're extracting, independent of whether it's technically
movable? This triage turns "this class is too tangled to touch" into a concrete, ordered list of
which dependencies to break first — do it before writing the first line of a big refactor.

## Sprout method: adding a feature without a full refactor

When there's no time (or no justification yet) to fully untangle a legacy type, add new
functionality as a new, separately-testable method or extension alongside the old code rather
than threading it through the existing untested logic (iOS Test-Driven Development, ch. 15).
Write the new capability test-first behind its own narrow protocol, even if that means
temporarily near-duplicating a small amount of existing logic instead of reusing an untested
method wholesale. Add the new conformance to the legacy type via a Swift extension, often in its
own file, so the new tested surface stays textually and conceptually separate from the old
untested surface. Wire the real implementation at one composition-root call site — the same
"one call site resolves the concrete type" discipline as ordinary DI. Treat sprouting as a
deliberate, temporary trade: it adds indirection and duplicated logic as debt to be folded back
into a proper refactor later, not a permanent substitute for eventually untangling the type —
used repeatedly with no follow-up, it just relocates the mess instead of reducing it.

## Checklist / classic mistakes

- Track call counts, not a boolean "was it called" flag, in spies/mocks — a `Bool` can't
  distinguish "called once" from "called three times," which is exactly the kind of bug a spy
  should be able to catch (Testing Swift, ch. 3, citing Jon Reid).
- Reset every double's state, and any shared/global state a double touches (singletons, shared
  app-delegate-style state), in teardown — leaked state between tests is one of the most common
  sources of flaky, order-dependent test failures.
- Keep a double's implementation exactly as large as the protocol it conforms to demands — don't
  let a fake accrete production-grade logic; if it needs that much behavior, question whether the
  test should be an integration test instead.
- If a test is flaky, don't reach for a longer timeout as the fix — check first for un-isolated
  shared state, a double that's inadvertently doing real async work, or a genuine race condition.
