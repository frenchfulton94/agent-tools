# Trigger battery: linting-and-formatting-rust

## Should trigger (10)

1. "Set up Clippy for my new library crate — which lint groups should I turn on?"
2. "Is it a good idea to enable clippy::restriction for the whole workspace?"
3. "I added `#![warn(clippy::all, clippy::pedantic)]` and now `x == x` only warns instead of failing the build. Why?"
4. "Clippy fails with 'error reading Clippy's configuration file: unknown field' after I copied settings from the Clippy website."
5. "Add a GitHub Actions job that runs clippy and rustfmt and fails on any warning."
6. "My rustfmt.toml has `imports_granularity = \"Crate\"` but nothing changes and it prints something about the nightly channel."
7. "cargo fmt and running rustfmt on the file directly sort my imports differently."
8. "Our crate's MSRV is 1.70 — how do I make Clippy stop suggesting APIs we can't use?"
9. "I set `doc-valid-idents = [\"MyCorp\"]` and now doc_markdown complains about GitHub and macOS everywhere."
10. "Should we switch to the 2024 style edition in rustfmt, and what will it change?"

## Should not trigger (10) — near-misses

1. "What does clippy::needless_range_loop mean and how do I fix it here?" (what one lint means and fixing the site: fixing-rust-compile-errors)
2. "How do I write the [workspace.lints] table and make members inherit it?" (`[lints]` syntax and inheritance: using-cargo)
3. "error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable" (a compile error: fixing-rust-compile-errors)
4. "Set rust-version in Cargo.toml and make the resolver respect it." (MSRV in Cargo: using-cargo)
5. "Add `#![deny(missing_docs)]` and write the missing doc comments for this module." (writing docs: documenting-rust)
6. "Should this builder method be called `with_timeout` or `timeout`?" (API naming: designing-rust-apis)
7. "Configure ESLint and Prettier for our TypeScript monorepo." (another language's linters)
8. "Set up Biome to format and lint the frontend." (another toolchain)
9. "Run the test suite in CI with `cargo test` across three OSes." (testing CI: testing-rust)
10. "Rewrite this function to use let chains from edition 2024." (language idioms: writing-rust)

## Notes on the negatives

Negatives 1, 2 and 4 are the hard ones. They name Clippy, `[lints]`, or MSRV, which this skill also touches, but they ask what one lint means, how the table is written, or how Cargo enforces `rust-version`. This skill owns which lints to turn on and how the tools are configured and run. A description that triggers on any mention of "clippy" or "lint" catches all three.
