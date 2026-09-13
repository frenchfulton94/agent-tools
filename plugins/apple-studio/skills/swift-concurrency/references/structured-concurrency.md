> verified: 2026-08 against https://developer.apple.com/documentation/swift/taskgroup.md, https://developer.apple.com/documentation/swift/task.md, https://developer.apple.com/documentation/swift/taskpriority.md, https://developer.apple.com/documentation/swift/asyncstream.md, https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
> sources: Modern Concurrency in Swift, Swift Concurrency by Example

## Ownership framing

Before writing any spawned unit of work, answer two questions: who owns this task's
lifetime, and what cancels it? Structured constructs (`async let`, `TaskGroup` children)
answer both automatically — their lifetime is bound to the enclosing scope, and cancelling
or exiting that scope cancels/awaits them for you. Unstructured constructs (`Task { }`,
`Task.detached`) answer neither automatically — you must store a handle and cancel it
yourself, or accept that the work runs to completion regardless of what triggered it
(Book, ch. 2; Book, ch. 4).

Default to structured concurrency (`async let`, `TaskGroup`) whenever the calling scope
can simply wait for the result. Reach for a standalone `Task` only when you need one of:
a bridge from synchronous code (button actions, delegate callbacks) into `async`, a stored
handle to cancel or await later from elsewhere, or a deliberate actor-context hop. Treat
`Task.detached` as close to never — it forfeits priority inheritance, task-local values, and
actor isolation from the caller, and nearly every case people reach for it turns out to be
solvable with a plain `Task` or `async let` (Book, ch. 4).

Critical distinction, because it's the one people get backwards: a plain `Task { }` created
inside an already-running task inherits that task's priority, actor context, and task-local
values — but is **not** structurally cancelled when the enclosing task is cancelled; only
genuinely structured children (`async let`, `TaskGroup`/`ThrowingTaskGroup` `addTask`) get
automatic cancellation propagation. If a spawned `Task { }` needs to stop when its context
goes away, store the handle and cancel it explicitly — a `Task.isCancelled` check inside it
reads its *own* cancellation flag, not the enclosing task's; there's no ambient inheritance of
cancellation itself, only of priority/actor/task-locals.

## Task ownership in SwiftUI

- View-scoped async work belongs in `.task { }` (or `.task(id:)`), not `.onAppear` plus a
  manually stored `Task`. The modifier ties the task's lifetime to the view's identity: it
  starts on appear and cancels on disappear, with no bookkeeping required. Reserve
  `.task(id:)` for work that should restart when some `Equatable` value changes (selected
  filter, logged-in user) — SwiftUI cancels the old task and starts a new one for you
  (Book, ch. 4).
- Work triggered from a button action or other synchronous closure has no enclosing task
  to inherit a cancellation story from, so if it needs to be cancellable (e.g., a "Cancel"
  button, or a screen the user can navigate away from mid-download), store the `Task` as
  `@State` and cancel it explicitly at the point that should stop the work — `onDisappear`,
  a cancel button, or both (Book, ch. 2; Book, ch. 3).
- A `Task { }` created from a synchronous main-thread context defaults to `.high` priority
  and inherits the actor context it started on, so it runs on the main actor until its first
  `await`, then may hop off. Prefer annotating the owning method/type `@MainActor` for
  post-suspension UI mutations over sprinkling `await MainActor.run { }` calls, which
  fragment control flow (Book, ch. 1; Book, ch. 2).
- Prefer collecting several independent, view-scoped async calls into one `.task { }` using
  `async let` rather than two separate `.task` modifiers — this keeps a single cancellation
  point and avoids subtly different lifetimes for calls that conceptually belong together.

## Cancellation discipline

Cancellation in Swift concurrency is cooperative: calling `cancel()` (or a parent scope
exiting) only flips a flag. Nothing stops running code until it chooses to check that flag.
Treat every `async` function you write as needing an explicit answer to "what do I do when
I've been cancelled?" — silently ignoring it means wasted work, not a bug that shows up
immediately (Book, ch. 3; Book, ch. 4).

Two checking primitives, chosen by what should happen next:

- `try Task.checkCancellation()` — throws `CancellationError`, letting normal error
  propagation unwind the call stack. Use this as the default when "stop and let the error
  bubble" is the correct behavior.
- `Task.isCancelled` — a plain `Bool`. Use it when cancellation should produce a specific
  fallback (a default value, a partial result) rather than a thrown error, or when you need
  to run cleanup before returning.

Placement matters more than exhaustiveness: check after each `await` that does real work (a
network call, a decode, a batch of an iteration), not before trivial synchronous steps. Many
system APIs (`URLSession` data/bytes calls, `Task.sleep`) already check cancellation
internally, so an explicit check is often only needed *after* such a call returns, to avoid
further unnecessary work with data that's no longer wanted (Book, ch. 4). For CPU-bound loops
with no natural suspension point, call `await Task.yield()` periodically — after producing a
unit of result, not every iteration, or yielding overhead can rival the work itself
(Book, ch. 4).

`CancellationError` thrown from user-facing code is usually not an error the user should
see — catch and ignore it (`catch is CancellationError { }`) at the boundary where you
present alerts, rather than letting a generic catch surface "The operation was cancelled"
as if it were a failure.

Priority is a scheduling hint, not a lifetime or ordering guarantee — don't use it as a
substitute for real cancellation or sequencing logic. Swift also *escalates* priority
automatically in two situations: when a higher-priority task awaits a lower-priority one
(the awaited task is bumped to match), and when a higher-priority task is enqueued onto an
actor where a lower-priority task is already running. Design implication: you generally
don't need to hand-tune priorities to avoid priority inversion — just don't fight the
escalation by working around `await` (Book, ch. 4).

## async let vs. Task vs. TaskGroup

Pick based on shape of the work, in this order of preference:

1. **`async let`** — default choice for a fixed, statically-known set of concurrent
   operations (two or three parallel requests you're going to consume together). Each
   binding starts executing immediately at its declaration, not at first `await` — this is
   the most commonly missed detail, and it's why sequential `async let` lines run in
   parallel with the rest of the enclosing scope while a sequence of plain `await` calls
   does not (Book, ch. 2; Book, ch. 4). Bindings can each return a different type for free.
   Trade-off: no handle to cancel a single binding independently, and no way to pass the
   underlying work to another function — you can only await it in the scope that declared it.
2. **`Task`** — when you need a handle: to cancel later, to pass to another scope, or to
   bridge a synchronous context into `async`. Every task in a group must return the same
   type; a plain `Task<Success, Failure>` has no such constraint.
3. **`TaskGroup` / `ThrowingTaskGroup`** — when the amount of concurrent work is dynamic
   (unknown array length, work discovered at runtime), when you want results as they
   complete rather than in declaration order (a "fastest of N servers wins" pattern via
   `addTask` + `group.next()`), or when you need bounded/batched concurrency (start N,
   backfill one for each completion) that `async let` has no vocabulary for.

A `TaskGroup` needing heterogeneous result types (via an enum wrapper per case) signals the
wrong tool — switch to `async let` if the count is fixed at compile time, which returns
distinct types natively without wrapper boilerplate (Book, ch. 4). For fire-and-forget
children whose individual results don't matter — only "did everything finish, did anything
throw" — use `withDiscardingTaskGroup`/`withThrowingDiscardingTaskGroup` instead of a plain
`TaskGroup`: results are discarded as children finish rather than drained through a
`for await` loop, so the group doesn't accumulate unbounded memory for a large/unbounded
child count.

## TaskGroup canonical patterns

- `withTaskGroup`/`withThrowingTaskGroup` only return once every child has finished — you
  cannot leak a running child out of the closure. Awaiting explicitly, calling
  `group.waitForAll()`, or just exiting the closure (which implicitly awaits stragglers) are
  equivalent; prefer explicit awaiting so a reader can see nothing is silently discarded
  (Book, ch. 4; Book, ch. 7).
- Children complete in **completion order, not insertion order** — never assume the Nth
  value read from the group corresponds to the Nth task added. If order matters, tag each
  task's result with an index/id and sort afterward (Book, ch. 4; Book, ch. 7).
- Bounded-concurrency batching pattern — start a fixed number of workers, then replenish
  one for each completion, capping in-flight work regardless of total item count:

  ```swift
  await withTaskGroup(of: Result.self) { group in
      var index = 0
      for _ in 0..<batchSize where index < total {
          group.addTask { await worker(index) }; index += 1
      }
      for await result in group {
          handle(result)
          if index < total {
              group.addTask { [index] in await worker(index) }
              index += 1
          }
      }
  }
  ```

- An uncaught `throw` inside a child does **not** cancel siblings by itself — cancellation
  only fires when you observe that failure, via `group.next()` or a `for try await` loop.
  A group whose children you never iterate can fail silently without cancelling anything.
  If fail-fast behavior on first error is what you want, make sure you're actively looping
  over the group (Book, ch. 4).
- `addTask(...)` always adds a task, even to an already-cancelled group. Use
  `addTaskUnlessCancelled(...)` (returns `Bool`) when adding tasks in response to
  completions after a possible `cancelAll()`, so you don't keep growing a group that's
  already winding down (Book, ch. 4; Book, ch. 7).
- `cancelAll()` is cooperative like any other cancellation — it does nothing to children
  that don't check for cancellation, and it never un-does work already completed. Pair it
  with `checkCancellation()`/`isCancelled` inside each child, not as a substitute for it.
- Never mutate shared, non-isolated state (a plain class property, a top-level `var`) from
  inside child task bodies — that's a data race that will often pass silently in Debug and
  crash in Release. Collect results through the group's `AsyncSequence` conformance
  (`for await`/`reduce`) in the synchronous body around the group instead, or isolate the
  shared state behind an actor (Book, ch. 7).
- Give background/bulk group children a lower explicit priority
  (`.addTask(priority: .medium)`) when the group runs alongside UI-facing updates on the same
  context, or the scheduler may starve quick UI partials behind bulk work, making progress
  indicators appear frozen (Book, ch. 7).

## AsyncSequence design

- Adopting `AsyncSequence` requires only: an `Element` type, a `next() async throws ->
  Element?` on the iterator, and `makeAsyncIterator()`. The protocol then gives you
  `map`/`filter`/`prefix`/`reduce`/etc. for free, mirroring `Sequence` (Book, ch. 3).
- Contract that's easy to violate in a hand-rolled iterator: **once `next()` returns `nil`
  (or throws), every subsequent call must also return `nil`.** Consumers (including the
  standard `for await` desugaring) rely on this; an iterator that "comes back to life" after
  signaling completion is a classic source of hard-to-reproduce bugs (Book, ch. 3).
- Whole-sequence operations (`allSatisfy`, `min`, `max`, `reduce`, `contains`) must consume
  every element before returning, so they will never return on an infinite/unterminated
  sequence — don't call them on a live stream that has no natural end.
- Prefer wrapping an existing push-based API (delegate callbacks, `NotificationCenter`) as
  an `AsyncStream` over writing a custom `AsyncIteratorProtocol` type by hand — the custom
  route is appropriate mainly when the sequence has meaningful internal state machinery
  (e.g., polling with backoff, deduplicating against a previous value) that doesn't fit the
  stream's single-closure shape.
- Reading the *same* `AsyncSequence`/`AsyncStream` instance concurrently from multiple
  `Task`s **divides** elements between readers non-deterministically — it is not a
  broadcast/fan-out. If every subscriber must see every value, an `AsyncStream` alone is
  the wrong tool; reach for a Combine publisher or a hand-built actor-based fan-out instead
  (Book, ch. 3).
- For composition beyond `map`/`filter`/`prefix` (debounce, throttle, merge, zip), use the
  `swift-async-algorithms` package rather than reimplementing these — they're easy to get
  subtly wrong around cancellation and timing.

## AsyncStream / AsyncThrowingStream design

- Two constructor shapes, chosen by the shape of the source: the **unfolding** initializer
  (closure returns the next value or `nil`) fits naturally pull-based sources — polling,
  timers, anything you'd otherwise write as a `while` loop. The **continuation** initializer
  (closure receives a `Continuation` you `yield(_:)`/`finish()` into) fits push-based
  sources — delegate callbacks, notifications, anything that hands you values on its own
  schedule (Book, ch. 4).
- `continuation.finish()` is the *only* end-of-stream signal for the continuation variant —
  omit it and a consuming `for await` loop simply never terminates. Any `yield` called after
  `finish()` is silently dropped, not queued or erroring (Book, ch. 3; Book, ch. 4).
- Buffering policy is a load-shedding contract — pick deliberately, not by leaving the
  default: `.unbounded` (default) is fine only when the producer can't outpace the consumer
  or volume is bounded, else unbounded memory growth is the failure mode; `.bufferingNewest(n)`
  drops the *oldest* value on overflow, matching "only current state matters" streams (live
  prices, progress percentages); `.bufferingOldest(n)` drops *new* values once full,
  effectively backpressuring the producer, matching "don't lose events, ok to lag and catch
  up" streams (command/event queues); buffer size `0` (`.bufferingOldest(0)`) keeps a value
  only if something is actively awaiting `next()` at the moment it's yielded, for "only
  changes from *now* on" semantics like a filesystem watcher that shouldn't replay history to
  a late subscriber (Book, ch. 3).
- `AsyncThrowingStream`'s `continuation.finish(throwing:)` ends the stream after already-
  yielded values have been delivered — decide deliberately whether a given failure should
  end the whole stream (`finish(throwing:)`) or just be skipped so the stream continues.
- The unfolding initializer accepts an `onCancel` closure, invoked when the consuming task
  is cancelled — use it for cleanup (removing observers, closing sockets) that must run
  even if no one ever iterates to a natural `nil`/`finish()`.
- Prefer the static `AsyncStream.makeStream(of:bufferingPolicy:)` factory (returns a
  `(stream:, continuation:)` tuple directly, no closure) over the closure-based continuation
  initializer whenever the continuation needs to be stored as a property on a type rather than
  captured inline — it avoids the awkwardness of escaping a continuation out of an initializer
  closure via a `var` captured by reference. `AsyncThrowingStream` offers the equivalent
  factory.

## Bridging callback-based APIs via continuations

- Two continuation families: `CheckedContinuation`/`withCheckedContinuation` (runtime
  verifies exactly-once resume, logs misuse) and `UnsafeContinuation`/
  `withUnsafeContinuation` (identical API, no runtime check). Default to Checked always;
  treat Unsafe as a micro-optimization to reach for only after profiling shows the checking
  overhead matters — which in practice is close to never in application code (Book, ch. 5).
- The one inviolable rule: **resume exactly once per continuation, on every code path.**
  Zero resumes leaks the continuation — the awaiting task hangs forever and the runtime
  logs "…leaked its continuation!"; two or more resumes is a hard crash, by design, because
  silently ignoring the second resume would hide a real bug (Book, ch. 3; Book, ch. 5).
- Classic mistake: an early-return, an `else` branch, or a `nil`-coalescing default inside
  the wrapped callback that quietly skips calling `resume`. Audit *every* branch of the
  callback closure for a reachable `resume` call — don't just verify the happy path
  compiles (Book, ch. 3).
- Single-callback completion-handler APIs: wrap the call directly inside
  `withCheckedThrowingContinuation`, resuming from within the completion closure. When the
  wrapped API's callback signature allows implausible states (e.g., both result and error
  `nil`, or both non-`nil`), handle every combination explicitly rather than force-unwrapping
  — you don't control what the API might someday send (Book, ch. 5).
- Multi-callback delegate APIs (success/failure via separate delegate methods): stash the
  continuation as a property on the owning type when starting the operation, resume it from
  whichever delegate method fires, and nil out the property immediately after — so a delegate
  firing twice becomes a harmless no-op instead of a crash (Book, ch. 5).
- Add a `deinit` safety net that resumes any still-pending continuation with a
  `CancellationError` if the owning object deallocates before any delegate callback fires —
  otherwise re-triggering the operation on a fresh instance, or simply navigating away, leaks
  the earlier continuation permanently (Book, ch. 5).
- Continuations themselves are thread-safe to resume from any thread/queue the wrapped API
  happens to call back on — no extra synchronization is needed around `resume`. What still
  needs care is any `self` capture *inside* the continuation body: if that code touches
  actor-isolated state, route it through the correct actor same as any other async code.
