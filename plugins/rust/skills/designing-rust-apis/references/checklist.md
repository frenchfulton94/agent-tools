# Rust API Guidelines checklist, current to Rust 1.97

All 54 items of the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/checklist.html), in the guidelines' order and by their IDs. Each row gives the rule as it applies today, then what has changed since the guideline was written or where std departs from it, then the lint that enforces it.

Lint column key. **default** means Clippy warns with no flags. **pedantic**, **nursery**, **restriction**, and **cargo** are the allow-by-default Clippy groups; enable restriction lints one by one. **rustc allow** is an allow-by-default compiler lint. ⊘ marks a lint that `avoid-breaking-exported-api = true` (Clippy's default) silences on public items. Every Clippy lint's group, and each ⊘, was measured on Clippy 1.97.1; rustc and rustdoc levels come from their lint listings. "—" means no lint checks the item, so review it by hand.

## Contents

- [Naming](#naming)
- [Interoperability](#interoperability)
- [Macros](#macros)
- [Documentation](#documentation)
- [Predictability](#predictability)
- [Flexibility](#flexibility)
- [Type safety](#type-safety)
- [Dependability](#dependability)
- [Debuggability](#debuggability)
- [Future proofing](#future-proofing)
- [Necessities](#necessities)

## Naming

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-CASE | Types, traits, variants, and type parameters are `UpperCamelCase`. Functions, methods, modules, locals, fields, and macros are `snake_case`. Constants and statics are `SCREAMING_SNAKE_CASE`. Lifetimes are short (`'a`, `'de`). Acronyms count as one word (`Uuid`, `Stdin`). A single letter is a word only at the end (`btree_map`, `PI_2`). No `-rs` or `-rust` in a crate name | A keyword used as a name: `crate`, `self`, `super`, and `Self` cannot be raw identifiers (error), so write `crate_`, not `krate`. `r#type` works | rustc `nonstandard_style` (warn); `upper_case_acronyms` default ⊘, which catches `HTTPResponse` only with `upper-case-acronyms-aggressive = true`; `enum_variant_names` default ⊘ |
| C-CONV | `as_`: free, borrowed to borrowed. `to_`: expensive, or a `Copy` value by value. `into_`: consumes `self`, at variable cost (`String::into_bytes` is free, `BufWriter::into_inner` may flush). `mut` goes where it sits in the return type (`as_mut_slice`). A single-value wrapper exposes `into_inner` | — | `wrong_self_convention` default ⊘. It checks the `self` kind per prefix: `as_` takes `&self` or `&mut self`; `into_` takes `self`; `to_` takes `&self`, or `self` on a `Copy` type; `is_` takes `&self` or nothing. It does not check `to_` in trait definitions |
| C-GETTER | No `get_` prefix: `first()`, `first_mut()`. `get` alone when there is one obvious value (`Cell::get`). `unsafe fn get_unchecked` for a checked getter's opt-out. A getter (`TempDir::path`) differs from a conversion (`TempDir::into_path`) | std uses `get_ref` and `get_mut` on single-value wrappers (`Cursor`, `Pin`, `Mutex`) | — (`misnamed_getters`, default, only catches a getter returning a differently named field) |
| C-ITER | A collection of `U` offers `iter()` (yielding `&U`), `iter_mut()` (yielding `&mut U`), and `into_iter()` (yielding `U`). Applies to methods on homogeneous collections only: `str` has `bytes()` and `chars()` | Pair `iter` with `impl IntoIterator for &C` (and `iter_mut` with `&mut C`) so that `for x in &c` works | `iter_without_into_iter`, `into_iter_without_iter`, `iter_not_returning_iterator` (pedantic) |
| C-ITER-TY | `iter` returns `Iter`, `iter_mut` returns `IterMut`, `into_iter` returns `IntoIter`, `keys` returns `Keys`. Names read with the module: `vec::IntoIter` | With `impl Trait` returns there is no type to name. See C-NEWTYPE-HIDE for when to use a named type | — |
| C-FEATURE | No placeholder words: `abc`, not `use-abc` or `with-abc`. The std feature is named exactly `std`. Never a negative `no-abc`, because features are additive | With `dep:` (Rust 1.60), the optional dependency's implicit feature is gone and you name it yourself: `serde = ["dep:serde"]` | `redundant_feature_names`, `negative_feature_names` (cargo) |
| C-WORD-ORDER | Error types read verb-object-error, like std's `ParseIntError`, `JoinPathsError`, and `RecvTimeoutError`. Consistency within the crate matters more than the exact order | std's own `net::AddrParseError` is object-verb, and the guideline cites it as the wrong order | — (`module_name_repetitions`, restriction, flags `io::IoError`-style names; `error_impl_error`, restriction, flags `io::Error`-style names) |

## Interoperability

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-COMMON-TRAITS | Eagerly implement every common trait that applies: `Copy`, `Clone`, `Eq`, `PartialEq`, `Ord`, `PartialOrd`, `Hash`, `Debug`, `Display`, `Default`. Downstream crates cannot add them (orphan rule). Provide both `Default` and a no-argument `new` | Not in the guideline: each derive is a SemVer promise. Removing one is breaking, and a `Copy` type cannot gain a non-`Copy` field. Implement `Display`, never `ToString` | rustc `missing_copy_implementations`, `missing_debug_implementations` (rustc allow); `new_without_default`, `len_without_is_empty`, `inherent_to_string`, `to_string_trait_impl` (default); `derive_partial_eq_without_eq` (nursery) |
| C-CONV-TRAITS | Implement `From`, `TryFrom`, `AsRef`, and `AsMut` where they make sense, never `Into` or `TryInto`. Lossless conversions get `From` (`From<u16> for u32`); lossy ones get `TryFrom` | — | `from_over_into`, `infallible_try_from` (default); `fallible_impl_from` (nursery) |
| C-COLLECT | Collections implement `FromIterator` (for `collect`) and `Extend` (for adding to an existing collection; `unzip` and `partition` need `Default + Extend`) | — | — |
| C-SERDE | Data structures implement `Serialize` and `Deserialize`, behind an optional dependency whose feature is named `serde` (not `serde_impls`). Derive with `#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]` | Spell the feature `serde = ["dep:serde"]` when using `dep:` syntax | `unsafe_derive_deserialize` (pedantic): a derived `Deserialize` bypasses constructor invariants |
| C-SEND-SYNC | Types are `Send` and `Sync` where possible. A type holding raw pointers needs an `unsafe impl` when it is sound | Assert at compile time rather than in a `#[test]`: `const _: () = { const fn check<T: Send + Sync>() {} check::<MyType>(); };` (E0277 when it fails, measured) | `non_send_fields_in_send_ty` (nursery) |
| C-GOOD-ERR | Every error type in a public `Result` implements `Error`, is `Send + Sync`, and is meaningful. Never `()` as an error. `Display` text is lowercase, concise, and has no trailing punctuation. An erased error is `Box<dyn Error + Send + Sync + 'static>`, where `'static` enables downcasting | `Error::description` and `cause` are deprecated (calling `description` warns). `core::error::Error` is stable (1.81) for `no_std`. `Error::provide` is still unstable (E0658). `io::Error::other` (1.74) needs `Send + Sync + 'static`. `error-chain` is abandoned | `result_unit_err`, `result_large_err` (default); `map_err_ignore`, `error_impl_error` (restriction) |
| C-NUM-FMT | Number-like types used with bitwise operators implement `UpperHex`, `LowerHex`, `Octal`, and `Binary`. Quantity types (`Nanoseconds(u64)`) need not | `bitflags` 2 types get these implementations from the macro (measured) | — |
| C-RW-VALUE | Generic reader and writer functions take `R: Read` or `W: Write` by value. Document that `&mut reader` can be passed, because `&mut R: Read` | — | `needless_pass_by_value` (pedantic) does not fire on a reader that is read from (measured) |

## Macros

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-EVOCATIVE | Input syntax mirrors the output: require the `struct` keyword if the macro defines a struct, and end constants with `;` | — | — |
| C-MACRO-ATTR | Item macros accept attributes on each generated item and outer attributes (such as `#[derive]`) on a generated type: capture `$(#[$m:meta])*` and re-emit it | — | — |
| C-ANYWHERE | Item macros work wherever items are allowed, at module scope and inside a function body. Test both. A generated `super::` path breaks inside a function | — | — |
| C-MACRO-VIS | Generated items are private unless the input says `pub`. Use a `$vis:vis` fragment | — | — |
| C-MACRO-TY | A `$t:ty` fragment works with primitives, relative and absolute paths, `super::` paths, and generics. Placing `$t` inside a generated module breaks relative paths | Use `$crate::` for the macro's own paths. Edition 2024 changes the `expr` fragment (see `writing-rust`) | — |

## Documentation

Documentation conventions are owned by `documenting-rust`. These rows only map the IDs.

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-CRATE-DOC | Crate docs are thorough and include examples | — | rustdoc `missing_crate_level_docs` (allow) |
| C-EXAMPLE | Every public module, type, trait, function, method, and macro has an example, within reason. Show *why* to use it, not just how to call it. A link to another item's example can suffice | `missing_doc_code_examples` is nightly-only | — |
| C-QUESTION-MARK | Examples use `?`, not `try!` or `unwrap` | `try!` is a reserved keyword since edition 2018. For the hidden `Ok::<(), E>(())` trailer, see `documenting-rust` | — |
| C-FAILURE | Document `# Errors`, `# Panics`, and `# Safety`, including on trait methods whose implementations may fail | — | `missing_safety_doc` (default); `missing_errors_doc`, `missing_panics_doc` (pedantic, *not* on by default) |
| C-LINK | Prose links to relevant items | Write intra-doc links (`` [`Value`] ``, `[Self::method]`), not the guideline's `trait.X.html` targets | rustdoc `broken_intra_doc_links` (warn) |
| C-METADATA | `Cargo.toml` has `description`, `license`, `repository`, `keywords`, and `categories`. Set `documentation` only when docs are not on docs.rs, and `homepage` only for a separate site | The guideline lists `authors`, which Cargo has deprecated. Add `readme` and `rust-version` | `cargo_common_metadata` (cargo): checks description, license, repository, readme, keywords, categories (measured) |
| C-RELNOTES | Release notes identify every breaking change. Tag each published version with an annotated tag (`git tag -a`) | Breaking-change rules are in `using-cargo` (publishing and SemVer reference) | — |
| C-HIDDEN | rustdoc shows what users need and nothing more. Use `pub(crate)` for internals and `#[doc(hidden)]` for impls users never need | rustdoc already omits impls that mention a private type, so `impl From<PrivateError> for PublicError` needs no attribute. `#[doc(hidden)]` is needed only for impls between public types (both measured) | rustc `unreachable_pub`, `unnameable_types` (rustc allow) |

## Predictability

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-SMART-PTR | A smart pointer's own operations are associated functions, not methods: `Box::into_raw(b)`, `Rc::strong_count(&rc)`, `Arc::try_unwrap(a)`. With `Deref`, a method would shadow the pointee's method of the same name | — | `clone_on_ref_ptr` (restriction) asks for `Rc::clone(&rc)` |
| C-CONV-SPECIFIC | A conversion lives on the more specific type, the one with the extra invariant: `str::from_utf8` and `str::as_bytes`, nothing on `[u8]`. Prefer `to_`/`as_`/`into_` methods to `from_` functions | — | — |
| C-METHOD | An operation with a clear receiver is a method. Methods need no import, autoborrow, and appear in rustdoc under the type | — | `unused_self` ⊘ (pedantic) flags the opposite: a method that never uses `self` |
| C-NO-OUT | Return several values as a tuple or struct, not through `&mut` out-parameters. Filling a caller's buffer is the exception | — | — |
| C-OVERLOAD | Implement an operator trait only for an operation that behaves like the operator (for example, `Mul` is associative) | — | `suspicious_arithmetic_impl`, `suspicious_op_assign_impl` (default) |
| C-DEREF | Only smart pointers implement `Deref` and `DerefMut` | std also derefs non-pointers it owns or is: `Vec<T>` → `[T]`, `PathBuf` → `Path`, `OsString`, `Cow`, lock guards, `ManuallyDrop`, `AssertUnwindSafe`. The working rule: never `Deref` to borrow another type's methods | — |
| C-CTOR | Constructors are static inherent methods: `new`, domain verbs for I/O (`File::open`, `TcpStream::connect`), `with_…` secondary forms (`Vec::with_capacity`), `from_…` conversion constructors. `new` and `Default` behave the same. Name a fallible constructor `try_new` or `build` (see `writing-rust`) | — | `new_ret_no_self`, `should_implement_trait`, `self_named_constructors`, `new_without_default` (default) |

## Flexibility

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-INTERMEDIATE | Return data you computed anyway: `binary_search` returns `Result<usize, usize>`, `HashMap::insert` returns the old value, `FromUtf8Error` returns the bytes and `valid_up_to` | The entry API is the same idea | — |
| C-CALLER-CONTROL | Take ownership by value when the function keeps the argument, and borrow when it does not. Never borrow and then clone inside. Do not add a `Copy` bound just to signal that a type is cheap | — | `ptr_arg`, `owned_cow` ⊘ (default); `needless_pass_by_value`, `implicit_hasher`, `trivially_copy_pass_by_ref` ⊘, `ref_option` ⊘ (pedantic); `needless_pass_by_ref_mut` ⊘ (nursery) |
| C-GENERIC | Use generics to state exactly what a function needs: `I: IntoIterator<Item = i64>` over `&[i64]` or `&Vec<i64>`, `P: AsRef<Path>` for paths. The trade-offs are code size and homogeneous types | Not in the guideline: argument-position `impl Trait` cannot be turbofished (E0107, measured), so use a named generic where callers may need one. Forward a large generic body to a non-generic inner function | `impl_trait_in_params` (restriction) |
| C-OBJECT | Decide early whether a trait is for `dyn` or for bounds. Exclude generic methods from the vtable with `where Self: Sized`, as `Iterator` does | "Object safe" is now "dyn compatible". `async fn` and `-> impl Trait` methods also make a trait dyn incompatible. Rules: `writing-rust` (traits and generics reference) | — |

## Type safety

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-NEWTYPE | Newtypes make distinct meanings distinct types: `Miles(f64)` versus `Kilometers(f64)` | The guideline's newtype has a `pub` field. When the newtype holds an invariant, keep the field private (C-STRUCT-PRIVATE) | — |
| C-CUSTOM-TYPE | Arguments carry meaning through types, not `bool` or `Option`: `Widget::new(Small, Round)`, not `Widget::new(true, false)` | — | `fn_params_excessive_bools`, `struct_excessive_bools` (pedantic) fire only above 3 bools (`max-fn-params-bools`, `max-struct-bools`) |
| C-BITFLAG | Use the `bitflags` crate for sets of flags. Use explicit discriminants only for one-of-many values that must match another system's integers | bitflags 2.x: derives are no longer implicit, so write `#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]` inside `bitflags!`. `from_bits` returns `None` on unknown bits, `from_bits_truncate` drops them, `from_bits_retain` keeps them (measured with 2.13.2) | — |
| C-BUILDER | Use a builder for many inputs, compound or optional configuration, or construction with side effects. Name it after what it does when possible (`Command` builds a `Child`). The builder's constructor takes only required data. Prefer non-consuming (`&mut self -> &mut Self`, terminal `&self`); consume only when the terminal method needs ownership, and then every method takes `self` | std's consuming builder is `thread::Builder`. The guideline's `Box<io::Write + Send>` is `Box<dyn io::Write + Send>` today | `return_self_not_must_use` (pedantic) for consuming builders |

## Dependability

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-VALIDATE | Enforce validity rather than be liberal in what you accept. Prefer, in order: static (a type that rules out bad input), dynamic (return `Result` or panic, documented), `debug_assert!`, and an opt-out `_unchecked` sibling or a `raw` module | An `_unchecked` sibling whose misuse can cause UB is an `unsafe fn` with `# Safety` (`str::from_utf8_unchecked`, `NonZero::new_unchecked`) | — |
| C-DTOR-FAIL | Destructors never fail. A panic in `drop` while unwinding aborts. Offer a fallible `close(self) -> Result<..>`; `Drop` then ignores or logs errors | std follows this pattern: `File`'s drop ignores close errors (hence `sync_all`), and `BufWriter`'s drop ignores flush errors (hence `flush` and `into_inner`) | — |
| C-DTOR-BLOCK | A destructor that may block has a non-blocking alternative that prepares for an infallible teardown | Stable Rust has no async drop, so async types need an explicit `async fn shutdown` or `close` | — |

## Debuggability

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-DEBUG | Every public type implements `Debug` | For secrets, write `Debug` by hand and end with `finish_non_exhaustive()`, which prints `Key { id: 7, .. }` (measured) | rustc `missing_debug_implementations` (rustc allow); `missing_fields_in_debug` (pedantic) |
| C-DEBUG-NONEMPTY | `Debug` output is never empty: `""` prints `""` and an empty `Vec` prints `[]` | A derived `Debug` on `struct Unit;` prints `Unit` (measured) | — |

## Future proofing

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-SEALED | Seal traits that only this crate should implement: a supertrait that is `pub` inside a private module. You can then add methods without a major release. Removing or changing a public method is still breaking. Say in the docs that the trait is sealed | rustc now explains a downstream impl attempt itself ("is a "sealed trait""). `#[diagnostic::on_unimplemented]` (1.78) on the public trait improves call-site errors. A `pub(crate)` supertrait gives the `private_bounds` warning, where it used to be error E0445. Seal a single method with a private-type parameter (all measured) | `unnameable_types` (rustc allow) fires on the `Sealed` trait, as intended |
| C-STRUCT-PRIVATE | A public field fixes the representation and rules out invariants. Use public fields only for passive, C-like data | Use `#[non_exhaustive]` (1.40) on public-field data structs and on enums that may grow. It blocks literals and `..base` construction (E0639) and requires `..` in patterns (E0638) and `_` in matches (E0004), outside the crate only (measured). Adding it later is breaking | `manual_non_exhaustive` (default); `exhaustive_structs`, `exhaustive_enums`, `partial_pub_fields` (restriction); `pub_underscore_fields` (pedantic) |
| C-NEWTYPE-HIDE | Wrap a compound return type in a newtype to promise less (`MyTransformResult<I>` rather than `Enumerate<Skip<I>>`) | `impl Trait` returns are shorter, but they leak `Send` and `Sync` from the body (measured), cannot be named by callers (a type alias of `impl Trait` is E0658), and cannot implement traits conditionally. Edition 2024 captures every in-scope lifetime (`writing-rust`) | — |
| C-STRUCT-BOUNDS | Do not repeat derivable or non-semantic bounds on a generic struct: `#[derive(Clone)] struct Good<T>`, not `struct Bad<T: Clone>`. Adding a bound later breaks callers; adding a derive does not. Never use `Clone`, `PartialEq`, `PartialOrd`, `Debug`, `Display`, `Default`, `Error`, `Serialize`, `Deserialize`, or `DeserializeOwned` as struct bounds | Bounds are required when a field uses an associated type (`Cow<'a, B: ToOwned + ?Sized>`), for `?Sized`, and when a `Drop` impl needs one (E0367 otherwise, measured). A derive bounds every type parameter, even one used only in `PhantomData`; write the impl by hand when that bound is wrong | — |

## Necessities

| ID | Rule | Changed since, or std departs | Lint |
|---|---|---|---|
| C-STABLE | A crate at 1.0 or later has only 1.0-or-later public dependencies: crates whose types appear in its API, including through `impl From<dep::Error>`. A private enum variant holding `dep::Error` is fine | `exported_private_dependencies` (warn) cannot fire on stable. Marking a dependency `public = true` makes Cargo print "ignoring `public` on dependency …, pass `-Zpublic-dependency`" (measured). Check by hand | rustc `exported_private_dependencies` (nightly only, in effect) |
| C-PERMISSIVE | License the crate `MIT OR Apache-2.0`, with `LICENSE-MIT` and `LICENSE-APACHE` files and the standard README "License" and "Contribution" sections. A single permissive licence also works; Apache-2.0 alone does not. Depend only on permissively licensed crates | Use the SPDX `OR`, not the legacy `MIT/Apache-2.0`. `cargo deny check licenses` checks dependencies | — |
