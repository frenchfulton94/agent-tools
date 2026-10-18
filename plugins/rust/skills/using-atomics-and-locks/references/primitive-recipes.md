# Primitive recipes

Final designs from *Rust Atomics and Locks* ch. 2, 4–6, 9 and 10 (Mara Bos, Rust 1.66), rewritten for edition 2024. Every recipe below was compiled and stress-tested in release mode on rustc 1.97.1, aarch64-apple-darwin (Apple M4 Pro), unless marked otherwise. The futex-based ones used the `atomic-wait` crate, still at 1.1.0. Each section ends with the bugs of the earlier versions, because those are what a review should look for.

## Contents

- [Small patterns](#small-patterns)
- [Spin lock](#spin-lock)
- [One-shot channel](#one-shot-channel)
- [Arc and Weak](#arc-and-weak)
- [Futex wait and wake](#futex-wait-and-wake)
- [Mutex](#mutex)
- [Condition variable](#condition-variable)
- [Reader-writer lock](#reader-writer-lock)
- [Seqlock](#seqlock)
- [Lock-free structures and reclamation](#lock-free-structures-and-reclamation)
- [Other designs](#other-designs)

## Small patterns

**Stop flag:** `static STOP: AtomicBool`; the worker loops `while !STOP.load(Relaxed)`; the controller stores `true` with `Relaxed` and joins. Relaxed is enough because the flag publishes no other data. The join supplies the happens-before for anything the worker produced.

**Progress with low latency:** the worker stores progress with `Relaxed` and calls `main_thread.unpark()` after each item. The reporter loops on `thread::park_timeout(Duration::from_secs(1))`. Capture `thread::current()` before spawning.

**Bounded ID allocation:** check before incrementing, so the counter never passes the limit.

```rust
fn allocate_id(next: &AtomicU32, limit: u32) -> Option<u32> {
    next.try_update(Relaxed, Relaxed, |n| (n < limit).then_some(n + 1)).ok()
}
```

Three wrong alternatives. `fetch_add` then `assert!(id < limit)` keeps incrementing on every panicking call and eventually wraps, giving out duplicate IDs. `fetch_add`, then `fetch_sub` and panic when over the limit, is usable: the overshoot is bounded by the number of concurrent callers. `fetch_add` and `abort()` when far past the limit is what `Arc::clone` does.

**One-time init, value is the whole payload:** load; if 0, compute; `compare_exchange(0, new, Relaxed, Relaxed)`; on `Err(k)` return `k`. Use the **strong** CAS: it is not in a loop, and a spurious failure would return 0. Relaxed is correct only because no other memory is published. Publishing a pointer needs the next pattern.

**Racy lazy init through a pointer:** non-blocking. Losers free their allocation.

```rust
fn get_or_init<T>(slot: &AtomicPtr<T>, init: impl FnOnce() -> T) -> &T {
    let mut p = slot.load(Acquire);
    if p.is_null() {
        p = Box::into_raw(Box::new(init()));
        if let Err(winner) = slot.compare_exchange(ptr::null_mut(), p, Release, Acquire) {
            drop(unsafe { Box::from_raw(p) });
            p = winner;
        }
    }
    unsafe { &*p }
}
```

If the initialiser is expensive or must run once, block instead with `OnceLock::get_or_init` or `LazyLock` (std, 1.70 and 1.80).

## Spin lock

```rust
pub struct SpinLock<T> { locked: AtomicBool, value: UnsafeCell<T> }
unsafe impl<T: Send> Sync for SpinLock<T> {}   // T: Send, not T: Sync

impl<T> SpinLock<T> {
    pub const fn new(value: T) -> Self { /* .. */ }
    pub fn lock(&self) -> Guard<'_, T> {
        while self.locked.swap(true, Acquire) {
            while self.locked.load(Relaxed) { std::hint::spin_loop(); } // test-and-test-and-set
        }
        Guard { lock: self }
    }
}

pub struct Guard<'a, T> { lock: &'a SpinLock<T> }   // no public constructor: a Guard proves the lock is held
unsafe impl<T: Sync> Sync for Guard<'_, T> {}        // required; see below
// Deref / DerefMut through `unsafe { &*self.lock.value.get() }` / `&mut *..`
impl<T> Drop for Guard<'_, T> {
    fn drop(&mut self) { self.lock.locked.store(false, Release); }
}
```

- `Sync for SpinLock<T>` needs only `T: Send`. Handing `T` to one thread at a time is sending it. Only a lock that shares `&T` with several threads at once (an rwlock's readers) also needs `T: Sync`.
- The guard's auto `Sync` follows its field `&SpinLock<T>`, which means "`T: Send`". But through `Deref` the guard acts like `&mut T`, so sharing `&Guard` shares `&T`, which is unsound for a `T` like `Cell<i32>` that is `Send` but not `Sync`. Write `unsafe impl<T: Sync> Sync for Guard<'_, T>`, or give the guard a `PhantomData<&'a mut T>`. Whenever an unsafe `Deref` changes what a type effectively holds, re-derive its auto traits.
- Spin on a `load`, then `swap`. A failed `swap` or CAS still takes the cache line exclusively.
- `std::hint::spin_loop()` is a CPU hint (`isb` on aarch64, *measured*; `pause` on x86-64, from std's source), not a yield to the OS. A spin lock pays off only when the lock is held very briefly and the holder is running on another core.
- Earlier-version bugs: `lock(&self) -> &mut T` is sound only while there is no `unlock`. With an `unlock`, the `&mut T` can outlive the critical section, so `unlock` must be `unsafe` with a contract. The guard ties unlocking to the end of the borrow, and use after `drop(guard)` is E0382.

## One-shot channel

Runtime-checked version with a single state byte:

```rust
const EMPTY: u8 = 0; const WRITING: u8 = 1; const READY: u8 = 2; const READING: u8 = 3;
pub struct Channel<T> { message: UnsafeCell<MaybeUninit<T>>, state: AtomicU8 }
unsafe impl<T: Send> Sync for Channel<T> {}

pub fn send(&self, message: T) {
    if self.state.compare_exchange(EMPTY, WRITING, Relaxed, Relaxed).is_err() {
        panic!("can't send more than one message");
    }
    unsafe { (*self.message.get()).write(message) };
    self.state.store(READY, Release);
}
pub fn is_ready(&self) -> bool { self.state.load(Relaxed) == READY }
pub fn receive(&self) -> T {
    if self.state.compare_exchange(READY, READING, Acquire, Relaxed).is_err() {
        panic!("no message available");
    }
    unsafe { (*self.message.get()).assume_init_read() }
}
impl<T> Drop for Channel<T> {
    fn drop(&mut self) {
        if *self.state.get_mut() == READY { unsafe { self.message.get_mut().assume_init_drop() } }
    }
}
```

- The claim (`EMPTY` → `WRITING`) is Relaxed: the modification order alone guarantees one winner, and it publishes nothing. The `Release` store of `READY` and the `Acquire` CAS in `receive` publish the message.
- `is_ready` can be Relaxed only because `receive` does its own acquire. If `is_ready` were the synchronising load, it would need `Acquire`.
- `Drop` takes `&mut self`, which proves no other thread can see the value: use `get_mut` on the atomic and the cell, with no atomic operations.
- Earlier-version bugs: a second `send` races the reader and the other sender. A second `receive` duplicates a non-`Copy` `T` (`assume_init_read` is a bitwise copy). Receive-before-ready reads uninitialised memory. A missing `Drop` leaks an unreceived message, because `MaybeUninit` never drops its contents. A `ready` flag alone cannot stop two concurrent senders, since it says a send finished, not that one started. A reliable panic beats undefined behaviour.
- **Type-level version:** split into `Sender<T>` and `Receiver<T>` whose `send(self, ..)` and `receive(self)` take `self` by value, so a second call is E0382. Shared state lives in an `Arc<Channel<T>>`.
- **Borrowing version:** `fn split<'a>(&'a mut self) -> (Sender<'a, T>, Receiver<'a, T>)`. Start `split` with `*self = Self::new();`, because after both endpoints are dropped or forgotten the borrow ends and `split` can be called again on a channel whose state is still `READY`.
- **Blocking version:** the sender stores the receiver's `Thread` and calls `unpark()` after the release store. The receiver loops `while !ready.swap(false, Acquire) { thread::park(); }`. The receiver must be `!Send` (`PhantomData<*const ()>`), or it could move to a thread the sender never unparks. That is a hang, not undefined behaviour.

## Arc and Weak

The book's optimised design, which it describes as nearly identical to std's (std 1.97.1 source checked: the same two counters, the same clone and drop orderings, the `usize::MAX` weak-count lock, and `MAX_REFCOUNT = isize::MAX` with an abort above it).

```rust
struct ArcData<T> {
    data_ref_count: AtomicUsize,   // number of Arcs
    alloc_ref_count: AtomicUsize,  // number of Weaks, plus one for all Arcs together
    data: UnsafeCell<ManuallyDrop<T>>,
}
pub struct Arc<T> { ptr: NonNull<ArcData<T>> }   // NonNull gives Option<Arc<T>> its niche
pub struct Weak<T> { ptr: NonNull<ArcData<T>> }
unsafe impl<T: Send + Sync> Send for Arc<T> {}   // same four impls for Sync, and for Weak
```

| Operation | Ordering | Why |
|---|---|---|
| `Arc::clone` | `fetch_add(1, Relaxed)`, then `abort()` if the old value > `usize::MAX / 2` | The cloner already has access. Abort, not panic, because the count is already too high. `usize::MAX - 1` is not a safe limit: other threads keep incrementing before the abort lands |
| `Arc::drop` | `fetch_sub(1, Release)`; if it returned 1: `fence(Acquire)`, `ManuallyDrop::drop` the data, then drop a `Weak { ptr }` for the implicit weak count | Every earlier use happens before the free, through the release sequence of decrements. A `Relaxed` decrement lets the last thread free data that another thread is still using |
| `Weak::drop` | the same, on `alloc_ref_count`, freeing the `Box` | |
| `Weak::upgrade` | CAS loop: return `None` at 0, `assert!(n <= usize::MAX / 2)`, `compare_exchange_weak(n, n + 1, Relaxed, Relaxed)` | A `fetch_add` could resurrect a count that already reached 0 |
| `Arc::downgrade` | CAS loop on `alloc_ref_count`; spin while it equals `usize::MAX`; success ordering `Acquire` | Pairs with `get_mut`'s release unlock |
| `Arc::get_mut(&mut Self)` | `compare_exchange(1, usize::MAX, Acquire, Relaxed)` on `alloc_ref_count` ("lock" it), Relaxed load of `data_ref_count == 1`, `store(1, Release)` to unlock, then `fence(Acquire)` before returning `&mut T` | Read either counter first without the lock and a concurrent `upgrade` or `downgrade` slips past. A Relaxed lock CAS can miss a fresh upgrade; a Relaxed unlock lets the load see a later `drop` |

- Methods on a `Deref` smart pointer take `arc: &Self` (`Arc::get_mut(&mut a)`, `Arc::downgrade(&a)`) so they never shadow methods of `T`.
- `Arc` gives no `DerefMut`.
- The two-counter trap: a thread looping downgrade, drop the `Arc`, upgrade, drop the `Weak` always holds one of the two, yet a checker reading the counters one after the other can see both "unique". With more than one atomic, a brief spin lock on one of them, like the `usize::MAX` sentinel above, is a legitimate tool.
- std adds what the book omits: `PhantomData<ArcInner<T>>` for drop check, `T: ?Sized`, allocators, and, under ThreadSanitizer, an acquire load instead of the fence, because TSan does not understand fences.

## Futex wait and wake

Every blocking primitive below needs three operations, which the `atomic-wait` crate (1.1.0, unchanged API since the book) provides on Linux, Windows, FreeBSD and macOS:

- `wait(&AtomicU32, expected)` sleeps only if the value still equals `expected`, checked atomically with respect to wakes, so a wake between your check and the sleep is never lost. It **may return spuriously**.
- `wake_one(&AtomicU32)` and `wake_all(&AtomicU32)`.

Two rules follow. The wait and wake calls never matter for memory safety: delete them and the primitive degrades to a correct spin lock, because all state lives in the atomic. Wakes never synchronize memory: the happens-before comes from the release store and acquire load on the state. Consequence for tests: check that a waiter actually sleeps (count wake-ups), since a spinning implementation still passes a correctness test.

## Mutex

The canonical three-state futex mutex. std's Linux and Windows `Mutex` uses the same states (std 1.97.1 checked).

```rust
// state: 0 unlocked, 1 locked with no waiters, 2 locked and maybe waiters
pub fn lock(&self) -> MutexGuard<'_, T> {
    if self.state.compare_exchange(0, 1, Acquire, Relaxed).is_err() {
        lock_contended(&self.state);
    }
    MutexGuard { mutex: self }
}
#[cold]
fn lock_contended(state: &AtomicU32) {
    let mut spin = 0;
    while state.load(Relaxed) == 1 && spin < 100 { spin += 1; std::hint::spin_loop(); }
    if state.compare_exchange(0, 1, Acquire, Relaxed).is_ok() { return; }
    while state.swap(2, Acquire) != 0 { wait(state, 2); }
}
impl<T> Drop for MutexGuard<'_, T> {
    fn drop(&mut self) {
        if self.mutex.state.swap(0, Release) == 2 { wake_one(&self.mutex.state); }
    }
}
```

- After waiting, a thread must re-lock with **2**, never 1. Unlocking erased the knowledge of other waiters, so locking with 1 forgets them and they sleep forever.
- Spin on a `load`, and only while the state is 1. A state of 2 means another thread already gave up spinning.
- `wake_one`, not `wake_all`: only one thread can win, and waking all is a thundering herd. The woken thread is not guaranteed the lock. This mutex is unfair.
- Uncontended cost: one CAS to lock, one swap to unlock, no syscalls. The two-state version (swap 1, wait on 1, always `wake_one` on unlock) makes a syscall on every unlock. On Linux the book measured 10× to 30× slower uncontended, while on macOS both versions ran the same, because libc++'s wait and notify, like Windows' `WakeByAddressSingle`, skip the kernel when nobody waits.
- Whether spinning helps depends on the CPU. The book measured it helping on an older Intel and hurting on a newer AMD. Benchmark both, and use `std::hint::black_box` to stop the optimiser deleting the loop.
- Mark the slow path `#[cold]` and the small lock and unlock methods `#[inline]`.
- Guard traits as for the spin lock: `unsafe impl<T: Sync> Sync for MutexGuard<'_, T>`. The guard may also be `Send` (where `T: Send`): a futex lock can be unlocked by any thread. std's `MutexGuard` is `!Send` because pthread mutexes must be unlocked by the locking thread.
- To get a full safe `Mutex<T>` from a raw lock, implement `lock_api::RawMutex` (`lock_api` 0.4.14) and use `lock_api::Mutex<R, T>`.

## Condition variable

A counter of notifications. std's futex `Condvar` on Linux and Windows is this, without the waiter count (std 1.97.1 checked).

```rust
pub struct Condvar { counter: AtomicU32, num_waiters: AtomicUsize }

pub fn notify_one(&self) {
    if self.num_waiters.load(Relaxed) > 0 {
        self.counter.fetch_add(1, Relaxed);
        wake_one(&self.counter);
    }
}
pub fn wait<'a, T>(&self, guard: MutexGuard<'a, T>) -> MutexGuard<'a, T> {
    self.num_waiters.fetch_add(1, Relaxed);       // while holding the mutex
    let seen = self.counter.load(Relaxed);        // before unlocking
    let mutex = guard.mutex;
    drop(guard);
    wait(&self.counter, seen);                    // returns at once if notified since `seen`
    self.num_waiters.fetch_sub(1, Relaxed);
    mutex.lock()
}
```

- Every ordering is `Relaxed`. The mutex's unlock → lock edge orders the waiter's load of the counter before the notifier's increment, provided the notifier changed the data under the same mutex. That precondition is the contract of every condvar.
- `wait` takes the guard by value (proof the mutex is held) and returns a guard with the same lifetime.
- Callers loop on their condition: `while !ready(&g) { g = cv.wait(g); }`, or std's `Condvar::wait_while`. A wake can be spurious, and `notify_one` can release two threads: one that loaded the counter but had not yet slept, plus the one woken.
- Do not "fix" that by counting permitted wake-ups. A thread that starts waiting after the notify, even the notifier itself, can consume the permit and leave the original waiter asleep. glibc's `pthread_cond_t` had this bug until glibc 2.25 (2017).
- The counter can wrap: missing exactly 2^32 notifications between the load and the wait makes the waiter sleep. The window is tiny; a timeout on the wait closes it.
- `notify_all` wakes every waiter into a fight over one mutex. Linux's `FUTEX_REQUEUE` moves all but one onto the mutex's futex instead. A requeueing condvar must know its mutex, which is why condvars bind to one mutex. std's pthread `Condvar` (macOS and other non-futex Unix) panics with "attempted to use a condition variable with two mutexes" (*measured* on macOS). std's futex `Condvar` does not check.

## Reader-writer lock

Writer-preferring, with a separate futex so writers do not busy-loop.

```rust
// state = 2 × readers, +1 while a writer waits; u32::MAX = write-locked
unsafe impl<T: Send + Sync> Sync for RwLock<T> {}   // readers share &T, so T: Sync too

pub fn read(&self) -> ReadGuard<'_, T> {
    let mut s = self.state.load(Relaxed);
    loop {
        if s % 2 == 0 {
            assert!(s < u32::MAX - 2, "too many readers");
            match self.state.compare_exchange_weak(s, s + 2, Acquire, Relaxed) {
                Ok(_) => return ReadGuard { rwlock: self },
                Err(e) => s = e,
            }
        }
        if s % 2 == 1 { wait(&self.state, s); s = self.state.load(Relaxed); }
    }
}
pub fn write(&self) -> WriteGuard<'_, T> {
    let mut s = self.state.load(Relaxed);
    loop {
        if s <= 1 {
            match self.state.compare_exchange(s, u32::MAX, Acquire, Relaxed) {
                Ok(_) => return WriteGuard { rwlock: self },
                Err(e) => { s = e; continue; }
            }
        }
        if s % 2 == 0 {   // block new readers; Relaxed, it publishes nothing
            if let Err(e) = self.state.compare_exchange(s, s + 1, Relaxed, Relaxed) { s = e; continue; }
        }
        let w = self.writer_wake_counter.load(Acquire);   // read the counter before re-checking
        s = self.state.load(Relaxed);
        if s >= 2 { wait(&self.writer_wake_counter, w); s = self.state.load(Relaxed); }
    }
}
// ReadGuard::drop:  if state.fetch_sub(2, Release) == 3 {          // 3 -> 1: last reader, writer waiting
//                       writer_wake_counter.fetch_add(1, Release); wake_one(&writer_wake_counter); }
// WriteGuard::drop: state.store(0, Release); writer_wake_counter.fetch_add(1, Release);
//                   wake_one(&writer_wake_counter); wake_all(&state);
```

- Futex `wait` needs the exact value observed. When the locked state varies (a reader count), pass the value the failed CAS returned.
- The writer's `Acquire` load of `writer_wake_counter` pairs with the unlocker's `Release` increment, which comes after releasing `state`. Without it the writer can see the new counter and the stale state, and sleep through its wake-up.
- Write unlock wakes one writer and all readers, because it cannot tell who is waiting.
- Earlier-version bugs: a writer that waits on `state` itself busy-loops through syscalls under read churn, because the value keeps changing. Without the waiting-writer bit, a stream of readers starves writers.
- Writer preference means a thread that calls `read()` twice can deadlock if a writer queues in between. That holds for std's `RwLock` too (see `hardware-and-os.md`).
- `ReadGuard` implements only `Deref`; `WriteGuard` implements `Deref` and `DerefMut`.

## Seqlock

The book describes the seqlock (a counter that is odd while writing; readers retry if it changed or was odd) but gives no orderings. This one follows Boehm's 2012 analysis and was stress-tested here: 0 torn reads in 25M against a concurrent writer, versus 2.2M torn reads for the all-Relaxed version.

```rust
pub struct SeqLock { seq: AtomicU64, data: [AtomicU64; 2] }   // data words are atomics

pub fn write(&self, v: [u64; 2]) {            // one writer; serialise writers with a lock
    let s = self.seq.load(Relaxed);
    self.seq.store(s + 1, Relaxed);           // odd: write in progress
    fence(Release);                           // the odd value is ordered before the data stores
    self.data[0].store(v[0], Relaxed);
    self.data[1].store(v[1], Relaxed);
    self.seq.store(s + 2, Release);
}
pub fn read(&self) -> [u64; 2] {
    loop {
        let s1 = self.seq.load(Acquire);
        if s1 & 1 == 1 { std::hint::spin_loop(); continue; }
        let v = [self.data[0].load(Relaxed), self.data[1].load(Relaxed)];
        fence(Acquire);                       // the data loads are ordered before the re-check
        if self.seq.load(Relaxed) == s1 { return v; }
    }
}
```

The data must be atomics, each word Relaxed. A plain read racing a write is a data race and undefined behaviour **even if the torn value is discarded**. RFC 3301's `AtomicPerByte` would fix this but does not exist in std 1.97.1. Seqlocks suit shared memory with untrusted readers (Linux's vDSO clock), since readers never write.

## Lock-free structures and reclamation

- **ABA:** a CAS succeeds if the value went A → B → A in between. Harmless for counters, a real bug for pointer CAS when an allocation is freed and reused at the same address. Tag the pointer (a version counter, or low bits through `AtomicPtr::fetch_or` and `map_addr`, stable 1.91), or make reuse impossible while anyone can hold the old pointer.
- **RCU:** read the pointer, copy into a new allocation, modify, then `compare_exchange` the pointer (fails if someone else replaced it). The hard part is the unstated fourth step, freeing the old copy while readers may still hold it. Options: reference counting (`arc-swap` 1.9), leaking, hazard pointers (`haphazard` 0.1), epochs or quiescent states (`crossbeam-epoch` 0.9).
- **Lock-free linked list:** push-front is allocate, point at the head, CAS the head. Concurrent removal and insertion on neighbouring nodes can drop a fresh node or resurrect a removed one. A common simplification serialises writers with a `Mutex` and keeps reads lock-free. Any structure that CASes pointers needs a reclamation strategy.

## Other designs

- **Semaphore:** std has none (tokio has `tokio::sync::Semaphore`). `Mutex<u32>` + `Condvar`, or one atomic with futex wait and wake. Never build a semaphore-based mutex on a mutex-based semaphore.
- **Queue-based locks:** the lock is one `AtomicPtr` to a list of waiters (each holding a `Thread` to unpark, often on its own stack), with state in the pointer's low bits. They need only park and unpark, no futex. Windows' SRW lock and std's non-futex `RwLock` and `Once` work this way.
- **Parking-lot locks:** waiter queues live in a global hash map keyed by address, so the lock itself is one byte (WebKit 2015, the `parking_lot` crate, 0.12).
