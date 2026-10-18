# Concurrency and async

From the Book (ch. 16–17, 21), the std docs and the Reference (1.99). Results marked *measured* were run on rustc 1.97.1.

## Contents

- [Threads](#threads)
- [Channels](#channels)
- [Locks and guard lifetimes](#locks-and-guard-lifetimes)
- [Atomics and one-time initialisation](#atomics-and-one-time-initialisation)
- [`Send` and `Sync`](#send-and-sync)
- [Async fundamentals](#async-fundamentals)
- [Running futures concurrently](#running-futures-concurrently)
- [Async closures and async functions in traits](#async-closures-and-async-functions-in-traits)
- [`Pin` and `Unpin`](#pin-and-unpin)
- [Streams](#streams)
- [The Book's `trpl` crate](#the-books-trpl-crate)

## Threads

- std threads are 1:1 OS threads. When `main` returns, the process ends and other threads are killed without running their destructors.
- `thread::spawn` needs a `'static` closure, hence `move`. To borrow from the parent stack, use **`thread::scope`**, which joins every spawned thread before returning:

```rust
let mut total = 0;
let data = vec![1, 2, 3];
thread::scope(|s| {
    s.spawn(|| println!("{}", data.len()));   // borrows `data`
    s.spawn(|| total += 1);                   // a mutable borrow is fine too
});
```

- `JoinHandle::join()` returns `Err(payload)` if the thread panicked. The payload is `&dyn Any + Send` holding a `&str` **or** a `String` (unspecified which); downcast to both, or use `PanicHookInfo::payload_as_str()` (1.91) in a hook.
- `thread::spawn` panics if the OS cannot create a thread; `thread::Builder::new().spawn(..)` returns `io::Result`.
- The default stack for spawned threads is 2 MiB on tier-1 platforms. `Builder::stack_size` overrides `RUST_MIN_STACK`.
- A panic in a thread does not take down the process (unless `panic = "abort"`); a panic in `main` exits with code 101.
- Throughput: `thread::available_parallelism()` gives a sensible worker count.

## Channels

- `mpsc::channel()` is unbounded; `mpsc::sync_channel(n)` is bounded and `send` blocks when full (`n = 0` is a rendezvous). `send` returns `Err` once the receiver is dropped.
- `for msg in rx` ends when **every** `Sender` is dropped. A thread that keeps a clone of `tx` alive hangs the loop; drop the original after cloning for workers.
- `Receiver` is single-consumer. Several workers share it as `Arc<Mutex<Receiver<T>>>`, taking the lock only to `recv()` (see the guard table below). `mpmc` channels are unstable.
- For a graceful shutdown in `Drop`: store the sender as `Option<Sender<_>>`, `drop(self.sender.take())`, then join the workers, each of which exits when `recv()` returns `Err`.

## Locks and guard lifetimes

- `lock()` returns `Err` if a thread panicked while holding the lock (poisoning). `unwrap()` propagates the panic; `.unwrap_or_else(PoisonError::into_inner)` recovers the data. Non-poisoning locks (`std::sync::nonpoison`) are unstable.
- The lock is released when the `MutexGuard` drops; there is no `unlock`. Call `drop(guard)` to release early.
- How long a guard lives depends on the syntax around it (*measured*, both editions unless noted):

| Code | Guard held during the body? |
|---|---|
| `match m.lock().unwrap().len() { .. }` | yes, for the whole `match` |
| `while let Some(x) = m.lock().unwrap().pop() { .. }` | yes, every iteration |
| `if let Some(x) = m.lock().unwrap().first() { .. }` | yes, in the `then` block |
| the `else` block of that `if let` | 2021: yes; 2024: no |
| `let x = m.lock().unwrap().len();` then later code | no |
| `let _ = m.lock();` | no, dropped at once; deny-by-default `let_underscore_lock` |

  To process items without holding the lock, take them out in a `let` first: `let job = rx.lock().unwrap().recv();`.
- Deadlocks and lock-ordering bugs are not prevented. Take multiple locks in one global order.
- `RwLockWriteGuard::downgrade` (1.92) turns a write guard into a read guard atomically.
- A std `MutexGuard` is not `Send`. Holding one across an `.await` makes the future `!Send`, which most multithreaded runtimes reject. Drop it before the `.await`, or use the runtime's async mutex when the lock really must be held across an await.

## Atomics and one-time initialisation

Choosing an `Ordering`, fences, or building your own lock, channel or `Arc` → `using-atomics-and-locks`.

- For a simple shared counter or flag, use an atomic, not `Mutex<i32>`: `a.fetch_add(1, Ordering::Relaxed)`. Atomic `update` and `try_update` (1.95; `try_update` is the new name of `fetch_update`) wrap a compare-exchange loop. Use them only when no `fetch_*` method expresses the operation, such as `a.try_update(Ordering::Relaxed, Ordering::Relaxed, |x| x.checked_add(1))`: a `fetch_*` is one instruction on ARM64, the loop is not (*measured*).
- Invalid orderings panic at runtime and are caught by the deny-by-default `invalid_atomic_ordering`: `store` with `Acquire`/`AcqRel`, `load` with `Release`/`AcqRel`, `fence` with `Relaxed`.
- Store pointers in `AtomicPtr`, not `AtomicUsize`, to keep provenance.
- On targets without native atomics (thumbv6m, some RISC-V), only load and store exist; gate with `#[cfg(target_has_atomic = "32")]` or use the `portable-atomic` crate.
- **Globals:** `static CONFIG: LazyLock<Config> = LazyLock::new(load);` (1.80) replaces `lazy_static!` and `once_cell::sync::Lazy`. `OnceLock::get_or_init` when the initialiser depends on runtime input. `LazyLock::get` and `force_mut` exist since 1.94. `OnceLock::get_or_try_init` is unstable.
- `thread_local!` with a constant initialiser skips lazy-initialisation checks: `thread_local! { static N: Cell<u32> = const { Cell::new(0) }; }`. For a `RefCell` key, `N.with_borrow(|v| ..)` and `with_borrow_mut`.

## `Send` and `Sync`

- `T: Send`: ownership can move to another thread. `T: Sync`: `&T` can be shared, which holds exactly when `&T: Send`.
- Not `Send`: `Rc`, raw pointers, `MutexGuard`. Not `Sync`: `Rc`, `Cell`, `RefCell`, `OnceCell`, raw pointers. `Mutex<T>` is `Sync` when `T: Send`.
- Both are auto traits: a type is `Send`/`Sync` when all its fields are. Implementing them by hand needs `unsafe impl` and a proof.
- `Rc<..>` moved into `thread::spawn` gives E0277 "`Rc<..>` cannot be sent between threads safely", with a note naming the closure. Use `Arc`.
- Closure capture is per field (2021+), so a closure can be `!Send` because it captured one raw-pointer field rather than the whole struct.

## Async fundamentals

- **Futures are lazy.** Nothing runs until the future is polled, usually by `.await` or a runtime. An unawaited future triggers an unused-must-use warning. A spawned thread, by contrast, starts at once.
- `async fn f(x: &T) -> U` is roughly `fn f(x: &T) -> impl Future<Output = U>` whose body is `async move { .. }`. It captures **all** parameters, used or not, so they drop when the future completes.
- Inside an `async` block, `?` and `return` complete the block's future, not the enclosing function. `break` and `continue` cannot cross an async block (E0267).
- std has no runtime. `async fn main` is E0752 "`main` function is not allowed to be `async`"; a runtime attribute such as `#[tokio::main]` rewrites it into a `block_on` call.
- A future only yields at an `.await`. Code between awaits runs synchronously, so a blocking call (`std::thread::sleep`, heavy computation, blocking I/O) starves every other future on that thread. Move such work to a thread or the runtime's blocking pool; insert `yield_now().await` to break up long loops, and measure, because yielding has a cost.
- Do not poll a future again after it returned `Ready`; many panic.
- std pieces: `Future`, `IntoFuture` (both in the 2024 prelude), `std::future::{ready, pending, poll_fn}`, `std::task::{Context, Poll, Waker}`, `Waker::noop()` (1.85). `future::join!` and async iterators are unstable.

## Running futures concurrently

- **Awaiting futures one after another is sequential.** `a.await; b.await;` runs `b` only after `a` finishes. Run them together with a join (`futures::join!`, `tokio::join!`, `join_all`) or by spawning tasks.
- Code inside a single async block runs in order. To interleave a producer and a consumer, put each in its own block and join them.
- **The hang:** a producer block that only borrows `tx` keeps the channel open until the outer block ends, while the outer block waits on the consumer, which waits for the channel to close. Make every producer block `async move` so each sender drops when its block finishes.
- A `for` loop cannot iterate asynchronously produced items; write `while let Some(v) = rx.recv().await`.
- `select` takes the first future to finish. Fairness differs: `futures::future::select` always polls its arguments in order; `tokio::select!` picks randomly unless `biased;`. In a hand-written timeout, pass the work future first.
- Rule of thumb from the Book: parallel, CPU-bound work goes on threads; highly concurrent, I/O-bound work goes on async. Mixing is normal: a thread can send on an async channel that a task awaits.

## Async closures and async functions in traits

- **Async closures** `async |x| { .. }` and `async move || { .. }` (1.85). Take them with `impl AsyncFn(T) -> U`, `AsyncFnMut` or `AsyncFnOnce` (in the prelude on every edition). Unlike `|x| async move { .. }`, an async closure can lend its captures to the future it returns. The allow-by-default lint `closure_returning_async_block` suggests the rewrite.
- `AsyncFn*` traits are not dyn compatible.
- **`async fn` in traits** and return-position `impl Trait` in traits are stable (1.75). Such a trait is not dyn compatible (E0038) unless the method has `where Self: Sized`.
- A caller cannot require the future returned by a trait's `async fn` to be `Send`. If implementations must be usable from a multithreaded runtime, declare the method as `fn call(&self) -> impl Future<Output = R> + Send;`; implementations may still write `async fn call(&self) -> R`.

## `Pin` and `Unpin`

- An async block's state machine can hold references into itself, so moving it after it has been polled would leave them dangling. `Pin<P>` promises that the pointee will not move again until it is dropped.
- `Unpin` is the normal case (an auto trait); types that opt out include most `async` blocks and anything with `PhantomPinned`. `.await` pins the future for you.
- `Box<T>` implements `Future` only when `T: Future + Unpin`. A `Vec<Box<dyn Future<Output = ()>>>` passed to a join gives E0277 "`dyn Future<Output = ()>` cannot be unpinned". Use `Vec<Pin<Box<dyn Future<Output = ()>>>>` with `Box::pin(fut)`, or `std::pin::pin!(fut)` for a local `Pin<&mut _>` that does not outlive the scope.
- `Pin<Box<T>>` pins the `T`, not the box; the box pointer itself may move.
- `pin!(x)` no longer applies deref coercion (1.97): with `x: &mut T` it produces `Pin<&mut &mut T>`.
- Writing a future or a pinned type by hand:
  - The pinning **drop guarantee**: pinned memory must not be invalidated or reused until `drop` runs. Leaking is allowed; overwriting an `Option` that holds pinned data, or `Vec::set_len` over pinned elements, is not.
  - **Structural pinning** of a field is your per-field choice. A structurally pinned field requires: the struct is `Unpin` only if that field is; `Drop` treats `self` as pinned; the struct is not `#[repr(packed)]`; nothing moves the field out while pinned. Project with `map_unchecked_mut(|s| &mut s.field)`. Non-structural fields are reached with `get_unchecked_mut` and may be moved.
  - No pinning with `#[repr(packed)]`.
  - In practice, use the `pin-project-lite` or `pin-project` crate for projections.

## Streams

- A stream is an async iterator. `Stream` and `StreamExt` are not in std; they come from the `futures` crate (and `tokio-stream`). `std::async_iter::AsyncIterator` is unstable.
- `.next()` needs `StreamExt` in scope (E0599 "items from traits can only be used if the trait is in scope"). `StreamExt::next` requires `Self: Unpin`; pin the stream first (`pin!(stream)`).
- Implement only `Stream` for your type; `StreamExt` has a blanket impl.

## The Book's `trpl` crate

Book chapter 17 uses its own teaching crate, `trpl`, which wraps `tokio` and `futures`. Real code depends on those directly. Likely equivalents:

| `trpl` | Real API |
|---|---|
| `trpl::block_on` | a Tokio runtime's `block_on`, or `#[tokio::main]` |
| `trpl::spawn_task` | `tokio::spawn` |
| `trpl::sleep` | `tokio::time::sleep` |
| `trpl::yield_now` | `tokio::task::yield_now` |
| `trpl::join`, `join!`, `join_all` | `futures::future::join`, `futures::join!`, `futures::future::join_all` |
| `trpl::select` | `futures::future::select` (returns `Either`) |
| `trpl::channel` | `tokio::sync::mpsc::unbounded_channel` |
| `trpl::stream_from_iter` | `tokio_stream::iter` or `futures::stream::iter` |
| `trpl::StreamExt` | `futures::StreamExt` or `tokio_stream::StreamExt` |
