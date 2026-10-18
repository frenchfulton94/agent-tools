---
name: documenting-rust
description: Writes and fixes Rust API documentation — `///` and `//!` doc comments, crate-level docs, intra-doc links and disambiguators, doctest syntax and code-block attributes, edition-2024 merged doctests, `#[doc]` attributes (hidden, inline, alias, include_str), re-export inlining, `doc(cfg)` and `auto_cfg` badges for docs.rs, rustdoc lints, and `cargo doc` and rustdoc flags. Use when the user is writing or reviewing doc comments, adding examples to a public API, setting up docs.rs builds, or wants docs to build without warnings. Also use for symptoms that never say rustdoc - an "unresolved link" or "both a struct and a function" warning, a doctest failing with mismatched types on `?`, a doctest that is silently skipped, `line!()` or a panic pointing at `doctest_bundle_2024.rs`, a `compile_fail` example passing for the wrong reason, `feature(doc_auto_cfg)` breaking a docs.rs build, "`#[doc(cfg)]` is experimental", or a re-export rendered as a bare `pub use` line.
license: MIT
---

# Documenting Rust

Sourced from the Rust 1.99 stable documentation (the rustdoc book, Reference, Cargo book, rustc book). Every behaviour marked *measured* was checked on rustc/rustdoc/cargo **1.97.1** (aarch64-apple-darwin). Nothing below depends on 1.98 or 1.99. Check `rustc --version` before relying on a version-gated claim.

This skill covers writing docs and the syntax of doctests. *Running* tests, `cargo test` filters, and libtest flags belong to `testing-rust`. What a rustc lint means in general belongs to `fixing-rust-compile-errors`. The `[lints]` table syntax and `RUSTDOCFLAGS` precedence belong to `using-cargo`. Naming and API shape (the API Guidelines) belong to `designing-rust-apis`, and Clippy's documentation lints as policy to `linting-and-formatting-rust`.

## Corrections that stale knowledge gets wrong

### 1. Edition-2024 crates merge doctests (measured)

When the **crate's** edition is 2024, rustdoc compiles compatible doctests into one binary. Each test still runs in its own process. `cargo test --doc` prints several `running N tests` groups and ends with `all doctests ran in Xs; merged doctests compilation took Ys`. A 2021 crate never merges, even for blocks tagged `edition2024`.

- **What is merged:** blocks with `should_panic`, `no_run`, `?`, `fn main`, a single `#[macro_export]`, or inner `#![allow]` attributes. Blocks tagged with another edition (`edition2021`) form a separate merged group. **What compiles standalone:** `compile_fail`, `test_harness`, and `standalone_crate` blocks.
- **Position-dependent code breaks.** In a merged doctest, `line!()`, `file!()`, `Location::caller()`, and panic locations point into a temporary `doctest_bundle_2024.rs`, not `src/lib.rs`. An assertion on `line!()` fails. Tag such blocks `standalone_crate`.
- **A failed merged compile falls back silently.** Two doctests that both `#[macro_export]` a macro of the same name fail the merged compile. rustdoc then compiles every doctest standalone, with no error and no `merged doctests compilation` line. If a 2024 crate's doctests are slow and that line is missing, look for a doctest that cannot share a crate with the others.

### 2. `compile_fail,E0308` does not check the error code on stable (measured)

On stable the block is still a `compile_fail` test, but the code after the comma is **ignored**. `compile_fail,E0599` on code that fails with E0308 passes. Error-code checking happens only on nightly. A `compile_fail` example therefore passes when it fails for *any* reason, including a missing `use` or a typo. Before you commit one, remove `compile_fail`, run it once, and read the error.

### 3. `?` in a doctest needs the exact trailer `(())` (measured)

The implicit `fn main()` returns `()`, so a bare `?` gives E0308 "expected `()`, found `Result`". End the example with a hidden line:

```rust
/// ```
/// let n: u32 = "7".parse()?;
/// # Ok::<(), std::num::ParseIntError>(())
/// ```
```

rustdoc detects the trailer textually. `Ok::<(), io::Error>( () )`, with spaces, is not detected and fails with E0308. The longer form also works: `# fn main() -> Result<(), Box<dyn std::error::Error>> {` … `# Ok(())` `# }`. Prefer either form over `unwrap()` in examples, because users copy them.

### 4. A misspelled code-block attribute silently disables the test (measured)

` ```should-panic ` produces one `rustdoc::invalid_codeblock_attributes` warning, and the block is then treated as another language: it **does not appear in the test list at all**. Unknown words mean "not Rust" unless `rust` is also present. A README fence such as ` ```sh ` or ` ```toml ` is skipped for the same reason, which is correct.

### 5. `ignore-<x>` matches a substring of the target triple (measured)

`ignore-aarch64`, `ignore-apple`, and `ignore-windows` work because those strings appear in triples. **`ignore-macos` does not match `aarch64-apple-darwin`**, so the block runs. Use `ignore-apple` or `ignore-darwin`. Since 1.88, `ignore,ignore-x86_64` runs everywhere except x86_64. Older rustdoc ignored it everywhere, so that pairing is the backward-compatible spelling.

### 6. cfg in doctests (measured)

- Inside a doctest body, `cfg!(doc)`, `cfg!(doctest)`, and `cfg!(test)` are all **false**.
- A doctest links against the library compiled *normally*. A `#[cfg(doc)]` item exists in the rendered docs but is E0425 "cannot find function" from a doctest. A `#[cfg(doctest)]` item exists only while rustdoc *collects* doctests. It is not rendered and not callable. It is useful only as a carrier for doctests, such as hidden `compile_fail` cases or a README.
- Doctests see the **public** API only: calling a `pub(crate)` item gives E0603. Doctests on items in private modules **still run**, even though those items are not documented (the `rustdoc::private_doc_tests` lint, allow by default, flags them).
- To show platform-specific items in docs built on any host, write `#[cfg(any(windows, doc))]`.

### 7. `doc(cfg)` and `auto_cfg` are nightly-only and were redesigned (measured)

- On stable, `#[doc(cfg(...))]` and `#[doc(auto_cfg ...)]` are **E0658 "is experimental"**. Stable `cargo doc` renders no "Available on …" badges at all.
- `#![feature(doc_auto_cfg)]` is **E0557 "feature has been removed … removed in 1.92.0 … merged into `doc_cfg`"**. `#[doc(cfg_hide(...))]` is now an unknown `doc` attribute. The many crates that still write `#![cfg_attr(docsrs, feature(doc_auto_cfg))]` fail on docs.rs, which builds with nightly.
- The current form is one line in `lib.rs`: `#![cfg_attr(docsrs, feature(doc_cfg))]`. With the feature on, `auto_cfg` is **on by default**: every `#[cfg(feature = "x")]` item gets its badge with no per-item attribute (measured). Add `#[cfg_attr(docsrs, doc(cfg(...)))]` only to override the automatic text. Hide noise with `#![cfg_attr(docsrs, doc(auto_cfg(hide(...))))]`, and turn badges off with `doc(auto_cfg = false)`.
- docs.rs sets `cfg(docsrs)` itself, for the crate being documented only, so `rustdoc-args = ["--cfg", "docsrs"]` in metadata is redundant. Cargo's check-cfg knows `docsrs`, so `#[cfg(docsrs)]` raises no `unexpected_cfgs` warning (measured). Put `all-features = true` (or `features = [...]`) under `[package.metadata.docs.rs]` so that feature-gated items exist when docs.rs builds.

Full `auto_cfg` syntax: `references/rustdoc-reference.md` → *doc(cfg) and auto_cfg*.

### 8. Intra-doc links (measured)

Write links as `` [`Foo`] ``, `[Foo::bar]`, or `[text](crate::path::Item)`. Prefer them to hand-written HTML paths. They resolve in the module where the item is **defined**, even when it is re-exported.

- **Ambiguity.** When a name is in two namespaces, rustdoc warns "`Bar` is both a function and a struct". Fix it with a prefix (`struct@Bar`, `fn@Bar`, `macro@Clone`, `prim@u8`, `mod@inner`, `field@`, `method@`, `variant@`, `derive@`, `type@`, `value@`, `tyalias@`) or a suffix (`Bar()` for a function, `mac!` for a macro). For a name that is both a trait and a derive (e.g. `Clone`), the link goes to the trait without a warning.
- **Unresolvable on purpose:** methods that come only from a blanket impl (`` [`String::to_string`] `` warns "unresolved link"), and fully qualified syntax (`<Vec<u8> as IntoIterator>::into_iter`). Link to the trait method instead (`` [`ToString::to_string`] ``).
- `` [`Vec<T>`] `` resolves as `Vec`. URL fragments work: `[x](std::fmt#formatting-parameters)`.
- `` [`usize`](usize) `` warns `redundant_explicit_links`. Drop the target.
- A bare `https://…` warns `bare_urls`. Write `<https://…>`.
- A link to a private item from public docs warns `private_intra_doc_links`. `cargo doc` on a **binary** suppresses this lint and documents private items by default.

### 9. Rustdoc lints and their defaults (measured with `rustdoc -W help`)

| Warn by default | Allow by default |
|---|---|
| `rustdoc::broken_intra_doc_links` (also covers ambiguity), `private_intra_doc_links`, `invalid_codeblock_attributes`, `invalid_html_tags`, `invalid_rust_codeblocks`, `bare_urls`, `redundant_explicit_links` | `missing_docs` (a rustc lint, no prefix), `rustdoc::missing_crate_level_docs`, `private_doc_tests`, `unescaped_backticks` |

`rustdoc::missing_doc_code_examples` is **nightly-only**: on stable, naming it gives "unknown lint … is unstable". The group `rustdoc::all` covers the stable ones. A generic type in prose (`Vec<u8>` without backticks) triggers `invalid_html_tags` ("unclosed HTML tag `u8`"). Wrap it in backticks.

To gate CI, use `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps`, or `[lints.rustdoc] broken_intra_doc_links = "deny"` in `Cargo.toml` (both measured). For full coverage, add `[lints.rust] missing_docs = "warn"`. Clippy adds `missing_safety_doc` (warn by default) and, in `clippy::pedantic`, `missing_errors_doc`, `missing_panics_doc`, and `doc_markdown` (measured on clippy 0.1.97).

## Writing the docs

- **The summary is everything before the first blank line.** It appears in search results and module listings, so keep it to one sentence. Do not restate the signature in prose, because the types are already linked.
- **Sections, in std's order:** `# Examples` (at least one copy-pasteable example), then `# Panics`, `# Errors` (which `Err` variants, and when), and `# Safety` on every `unsafe fn` and `unsafe trait` (the invariants the caller must uphold). Justify each `unsafe {}` block in the body with a `// SAFETY:` comment, not a doc comment.
- **Crate root (`//!` at the top of `lib.rs`):** a one-sentence summary of where the crate fits, then a real example with no shortcuts, then the Cargo features. `#![doc = include_str!("../README.md")]` reuses the README, and its Rust fences then run as doctests. Tag README blocks ` ```rust,ignore ` (not bare `ignore`) when GitHub must still highlight them.
- **Hide lines with `# `.** Hidden lines compile but do not render. Use them for setup and for the `?` trailer. Escape a literal leading `#` as `##`.
- **`ignore` is almost never right.** Use `text` for non-Rust, `no_run` for code that must compile but cannot run in tests (network, infinite loops), and hidden lines to make an example real.
- `#[doc(hidden)]` keeps an item public but out of the docs (macro internals). `--document-private-items` still skips hidden items.
- `///` on a `let` or other statement does nothing (`unused_doc_comments`). Use `//`.
- Block doc comments end at the first `*/`, even inside a code span: `` /** `*/*.rs` */ `` is a syntax error. Prefer line comments.

## Re-exports (measured)

| Re-export | Rendered as |
|---|---|
| `pub use local_public_mod::Item;` | a "Re-exports" line, not full docs. Add `#[doc(inline)]` to inline |
| `pub use private_mod::Item;` | inlined, as if defined here |
| `pub use dep::Item;` or `pub use dep::module;` (from another crate) | inlined |
| `pub use dep;` (the whole crate) | a "Re-exports" line, unless `#[doc(inline)]` |

`#[doc(no_inline)]` forces a "Re-exports" line. Inlined items concatenate the doc comments along the chain and inherit cfgs. They do not inherit `doc(alias)`, `doc(hidden)`, `doc(inline)`, or `doc(no_inline)`.

## Commands

| Task | Command |
|---|---|
| Build and open docs | `cargo doc --open` (dependencies too). Add `--no-deps` for only the workspace |
| Include private items | `cargo doc --document-private-items` (the default for binaries) |
| Pass a flag to one crate's rustdoc | `cargo rustdoc --lib -- --default-theme=ayu`. Use `RUSTDOCFLAGS` for every invocation |
| Run only doctests | `cargo test --doc` (library targets only. A binary-only package errors with "no library targets found") |
| See doctest warnings | `cargo test --doc -- --show-output`. `unused` lints stay hidden unless `#![doc(test(attr(warn(unused))))]` |
| Clear stale pages | `cargo clean --doc`. Doc output is cumulative, so deleted items' pages persist |

Direct `rustdoc` defaults to **edition 2015** (measured: `async fn` gives E0670). Pass `--edition 2024`. Cargo passes the crate's edition. On stable, `--output-format json`, `--output-format=doctest`, `--show-coverage`, and `--document-hidden-items` all require `-Z unstable-options`, so they are nightly-only (measured).

## Where to look

Read only the file the question touches.

- `references/doctests.md` — read when writing or debugging a doctest: every code-block attribute, the preprocessing rustdoc applies, hidden-line escapes, macros in doctests, `#![doc(test(...))]`, README testing, merged-doctest details, and working directories.
- `references/rustdoc-reference.md` — read for a `#[doc]` attribute, crate-level `#![doc(...)]` keys, alias rules, full re-export rules, the intra-doc link catalogue, the full `doc(cfg)`/`auto_cfg` syntax, lint diagnostic texts, rustdoc's Markdown extensions, stable and unstable rustdoc flags, docs.rs metadata keys, and search syntax.
