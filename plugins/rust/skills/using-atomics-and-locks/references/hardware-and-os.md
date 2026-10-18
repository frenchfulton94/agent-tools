# Hardware and operating system

From *Rust Atomics and Locks* ch. 7–8 (Mara Bos, Rust 1.66), updated by measurement. ARM64 codegen was *measured* with `rustc -O --emit=asm` on rustc 1.97.1 for aarch64-apple-darwin. x86-64 codegen could not be built here (no target std installed) and is **from the book**. std's implementations were read from the source at the `1.97.1` tag.

## Contents

- [Codegen by ordering](#codegen-by-ordering)
- [What the codegen implies](#what-the-codegen-implies)
- [Reading the assembly yourself](#reading-the-assembly-yourself)
- [Caches, contention and false sharing](#caches-contention-and-false-sharing)
- [Waiting on an address: the futex family](#waiting-on-an-address-the-futex-family)
- [pthread, Windows and macOS lock types](#pthread-windows-and-macos-lock-types)
- [How std implements its primitives in 1.97.1](#how-std-implements-its-primitives-in-1971)

## Codegen by ordering

The ARMv8.0 column is the book's (and was reproduced here with `-C target-feature=-lse,-rcpc,-rcpc2`). The "Apple default" column is what aarch64-apple-darwin emits, because its baseline CPU is apple-m1 with LSE (ARMv8.1 atomics) and RCPC.

| Operation | x86-64 (book) | ARMv8.0 | Apple default (measured) |
|---|---|---|---|
| load `Relaxed` | `mov` | `ldr` | `ldr` |
| load `Acquire` | `mov` | `ldar` | **`ldapr`** |
| load `SeqCst` | `mov` | `ldar` | `ldar` |
| store `Relaxed` | `mov` | `str` | `str` |
| store `Release` | `mov` | `stlr` | `stlr` |
| store `SeqCst` | **`xchg`** | `stlr` | `stlr` |
| `fetch_add`, result unused / used | `lock add` / `lock xadd` | `ldxr`/`add`/`stxr`/`cbnz` loop | `ldadd`, `ldaddl` (Release), `ldaddal` (AcqRel) |
| `fetch_or`, `fetch_and`, `fetch_xor`, result used | `cmpxchg` loop (single-bit masks: `lock bts`/`btr`/`btc`) | LL/SC loop | `ldset`, `ldclr`, `ldeor` |
| `fetch_max`, `fetch_min` | `cmpxchg` loop | LL/SC loop | `ldsmax`, `ldumax`, … |
| `swap` | `xchg` | `ldaxr`/`stxr` loop (Acquire) | `swp`, `swpa`, `swpl`, `swpal` |
| `compare_exchange` | `lock cmpxchg` | LL/SC with a `cbnz` retry; `clrex` on mismatch | `cas`, `casa`, `casl`, `casal` |
| `compare_exchange_weak` | `lock cmpxchg` | LL/SC with **no** retry | same `cas*` as strong |
| hand-written CAS loop, or `update` | `cmpxchg` loop | a loop around a strong-CAS LL/SC loop | `cas` loop |
| `fence(Acquire)` | nothing | `dmb ishld` | `dmb ishld` |
| `fence(Release)`, `fence(AcqRel)` | nothing | `dmb ish` | `dmb ish` |
| `fence(SeqCst)` | `mfence` | `dmb ish` | `dmb ish` |
| `std::hint::spin_loop()` | `pause` | `isb` | `isb` |

Other targets differ. Read with `--print target-spec-json` (an unstable flag; `RUSTC_BOOTSTRAP=1` was used only to print it): aarch64-unknown-linux-gnu and -musl are `+v8a,+outline-atomics`, without RCPC, so Acquire loads should be `ldar`, and LLVM routes RMWs through `__aarch64_*` helpers that choose LSE at run time. aarch64-pc-windows-msvc is `+v8a,+neon`, so RMWs are inline LL/SC loops. Check a target with `rustc --print cfg --target <t> | grep target_feature`.

## What the codegen implies

- **x86-64 hides ordering bugs.** Every x86-64 load is already acquire and every store already release; only a store followed by a later load (store buffering) can reorder. Relaxed, Acquire, Release and AcqRel cost the same there. SeqCst costs extra only for stores (`xchg`) and fences (`mfence`). Code with missing Acquire or Release usually passes every test on x86-64 and fails on ARM64.
- **On ARM64, Relaxed is cheaper, and Acquire is no longer the same as SeqCst.** The book says Acquire, Release and SeqCst cost the same on ARM64 because all use `ldar`/`stlr`. With RCPC (every Apple target), an Acquire load is `ldapr`, which may be reordered before an earlier `stlr` to another address, exactly the difference between acquire and SeqCst. The store-buffering test in `memory-ordering.md` caught this on an M4 Pro.
- **`compare_exchange_weak` exists because of LL/SC.** `stxr` can fail spuriously. The weak form has no retry, and the strong form adds one. With LSE, or on x86-64, they are identical. Use `_weak` in a loop that already retries, and the strong form for a one-shot CAS whose failure you act on.
- **Prefer a `fetch_*` method to a CAS loop when one expresses the operation.** A hand-written CAS loop, `update`, or `try_update` is still a loop (*measured* on 1.97.1: a `cas` loop with LSE, a loop around an LL/SC loop without), whereas `fetch_add`, `fetch_or` and `fetch_max` are single instructions with LSE. On x86-64, `fetch_or`, `fetch_and` and `fetch_xor` whose result is used become `cmpxchg` loops, so ignore the result if you can.
- Relaxed loads and stores are plain `mov`/`ldr`/`str`. The difference from a non-atomic access is a compiler contract: a non-atomic access may be split, merged, or removed.
- x86-64 and ARM64 are "other-multi-copy atomic": a store visible to one other core is visible to all. Some architectures, GPUs among them, are not, so two cores can see two stores in opposite orders. The abstract model allows that, so reason with the model, not with "instruction reordering".

## Reading the assembly yourself

```bash
rustc -O --edition 2024 --crate-type=lib --emit=asm f.rs -o f.s      # host target
rustc -O --emit=asm -C target-feature=-lse,-rcpc,-rcpc2 ...           # ARMv8.0-style output on Apple
cargo asm --release crate::path::func                                 # cargo-show-asm
```

Use `#[unsafe(no_mangle)]` (edition 2024) or `#[inline(never)]` to keep functions findable. Always use `-O`: unoptimised code hides reordering and buries the atomics in noise. Compiler Explorer covers targets that are not installed. Benchmarking atomics: call `std::hint::black_box(&A)` once and wrap each load in `black_box`, or the optimiser deletes the loop.

## Caches, contention and false sharing

- Coherence protocols (MESI and its MOESI and MESIF variants) let many cores hold a line in the Shared state, but a writer needs it Exclusive. Caching affects only speed on coherent systems; reordering is what affects correctness.
- **Writing is what costs.** The book's figures: 10^9 Relaxed loads took about 300 ms alone or while another core only loaded the same variable, and about 3 s on an older x86-64 while another core stored to it (M1: 350 → 500 ms; recent AMD: 250 → 650 ms).
- **A failed `compare_exchange`, or a `swap` that writes the same value, still takes the line exclusively.** Spin on `load(Relaxed)` and attempt the RMW only when it looks free (test-and-test-and-set).
- **False sharing:** independent atomics in one cache line slow each other as if shared. *Measured* on an M4 Pro: two threads each doing 5×10^7 `fetch_add` on their own counter took about 350 ms with the counters 8 bytes apart and about 80 ms with them 64 or 128 bytes apart. `sysctl hw.cachelinesize` reports 128 on Apple Silicon, and Intel's spatial prefetcher pulls 64-byte lines in pairs, so pad to 128 on x86-64 and aarch64: `#[repr(align(128))]`, or `crossbeam_utils::CachePadded` (0.8.23: 128 on x86-64, aarch64 and powerpc64; 256 on s390x; 32 on arm and mips; 64 elsewhere).
- The opposite also holds: a lock flag next to the data it guards, as in `SpinLock<T>`, brings the data in with the lock. A packed array of small mutexes can be slower than spaced ones.

## Waiting on an address: the futex family

| Platform | Wait / wake | Sizes | Notes |
|---|---|---|---|
| Linux | `syscall(SYS_futex, addr, FUTEX_WAIT, expected, timeout)` / `FUTEX_WAKE, n` | 32-bit | Stable syscall ABI, so a direct `libc::syscall` is legitimate. Relative timeout on the monotonic clock. `FUTEX_PRIVATE_FLAG` when all users are in one process (then on every operation on that address) |
| Linux, more operations | `FUTEX_WAIT_BITSET` (absolute timeout; bitset `u32::MAX` = plain wait), `FUTEX_REQUEUE`, `FUTEX_CMP_REQUEUE`, `FUTEX_WAKE_OP`, the `_PI` priority-inheritance family (kernel-defined word: owner TID, waiters bit), `futex_waitv` (Linux 5.16, several futexes at once) | | `linux-futex` crate encodes `WAKE_OP` |
| Windows 8+ | `WaitOnAddress(addr, &expected, size, ms)` / `WakeByAddressSingle`, `WakeByAddressAll` | 8, 16, 32, 64-bit | Win32 API via `windows-sys`; the Native API underneath is off limits |
| macOS 14.4+ | `os_sync_wait_on_address(addr, value, size, flags)` / `os_sync_wake_by_address_any`, `_all` (`<os/os_sync_wait_on_address.h>`) | 4 or 8 bytes | Public since macOS 14.4 (SDK header checked). **The book, from 2022, says macOS has no futex; that is stale.** `__ulock_wait`/`__ulock_wake` are private and get apps rejected from the App Store. The syscall ABI is unstable: never issue raw syscalls on macOS or Windows |
| FreeBSD | `_umtx_op` with `UMTX_OP_WAIT_UINT`, `UMTX_OP_WAKE` | 32 or 64-bit | OpenBSD has futex WAIT, WAKE and REQUEUE only; NetBSD has the full set |
| Portable | `atomic-wait` 1.1.0: `wait(&AtomicU32, u32)`, `wake_one`, `wake_all` | 32-bit | On macOS it calls libc++'s `std::atomic::wait` machinery. C++20 has `std::atomic::wait`/`notify_*` |

Every one of them may return spuriously, so loop on the condition. None of them orders memory. Change the atomic before calling wake.

## pthread, Windows and macOS lock types

Wrapping an OS lock in Rust has four traps (book ch. 8), and they apply to any address-sensitive C type:

1. Lock and unlock mutate through `&self`, so the field needs `UnsafeCell`.
2. **Not movable.** pthread types may be registered by address; returning one from `new` moves it. Box it (stable address, but `new` stops being `const`), pin it, or allocate lazily on first use, as std now does.
3. **`mem::forget(guard)` then drop the lock.** Destroying a locked `pthread_mutex_t` may be undefined behaviour, and leaking is safe Rust. `Drop` must cope: std try-locks, and leaks the box if the lock is held (std 1.97.1 source).
4. **Recursive locking.** `PTHREAD_MUTEX_DEFAULT` makes it undefined behaviour, and `PTHREAD_MUTEX_INITIALIZER` gives only the default type. std sets `PTHREAD_MUTEX_NORMAL`, which deadlocks instead.

Further facts that models get wrong:

- `pthread_rwlock_t` must let a thread take a read lock it already holds even with writers waiting, so most implementations prefer readers and can starve writers. `pthread_cond_t` with default attributes times its waits on the wall clock. std's `Condvar::wait_timeout` uses the monotonic clock.
- macOS pthread mutexes are fair (FIFO) by default and slow under contention. `os_unfair_lock` (macOS 10.12+) is a 32-bit unfair lock with no condvar and no rwlock.
- Windows `CRITICAL_SECTION` is recursive: a wrapper must not hand out `&mut T`, since one thread could enter twice and hold two. The same goes for any reentrant lock; std's `ReentrantLock` gives only `&T` and is still unstable (`#![feature(reentrant_lock)]`).
- Windows `SRWLOCK` (Vista+): one pointer, no destroy, movable while unlocked (documented in 2020 at the Rust project's request). A second shared lock on the same thread can deadlock if a writer queued in between. `CONDITION_VARIABLE` pairs with it. Kernel objects (`CreateMutex`, events) are cross-process `HANDLE`s and syscall on every operation.

## How std implements its primitives in 1.97.1

Read from `library/std/src/sys/sync/*/mod.rs` and their `cfg_select!` dispatch at the `1.97.1` tag. The book describes 1.66, when std on Windows still wrapped SRW locks directly.

| Primitive | Linux, Android, FreeBSD, OpenBSD | Windows 8+ | macOS and other Apple | Windows 7 target (`win7` vendor) |
|---|---|---|---|---|
| `Mutex` | futex, the three-state design with 100 spins | futex on a **u8** through `WaitOnAddress` | `pthread_mutex_t` set to `PTHREAD_MUTEX_NORMAL`, lazily boxed (`OnceBox`), leaked if dropped while locked. `size_of::<Mutex<()>>() == 16` (*measured*) | SRW lock |
| `Condvar` | futex notification counter, all Relaxed; no two-mutex check | same as Linux | `pthread_cond_t`, lazily boxed; **panics** if used with two mutexes (*measured*) | `CONDITION_VARIABLE` |
| `RwLock` | futex: 30-bit reader count, readers-waiting and writers-waiting bits, a separate `writer_notify` futex; **writer-preferring** | same as Linux | queue-based (`rwlock/queue.rs`, modelled on SRW and `usync`): spins, then queues waiters on their stacks; writer-preferring, unfair | queue-based |
| `Once`, `OnceLock`, `LazyLock` | futex | futex | queue-based | queue-based |
| `thread::park` | futex, states 0 empty, 1 notified, all-ones parked | futex on a u8 | `dispatch_semaphore` (the source notes `__ulock` is private) | `WaitOnAddress` if present, else `NtWaitForKeyedEvent` |

Consequences:

- **A recursive `read()` can deadlock on every tier-1 platform** when a writer queues between the two reads: the futex lock refuses new readers while writers wait, and the queue lock prefers writers. *Measured* on macOS: the second `read()` hung. std's docs say the policy is OS-dependent and that this "may deadlock". Never take a read lock you already hold.
- `Mutex::new`, `RwLock::new` and `Condvar::new` are `const` (since 1.63), so `static M: Mutex<Vec<T>> = Mutex::new(Vec::new());` needs no `LazyLock`.
- std's `MutexGuard` is `!Send` on every platform, because the pthread backend requires it. A hand-written futex mutex may make its guard `Send`.
- Using a `Condvar` with two mutexes is a bug everywhere, even where it does not panic.
- `size_of` and the layout of std's locks differ by platform, so never transmute them or share them across processes.
