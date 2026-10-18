# Doctests: syntax and attributes

Rustdoc book (Rust 1.99 docs). Items marked *measured* were checked on rustdoc 1.97.1. For running doctests (`cargo test` selection, libtest flags), see `testing-rust`.

Contents:
- [Code-block attributes](#code-block-attributes)
- [What rustdoc does to a code block](#what-rustdoc-does-to-a-code-block)
- [Hidden lines](#hidden-lines)
- [Using `?`](#using-)
- [Macros in doctests](#macros-in-doctests)
- [Crate-wide doctest attributes](#crate-wide-doctest-attributes)
- [Merged doctests (edition 2024)](#merged-doctests-edition-2024)
- [cfg, visibility, and README tests](#cfg-visibility-and-readme-tests)
- [Working directories and direct rustdoc use](#working-directories-and-direct-rustdoc-use)

## Code-block attributes

An untagged fence and ` ```rust ` are both Rust doctests. A doctest passes when it compiles and runs without panicking. Separate attributes with commas, spaces, or tabs. A comment goes in parentheses: ` ```ignore (needs a database) `.

| Attribute | Effect |
|---|---|
| `ignore` | Not compiled. Reported as `ignored`. The book calls it "almost never what you want" |
| `text` (or any unknown word) | Not Rust, not tested. A *misspelled* attribute (`should-panic`) also lands here, with one `invalid_codeblock_attributes` warning (measured) |
| `should_panic` | Must compile and must panic |
| `no_run` | Compiled, not run. Reported as `- compile` (measured) |
| `compile_fail` | Passes if compilation fails. On a block that compiles: "Test compiled successfully, but it's marked `compile_fail`." (measured) |
| `compile_fail,E0308` | On stable the error code is **ignored**: any compile error passes (measured). Checked on nightly only |
| `edition2015` … `edition2024` | Compile this block with that edition |
| `standalone_crate` | Opt out of edition-2024 merging |
| `test_harness` | Compile with `--test`, so the block's `#[test]` functions run instead of `main` |
| `ignore-<substring>` | Ignored when the target triple contains the substring: `ignore-x86_64`, `ignore-windows`, `ignore-apple`. `ignore-macos` matches no triple (measured). Repeatable |
| `ignore,ignore-x86_64` | 1.88+: ignored only on x86_64 (measured on aarch64: runs). Older rustdoc ignores it everywhere |
| `rust` | Forces Rust. Needed alongside an unknown word, e.g. `rust,ignore` in a README that GitHub also renders |
| `custom,{.language-c}` or `custom,{class=language-c}` | Not Rust: renders without highlighting, with the CSS class. **Without `custom`, `{.x}` only adds a class and the block is still a Rust doctest** |

An indented (four-space) code block is also a doctest but cannot take attributes. Use fences.

## What rustdoc does to a code block

In order:

1. Adds `#![allow(unused_variables, unused_assignments, unused_mut, unused_attributes, dead_code)]`.
2. Adds the attributes from `#![doc(test(attr(...)))]`.
3. Keeps leading `#![...]` lines as crate attributes.
4. Inserts `extern crate <yourcrate>;` unless the block has its own `extern crate` or the crate sets `#![doc(test(no_crate_inject))]`.
5. Wraps the code in `fn main() { … }` unless the text contains `fn main`.

## Hidden lines

A line starting with `# ` (or a lone `#`) is compiled but not rendered. To render a literal leading `#`, write `##`: `/// ## bar # baz` renders `# bar # baz`. Only the first `#` needs escaping. A macro token `##tag` is written `###tag`.

## Using `?`

The generated `main` returns `()`, so a bare `?` gives E0308. Two fixes:

```rust
/// ```
/// use std::io;
/// let s = std::fs::read_to_string("Cargo.toml")?;
/// # Ok::<(), io::Error>(())
/// ```
```

The trailer must end in `(())` with no whitespace. `( () )` is not detected and fails with E0308 (measured). Alternatively, write the wrapper as hidden lines: `# fn main() -> Result<(), Box<dyn std::error::Error>> {` at the top, `# Ok(())` and `# }` at the bottom.

## Macros in doctests

In 2018+ editions, a `#[macro_export]` macro is reachable by path. `mycrate::mac!()` or `use mycrate::mac;` works in a doctest with no `#[macro_use] extern crate` (measured). The book's `# #[macro_use] extern crate foo;` recipe is only needed for 2015-edition crates.

A doctest that itself defines a `#[macro_export]` macro without its own `fn main` triggers `non_local_definitions`. Give that block an explicit `fn main() { … }`.

## Crate-wide doctest attributes

- `#![doc(test(attr(deny(warnings))))]` turns doctest warnings into errors. It **also overrides the default `allow(unused_variables, …)`**: an example with an unused `let x = 5;` then fails (measured). Use `deny(warnings, ...)` deliberately, or `warn(unused)` to see such warnings without failing.
- `#![doc(test(attr(...)))]` may also sit on a module. The module's list is **appended** to the crate's list, so both apply.
- `#![doc(test(no_crate_inject))]` is crate-level only. Inside a module, rustc warns "this attribute can only be applied at the crate level" (`invalid_doc_attributes`, measured).
- Doctest warnings are captured. To see them, run `cargo test --doc -- --show-output`. `unused` lints stay silent because of step 1 above. Add `#![warn(unused)]` to one block, or `#![doc(test(attr(warn(unused))))]` to the crate.

## Merged doctests (edition 2024)

Measured on 1.97.1:

- Merging depends on the **crate's** edition. A 2021 crate does not merge, even for blocks tagged `edition2024`.
- In a 2024 crate, untagged blocks form one merged group. Blocks tagged with another edition form their own merged group. `compile_fail`, `test_harness`, and `standalone_crate` blocks compile separately.
- Merged and run as normal: `should_panic`, `no_run`, blocks using `?`, blocks with their own `fn main`, a single `#[macro_export]`, and blocks with inner `#![allow(...)]`.
- Each test still runs in its own process, so global state (panic hooks, env vars) does not leak between tests.
- In merged code, `line!()`, `file!()`, `Location::caller()`, and panic locations refer to a temporary `doctest_bundle_2024.rs` (measured: `line!()` returned 6 where standalone returned 3). Mark position-sensitive blocks `standalone_crate`.
- When the merged compile fails, for example because two blocks `#[macro_export]` the same macro name, rustdoc silently compiles everything standalone. The output then lacks the final `merged doctests compilation took …` line.
- The book measured the core library at 775 s total compile time before merging against 102 s wall time after. Slow doctests in a 2024 crate with no merge line are worth investigating.

## cfg, visibility, and README tests

- `cfg!(doc)`, `cfg!(doctest)`, and `cfg!(test)` are false inside a doctest body (measured).
- `#[cfg(doc)]` items render in docs but do not exist when doctests link the crate (E0425, measured).
- `#[cfg(doctest)]` items exist only while rustdoc collects tests. They are neither rendered nor callable (measured). Use them as carriers:

  ```rust
  /// ```compile_fail
  /// fn assert_send<T: Send>() {}
  /// assert_send::<mycrate::Handle>(); // Handle must stay !Send
  /// ```
  #[cfg(doctest)]
  pub struct HandleIsNotSend;

  #[doc = include_str!("../README.md")]
  #[cfg(doctest)]
  pub struct ReadmeDoctests;
  ```

  If the README is already the crate docs (`#![doc = include_str!("../README.md")]`), its examples run already. The `ReadmeDoctests` carrier then runs them twice (measured).
- Doctests link against the public API only. `pub(crate)` items are E0603. Test private items with unit tests (see `testing-rust`). Doctests on items inside private modules still run (measured).
- Only library targets have doctests. `cargo test --doc` on a binary-only package errors "no library targets found".

## Working directories and direct rustdoc use

- Under Cargo (1.72+), doctests are compiled from the **workspace root**, which affects `file!()` and diagnostic paths. They run with the **package root** as the working directory, which affects relative file paths in examples.
- Direct `rustdoc --test src/lib.rs` defaults to edition 2015 (measured). Pass `--edition 2024 --crate-name NAME`, plus `-L`/`--extern` for dependencies. Cargo does all of this for you.
- Stable `rustdoc` flags (measured on 1.97.1): `--test-args ARGS` (to libtest), `--test-run-directory DIR`, and `--test-runtool PROG` with repeated `--test-runtool-arg ARG` (runs `PROG args… <doctest-binary>`, e.g. under an emulator).
- Nightly-only, behind `-Z unstable-options`: `--persist-doctests DIR`, `--no-capture`, `--test-builder`, `--doctest-build-arg`, and `--output-format=doctest`, which prints JSON describing each doctest (error measured on stable).
