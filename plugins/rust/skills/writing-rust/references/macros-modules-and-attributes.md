# Macros, modules and attributes

Rules from the Rust Reference (1.99) and std docs. Results marked *measured* were compiled on rustc 1.97.1.

## Contents

- [`macro_rules!`](#macro_rules)
- [Procedural macros](#procedural-macros)
- [Modules and files](#modules-and-files)
- [`use`, re-exports and visibility](#use-re-exports-and-visibility)
- [Conditional compilation](#conditional-compilation)
- [Lint and diagnostic attributes](#lint-and-diagnostic-attributes)
- [Other attributes worth getting right](#other-attributes-worth-getting-right)

## `macro_rules!`

**Fragment specifiers:** `block expr expr_2021 ident item lifetime literal meta pat pat_param path stmt tt ty vis`.

- `expr` follows the edition of the defining crate. On 2024 it also matches `_` and `const { }`; `expr_2021` keeps the old grammar (stable on every edition since 1.83).
- `pat` matches top-level or-patterns (`A | B`) since 2021; `pat_param` does not.
- `ident` does not match `_`. `literal` matches `-1`. `vis` may match nothing. `stmt` has no trailing semicolon.

**Follow-set restrictions** (what may come right after a fragment in a matcher):

| Fragment | May be followed by |
|---|---|
| `expr`, `expr_2021`, `stmt` | `=>` `,` `;` |
| `pat` (2021+) | `=>` `,` `=` `if` `in` |
| `pat_param` | `=>` `,` `=` `\|` `if` `in` |
| `path`, `ty` | `=>` `,` `=` `\|` `;` `:` `>` `>>` `[` `{` `as` `where`, or a `block` fragment |
| `vis` | `,`, a non-raw identifier other than `priv`, a token that can start a type, or an `ident`/`ty`/`path` fragment |
| everything else | anything |

A repetition separator must itself be allowed to follow the fragment (`$($t:ty)-+` is illegal). An unseparated `$($e:expr)*` is accepted today though it breaks the documented invariant (*measured*); it may be rejected in a future edition.

**Matching.**

- Rules are tried in order and the first that matches is transcribed. If transcription then fails, later rules are not tried.
- There is no lookahead: `($($i:ident)* $j:ident)` is a "local ambiguity" error.
- A captured fragment is opaque when forwarded to another macro: after `$e:expr` has matched `3`, an inner macro's literal `3` arm will not match it. Only `ident`, `lifetime` and `tt` fragments stay transparent, so capture as `tt` when forwarding.
- The outer delimiters of a rule match any delimiter pair. `$` cannot be matched literally.
- In the transcriber, every metavariable must appear at the same repetition depth as in the matcher, each repetition must contain at least one metavariable, and metavariables repeated together must repeat the same number of times.

**Hygiene and paths.**

- Hygiene is mixed-site: local variables, loop labels and block labels resolve where the macro is defined; everything else (functions, types, macros, items) resolves where it is invoked. A local created by one invocation is invisible to a later invocation.
- Refer to items of the defining crate as `$crate::path::item`, and to other macros of that crate as `$crate::helper!()`. `$crate` does not bypass privacy: the item must be visible from the call site.
- `#[macro_export(local_inner_macros)]` is a migration aid only; use `$crate::` in new code.

**Scope.**

- A `macro_rules!` macro is in textual scope from its definition to the end of the enclosing module, including child modules declared after it, even in other files. Within a file it must be defined before use; functions have no such ordering rule.
- Its default visibility is effectively `pub(crate)`. `#[macro_export]` places it at the crate root (`crate::m!`, `other_crate::m!`), whatever module defines it. To give a non-exported macro a path, write `pub(crate) use m;` after it.
- `#[macro_use]` on a `mod` extends the textual scope past the module. `#[macro_use] extern crate` is the old style; import macros with `use` (lint `macro_use_extern_crate`).
- A `macro_rules!` invoked with `()` or `[]` in item position needs a trailing `;`.

## Procedural macros

- Live in a crate with `[lib] proc-macro = true`, at the crate root; they cannot be used in the crate that defines them. `proc_macro` is in the extern prelude of such crates, so `extern crate proc_macro;` is unnecessary. A proc-macro crate always builds for the host, even when cross-compiling.
- Signatures: `#[proc_macro] fn(TokenStream) -> TokenStream`; `#[proc_macro_derive(Name, attributes(helper))] fn(TokenStream) -> TokenStream`; `#[proc_macro_attribute] fn(attr: TokenStream, item: TokenStream) -> TokenStream`.
- Report errors by emitting `compile_error!` tokens (with `syn`, `syn::Error::to_compile_error()`), or by panicking with a specific message; a panic becomes a compile error.
- Proc macros are unhygienic: generate absolute paths (`::core::option::Option`, `::std::...`) and unlikely names (`__my_crate_internal`).
- A derive **appends** items after the input; an attribute macro **replaces** the item with its output. Doc comments reach a macro as `#[doc = "…"]` attributes. Using a derive helper attribute before the `#[derive]` that introduces it is deprecated.
- Proc macros run arbitrary code at build time with the same access as build scripts.
- Convention: the derive crate for `foo` is `foo_derive`, re-exported by `foo`.

## Modules and files

- `mod garden;` loads `garden.rs` or `garden/mod.rs`; its submodule `mod vegetables;` loads `garden/vegetables.rs` or `garden/vegetables/mod.rs`. Prefer `garden.rs` plus a `garden/` directory. Having both `garden.rs` and `garden/mod.rs` is an error.
- `mod` declares a module once; it is not an include. Other files refer to it by path. `use` never affects which files compile.
- `#[path = "x.rs"]` on a file module is relative to the directory of the current file: in `src/a/b.rs`, `#[path = "foo.rs"] mod c;` loads `src/a/foo.rs`, not `src/a/b/foo.rs`.
- For a package with a library and a binary, keep the module tree in `src/lib.rs` and a thin `main.rs` that uses the library by its crate name. Only the library's public API is reachable from the binary and from integration tests.
- `alloc` is not added to the extern prelude automatically: a `no_std` crate needs `extern crate alloc;`. `#![no_std]` does not stop `std` from being linked if any dependency uses it. The idiom for an optional-std crate is `#![no_std]` plus `#[cfg(feature = "std")] extern crate std;`.

## `use`, re-exports and visibility

- `use` creates a name only in the scope where it appears; a child module does not inherit it. The Book's convention: import the parent module for functions (`hosting::add()`), and the full path for types, traits and macros.
- Globs are shadowed by explicit imports and local items. Two globs that provide the same name are an error only where the name is used ("`X` is ambiguous").
- `use` cannot reach type-relative paths: `use Alias::Variant;` through a type alias, or `use Enum::ASSOC_CONST;` for an inherent constant, is "unresolved import", though both work in expressions.
- `use std::io::{self, Write};` imports the module and the trait. `{self}` needs a module, enum or trait parent; `use S::{self};` for a struct is an error since 1.96. Trailing `self` (`use m::E::self;`, `use m::inner::self as _;`) is accepted on 1.97 (*measured*).
- `crate`, `self`, `super` and `$crate` must be renamed when imported: `use super as parent;`.
- Items are private to their parent module by default; a child sees everything in its ancestors. `pub mod` exposes the name, not the contents. Variants of a `pub enum` and items of a `pub trait` are public. A `pub struct` with a private field cannot be built outside its module without a constructor.
- `pub(crate)`, `pub(super)`, `pub(in crate::a::b)` (the path must be an ancestor and start with `crate`, `self` or `super`).
- `pub use` re-exports make a public path through private modules: with a private `mod imp` and `pub use imp::api;`, outsiders can use `api` but not `imp::api`.
- A `pub` item that is reachable but not nameable (returned from a public function, defined in a private module) triggers `unnameable_types` (allow). `unreachable_pub` (allow) flags `pub` that should be `pub(crate)`.

## Conditional compilation

- Predicates: an option (`unix`, `target_os = "linux"`, `feature = "x"`), `all(..)` (empty is true), `any(..)` (empty is false), `not(..)`, and `true`/`false` (since 1.88).
- **`cfg_select!`** (1.95) expands the first arm whose predicate holds, with `_` as the fallback, in item or expression position. With no matching arm and no `_` it is a compile error. It replaces the `cfg-if` crate.

```rust
cfg_select! {
    unix => { fn open() { /* unix */ } }
    windows => { fn open() { /* windows */ } }
    _ => { compile_error!("unsupported platform"); }
}
let sep = cfg_select! { windows => '\\', _ => '/' };
```

- `cfg!(pred)` is a `bool`; both branches must type-check. `#[cfg]` removes code, but the removed code must still parse.
- `#[cfg_attr(pred, attr1, attr2)]` expands to zero or more attributes.
- `target_env` is often `""` on GNU-style targets. `target_has_atomic = "64"` gates atomic widths; `target_has_atomic_primitive_alignment` is stable since 1.97.
- In a build script, `cfg!` describes the **host**; read `CARGO_CFG_*` environment variables for the target.

## Lint and diagnostic attributes

- Levels `allow`, `expect`, `warn`, `deny`, `forbid`, each accepting `reason = "…"`, which is shown in the diagnostic.
- **`#[expect(lint)]`** (1.81) suppresses the lint and warns (`unfulfilled_lint_expectations`) when the lint no longer fires. Prefer it to `#[allow]` for a temporary or deliberate suppression.
- Inside `forbid`, other level changes are errors except `deny`. Use `#![deny(warnings)]`, not `#![forbid(warnings)]` (`forbidden_lint_groups`).
- A later, more specific attribute overrides a group (`#[allow(unused)] #[deny(unused_must_use)]`). The `warnings` group ignores order and covers every lint that would warn.
- `#[must_use]` goes on functions, types and **traits** (then every `impl Trait` or `dyn Trait` return is must-use). It does nothing on a function inside a trait impl. It does not fire for `Result<(), E>` or `ControlFlow<E, ()>` when `E` is uninhabited, such as `Infallible` (1.92). Discard deliberately with `let _ = f();` or `_ = f();`.
- `#[diagnostic::on_unimplemented(message = "…", label = "…", note = "…")]` on a trait customises E0277; only `{Self}` and the trait's generic parameter names are interpolated. `#[diagnostic::do_not_recommend]` (1.85) on an impl keeps it out of error suggestions. Unknown `diagnostic::` attributes only warn.

## Other attributes worth getting right

- **`#[non_exhaustive]`** has effect only outside the defining crate. There: a non-exhaustive struct or variant cannot be built with a literal or `..base`, and its patterns need `..`; a non-exhaustive enum needs a wildcard arm; `as` casts are forbidden on an enum with a non-exhaustive variant. Adding `#[non_exhaustive]` to an existing public item is a breaking change.
- **`#[deprecated(since = "1.2.0", note = "use `bar`")]`**; `since` is not checked by rustc. Not allowed on items in trait impls.
- **`#[track_caller]`** makes `Location::caller()` and panic locations report the caller. Through a function pointer or `dyn` method call, the location is the attributed function's own definition.
- **`#[inline]`, `#[inline(always)]`, `#[inline(never)]`, `#[cold]`** are hints. `#[inline]` matters mostly for small functions called across crates. `std::hint::cold_path()` (1.95) marks a cold branch inside a function.
- **Unsafe attributes:** `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "…")]`, `#[unsafe(link_section = "…")]` (required on 2024) and `#[unsafe(naked)]`. `no_mangle` is not allowed on generic items; with `export_name` present, `export_name` wins.
- `#![recursion_limit = "N"]` (default 128) covers macro expansion depth and auto-deref depth. `#![type_length_limit]` is not enforced on stable.
- Attribute arguments cannot carry literal suffixes (`#[x = 1u8]` is rejected). `#[doc = include_str!("../README.md")]` expands after other macros and derives.
