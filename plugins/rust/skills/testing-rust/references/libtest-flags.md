# libtest and `cargo test` flags

Status is for **stable 1.97.1, measured**. The docs describe 1.99. Every libtest flag goes after `--` in `cargo test -- ...` (or `cargo bench -- ...`). Run `cargo test -- --help` to see the installed harness's own list.

Contents:
- [Selection and filtering](#selection-and-filtering)
- [Execution](#execution)
- [Output](#output)
- [Nightly-only flags](#nightly-only-flags)
- [Environment variables](#environment-variables)
- [Cargo-side options](#cargo-side-options)
- [Reading the output](#reading-the-output)

## Selection and filtering

| Flag | Stable | Behaviour |
|---|---|---|
| `FILTER...` (positional) | yes | Substring of the full test path. Several filters are OR-ed. Matching nothing exits 0. |
| `--exact` | yes | Filters must equal the full path, `tests::name` and not `name`. Also makes `--skip` exact. |
| `--skip FILTER` | yes | Skip tests whose path contains FILTER. Repeatable. |
| `--ignored` | yes | Run only `#[ignore]` tests. |
| `--include-ignored` | yes | Run ignored and normal tests together. |
| `--list` | yes | Print `path: test` lines and a `N tests, M benchmarks` count, then exit. Respects filters and `--ignored`. Works for doctests (`cargo test --doc -- --list`). |
| `--test` | yes | The default mode: run tests, and run each `#[bench]` once as a smoke test. |
| `--bench` | yes | Run benchmarks only. On stable there are none, so every test reports as ignored. |
| `--exclude-should-panic` | **nightly** | Skip `#[should_panic]` tests. |

## Execution

| Flag | Stable | Behaviour |
|---|---|---|
| `--test-threads N` | yes | Default is `std::thread::available_parallelism`. `N = 1` runs serially in alphabetical order. `0` is rejected: `argument for --test-threads must not be 0`. `=N` and ` N` both parse. |
| `--fail-fast` | **nightly** | Stop starting new tests in this binary after the first failure. Not the same as Cargo's `--no-fail-fast`, which is about binaries. |
| `--shuffle` | **nightly** | Random order. It prints the seed. It does not change parallelism. |
| `--shuffle-seed SEED` | **nightly** | Reproduce a shuffled order. |
| `--report-time`, `--ensure-time` | **nightly** | Per-test timing, thresholds from `RUST_TEST_TIME_UNIT`, `RUST_TEST_TIME_INTEGRATION` and `RUST_TEST_TIME_DOCTEST` (`WARN_MS,CRITICAL_MS`). |
| `--force-run-in-process` | **nightly** | Only meaningful with `-Z panic-abort-tests`. |

## Output

| Flag | Stable | Behaviour |
|---|---|---|
| `--no-capture` | yes | Do not capture stdout and stderr. Output appears live and interleaved across threads. |
| `--nocapture` | yes, hidden | Deprecated alias. Accepted silently on 1.97.1 but no longer listed in `--help`. Write `--no-capture`. |
| `--show-output` | yes | After the run, print each passing test's captured output in a `successes:` section. |
| `-q`, `--quiet` | yes | `--format terse`: one character per test (`.`, `i`, `F`). `cargo test -q` forwards it to libtest. |
| `--format pretty` | yes | The default. |
| `--format terse` | yes | As `-q`. |
| `--format json` | **nightly** | One JSON event per line. |
| `--format junit` | **nightly** | JUnit XML. It appears in `--help` but stable rejects it. |
| `--color auto\|always\|never` | yes | `auto` colours only on a tty. |
| `--logfile PATH` | yes, deprecated | Prints ``warning: `--logfile` is deprecated``. Redirect output instead. |

Neither capture flag shows the stdout of a **passing doctest** (measured on 1.97.1, both edition 2021 and 2024). A failing doctest prints its stdout and stderr under `stdout:` and `stderr:` headings.

## Nightly-only flags

On stable each one fails the run with:

```
error: The "shuffle" flag is only accepted on the nightly compiler with -Z unstable-options
```

(`"json" format`, `"shuffle-seed" option`, and so on, with the matching wording.) `-Z unstable-options` on its own gives ``error: the option `Z` is only accepted on the nightly compiler``. On nightly, write `cargo +nightly test -- -Z unstable-options --format json`.

`RUSTC_BOOTSTRAP=1` makes a stable toolchain accept them (measured with `--format json`). It is an unsupported override intended for building the compiler itself. Do not put it in CI as if it were a stable feature. If the user asks, say what it is and let them decide.

## Environment variables

| Variable | Docs status | Measured on 1.97.1 |
|---|---|---|
| `RUST_TEST_THREADS=N` | deprecated, use `--test-threads` | Still works, with no warning |
| `RUST_TEST_NOCAPTURE=1` (any value but `0`) | deprecated, use `--no-capture` | Still works, with no warning |
| `RUST_TEST_SHUFFLE`, `RUST_TEST_SHUFFLE_SEED` | deprecated, and nightly-only anyway | Silently ignored on stable |
| `RUST_BACKTRACE=1` / `full` | current | Backtrace on panic. The test failure footer suggests it. |

## Cargo-side options

These go **before** `--`.

- `--no-run`: build the test executables without running them. It prints `Executable tests/cli.rs (target/debug/deps/cli-<hash>)` for each one. Executables live in `target/debug/deps/` and are not copied to `target/debug/`. For tools, read the `executable` field of `--message-format=json` rather than parsing that text.
- `--no-fail-fast`: run every test executable even after one fails. It ends with `error: 1 target failed:` followed by the failing targets, and exit status 101.
- `-j N`: build parallelism only. Test-thread count is `-- --test-threads=N`.
- `--keep-going` does not exist on `cargo test` or `cargo bench`. Use `cargo build --tests --keep-going`, then `cargo test --no-fail-fast`.
- `-q`: quiet Cargo, and forwarded to libtest as terse output.
- `--release`: uses the `release` profile. Plain `cargo test` uses `test`, which inherits `dev`.
- `--doc`: library doctests only. Rejects other target flags (`can't mix --doc with other target selecting options`) and `--no-run` (`can't skip running doc tests with --no-run`).
- `--all-targets`: `--lib --bins --tests --benches --examples`. It never includes doctests.
- `--tests`: every target with `test = true`, meaning lib and bin unit tests plus integration tests. `--test '*'` (quoted) selects integration targets only.
- Feature flags: tests build with default features unless told otherwise. Test feature combinations explicitly with `--no-default-features`, `--features`, or `--all-features`.
- Exit status: 0 when everything passed, **including runs where filters matched nothing**. 101 on any test failure or build failure.

## Reading the output

```
     Running unittests src/lib.rs (target/debug/deps/tp-3e4e4a0252f566ad)

running 8 tests
test tests::ignored_one ... ignored, slow, needs network
test tests::big_guess - should panic ... ok
...
test result: ok. 6 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

- Sections appear in this order: `Running unittests src/lib.rs`, `Running unittests src/bin/<name>.rs` for each bin, `Running tests/<file>.rs` for each integration target, and then `Doc-tests <crate>`.
- `measured` counts benchmarks. `filtered out` counts tests excluded by filters or `--skip`.
- A failure adds a `---- <path> stdout ----` block, a `failures:` list, `test result: FAILED.`, and Cargo's hint naming the target to rerun (``error: test failed, to rerun pass `--lib` ``).
- Edition-2024 crates end the doctest section with `all doctests ran in X; merged doctests compilation took Y`.
