# Ownership, lifetimes and drops

Precise rules from the Rust Reference (1.99) and the Book. Results marked *measured* were compiled or run on rustc 1.97.1.

## Contents

- [Borrows that compile when you might expect them not to](#borrows-that-compile-when-you-might-expect-them-not-to)
- [Moving out of places](#moving-out-of-places)
- [Temporary scopes](#temporary-scopes)
- [Temporary lifetime extension](#temporary-lifetime-extension)
- [Drop order](#drop-order)
- [Closure capture](#closure-capture)
- [Lifetimes in signatures](#lifetimes-in-signatures)
- [Variance and implied bounds](#variance-and-implied-bounds)
- [Smart pointers and interior mutability](#smart-pointers-and-interior-mutability)

## Borrows that compile when you might expect them not to

- **Non-lexical lifetimes.** A borrow lasts from creation to its last use, not to the end of the block.
- **Two-phase borrows.** An autoref'd `&mut` receiver is reserved first and activated after the arguments are evaluated, so `v.push(v.len())`, `x.push(x.len())` with `x: &mut Vec<_>`, and `x += x` compile (*measured*). Spelled out by hand, `(&mut x).add_assign(x)` or `<T as AddAssign>::add_assign(&mut x, x)` is an error, "cannot use `x` because it was mutably borrowed".
- **Disjoint fields.** Fields of a local struct, or of a struct behind a reference, are separate borrow targets. This does **not** work through a user `Deref` type other than `Box`, and not across a method call that takes `&mut self`: a method borrows the whole value. Split the borrow by destructuring (`let Self { a, b, .. } = self;`) or by passing the fields to a free function.

## Moving out of places

You can move out of: an unborrowed local, a temporary, a field of a movable place **whose type does not implement `Drop`**, and `*b` where `b: Box<T>` (the only deref you can move out of). After a move, the local is uninitialised until reassigned.

Moving a field out from behind `&mut self` (E0507 "cannot move out of `self.x` which is behind a mutable reference"), in order of preference:

- `Option::take()` when the field is an `Option`;
- `mem::take(&mut self.x)` when the type has a cheap `Default`;
- `mem::replace(&mut self.x, new)`;
- `Vec::drain(..)` to move all elements out of a vector field (the Book prefers this to wrapping each element in `Option` when joining threads in `Drop`).

## Temporary scopes

A temporary is created when a value expression is used where a place is needed (`&f()`, `f().method()`, a `match` scrutinee). It is dropped at the end of its **temporary scope**, the smallest enclosing one of:

- the whole function body;
- a statement;
- the body of `if`, `while` or `loop`, and the `else` block of an `if`;
- a non-binding condition of `if` or `while`, or a non-binding match guard;
- each operand of `&&` and `||`;
- a binding match guard together with its arm body;
- the condition and body of `while let`;
- on edition 2024: the condition and `then` block of `if let` (not the `else`), and a block's entire tail expression.

A `match` scrutinee is **not** a temporary scope. Measured with a `Mutex` on both editions:

| Code | Guard held in the body? |
|---|---|
| `match m.lock().unwrap().len() { _ => .. }` | yes, for the whole `match` |
| `while let Some(_) = m.lock().unwrap().get(n) { .. }` | yes, every iteration |
| `if let Some(_) = m.lock().unwrap().first() { .. }` | yes, in the `then` block |
| `if let … { } else { .. }` | 2021: yes; 2024: no |
| `let len = m.lock().unwrap().len();` | no, dropped at the end of the `let` statement |

So the Book's thread-pool worker must write `let job = rx.lock().unwrap().recv().unwrap(); job();` rather than `while let Ok(job) = rx.lock().unwrap().recv() { job(); }`, which serialises the workers.

- `let _ = m.lock();` drops the guard immediately (deny-by-default `let_underscore_lock`, "non-binding let on a synchronization lock"). Bind a name: `let _guard = m.lock();`. For other `Drop` types, `let _ = expr` also drops at once (allow-by-default `let_underscore_drop`).
- `_` does not bind and does not move: `let _ = x;` leaves `x` usable, while `let _x = x;` moves it.
- If an expression panics or returns part-way, already-evaluated operand temporaries drop in reverse order.

## Temporary lifetime extension

In a `let` initializer, some temporaries live to the end of the enclosing block instead of the statement. The rules are marked "subject to change" in the Reference.

**Extending expressions** (the temporary lives as long as the binding): the initializer itself; the operand of an extending `&` or `&mut`; the operands of extending array, cast, braced-struct and tuple expressions; the arguments of tuple-struct and tuple-variant constructors (since 1.89); the tail of an extending block, including `unsafe { }` and `const { }`; the tails of extending `if`/`else` blocks and `match` arms; the arguments of `format_args!` (storing it in a `let` works since 1.89) and `pin!`.

```rust
let a = &temp();                       // ok
let b = Some(&temp());                 // ok since 1.89 (measured)
let c = (&temp(), 1);                  // ok
let d = if cond { &temp() } else { &other() };   // ok
let e = format_args!("{}", temp());    // ok since 1.89 (measured)
```

**Not extended**, so using the binding later is E0716 "temporary value dropped while borrowed": function and method arguments (`let x = id(&temp());`, *measured*), method receivers (`(&temp()).m()`), a `match` scrutinee (`match &temp() { x => x }`), an `async` block tail, a closure body, `loop { break &temp() }`, a labelled-block `break`, `&0 + &1`. Fix: bind the temporary to its own `let`.

Constant promotion is separate: `&5`, `&None`, `&[1, 2]` are `'static` because the value could be a constant with no interior mutability and no destructor.

## Drop order

- Locals drop in reverse order of declaration. Variables in one pattern drop in reverse order of their position (`let (a, b) = ..` drops `b` first). An or-pattern drops in the binding order of its **first** alternative.
- Function parameters drop **after** the body's locals, each after the bindings from its own pattern.
- Fields drop in **declaration** order after the type's own `Drop::drop`; tuple and array elements first to last. By-value closure captures drop in an unspecified order.
- Temporaries drop in reverse order of creation at the end of their scope.
- Assigning to an initialised place drops the old value first. A partially moved variable drops only its remaining fields.
- Statics are never dropped. `process::exit`, `abort` and `panic = "abort"` skip destructors.
- **Leaking is safe.** `mem::forget`, `ManuallyDrop` and `Rc` cycles do not cause UB, so unsafe code must never rely on a destructor running (the one exception is the pinning drop guarantee; see `concurrency-and-async.md`). Break `Rc` cycles with `Weak` (parent → child strong, child → parent weak).
- A value cannot be `Copy` if it or any field implements `Drop`.
- You cannot call `x.drop()` (E0040); call `drop(x)`, which is in the prelude.

## Closure capture

- A closure captures each **place path** it uses (`s.a`, `(*r).f`), not whole variables (edition 2021+), with the weakest mode its body needs: shared borrow, unique borrow, mutable borrow, then by value. The mode depends only on the body, not on surrounding code.
- `move` makes every capture by value, but still per path: after `thread::spawn(move || s.a.len())`, `s.b` remains usable (*measured*).
- Capture paths are truncated: at the rightmost deref of a shared reference; in a `move` closure, before the first deref of a reference (the reference itself moves in); at a raw-pointer deref; at a union (the whole union is captured); before a field of a `#[repr(packed)]` struct (the whole struct is captured, which can change borrow errors and `Send`-ness).
- `let _ = x;` and `match x { _ => .. }` inside a closure do not capture `x`. Arrays and slices are never partially captured: `[a, _]`, indexing and sub-slicing capture the whole array.
- Matching a variant of a multi-variant enum reads the discriminant, so the closure borrows it. Since 1.95 this includes a single-variant `#[non_exhaustive]` enum.
- The `Fn` traits follow what the body does with captures, not how they were captured: moving a capture out makes the closure only `FnOnce`; mutating makes it `FnMut`; otherwise `Fn`. A `move` closure can be `Fn`.
- A closure is `Send` if every by-value capture is `Send` and every by-reference capture is `Sync`.
- Only non-capturing, non-async closures coerce to `fn` pointers.
- Async closures capture all their arguments, used or not. When the returned future holds a mutable or by-value capture, the closure implements only `AsyncFnOnce`/`FnOnce`, not `Fn`/`FnMut`; take `impl AsyncFn..` bounds instead of `impl Fn() -> Fut`.

## Lifetimes in signatures

- **Elision.** Each elided input lifetime is distinct. With exactly one input lifetime, it goes to every elided output. With `&self` or `&mut self`, self's lifetime goes to every elided output. Otherwise an elided output is an error (E0106).
- When E0106's help puts `'a` on every parameter, tie the output only to the input it actually borrows from: `fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str>`.
- When the compiler suggests `'static`, the real problem is usually a dangling reference or a mismatched lifetime. Return an owned value instead of a reference to a local (E0515).
- Write `'_` for a hidden lifetime in a path (`Formatter<'_>`, `Ref<'_, T>`). `elided_lifetimes_in_paths` is allow-by-default; `mismatched_lifetime_syntaxes` (warn, 1.89) flags a signature that hides a lifetime on one side and shows it on the other.
- **Default trait-object lifetimes.** `Box<dyn Trait>` means `Box<dyn Trait + 'static>`; `&'a dyn Trait` means `&'a (dyn Trait + 'a)`; `&'a Box<dyn Trait>` is `&'a Box<dyn Trait + 'static>` (the innermost container decides). A container with two lifetime bounds on the parameter needs an explicit `+ 'a`. Store borrowed trait objects as `Box<dyn Trait + 'a>`.
- `const` and `static` reference types default to `'static`.
- Return-position `impl Trait` capture differs by edition; see `edition-2024.md`.

## Variance and implied bounds

| Type | Variance in `'a` | Variance in `T` |
|---|---|---|
| `&'a T` | covariant | covariant |
| `&'a mut T` | covariant | **invariant** |
| `*const T` | | covariant |
| `*mut T`, `UnsafeCell<T>`, `Cell<T>` | | invariant |
| `fn(T) -> U` | | contravariant in `T`, covariant in `U` |
| `dyn Trait<T> + 'a` | covariant | invariant |
| `PhantomData<T>` | | covariant |

A user type is invariant in a parameter used in positions of different variance. Because `&mut T` is invariant in `T`, a `&mut Vec<&'static str>` cannot be passed where `&mut Vec<&'a str>` is expected.

Only **lifetime** bounds are implied: `fn f<'a, T>(x: &'a T)` gets `T: 'a` for free. Trait bounds on a struct are not implied: with `struct W<T: Debug>(T)`, `fn f<T>(w: W<T>)` is E0277 until the function also says `T: Debug`. So put trait bounds on impls and functions, not on the struct definition, unless the struct cannot exist without them.

## Smart pointers and interior mutability

| Need | Use |
|---|---|
| Heap allocation, recursive type, trait object, cheap move of a large value | `Box<T>` |
| Shared ownership, one thread | `Rc<T>`; with mutation `Rc<RefCell<T>>` |
| Shared ownership across threads | `Arc<T>`; with mutation `Arc<Mutex<T>>`, `Arc<RwLock<T>>`, or atomics |
| Mutate a `Copy` value through `&` | `Cell<T>` (never hands out a reference; `Cell::update` since 1.88) |
| Mutate through `&` with runtime-checked borrows | `RefCell<T>`; a conflicting borrow panics `RefCell already borrowed` |
| Initialise once | `OnceCell` / `OnceLock` |
| Initialise lazily from one closure | `LazyCell` / `LazyLock` (1.80) |
| A back-reference that must not keep its target alive | `Weak<T>` (`Rc::downgrade`, `upgrade()` returns `Option`) |

- Write `Rc::clone(&a)` and `Arc::clone(&a)`, not `a.clone()`, so reference-count bumps stand out from deep clones.
- `RefCell`, `Cell` and `Rc` are not `Sync`; `Rc` is not `Send`. The thread-safe counterpart of `Rc<RefCell<T>>` is `Arc<Mutex<T>>`.
- Interior mutability is a last resort in the docs' words. Legitimate uses: shared state inside `Rc`/`Arc`, caches behind logically immutable methods, and test mocks whose trait methods take `&self` (do not change a production trait to `&mut self` for a test).
- Deref coercion applies in exactly three cases: `&T` → `&U` when `T: Deref<Target = U>`; `&mut T` → `&mut U` when `T: DerefMut<Target = U>`; `&mut T` → `&U`. A shared reference never coerces to a mutable one. It chains as often as needed (`&Box<String>` → `&str`) at compile time.
