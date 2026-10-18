# Traits, generics and patterns

Exact rules from the Rust Reference (1.99) and the Book. Results marked *measured* were compiled on rustc 1.97.1.

## Contents

- [Dyn compatibility](#dyn-compatibility)
- [Trait objects and upcasting](#trait-objects-and-upcasting)
- [Method resolution traps](#method-resolution-traps)
- [Coherence and the orphan rule](#coherence-and-the-orphan-rule)
- [`impl Trait` in argument and return position](#impl-trait-in-argument-and-return-position)
- [Associated types, bounds and const generics](#associated-types-bounds-and-const-generics)
- [Derives](#derives)
- [Choosing a design](#choosing-a-design)
- [Pattern semantics](#pattern-semantics)

## Dyn compatibility

"Dyn compatible" is the current term for "object safe"; E0038 reads "the trait `X` is not dyn compatible" (*measured*). A trait is dyn compatible when:

- all supertraits are dyn compatible, and `Sized` is not a supertrait;
- it has **no associated constants** and **no generic associated types**;
- it has no supertrait mentioning `Self` as a type argument (`trait T: Super<Self>`);
- every associated function is either dispatchable or opts out with `where Self: Sized`.

A method is dispatchable when it has no type parameters (lifetime parameters are fine), uses `Self` only in the receiver, has a receiver of `&Self`, `&mut Self`, `Box<Self>`, `Rc<Self>`, `Arc<Self>` or `Pin<P>` of one of those, does not return an opaque type (so no `async fn` and no `-> impl Trait`), has no `where Self: Sized` bound and is not C-variadic.

`AsyncFn`, `AsyncFnMut` and `AsyncFnOnce` are not dyn compatible. A trait with `async fn` methods can still be used as `dyn` for its other methods if each `async fn` has `where Self: Sized` (*measured*).

## Trait objects and upcasting

- A trait object is one non-auto trait plus any auto traits (`Send`, `Sync`, `Unpin`, `UnwindSafe`, `RefUnwindSafe`) and at most one lifetime: `dyn Read + Send + 'a`. `dyn A + B` with two non-auto traits is an error; define `trait AB: A + B {}` with a blanket impl.
- `&'a (dyn Any + Send)` needs the parentheses after `&`.
- **Upcasting** `&dyn Sub` → `&dyn Super` is a coercion since 1.86. Auto traits can be dropped; one can be added only if it is a supertrait of the principal trait (`trait T: U + Send` lets `dyn T` become `dyn U + Send`). A hand-written `Deref<Target = dyn Super>` for `dyn Sub` is now shadowed by upcasting (`deref_into_dyn_supertrait`).
- `Box<dyn Any>::type_id()` returns the `TypeId` of the `Box` itself; call `(*boxed).type_id()` (*measured*: `false` versus `true` for a boxed `u8`).
- `fn f<T: Trait + ?Sized>(t: &T)` accepts everything `fn f(t: &dyn Trait)` does, plus concrete types with static dispatch. Without `?Sized`, `&dyn Trait` is rejected.
- An inherent method on a `dyn Trait` type with the same name as a trait method can never be called: method syntax errors and fully qualified syntax picks the trait method. Do not write one.

## Method resolution traps

For a receiver of type `T`, the compiler tries in order `T`, `&T`, `&mut T`, then dereferences and repeats (`*T`, `&*T`, …), finishing with an unsizing step for arrays. At each candidate type it looks at inherent methods first, then methods of traits in scope.

- An inherent method shadows a trait method of the same name. Adding an inherent method to a public type can silently change which method downstream code calls.
- Because `&T` is tried before `&mut T`, a trait method taking `&self` beats an inherent method taking `&mut self` on a by-value receiver.
- Lookup ignores mutability, lifetimes and `unsafe`. If the chosen method then cannot be called, that is an error; the compiler does not fall back to another candidate.
- Two traits in scope providing the method: "multiple applicable items in scope". `Type::method(&v)` is still ambiguous; write `<Type as Trait>::method(&v)`. An associated function without `self` on a trait needs the fully qualified form (E0790).
- Trait methods are callable only when the trait is in scope. `use Trait as _;` imports the methods without the name.
- `s.field()` is a method call. To call a closure stored in a field, write `(s.field)()`. A tuple field is the exception: `t.0()` calls it.

## Coherence and the orphan rule

- `impl Trait for Type` is allowed only if the trait or the type is local. Precisely: for `impl<P..> Trait<T1..Tn> for T0`, either the trait is local, or some `Ti` is local and no uncovered type parameter appears in `T0..Ti` before it.
- `&T`, `&mut T`, `Box<T>` and `Pin<T>` are fundamental: `Box<Local>` counts as local and does not cover `T`. `Vec<Local>` is **not** local.
- Adding a blanket impl of an existing trait, or an impl of a fundamental trait (`Fn*`, `Sized`), is a breaking change.
- The workaround for a foreign trait on a foreign type is a newtype, `struct Wrapper(Vec<String>);`. It has no runtime cost but none of the inner type's methods; delegate the ones you need (implementing `Deref` exposes all of them, which defeats the restriction).
- Implement `Display`, not `ToString`; the blanket `impl<T: Display> ToString for T` provides `to_string`. Likewise implement `From`, not `Into`.

## `impl Trait` in argument and return position

- **Argument position** (`fn f(x: impl Trait)`) is an anonymous generic parameter. Callers cannot turbofish it, so switching between `impl Trait` and a named generic changes the number of generic arguments and is a breaking change. Two `impl Trait` parameters may be different types; use one named generic to force the same type.
- **Return position** must resolve to one concrete type on every path. An `if`/`else` returning two closure types does not compile; return `Box<dyn Fn..>` or an enum.
- Two functions returning `impl Fn(i32) -> i32` have distinct opaque types: putting both in a `Vec` is E0308 "distinct uses of `impl Trait` result in different opaque types". Box them as `dyn`.
- `impl Trait` is not allowed in a `let` type, a field, or a type alias on stable (E0562 "`impl Trait` is not allowed in the type of variable bindings", *measured*).
- Return-position `impl Trait` in traits and `async fn` in traits are stable (1.75). They make the trait dyn incompatible, and a caller cannot add a `Send` bound to the returned future after the fact. To promise `Send`, write the method as `fn call(&self) -> impl Future<Output = u8> + Send;`.
- Lifetime capture and `use<..>`: see `edition-2024.md`.

## Associated types, bounds and const generics

- Use an associated type when each implementing type has exactly one natural choice (`Iterator::Item`); use a generic parameter when a type can implement the trait several ways (`From<T>`, `Add<Rhs>`).
- **Associated type bounds** (1.79): `fn f(it: impl Iterator<Item: Display>)` instead of a `where` clause. Since 1.92 the same associated item may carry several bounds, except in trait objects.
- **GAT required where-clauses:** if a method that uses `Self::Item<'a>` can prove `Self: 'a`, the GAT must declare it: `type Item<'a> where Self: 'a;`.
- `?Sized` relaxes only `Sized`; no other trait can be relaxed. Type parameters and associated types are `Sized` by default; `Self` in a trait is not.
- **Const generics.** Parameter types are limited to integers, `char` and `bool` on stable. An expression using a parameter (`[u8; N + 1]`) needs the unstable `generic_const_exprs`. A const argument that is not a literal or a single identifier needs braces: `f::<{ m::C }>()`. If a name is both a type and a const, `Foo<N>` resolves to the type; write `Foo<{ N }>`.
- **Inferred const arguments** (1.89): `let a: [u8; _] = [0; 3];`, `f::<_>()`. Not allowed inside braces (`{ _ }`) or in item signatures (`-> [u8; _]`).
- **`const { }` blocks** may use the surrounding generic parameters, and are guaranteed to be evaluated when executed: `const { assert!(size_of::<T>() > 0) }` is a compile-time check per instantiation. A free `const _: () = assert!(..);` is always evaluated, even inside an unused generic function.
- A `where` clause can bound any type (`String: PartialEq<T>`). A bound that is trivially false without involving parameters (`i32: Iterator`) is an error at the definition.
- Inside a function body, nested items cannot use the outer generic parameters (E0401); make the inner item generic itself.

## Derives

- Derivable std traits: `Debug`, `Clone`, `Copy`, `PartialEq`, `Eq`, `PartialOrd`, `Ord`, `Hash`, `Default`. `Display` is never derived.
- A derive bounds **every** type parameter, even one used only in `PhantomData<T>`: `#[derive(Clone)] struct Id<T>(u32, PhantomData<T>)` is `Clone` only when `T: Clone`. Write the impl by hand when that bound is wrong.
- Derived `PartialOrd`/`Ord` compare fields in declaration order; for enums, earlier variants are smaller.
- `#[derive(Default)]` on an enum needs `#[default]` on a unit variant.
- Never hand-implement `Eq::assert_receiver_is_total_eq`; write `impl Eq for T {}` (manual impls are deprecated since 1.95).
- A `Hash` impl must agree with `Eq`: equal values hash equally. Breaking this, or mutating a key inside a `HashMap`, `BTreeMap` or `BinaryHeap`, is a logic error (wrong results or panics), never UB.

## Choosing a design

For a public API, the `designing-rust-apis` skill carries the API Guidelines checklist (generics versus trait objects for callers, sealed traits, conversions, future-proofing).

- A closed set of types known at compile time → an `enum` and `match`. A set users can extend → a trait object. A homogeneous collection → a generic (`Screen<T: Draw>`); a heterogeneous one → `Vec<Box<dyn Draw>>`.
- Generics monomorphise (static dispatch, more code). Trait objects use a vtable (one copy of the code, no inlining).
- **Typestate** over a runtime state field: one type per state, transitions take `self` and return the next type, and methods exist only on the states where they are valid. Misuse becomes a compile error. The Book presents this as the Rust-idiomatic alternative to the object-oriented state pattern.
- Default trait methods can call required methods, but an override cannot call the default implementation of the same method.
- A `self: Box<Self>` receiver consumes the box; the method is callable only on a `Box<Self>`.

## Pattern semantics

- **Binding modes ("match ergonomics").** A non-reference pattern matched against a reference dereferences it and switches the default binding mode to `ref` (or `ref mut`). Edition 2024 forbids `mut`, `ref` and `&` under that default; see `edition-2024.md`.
- **A path pattern beats a binding.** A single identifier that names an in-scope constant, unit struct or unit variant is a path pattern. A misspelt or out-of-scope constant name silently becomes a catch-all binding. Patterns may not shadow constants, statics, const generics or constructors.
- **`_x` binds and therefore moves**; `_` does not. `if let Some(_s) = s` moves out of `s`; `if let Some(_) = s` does not.
- **Or-patterns have the lowest precedence.** `x @ A(..) | B(..)` is E0408 "variable `x` is not bound in all patterns" (*measured*); write `x @ (A(..) | B(..))`. A top-level or-pattern in `let` or a parameter needs parentheses: `let (A(x) | B(x)) = v;`. Every alternative must bind the same names with the same types and binding modes.
- **Guards.** A guard covers the whole or-pattern (`4 | 5 | 6 if y` means `(4 | 5 | 6) if y`) and may run once per alternative tried. Guards are not considered for exhaustiveness. A guard sees the bindings through a shared reference and cannot mutate them.
- **`if let` and let chains are not exhaustiveness-checked**; `match` is.
- **Ranges.** `a..b`, `a..=b`, `a..`, `..b`, `..=b` (exclusive forms since 1.80). Bounds are literals or paths to constants of integer, `char` or float type; the range must be non-empty; float bounds cannot be NaN. Inside a slice pattern, a half-open range needs parentheses: `[(1..), _]`. `...` is an error since 2021. `char` exhaustiveness knows the surrogate gap.
- **Constant patterns** require a type whose `PartialEq` is derived (structural equality); floats only if not NaN. A constant that depends on a generic parameter cannot be a pattern. A `c"…"` literal parses as a pattern but `&CStr` has no structural equality, so it is a type error.
- **`let … else`**: the `else` block must diverge. The initializer cannot end in `}` or be a lazy boolean (`a && b`); parenthesise it.
- **Rest and wildcards.** `..` may appear once per tuple or slice pattern (`(first, .., last)`); `name @ ..` binds a sub-slice (`[head, tail @ ..]`). Struct patterns must list every field or end in `..`. A tuple-struct can be matched by index: `Color { 0: r, .. }`.
- **Binding and testing at once:** `id @ 3..=7`.
- **Matching a `String` against literals:** `match s.as_str() { "a" => .. }`; `match` does not auto-deref the way `==` does.
- A union field in a pattern may be read even when another part of the pattern fails to match. Match the tag first, then read the field inside the arm.
- `matches!(v, Some(x) if x > 3)` for a boolean test; in tests prefer `assert_matches!` (1.96, `use std::assert_matches;`), which prints the value on failure.
