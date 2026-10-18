# The memory model in detail

From *Rust Atomics and Locks* ch. 2–3 and 7 (Mara Bos, written for Rust 1.66). Results marked *measured* were run on rustc 1.97.1, aarch64-apple-darwin (Apple M4 Pro), release mode.

## Contents

- [Happens-before](#happens-before)
- [Relaxed and the total modification order](#relaxed-and-the-total-modification-order)
- [Release and acquire](#release-and-acquire)
- [Which store did I synchronize with](#which-store-did-i-synchronize-with)
- [Release sequences](#release-sequences)
- [SeqCst](#seqcst)
- [Fences](#fences)
- [compiler_fence and process-wide barriers](#compiler_fence-and-process-wide-barriers)
- [Consume does not exist](#consume-does-not-exist)
- [Misconceptions](#misconceptions)
- [Measured litmus tests](#measured-litmus-tests)

## Happens-before

The model defines only happens-before relations. It says nothing about caches, timing, or instructions. Two operations not related by happens-before are unordered, and a thread may observe their effects in either order.

Sources of happens-before, the complete list:

1. Program order within one thread.
2. `thread::spawn`: everything before the spawn happens before everything in the new thread.
3. `join`: everything in the thread happens before everything after the `join` returns.
4. Mutex unlock happens before the next lock of the same mutex.
5. An acquire operation that reads a value written by a release operation (or by a later RMW in that release sequence).
6. The single total order of `SeqCst` operations.
7. Fences, under the rules below.

**`Relaxed` alone never creates a cross-thread edge.** A wake (futex wake, `unpark`, `notify_one`) is not on the list either. Data is published by the atomic or mutex that the woken thread then checks, never by the wake itself.

*Spawn and join in action (the book's Figure 3-2, in words):* main stores 1 to `X`, spawns a thread, stores 2, joins, then stores 3. The spawned thread loads `X`. Arrows run from the spawn to the load and from the load to the join, but none between the load and "store 2". The load therefore sees 1 or 2, never 0 or 3, even with every operation `Relaxed`.

## Relaxed and the total modification order

Every atomic variable has a **total modification order** that all threads agree on, whatever the ordering. Relaxed guarantees this and nothing more.

- One thread does `fetch_add(5)` then `fetch_add(10)`, so the order is 0 → 5 → 15. A thread that loads it four times may print `0 0 0 0`, `0 0 5 15`, `0 15 15 15`, but never `0 5 0 15` (going backwards) or `0 0 10 15` (10 is not in the order). Successive loads by one thread never go backwards.
- Two threads each do one `fetch_add` (5 and 10). The order is 0 → 5 → 15 or 0 → 10 → 15. If any thread observes 10, no thread observes 5.
- Across **two** variables, Relaxed promises nothing. In the book's Figure 3-1, thread A does `X.store(10)` then `Y.store(20)`, and thread B does `Y.load()` then `X.load()`, all Relaxed. B may print `0 20`, an outcome no interleaving produces: reading 20 from `Y` does not make A's earlier store to `X` visible.

What Relaxed is enough for: a stop flag that publishes nothing else, a statistics counter, ID allocation, the refcount *increment*, a "someone is waiting" hint that a mutex already orders. Several Relaxed counters (`num_done`, `total_time`, `max_time`) read together are not a consistent snapshot: the reader can see a new total with an old count. Put them under one `Mutex` if they must agree.

Out-of-thin-air values (a cycle of Relaxed load-then-store in two threads, formally allowed to "invent" 37) are a known defect of the formal model. They do not happen in practice. Do not reason about them.

## Release and acquire

`Release` applies to stores, `Acquire` to loads. On an RMW (`swap`, `fetch_*`, `compare_exchange`), `Acquire` applies to its load part and `Release` to its store part, and `AcqRel` gives both. When an acquire load reads the value a release store wrote, the store and everything before it in its thread happen before the load and everything after it.

*The publish pattern (Figure 3-3, in words):* the producer stores 123 to `DATA`, then release-stores `true` to `READY`. The consumer acquire-loads `READY` repeatedly. The loads that return `false` get no arrow. The one that returns `true` gets an arrow from the release store, and that path (store `DATA` → release store → acquire load → load `DATA`) is what guarantees the consumer reads 123. Because happens-before now separates the two accesses, `DATA` need not even be atomic.

*Locking (Figure 3-4, in words):* each thread changes `LOCKED` from false to true with acquire ordering, accesses the data, and stores false with release ordering. The arrow runs from one thread's release store of `false` to the next thread's acquire operation that read that `false`, which chains every holder of the lock. The failure ordering of the lock attempt is `Relaxed` because a failed attempt touches nothing.

*Lazy init through a pointer (Figure 3-5, in words):* threads A and B both load null and both allocate. A's compare-exchange from null to its pointer succeeds with release ordering. B's compare-exchange fails, loads A's pointer with acquire ordering, frees B's box, and uses A's. A third thread C acquire-loads A's pointer. Arrows run from A's release CAS to B's failed CAS and to C's load, so all three use A's fully initialised box. Both places that can load a non-null pointer (the plain load and the **failed** CAS) need `Acquire`. The only store (the successful CAS) needs `Release`. The failure ordering (`Acquire`) is stronger than the success ordering (`Release`), which is allowed since Rust 1.64 (*measured* on 1.97.1).

## Which store did I synchronize with

Equal values are different events. Each store is its own point in the modification order, and an acquire load synchronizes with the store whose point it read. Take the order: 0, a release store of 7 by thread one, a Relaxed store of 6, a release store of 7 by thread two. An acquire load of 7 synchronizes with one of the two sevens. If the loading thread has already, in happens-before, seen the 6, it must have read the later 7 and synchronizes with thread two only.

## Release sequences

After a release store, any number of **RMW** operations of any ordering may modify the variable. An acquire load that reads the result of any of them still synchronizes with the original release store. Take the order: 0, release store 7, Relaxed `fetch_add` → 8, release `fetch_add` → 9, release store 7, Relaxed `swap` → 10.

- An acquire load of 9 synchronizes with the `fetch_add` that wrote 9 and with the first store of 7, despite the Relaxed RMW between them.
- An acquire load of 10 (written by a Relaxed swap) synchronizes with the second store of 7 only.
- The plain store of 7 **breaks** the chain. Only RMWs continue a release sequence (the C++20 definition, which Rust follows).

This is why `Arc` can decrement with `Release` and fence only on the final decrement: every earlier decrement is an RMW, so the last thread's acquire reaches all of them.

## SeqCst

`SeqCst` is `Acquire` on loads, `Release` on stores, plus membership in one global order of all `SeqCst` operations that every thread agrees on. A `SeqCst` store pairs with an `Acquire` load, and a `SeqCst` load with a `Release` store, but only the relation between two `SeqCst` operations is guaranteed consistent with the global order.

The one pattern that needs it is a store followed, in the same thread, by a load of a **different** variable, where the store must be visible before the load (store buffering, or Dekker):

```rust
// thread a                               // thread b
A.store(true, SeqCst);                    B.store(true, SeqCst);
if !B.load(SeqCst) { /* critical */ }     if !A.load(SeqCst) { /* critical */ }
```

At most one thread enters (possibly neither). With `Release`/`Acquire` both can enter, which was *measured* on ARM64 (see below). `Relaxed` operations with a `fence(SeqCst)` between the store and the load also work, because the two fences are ordered with each other.

## Fences

`fence(Release)`, `fence(Acquire)`, `fence(AcqRel)`, `fence(SeqCst)`. `fence(Relaxed)` and `compiler_fence(Relaxed)` are compile errors through the deny-by-default `invalid_atomic_ordering` lint, and panic at runtime if the ordering is only known then (*measured*).

- `x.store(v, Release)` behaves like `fence(Release); x.store(v, Relaxed)`. `x.load(Acquire)` behaves like `let v = x.load(Relaxed); fence(Acquire)`. The fence form can cost an extra instruction.
- A release fence followed (in its thread) by **any** atomic store, and an acquire fence preceded (in its thread) by **any** atomic load, synchronize if that load reads that store. Fences are not tied to one variable: if thread 1 does `fence(Release)` then Relaxed stores to `A`, `B` and `C`, and thread 2 Relaxed-loads all three then does `fence(Acquire)`, then any one load reading its store is enough.
- Code and branches may sit between the operation and the fence, which allows a **conditional acquire**:

```rust
let p = PTR.load(Relaxed);
if !p.is_null() {
    fence(Acquire); // pay for acquire only when there is something to read
    use_it(unsafe { &*p });
}
```

- **Batch acquire:** load ten `ready` flags with Relaxed, then issue one `fence(Acquire)` if any was true, before reading the corresponding data.
- **A `SeqCst` operation cannot be split into a Relaxed operation plus `fence(SeqCst)`.** The fence joins the global order and the Relaxed operation next to it does not. The Dekker pattern still works with fences on both sides, because the fences order each other.

## compiler_fence and process-wide barriers

`compiler_fence` stops only the compiler. It emits no instruction, so it does not order anything between threads on a weakly ordered CPU. It is correct for:

- Unix signal handlers and embedded interrupt handlers, which run on the same core as the code they interrupt.
- The cheap side of an asymmetric barrier. Linux's `membarrier` syscall and Windows' `FlushProcessWriteBuffers` run a full fence on every running thread of the process. The hot path then needs only `compiler_fence`, and the rare path pays for the syscall. The `membarrier` crate wraps both. This is outside Rust's memory model, and std exposes no such barrier.

The book uses `compiler_fence` deliberately to break a spin lock and expose CPU reordering. The same experiment is in the litmus results below.

## Consume does not exist

Rust has no `Ordering::Consume`. In C++ it orders only operations that depend on the loaded value. No compiler implements it, because optimisations erase dependencies, and compilers silently upgrade it to acquire. In Rust use `Acquire`, or Relaxed plus a conditional `fence(Acquire)`.

## Misconceptions

| Belief | Fact |
|---|---|
| Stronger ordering makes a store visible sooner | The model has no timing. Ordering constrains order only; stronger orderings can be slower |
| A debug build, or an in-order or single-core CPU, avoids ordering problems | The compiler still reorders in debug builds and on any CPU |
| Relaxed is free | Relaxed loads and stores compile to plain loads and stores on x86-64 and ARM64. Contention is not free: a line written by one core and read by others is far slower (see `hardware-and-os.md`) |
| `SeqCst` is the safe default | If any ordering is correct, `SeqCst` is too, but an algorithm can be wrong at every ordering. `SeqCst` also tells a reviewer "this depends on the global order of every SeqCst operation", which is much harder to check than a release/acquire pair on one variable. Treat it as a reason to look harder |
| `SeqCst` gives a release load or an acquire store | Neither exists. A `Release` store does not synchronize with another `SeqCst` store; to order two stores globally, both must be `SeqCst` |
| It is a plain `mov` either way, so a non-atomic access is fine | The data race is undefined behaviour in the model, whatever the instruction. The compiler may split, merge, or delete a non-atomic access |
| I read the value it wrote, so I see everything it wrote before | True only for an acquire load reading a release store (or its release sequence) |

## Measured litmus tests

rustc 1.97.1, `--release`, Apple M4 Pro (aarch64-apple-darwin, whose baseline CPU is apple-m1 with LSE and RCPC). Source in the verification scratch directory, not shipped. These show that the wrong orderings fail on real hardware. A run with zero failures proves nothing.

| Test | Wrong ordering | Result | Correct ordering | Result |
|---|---|---|---|---|
| Message passing, 4M items, `compiler_fence` to stop the compiler reordering | Relaxed / Relaxed | stale `DATA` read in 3 of 13 runs (1, 7, 26 items) | Release / Acquire | 0 in 13 runs |
| Spin lock, 4 threads × 1M increments (the book's ch. 7 experiment) | `swap(Relaxed)` / `store(Relaxed)` + `compiler_fence` | increments lost in 5 of 13 runs (9 to 58 lost) | Acquire / Release | 4,000,000 every run |
| Store buffering (Dekker), 4M rounds | Relaxed | both entered in about half the rounds | | |
| | Release / Acquire (`stlr` + `ldapr`) | both entered in 3 of 20 runs (26, 129, 148 rounds) | `SeqCst`, or Relaxed + `fence(SeqCst)` | 0 in 20 runs |
| Seqlock, 5M writes against 5M reads | all Relaxed, no fences | 2.2M torn reads over 5 runs | the recipe in `primitive-recipes.md` | 0 torn in 25M reads |

The book's own run of the spin-lock experiment found 0 lost increments on x86-64, a 2021 Android phone, and a Raspberry Pi 3, and about 0.4% lost on an Apple M1. Test ordering bugs on ARM64 in release mode, and judge them against the model.
