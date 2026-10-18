# Trigger battery: using-cargo

## Should trigger (10)

1. "Set up a Cargo workspace for these three crates so they share one version and one serde dependency."
2. "My CI sets RUSTFLAGS=-Dwarnings and now the target-cpu flag from .cargo/config.toml stopped applying. Why?"
3. "serde_json shows up twice in my build, 1.0.100 and 1.0.140. How do I find out who pulls in the old one?"
4. "We support Rust 1.75. How do I stop `cargo update` from pulling dependency versions that need a newer compiler?"
5. "Cross-compile my binary for a Raspberry Pi from my Ubuntu laptop."
6. "Add a `tls` feature that turns on rustls only when the user asks for it, without exposing rustls as its own feature."
7. "Every `cargo build` recompiles my crate even though I didn't change anything."
8. "Is it a breaking change to add a variant to this public enum before I publish 2.3.0?"
9. "Write a build.rs that compiles the bundled C library and sets a cfg when the system has libfoo 2.x."
10. "Turning on --all-targets changed how my release binary behaves, and a dev-dependency feature seems to leak in."

## Should not trigger (10) — near-misses

1. "What does error E0502 mean and how do I fix this borrow?" (a compiler diagnostic: fixing-rust-compile-errors)
2. "Why is clippy warning about needless_range_loop here?" (what a lint means: fixing-rust-compile-errors)
3. "How do I run only the tests in one module and show their println output?" (libtest filters and capture: testing-rust)
4. "How do I write a doctest that is expected to fail to compile?" (doctest attributes: documenting-rust)
5. "Should this function take &str or String, and how do I return an iterator?" (API design: writing-rust)
6. "Parse --verbose and a subcommand with clap derive." (argument parsing: building-rust-clis)
7. "Set up a pnpm workspace with shared TypeScript config." (another language's package manager)
8. "My Python package build with maturin fails on manylinux." (Python packaging on top of Rust, outside Cargo's own behaviour)
9. "Install the nightly toolchain and make it the default with rustup." (toolchain management, not Cargo configuration)
10. "Configure Go modules to use a private GitHub repository." (a different language's dependency system)

## Notes on the negatives

Negatives 3, 4, and 9 are the hard ones. `cargo test` and `cargo doc` are Cargo commands, but the question is about the harness or rustdoc, which the sibling skills own; this skill should fire only when the question is about profiles, features, or target selection for those commands. Negative 9 shares the toolchain (`rustup`) but not Cargo's manifest, resolver, or configuration. A description that over-triggers on the word "cargo" will catch them.
