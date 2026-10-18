---
name: linting-and-formatting-rust
description: Sets Rust lint and format policy - which Clippy groups and lints to enable for a library, a binary, or CI and which never to enable wholesale, a tested starting [lints] block, clippy.toml keys and defaults, MSRV-aware linting, Clippy attributes, Clippy in CI (build.warnings versus -D warnings, --all-targets, --all-features), cargo clippy --fix, rustfmt and rustfmt.toml (stable versus nightly-only options, style_edition, edition pitfalls), and the Style Guide rules rustfmt does not apply. Use when the user wants to set up or review Clippy or rustfmt, choose lints or groups such as pedantic, nursery, or restriction, write a clippy.toml or rustfmt.toml, or add lint and format checks to CI. Also use for symptoms - correctness lints no longer fail the build, "error reading Clippy's configuration file", a rustfmt option that warns about nightly or does nothing, cargo fmt disagreeing with an editor or CI, a toolchain bump flooding CI with new warnings, or a lint from the Clippy site that is unknown.
license: MIT
---

# Linting and formatting Rust

This skill sets policy: which lints run, how they are configured, how CI enforces them, and how code is formatted. What one lint means and how to fix the code it flags belongs to `fixing-rust-compile-errors`. The `[lints]` table's syntax and workspace inheritance belong to `using-cargo`.

**Version basis.** Sourced from the Clippy book, the stable Clippy lint list (830 lints), and the Rust Style Guide, read in full on 2026-10-17. Both Clippy documents track Clippy 1.99 and newer. Everything marked *measured* was run on clippy 0.1.97 and rustfmt 1.9.0 from the **1.97.1** toolchain. Items marked **1.98+** come from the docs and could not be measured: check `cargo clippy --version` before relying on one.

## Corrections to carry into every answer

All measured on 1.97.1.

- **Never set `clippy::all`.** `#![warn(clippy::all)]`, `[lints.clippy] all = "warn"`, and `-W clippy::all` all **downgrade `correctness` from deny to warn**: `x == x` became a warning and the build passed. `all` is only the five default groups, so warning on it adds nothing. The Clippy book's own `#![warn(clippy::all, clippy::pedantic)]` example falls into this. Add only the allow-by-default groups or lints you want.
- **Never enable `restriction` as a group.** It fires `blanket_clippy_restriction_lints` ("`clippy::restriction` is not meant to be enabled as a group"), and its lints contradict each other and the defaults: `implicit_return` flagged every function that `needless_return` did not. Cherry-pick restriction lints one by one. Treat `nursery` the same way: the book calls it "buggy or need more work".
- **Group membership has moved.** A model's memory is stale for these: `module_name_repetitions` (once pedantic), `mutex_atomic`, and `mutex_integer` are **restriction**. `uninlined_format_args`, `single_char_pattern`, and `nonminimal_bool` are **pedantic**, so `println!("{}", x)` is not flagged by default. `redundant_clone`, `needless_collect`, `or_fun_call`, `use_self`, and `significant_drop_in_scrutinee` are **nursery**, so a plain `cargo clippy` never shows them. To check a group, read the `Lint groups loaded by this crate` section at the end of `clippy-driver -W help`. `cargo clippy --explain` does not print the group.
- **The Clippy website lists lints the installed Clippy lacks.** The site (`/stable/` and `/master/`) documents 16 lints that 1.97.1 does not have. Its "Added in" field is not reliable either: `map_or_identity` says 1.97.0 and is absent from 1.97.1. In `[lints]` an unknown Clippy lint is only `warning[E0602]: unknown lint` under Clippy, but it fails CI once warnings are denied. Check a name with `cargo clippy --explain NAME`, which prints `unknown lint: NAME` for a lint the toolchain does not have. The "for further information" link in each warning is versioned (`rust-clippy/rust-1.97.0/index.html#…`), so it matches the installed toolchain.
- **`clippy.toml` holds values, never levels**, and an **unknown key is a hard error**: "error reading Clippy's configuration file: unknown field `…`", exit 101, nothing linted. Keys copied from the current book can be newer than the toolchain. The error lists every valid key.
- **`msrv` must be quoted.** `msrv = 1.70` fails ("invalid type: floating point `1.7`, expected a string"). Write `msrv = "1.70"`. Usually leave it out: it defaults to `rust-version` in `Cargo.toml`.
- **A list key replaces its default unless it contains `".."`.** `doc-valid-idents = ["MyCorp"]` drops the ~80 built-in words (GitHub, JavaScript, macOS, …), and `doc_markdown` starts flagging them. Write `doc-valid-idents = ["MyCorp", ".."]`. The same applies to `disallowed-names`, `allowed-idents-below-min-chars`, `allowed-prefixes`, and `allow-renamed-params-for`.
- **`avoid-breaking-exported-api = true` (default) hides 19 lints on a library's public items**, among them `upper_case_acronyms`, `wrong_self_convention`, `trivially_copy_pass_by_ref`, `unnecessary_wraps`, `enum_variant_names`, and `needless_pass_by_ref_mut`. `pub struct HTTP` passed while private `struct JSON` was flagged. Set it to `false` for a library with no outside users: a workspace-internal crate, or the `lib.rs` of an application. It has no effect in a binary crate, whose `pub` items are not exported, so the lints fire there anyway.
- **`style_edition = "2024"` is stable** in `rustfmt.toml`, despite the Style Guide calling it nightly-only. It re-sorts imports (`U8, Zeta, alpha, u8, u16` replaces `alpha, u16, u8, Zeta, U8`) and puts a short `if x { 0 } else { 1 }` tail expression on one line. Switch it in a commit of its own: the diff is large.
- **Bare `rustfmt file.rs` is edition 2015**, both the language and the style edition. It rejects let chains ("let chains are only allowed in Rust 2024 or later") and sorts imports the old way. `cargo fmt` passes `--edition` from `Cargo.toml`. For a single file, run `rustfmt --edition 2024 file.rs`.
- **Most rustfmt options are nightly-only, and stable ignores them silently.** `imports_granularity`, `group_imports`, `wrap_comments`, `format_code_in_doc_comments`, `ignore`, `required_version`, and 49 more print "can't set …, unstable features are only available in nightly channel" and exit 0 with the option ignored. Only 28 options are stable (`references/rustfmt-and-style.md`).

## A starting `[lints]` block

Measured: each block compiled against a sample crate. Every listed lint fired on code written to trigger it, with no `unknown_lints` and no `lint_groups_priority` error.

**Library:**

```toml
[lints.rust]
missing_docs = "warn"                    # every public item carries a doc comment
missing_debug_implementations = "warn"   # public types implement Debug (API Guidelines C-DEBUG)
unreachable_pub = "warn"                 # `pub` that is not reachable from the crate root becomes pub(crate), so the real API is visible
unsafe_code = "deny"                     # deny, not forbid: one audited block can still opt out with #[expect(unsafe_code, reason = "…")]

[lints.clippy]
pedantic = { level = "warn", priority = -1 }   # production-ready per the Clippy book; priority -1 lets the lines below override it
must_use_candidate = "allow"             # its own docs say "Expect many false positives"
undocumented_unsafe_blocks = "warn"      # every unsafe block carries a // SAFETY: comment
allow_attributes_without_reason = "warn" # every #[allow] and #[expect] says why
dbg_macro = "warn"                       # a stray dbg! fails CI once warnings are denied
todo = "warn"                            # the same for todo!()
print_stdout = "warn"                    # a library must not write to its caller's stdout or stderr
print_stderr = "warn"
```

**Binary:** keep `unsafe_code`, `pedantic`, `undocumented_unsafe_blocks`, `allow_attributes_without_reason`, `dbg_macro`, and `todo`. Drop the rest. `missing_docs`, `missing_debug_implementations`, and `unreachable_pub` serve a library's callers. `must_use_candidate`, `missing_errors_doc`, and `missing_panics_doc` never fire in a binary crate (measured), so they need no `allow`. Printing is a binary's job.

For a workspace, put the same tables under `[workspace.lints.rust]` and `[workspace.lints.clippy]`. A member that writes `[lints] workspace = true` cannot add a lint of its own: Cargo rejects the manifest with "cannot override `workspace.lints` in `lints`" (measured). Put a member's extra levels in its crate root (`#![warn(clippy::unwrap_used)]`), or give it a full table of its own. `lint_groups_priority` checks inherited workspace lints too: a group at the default priority 0 beside an `allow` failed the build (measured).

Before adding a lint, read `cargo clippy --explain NAME`. It prints the installed version's text, its "Known issues", and its `clippy.toml` keys with their defaults. Read `references/choosing-lints.md` when picking further lints: worth-enabling lists per group, restriction lints that conflict in pairs, lints with documented false positives, and every lint and group move between 1.97 and the docs.

## `clippy.toml`

- Lookup: `CLIPPY_CONF_DIR` if set, else the package directory, walking up to the filesystem root, so a workspace root's file covers every member. `.clippy.toml` beats `clippy.toml` with a warning. The book calls the file "unstable and may be deprecated", so prefer `[lints]` for anything that is a level.
- An edit to an existing `clippy.toml` triggers a re-check. A **newly created** one did not: Clippy replayed the cached result until a source file changed (measured). After adding the file, `touch` a source file.
- Keys worth knowing: `avoid-breaking-exported-api` (above); `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-print-in-tests`, `allow-dbg-in-tests`, and `allow-indexing-slicing-in-tests`, which all default to **false**, so enabling `unwrap_used` and its kin flags test code too; `allow-unwrap-types = ["std::sync::LockResult"]` to exempt `.lock().unwrap()`; `check-private-items` (default false) for the `missing_*_doc` lints; `disallowed-methods`, `disallowed-types`, and `disallowed-macros`, whose lints are already warn by default and need only the list.

Read `references/clippy-toml.md` for every key with its default, the `disallowed-*` entry syntax, and the keys the docs list but 1.97 rejects.

## MSRV

- Setting `rust-version` in `Cargo.toml` is enough. About 85 lints then hold back suggestions the MSRV cannot compile: `manual_strip` went silent at `rust-version = "1.40"`. `incompatible_msrv` (warn) flags std APIs newer than the MSRV, which rustc itself never does: `x.is_multiple_of(3)` under `rust-version = "1.80"` warned "this item is stable since `1.87.0`".
- A `clippy.toml` `msrv` that disagrees wins, with the warning "the MSRV in `clippy.toml` and `Cargo.toml` differ".
- `#[clippy::msrv = "1.40"]` on an item (a fn, a mod) works on stable and scopes the MSRV to that item. The **inner** form `#![clippy::msrv = "…"]` is `error[E0658]: custom inner attributes are unstable`. It breaks `cargo build` too, not just Clippy. The lint list's `#![cfg_attr(test, clippy::msrv = "…")]` fails the same way as soon as the cfg is active (under `--all-targets`).

## Attributes and cfg

- `#[expect(clippy::lint, reason = "…")]` beats `allow`: Clippy warns "this lint expectation is unfulfilled" when the lint stops firing. `cargo build` does not check expectations on Clippy lints, so a stale one surfaces only under `cargo clippy` (measured).
- `#[clippy::format_args]` on a `macro_rules!` that forwards to `format_args!` (Clippy 1.85+) makes the format-string lints check the macro's arguments. Add it to a library's logging or formatting macros.
- `#[clippy::has_significant_drop]` on a guard-like type makes the `significant_drop_*` lints treat it like a `MutexGuard`.
- `cfg(clippy)` is set under Clippy and needs no `check-cfg` declaration. `#[cfg(not(clippy))]` hides code (a huge generated `include!`) from Clippy; give it a `#[cfg(clippy)]` stub so the crate still compiles. `cfg(feature = "cargo-clippy")` is the old spelling, and `deprecated_clippy_cfg_attr` flags it.

## Clippy in CI

```bash
cargo fmt --all --check
CARGO_BUILD_WARNINGS=deny cargo clippy --workspace --all-targets --all-features --keep-going
```

- **`CARGO_BUILD_WARNINGS=deny`** (Cargo 1.97+) fails on warnings from workspace packages, rustc's included. It does not invalidate the cache. `-- -D warnings` re-checked every workspace crate, and the next plain `cargo clippy` re-checked them again (measured). `RUSTFLAGS=-Dwarnings`, which the book's CI samples use, is worse still: it reaches every dependency and rebuilds the whole graph. Set it as an environment variable in CI rather than `build.warnings` in `.cargo/config.toml`, which would also fail every local build on a warning.
- **`--keep-going`.** Without it, a run stopped at the first package with warnings. With `build.warnings` and `--keep-going`, every package was reported, including dependents of the failing one. Under `-D warnings` a dependent is never checked at all, `--keep-going` or not, because its dependency failed to compile (measured).
- **`--all-targets`**: plain `cargo clippy` lints only the library and binaries, never tests, examples, or benches. **`--all-features`**: by default only default features are linted. Drop it if features are mutually exclusive, and test combinations as `using-cargo` describes. **`--workspace`**: at a root that is also a package, commands act on that package alone.
- **Older Cargo:** `cargo clippy --workspace --all-targets --all-features -- -D warnings`.
- **Pin the toolchain** (`rust-toolchain.toml` with `components = ["clippy", "rustfmt"]`). Clippy ships every six weeks with new lints, so an unpinned CI starts failing on code nobody changed. The `minimal` rustup profile omits both components.
- `cargo clippy -p crate` also lints that crate's workspace path dependencies. Add `--no-deps` to lint only the named crate.

## `cargo clippy --fix`

Pass `--all-targets`. `--help` says `--fix` implies it, but on 1.97.1 it fixed only `src/lib.rs` and left `tests/` alone (measured). It applies only `MachineApplicable` suggestions, so warnings marked `MaybeIncorrect` remain by design. It refuses a dirty tree; pass `--allow-dirty` only after the user agrees. Review the diff: `redundant_pattern_matching`'s fix changes when a lock guard drops. Reading what a fix did belongs to `fixing-rust-compile-errors`.

## rustfmt

- Config: `rustfmt.toml` or `.rustfmt.toml`, found by walking up from the file. If both exist, `.rustfmt.toml` wins, with no warning (measured). An unknown key only warns ("Unknown configuration option"), the opposite of `clippy.toml`. A value of the wrong type fails with exit 1.
- **Edition precedence**, measured: `cargo fmt` passes `--edition` from `Cargo.toml`, which **overrides `edition` in `rustfmt.toml`**. `style_edition` overrides both. So `edition = "2024"` in `rustfmt.toml` helps only bare `rustfmt`. A 2021 crate that wants the 2024 style sets `style_edition = "2024"`, and a 2024 crate that wants the old style sets `style_edition = "2021"`.
- `cargo fmt` in a workspace member formats that member only. At a virtual root, or with `--all`, it formats every member. `--check` prints a diff and exits 1. `cargo fmt` formats `.rs` files only, never `Cargo.toml`.
- **Skipping:** `#[rustfmt::skip]` works on items, statements, and expressions. Inner `#![rustfmt::skip]` is E0658 on stable and breaks the build. To skip a whole file, put `#[rustfmt::skip]` on its `mod` declaration. Files marked `@generated` **are** formatted on stable (measured), and `ignore` is nightly-only, so the `mod` attribute is the stable way to protect generated code.
- `version = "Two"` is the old, unstable spelling of `style_edition`.

Read `references/rustfmt-and-style.md` for the 28 stable options with their defaults, the unstable ones, the 2024 sorting rules, and the Style Guide rules rustfmt does not apply.

## Style Guide rules rustfmt leaves to you

Measured, rustfmt 1.9.0 left each of these unchanged: comments are not wrapped (the guide wants comment lines ≤80 columns, and `wrap_comments` is nightly); a doc comment between two `#[derive]`s blocks their merge (put doc comments before attributes); `struct Foo {}` stays (the guide prefers `struct Foo;`); `if (x)` keeps its parentheses (rustc's `unused_parens` warns); `0xAbCd` keeps mixed case (Clippy's `mixed_case_hex_literals` warns); imports are sorted only within a blank-line-separated group and never merged or split; `P { a: a }` keeps the field name (`use_field_init_shorthand` is off by default; Clippy's `redundant_field_names` warns). Name a keyword-named binding with a trailing underscore: `r#crate` is an error ("`crate` cannot be a raw identifier"), though the guide suggests it.

## Where to look

Read only the file the question needs.

- `references/choosing-lints.md`: when choosing lints beyond the starting block, reviewing a `[lints]` table, or when a lint from the docs is unknown or sits in a different group on the installed toolchain.
- `references/clippy-toml.md`: when writing or debugging a `clippy.toml`, or tuning a threshold.
- `references/rustfmt-and-style.md`: when writing a `rustfmt.toml`, switching style edition, or applying the Style Guide beyond what rustfmt does, including `Cargo.toml` layout.

## Hand-offs

- What a lint means, why it fires, how to fix or silence one site, lint-level precedence: `fixing-rust-compile-errors`.
- `[lints]` syntax, `priority`, `[workspace.lints]` inheritance, `rust-version`, feature-combination testing: `using-cargo`.
- Whether an API's names, conversions, and error types are right (the guidelines several lints enforce): `designing-rust-apis`.
- Rustdoc lints and `missing_docs` wording: `documenting-rust`.
