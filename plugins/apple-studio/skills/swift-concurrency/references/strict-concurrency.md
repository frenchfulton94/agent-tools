> verified: 2026-08 against https://developer.apple.com/documentation/swift/concurrency, https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/, https://github.com/swiftlang/swift-migration-guide (DataRaceSafety.md, CommonProblems.md), Swift Evolution SE-0313 (nonisolated stored properties), SE-0327 (actor init/deinit isolation), SE-0337 (incremental migration / @preconcurrency), SE-0430 (sending), SE-0434 (global-actor-isolated stored property nonisolated inference), SE-0461 (nonisolated async function isolation), SE-0466 (default actor isolation), https://developer.apple.com/documentation/swiftui/view, https://developer.apple.com/documentation/xcode/diagnosing-memory-thread-and-crash-issues-early (Thread Sanitizer)
> sources: Modern Concurrency in Swift, Swift Concurrency by Example, Concurrency by Tutorials

## The central idea

A strict-concurrency error is not a compiler nuisance to silence — it is the compiler telling you
it cannot prove which isolation domain a piece of mutable state belongs to. Every fix decision
should start from "who legitimately owns this data and when is it read/written," not from
"what annotation makes the red squiggle disappear." Treat `@unchecked Sendable`,
`@preconcurrency`, and `nonisolated(unsafe)` as documented last resorts for code you cannot
redesign (usually a boundary with unmigrated/C code, or a type genuinely protected by external
synchronization) — not as the first thing you reach for. Reaching for them first converts a
compile-time proof into an unverified promise, and the promise is usually wrong (Modern
Concurrency, ch. 8).

Also reframe the mental model itself: strict concurrency checking is a static proof over
*isolation domains*, not a runtime property of *threads*. Two calls can be "on the same thread"
by coincidence and still be a Sendable violation, and two calls can hop threads constantly while
being fully safe, because they never share unprotected mutable state at the same time (Swift
Concurrency by Example, ch. 1). Debug by asking "which isolation domain owns this," never
"which thread is this running on."

## Isolation domains: the three buckets

Every declaration falls into exactly one of:
- **Non-isolated** (the default for free functions, and the default for `nonisolated` members) —
  callable from anywhere, but for that reason it can never synchronously touch protected state.
- **Actor-isolated** — isolated to a specific actor instance; only code already running on that
  actor can touch it synchronously, everything else needs `await`.
- **Global-actor-isolated** — isolated to a singleton actor like `MainActor` or a custom
  `@globalActor`, identified by type rather than instance.

This three-way split (non-isolated / actor-instance-isolated / global-actor-isolated) is exactly
how the current Swift concurrency model itself describes isolation — it's not a simplification,
it's the actual vocabulary the compiler's isolation checker uses (The Swift Programming Language,
"Concurrency").

**Non-isolated async functions are a special case worth knowing precisely.** Historically
(SE-0338), a `nonisolated` **async** function unconditionally hopped off the caller's actor to run
on a generic executor — unlike a `nonisolated` **synchronous** function, which just keeps running
wherever it was called from. That asymmetry meant an innocuous `await someHelper()` from inside an
actor was a real, silent isolation-boundary crossing. SE-0461 corrects this: a plain `nonisolated`
async function now defaults to running on the *caller's* actor (`nonisolated(nonsending)`),
matching non-isolated synchronous semantics; the old always-switch-off behavior is still available
explicitly as `@concurrent`, for work that genuinely needs to guarantee off-actor execution
(CPU-bound work you don't want serialized behind actor calls). When diagnosing an isolation error
around a call into a `nonisolated` async function, check which of the two the target actually
compiles under before assuming the old blanket hop-off.

## Actors: what they actually protect

An actor serializes access to its own stored state via a runtime-managed serial executor.
Code *inside* an actor's own methods can read/write that state synchronously. Code from
*outside* must `await`, because the call becomes an asynchronous message send that may need
to wait its turn (Modern Concurrency, ch. 8; Swift Concurrency by Example, ch. 5).

Rule of thumb: if the code could legally say `self`, it doesn't need `await`; if it's calling in from
outside the actor's own scope, it does — even for a synchronous method (Swift Concurrency by
Example, ch. 5).

Constants (`let` properties) are exempt from isolation — they're inherently race-free and
readable without `await` from anywhere (Swift Concurrency by Example, ch. 5).

Actors do not support inheritance, `final`, or `override` — design actor hierarchies around
composition and protocols, not subclassing (Swift Concurrency by Example, ch. 5).

## nonisolated and isolated parameters

`nonisolated` opts a method (or computed property) *out* of actor isolation. Use it when a
member provably touches no protected mutable state — a pure function, or one that only reads
constants. This is a real, meaningful signal to the compiler and to future readers: "this code
has nothing to protect," not "stop bothering me" (Modern Concurrency, ch. 8; Swift Concurrency
by Example, ch. 5).

- `nonisolated` stored properties are allowed, not just methods and computed properties. An
  actor's own `nonisolated let` constant has been synchronously accessible from any module
  since SE-0313 (e.g. `public actor BankAccount { public nonisolated let accountNumber: Int }`).
  For a global-actor-isolated value type (`@MainActor struct S`), `let` properties of `Sendable`
  type were already implicitly `nonisolated` within the defining module; SE-0434 (Swift 6.0)
  extends that inference to `var` stored properties of `Sendable` type and lets you write an
  explicit `nonisolated` (no `(unsafe)` needed) to expose them outside the module too. What
  still can't go `nonisolated` is a *computed* property backed by isolated state (or a property
  wrapper / `lazy` property, which Swift treats as computed even when it looks stored).
- A `nonisolated` member can only touch other `nonisolated` state; it cannot silently reach
  into isolated state without `await`, same as any other outside caller.
- `nonisolated` doesn't help with synchronous protocol requirements like `Equatable`/`Hashable`
  that a type must satisfy without suspension — those still need actual non-isolated storage.

The inverse tool is an `isolated` parameter: a free function that takes `isolated SomeActor`
gets synchronous, `self`-like access to that actor's state for the duration of the call, at the cost
of the whole function becoming a suspension point (call it with `await`) even though it isn't
`async` (Swift Concurrency by Example, ch. 5). Use this pattern instead of scattering ad hoc
`await MainActor.run { ... }`/`await someActor.doThing()` calls when a function's entire job is
to operate on one actor's data.

## Reentrancy: the classic actor bug

Actors are not naive mutexes. Every `await` inside an actor method is a suspension point where
the actor can interleave and run a *different* call to itself before resuming the first — this is
reentrancy, and it's intentional, not a bug (Swift Concurrency by Example, ch. 5).

The failure mode: check an invariant, `await` something, then act on state assumed unchanged —
but another call ran to completion in between and invalidated it (classic instance: checking a
cache-in-progress map, awaiting a download, writing the result back as if nothing else touched the
map meanwhile). Mitigation: never assume actor state is unchanged across an `await` inside the
same method — re-check invariants after resuming, or restructure so all mutation for one
"transaction" happens in a single synchronous stretch with no `await` between check and write.

## Sendable: the actual meaning

`Sendable` marks a type as safe to move into a different isolation domain. It's a marker
protocol with no requirements — you're vouching, and the compiler enforces the vouch
structurally wherever it can (Modern Concurrency, ch. 8).

Conformance rules that matter for design decisions:
- A value type is **implicitly** Sendable when every stored property is Sendable — but that
  implicit conformance is only visible *within the defining module*. A public type must declare
  `Sendable` explicitly, because Sendable-ness is part of its public API contract.
- Actors are **always** implicitly Sendable, even if their stored properties aren't, because the
  actor itself is the synchronization mechanism.
- A global-actor-isolated type (e.g. `@MainActor class Foo`) is implicitly Sendable for the same
  reason.
- A reference type (class) can only be validly Sendable if it's `final` and every stored property
  is immutable and itself Sendable — mutable state on a class breaks the guarantee structurally.
- You can suppress an unwanted implicit conformance with an unavailable extension
  (`@available(*, unavailable) extension Foo: Sendable {}`) when a type looks Sendable
  structurally but genuinely isn't safe to share — this is the current, documented mechanism
  (SE-0337).

`@Sendable` (the closure attribute) is the same contract applied to a closure value — required
wherever a closure might run in a different isolation domain than where it was formed, e.g. task
group child closures and `Task.init`'s operation closure (Modern Concurrency, ch. 8).

## Global actors and @MainActor

`@MainActor` is a `GlobalActor` — a singleton actor addressable by *type*, not instance, because
there's only ever one (Modern Concurrency, ch. 9; Swift Concurrency by Example, ch. 5). Its
isolation domain is "the UI," and it serializes onto the main thread.

You can define your own with `@globalActor`: the type must satisfy `GlobalActor` by exposing a
static `shared` instance, and any declaration or whole type annotated `@YourActor` runs on
that actor's executor (Modern Concurrency, ch. 9). This is the right tool for app-wide singleton
state that isn't the UI — a database layer, a persistent cache, an auth-status store — where you'd
otherwise be threading a dependency through the whole app just to keep access serialized.

Design guidance for choosing a global actor vs. a plain actor vs. `@MainActor`:
- If it's UI state, it's `@MainActor` — don't invent a parallel actor for it (SwiftUI-observable
  models should generally be `@MainActor`-isolated even though `View` bodies already run on
  the main actor, because your model's own async work still needs a home) (Swift Concurrency
  by Example, ch. 5).
- If several otherwise-unrelated types need to share one synchronized silo and injecting an
  actor instance everywhere is impractical, a custom global actor groups them without an
  explicit dependency graph (Modern Concurrency, ch. 9).
- If it's local to one owner and doesn't need app-wide singleton access, prefer a plain actor
  instance — global actors are a bigger, harder-to-undo commitment.

One SwiftUI-specific consequence: `View` is declared `@MainActor @preconcurrency protocol View`,
so conforming in a type's *primary declaration* inherits `@MainActor` automatically (no annotation
needed on your own view structs); conforming in an `extension` instead opts out, occasionally
useful for a type that must stay non-isolated but also wants to satisfy `View`.

### Default actor isolation (module/file-wide)

Newer Swift tooling lets a whole module (or file) default to `@MainActor` isolation instead of
annotating everywhere: the `-default-isolation MainActor` compiler flag, or (Swift tools 6.2+)
`SwiftSetting.defaultIsolation(MainActor.self)` in a package target (pass `nil` for explicit
non-isolated default). An explicit `nonisolated` on a declaration always overrides the module
default. This is meant for application code (especially SwiftUI apps) where nearly everything is
UI-adjacent — not recommended for libraries usable from arbitrary isolation domains, or
concurrency-heavy server code, since it silently narrows every unannotated declaration to the main
actor (SE-0466).

## Region-based isolation and `sending`

The compiler doesn't require full `Sendable` conformance to move *every* value across an
isolation boundary — it performs flow-sensitive analysis proving a specific value's ownership
transfers cleanly (no remaining aliases on the source side) even when the value's type isn't
Sendable, which is why non-Sendable values often pass through task groups and `await` calls
without complaint: the compiler proved that particular instance stays in one domain at a time,
not that the type is universally safe.

`sending` (Swift 6.0, SE-0430) on a parameter or return type writes this guarantee explicitly
into a signature — `func resume(returning value: sending T)` or `func fetch() async -> sending T`
— meaning "this specific value, this call, transfers cleanly," enforced by requiring the value be
in a disconnected region and unused by the caller afterward. It's a narrower, call-site-scoped
promise than making the whole type Sendable, often the better fix when a type is used
single-threaded internally but occasionally needs to cross once.

## Diagnosing a strict-concurrency error: the decision procedure

When the compiler rejects code for crossing an isolation boundary, work through this order
before reaching for an escape hatch:

1. **Is this latent isolation?** — i.e., does the *function itself* belong on a specific actor and
   just isn't annotated yet? A free/non-isolated function that immediately awaits into
   `@MainActor` work with a non-Sendable parameter is usually just missing `@MainActor` on
   itself. Annotating the function (not the type crossing the boundary) is very often the entire
   fix, and it's the most common root cause in practice.
2. **Is this a protocol conformance isolation mismatch?** — a protocol with no isolation is
   implicitly non-isolated, but your conforming type is actor-isolated. Fix at the narrowest
   scope that works: isolate just the requirement (`@MainActor func foo()` inside the protocol)
   rather than the whole protocol, unless every plausible conformer is actually MainActor-bound.
   Making the requirement `async` is the other lever — it lets an isolated implementation satisfy
   a non-isolated async requirement, at the cost of async-ifying every call site.
3. **Is this a value that could be `sending` instead of `Sendable`?** — if the type is used
   single-threaded and only needs to transfer once, prefer `sending` at the call boundary over
   making the whole type Sendable.
4. **Does the type actually need to become Sendable?** — only after ruling out 1–3. Prefer, in
   order: give it a global actor (implicit Sendable, no manual synchronization to maintain), make
   it an actor, or make it a genuinely immutable `final` class/struct. Manual synchronization
   (`@unchecked Sendable` over a lock/queue) is the last option, not the first.

## The escape hatches, and when they're actually justified

- **`nonisolated(unsafe)`** — for a single global/static var (or occasionally a stored property)
  manually, correctly synchronized with a lock/queue outside the type system, or provably never
  mutated after a one-time init. It removes compiler checking for that declaration; it doesn't
  make the access pattern safe. No exact external synchronization mechanism to point to means
  this isn't a fix, it's a deferred crash.
- **`@unchecked Sendable`** — for a type using real external synchronization (locks, serial
  queues) the compiler can't see through. Legitimate uses keep the queue/lock — you're not
  removing the synchronization, just telling the compiler you've already handled what it would
  otherwise enforce. Not legitimate: slapping it on a type because migrating it to an actor felt
  like too much work.
- **`@preconcurrency`** — two distinct uses, both about *unmigrated dependencies*, not your own
  design: `@preconcurrency import Module` suppresses Sendable-crossing diagnostics entirely for
  implicitly-non-Sendable types from that module in Swift 5 mode, downgrading to warnings in
  Swift 6 mode (a type the module *explicitly* marks non-Sendable still warns in both modes,
  since that's a deliberate signal, not a migration gap) (SE-0337) — so you aren't blocked on
  someone else's migration. `@preconcurrency SomeProtocol` on a conformance inserts a runtime
  check instead of a compile-time one when a non-isolated protocol you don't own is implemented
  by an isolated type. Both are temporary bridges, not permanent suppressions of your own code's
  issues.

## Actor init and deinit

- **`async` actor initializers have `self` isolated throughout.** From the programmer's point of
  view the whole initializer behaves like an ordinary isolated `async` method — no explicit
  `await` is needed to call other actor-isolated members on `self`. Under the hood the compiler
  implicitly inserts one suspension that hops onto the actor's own executor immediately after all
  stored properties finish initializing, but that hop is invisible; there's no boundary partway
  through the init for you to reason about (SE-0327, "On Actors and Initialization").
- **Synchronous (non-`async`) actor initializers have `self` nonisolated** — as do `nonisolated`
  and global-actor-isolated initializers. Direct stored-property assignment is unrestricted
  throughout, but the *first* non-direct use of `self` on a given path — calling a method, reading
  a computed property, capturing `self` in a closure, passing `self` as an argument — permanently
  decays `self` to nonisolated for the rest of that path; past that point only `let`-bound
  `Sendable` properties stay accessible (SE-0327). Keep a synchronous actor init to straight-line
  property assignment; reach for an `async` init if it needs to call the actor's own isolated
  methods.
- `deinit` is **always** non-isolated, regardless of the type's isolation — there is no way to
  `await` inside a `deinit`. If cleanup needs actor-isolated work, spin an unstructured `Task`
  from `deinit`, but never capture `self` in it — a deinitializing instance whose lifetime gets
  extended by a captured `self` will crash at runtime. Capture only the specific values you need
  (e.g. `Task { [store] in await store.cleanup() }`).

## Detecting races the static checker can't catch

Strict concurrency checking is a compile-time proof; it has nothing to say about correctness
inside code you've told it to stop checking (`@unchecked Sendable`, `nonisolated(unsafe)`,
`@preconcurrency`-bridged code, or any manual lock/queue synchronization). For that code, use
Xcode's Thread Sanitizer (TSan) as a runtime check — it instruments builds to catch actual
concurrent unsynchronized access to the same memory (Concurrency by Tutorials, ch. 12).

Two properties worth remembering when triaging: TSan is *runtime* analysis, so a race that never
actually occurs during your test run won't be flagged even though it's still latent; and it
carries a real slowdown (roughly 2–20x CPU, 5–10x memory), so it's a targeted diagnostic pass, not
something left on for every debug build (Concurrency by Tutorials, ch. 12). It only works on a
64-bit macOS build or Simulator run, not a physical iOS/iPadOS/tvOS/watchOS/visionOS device.
Enable per-scheme (Edit Scheme → Diagnostics → Thread Sanitizer) or `-enableThreadSanitizer YES`
for `xcodebuild`.

Practical use in a strict-concurrency codebase: run TSan specifically against code paths that use
an escape hatch. If the static checker has been told to trust a type or declaration, TSan is your
only remaining line of defense for that code — treat every `@unchecked Sendable` type and every
`nonisolated(unsafe)` declaration as a standing item on your TSan sweep list, not a one-time
check.
