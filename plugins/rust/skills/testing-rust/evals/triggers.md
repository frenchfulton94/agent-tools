# Trigger battery: testing-rust

## Should trigger (10)

1. "How do I run just one test in my Rust crate? `cargo test parse_header` runs a bunch of others too."
2. "`cargo test -- --shuffle` says it's only accepted on the nightly compiler. How do I randomise test order?"
3. "My println! output doesn't show up when my Rust test passes. How do I see it?"
4. "These tests pass one at a time but fail when I run the whole suite with cargo test."
5. "I wrote `#[test] async fn fetch_works()` and rustc says async functions cannot be used for tests."
6. "How do I share setup code between files in my tests/ directory without it showing up as its own test?"
7. "I want an integration test that runs my CLI binary and checks its exit status. How do I find the binary's path?"
8. "How do I benchmark a function on stable Rust? `#[bench]` gives me an unstable feature error."
9. "`cargo test --all-targets` in CI doesn't seem to run my doc examples. Why?"
10. "I need a JSON or JUnit report from cargo test for our CI dashboard."

## Should not trigger (10): near-misses

1. "How do I hide the setup lines in a doc example and mark one example as no_run?" (doctest syntax and attributes: documenting-rust)
2. "rustc says E0502 cannot borrow as mutable because it is also borrowed as immutable." (borrow-checker diagnostic: fixing-rust-compile-errors)
3. "How do I declare a dev-dependency only for one target platform in Cargo.toml?" (manifest syntax: using-cargo)
4. "Should my library return `Box<dyn Error>` or a custom error enum?" (error-handling design: writing-rust)
5. "Set up a release profile with LTO and `codegen-units = 1`." (profiles for building, not tests: using-cargo)
6. "How should my CLI print errors to stderr and choose exit codes?" (CLI behaviour: building-rust-clis)
7. "Write Vitest tests for my React hook." (JavaScript testing)
8. "My pytest fixtures run in the wrong order." (Python testing)
9. "How do I run `go test` with the race detector?" (Go testing)
10. "Configure clippy to deny `unwrap_used` across the workspace." (lint policy: linting-and-formatting-rust)

## Notes on the negatives

Negatives 1, 3 and 5 are the hard ones. Doctests, dev-dependencies and profiles are all words this skill's description uses, but the questions ask about doc-comment syntax, manifest tables and build tuning rather than about running or organising tests. The description scopes doctests to running and filtering, and profiles to the test and bench ones, to keep those questions with the sibling skills. Negatives 7 to 9 check that "tests" alone does not pull the skill into other languages.
