# Trigger battery: building-rust-clis

## Should trigger (10)

1. "My Rust tool panics with 'failed printing to stdout: Broken pipe' when I pipe it into head."
2. "Set up clap for a Rust CLI with `add` and `remove` subcommands and a `-v` flag that can repeat."
3. "My program's error just says `Error: Os { code: 2, kind: NotFound }`. How do I make it say which file was missing?"
4. "What exit code should my Rust command-line tool use for bad arguments versus a runtime failure, and how do I return it from main?"
5. "Writing a million lines with println! is really slow when I redirect the output to a file."
6. "Add a progress bar to my Rust CLI. It shouldn't break when output is redirected."
7. "`cargo_bin_cmd!` doesn't resolve in my assert_cmd test. The CLI book says to use it."
8. "How do I handle Ctrl-C in my Rust command-line app so it deletes its temp files first?"
9. "I want my Rust tool to read a config file from the user's config directory and let an env var override it."
10. "What's the best way to ship my Rust CLI to people who don't have cargo installed?"

## Should not trigger (10): near-misses

1. "Should my library crate return `Box<dyn Error>` or a thiserror enum?" (error-type design: writing-rust)
2. "How do I run just one integration test with cargo test and see its println output?" (test selection and capture: testing-rust)
3. "rustc says E0277 `the size for values of type str cannot be known`." (diagnostic: fixing-rust-compile-errors)
4. "Configure `[profile.release]` with `lto` for my workspace, and explain what `lto = false` means." (profile semantics: using-cargo)
5. "How do I hide setup lines in a doc example?" (doctest syntax: documenting-rust)
6. "Build a terminal UI with panes and mouse support in ratatui." (full-screen TUI framework, not stream-oriented CLI behaviour)
7. "Parse command-line arguments in Python with argparse." (another language)
8. "Write a bash script that greps logs and exits 1 on errors." (shell scripting)
9. "Add a `bin` field to package.json so npm installs my Node CLI globally." (Node packaging)
10. "Cross-compile my Rust library for wasm32 and set the target in `.cargo/config.toml`." (targets and config: using-cargo)

## Notes on the negatives

Negatives 1, 2, and 4 are the hard ones. They use words this skill uses (errors, tests, release profiles), but the question is about error-type design, the test harness, or Cargo semantics, which belong to the sibling skills. This skill covers those subjects only where a command-line program changes the answer: what `main` prints, what status it returns, how its binary is run from a test, and how small it ships. Negative 6 is close because a TUI is a command-line program, but its rendering and event loop are outside this skill. Its stdout, exit-code, and signal advice still applies.
