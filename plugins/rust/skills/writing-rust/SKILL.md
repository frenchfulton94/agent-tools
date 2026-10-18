---
name: writing-rust
description: Writes and reviews Rust against the current language and standard library — edition 2024 rules, ownership, borrowing, lifetimes and drop order, traits and generics, patterns, error-handling design, smart pointers, concurrency and async, unsafe code and undefined behaviour, macros, modules, and which std API to reach for, including APIs stabilised since 1.80. Use when the user is writing, refactoring, or reviewing Rust code, migrating a crate to edition 2024, choosing between Rust idioms or std types, or asks whether a Rust feature or std method exists or is stable yet. Also use for symptoms of stale Rust knowledge or edition semantics — code that built on edition 2021 but fails on 2024, an `extern` block or `#[no_mangle]` suddenly rejected, a `static mut` reference denied, a lock or `RefCell` borrow released earlier or later than expected, an `impl Trait` return that now keeps its argument borrowed, `lazy_static!` or `cfg_if!` in new code, or a pattern with `ref` or `mut` that stopped compiling.
license: MIT
---

# Writing Rust

You already write good Rust. This skill corrects what training data gets wrong: edition 2024 rules, APIs and syntax stabilised after most training cut-offs, renamed terms, and precise rules that are easy to misremember.

**Version basis.** Sourced from the Rust 1.99 stable documentation (Book, Reference, std; fetched 2026-10-17). Every edition and compile claim here was measured on rustc 1.97.1. Items marked **1.98+** could not be measured: check `rustc --version` before relying on them.

## Establish the edition and toolchain first

The edition changes what compiles and when values drop, so read it before writing or judging code:

```bash
grep -nE '^(edition|rust-version)' Cargo.toml; rustc --version
```

- No `edition` key means **2015**. Bare `rustc` also defaults to 2015; pass `--edition 2024` when testing a snippet. `cargo new` writes `edition = "2024"`.
- The edition is per crate, and crates of any edition link together. A `macro_rules!` macro uses the edition of the crate that **defines** it.
- A `rust-version` older than an API's version below means you cannot use that API in the crate.

## Edition 2024: what changed

All measured on 1.97.1 with `--edition 2024` against `--edition 2021`. Full before/after examples, the lint behind each change, and migration caveats are in `references/edition-2024.md`.

| Change | Write this | On 2024 the old form gives |
|---|---|---|
| `extern` blocks must be `unsafe` | `unsafe extern "C" { pub safe fn abs(x: i32) -> i32; fn strlen(p: *const c_char) -> usize; }` — items are unsafe to call unless marked `safe` | error: extern blocks must be unsafe |
| `no_mangle`, `export_name`, `link_section` are unsafe attributes | `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "f")]` (the wrapped form also works on 2021) | error: unsafe attribute used without unsafe |
| The body of an `unsafe fn` is not an unsafe context | wrap each unsafe operation in `unsafe { }` with a `// SAFETY:` comment | warning[E0133] (`unsafe_op_in_unsafe_fn`) |
| References to a `static mut` are denied | `&raw const X` / `&raw mut X`, or an atomic, `Mutex`, `OnceLock`, `LazyLock`. `println!("{}", X)` takes a hidden reference; `X += 1` does not | error (`static_mut_refs`; a warning on 2021) |
| `std::env::set_var` and `remove_var` are unsafe | `unsafe { env::set_var(..) }`, sound only while no other thread reads the environment | error[E0133] |
| `if let` scrutinee temporaries drop before `else` | nothing; but a lock guard or `RefCell` borrow in the scrutinee is now released in the `else` branch | old code that relied on it being held still compiles |
| Tail-expression temporaries drop before the block's locals | `let c = RefCell::new(s); c.borrow().len()` now compiles (E0597 on 2021) | drop order of `Drop` types in tail position flips |
| Return-position `impl Trait` captures every in-scope lifetime | opt out with `-> impl Sized + use<>` or list `use<'a, T>` | a caller that mutates the argument while holding the result gets E0502 |
| Match ergonomics: no `mut`, `ref`, or `&` under an implicit borrow | `if let &Some(mut x) = opt` instead of `if let Some(mut x) = opt` (with `opt: &Option<_>`) | error: cannot mutably bind by value / explicitly dereference / explicitly borrow within an implicitly-borrowing pattern |
| Never-type fallback is `!`, not `()` | annotate: `let x: () = match n { 4 => Default::default(), _ => return };` | error[E0277]: the trait bound `!: Default` is not satisfied |
| `gen` is a reserved keyword | `r#gen` | error: expected identifier, found reserved keyword `gen` |
| `#"…"#` and `##` are reserved tokens | add a space in macro input: `# "x"#` | error: invalid string literal / reserved multi-hash token |
| `$e:expr` also matches `_` and `const { .. }` | use `$e:expr_2021` only where the old grammar is wanted | macro arms after an `expr` arm stop being reached |
| Prelude adds `Future` and `IntoFuture` | no import needed | user traits with `poll`/`into_future` methods become ambiguous |
| `boxed_slice.into_iter()` yields `T` by value | nothing | (on 2021 it yields `&T`) |
| Let chains | `if let Some(a) = x && a > 3 && let Ok(b) = f(a) { .. }`, also in `while` | error: let chains are only allowed in Rust 2024 or later |

Let chains reject an unparenthesised `||` anywhere in the chain; write `&& (a || b)`.

## Corrections to stale defaults

Versions are the release that stabilised the item. Each was compiled on 1.97.1 unless marked 1.98+.

**Language**

- **`if let` guards in `match` arms** are stable since 1.95 on **every** edition, including chains: `Some(n) if let Some(m) = f(n) && m > 4 => ..`. The Book's claims that guards exist only as boolean `match` guards, and that `if let Ok(age) = age && age > 30` cannot be written, are both stale.
- **`cfg_select!`** (1.95) replaces the `cfg-if` crate, in item and expression position: `let os = cfg_select! { unix => "unix", _ => "other" };`. `#[cfg(true)]` and `#[cfg(false)]` work since 1.88. cfg'd-out code must still parse.
- **Raw borrows** `&raw const place` / `&raw mut place` (1.82) replace `addr_of!` and `&x as *const _`. They are required for `#[repr(packed)]` fields (`&p.field` is error E0793) and for fields of uninitialised memory.
- **Precise capturing** `impl Trait + use<'a, T>` (1.82; in traits since 1.87). The list must name every in-scope type and const parameter.
- **Async closures** `async |x| { .. }` and the bounds `AsyncFn`, `AsyncFnMut`, `AsyncFnOnce` (1.85, in the prelude on every edition). Prefer `f: impl AsyncFn(u8) -> u8` to `F: Fn(u8) -> Fut, Fut: Future`; async closures can lend their captures to the returned future.
- **Trait upcasting** `&dyn Sub` → `&dyn Super` (1.86). The current term is **dyn compatible** (formerly "object safe"); E0038 says "the trait `X` is not dyn compatible". A trait with an `async fn` or `-> impl Trait` method is not dyn compatible unless that method has `where Self: Sized`.
- **Safe `#[target_feature]` functions** (1.86). A caller that enables the same features calls them safely; any other caller needs `unsafe` (error[E0133] "call to function `f` with `#[target_feature]` is unsafe"), even when the feature is enabled crate-wide.
- **Naked functions** are `#[unsafe(naked)]` with a single `naked_asm!` body (1.88). Bare `#[naked]` is an error on every edition.
- **Patterns:** exclusive ranges `0..5` and half-open `5..` (1.80). **Inferred const arguments** `let a: [u8; _] = [0; 3];` (1.89), not allowed in item signatures.
- **`#[expect(lint, reason = "…")]`** (1.81) instead of `#[allow]` for a deliberate suppression; it warns once the lint stops firing.
- **Temporary lifetime extension** now reaches tuple-struct and tuple-variant constructor arguments (`let x = Some(&temp());`, 1.89) and `let a = format_args!(..)` (1.89). Plain function arguments still do not: `let a = id(&temp());` is E0716.
- **`move` closures capture field paths**, not whole variables (2021+): after `thread::spawn(move || s.a.len())`, `s.b` is still usable.
- **Defining C-variadic functions** (`unsafe extern "C" fn f(n: i32, mut args: ...)`) is documented in the 1.99 Reference but is E0658 on 1.97 (where `VaList` has `arg`, not the documented `next_arg`). Declaring variadic foreign functions is stable.

**Standard library**

- **`LazyLock` / `LazyCell`** (1.80) and **`OnceLock`** replace `lazy_static!` and `once_cell` in new code: `static RE: LazyLock<Regex> = LazyLock::new(|| ..);`.
- **`assert_matches!` / `debug_assert_matches!`** (1.96) are not in the prelude: write `use std::assert_matches;` or get "cannot find macro".
- **Prelude additions:** `size_of`, `size_of_val`, `align_of`, `align_of_val` (1.80, every edition); `AsyncFn*` (1.85, every edition); `Future`, `IntoFuture` (edition 2024 only).
- **Associated constants, not module constants or methods:** `i32::MAX`, `f64::EPSILON`, `char::from_u32`, never `std::i32::MAX`, `i32::max_value()`, `std::f64::EPSILON`, `std::char::from_u32`. The 1.99 docs mark the old forms deprecated (**1.99+**, a `deprecated` warning); on 1.97 rustc reports them only through the allow-by-default `deprecated_in_future` lint, but `cargo clippy` flags them through `clippy::legacy_numeric_constants` (style, warn).
- **Integer methods:** `strict_add` and the `strict_*` family (1.91) panic on overflow in release too; `unbounded_shl`/`unbounded_shr` (1.87) shift everything out, while `wrapping_shl` masks the amount (`42i32.wrapping_shl(32) == 42`); `is_multiple_of` (1.87) never panics on 0; signed `div_ceil`/`div_floor`/`next_multiple_of` are still unstable (`int_roundings`). Full table in `references/std-recent-apis.md`.
- **`Vec::extract_if(range, pred)`** (1.87) takes a range first: `v.extract_if(.., |x| *x > 1)`. `HashMap::extract_if(pred)` (1.88) takes only the predicate.
- **`std::range::{Range, RangeInclusive, …}`** (1.95–1.96) are new `Copy` range types that implement `IntoIterator`, not `Iterator`. Range syntax `a..b` still produces `std::ops::Range`; convert with `.into()`.
- **Panic output** includes the thread id since 1.91: `thread 'main' (81234) panicked at src/main.rs:4:5:`. A `RefCell` double borrow panics with `RefCell already borrowed`. Do not match the old format in tests or tools.
- `str::from_utf8` is an inherent function (1.87); no `use std::str` needed.
- The Book uses rand 0.10: `use rand::prelude::*; rand::rng().random_range(1..=100)`, not `thread_rng().gen_range` (from the Book; not compiled here).
- **1.98+, docs only** (E0658 on 1.97): `bool::ok_or`/`ok_or_else`, `str::strip_circumfix` and the slice form, `str::substr_range` and `slice::subslice_range` (they return the new `core::range::Range`), `{integer}::format_into(&mut fmt::NumBuffer)`, `f32`/`f64::algebraic_*`.

## Error-handling design

- Return `Result` for failure a caller can anticipate; panic only for a broken invariant, and document it under `# Panics`. Write `expect` messages as the precondition: `.expect("config path should be set by main")`.
- `?` converts the error with `From::from`, so `impl From<io::Error> for MyError` is what makes `?` work across error types. `?` never converts between `Option` and `Result`; use `.ok_or(e)?` or `.ok()?`.
- A library exposes an error enum implementing `std::error::Error` (`core::error::Error` in `no_std`, 1.81). A binary may use `fn main() -> Result<(), Box<dyn Error>>`; an `Err` exits non-zero.
- Implement `From` / `TryFrom`, never `Into` / `TryInto`; the blanket impls supply those.
- A constructor that can fail is named `build` or `try_new`, not `new`.
- For a library's public error type (what it implements, `Send + Sync + 'static`, opaque versus enum), see `designing-rust-apis`.
- A `Display` or `Debug` impl returns `Err` only when the `Formatter` did; formatting is otherwise infallible.

## Where to look

Read at most the file the question touches.

- `references/edition-2024.md` — when migrating a crate, or when code behaves differently between editions. Every 2024 change with before/after code, its lint and default level, what `cargo fix --edition` does and does not fix, and the 2018/2021 changes still seen in old code.
- `references/ownership-lifetimes-and-drops.md` — when a borrow error looks like a design problem, or when drop timing matters (locks, `RefCell`, guards). Temporary scopes and lifetime extension, drop order, two-phase borrows, moving out of `&mut`, closure capture rules, elision and default object lifetimes, variance, implied bounds, `impl Trait` capture, smart-pointer choice.
- `references/traits-generics-and-patterns.md` — when designing trait or generic APIs or writing non-trivial patterns. Dyn compatibility, upcasting, method resolution traps, coherence and the orphan rule, `impl Trait` rules, const generics, derive bounds, and pattern semantics (binding modes, path-pattern capture, or-pattern precedence, guards, ranges, constants).
- `references/macros-modules-and-attributes.md` — when writing `macro_rules!` or proc macros, organising modules and imports, or using `cfg`, lint, `must_use`, `non_exhaustive`, or `diagnostic` attributes.
- `references/concurrency-and-async.md` — threads, scoped threads, channels, locks and guard lifetimes, atomics, `Send`/`Sync`, lazy statics, and async: laziness, `join` versus sequential `.await`, `select` fairness, blocking, `Pin`, async closures and async fns in traits, streams.
- `references/unsafe-and-ub.md` — when writing or reviewing `unsafe`, FFI, raw pointers, `MaybeUninit`, `transmute`, unions, inline or naked assembly, or `const` evaluation. The full UB list, validity invariants, aliasing, provenance APIs, FFI ABIs and unwinding, deny-by-default UB lints, Miri.
- `references/std-recent-apis.md` — before calling a std method you are unsure exists, or when choosing between std APIs. APIs stabilised 1.80–1.97 by version, 1.98+ items, deprecations, still-unstable traps, the integer overflow families, float semantics, `str` and slice edge cases, collection choice.
- `references/expressions-and-casts.md` — operator precedence (where it differs from C), evaluation order, `as` cast semantics, literal and array-repeat edge cases, and what `?` works on.

## Neighbouring skills

- What a compiler error or lint means, error codes, `cargo fix` → `fixing-rust-compile-errors`; for more than a handful of diagnostics, hand the build to the `rust-build-triage` agent.
- `Cargo.toml`, features, the `edition` and `rust-version` keys, resolver 3, profiles → `using-cargo`.
- Designing a library's public surface (naming, conversions, which traits to implement, error types, sealed traits, `#[non_exhaustive]`) → `designing-rust-apis`. Which Clippy lints to enable, `clippy.toml`, rustfmt → `linting-and-formatting-rust`.
- Memory orderings, fences, and building or reviewing spin locks, channels, `Arc`, mutexes and other primitives on atomics → `using-atomics-and-locks`.
- Writing and running tests → `testing-rust`. Doc comments and doctests (including edition 2024 merged doctests) → `documenting-rust`. Argument parsing, exit codes, stdout and `BrokenPipe` → `building-rust-clis`.
