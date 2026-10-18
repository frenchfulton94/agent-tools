---
name: designing-rust-apis
description: Designs and reviews public Rust APIs of library crates and modules against the Rust API Guidelines, corrected for current Rust — naming (casing, `as_`/`to_`/`into_` conversions, getters, iterator names), which common traits to implement, `From`/`TryFrom`/`AsRef` conversions, library error types, constructors and builders, methods versus functions, `Deref`, generics versus trait objects, newtypes instead of bool arguments, validation, destructors, `Debug`, future-proofing with sealed traits, private fields and `#[non_exhaustive]`, and the Clippy lints behind them. Use when the user is designing, naming, or reviewing a public Rust API, preparing a crate for 1.0, asks what a type should derive or whether to use a builder, or wants an API Guidelines checklist review. Also use for symptoms - Clippy stays silent on a public API that breaks naming conventions, downstream crates can implement or exhaustively match something they should not, or a release broke callers via a field, variant, or auto-trait change.
license: MIT
---

# Designing Rust APIs

For library crates and the public modules of any crate. A binary's internals need little of this: the guidelines exist because a library's users cannot change its API, and every change to it is a SemVer event.

**Source and version basis.** The [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), read in full on 2026-10-17: 54 checklist items with IDs such as `C-CONV`. The guidelines call themselves recommendations, not a mandate. Much of the text dates from 2017–2018. It predates `#[non_exhaustive]`, `dep:` features, intra-doc links, `dyn` syntax, and edition 2024, and its examples use `try!`, `error-chain`, and `Error::description`. Apply the rules, not the examples. Every compile and lint claim below was measured on rustc and Clippy **1.97.1**.

## Checklist while writing a public API

**Naming**
- Acronyms are one word in `UpperCamelCase`: `Uuid`, `HttpResponse`, `Stdin`, not `UUID` or `HTTPResponse`. In `snake_case`, a single letter is a word only at the end: `btree_map`, `PI_2`. No `-rs` or `-rust` in crate names.
- Conversion prefixes encode cost and ownership. `as_` is free, borrowed to borrowed. `to_` is expensive (`Path::to_str` validates UTF-8, so it is not `as_str`), or takes a `Copy` value by value (`f64::to_radians`). `into_` consumes `self`, at any cost. `mut` goes where it sits in the return type: `as_mut_slice`. A wrapper hands back its inner value with `into_inner`.
- Getters have no `get_` prefix: `name()`, `name_mut()`. Plain `get` is for a type with one obvious thing to get (`Cell::get`). A bounds-checked getter can have `unsafe fn get_unchecked`.
- A collection's `iter()`, `iter_mut()`, and `into_iter()` return types named `Iter`, `IterMut`, and `IntoIter`. Implement `IntoIterator` for `&C` and `&mut C` too, so that `for x in &c` works. Other iterator types take the method's name (`keys` → `Keys`) and read with their module (`btree_map::Keys`).
- Error types read verb-object-error (`ParseIntError`), consistently within the crate. Feature names carry no placeholder words: `serde` and `std`, never `use-serde`, `with-std`, or a negative `no-std` (features are additive).

**Traits every public type should consider**
- Implement every common trait that applies, eagerly: `Debug` (on every public type), `Clone`, `Copy`, `PartialEq`, `Eq`, `PartialOrd`, `Ord`, `Hash`, `Default`, `Display`. The orphan rule stops downstream crates adding them later.
- Each one is also a promise. Removing `Copy`, `Eq`, `Hash`, or `Default` breaks callers, and a `Copy` type can never gain a non-`Copy` field. Derive `Copy` only on types that will always be plain values.
- Provide both a no-argument `new()` and `Default` when either makes sense, and make them agree.
- Collections implement `FromIterator` and `Extend`. Data structures implement serde's traits behind an optional feature named `serde`. Integer-like types used with `|` and `&` implement `Binary`, `Octal`, `LowerHex`, and `UpperHex`.
- `Send` and `Sync` are inferred. One `Rc`, `Cell`, or raw-pointer field removes them silently, and that removal is breaking. Assert them at compile time (see the table of corrections below).

**Conversions**
- Implement `From`, `TryFrom`, `AsRef`, and `AsMut`, never `Into` or `TryInto`. Use `From` only when the source type alone determines the result. Otherwise use a named constructor, which can also take extra arguments or be `unsafe`: `String::from_utf8`, `u64::from_str_radix`, `Box::from_raw`.
- Put the conversion on the more specific type: `str::from_utf8` and `str::as_bytes`, not methods on `[u8]`. When unsure, prefer the `as_`/`to_`/`into_` method to a `from_` function.

**Errors in a library**
- Return a type that implements `std::error::Error` (`core::error::Error` in `no_std`, since 1.81) and is `Send + Sync + 'static`. Never `Result<T, ()>`. With nothing to report, use a unit struct with `Display` and `Error`.
- `Display` text is lowercase with no trailing punctuation: "invalid IP address syntax".
- An erased error is `Box<dyn Error + Send + Sync + 'static>`. The `'static` bound is what allows `downcast_ref`.
- `impl From<dep::Error> for MyError` puts `dep` in your public API (see C-STABLE in the checklist).

**Construction and methods**
- Constructors are static inherent methods: `new`, a domain verb for I/O (`File::open`, `TcpStream::connect`), and `with_…` for secondary forms (`Vec::with_capacity`).
- Use a builder for many inputs, optional configuration, or construction with side effects. A non-consuming builder (`fn arg(&mut self, ..) -> &mut Self`, terminal `fn spawn(&self)`) allows both one-liners and conditional configuration. Make it consuming (`self -> Self` on every method) only when the terminal method must own the configuration, and mark those methods `#[must_use]`.
- Return several values as a tuple or struct, not through `&mut` out-parameters. Filling a caller's buffer (`read(&mut self, buf: &mut [u8])`) is the exception.
- Return what you computed anyway: `binary_search` returns `Result<usize, usize>`, `HashMap::insert` returns the old value, and `FromUtf8Error::into_bytes` gives the input back.
- Implement `Deref` only on smart pointers and wrappers that *are* their target (`String` → `str`, lock guards). Never use it as inheritance on a newtype. A smart pointer's own operations are associated functions (`Rc::strong_count(&rc)`, `Box::leak(b)`), so that they cannot shadow the target's methods.

**Flexibility**
- Take an argument by value only when you keep it. Never borrow and then `.clone()` inside. Take `&str`, `&[T]`, and `&Path`, not `&String`, `&Vec<T>`, or `&PathBuf`.
- Ask for the weakest bound that works: `impl IntoIterator<Item = T>` over `&[T]` when you only iterate, `AsRef<Path>` for paths. Take readers and writers by value (`R: Read`). `&mut R` also implements `Read`, so document that callers can pass `&mut file`.
- Generic functions are duplicated for each type. For a large body behind `AsRef` or `Into`, convert first and forward to a non-generic inner function.
- Decide early whether a trait is for `dyn` or for bounds. Keep a trait meant for `dyn` dyn compatible: put `where Self: Sized` on its generic methods, as `Iterator` does.

**Type safety and dependability**
- Use newtypes for distinct meanings (`Miles`, `Kilometers`). Use enums instead of `bool` or `Option` arguments: `Widget::new(Size::Small, Shape::Round)`, not `new(true, false)`. Use `bitflags` for flag sets, not enums with explicit discriminants.
- Validate arguments. In order of preference: a type that makes bad input unrepresentable, a runtime check that returns `Result`, `debug_assert!`, and finally an `_unchecked` opt-out sibling. That sibling is an `unsafe fn` with a `# Safety` section whenever skipping the check could cause UB.
- `Drop` never fails and never blocks. A panic in `drop` during unwinding aborts the process. Offer `fn close(self) -> Result<..>` (or `async fn shutdown`, since there is no async drop), and let `Drop` ignore or log the error.
- `Debug` output is never empty. For a type that holds secrets, write `Debug` by hand and end with `finish_non_exhaustive()`, which prints `Key { id: 7, .. }`. Do not drop `Debug`.

**Future-proofing: what you can change later without a major release**
- Use private fields when the type has invariants. For plain data, use public fields plus `#[non_exhaustive]` (see the table of corrections below). Decide before the first release.
- Mark enums that may gain variants `#[non_exhaustive]`, including nearly every error enum.
- Seal traits that callers use but should not implement.
- Hide compound return types behind a newtype, or behind `impl Trait` after reading its trade-offs below.
- Do not put derivable trait bounds on a generic struct (`struct S<T: Clone>`). Bound the impls instead, and let derives add their own bounds. Struct bounds are needed only when a field uses an associated type (`Cow<'a, B: ToOwned + ?Sized>`), for `?Sized`, or when a `Drop` impl needs the bound (otherwise E0367).
- At 1.0, every public dependency must be 1.0 or later. That includes any crate your API mentions through a `From` impl. License the crate `MIT OR Apache-2.0`, not Apache-2.0 alone.

What counts as a breaking change, and how to version it, is in `using-cargo`, in its publishing and SemVer reference.

## Where the guidelines are stale: current answers

**`#[non_exhaustive]` and private fields.** C-STRUCT-PRIVATE predates `#[non_exhaustive]`. These results were measured from a downstream crate, on a `#[non_exhaustive]` struct whose fields are all public:

- A struct literal is E0639, and so is `Config { retries: 1, ..Default::default() }`. Callers construct the value through `Default` or `new` and then assign fields.
- Fields can be read and written. Destructuring needs `..` (E0638). A `#[non_exhaustive]` enum needs a `_` arm (E0004).
- The attribute has no effect inside the defining crate.

Use private fields with getters for invariants, and public fields with `#[non_exhaustive]` for plain data. Do not use the old `_priv: ()` field or a hidden variant: Clippy's `manual_non_exhaustive` flags both and is on by default. Adding `#[non_exhaustive]` later is itself a breaking change.

**Sealed traits.** The pattern still holds:

```rust
/// This trait is sealed and cannot be implemented outside this crate.
pub trait Format: private::Sealed { fn width(&self) -> usize; }
mod private { pub trait Sealed {} impl Sealed for u8 {} }
```

- On a downstream `impl Format for Local`, rustc itself explains the error (E0277): "`Format` is a "sealed trait", because to implement it you also need to implement `up::private::Sealed`, which is not accessible". No attribute is needed for that error.
- For a better error at a call site such as `use_format(Local)`, put `#[diagnostic::on_unimplemented(message = "…", note = "Format is sealed; it is implemented for u8 and u16")]` on the public trait (stable since 1.78). It replaces the E0277 headline and adds the note.
- `Sealed` must be `pub` inside a private module. A `pub(crate) trait Sealed` supertrait was error E0445; it now only triggers the warn-by-default `private_bounds` lint ("trait `Sealed` is more private than the item `Format`").
- The allow-by-default `unnameable_types` lint flags the pattern: "trait `private::Sealed` is reachable but cannot be named". That is the intended effect. If the crate enables the lint, put `#[expect(unnameable_types, reason = "sealed trait")]` on `Sealed` (measured clean).
- To seal a single method instead of the whole trait, give it a default body and a parameter of a private type. Downstream crates can still implement the trait, but overriding or calling that method is E0603 "module `private` is private".
- rustdoc renders `pub trait Format: Sealed` with no link, so state in the docs that the trait is sealed.

**`impl Trait` in return position, compared with a newtype (C-NEWTYPE-HIDE).**
- An opaque return type leaks auto traits. In a measured case, a body that captured an `Rc` made a caller's `T: Send` bound fail (E0277) through `impl Iterator<Item = u8>`. A change to the body alone breaks callers. A newtype's `Send` and `Sync` appear on its docs page and can be asserted.
- Callers cannot name the type, so they cannot store it in a field. `type Numbers = impl Iterator<…>` is E0658 on stable.
- `-> impl Iterator + Clone` promises `Clone` unconditionally, so the function must require `I: Clone` of every caller. A newtype can implement `Clone`, `DoubleEndedIterator`, and `ExactSizeIterator` conditionally, `where I: Clone`.
- Edition 2024 return-position `impl Trait` captures every in-scope lifetime; see `writing-rust`.

Use `impl Trait` for simple or internal returns, and a newtype for iterator types in a stable public API.

**`impl Trait` in argument position.** The guidelines do not discuss it. `apit::<u8>(1)` on `fn apit(x: impl Display)` is E0107 "function takes 0 generic arguments" (measured). Turbofish for named parameters alongside an `impl Trait` parameter works (since 1.63). Use a named generic for any parameter a caller may need to turbofish, because switching forms later changes the generic-argument count.

**Errors.** `Error::description` and `cause` are deprecated; calling `description` warns. Implement `Display` and `source` instead. `Error::provide` is still unstable (E0658 `error_generic_member_access`). `io::Error::other(e)` requires `e: Error + Send + Sync + 'static`, so an error with a `Cell` field cannot be wrapped (E0277). The guidelines' `error-chain` is abandoned.

| Item | The guideline says | Current answer (measured on 1.97.1 unless noted) |
|---|---|---|
| C-HIDDEN | put `#[doc(hidden)]` on `impl From<PrivateError> for PublicError` | rustdoc already omits impls that mention a private type. `#[doc(hidden)]` is still needed to hide an impl between public types |
| C-SEND-SYNC | assert in a `#[test]` | assert at compile time: `const _: () = { const fn check<T: Send + Sync>() {} check::<Handle>(); };` fails the build with E0277 |
| C-BITFLAG | bitflags 1 syntax | bitflags 2.x: derives are not implicit, so write `#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]` inside `bitflags!` (without it, `{:?}` and `==` fail). bitflags 2 implements `Binary`, `Octal`, and the hex traits. `from_bits` rejects unknown bits, `from_bits_truncate` drops them, and `from_bits_retain` keeps them |
| C-OBJECT | "object safe" | "dyn compatible"; the rules are in `writing-rust`, in its traits and generics reference |
| C-LINK | `[x]: trait.X.html` link targets | intra-doc links, owned by `documenting-rust` |
| C-METADATA | lists `authors` | `authors` is deprecated. Clippy's `cargo_common_metadata` checks `description`, `license`, `repository`, `readme`, `keywords`, and `categories` |
| C-STABLE | | `exported_private_dependencies` cannot fire on stable. Cargo prints "ignoring `public` on dependency …, pass `-Zpublic-dependency`", so check public dependencies by hand |
| C-FEATURE | relies on the implicit feature of an optional dependency | with `dep:` you name the feature yourself: `serde = ["dep:serde"]`, keeping the name `serde` |
| C-BUILDER | `Box<io::Write + Send>` | `Box<dyn io::Write + Send>`. Bare trait objects are an error from edition 2021 |
| C-CASE (Style Guide) | name a keyword binding `r#crate` | `crate`, `self`, `super`, and `Self` cannot be raw identifiers (error). Write `crate_`. `r#type` and `r#gen` work |

**Where std departs from the guidelines.** Do not rename code that mirrors these:

- `std::net::AddrParseError` is object-verb-error. The guideline uses that very name as its counter-example.
- Single-value wrappers use `get_ref` and `get_mut` (`Cursor`, `Pin`, `Mutex`). This fits the rule that `get` is for one obvious thing.
- `Vec<T>` derefs to `[T]`, `PathBuf` to `Path`, and so do lock guards, `ManuallyDrop`, and `AssertUnwindSafe`, though none is a pointer. The rule underneath: deref only to what the wrapper owns or *is*, never to borrow another type's methods.
- `io::Error` and `fmt::Error` are each named `Error` within their module. Clippy's restriction lint `error_impl_error` flags that style, and `module_name_repetitions` flags the opposite style (`io::IoError`). Choose one style per crate.

## Clippy enforces part of this, and is silent on public items by default

`avoid-breaking-exported-api` defaults to `true` in `clippy.toml`. It suppresses lints on public items when the fix would change a public name or signature. Measured: `pub struct HTTP`, `pub fn as_str(self)`, `pub fn into_thing(&self)`, and a public `enum Cake { BlackForestCake, .. }` raised no warning, while the same code on private items did. Clippy's configuration docs list 19 affected lints, including `wrong_self_convention`, `upper_case_acronyms`, `enum_variant_names`, `trivially_copy_pass_by_ref`, `unnecessary_wraps`, `ref_option`, `unused_self`, and `rc_buffer` (all eight measured). **A clean Clippy run says nothing about public naming.**

For a crate before 1.0, or for an API review:

```bash
printf 'avoid-breaking-exported-api = false\nupper-case-acronyms-aggressive = true\n' >> clippy.toml
cargo clippy --all-targets --all-features -- -W clippy::pedantic -W clippy::cargo \
  -W missing_debug_implementations -W clippy::exhaustive_enums -W clippy::exhaustive_structs
```

- `upper_case_acronyms` flags only fully capitalised names (`HTTP`). It catches `HTTPResponse` only with `upper-case-acronyms-aggressive = true`.
- `missing_errors_doc` and `missing_panics_doc` are **pedantic**, so off by default. `missing_safety_doc` is on by default (style).
- `fn_params_excessive_bools` fires only above three `bool` parameters, so `new(true, false)` passes. The guideline is stricter than the lint.
- No lint checks `get_` prefixes, word order, builder shape, `Deref` misuse, failing destructors, or where a conversion lives. Review those by hand.

The checklist reference names the lint for each item, with its group.

## Where to look

- `references/checklist.md` — read for a full API review, or when citing a guideline by ID. All 54 items in the guidelines' order, each with its current rule, what has changed since it was written, and the rustc or Clippy lint (and group) that enforces it.

## Neighbouring skills

- Which changes are breaking, version bumps, `#[deprecated]` before removal → `using-cargo`. Feature syntax and `[lints]` tables → `using-cargo`.
- Trait mechanics (dyn compatibility, coherence, `impl Trait` capture rules), `#[must_use]`, `#[diagnostic]` attributes, error-handling design inside an application → `writing-rust`.
- Doc comments, `# Errors`/`# Panics`/`# Safety` sections, examples, intra-doc links, `#[doc(hidden)]` mechanics → `documenting-rust`.
- What an individual lint means, and lint levels → `fixing-rust-compile-errors`.
