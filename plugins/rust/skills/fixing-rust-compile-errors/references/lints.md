# Lints: levels, groups, configuration, and the common ones

Levels and precedence rules come from the rustc book (1.99). Each behaviour marked "measured" was checked on rustc/cargo/clippy 1.97.1.

## Contents

- [Levels](#levels)
- [Which level wins](#which-level-wins)
- [Reading where a level came from](#reading-where-a-level-came-from)
- [Cargo: `[lints]`, dependencies, `build.warnings`](#cargo-lints-dependencies-buildwarnings)
- [Edition-dependent defaults](#edition-dependent-defaults)
- [Groups](#groups)
- [Clippy](#clippy)
- [The lints most often hit](#the-lints-most-often-hit)
- [Renamed lints](#renamed-lints)
- [Future-incompatibility warnings](#future-incompatibility-warnings)
- [Lints newer than 1.97](#lints-newer-than-197)

## Levels

Six levels: `allow`, `expect`, `warn`, `force-warn`, `deny`, `forbid`.

- `#[expect(lint)]` (stable since 1.81) silences the lint, and warns `unfulfilled_lint_expectations` ("this lint expectation is unfulfilled") when the lint no longer fires (measured). Prefer it to `allow` for temporary suppressions, so stale ones surface. It exists only as an attribute.
- `--force-warn LINT` exists only on the command line. It always warns, overriding `#![allow]` and even `--cap-lints allow` (measured).
- Every lint attribute takes `reason = "…"`, printed as a note on the diagnostic (measured): `#[allow(unused_mut, reason = "only modified on some platforms")]`.
- `rustc -W help` lists every lint, its default level, and every group for the installed compiler. It shows the edition-independent default: on 1.97.1 it lists `static-mut-refs` as warn and `unsafe-op-in-unsafe-fn` as allow, though both are stricter in edition 2024 (measured).
- `rustc --explain` takes error codes only. `rustc --explain unused_variables` fails with "is not a valid error code" (measured). For a Clippy lint, `cargo clippy --explain needless_return` works.

## Which level wins

Highest first:

1. `--force-warn`.
2. `--cap-lints LEVEL`, which caps everything below it: `--cap-lints warn` turns a `#![deny(unused)]` error into a warning (measured).
3. Command-line `-A/-W/-D/-F`. They act like crate-level attributes, so **an attribute in the source overrides them**: `#[allow(unused_variables)]` on a fn beats `-D unused-variables` (measured). `-F` is the exception, and an inner `allow` under `-F` is error E0453 (measured). Among flags, the rightmost wins: `-D unused -A unused-variables` denies the group except that lint; reversed, the lint is denied too (measured).
4. In source, the innermost attribute wins.

Special cases, all measured:

- `forbid` on one lint plus an inner `allow` of it is error E0453 "allow(unused_variables) incompatible with previous forbid".
- `forbid` on a **group** plus an inner `allow` is only a warning (`forbidden_lint_groups`, a future-incompatibility lint), and the `allow` takes effect. A forbidden group does not forbid. Use `#![deny(warnings)]`, not `#![forbid(warnings)]`.
- The `warnings` group ignores attribute order: under `#![deny(warnings)]`, an inner `#[warn(unused_variables)]` still produces an error, with the note "`#[deny(unused_variables)]` implied by `#[deny(warnings)]`".
- Other groups behave as if expanded into their lints, so a later, more specific attribute overrides them: `#[allow(unused)] #[deny(unused_must_use)]`.

## Reading where a level came from

The notes under a lint diagnostic say who set its level:

- "`#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default": the default, and the group it belongs to.
- "requested on the command line with `-D unused-variables`": a flag, from `RUSTFLAGS`, `[lints]`, or a build tool.
- "`#[deny(unused_variables)]` implied by `#[deny(warnings)]`": the `warnings` group.
- "the lint level is defined here", pointing at an attribute.

To silence a lint at the narrowest scope, put `#[expect]`/`#[allow]` on the item the span points into, not on the crate.

## Cargo: `[lints]`, dependencies, `build.warnings`

The `[lints]` table syntax belongs to the `using-cargo` skill. What matters when a diagnostic surprises you:

- Cargo turns `[lints]` into command-line flags (`--allow=unused_variables --deny=unused`, measured with `cargo check -v`). So any `#[allow]` in the source overrides it.
- With equal `priority`, the table's order is ignored. `unused = "deny"` with `unused_variables = "allow"` denied `unused_variables` anyway (measured). Give the group `{ level = "deny", priority = -1 }`. Clippy's deny-by-default `clippy::lint_groups_priority` reports this mistake.
- Cargo passes `--cap-lints allow` to non-path dependencies, so their warnings never appear. A warning always belongs to a workspace package.
- `build.warnings = "deny"` in `.cargo/config.toml`, or `CARGO_BUILD_WARNINGS=deny` (stable in Cargo 1.97), fails the build on warnings from local packages, with "error: warnings are denied by `build.warnings` configuration" (measured). It replaces `RUSTFLAGS=-Dwarnings` for CI and does not touch dependencies.
- `unexpected_cfgs` fires under Cargo because Cargo always passes `--check-cfg` (bare `rustc` does not; measured). For a custom cfg such as `tokio_unstable`, declare it: `[lints.rust] unexpected_cfgs = { level = "warn", check-cfg = ['cfg(tokio_unstable)'] }`, or `println!("cargo::rustc-check-cfg=cfg(tokio_unstable)")` in `build.rs`. For `cfg(feature = "x")`, add `x` to `[features]`. The compiler's help lists all three (measured).

## Edition-dependent defaults

| Lint or rule | Edition ≤2021 | Edition 2024 |
|---|---|---|
| `static_mut_refs` (`&X` / `&mut X` on a `static mut`) | warn | deny. It is a lint: `#[allow(static_mut_refs)]` silences it (measured). Fix with `&raw const X`, atomics, or `Mutex` |
| `unsafe_op_in_unsafe_fn` | allow | warn, reported as `warning[E0133]` (measured) |
| `extern "C" { … }` without `unsafe` | accepted | hard error "extern blocks must be unsafe", no code (measured) |
| `#[no_mangle]`, `#[export_name]`, `#[link_section]` without `unsafe(…)` | accepted | hard error "unsafe attribute used without unsafe" (measured) |
| `gen` as an identifier | accepted | reserved; use `r#gen` (`cargo fix --edition` rewrites it; measured) |

The `rust-2024-compatibility` group holds the migration lints (`if_let_rescope`, `tail_expr_drop_order`, `impl_trait_overcaptures`, `edition_2024_expr_fragment_specifier`, and others). Most are allow by default. `cargo fix --edition` enables them and applies their fixes. It does **not** change `edition` in `Cargo.toml`; edit that yourself afterwards (measured: the key still read `2021`).

Bare `rustc file.rs` uses edition 2015 (measured). Pass `--edition 2024` when reproducing a diagnostic outside Cargo.

## Groups

On 1.97.1 (`rustc -W help`):

- `warnings`: every lint currently at warn.
- `unused`: `unused_imports`, `unused_variables`, `unused_assignments`, `dead_code`, `unused_mut`, `unreachable_code`, `unreachable_patterns`, `unused_must_use`, `unused_unsafe`, `path_statements`, `unused_attributes`, `unused_macros`, `unused_macro_rules`, `unused_allocation`, `unused_doc_comments`, `unused_extern_crates`, `unused_features`, `unused_labels`, `unused_parens`, `unused_braces`, `redundant_semicolons`, `map_unit_fn`, `unused_visibilities` (the complete 1.97.1 list; the 1.99 docs add `unreachable_cfg_select_predicates`). `unused_comparisons` is **not** in it.
- `nonstandard_style`: `non_camel_case_types`, `non_snake_case`, `non_upper_case_globals`.
- `future_incompatible`: lints for code that will become an error.
- `rust_2018_compatibility`, `rust_2021_compatibility`, `rust_2024_compatibility`: edition migration. `rust_2018_idioms`: `bare_trait_objects`, `elided_lifetimes_in_paths`, `unused_extern_crates`, `explicit_outlives_requirements`, `ellipsis_inclusive_range_patterns`.
- `let_underscore` (`let_underscore_drop` allow, `let_underscore_lock` deny), `keyword_idents`, `refining_impl_trait`, `deprecated_safe`, `unknown_or_malformed_diagnostic_attributes`.

## Clippy

- Default levels (measured): `clippy::correctness` is deny (`eq_op` on `x == x` failed the build); `style`, `complexity`, `perf`, `suspicious` warn (`needless_return`, `ptr_arg`); `pedantic`, `nursery`, `cargo`, `restriction` are allow.
- A misspelled tool name in a lint attribute (`#[allow(clipy::all)]`) is error E0710. A misspelled lint name is only the `unknown_lints` warning (measured).
- `cargo clippy --fix` applies Clippy's machine-applicable suggestions plus rustc's. Its `--help` says `--fix` implies `--all-targets`. On 1.97.1 it did not: it fixed only the library, and tests needed `--all-targets` (measured).

## The lints most often hit

| Lint (default) | What it means | Fix |
|---|---|---|
| `unused_variables` (warn) | Binding never read | Prefix `_`; or it reveals a bug |
| `unused_imports` (warn) | `use` never used | Remove; under `cfg`, gate the `use` the same way |
| `unused_mut` (warn) | `mut` not needed | Remove |
| `dead_code` (warn) | Item never used. Not reported at all while any error exists in the crate (measured) | Use it, remove it, `pub` it, or `#[expect(dead_code)]` |
| `unused_must_use` (warn) | Ignored `Result` ("this `Result` may be an `Err` variant, which should be handled") or a lazy iterator ("iterators are lazy and do nothing unless consumed") | Handle with `?`; `let _ = …` to discard deliberately; consume iterators with `for`/`for_each` |
| `unreachable_patterns` (warn) | Arm after a catch-all, or already covered | Reorder or delete |
| `irrefutable_let_patterns` (warn) | `if let x = 5` / `let x = 5 else {}` always matches | Plain `let` |
| `non_snake_case`, `non_camel_case_types`, `non_upper_case_globals` (warn) | Naming style | Rename |
| `mismatched_lifetime_syntaxes` (warn) | One lifetime written two ways: "hiding a lifetime that's elided elsewhere is confusing" (`fn f(v: &str) -> P` should be `P<'_>`), "eliding a lifetime that's named elsewhere is confusing" | Spell it the same in input and output. Replaced `elided_named_lifetimes` |
| `unexpected_cfgs` (warn) | Unknown cfg name or value | See [Cargo](#cargo-lints-dependencies-buildwarnings) |
| `deprecated` (warn) | Use of a `#[deprecated]` item | The note names the replacement |
| `private_bounds`, `private_interfaces` (warn) | Private type in a public signature or bound (used to be error E0445) | Make it `pub`, or narrow the item's visibility |
| `async_fn_in_trait` (warn) | `async fn` in a public trait: callers cannot require `Send` | `fn m(&self) -> impl Future<Output = T> + Send`, or allow it for local traits |
| `non_local_definitions` (warn) | `impl` or `#[macro_export]` inside a fn body for non-local types | Move it to module level |
| `dropping_references` (warn) | `drop(&guard)` does nothing; the lock stays held | `drop(guard)` |
| `let_underscore_lock` (deny) | `let _ = m.lock()` unlocks at once | `let _guard = …` |
| `bindings_with_variant_name` (deny, code E0170) | `GET =>` binds a variable instead of matching the variant | `Method::GET` |
| `unconditional_panic`, `arithmetic_overflow`, `overflowing_literals` (deny) | Constant out-of-bounds index, `1_i32 << 32`, `let x: u8 = 1000` | Fix the constant |
| `invalid_reference_casting`, `dangerous_implicit_autorefs` (deny) | `&T` cast to `*mut T` and written; a raw-pointer expression that silently creates a reference | `UnsafeCell`; make the reference explicit |
| `dependency_on_unit_never_type_fallback` (deny) | Inference relies on `()` fallback that becomes `!` in 2024 | Annotate the type |
| `unnameable_test_items` (warn) | `#[test]` inside a fn body never runs | Move it to module level |
| `map_unit_fn`, `for_loops_over_fallibles`, `noop_method_call`, `invalid_nan_comparisons`, `unused_comparisons` (warn) | `.map(f)` with a unit fn; `for x in option`; `.clone()` on `&T` that only copies the reference; `x == f32::NAN`; `u8 >= 0` | `for_each`; `if let`; fix the receiver; `is_nan()`; delete |
| `unused_results`, `missing_docs`, `unsafe_code`, `unreachable_pub`, `elided_lifetimes_in_paths` (allow) | Opt-in; only fire when a project enables them | — |

## Renamed lints

This section covers rustc lints. Clippy's renamed and deprecated lints, and the Clippy lints newer than 1.97, are in the `linting-and-formatting-rust` skill (`references/choosing-lints.md`).

An attribute using an old name warns `renamed_and_removed_lints` and still works. Measured on 1.97.1: `elided_named_lifetimes` → `mismatched_lifetime_syntaxes`, `unused_tuple_struct_fields` → `dead_code`. From the 1.99 docs: `static_mut_ref` → `static_mut_refs`, `bare_trait_object` → `bare_trait_objects`, `non_fmt_panic` → `non_fmt_panics`, `overlapping_patterns` → `overlapping_range_endpoints`, `exceeding_bitshifts` → `arithmetic_overflow`, `single_use_lifetime` → `single_use_lifetimes`, `disjoint_capture_migration` → `rust_2021_incompatible_closure_captures`.

## Future-incompatibility warnings

They read "this was previously accepted by the compiler but is being phased out; it will become a hard error in a future release!" with a tracking-issue link. Edition lints read "this is accepted in the current edition (Rust 20XX) but is a hard error in Rust 20YY!". `cargo report future-incompatibilities` shows the ones in dependencies, whose ordinary warnings are capped away.

## Lints newer than 1.97

These are in the 1.99 documentation and absent from `rustc -W help` on 1.97.1. Check `rustc --version` before relying on them; on 1.97 an `#[allow]` of one only produces `unknown_lints` (measured).

- 1.98+: `c_void_returns` (an extern fn returning `c_void`; omit the return type), `raw_borrows_via_references` (allow; `&(*x).0 as *const _` → `&raw const (*x).0`), `invalid_runtime_symbol_definitions` (deny) and `suspicious_runtime_symbol_definitions` (warn) for `#[unsafe(no_mangle)]` definitions of `memcpy`, `malloc`, `exit` and similar, `method_call_on_diverging_infer_var` (future-incompatible; `let x = panic!(); x.clone();`), `recursion_depth_exceeding_limit` (future-incompatible).
- 1.99: `deprecated` fires on the legacy module constants (`std::i32::MAX`) and on `i32::max_value()`/`min_value()`; use `i32::MAX`/`i32::MIN`. Silent on 1.97.1 even under `#![deny(deprecated)]` (measured).
