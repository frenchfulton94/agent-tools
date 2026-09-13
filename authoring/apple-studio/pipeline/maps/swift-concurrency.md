# Chapter map: swift-concurrency

Targets (Task 4): `strict-concurrency.md`, `structured-concurrency.md`, `migration.md`.

## modern-concurrency-in-swift-v2-0-0.md

- L125–L592: Chapter 1: Why Modern Swift Concurrency? → structured-concurrency.md
- L593–L1218: Chapter 2: Getting Started With async/await → structured-concurrency.md
- L1219–L1788: Chapter 3: AsyncSequence & Intermediate Task → structured-concurrency.md
- L1789–L2268: Chapter 4: Custom Asynchronous Sequences With AsyncStream → structured-concurrency.md
- L2269–L2740: Chapter 5: Intermediate async/await & CheckedContinuation (bridging callback APIs) → structured-concurrency.md
- L3303–L3926: Chapter 7: Concurrent Code With TaskGroup → structured-concurrency.md
- L3927–L4562: Chapter 8: Getting Started With Actors → strict-concurrency.md
- L4563–L5088: Chapter 9: Global Actors → strict-concurrency.md
- L5089–L5718: Chapter 10: Actors in a Distributed System → strict-concurrency.md
- SKIP: Chapter 6: Testing Asynchronous Code (L2741–L3302) — testing-specific; belongs to the swift-testing skill, not one of this skill's three target files. Front matter/license/forums, Conclusion.

## concurrency-by-tutorials-v3-0-0.md

Entirely GCD/Operations-era material (predates async/await) — routes almost entirely to
`## Maintaining older code:` content in migration.md, except the one chapter (Thread
Sanitizer) that is a still-relevant diagnostic tool.

- L141–L236: Chapter 2: GCD vs. Operations → migration.md
- L237–L470: Chapter 3: Queues & Threads → migration.md
- L471–L686: Chapter 4: Groups & Semaphores → migration.md
- L687–L868: Chapter 5: Concurrency Problems (race conditions, deadlock, priority inversion under GCD) → migration.md
- L869–L1078: Chapter 6: Operations → migration.md
- L1079–L1200: Chapter 7: Operation Queues → migration.md
- L1201–L1416: Chapter 8: Asynchronous Operations → migration.md
- L1417–L1632: Chapter 9: Operation Dependencies → migration.md
- L1633–L1802: Chapter 10: Canceling Operations → migration.md
- L1803–L1920: Chapter 11: Core Data (NSManagedObjectContext thread safety under GCD) → migration.md
- L1921–L1992: Chapter 12: Thread Sanitizer (still-relevant race-detection tool, not GCD-specific) → strict-concurrency.md
- SKIP: Chapter 1: Introduction (L105–L140) — generic "what is concurrency" framing, no decision-grade or migration-specific content. Front matter/license/forums, Conclusion.

## swift-concurrency-by-example-2024-11-15-pdf.txt

(PDF text; headings verified with `sed -n '<line>p'` — "Chapter N" line, title on the
following line.)

- L125–L386: Chapter 1: Introduction (concurrency vs. parallelism, threads/queues — foundational isolation-domain reasoning) → strict-concurrency.md
- L387–L2184: Chapter 2: Async/await (incl. continuations — bridging callback APIs) → structured-concurrency.md
- L2185–L3247: Chapter 3: Sequences and streams (AsyncSequence, AsyncStream) → structured-concurrency.md
- L3248–L5863: Chapter 4: Tasks and task groups → structured-concurrency.md
- L5864–L7279: Chapter 5: Actors (isolation, nonisolated, @MainActor, actor hopping/reentrancy) → strict-concurrency.md
- SKIP: Chapter 6: Testing (L7280–L7986) — testing-specific, belongs to swift-testing skill. Chapter 7: Solutions (L7987–EOF) — exercise-solution appendix, no decision-grade content. Front matter.

## combine-asynchronous-programming-with-swift-v4-0-0.md

Per brief: ONLY chapters/sections useful for Combine→async migration; everything else
(pure Combine-operator tutorials: map/filter/combine/time-manipulation/custom
publishers/backpressure/schedulers/testing-Combine) is skipped as out of scope.

- L191–L204: Chapter 1, "Swift's Modern Concurrency" (Combine vs. async/await framing) → migration.md
- L1195–L1248: Chapter 2, "Bridging Combine Publishers to async/await" → migration.md
- L4713–L4834: Chapter 9: Networking (URLSession+Combine extensions — maps to `URLSession.data(from:)` async migration) → migration.md
- L5259–L5276: Chapter 12, "ObservableObject" (Combine-based ObservableObject — what to migrate to the Observation macro) → migration.md
- L5977–L6666: Chapter 15: In Practice: Combine & SwiftUI (ObservableObject, @Published, Environment objects in a real SwiftUI app — the shape of code this skill helps migrate away from) → migration.md
- SKIP: Chapters 3–8, 10–11, 13–14, 16–20 (operator API walkthroughs, debugging, timers, KVO, resource management, error handling, schedulers, custom publishers/backpressure, testing Combine code, building a complete app) — tutorial/API-walkthrough content, not migration-relevant. Front matter/license/forums, Conclusion.
