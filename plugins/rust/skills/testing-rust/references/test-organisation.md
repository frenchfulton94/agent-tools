# Organising Rust tests

Behaviour marked *measured* was run on cargo 1.97.1.

Contents:
- [Unit tests](#unit-tests)
- [Integration tests](#integration-tests)
- [Shared helpers](#shared-helpers)
- [One binary instead of many](#one-binary-instead-of-many)
- [Testing a binary crate](#testing-a-binary-crate)
- [Custom harness: `harness = false`](#custom-harness-harness--false)
- [Target keys that change what `cargo test` runs](#target-keys-that-change-what-cargo-test-runs)
- [Dev-dependencies and features](#dev-dependencies-and-features)
- [Unsafe code](#unsafe-code)

## Unit tests

```rust
#[cfg(test)]
mod tests {
    use super::*;          // private items of the parent are reachable

    #[test]
    fn rejects_empty() { /* ... */ }
}
```

- Unit tests live beside the code and can test private functions.
- `cfg(test)` is set **only for the crate being tested**. A `#[cfg(test)] pub fn` helper in `src/lib.rs` does not exist for that package's own integration tests, because they link the library built without `cfg(test)`. The error is `` E0425 cannot find function `only_in_test` in crate `tp` `` (measured). Put helpers for integration tests in `tests/common/`, or behind a Cargo feature that the tests enable.

## Integration tests

- Each `tests/*.rs` file is its own crate and its own executable. It reaches the library through `use cratename::...` and sees only the public API. It needs no `#[cfg(test)]`, and `cfg(test)` is set inside it (measured).
- Each file adds a link step and a `Running tests/<file>.rs` section. The binaries run one after another, not in parallel.
- Select one file with `cargo test --test <file stem>`.

## Shared helpers

- `tests/common/mod.rs` plus `mod common;` in each test file that needs it. Subdirectories of `tests/` are not compiled as separate test targets.
- `tests/common.rs` would become a test target of its own, with an empty `Running tests/common.rs` section (measured).
- Every test file compiles its own copy of `common`, so a helper one file does not use gives `warning: function ... is never used` for that file (measured). Put `#![allow(dead_code)]` at the top of `common/mod.rs`, or split the helpers.

## One binary instead of many

The Cargo docs recommend consolidating many integration files into one target, which means fewer link steps and lets libtest run all of them in parallel:

```
tests/it/main.rs     mod parse; mod render;
tests/it/parse.rs
tests/it/render.rs
```

Cargo discovers `tests/<dir>/main.rs` as a target named `<dir>` (measured: `Running tests/it/main.rs`, tests named `parse::...`). Run it with `cargo test --test it`, and filter by module with `cargo test --test it -- parse::`.

## Testing a binary crate

- A crate with only `src/main.rs` cannot be `use`d from `tests/`. Move the logic into `src/lib.rs` and leave `main` to parse arguments, call the library, and report errors. Unit tests in `main.rs` still run, under `Running unittests src/main.rs`.
- To exercise the built executable, use `env!("CARGO_BIN_EXE_<bin-name>")` with `std::process::Command`. The name is verbatim, hyphens included. Cargo builds the binary before the integration test. The variable is set only for binaries of the **same package**. A test in another workspace member gets `` environment variable `CARGO_BIN_EXE_x` not defined at compile time `` (measured). It is set at runtime as well since Cargo 1.94. It is not set when the bin's `required-features` are not enabled.
- `env!("CARGO_TARGET_TMPDIR")` (`target/tmp`) is a scratch directory for integration tests and benches. Cargo creates it but never cleans it, so use a unique subdirectory per test because tests run in parallel.
- The working directory is the package root. For fixtures, `Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/data/x")` works from any caller.
- CLI-specific assertion crates (`assert_cmd`, `predicates`, `snapbox`) and output conventions belong to **building-rust-clis**.

## Custom harness: `harness = false`

```toml
[[test]]
name = "custom"        # tests/custom.rs, must define fn main
harness = false
```

- No libtest. The file supplies `main`, and the target passes if and only if the process exits 0 (measured: `exit(1)` failed the run with `process didn't exit successfully`).
- Arguments after `--` reach `main` unchanged (`cargo test --test custom -- fail` gave `["fail"]`, measured). `cfg(test)` is still set.
- Uses include data-driven suites, test frameworks such as `libtest-mimic` that generate tests at runtime, and Criterion or divan benches (`[[bench]] harness = false`). Custom test frameworks through `#![feature(custom_test_frameworks)]` are nightly-only.
- A `harness = false` bench receives `--bench` as an argument from `cargo bench` (measured).

## Target keys that change what `cargo test` runs

| Key | Default | Effect |
|---|---|---|
| `test` | true for lib, bins, tests; false for examples and benches | Whether `cargo test` builds and runs the target's tests. Selecting a target by name (`--example x`) ignores it. |
| `doctest` | true for lib only | `[lib] doctest = false` turns doctests off. Bins never run doctests. |
| `bench` | true for lib, bins, benches | Whether `cargo bench` runs it. |
| `harness` | true | `false` means you supply `main`. |
| `required-features` | none | The target is skipped when the features are off. |

- `cargo test` **compiles examples** to check that they build, but runs their `#[test]`s only with `test = true`.
- `cargo test` does not run bench targets (measured with a `harness = false` bench). `cargo bench` runs lib and bin unit-test binaries in bench mode as well, which is why a `running 0 tests` section appears.

## Dev-dependencies and features

- `[dev-dependencies]` are available to tests, examples, and benches only, never to the library or bins.
- Resolver 2 unifies a dev-dependency's feature requests into normal dependencies only when building targets that need them. `cargo test` can therefore build a dependency with **more features** than `cargo build`. Code that compiles under test can fail to build normally, and the reverse. Check with `cargo build` as well, or `cargo tree -e features`.
- Tests run with default features only. Cover other combinations explicitly (`--no-default-features`, `--features x`, `--all-features`, or `cargo hack --feature-powerset` from crates.io).
- A dev-dependency cycle, where `foo` dev-depends on `bar` and `bar` depends on `foo`, links two copies of `foo` into the unit tests. Types from `bar`'s `foo` then do not match the local ones. Move those tests to `tests/`, which uses the single library copy.

## Unsafe code

Run the suite under Miri to catch undefined behaviour: `cargo +nightly miri test`. It needs the nightly toolchain and the `miri` component. Rules for unsafe code itself belong to **writing-rust**.
