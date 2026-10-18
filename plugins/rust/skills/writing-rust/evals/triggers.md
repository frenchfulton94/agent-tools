# Trigger battery: writing-rust

## Should trigger (10)

1. "I bumped my crate to edition 2024 and now `extern "C" { fn abs(x: i32) -> i32; }` won't compile. What's the new syntax?"
2. "Is `lazy_static` still the way to do a global regex in Rust, or is there something in std now?"
3. "Why does my `RefCell` borrow in an `if let` panic on one machine's build but not after I changed editions?"
4. "Write a Rust function that returns an iterator over the even numbers in a `&Vec<i32>`."
5. "Should this library return `Box<dyn Error>` or its own error enum? Here's the module."
6. "My worker threads share an `Arc<Mutex<Receiver<Job>>>` but they run one at a time instead of in parallel."
7. "Can a Rust trait with an `async fn` be used as `dyn Trait`?"
8. "Review this unsafe block that reads a field of a `#[repr(packed)]` struct through a pointer."
9. "Is `i32::max_value()` deprecated? And what's the right way to do overflow-safe addition that also panics in release?"
10. "Refactor this match so it uses let chains instead of nested `if let`s."

## Should not trigger (10) — near-misses

1. "What does error E0502 mean and how do I read this borrow-checker output?" (diagnostic interpretation → `fixing-rust-compile-errors`)
2. "Add a `serde` feature flag to my crate and make it optional in Cargo.toml." (manifest and features → `using-cargo`)
3. "How do I run only the ignored tests in one integration test file?" (test selection → `testing-rust`)
4. "My intra-doc link to a method on a re-exported type is broken in rustdoc." (rustdoc → `documenting-rust`)
5. "Set up clap so my CLI exits with code 2 on bad arguments and doesn't panic when piped into `head`." (CLI behaviour → `building-rust-clis`)
6. "Set `rust-version` and make CI fail if a dependency needs a newer compiler." (MSRV → `using-cargo`)
7. "Why does my Go goroutine leak when the channel is never closed?" (another language's concurrency)
8. "Convert this C++ class with a virtual destructor to idiomatic C++20." (C++, not Rust)
9. "Cross-compile my Rust binary for aarch64 Linux from macOS." (targets and linkers → `using-cargo`)
10. "Write a TypeScript type that mirrors this Rust enum for my frontend." (TypeScript authoring)

## Notes on the negatives

Negatives 1, 2, 6 and 9 are the hard ones: they are Rust questions, and a description that fires on "Rust" alone will catch them. They belong to sibling skills because the answer is about the compiler's output, Cargo's manifest, or the toolchain rather than about the language or std. Negative 1 is the closest: if the user then asks how to *restructure* the code the error points at, that follow-up does belong here.
