# Trigger battery: using-atomics-and-locks

## Should trigger (10)

1. "Is `Relaxed` enough for this `ready` flag, or do I need `Acquire`/`Release`? The other thread reads a `Vec` after it sees the flag."
2. "Review my lock-free stack: it uses `AtomicPtr` and `compare_exchange` to push and pop."
3. "When should I use `compare_exchange_weak` instead of `compare_exchange`?"
4. "I'm writing my own `Arc` for a no_std allocator. Which orderings do the refcount increment and decrement need?"
5. "Our counter loses updates on the Graviton build servers but never on our Intel laptops."
6. "Implement a mutex on top of a futex, with wait and wake, without calling into pthread."
7. "Two `AtomicU64` counters updated by different threads make the program slower with more cores. Why?"
8. "Is there a futex on macOS I can use, and what does std's `Mutex` use there?"
9. "Everything in this file uses `Ordering::SeqCst`. Can any of it be weakened?"
10. "How do I test this concurrent queue with loom, and will Miri catch a wrong ordering?"

## Should not trigger (10) — near-misses

1. "How do I share a `HashMap` between threads with `Arc<Mutex<..>>`?" (everyday std use → `writing-rust`)
2. "My `MutexGuard` is held across an `.await` and the future isn't `Send`." (async and guard lifetimes → `writing-rust`)
3. "Should I use `tokio::sync::Mutex` or `std::sync::Mutex` in my handler?" (async runtime choice → `writing-rust`)
4. "Replace `lazy_static!` with something from std for a global config." (`LazyLock` usage → `writing-rust`)
5. "What does E0277 '`Rc<i32>` cannot be sent between threads safely' mean?" (diagnostic reading → `fixing-rust-compile-errors`)
6. "Run only the tests in `tests/concurrency.rs` with one test thread." (test selection → `testing-rust`)
7. "Add `loom` as a dev-dependency only for one target in Cargo.toml." (manifest syntax → `using-cargo`)
8. "Explain `std::memory_order_acq_rel` in this C++ ring buffer." (C++, not Rust)
9. "Why does my Java `volatile` field not make `count++` atomic?" (another language's memory model)
10. "Use `sync.WaitGroup` to wait for my goroutines to finish." (Go)

## Notes on the negatives

Negatives 1–4 are the hard ones. They mention mutexes, `Arc`, or shared state, but the user is using std's primitives, not choosing an ordering or building one, and `writing-rust` covers that. Negatives 8 and 9 share the vocabulary (acquire/release, `volatile`, atomics) but not the language; a description that fires on "memory ordering" alone would catch them.
