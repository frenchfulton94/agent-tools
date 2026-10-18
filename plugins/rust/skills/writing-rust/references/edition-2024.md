# Edition 2024 in detail

Every compile result below was measured on rustc 1.97.1 by building the same file with `--edition 2021` and `--edition 2024`. Lint levels are the 1.97 defaults.

## Contents

- [How editions work](#how-editions-work)
- [Migrating a crate](#migrating-a-crate)
- [Unsafe and FFI changes](#unsafe-and-ffi-changes)
- [Temporary scopes: `if let` and tail expressions](#temporary-scopes-if-let-and-tail-expressions)
- [`impl Trait` lifetime capture](#impl-trait-lifetime-capture)
- [Match ergonomics restrictions](#match-ergonomics-restrictions)
- [Never-type fallback](#never-type-fallback)
- [Syntax, prelude and macro changes](#syntax-prelude-and-macro-changes)
- [Let chains](#let-chains)
- [Changes owned by other skills](#changes-owned-by-other-skills)
- [Earlier editions, still seen in old code](#earlier-editions-still-seen-in-old-code)

## How editions work

- Editions are 2015, 2018, 2021 and 2024. Edition 2024 is stable since 1.85.
- An edition affects only the front end, so crates of different editions link together freely.
- No `edition` key in `Cargo.toml` means 2015. A bare `rustc` call also defaults to 2015.
- The edition that applies to a macro is the edition of the crate that defines it. For method lookup on arrays and boxed slices, it is the edition of the method-name token, which matters inside macros.

## Migrating a crate

The edition lints are the `rust_2024_compatibility` group. `cargo fix --edition` raises them to warnings and applies their machine-applicable fixes; then set `edition = "2024"`. Review these, because the automatic fix preserves the **old** behaviour, which is often not what you want:

- `$x:expr` fragments are rewritten to `$x:expr_2021`. Most macros want the new grammar; revert where `_` or `const { }` should match.
- `if let` statements whose scrutinee has a significant drop are rewritten into single-arm `match` expressions to keep the old drop timing. Keep the `if let` where the new timing is fine or better.
- `env::set_var` calls are wrapped in `unsafe { }` with a `// FIXME: Audit that the environment access only happens in single-threaded code.` comment. Do the audit.
- `tail_expr_drop_order` has no automatic fix. Inspect each `Drop` impl it names for side effects such as releasing a lock or sending a message.

Default levels on 1.97, before migration: `static_mut_refs` and `boxed_slice_into_iter` warn; `dependency_on_unit_never_type_fallback` and `never_type_fallback_flowing_into_unsafe` deny (since 1.92); the rest of the group is allow.

## Unsafe and FFI changes

**`unsafe extern` blocks** (lint `missing_unsafe_on_extern`). Declaring foreign items can itself cause UB, so the block must be `unsafe`. Inside it, each item is unsafe to use unless marked `safe`, which is a promise you make:

```rust
unsafe extern "C" {
    pub safe fn abs(x: i32) -> i32;        // callable without `unsafe`
    pub fn strlen(s: *const c_char) -> usize;
    pub safe static ERRNO_BASE: i32;
}
```

Plain `extern "C" { }` on 2024: `error: extern blocks must be unsafe`. `unsafe extern` and the `safe`/`unsafe` item qualifiers are accepted on 2021 too (stable since 1.82).

**Unsafe attributes** (lint `unsafe_attr_outside_unsafe`). `no_mangle`, `export_name` and `link_section` can cause symbol collisions, so they are written `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "name")]`, `#[unsafe(link_section = ".x")]`. The bare form on 2024: `error: unsafe attribute used without unsafe`. `#[unsafe(naked)]` is unsafe on every edition.

**`unsafe_op_in_unsafe_fn` warns.** An `unsafe fn` declares an obligation for its callers; its body is a safe context. Each unsafe operation needs its own block:

```rust
/// # Safety
/// `p` must be non-null, aligned and point to an initialised `u8`.
unsafe fn read(p: *const u8) -> u8 {
    // SAFETY: the caller upholds this function's contract.
    unsafe { *p }
}
```

Without the inner block: `warning[E0133]: dereference of raw pointer is unsafe and requires unsafe block`, with `#[warn(unsafe_op_in_unsafe_fn)] (part of #[warn(rust_2024_compatibility)])`.

**`static mut` references are denied** (lint `static_mut_refs`, deny on 2024, warn on 2021). Any `&X`, `&mut X`, `ref` binding, or method call that autorefs a `static mut` is rejected, and so is `println!("{}", X)`, because formatting takes a reference. Assigning or compound-assigning (`X += 1`) inside `unsafe` is not a reference and is still allowed. Replacements, best first:

1. An atomic (`static COUNT: AtomicU32`), `Mutex`, `RwLock`, `OnceLock` or `LazyLock` in a plain `static`.
2. Raw pointers: `let p = &raw mut X; unsafe { *p += 1 }`, or `unsafe { *(&raw const X) }` to read.

**Newly unsafe functions** (lint `deprecated_safe_2024`): `std::env::set_var` and `std::env::remove_var` give `error[E0133]: call to unsafe function `set_var` is unsafe and requires unsafe block`. They are sound only when no other thread can read or write the environment at the same time, including through C code such as `getenv`.

## Temporary scopes: `if let` and tail expressions

**`if let` scrutinee temporaries drop before the `else` block** (lint `if_let_rescope`). On 2021 they lived to the end of the whole `if let … else …` statement.

```rust
let c = RefCell::new(None::<u8>);
if let Some(_) = *c.borrow() { } else { *c.borrow_mut() = Some(2); }
// 2021: panics "RefCell already borrowed"; 2024: works
```

They are still alive throughout the `then` branch. Measured with a `Mutex`: the guard from `if let Some(_) = m.lock().unwrap().first()` is held in the `then` branch on both editions and released in the `else` branch only on 2024. A `match` scrutinee is unaffected: its temporaries live to the end of the `match` on every edition. To keep the old timing, rewrite as `match x { Some(v) => .., _ => .. }`.

**Tail-expression temporaries drop before the block's locals** (lint `tail_expr_drop_order`). On 2021 they outlived the locals, which made this common function fail:

```rust
fn len() -> usize {
    let c = RefCell::new(String::from("abc"));
    c.borrow().len()   // 2021: E0597 `c` does not live long enough; 2024: compiles
}
```

Drop order also flips. With `let _local = D("local"); D("temp").n()` as a function body, 2021 prints `drop local, drop temp`; 2024 prints `drop temp, drop local`. To pin an order, hoist the temporary into a named `let`.

## `impl Trait` lifetime capture

On 2024, return-position `impl Trait` captures every generic parameter in scope, lifetimes included. On 2021, free and inherent functions captured only the lifetimes named in the bounds. (Trait methods already captured everything.)

This fixes the common under-capture error:

```rust
fn evens(v: &Vec<i32>) -> impl Iterator<Item = i32> {
    v.iter().copied().filter(|x| x % 2 == 0)
}
// 2021: E0700 hidden type captures lifetime that does not appear in bounds
// 2024: compiles
```

and creates over-capture where the returned value does not actually borrow:

```rust
fn key(s: &str) -> impl Sized { s.len() }
let k = key(&s); s.push('c');      // 2024: E0502, `s` still borrowed by `k`
fn key(s: &str) -> impl Sized + use<> { s.len() }   // fix: capture nothing
```

`use<..>` rules: at most one per bound list; it must list **every** in-scope type and const parameter (only lifetimes can be left out); lifetimes come first; `'_` is allowed where elision is; it cannot be used in a function that also has argument-position `impl Trait`. Lints: `impl_trait_overcaptures` (2024 migration), `impl_trait_redundant_captures` (a `use<..>` equal to the default).

## Match ergonomics restrictions

When a non-reference pattern matches a reference, the default binding mode becomes `ref` or `ref mut`. On 2024, under such a default mode you may not write `mut`, `ref`, `ref mut`, `&` or `&mut` (lint `rust_2024_incompatible_pat`). On 2021, `mut` silently reset the mode to by-value, which surprised people.

```rust
let opt = &Some(5u8);
if let Some(mut x) = opt {}       // error: cannot mutably bind by value within an implicitly-borrowing pattern
if let Some(&y) = &Some(&3u8) {}  // error: cannot explicitly dereference within an implicitly-borrowing pattern
let [ref z] = &[1u8];             // error: cannot explicitly borrow within an implicitly-borrowing pattern
```

Fix by making the outer reference explicit, which returns the default mode to "move", or by dropping the modifier:

```rust
if let &Some(mut x) = opt {}        // x: u8, a mutable copy
if let &Some(&y) = &Some(&3u8) {}   // y: u8
let [z] = &[1u8];                   // z: &u8
```

## Never-type fallback

When an inference variable meets only diverging expressions (`return`, `panic!`, `loop {}`), its type falls back to `!` on 2024, and to `()` before. Code that relied on `()` now fails:

```rust
let x = match foo() { 4 => Default::default(), _ => return };
// 2024: error[E0277]: the trait bound `!: Default` is not satisfied
// 2021: error: this function depends on never type fallback being `()`
//       (`dependency_on_unit_never_type_fallback`, deny since 1.92)
```

Annotate the intended type: `let x: () = …` or `<() as Default>::default()`. `never_type_fallback_flowing_into_unsafe` (deny) catches the dangerous case where the fallback reaches `mem::zeroed()` or a similar unsafe generic; write `mem::zeroed::<()>()`. The docs say the `!` fallback will later apply to all editions.

## Syntax, prelude and macro changes

- **`gen` is reserved** (lint `keyword_idents_2024`): `fn gen()` gives `error: expected identifier, found reserved keyword `gen``. Use `r#gen`. This hit rand's old `Rng::gen`; rand 0.9+ renamed it `random`.
- **Guarded strings and `##` are reserved** (lint `rust_2024_guarded_string_incompatible_syntax`). In macro input, `#"hi"#` gives `error: invalid string literal` and `## x` gives `error: reserved multi-hash token is forbidden`. Insert whitespace: `# "hi"#`, `# # x`.
- **`$e:expr` matches `_` and `const { … }`** (lint `edition_2024_expr_fragment_specifier`). Measured: with arms `($e:expr)` then `(const $b:block)`, `m!(const { 1 })` reaches the second arm on 2021 and the first on 2024; `u!(_)` falls to a `tt` arm on 2021 and matches `expr` on 2024. `expr_2021` keeps the old grammar and is accepted on every edition since 1.83.
- **Prelude gains `Future` and `IntoFuture`** (lint `rust_2024_prelude_collisions`). Without them, 2021 code naming `Future` gets E0405. A user trait with a `poll` or `into_future` method can become ambiguous; call it as `MyTrait::poll(&x)`.
- **`Box<[T]>::into_iter()` method call yields `T`** (lint `boxed_slice_into_iter`, warn on 2021). `Box<[T]>: IntoIterator` exists since 1.80 on every edition, but on 2015–2021 the method-call form still resolves to the slice iterator and yields `&T`. On old editions write `.iter()` or `IntoIterator::into_iter(b)`. The array equivalent (`array_into_iter`) changed in 2021.

## Let chains

`if` and `while` conditions may chain `let` bindings and boolean expressions with `&&` (stable 1.88, 2024 only):

```rust
if let Ok(age) = parse(s) && age > 30 && let Some(p) = lookup(age) { .. }
while let Some(x) = stack.pop() && x > 0 { .. }
```

- Bindings are visible in later conditions and in the body. Conditions short-circuit left to right.
- On 2021: `error: let chains are only allowed in Rust 2024 or later`. There, nest the `if let`s.
- If any operand is a `let`, no operand may be an unparenthesised `||`. Struct literals, ranges and assignments are also not allowed unparenthesised.
- A chain is not checked for exhaustiveness; a missing `else` is a silent logic gap, unlike `match`. `irrefutable_let_patterns` stopped linting chains in 1.95.
- `if let` guards in `match` arms (`Some(n) if let Some(m) = f(n) && m > 4 =>`) are a separate feature: stable since 1.95 on every edition.

## Changes owned by other skills

Edition 2024 also changed things outside the language. Hand them off:

- Cargo resolver `"3"` (MSRV-aware resolution) is the default for edition 2024 packages, and `cargo new` writes the edition key → `using-cargo`.
- Doctests are merged into one binary per crate on edition 2024 → `documenting-rust`.
- rustfmt's style edition 2024 changes formatting and import sorting → `linting-and-formatting-rust`.

## Earlier editions, still seen in old code

All are hard errors or behaviour changes in their edition.

- **2018:** paths in `use` start with a crate name, `crate`, `self` or `super` (`::foo` names an external crate); `dyn` is a keyword; anonymous trait-method parameters (`fn f(u8);`) are errors; `async`/`await` are keywords; `extern crate` is rarely needed (`alloc` and `test` still need it).
- **2021:**
  - `dyn Trait` is required (bare trait objects are errors).
  - `...` range patterns are errors; use `..=`.
  - `panic!("{}")` always takes a format string; use `std::panic::panic_any(x)` for a non-string payload.
  - `$p:pat` matches top-level `|`; `$p:pat_param` keeps the old meaning.
  - Unknown literal prefixes such as `z"x"` are reserved.
  - The prelude gains `TryFrom`, `TryInto` and `FromIterator`.
  - `array.into_iter()` yields values.
  - Closures capture disjoint fields, which changes drop order and auto traits. Force a whole-variable capture with `let _ = &p;` inside the closure.
