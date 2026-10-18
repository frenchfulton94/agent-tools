# Trigger battery: fixing-rust-compile-errors

## Should trigger (10)

1. "rustc says E0502 cannot borrow `v` as mutable because it is also borrowed as immutable. Here's the loop."
2. "What does error E0412 mean? My old notes use it but I can't get rustc to produce it."
3. "I fixed the two errors cargo showed me and now there's a brand-new borrow error and three warnings. Did I break something?"
4. "`future cannot be sent between threads safely` when I tokio::spawn this. I already call drop(guard) before the await."
5. "I put `#![forbid(unused)]` at the top but an `#[allow(unused_variables)]` further down still wins. Why?"
6. "My Cargo.toml has `unused = \"deny\"` and `unused_variables = \"allow\"` under [lints.rust], but unused variables still fail the build."
7. "`cargo check` is clean but `cargo build` fails with E0080 evaluation panicked. How is that possible?"
8. "cargo fix ran but my tests directory still has all the unused mut warnings."
9. "Help me parse rustc's --error-format=json output to pull out the suggested fixes."
10. "This won't compile: `if let Some(v) = map.get(&k) { return v; } map.insert(k, v2);` — the borrow should be over by then."

## Should not trigger (10): near-misses

1. "Should my library return `Box<dyn Error>` or a thiserror enum?" (error-handling design: writing-rust)
2. "How do I write the [lints] table so the whole workspace inherits it?" (manifest syntax: using-cargo)
3. "cargo says failed to select a version for `tokio` which could resolve this conflict." (dependency resolution: using-cargo)
4. "My test panics with `assertion left == right failed`; how do I see the full output?" (a failing test, not a compile error: testing-rust)
5. "rustdoc warns about a broken intra-doc link." (rustdoc lints: documenting-rust)
6. "My CLI should exit with code 2 on bad arguments; how do I set that?" (CLI behaviour: building-rust-clis)
7. "Explain Rust lifetimes to me from scratch with examples." (language teaching, no diagnostic: writing-rust)
8. "TypeScript says Type 'string' is not assignable to type 'number'." (another compiler: debugging-type-errors)
9. "My C++ template error is 300 lines long; which part matters?" (another language)
10. "My Rust program segfaults at runtime in an unsafe block." (runtime undefined behaviour, not a compile error: writing-rust)

## Notes on the negatives

Negatives 2, 3, and 4 are the hard ones. They mention cargo, lints, or errors, but the fix lives in `Cargo.toml` syntax, the resolver, or the test harness. A description that fires on "cargo error" or "lint" alone will catch them. Negative 7 shares the vocabulary of borrow errors without any diagnostic to read. Negative 8 is the TypeScript sibling skill's territory.
