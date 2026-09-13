> verified: 2026-08 against https://developer.apple.com/documentation/swift/taskgroup.md, https://developer.apple.com/documentation/swift/task.md, https://developer.apple.com/documentation/swift/taskpriority.md, https://developer.apple.com/documentation/coredata/nsmanagedobjectcontext.md, https://developer.apple.com/documentation/combine/publisher.md, https://developer.apple.com/documentation/combine/future.md, https://github.com/apple/swift-async-algorithms, https://developer.apple.com/documentation/swiftui/environment.md, https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro.md
> sources: Concurrency by Tutorials, Combine: Asynchronous Programming with Swift

## Maintaining older code: DispatchQueue.async/sync → Task and actors

A `DispatchQueue.async` closure is almost always standing in for one of two things: "run this off the main thread," or "serialize access to shared mutable state." Diagnose which one before picking a replacement.

- **Off the main thread, no shared state involved**: replace with `Task { ... }` (inherits the caller's actor context) rather than `Task.detached { ... }`. Detached tasks lose priority, cancellation, and task-local inheritance and are rarely what the legacy code actually wanted. `Task.detached(priority:operation:)` is still current when that isolation is genuinely intended.

- **Serialize access to shared mutable state**: replace the queue itself with an `actor`. A private serial `DispatchQueue` guarding `_value` (Concurrency by Tutorials, ch. 5) is structurally identical to an actor's isolated storage — except the compiler now enforces the isolation instead of you remembering to route every access through `queue.sync { }`.

- **`DispatchQueue.main.async` to hop back to the UI**: replace with `@MainActor` isolation on the type/method, or `await MainActor.run { }` at a call site. Prefer isolating the type — sprinkling `MainActor.run` everywhere is the async version of remembering to dispatch back, the same failure mode as GCD.

- **QoS-tagged queues** (`.userInitiated`, `.utility`, `.background`) map to `Task(priority:)` — current `TaskPriority` cases include `.high`, `.userInitiated`, `.medium`, `.low`, `.utility`, and `.background` (plus a couple of deprecated aliases), named to parallel GCD's QoS classes but not formally documented as a 1:1 mapping. The mapping isn't behaviorally 1:1: Task priority is a scheduling hint for the cooperative pool, not a hard queue assignment, though it can still be escalated by awaiters, similar to how GCD QoS was escalated by queue contents.

- **Never translate `sync` literally.** `queue.sync { }` blocking the caller until a closure finishes is exactly what `await` replaces — the async call *is* the "wait for it to finish" primitive. If you see `sync`, make the caller `async` and `await` the work; don't wrap it in a `Task` and block on a semaphore (see below).

- **`DispatchWorkItem.cancel()`**: replace with a stored `Task` handle and `task.cancel()`. The `isCancelled` polling pattern (ch. 3) maps to `Task.isCancelled` / `Task.checkCancellation()` — but structured Tasks propagate cancellation to children automatically, which `DispatchWorkItem` never did.

## Maintaining older code: DispatchGroup → async let / TaskGroup

`DispatchGroup`'s `enter`/`leave`/`notify` dance (ch. 4) exists to solve one problem: "run N things, know when all N are done." Structured concurrency solves this natively, so the manual counting disappears.

- **Fixed, known set of concurrent tasks** ("download these 3 named things"): use `async let` per task, then `await` all of them. No `enter`/`leave` bookkeeping — the compiler tracks in-flight work.

- **Dynamic/homogeneous set** (download every image in an array, the classic `Images.playground` case, ch. 4): use `withTaskGroup(of:returning:body:)` (or `withThrowingTaskGroup` if children can throw), adding one child task per item.

- A `DispatchGroup` wrapping a callback-based API needed manual `enter`/`leave` specifically because the underlying API wasn't structured. If you're migrating that callback API too, convert it to `async`/`await` first (via a continuation) — the group/TaskGroup need then disappears on its own instead of being reproduced.

- **`group.wait(timeout:)`** is a blocking synchronous wait and a documented code smell in the source itself (ch. 4). There is no direct replacement, because there shouldn't be one: the calling function should become `async` and `await` the equivalent, not block a thread to simulate waiting.

## Maintaining older code: semaphores → actor isolation, not a lock

`DispatchSemaphore` shows up in legacy code for two distinct purposes — treat them differently.

- **Rate-limiting concurrent work** ("only 4 downloads at once," ch. 4) maps to a bounded `TaskGroup`: add up to N child tasks, await one, add the next.

  ```swift
  await withTaskGroup(of: Void.self) { group in
      var iterator = items.makeIterator()
      for _ in 0..<maxConcurrent { if let i = iterator.next() { group.addTask { await process(i) } } }
      while await group.next() != nil {
          if let i = iterator.next() { group.addTask { await process(i) } }
      }
  }
  ```

- **Guarding mutable shared state** (using `wait`/`signal` as a lock) is exactly what an `actor` replaces. This use is an anti-pattern under structured concurrency for a sharper reason than style: `DispatchSemaphore.wait()` blocks a thread. Calling it inside a `Task` running on the cooperative pool can starve the pool — a bounded number of worker threads, and a blocked one is unavailable to other tasks, unlike a GCD queue that could spin up more OS threads. **Never call `semaphore.wait()` from inside a `Task`.** Migrate the guarded state to an actor and the semaphore disappears entirely; there's no async-safe semaphore to reach for instead.

- The source material's own framing — semaphores are "an advanced topic that rarely comes up" (ch. 4) — is itself a signal: most semaphore usage in inherited code is solving a serialization problem an actor solves more simply and more safely.

## Maintaining older code: race conditions, deadlock, priority inversion

The GCD-era diagnosis of these three problems (ch. 5) is worth knowing because it clarifies what actor isolation does and doesn't buy you.

- **Race conditions**: actor isolation eliminates data races on the actor's own stored state by construction — the compiler rejects code that lets two execution contexts touch state without going through the actor's serialized access. Strictly stronger than the manual "wrap every access in `queue.sync`" discipline, because the compiler enforces it instead of relying on future editors remembering to.

- **What isolation does NOT eliminate**: check-then-act races across multiple `await` points. The classic warning about `if x.value > 10 && x.value < 20` being unsafe because another thread can mutate between the two reads (ch. 5) has a direct async analog: two separate `await actor.value` reads with an `await` in between are not atomic, because the actor can service other callers between your two awaits. If a sequence of reads/mutations needs atomicity, expose a single actor method that performs the whole sequence internally, rather than composing multiple awaited calls from outside.

- **Deadlock**: classic GCD deadlock (submitting `sync` to the queue you're already running on) mostly can't happen with `await` — there's no thread-blocking wait to deadlock on. Deadlock-shaped bugs still occur through reentrancy and cyclic `await` dependencies between actors (actor A awaits a call that indirectly awaits back into actor A) — structurally the same "cycle in the dependency graph" failure as Operation dependency deadlock (ch. 9), just expressed through await chains instead of `addDependency`.

- **Priority inversion**: still possible with Tasks, but the cooperative scheduler is designed to propagate and escalate priority through `await` chains — a high-priority task awaiting a low-priority one gets that low-priority task scheduled at the higher priority for the duration, per the language's own concurrency documentation — a direct structural fix for the scenario ch. 5's semaphore-based priority-inversion playground demonstrates.

## Maintaining older code: NSOperation/OperationQueue → Task and TaskGroup

`Operation`'s value over GCD was reusability, state tracking (`isReady`/`isExecuting`/`isCancelled`/`isFinished`), cancellation, and dependencies (ch. 6–7). Structured concurrency gives you the first three for free; the fourth needs judgment (next section).

- **Reusable async unit of work** (subclassing `Operation`, overriding `main()`) maps to a plain `async` function or method — there's no need to reproduce the class-with-state-machine shape.

- **`AsyncOperation`**, the hand-rolled KVO state machine required to make an async operation correctly report `isExecuting`/`isFinished` (ch. 8), has no equivalent because it has no purpose anymore. `Task` suspension points (`await`) are the built-in version of "this work isn't done but isn't blocking a thread either." When this class turns up in inherited code, its contents typically collapse into "make the wrapped work `async`."

- **`BlockOperation`** maps to `TaskGroup` (concurrent closures, all must finish) or sequential `await` (if serial order was actually intended — recall `BlockOperation` runs its blocks *concurrently* by default, a common source of legacy bugs when serial order was assumed).

- **`maxConcurrentOperationCount`**: no direct `TaskGroup` equivalent; implement the cap with the admission-control loop shown above, or gate admission through an actor.

- **`isSuspended`** (pause/resume a whole queue): no structured-concurrency equivalent — pausing a `TaskGroup` mid-flight isn't a concept. If a feature genuinely needs pause/resume of a broad batch, that's a case for keeping `OperationQueue` (or building a pause-aware actor gate) rather than forcing a migration.

## Maintaining older code: Operation dependencies have no drop-in equivalent

This is the one area where the migration isn't mechanical — say so plainly when reviewing inherited code.

- **Linear chains** (`opB.addDependency(opA)`, ch. 9) map cleanly to sequential `await`: `let a = await stepA(); let b = await stepB(a)`. Strictly better than the Operation version — the "pyramid of doom" GCD comparison the source makes (ch. 9) is exactly what `await` chains flatten, and dependency data no longer needs a side-channel protocol (the `ImageDataProvider` pattern) to pass results between steps; it's just a return value.

- **Fan-out/fan-in** (several operations feed one downstream operation) maps to `async let` for the independent branches, awaited together at the join point.

- **General dependency DAGs** (arbitrary graphs, dynamically constructed, possibly with diamond dependencies) have **no direct structured-concurrency equivalent.** `TaskGroup`/`async let` express tree-shaped structured concurrency, not arbitrary graphs. If inherited code genuinely relies on `OperationQueue`'s general dependency graph — not just a chain or a fan-out — don't force-fit it into nested `TaskGroup`s. Either keep `OperationQueue` for that subsystem, or restructure the workflow (a DAG can often be flattened into a small number of ordered phases, each phase parallel internally).

- **Deadlock check carries over**: a cycle in an `await`-chain "dependency graph" is just as fatal as a cycle in an `Operation` dependency graph (ch. 9) — draw the graph, look for cycles.

## Maintaining older code: canceling operations → structured Task cancellation

- Manual `isCancelled` checks sprinkled through `main()` (ch. 10) map to `Task.checkCancellation()` (throws) or `Task.isCancelled` (poll and branch), used at the same natural checkpoints: before expensive work, before committing a result.

- The ch. 10 judgment call — "you already did the expensive work, is it worth discarding the result on cancellation?" — still applies verbatim and is still yours to make; cancellation is cooperative in both models.

- The structural win: `Operation` cancellation required manually propagating `cancel()` to every child operation and underlying resource (overriding `cancel()` to also cancel a `URLSessionDataTask`, ch. 10). Structured `Task` cancellation propagates to child tasks automatically — a canceled parent `Task`/`TaskGroup` cancels its children without extra propagation code, as long as the children are genuinely structured (`async let`/`TaskGroup`, not detached).

- Classic mistake carried forward: forgetting to check cancellation at all. An `async` function that never calls `Task.checkCancellation()` and never hits a suspension point that checks cancellation runs to completion regardless of the caller cancelling it — the same failure mode as an `Operation` that never checks `isCancelled`.

## Maintaining older code: NSManagedObjectContext confinement → actor-isolated persistence

Core Data's thread-confinement rules under GCD (ch. 11) — never touch a context off the queue that created it, never share an `NSManagedObject` across threads, pass `NSManagedObjectID` instead — map onto Swift concurrency as an isolation problem: a context and its managed objects belong to one isolation domain, and crossing domains needs the same kind of explicit boundary as GCD's `perform(_:)`/`performAndWait(_:)` provided. Modern Core Data offers an `async` `perform<T>(schedule:_:) async rethrows -> T` on `NSManagedObjectContext` that lets you `await` context work directly instead of wrapping the old closure-based `perform(_:)` in a continuation.

This skill covers concurrency correctness, not persistence architecture. For whether to keep Core Data's context-confinement model, move to `@ModelActor`/SwiftData, or wrap persistence behind your own actor, see swift-architecture's `persistence.md`.

## Maintaining older code: Combine Publishers → AsyncSequence / async-await

- **Simple bridging**: any `Publisher` exposes `.values`, an `AsyncSequence` iterable with `for await` (Combine, ch. 2). A `Future` exposes `.value` for a single awaited result. Both are current, still-supported bridging APIs. Reach for this first — most Combine pipelines that only exist to get a value into a `sink` are better expressed as a `for await` loop or a single `await`, with no publisher left at all.

- **Wrapping a still-Combine-only API you don't control**: use a continuation (`withCheckedThrowingContinuation` for a single value, `AsyncThrowingStream` for a stream — construct it via the static `AsyncThrowingStream.makeStream(of:bufferingPolicy:)` factory when the continuation needs to be stored on a type rather than captured in an initializer closure) around a `sink` subscription, resuming/yielding from the Combine callbacks and cancelling the underlying `AnyCancellable` when the async consumer is cancelled or the stream terminates.

- **Networking** (`URLSession.dataTaskPublisher`, Combine ch. 9): migrate directly to `URLSession.data(for:)`/`data(from:)`, decoding with `JSONDecoder().decode(_:from:)` inline. This removes the `.map(\.data).decode(...)` operator dance, since there's no tuple-splitting step needed.

- **`multicast()`/`share()`** for fanning one request out to multiple subscribers (ch. 9's own documented pain point — "Combine, surprisingly, lacks operators to make this easy") has a cleaner async answer: wrap the request in one `Task` and hand that same `Task` (or its cached awaited value) to every caller instead of resubscribing a publisher. An actor caching an in-flight `Task<T, Error>` keyed by request is the idiomatic replacement for connectable-publisher multicasting.

- **When not to migrate reflexively**: the `swift-async-algorithms` package now provides direct `AsyncSequence` equivalents for `combineLatest`, `merge`, `zip`, `debounce`, and `throttle`, so most operator-algebra pipelines do have a terse structured-concurrency answer — check that package before assuming a rewrite means hand-rolled plumbing. What still doesn't have an equivalent is Combine's more exotic backpressure-aware custom-publisher machinery; don't trade a five-line Combine chain for fifty lines of manual `AsyncSequence` code when a `swift-async-algorithms` combinator already covers it, and don't force a migration for the rare pipeline that genuinely needs bespoke backpressure control.

## Maintaining older code: ObservableObject/@Published → the Observation framework

This section covers migration judgment only — Observation mechanics themselves (how `@Observable` tracks reads, `@Bindable`, etc.) belong to swift-architecture's `state-and-di.md`.

- **When to migrate**: a Combine `ObservableObject` whose `@Published` properties exist purely to drive SwiftUI updates (the `ReaderViewModel`/`Settings` shape, Combine ch. 15) is exactly what `@Observable` replaces — with a real behavior change, not just a syntax swap. `objectWillChange` fires on *any* `@Published` change and every observing view re-renders on any change to the object (ch. 15's own caveat: "you can't know which property actually changed"), whereas `@Observable` tracks field-level reads and only invalidates views that actually read the field that changed. For view models with several independent published properties, migrating is a real performance and correctness win, not just cleanup.

- **What doesn't carry over 1:1**: `@Published var x = ...` becomes a plain `var x = ...` — no property wrapper on the fields themselves. `@ObservedObject`/`@StateObject` at the call site become plain `@State` (owning view) or no wrapper (passed-down reference); `@EnvironmentObject var settings: Settings` becomes `@Environment(Settings.self) var settings`, reading by *type* rather than by property-wrapper inference. Injection changes to match: the old `.environmentObject(settings)` becomes `.environment(settings)`. Where a view needs a writable `Binding` into an `@Environment`-sourced `@Observable` object, wrap the read with `@Bindable` at the point of use (`@Bindable var settings = settings` inside the view, then `$settings.someProperty`) rather than expecting `@Environment` itself to hand out bindings.

- **Classic pitfall migrating existing code**: if a Combine model type used `@Published` property piping into other Combine chains for reasons *other than* driving SwiftUI — cross-object reactive binding, not view invalidation (e.g. `userSettings.$keywords.map(...).assign(to:on:)`, ch. 15) — `@Observable` gives you no publisher to replace that chain with. That binding logic needs to move somewhere else (a plain `didSet`, an explicit method call, or a narrow, deliberate Combine publisher kept just for that link), not be dropped silently during a view-layer migration.

- **Mixed codebases**: `@Observable` and `ObservableObject`/Combine can coexist during an incremental migration. Migrate leaf view models first — the ones only used to drive UI — and leave shared model layers that other non-UI code subscribes to via Combine until those subscribers are migrated too.
