# Trigger battery: designing-rust-apis

## Should trigger (10)

1. "Review the public API of my crate before I publish 1.0 — anything that breaks the Rust API guidelines?"
2. "Should this method be called `as_bytes`, `to_bytes`, or `into_bytes`? It allocates a new Vec."
3. "What traits should my public `Duration`-like newtype derive?"
4. "I have `pub fn new(verbose: bool, recursive: bool)` — is there a more idiomatic signature?"
5. "How do I stop other crates from implementing my `Codec` trait so I can add methods later?"
6. "Clippy says nothing about my `pub struct HTTPClient` or my `get_name()` getter. Is the API fine?"
7. "Should my config struct have public fields, private fields with getters, or `#[non_exhaustive]`?"
8. "Is it better to return `impl Iterator<Item = Row>` or a named `Rows` type from my library function?"
9. "Design an error type for my parsing library — enum, Box<dyn Error>, or something else?"
10. "We changed a private helper in the iterator our lib returns and now downstream says it's no longer Send — how should we have designed that?"

## Should not trigger (10) — near-misses

1. "What does error E0277 `Rc<u8> cannot be sent between threads safely` mean here?" (diagnostic reading → fixing-rust-compile-errors)
2. "Is removing a public enum variant a major or minor version bump?" (SemVer rules → using-cargo)
3. "How do I write the `# Errors` section and a doctest for this function?" (doc comments → documenting-rust)
4. "Why does my trait with an `async fn` give 'not dyn compatible'?" (trait mechanics → writing-rust)
5. "Add clap argument parsing with subcommands to my CLI binary." (CLI → building-rust-clis)
6. "Set up `[lints]` in Cargo.toml so pedantic warns across the workspace." (lint table syntax → using-cargo)
7. "Write unit tests for my builder's validation logic." (tests → testing-rust)
8. "Design a REST API for a todo service — which endpoints and status codes?" (HTTP API design, not a Rust library surface)
9. "How should I name and export functions in my TypeScript library's public API?" (adjacent language)
10. "Implement a lock-free stack with `compare_exchange` for my crate." (atomics → using-atomics-and-locks)

## Notes on the negatives

Negatives 1, 2, 4, and 8 are the hard ones. Negative 1 shares the `Send` symptom of positive 10 but asks what an error means, not how to design the API that caused it. Negative 2 is SemVer, which `using-cargo` owns, even though this skill's future-proofing advice exists to avoid such bumps. Negative 4 is trait mechanics rather than the decision whether a trait should be dyn compatible. Negative 8 uses "API design" for a web service. A description that fires on "API" or "breaking change" alone will catch them.
