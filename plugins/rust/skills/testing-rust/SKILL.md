---
name: testing-rust
description: 'Writes, runs, filters, and organises Rust tests with cargo test and the libtest harness - #[test], #[should_panic], Result and ExitCode tests, #[ignore], the assert macros including assert_matches!, unit tests versus tests/ integration tests and shared helper modules, testing a binary through CARGO_BIN_EXE_*, harness = false targets, benchmarks on stable, running and filtering doctests, the test and bench profiles, code coverage, and which libtest flags are stable and which are nightly-only. Use when the user writes or debugs Rust tests, asks how to run one test or a subset, wants to see output from a passing test, has tests that pass alone but fail together, a filter that silently runs nothing, or cargo test rejecting an argument. Also use on errors such as "only accepted on the nightly compiler", "async functions cannot be used for tests", "functions using #[should_panic] must return ()", or "use of unstable library feature test", and when the user wants to benchmark without nightly.'
license: MIT
---

# Testing Rust

Sourced from the Rust 1.99 stable documentation (the Book ch. 11, the rustc book's "Tests" chapter, the Cargo Book, the Reference, std). Every behaviour marked *measured* was run on rustc and cargo 1.97.1. Nothing here needs a release newer than 1.97. On older toolchains check `rustc --version`: `assert_matches!` needs 1.96, and runtime `CARGO_BIN_EXE_*` needs Cargo 1.94.

Scope: the test harness and `cargo test`. Doctest *syntax* (fences, `# ` hidden lines, `should_panic`/`no_run`/`compile_fail` blocks, edition-2024 merging) belongs to **documenting-rust**. Reading a compile error in test code belongs to **fixing-rust-compile-errors**. Testing a CLI's behaviour end to end with crates such as `assert_cmd` belongs to **building-rust-clis**.

## The two argument lists

```
cargo test [cargo options] [ONE filter] -- [libtest options] [more filters]
```

Everything after `--` goes to each test binary (libtest). Cargo itself accepts one positional filter.

- `cargo test alpha beta` is a usage error: `` unexpected argument 'beta' found `` (measured). Write `cargo test -- alpha beta`. Multiple filters are OR-ed.
- `cargo test --test-threads=1` and `cargo test --nocapture` are rejected by Cargo, with a tip to put them after `--` (measured).
- `--test NAME` is a Cargo option that selects a test **target** (a file in `tests/`), not a test function. `cargo test --test runs_binary` fails with `` no test target named `runs_binary` `` and lists the available targets.
- A filter is a substring of the full path (`tests::parse::rejects_empty`), so a module name selects a module. A filter that matches nothing runs zero tests and **exits 0** (measured). Check the `N filtered out` count, or use `-- --list`.
- `--exact` compares against the full path including modules: `--exact alpha_works` matches nothing, `--exact tests::alpha_works` matches. `--exact` applies to `--skip` as well (measured).
- The filter goes to every binary in the run: unit, integration and doctest. Add `--lib`, `--test NAME` or `--doc` to stop building and running the others.

## Stable versus nightly libtest flags

Stable on 1.97.1 (measured): `--no-capture`, `--show-output`, `--test-threads N`, `--skip`, `--exact`, `--ignored`, `--include-ignored`, `--list`, `-q`/`--format terse`, `--format pretty`, `--color`, `--test`, `--bench`.

Nightly-only. Stable rejects each one with `error: The "<flag>" flag is only accepted on the nightly compiler with -Z unstable-options` and the run fails (measured): `--format json`, `--format junit`, `--shuffle`, `--shuffle-seed`, `--fail-fast` (libtest's own), `--exclude-should-panic`, `--report-time`, `--ensure-time`, `--force-run-in-process`. `-Z unstable-options` itself is rejected on stable. Do not suggest these for a stable toolchain. For machine-readable results on stable, parse the plain output or use a third-party runner.

Spelling: write `--no-capture`. `--nocapture` still works on 1.97.1 without a warning, but `--help` no longer lists it and the docs call it a deprecated alias.

Read `references/libtest-flags.md` for each flag's behaviour, the environment variables (`RUST_TEST_THREADS` and similar) and their status, the Cargo-side options (`--no-run`, `--no-fail-fast`, `-j`), and the output format.

## Writing tests: corrections to stale habits

- **`#[test]` takes a free, non-generic function with no arguments, and it cannot be `async`.** The compiler errors are `async functions cannot be used for tests`, `functions used as tests can not have any non-lifetime generic parameters`, and `functions used as tests can not have any arguments` (measured). For async code, use a runtime's own test attribute, such as `#[tokio::test]`, or block on the future inside a plain test.
- **A `#[test]` inside a function body never runs.** The only signal is the warning `cannot test inner items` (lint `unnameable_test_items`). Tests must be reachable from the crate root through modules.
- **Return types.** A test may return any `Termination` type. `()` passes if it does not panic, `Result<(), E: Debug>` passes on `Ok`, and `ExitCode::SUCCESS` passes. A failing `Result` test prints only `Error: ParseIntError { kind: InvalidDigit }`, with **no file or line** (measured). A failing `ExitCode` test prints nothing. Prefer `.unwrap()`/`.expect()` or an assert where the failure location matters. To assert that a call fails, use `assert!(r.is_err())` or `assert_matches!`, not `?`.
- **`#[should_panic]` requires a `()` return.** On a `Result` test the error is `` functions using `#[should_panic]` must return `()` ``. `expected = "..."` is a substring match. `#[should_panic = "..."]` is the same thing (measured). Without `expected`, any panic passes, including one from the wrong line. A mismatch prints `note: panic did not contain expected string`, followed by `panic message:` and `expected substring:`.
- **`#[ignore = "reason"]`** prints `test x ... ignored, reason` (measured). Ignored tests are still compiled.
- **`assert_matches!` is stable since 1.96 and needs an import.** Write `use std::assert_matches;` (without it: `` cannot find macro `assert_matches` in this scope ``, measured on 1.97.1). The form is `assert_matches!(v, Some(x) if x > 200, "context {v:?}")`, and a failure prints `` assertion `left matches right` failed `` with both sides. Prefer it to `assert!(matches!(..))`, which prints neither value. `debug_assert_matches!` also exists.
- **`assert_eq!` names its operands `left` and `right`**, not expected/actual, and both need `PartialEq + Debug`. The custom message follows the operands and is appended after `failed:`.
- **Panic headers carry a thread id:** `thread 'tests::eq_fails' (1773553) panicked at src/lib.rs:59:21:` (measured). Do not pattern-match the older `thread 'x' panicked at` form in scripts or snapshot tests.
- **`#[bench]` is nightly-only** (`` E0658 use of unstable library feature `test` ``). See *Benchmarks on stable* below.

## How a run executes

- Each test target is a separate executable. Cargo runs the executables **one after another**, and libtest runs the tests inside one executable **in parallel threads of one process**, by default as many as `available_parallelism`. Doctests run afterwards, each in its own process.
- **Shared process state is the usual reason a test passes alone but fails with the others.** The working directory, environment variables, and statics are shared. Confirm with `-- --test-threads=1`. Edition 2024 made `std::env::set_var` and `remove_var` `unsafe` for exactly this reason. Do not "fix" the race by wrapping the call in `unsafe`. Pass configuration explicitly, or serialise those tests.
- **The working directory is the package root**: unit, integration and doctests, even when `cargo test` starts from a subdirectory or from the workspace root (measured). For fixtures, prefer `env!("CARGO_MANIFEST_DIR")`. A test binary run directly from `target/` uses the caller's directory instead.
- **Order is alphabetical** by full path (visible with `--test-threads=1`, measured). Random order (`--shuffle`) is nightly-only.
- **Cargo stops at the first failing executable.** When unit tests fail, integration tests and doctests do not run at all. `cargo test --no-fail-fast` runs every target and still exits 101 (measured). Libtest's `--fail-fast`, which stops *within* a binary, is nightly-only.
- **Output capture.** Passing tests' stdout and stderr are hidden. `--no-capture` prints it live and interleaved. `--show-output` prints it after the run, grouped per test. A passing **doctest's** output is never shown: neither flag reveals it on 1.97.1 (measured). Make the doctest fail, or move the check into a unit test.

## Selecting what to run

| Goal | Command |
|---|---|
| Library unit tests only | `cargo test --lib` |
| One integration file `tests/api.rs` | `cargo test --test api` |
| All integration tests, no unit tests | `cargo test --test '*'` (`--tests` also runs lib and bin unit tests) |
| One test, exactly | `cargo test --lib -- --exact tests::parse::rejects_empty` |
| Doctests only | `cargo test --doc` (cannot be combined with `--lib` and similar flags, or with `--no-run`) |
| Everything except doctests | `cargo test --all-targets`: it **excludes** doctests (measured) |
| One workspace member | `cargo test -p NAME`. `--workspace` covers all members |
| Ignored tests | `-- --ignored` (only those) or `-- --include-ignored` (all) |
| What would run | `-- --list` (respects filters, runs nothing) |

Doctests run only for the library target. They are named `src/lib.rs - path::item (line N)`, and in a workspace the name starts with the member directory: `m1/src/lib.rs - f (line 1)` (measured). Filter them like any test: `cargo test --doc parse`.

## Profiles

- `cargo test` uses the `test` profile, which inherits `dev`. The measured flags are `-C debuginfo=2` with no optimisation, regardless of what the Cargo docs' prose says. `[profile.test] opt-level = 1` speeds up slow tests and applies to the tested crate (measured).
- `cargo test --release` uses the `release` profile, and `cargo bench` uses `bench`, which inherits `release`.
- `--profile=debug`, which the Cargo docs suggest for debugging a test, fails with `` profile name `debug` is reserved `` (measured). Use the default profile or a custom one that `inherits = "dev"`.
- `panic = "abort"` is ignored when tests are built. libtest needs unwinding, so the test and its dependencies are built with `unwind` (a `should_panic` test passed under `[profile.dev] panic = "abort"`, measured). Test-per-process with abort is nightly-only (`-Z panic-abort-tests`).

## Benchmarks on stable

`#[bench]` and `test::Bencher` are nightly-only. On stable, declare the bench target with `harness = false` and supply `main`, either through a framework crate (Criterion and divan are the common ones) or by hand with `std::hint::black_box` and `std::time::Instant`:

```toml
[[bench]]
name = "parse"      # benches/parse.rs
harness = false
```

`cargo bench` builds with the `bench` profile and passes `--bench` plus any filter to the binary (measured: `["somefilter", "--bench"]`), so a hand-written `main` must tolerate that argument. `cargo test` does not run bench targets by default.

## Testing a binary

Integration tests of a package with a `[[bin]]` get `env!("CARGO_BIN_EXE_<name>")`, the absolute path to the built binary, which Cargo builds first. `<name>` is the bin name verbatim, hyphens included: `CARGO_BIN_EXE_my-tool`. It is set only for **the same package's** binaries. Another workspace member's test fails with `` environment variable `CARGO_BIN_EXE_x` not defined at compile time `` (measured). Since Cargo 1.94 it is also set at runtime (`std::env::var`, measured). `env!("CARGO_TARGET_TMPDIR")` gives a scratch directory under `target/` for integration tests, which Cargo creates but never cleans. Logic that only lives in `src/main.rs` cannot be `use`d from `tests/`. Move it into `src/lib.rs` and keep `main` thin.

Read `references/test-organisation.md` when laying out tests: unit versus integration, shared helpers in `tests/common/mod.rs`, consolidating many integration files into one binary, `harness = false` test targets, the `test`/`doctest`/`bench` target keys, and dev-dependency gotchas.

## Large failing runs

When a run fails with more than a few tests, or the output is long, delegate to the plugin's **rust-build-triage** agent. It runs the suite with `--no-fail-fast`, reruns each failure alone, and returns only the failing names with their assertion output.

## Where to look

- `references/libtest-flags.md`: read when choosing or debugging a flag, an environment variable, or the output format, or when a flag is rejected.
- `references/test-organisation.md`: read when creating or restructuring test files, sharing helpers, testing a binary, or configuring test or bench targets in `Cargo.toml`.
- `references/coverage-and-cross.md`: read when measuring test coverage (`-C instrument-coverage`) or running tests for a non-host target (runners, `--no-run`, `panic = "abort"` targets).
