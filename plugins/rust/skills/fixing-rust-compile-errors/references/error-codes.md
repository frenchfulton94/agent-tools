# rustc error codes

Every code in the Rust 1.99 error index, as one-liners: what it means, then the usual fix. Wording in the most-hit table was measured on rustc 1.97.1. `rustc --explain EXXXX` prints the full page, including for retired codes.

## Contents

- [How to use this file](#how-to-use-this-file)
- [Most-hit codes, with their 1.97.1 wording](#most-hit-codes-with-their-1971-wording)
- [Errors with no code](#errors-with-no-code)
- Current codes by family
  1. [Ownership, moves, borrows, mutability](#1-ownership-moves-borrows-mutability)
  2. [Lifetimes and outlives](#2-lifetimes-and-outlives)
  3. [Trait bounds and method resolution](#3-trait-bounds-and-method-resolution)
  4. [Implementing a trait: signature conformance](#4-implementing-a-trait-signature-conformance)
  5. [Coherence, orphan rule, special traits](#5-coherence-orphan-rule-special-traits)
  6. [Trait objects](#6-trait-objects)
  7. [Associated items and qualified paths](#7-associated-items-and-qualified-paths)
  8. [Types, inference, operators, casts](#8-types-inference-operators-casts)
  9. [Name resolution, imports, modules](#9-name-resolution-imports-modules)
  10. [Privacy and visibility](#10-privacy-and-visibility)
  11. [Patterns and match](#11-patterns-and-match)
  12. [Struct and enum definition and construction](#12-struct-and-enum-definition-and-construction)
  13. [Generics, const generics, const evaluation](#13-generics-const-generics-const-evaluation)
  14. [async, await, closures](#14-async-await-closures)
  15. [unsafe, FFI, ABI, layout](#15-unsafe-ffi-abi-layout)
  16. [Attributes, lints, features](#16-attributes-lints-features)
  17. [Syntax, literals, control flow, entry point](#17-syntax-literals-control-flow-entry-point)
  18. [Crate loading and toolchain mismatch](#18-crate-loading-and-toolchain-mismatch)
  19. [Nightly-only or std-internal](#19-nightly-only-or-std-internal)
- [Retired codes and where each went](#retired-codes-and-where-each-went)

## How to use this file

- ★ marks the codes most often hit in ordinary stable code.
- The 1.99 index has 518 pages: 385 current codes, 130 retired, and 5 internal to the compiler (E0208, E0640, E0711, E0717, E0789; never emitted for normal code).
- rustc 1.97.1 still treats as live 7 codes that the 1.99 docs list as retired: **E0232, E0517, E0537, E0552, E0693, E0718, E0734** (measured: `rustc --explain` on all 518 codes; E0517, E0552 and E0693 also reproduced). Accept either the old or the new code for those.
- A code you remember may now be retired and folded into another. Check [the retired list](#retired-codes-and-where-each-went) before you conclude that the compiler is wrong.

## Most-hit codes, with their 1.97.1 wording

| Code | Headline on rustc 1.97.1 | First move |
|---|---|---|
| E0382★ | borrow of moved value: `s` · use of moved value: `s` | Borrow instead of moving, clone if cheap, or restructure. In a loop: "value moved here, in previous iteration of loop" |
| E0499★ | cannot borrow `v` as mutable more than once at a time | Split the borrow: fields, `split_at_mut`, `get_disjoint_mut` |
| E0502★ | cannot borrow `v` as mutable because it is also borrowed as immutable | End the shared borrow first: copy the value out, reorder |
| E0505★ | cannot move out of `s` because it is borrowed | Move after the borrow's last use |
| E0506★ | cannot assign to `x` because it is borrowed | Assign after the borrow's last use |
| E0507★ | cannot move out of `s.name` which is behind a shared reference (also "…a mutable reference", "…index of `Vec<String>`", "…`self.st` as enum variant `A`…") | `mem::take`, `Option::take`, `mem::replace`, borrow, or clone |
| E0596★ | cannot borrow `v` as mutable, as it is not declared as mutable | `let mut`; for a closure that mutates, `let mut c = …` |
| E0594★ | cannot assign to `p.x`, which is behind a `&` reference | Take `&mut`, or use interior mutability |
| E0384★ | cannot assign twice to immutable variable `x` | `let mut`, or shadow |
| E0597★ | `x` does not live long enough | Move the owner to an outer scope, or store owned data |
| E0716★ | temporary value dropped while borrowed | Bind the temporary with `let` first (the compiler's help shows this) |
| E0515★ | cannot return reference to local variable `s` · cannot return value referencing local variable `v` | Return owned data (`String`, `into_iter()`) |
| E0373★ | closure may outlive the current function, but it borrows `v`, which is owned by the current function | `move`, or `std::thread::scope` to borrow |
| E0521★ | borrowed data escapes outside of function · …outside of closure | Owned or `'static` data for `thread::spawn`; or scoped threads |
| E0525 | expected a closure that implements the `Fn` trait, but this closure only implements `FnOnce` | Stop moving captures out, or loosen the bound to `FnOnce` |
| E0308★ | mismatched types | Read the expected/found pair; check for a trailing `;` on the tail expression |
| E0282★ | type annotations needed for `Vec<_>` | Annotate the binding or turbofish |
| E0283★ | type annotations needed (note: "the type must implement `FromIterator<i32>`") | Several impls fit (`collect`, `into`): name the target type |
| E0284 | type annotations needed (note: "cannot satisfy `<_ as FromStr>::Err == _`") | `let n: i32 = s.parse()?` or `parse::<i32>()` |
| E0277★ | `S` doesn't implement `Debug` · the trait bound `X: Y` is not satisfied · `Rc<i32>` cannot be sent between threads safely · the `?` operator can only be used in a function that returns `Result` or `Option` … | Implement or derive the trait, or add the bound to the generic |
| E0599★ | no method named `go` found for struct `S` in the current scope · no associated function or constant named `new` found for struct `S` | Import the trait (help: "trait `T` which provides `go` is implemented but not in scope"), satisfy the impl's bounds |
| E0609★ | no field `b` on type `S` | Fix the name, or unwrap the `Option`/`Box` first |
| E0061 | this function takes 2 arguments but 1 argument was supplied | Rust has no default or optional arguments |
| E0369 | cannot add `&str` to `&str` | Owned left side: `a.to_owned() + b`, or `format!` |
| E0106★ | missing lifetime specifier | Name the lifetime and tie the output to the one input it borrows from |
| E0621★ | explicit lifetime required in the type of `y` | Give `y` the same named lifetime as the return |
| E0310★ | the parameter type `T` may not live long enough | Add `T: 'static` (the help shows where) |
| E0700★ | hidden type for `impl Sized` captures lifetime that does not appear in bounds | Edition ≤2021 only, unless a `use<..>` list omits the lifetime: add `+ use<'x>` |
| E0038★ | the trait `T` is not dyn compatible | `where Self: Sized` on the offending method. An `async fn` in the trait also causes it |
| E0046★ | not all trait items implemented, missing: `a` | Add the items |
| E0053★ | method `a` has an incompatible type for trait | Copy the trait's signature exactly, receiver included |
| E0117★ | only traits defined in the current crate can be implemented for types defined outside of the crate | Newtype, or a local trait |
| E0119★ | conflicting implementations of trait `T` for type `S` | Remove the overlap; narrow the blanket impl |
| E0271★ | expected `IntoIter<&str>` to be an iterator that yields `u32`, but it yields `&str` | Make the associated type agree |
| E0746★ | return type cannot be a trait object without pointer indirection | `impl Trait`, `Box<dyn Trait>`, or an enum |
| E0425★ | cannot find value `y` in this scope · cannot find type `Foo` in this scope | Spell, declare, or `use` it. Unknown *type* names are E0425 now; E0412 is retired |
| E0433★ | cannot find type `HashMap` in this scope · cannot find module or crate `hosting` in this scope | `use` the path; add the dependency. "failed to resolve: use of undeclared type" is the old wording |
| E0432★ | unresolved import `std::collections::HashMapp` | Fix the path; `crate::`/`super::`/`self::`; add the dependency |
| E0603★ | function `g` is private | `pub`/`pub(crate)`, or a public re-export |
| E0616 | field `x` of struct `S` is private | Getter or `pub` field |
| E0624 | method `p` is private | `pub`. On `Option<String>`, `o.len()` also reports "method `len` is private" (a private std method): the real fix is to unwrap first, as the help line "the method `len` exists on the type `String`" says |
| E0004★ | non-exhaustive patterns: `None` not covered | Add the arm, or `_` |
| E0005★ | refutable pattern in local binding | `let … else`, `if let`, or `match` |
| E0107★ | enum takes 1 generic argument but 2 generic arguments were supplied | Supply exactly the declared count |
| E0015★ | cannot call non-const function `g` in constants | `const fn` callee, or `LazyLock` |
| E0728★ | `await` is only allowed inside `async` functions and blocks | Make the enclosing fn or closure `async` |
| E0133★ | call to unsafe function `g` is unsafe and requires unsafe block | `unsafe {}`. In edition 2024 it also appears as a *warning* inside `unsafe fn` bodies (`unsafe_op_in_unsafe_fn`) |
| E0658★ | use of unstable library feature `str_as_str` | Use a stable alternative. Often the code needs a newer toolchain, not nightly |
| E0423 | expected function, found macro `println` | `println!` (also `Foo()` on a braced struct, `a.b` for a module path) |

## Errors with no code

Several common errors carry no code (`"code": null` in JSON), so a filter on `.code.code` misses them:

- `future cannot be sent between threads safely`: a non-`Send` value (`Rc`, `std::sync::MutexGuard`) lives across an `.await` in a future passed to a `Send`-bound spawn. Measured on 1.97.1: `drop(guard)` before the `.await` does **not** fix it; ending the guard's scope with a block does.
- Edition 2024: `extern blocks must be unsafe`, `unsafe attribute used without unsafe` (`#[no_mangle]` → `#[unsafe(no_mangle)]`).
- Attribute on the wrong item: `` `#[inline]` attribute cannot be used on structs `` (was E0518).
- Parse errors: `expected expression, found …`, `` `..` can only be used once per tuple pattern ``, and `` cannot find macro `x` in this scope ``.
- `functions using #[should_panic] must return ()`.

## 1. Ownership, moves, borrows, mutability

Patterns and measured fixes are in `borrow-checker-patterns.md`.

- E0040 — explicit `x.drop()` call — `drop(x)`.
- E0161 — moving an unsized value (by-value `self` on `Box<dyn Trait>`) — `&self`, or `self: Box<Self>`.
- E0373★ — closure or async block may outlive borrowed locals — `move`/`async move`; `thread::scope` to borrow. Joining the thread does not satisfy the checker.
- E0381 — use of a possibly-uninitialized variable — initialize on every path.
- E0382★ — use after move (also moved in an earlier loop iteration, into a closure, by `for x in v`) — borrow, clone, `Copy`, `Rc`/`Arc`.
- E0384★ — assign twice to an immutable binding — `let mut` or shadow.
- E0499★ — two simultaneous `&mut` — sequence them, split borrows, indices.
- E0500 — closure needs unique access to an already-borrowed variable — create the closure after the borrow ends.
- E0501 — variable used while a closure holding a unique borrow is live — call or drop the closure first. (1.97.1 often reports this case as E0502 instead.)
- E0502★ — `&mut` while `&` is live, or the reverse — end the first borrow, copy out, reorder.
- E0503 — value used while mutably borrowed — finish with the `&mut` first.
- E0505★ — move while borrowed — move after the borrow's last use.
- E0506★ — assign to a borrowed place — end the borrow first.
- E0507★ — move out of a borrow (`&`, `&mut`, index, `RefCell::borrow()`, `Rc`, an `Fn` capture) — borrow, clone, `Option::take`, `mem::take`/`replace`.
- E0508 — move out of an array by index — borrow, clone, destructure, or `into_iter()`.
- E0509 — move a field out of a type that implements `Drop` — `mem::take` on the field, or `Option` + `take()`.
- E0510 — matched place assigned or `&mut`-borrowed inside a match guard — move the mutation into the arm body.
- E0515★ — return a reference to a local or temporary — return owned data.
- E0521★ — borrowed data escapes the closure or function — drop the closure-parameter type annotation (`|el: &str|` introduces a fresh lifetime); owned data for `spawn`.
- E0524 — one variable needing unique access in two live closures — run them in turn, or `Rc<RefCell>`.
- E0525 — closure is `FnOnce`/`FnMut` where `Fn` is required — stop moving or mutating the capture, or loosen the bound.
- E0594★ — assign through `&` or to a non-`mut` binding — `let mut`, `&mut`, `FnMut`, interior mutability.
- E0596★ — `&mut` borrow of a non-`mut` binding, including calling a mutating closure — add `mut`.
- E0597★ — borrowed value does not live long enough — move the owner outward or store owned data.
- E0713 — borrow of data owned by a `Drop` type outlives that value — take `&'a mut S<'a>`, or drop the `Drop` impl.
- E0716★ — temporary dropped while borrowed — bind with `let`. `let r = &temp();` extends the temporary; `let r = f(&temp());` does not.

## 2. Lifetimes and outlives

- E0106★ — missing lifetime in a type or failed elision (an elided output needs exactly one input lifetime, or `&self`) — name it. The help puts `'a` on every parameter; tie the output only to the input it really borrows from.
- E0195 — impl method's lifetime params or bounds differ from the trait — copy them.
- E0212 — associated type of a trait with an uninferred HRTB lifetime — `<I as Foo<&'a isize>>::A`.
- E0226 — more than one lifetime bound on a trait object — keep one.
- E0227 — no unique region from derived object bounds — add `+ 'c` with `'c: 'a + 'b`.
- E0228 — object lifetime default cannot be deduced — write `dyn Trait + 'a`.
- E0261 — undeclared lifetime — declare it on the fn, struct, or `impl<'a>`.
- E0262 — invalid lifetime parameter name (`'static`, `'_`) — rename.
- E0309 — generic type missing `T: 'a` that a field needs — add `where T: 'a`.
- E0310★ — `T` may not live long enough (`'static` required by `Box<dyn Any>`, `spawn`) — `T: 'static`.
- E0311 — outlives bound between an elided lifetime and a generic — name the lifetime, add `T: 'a`.
- E0316 — nested `for<>` in one where-clause — merge into `for<'a, 'b>`.
- E0478 — lifetime bound not satisfied — declare `'b: 'a` on the type.
- E0491 — `&'a Foo<'b>` without `'b: 'a` — add it.
- E0496 — inner lifetime shadows an outer one — rename.
- E0581 — fn-pointer lifetime only in the return type — use it in an argument, or `'static`.
- E0582 — HRTB lifetime only in an associated-type binding or return — use it in an input.
- E0621★ — signature lifetimes do not match the data flow — give the parameter the return's lifetime.
- E0623 — value of one lifetime flows into an unrelated one — add `'a: 'b`, or use one lifetime.
- E0637 — `'_` declared as a parameter, or `&T` without a lifetime where elision is not allowed (`Item = &u32`) — named lifetime or `for<'a>`.
- E0657 — `impl Trait` capturing a higher-ranked lifetime — restructure with a named type.
- E0700★ — hidden type captures a lifetime missing from the bounds — edition ≤2021 only (2024 captures every in-scope lifetime), or a `use<..>` list that omits it — add `+ use<'x>`.
- E0726 — elided lifetime in a path type in an `async fn` parameter — `Content<'_>`.
- E0747 — generic arguments out of order — lifetimes first.
- E0794 — explicit argument for a late-bound lifetime — remove it.
- E0799 — `use<..>` lists something other than a lifetime, type, or const param — remove it.
- E0800 — `use<T>` names a parameter not in scope — fix the name.
- E0803 — trait impl returns a reference not tied to `self` — thread the lifetime through the trait.

## 3. Trait bounds and method resolution

- E0034 — two traits provide the same method name — `<Type as Trait>::f(&x)`.
- E0275 — overflow evaluating a requirement (self-referential bounds) — simplify the bound; sometimes `#![recursion_limit]`.
- E0276 — impl method adds bounds the trait lacks — remove them, or add to the trait.
- E0277★ — trait bound not satisfied — implement it, or declare the bound on the generic. A generic body is checked against its signature only, so every bound it uses must be declared. Bounds on a struct are not implied for fns taking it (only lifetime bounds are). Read the `required for X to implement Y` notes; the last one names the real missing impl.
- E0271★ — associated-type mismatch (`T: Trait<Assoc = u32>` given `&str`; most often an iterator's `Item`) — make the bound and the impl agree.
- E0283★ — several impls fit (`collect`, `into`, `sum`) — annotate or turbofish.
- E0391 — query cycle (supertraits `A: B`, `B: A`) — break the cycle.
- E0404 — non-trait used as a bound (struct, or a type alias of a trait) — use a real trait or a supertrait with a blanket impl.
- E0405 — trait not in scope — import it or fix the spelling.
- E0407 — impl defines a method the trait lacks — move it to an inherent impl.
- E0599★ — no method or associated item — import the trait, satisfy the impl's bounds (read "the following trait bounds were not satisfied"), or unwrap the `Option`/`Result`.
- E0790 — trait associated fn without `self` called through the trait — `<Type as Trait>::f()`.

## 4. Implementing a trait: signature conformance

- E0046★ — missing required items — add them.
- E0049 — wrong number of generic params on an impl method — match the trait.
- E0050 — wrong number of fn params — match the trait.
- E0053★ — param types or receiver mutability differ — copy the trait signature.
- E0185 / E0186 — impl has a receiver where the trait has none, or the reverse — match.
- E0201 — duplicate associated item in one impl — rename.
- E0323 / E0324 / E0325 — impl item is a different kind (const, method, type) than the trait's — match.
- E0326 — associated const has a different type than the trait's — match.
- E0366 — `Drop` for one instantiation (`impl Drop for Foo<u32>`) — be as generic as the type.
- E0367 — `Drop` impl with bounds the type lacks — put the bounds on the type.
- E0379 — `const fn` in a trait or trait impl — not allowed; use an associated `const`.
- E0437 / E0438 — impl defines an associated type or const the trait lacks — remove it.
- E0592 — same method name in two inherent impls of one type — rename.
- E0643 — trait uses `impl Trait` argument, impl uses a generic (or the reverse) — use the same form.
- E0120 — `Drop` on a trait object or reference — implement on a wrapper.
- E0207 — impl parameter not constrained by the self type, trait params, or an associated-type binding — move it to the method or add `PhantomData<T>`.

## 5. Coherence, orphan rule, special traits

- E0116 — inherent impl on a foreign type, also through a `type` alias — extension trait or newtype.
- E0117★ — orphan rule: foreign trait for foreign types — newtype, or local trait.
- E0118 — inherent impl on a non-nominal type (`impl<T> T`) — trait with blanket impl.
- E0119★ — overlapping impls — remove the overlap (specialization is unstable).
- E0184 — `Copy` and `Drop` on one type — not allowed.
- E0197 / E0198 / E0199 — `unsafe` on an inherent impl, a negative impl, or a safe trait's impl — remove `unsafe`.
- E0200 — safe impl of an `unsafe trait` (`Send`, `Sync`) — `unsafe impl`.
- E0204 — `Copy` with a non-`Copy` field (`&mut T` is never `Copy`; `&T` always is) — use `Clone`.
- E0206 — `impl Copy` for a non-ADT — structs, enums, unions only.
- E0210 — orphan rule, uncovered type parameter (`impl<T> ForeignTrait for T`); order of trait params matters — wrap in a local type.
- E0321 — auto-trait impl on a non-local or non-ADT type — local structs and enums only.
- E0322 — explicit impl of a built-in trait (`Sized`) — not allowed.
- E0328 — manual `Unsize` impl — not allowed.
- E0371 — impl of a supertrait for `dyn Subtrait` — redundant; remove.
- E0390 — inherent impl on a primitive or reference type — use a trait.
- E0751 — positive and negative impl for one type — remove one.

## 6. Trait objects

- E0033 — pattern derefs a trait object — call methods through the pointer.
- E0038★ — trait not dyn-compatible ("object safe" is the old term). Causes: a method returns or takes `Self`, a generic method, a method without receiver, an `async fn`, associated consts, `Self: Sized` on the trait, `trait T: Super<Self>`. Fix: `where Self: Sized` on the method (then it is not callable on `dyn`), `Box<dyn Other>` for generics, a getter for a const.
- E0178 — `+` in an ambiguous type position (`&'a Foo + 'a`) — `&'a (dyn Foo + 'a)`.
- E0191 — `dyn Trait` without its associated types — `dyn Trait<Item = i32>`.
- E0224 — trait object with no trait — add one.
- E0225 — more than one non-auto trait (`dyn Read + Write`) — supertrait `trait RW: Read + Write {}` with blanket impl. Auto traits (`+ Send + Sync`) are fine.
- E0393 — `dyn A` where `A<T = Self>` — `dyn A<i32>`.
- E0719 — associated type specified twice — remove one.
- E0746★ — `dyn Trait` as a return type — `impl Trait`, `Box<dyn Trait>`, or an enum.
- E0782 — trait object without `dyn` — `dyn Trait`. Hard error since edition 2021.
- E0804 — pointer cast adds an auto trait to `dyn` (`as *const (dyn Any + Send)`) — not allowed with `as`. Emitted on 1.97.1.

## 7. Associated items and qualified paths

- E0220 — associated type not in the trait — declare it or fix the name.
- E0221 — subtrait and supertrait both declare `A` — `<Self as Bar>::A`.
- E0222 — constraining an associated type that is ambiguous across supertraits — new type param with separate where-clauses.
- E0223 — ambiguous `Struct::X` — `<Struct as Trait>::X` (inherent associated types are unstable).
- E0229 — `Assoc = T` constraint inside a qualified path — move it to a bound.
- E0411 — `Self` outside an impl or trait — use the concrete type.
- E0424 — `self` in an associated fn without a receiver — add `&self`, or call `Self::f()`.
- E0575 — non-type where an associated type is expected — use an associated *type*.
- E0576 — associated item not found in the type or trait — use one that exists.

## 8. Types, inference, operators, casts

- E0054 — `x as bool` — `x != 0`.
- E0055 — auto-deref hit the recursion limit — break the `Deref` loop.
- E0057 — closure called with the wrong number of arguments — match its arity.
- E0061 — wrong number of fn arguments — pass exactly N; Rust has no defaults.
- E0067 / E0070 — `+=` or `=` to a non-place — assign to a variable, field, index, or `*deref`.
- E0069 — `return;` in a fn returning a value — return one.
- E0282★ — type annotations needed — annotate or turbofish (`collect::<Vec<_>>()`).
- E0284 — return-type-generic result cannot be inferred (`parse()`, `into()` in arithmetic) — bind with a concrete type. The Book's `"42".parse()` example is E0284, not E0282.
- E0308★ — mismatched types: wrong argument, non-`bool` condition (no truthiness), trailing `;` making the tail `()` (label: "implicitly returns `()`"), `if` without `else`, `&String` vs `&str`, `Option<T>` vs `T`, two `impl Trait`s being distinct opaque types, a fn item vs a fn pointer.
- E0317 — `if` without `else` where a value is needed — add `else`.
- E0368 — compound op unsupported (implementing `Add` does not give `+=`) — implement `AddAssign`.
- E0369★ — binary op unsupported (`&str + &str`, `==` without `PartialEq`, `>` on unbounded `T`) — derive or implement the op trait; add `T: PartialOrd`.
- E0593 — closure arity differs from the `Fn` bound — match it; tuples need `|(a, b)|`.
- E0600 — `!`/`-` on a type without `Not`/`Neg` — implement it.
- E0604 — `as char` from anything but `u8` — `char::from_u32`.
- E0605 — non-primitive cast (`&str as String`) — `From`/`Into`/`TryFrom`.
- E0606 — incompatible cast (`&u8 as u32`) — deref first.
- E0607 — thin to wide pointer cast — `ptr::slice_from_raw_parts`.
- E0608 — indexing a type without `Index` — `.0`/`.field`, or implement `Index`.
- E0609★ — no such field — fix the name, or reach through the wrapper.
- E0610 — field access on a primitive — wrong type.
- E0614 — `*x` on a non-`Deref` type — remove the `*`.
- E0615 — method used like a field — add `()`.
- E0618 — calling a non-function (unit variant, integer) — remove `()`.
- E0620 — cast to an unsized type — cast to a reference.
- E0631 — closure parameter type differs from the `Fn` bound — fix or remove the annotation.
- E0641 — cast to or from a pointer of unknown pointee (`0 as *const _`) — name the pointee type.
- E0689 — method on an ambiguous numeric literal (`2.0.neg()`) — suffix it: `2.0_f32`.

## 9. Name resolution, imports, modules

- E0252 — two imports bind the same name — `use a::x as y`.
- E0254 / E0259 / E0260 — import or item collides with an `extern crate` name — rename one.
- E0255 — import collides with a local item — alias the import.
- E0401 — inner item uses the outer fn's generics — make the inner item generic, or use a closure.
- E0403 — same generic name declared twice (including a method shadowing the impl's `T`) — rename.
- E0415 / E0416 — duplicate parameter name, or the same name bound twice in one pattern — rename.
- E0422 — struct-literal syntax on an unknown name — define or import it.
- E0423 — name in the wrong namespace (`println("")`, `Foo()` on a braced struct, `a.b` for a path) — fix the syntax.
- E0425★ — unresolved value **or type** name (`fn f(x: T)` without `<T>` is E0425 on 1.97.1) — declare, import, or make `pub`.
- E0426 — undeclared loop label — declare it.
- E0428 — name defined twice in one namespace — rename.
- E0432★ — unresolved import. Since 2018, `use` paths are relative to the current module unless they start with a crate name, `crate::`, `self::`, or `super::`. In a workspace, each member declares its own dependencies.
- E0433★ — unresolved path prefix: `HashMap::new()` without `use` reports "cannot find type `HashMap` in this scope"; an unknown module reports "cannot find module or crate `x` in this scope" — `use` it, or add the dependency.
- E0434 — inner `fn` uses a local of the outer fn — closure, or `const`.
- E0531 — unknown tuple struct or variant in a pattern — import it.
- E0573 — non-type where a type is expected (a variant as a return type) — use the enum type.
- E0574 — non-struct where a struct is expected — use the struct or variant path.
- E0583 — `mod foo;` with no `foo.rs` or `foo/mod.rs` — create it.
- E0659 — ambiguous name from two glob imports — import explicitly.
- E0754 — non-ASCII identifier where disallowed (out-of-line `mod`, `#[no_mangle]`) — ASCII or `#[path]`.
- E0761 — both `foo.rs` and `foo/mod.rs` exist — delete one.

## 10. Privacy and visibility

- E0364 / E0365 — `pub use` of a private item or module — make it `pub`.
- E0446 — private type in a public associated type — make it `pub`. Private items in public *bounds* are now the `private_bounds`/`private_interfaces` warnings, not errors.
- E0449 — visibility qualifier where not allowed (enum variants, trait items, trait impl items) — remove it.
- E0451 — struct literal sets private fields — constructor.
- E0577 — `pub(in path)` where the path is not a module — name a module.
- E0603★ — private item used outside its module — `pub`, `pub(crate)`, or a re-export.
- E0616 — private field — getter or `pub`.
- E0624 — private method — `pub`. See the most-hit table for the misleading `Option` case.
- E0639 — constructing a foreign `#[non_exhaustive]` struct with a literal — use its constructor.
- E0704 — malformed `pub(foo)` — `pub(in crate::foo)`, `pub(crate)`, `pub(super)`, `pub(self)`.
- E0742 — `pub(in path)` naming a non-ancestor — name an ancestor.

## 11. Patterns and match

- E0004★ — non-exhaustive `match` — add arms or `_`.
- E0005★ — refutable pattern in `let` — `let … else`, `if let`, `match`.
- E0023 — wrong number of fields in a tuple-variant pattern — one per field, or `..`.
- E0025 / E0026 / E0027 — field bound twice, nonexistent field, or fields omitted in a struct pattern — fix; `..` for the rest.
- E0029 — range pattern on a non-number (`"a"..="z"`) — use a guard.
- E0030 / E0579 — empty range pattern (`1000..=5`, `5..5`) — fix the bounds.
- E0158 — generic param, generic associated const, or `static` used as a pattern — guard `x if x == A::X`.
- E0164 — pattern uses an associated fn (`A::new()`) — match variants only.
- E0170 — a binding named like a variant (`GET =>` binds a new variable) — `Method::GET`. Reported as an error with code E0170 by the deny-by-default lint `bindings_with_variant_name`.
- E0408 / E0409 — or-pattern alternatives bind different names or modes — bind the same in each.
- E0527 / E0528 / E0529 — slice pattern length wrong, too long, or on a non-slice — match the length or add `..`.
- E0530 — binding shadows a variant, struct, `static`, or associated const — rename, or add `(_)`.
- E0532 / E0533 / E0769 — pattern kind differs from the item (unit vs tuple vs struct variant, method path) — use the right form.
- E0638 — exhaustive match of a foreign `#[non_exhaustive]` enum or struct — `_ =>` or `..`.
- E0730 — matching an array of generic length — match a slice.

## 12. Struct and enum definition and construction

- E0062 / E0063 — field given twice, or missing — supply each once; `..Default::default()`.
- E0071 — struct-literal syntax on a non-struct alias — use the right initializer.
- E0072 — recursive type of infinite size — `Box`, `Rc`, or `&`.
- E0081 — duplicate discriminant (implicit ones count up from the previous) — renumber.
- E0084 — `#[repr(int)]` on a zero-variant enum — add variants or drop the repr.
- E0091 / E0392 — unused type or lifetime parameter — remove it, or `PhantomData`.
- E0124 — duplicate field name — rename.
- E0320 — drop-check overflow from polymorphic recursion — remove the recursion.
- E0370 — implicit discriminant overflowed the repr — set it explicitly.
- E0436 — `..base` on a non-struct — destructure instead.
- E0559 / E0560 — unknown field in a variant or struct literal — fix the name.
- E0665 — `#[derive(Default)]` on an enum without `#[default]` — mark a unit variant `#[default]`.
- E0732 — explicit discriminants on a data-carrying enum without `#[repr(int)]` — add `#[repr(u8)]`.
- E0784 — union literal with other than one field — exactly one.
- E0797 — struct update `..` without a base — `..base` (bare `..` is the nightly default-field-values feature).

## 13. Generics, const generics, const evaluation

- E0015★ — non-`const` fn in a const or static — `const fn`, or `LazyLock`.
- E0080 — const evaluation failed (overflow, divide by zero, a panic in const). In a generic, it can appear only at `cargo build`, never at `cargo check` (measured: a `const { assert!(N > 0) }`-style associated const).
- E0107★ — wrong number of generic arguments — match the declaration.
- E0109 — generic arguments on a type that takes none — remove them.
- E0121 — `_` in an item signature — write the type.
- E0128 — a default names a later parameter — reorder.
- E0203 — duplicate relaxed bound — keep one.
- E0214 — `Vec(&str)` — angle brackets.
- E0435 — runtime value in a const context (`[u8; n]` with `let n`) — `const` or a const generic.
- E0492 — `&` to a `const` with interior mutability — use a `static`.
- E0493 — a value with `Drop` dropped during const evaluation — let it escape into the final value.
- E0562 — `impl Trait` outside argument and return position (in `let` or a field) — concrete type, generic, or `Box<dyn>`.
- E0572 — `return` outside a fn — remove it.
- E0666 — nested `impl Trait` in generic arguments — named generic.
- E0720 — recursive opaque `impl Trait` — concrete or boxed type.
- E0735 — `Self` in a type-parameter default — not allowed.
- E0741 — const generic of a non-structural type — stable allows integers, `char`, `bool`.
- E0764 — `&mut` in the final value of a const or static — `static` with interior mutability.
- E0770 — const param type depends on a generic — concrete type.

## 14. async, await, closures

- E0267 / E0268 — `break`/`continue` inside a closure or async block but not a loop, or outside any loop — `return` from the closure.
- E0644 — closure refers to its own type — use a fn or `&dyn Fn`.
- E0670 — `async fn` in edition 2015 — edition 2018+.
- E0697 — `static` closure outside coroutines — remove `static`.
- E0728★ — `.await` outside async (including a non-async closure inside an async fn) — `async` fn, block, or closure (`async || {}`, stable 1.85).
- E0733 — recursive `async fn` — `Box::pin(f(n - 1)).await` inside it.
- E0752 — `async fn main` with no runtime — `#[tokio::main]` or a `block_on`.
- E0767 — label used across a closure, async block, or fn — restructure.

## 15. unsafe, FFI, ABI, layout

- E0044 — generic params on a foreign fn — one declaration per type.
- E0045 — C-variadic `...` on a non-C ABI — `extern "C"` only.
- E0060 — variadic fn called with fewer than its fixed params — pass them.
- E0130 — pattern as a parameter in a foreign fn — plain name.
- E0133★ — unsafe op outside `unsafe {}` — wrap it. Inside an `unsafe fn` body, 2024 warns (lint `unsafe_op_in_unsafe_fn`, still code E0133); ≤2021 is silent.
- E0472 — `asm!` unsupported on the target (E0658 instead means support is in progress).
- E0512 — `transmute` between differently-sized or generically-sized types — same sizes, or `ptr::read`.
- E0566 / E0587 / E0588 / E0589 / E0634 — conflicting or invalid repr hints (`packed` with `align`, `align` not a power of two) — one valid hint.
- E0570 / E0703 — ABI unsupported on the target, or unknown ABI string — supported ABI, `cfg`-gated.
- E0591 — transmuting a fn item (zero-sized) to a fn pointer — cast with `as fn(..)` first.
- E0617 — un-promoted type to a C variadic — `f32 as c_double`, small ints `as c_int`.
- E0690 / E0692 / E0731 — `repr(transparent)` with more than one non-ZST field, extra hints, or an enum not of one variant — `PhantomData` for extra fields.
- E0736 / E0787 — `#[unsafe(naked)]` with incompatible attributes or a body other than one `naked_asm!` — fix.
- E0737 — `#[track_caller]` on a non-Rust ABI fn — remove.
- E0740 — union field with `Drop` — `ManuallyDrop<T>`.
- E0743 — `...` nested inside a type — only bare as the last parameter.
- E0745 — `&raw const` of a temporary — bind to a local first.
- E0793 — reference to an unaligned field of a `#[repr(packed)]` struct, including implicitly in `println!("{}", s.f)` — `{ s.f }` copies it; or `&raw const s.f` + `read_unaligned()`. `unsafe` does not help.
- E0454 / E0459 / E0455 — `#[link]` with empty or missing `name`, or a kind the target lacks (`framework` is Apple-only; gate with `cfg_attr(target_os = "macos", …)`).

## 16. Attributes, lints, features

- E0452 — malformed lint attribute (`allow(foo = "")`) — lint paths only, plus `reason = "…"`.
- E0453 — `allow` inside a `forbid` scope for that lint (attribute or `-F`) — use `deny`, or fix the code. `forbid` on a *group* only warns (`forbidden_lint_groups`) and the inner `allow` wins (measured).
- E0538 — attribute key repeated — keep one.
- E0539 — malformed attribute input: list vs `key = value` vs keyword (`#[inline(maybe)]`, `#[deprecated(note)]`) — use the documented form. Absorbs E0535, E0551, and (after 1.97) E0552 and E0693.
- E0554 — `#![feature]` on stable — nightly, or avoid it.
- E0557 / E0635 — removed or unknown feature name — delete it.
- E0565 — literal where an identifier is expected (`#[repr("C")]`) — `#[repr(C)]`.
- E0602 — unknown lint on the command line — fix the name. An unknown lint in an attribute is the `unknown_lints` warning instead.
- E0648 — NUL in `#[export_name]` — remove it.
- E0658★ — unstable feature or library API — stable alternative or newer toolchain.
- E0710 — unknown tool in a scoped lint (`clipy::x`) — `clippy::`, `rustdoc::`.
- E0725 — feature not in `-Z allow-features` — remove.
- E0774 / E0777 — `derive` on a non-ADT, or a string in `derive("Clone")` — fix.
- E0780 — `#[doc(inline)]` on `pub use x as _` — remove.
- E0805 — wrong number of attribute arguments (`#[inline()]`) — `#[inline]` or one argument. Emitted on 1.97.1.
- E0468 / E0469 — `#[macro_use] extern crate` outside the crate root, or naming an unexported macro — move it or fix the name.

## 17. Syntax, literals, control flow, entry point

- E0131 / E0646 / E0580 — `main` with generics, a where-clause, or arguments — `fn main()`; read `std::env::args()`.
- E0561 — pattern as a parameter in a fn-pointer type — plain name.
- E0571 — `break value` in `for`/`while` — only `loop` or a labeled block yields a value.
- E0584 / E0585 — doc comment attached to nothing — move it or use `//`.
- E0586 — `1..=` with no end — `1..`.
- E0590 / E0695 / E0696 — unlabeled `break`/`continue` across a `while` condition or labeled block, or `continue` to a block — label it.
- E0601 — no `main` in a binary crate: "`main` function not found in crate `x`" — add it, or make it a library.
- E0642 — patterns as parameters in a bodiless trait method — single name.
- E0748 — raw-string `#` count mismatch — match them.
- E0753 — `//!` after items — only at the top; use `///`.
- E0758 / E0762 / E0763 / E0765 / E0766 — unterminated comment, char, byte, string, or byte string — close it.
- E0768 — `0b` with no digits — add digits.
- E0783 — `...` range pattern — `..=`.

## 18. Crate loading and toolchain mismatch

- E0460 / E0464 / E0786 — stale or duplicate crate artifacts, or corrupt metadata — `cargo clean`.
- E0461 — dependency built for another target — consistent `--target`.
- E0462 — found a `staticlib` where an `rlib` is needed — build it as an rlib.
- E0463 — can't find crate: not in `[dependencies]`, renamed with `package =`, or `std` missing for a cross target — add it; `rustup target add <triple>`.
- E0514 — dependency built by a different rustc — `cargo clean` after a toolchain switch.
- E0519 — current crate indistinguishable from a dependency — rename (Cargo normally prevents it).

## 19. Nightly-only or std-internal

These need a `#![feature]` or the std-internal `staged_api`; on stable you see E0554/E0658 first.

- Auto traits: E0380, E0567, E0568, E0785. Specialization: E0520, E0750. Negative impls: E0749. `#[marker]`: E0714, E0715.
- `CoerceUnsized`/`DispatchFromDyn`: E0374, E0375, E0377, E0378, E0476. `fn_traits`: E0183, E0059. `dropck_eyepatch`: E0569.
- Coroutines: E0626, E0627, E0628, E0727. TAIT: E0792. `CoercePointee`: E0802. Externally implementable items: E0806 (a wrong `#[panic_handler]` signature). `adt_const_params`: E0741.
- `#[thread_local]`: E0625, E0712. `#[linkage]`: E0791. cmse: E0781, E0798. FFI attributes: E0757. `offset_of!` on a variant: E0795. `arbitrary_self_types`: E0801; E0307 lists the stable receivers (`self`, `&self`, `&mut self`, `Box<Self>`, `Rc<Self>`, `Arc<Self>`, `Pin<P>`).
- SIMD and intrinsics: E0075, E0076, E0077, E0093, E0094, E0511. Lang items: E0152, E0264, E0522. `staged_api`: E0542, E0543, E0544, E0545, E0546, E0547, E0549.

## Retired codes and where each went

`rustc --explain` still prints these pages, headed "this error code is no longer emitted by the compiler". **Bold** codes are retired in the 1.99 docs but still live on rustc 1.97.1.

Folded into another code:

- E0087, E0088, E0089, E0090, E0243, E0244 → E0107 (generic argument count). E0110 → E0109.
- E0263 → E0403. E0281 → E0631. E0297 → E0005. E0448 → E0449. E0504 → E0505. E0523 → E0464.
- E0534 → E0805. E0535, E0551, **E0552** (unknown repr hint), **E0693** (`repr(align=8)`), E0722 → E0539.
- E0619, E0698, E0699 → E0282-style inference errors. E0205 → E0204. E0139 → E0512.
- **E0734** (stability attributes outside std) → E0658. E0387, E0389, E0595 → E0594/E0596.
- E0412 (type name not in scope) → E0425 ("cannot find type `X` in this scope"). Already retired on 1.97.1.
- **E0517** (`#[repr]` on the wrong item) and E0518 (`#[inline]` on a non-fn) → the uncoded "attribute cannot be used on …" error. E0518 is already uncoded on 1.97.1; E0517 is not.
- **E0232**, E0230, E0231 (`rustc_on_unimplemented` misuse) → warnings and the `malformed_diagnostic_*` lints.

Now a lint, not an error:

- E0001 → `unreachable_patterns`. E0162, E0165 → `irrefutable_let_patterns`. E0445 → `private_bounds`/`private_interfaces` warnings. E0636 (duplicate feature) → `duplicate_features`. E0729 → (NLL migration finished).
- E0796 (reference to `static mut`) → `static_mut_refs`: warn ≤2021, **deny in 2024**. It is a lint, so `#[allow(static_mut_refs)]` silences it (measured), although the 2024 docs call it a hard error. Fix with `&raw const X`/`&raw mut X`, atomics, or a `Mutex`.

Now legal, so no error:

- E0007, E0303 (bindings after `@`), E0009 (by-move and by-ref in one pattern), E0154 (`use` after statements), E0301, E0302 (mutation in match guards), E0329, E0632 (explicit generics alongside `impl Trait` arguments), E0706 (`async fn` in traits, 1.75), E0708 (async closures, 1.85), E0760, E0773.

Removed features or other retirements:

- E0002 (empty match on a non-empty type), E0010, E0013, E0014 (const restrictions since lifted or reworded); E0073, E0074, E0092, E0132, E0136, E0137, E0138, E0192, E0193, E0211, E0251, E0253, E0256, E0312, E0376, E0383, E0386, E0388, E0398, E0399, E0429, E0430, E0431, E0439, E0447, E0457, E0458, E0466, E0477, E0482, E0495, E0497, E0498, E0516, **E0537** (unknown `cfg` predicate), E0536, E0541, E0550, E0556, E0578, E0622, E0633, E0647, E0660, E0661, E0662, E0663, E0664 (old `llvm_asm!`), E0667, E0668, E0669, E0671, E0687, E0688, E0691 (`repr(transparent)` with an over-aligned ZST), E0701, E0705, E0724, E0739, E0744, E0755, E0756, E0759, E0771, E0772, E0775, E0776, E0778, E0779, E0788.
- **E0718** (lang attribute on the wrong item) is std-internal. E0208 and E0640 are both retired and internal to the compiler.
