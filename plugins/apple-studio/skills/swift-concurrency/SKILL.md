---
name: swift-concurrency
description: Swift 6 concurrency correctness - actor isolation, Sendable conformance, structured concurrency, cancellation, and migrating GCD or Combine code to async/await. Use when writing or reviewing async Swift code, fixing strict-concurrency or Sendable errors, designing actor boundaries, or modernizing callback/Combine code.
---

# Swift concurrency

- Strict-concurrency errors, isolation design, Sendable → `references/strict-concurrency.md`
- Tasks, groups, cancellation, AsyncSequence → `references/structured-concurrency.md`
- Migrating GCD/Combine code → `references/migration.md`

Rules that always apply:
- A strict-concurrency error is a design signal. Diagnose which isolation
  domain the data belongs to BEFORE reaching for @unchecked Sendable,
  @preconcurrency, or nonisolated(unsafe) - those are documented last resorts.
- Every spawned Task needs an owner and a cancellation story.
- Never block an actor (or the main actor) on synchronous waiting.
