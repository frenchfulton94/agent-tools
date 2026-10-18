# Trigger battery: documenting-rust

## Should trigger (10)

1. "Write doc comments for this public Rust API, with examples, a Panics section and an Errors section."
2. "cargo doc warns that `Parser` is both a struct and a function. How do I link to the struct?"
3. "My doctest uses `?` and fails with 'expected `()`, found `Result`'."
4. "Since we moved the crate to edition 2024, a doctest that asserts `line!()` fails and the panic points at doctest_bundle_2024.rs."
5. "Our docs.rs build broke with 'feature has been removed' on `doc_auto_cfg`. What's the current way to show feature badges?"
6. "I marked an example `compile_fail,E0277` but it passes even when I fix the bug it's supposed to catch."
7. "Why does `pub use internal::Config;` show up as a one-line re-export instead of the full struct docs?"
8. "Make the README examples run as tests without duplicating them into lib.rs."
9. "Set up CI so broken intra-doc links and missing docs fail the build."
10. "This code example in my `///` comment never runs. `cargo test --doc` doesn't even list it." (attribute typo or unknown language)

## Should not trigger (10) — near-misses

1. "`cargo test` runs my integration tests twice. How do I filter to one test file?" (running and selecting tests: testing-rust)
2. "How do I write a unit test for a private function in the same module?" (test layout: testing-rust)
3. "What does error E0277 'the trait bound is not satisfied' mean here?" (diagnostic reading: fixing-rust-compile-errors)
4. "Add a `docs` feature to Cargo.toml and make serde optional." (feature definitions: using-cargo)
5. "Generate a man page and shell completions for my clap CLI." (CLI docs: building-rust-clis)
6. "Should this function return `impl Iterator` or `Vec<T>`?" (API design: writing-rust)
7. "Write JSDoc comments for this TypeScript module." (another language's doc comments)
8. "Set up mdBook for our project's user guide." (a separate tool, not rustdoc)
9. "Write Python docstrings with doctest examples for this module." (Python doctest, not Rust)
10. "Clippy says this `match` can be an `if let`. Apply the fix." (a non-doc lint: fixing-rust-compile-errors)

## Notes on the negatives

Negatives 1, 2, and 9 are the hard ones. They share words with this skill: test, doctest, docs. Running doctests belongs to `testing-rust`, and only their syntax and attributes belong here. Negative 5 says "docs" but means CLI help output. A description that fires on "test" or "documentation" alone catches all four.
