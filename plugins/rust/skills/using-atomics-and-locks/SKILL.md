---
name: using-atomics-and-locks
description: Chooses memory orderings and builds or reviews low-level synchronization in Rust - atomics, Relaxed, Acquire, Release and SeqCst, happens-before, release sequences, fences, compare_exchange versus compare_exchange_weak, fetch_* versus CAS loops, and hand-written spin locks, channels, Arc and Weak, futex-based mutexes, condvars, rwlocks, once and lazy init, seqlocks, and lock-free structures with memory reclamation. Also covers x86-64 and ARM64 codegen, false sharing, futex and its Windows and macOS equivalents, thread parking, std's lock implementations per platform, Send and Sync for such primitives, and testing with loom or Miri. Use when code uses atomics or atomic memory orderings, builds a synchronization primitive or unsafe concurrent structure, or asks whether an ordering is strong enough. Also use for symptoms - lost updates or stale reads only on Apple Silicon or ARM servers, lock-free code that passes on x86 but fails on ARM, a missed wake-up hang, or atomics that slow down as threads are added.
license: MIT
---

# Using atomics and locks

This skill corrects what a capable model gets wrong about memory ordering and hand-built synchronization: orderings chosen by habit (`SeqCst` everywhere, or `Relaxed` because "it's just a counter"), happens-before rules recalled loosely, tests on x86-64 taken as proof, and stale facts about std and the OS.

**Source and basis.** Sourced from Mara Bos, [*Rust Atomics and Locks*](https://mara.nl/atomics/) (O'Reilly, 2023; read in full on 2026-10-17). The book targets Rust 1.66. Its std and OS claims were rechecked against the std source at the 1.97.1 tag, and its ordering and codegen claims were measured on rustc 1.97.1, aarch64-apple-darwin (Apple M4 Pro), in release mode. x86-64 codegen could not be built here and is attributed to the book.

**Scope.** Everyday use of std's `Mutex`, `RwLock`, `Arc`, channels, threads, `OnceLock`/`LazyLock`, guard lifetimes, and async belongs to `writing-rust` and its concurrency-and-async reference. This skill starts where you pick an `Ordering` or write the primitive yourself.

## Choosing an ordering

Decide from the happens-before you need, never from cost or habit. For each atomic operation, name the operation in another thread it pairs with, or state that it needs none.

| Situation | Ordering |
|---|---|
| A counter, statistic, ID, or flag that publishes no other memory (stop flag, progress) | `Relaxed` |
| Publishing data: the writer's last step and the reader's first step | `Release` store, `Acquire` load (or RMW) |
| Taking a lock / releasing it | `Acquire` on the successful lock RMW, `Release` on the unlock store; failure ordering `Relaxed` |
| Reference count | increment `Relaxed`; decrement `Release`, then `fence(Acquire)` only on the thread that reached zero |
| Lazy init through a pointer | load `Acquire`; CAS success `Release`, failure `Acquire` (the failed CAS also loads the pointer) |
| A store that must be visible before a **later load of a different variable** in the same thread (Dekker, store buffering) | `SeqCst` on both, or `Relaxed` with `fence(SeqCst)` between, on both sides. Release/Acquire does not order a store before a later load |
| Acquire only on some paths, or after loading many flags | `Relaxed` loads, then `fence(Acquire)` where the data is used |
| An atomic that is only written while holding a mutex, or read in the order a mutex's unlock → lock already fixes (a futex condvar's counter) | `Relaxed` |

Rules that follow:

- **`SeqCst` is almost never needed.** Treat it in a review as a request to name the store→load pattern it protects. If there is none, the ordering is unanalysed, not safe. Where any ordering would be correct, `SeqCst` is too; where the algorithm is wrong, no ordering fixes it.
- **Use the `fetch_*` method that expresses the operation.** `fetch_add`, `fetch_or` and `fetch_max` are single instructions on ARM64 with LSE; a CAS loop, `update`, or `try_update` stays a retry loop (measured on ARM64; the book shows the same on x86-64). Reserve CAS loops for operations with no `fetch_*`: checked or saturating arithmetic, a conditional update, "increment unless zero".
- **`compare_exchange_weak` inside a retry loop, `compare_exchange` when not looping** or when a spurious failure would change the result. On a failure, reuse the returned value as the next `current`; do not reload.
- **CAS failure ordering** cannot be `Release` or `AcqRel` (a failed CAS does not write). It may be stronger than the success ordering since Rust 1.64: `compare_exchange(null, p, Release, Acquire)` is valid.
- **`fetch_add` and `fetch_sub` wrap on overflow, in debug builds too** (measured), unlike `+`. A counter whose wrap could cause unsoundness needs a CAS loop that checks first, or `abort()` far below the limit, as `Arc::clone` does.

## Corrections to carry into every answer

- **Relaxed never creates cross-thread happens-before.** "I read the value it wrote, so I see everything it wrote earlier" holds only for an acquire load that reads a release store, or a value derived from it by later read-modify-write operations (a release sequence). A plain store breaks a release sequence.
- **There is no release load, no acquire store, and no `Consume`.** `Release` on a load or `Acquire` on a store is a compile error through the deny-by-default `invalid_atomic_ordering` lint, and a runtime panic when the ordering is only known at run time (measured). `fence(Relaxed)` and `compiler_fence(Relaxed)` likewise.
- **A wake never publishes data.** `unpark`, `notify_one` and futex wake order nothing. The waiter must re-check state that was published with Release/Acquire or under a mutex. `park`, `Condvar::wait` and futex wait all return spuriously, so always loop on the condition.
- **An `unpark` before `park` is not lost, and tokens do not stack.** Two `unpark()` calls then two `park()` calls: the second park sleeps (measured).
- **Ordering is not timing.** Stronger orderings do not make stores visible sooner, and a debug build or an in-order CPU does not remove reordering.
- **`compiler_fence` emits no instruction.** It orders nothing between threads; it serves signal handlers, interrupts, and the cheap side of a `membarrier` barrier.
- **On Apple Silicon an `Acquire` load is `ldapr`, not `ldar`** (measured). The book's statement that Acquire costs the same as SeqCst on ARM64 is stale for RCPC targets, and the difference is observable: a Release/Acquire Dekker let both threads in on an M4 Pro.
- **A data race is undefined behaviour even when the CPU instruction is the same.** A Relaxed load and a plain load are both `ldr`/`mov`, but only the atomic one is defined. A seqlock's data must be atomics, even though torn reads are thrown away.
- **More than one atomic is not one atomic.** Two counters read one after the other are not a snapshot. Use a mutex, pack the state into one atomic, or briefly lock one of them with a sentinel value, as `Arc::get_mut` does.

## Reviewing atomic code

Work through every atomic and every `unsafe impl` in the change:

- [ ] Each non-`Relaxed` operation names its partner (this `Release` pairs with that `Acquire` on the same variable, or a fence pair), and each `Relaxed` one says why nothing is published through it.
- [ ] Every `SeqCst` names the store→load pattern it needs; otherwise downgrade it or ask.
- [ ] Each failed CAS path: does it load a pointer or data that is then used? Then its failure ordering needs `Acquire`.
- [ ] CAS loops: `_weak`, with the returned value reused; no `fetch_*` would do the same job; no `fetch_add` where a count of zero must stay zero (`Weak::upgrade`).
- [ ] Pointer CAS: ABA considered, and a reclamation strategy named (refcount, hazard pointers, epochs, or leaking). Pointers kept in `AtomicPtr`, not `AtomicUsize`, so they keep provenance.
- [ ] Counters that can overflow: what happens at wrap, and is it far enough away that concurrent increments cannot reach it before an `abort()`?
- [ ] Blocking: state is changed before the wake; the waiter re-checks in a loop; futex wait is passed the exact value it observed; nothing relies on the wait or wake for memory safety.
- [ ] `Drop` uses `get_mut` (no atomic operations) where `&mut self` proves exclusivity, and drops anything left in `MaybeUninit` or `ManuallyDrop`.
- [ ] Soundness does not depend on a guard's destructor running (`mem::forget` is safe), on a `Condvar` seeing only one mutex, or on a non-reentrant lock never being re-locked by the same thread.
- [ ] Hot atomics written by different threads are on separate cache lines (128-byte alignment on x86-64 and aarch64), and spin loops spin on `load(Relaxed)` before attempting the RMW.
- [ ] It was tested on ARM64 in release mode, or with loom, not only on x86-64.

## Send and Sync for hand-built primitives

`UnsafeCell` is `!Sync`, raw pointers and `NonNull` are neither `Send` nor `Sync`, so these impls are written by hand. Each needs a `// SAFETY:` argument.

| Type | Bound |
|---|---|
| Lock or channel giving one thread at a time access to `T` | `unsafe impl<T: Send> Sync` (not `T: Sync`: exclusive access amounts to sending `T`) |
| Reader-writer lock | `Sync where T: Send + Sync` (readers share `&T`) |
| `Arc<T>`, `Weak<T>` | `Send` and `Sync` where `T: Send + Sync` (shares `T`, and any holder may drop it) |
| Guard that derefs to `T` | `unsafe impl<T: Sync> Sync for Guard<'_, T>`. The auto impl follows the field `&Lock<T>` and only requires `T: Send`: **unsound** for `T` like `Cell<i32>` |
| Guard `Send` | allowed for a futex lock (`T: Send`); std's `MutexGuard` is `!Send` because pthread mutexes must be unlocked by the thread that locked them |
| Type tied to its creating thread (a receiver that the sender unparks) | add `PhantomData<*const ()>` to make it `!Send` and `!Sync` |
| `!Sync` but still `Send` | add `PhantomData<Cell<()>>` (negative impls are unstable) |

Whenever an unsafe `Deref` changes what a type effectively holds, re-derive its auto traits instead of trusting the compiler's. A reentrant lock (`ReentrantLock`, Windows `CRITICAL_SECTION`) may give out only `&T`, never `&mut T`.

## Testing concurrent code

- **Stress tests prove little.** Run them in release mode on ARM64 (Apple Silicon, Graviton), never only on x86-64, and count failures over many runs. Measured on an M4 Pro: a Relaxed spin lock lost increments in 5 of 13 runs, and a Relaxed message pass returned stale data in 3 of 13. A clean run means nothing. Also check that a blocking primitive actually sleeps (count wake-ups); a spinning one passes correctness tests.
- **loom** (0.7.2, stable Rust) explores interleavings and weak-memory outcomes of code written against `loom::sync` and `loom::thread` types behind `#[cfg(loom)]`. Run `RUSTFLAGS="--cfg loom" cargo test --release`; bound large models with `LOOM_MAX_PREEMPTIONS=2` or `3`. Measured: it catches a Relaxed publish ("Causality violation: Concurrent read and write accesses"). Two documented gaps, the first measured: **`SeqCst` loads and stores are modelled as `AcqRel`**, so a correct `SeqCst` Dekker fails under loom while the `fence(SeqCst)` version passes; and it does not explore load buffering, so a pass is not a proof.
- **Miri** detects data races and emulates some weak-memory effects. It needs nightly (`cargo +nightly miri test`; vary schedules with `MIRIFLAGS="-Zmiri-many-seeds"`). It was **not run here**: no nightly is installed. Its README says its weak-memory emulation is incomplete and points to loom for complicated atomic code.
- Read the generated code for the target you ship (`references/hardware-and-os.md`), and judge correctness against the model, not the assembly.

## Stale facts, current answers

| The book (Rust 1.66) or common belief | Rust 1.97.1 (measured or read from source) |
|---|---|
| `fetch_update(set, fetch, f)` | Renamed `try_update`; `fetch_update` is marked deprecated **since 1.99.0** (a `deprecated_in_future` warning on 1.97, which is allow by default). `try_update` and `update` are stable since 1.95. `update` takes a closure returning `T`, not `Option<T>` |
| `const ATOMIC_FALSE: AtomicBool = ..; [ATOMIC_FALSE; 10]` | `[const { AtomicBool::new(false) }; 10]`. Calling an atomic method on a `const` item warns (`const_item_interior_mutations`): it modifies a fresh temporary |
| `static mut DATA: String` + `unsafe { DATA.push('!') }` | Error on edition 2024 ("creating a mutable reference to mutable static"). Use an `UnsafeCell` in a `Sync` wrapper, or `&raw mut` |
| No generic `Atomic<T>` | `AtomicU32` and the rest are now aliases of `Atomic<T>`, which appears in diagnostics, but naming it is still unstable (`generic_atomic`, E0658) |
| Tagging pointers needs `AtomicUsize` | `AtomicPtr::fetch_or`, `fetch_and`, `fetch_ptr_add` and the rest are stable since 1.91 and keep provenance |
| macOS has no futex | `os_sync_wait_on_address` is public since macOS 14.4. std does not use it |
| std locks: SRW on Windows, futex on Linux | Futex on Linux and Windows 8+ (`WaitOnAddress`); pthread mutex and condvar plus std's own queue-based `RwLock` and `Once` on macOS. Per-platform table in `references/hardware-and-os.md` |
| `atomic-wait` 1.x | Still 1.1.0, same API |
| `OnceLock` is unstable | `OnceLock` (1.70) and `LazyLock` (1.80) are stable, and are what to use for blocking one-time init |
| std has a semaphore, or `AtomicPerByte` | Neither exists in std 1.97.1 |

## Where to look

Read at most the file the question touches.

- `references/memory-ordering.md` — when reasoning about whether code is correct: the happens-before sources, the total modification order, release/acquire with the book's figures described in words, which store a load synchronizes with, release sequences, SeqCst, fence rules, `compiler_fence` and process-wide barriers, misconceptions, and the measured litmus results.
- `references/primitive-recipes.md` — when building or reviewing a primitive: verified designs with every ordering justified, and the bugs of the earlier versions, for stop flags and ID allocation, lazy init, the spin lock, one-shot channels, `Arc`/`Weak`, futex wait and wake, the three-state mutex, the condvar, the writer-preferring rwlock, a seqlock, ABA, RCU and memory reclamation, queue-based and parking-lot locks.
- `references/hardware-and-os.md` — when performance or platform matters: codegen per ordering on x86-64 and ARM64, LL/SC versus LSE, cache coherence, contention and false sharing, futex operations and the Windows and macOS equivalents, pthread and SRW pitfalls, and std's implementation of each primitive per platform in 1.97.1.

## Neighbouring skills

- Everyday threads, `Mutex`/`RwLock` usage and poisoning, guard lifetimes, channels, `Arc`, lazy statics, async → `writing-rust`. The general UB list, `UnsafeCell` and aliasing rules, provenance → `writing-rust` and its unsafe-and-ub reference.
- Writing and running the tests themselves → `testing-rust`. Cargo features such as `--cfg loom` in `RUSTFLAGS`, targets and `target-feature` → `using-cargo`. A compile error such as E0277 on a `Send` bound → `fixing-rust-compile-errors`.
