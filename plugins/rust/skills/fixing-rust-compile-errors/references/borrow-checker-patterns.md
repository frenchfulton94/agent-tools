# Borrow-checker patterns

The borrow errors that recur in real code, each with the fix that compiles. Every "errors" and "compiles" claim here was measured on rustc 1.97.1, in editions 2021 and 2024 unless a row says otherwise.

## Contents

- [Choosing a fix](#choosing-a-fix)
- [Conflicting borrows: E0499, E0502](#conflicting-borrows-e0499-e0502)
- [Moving out of a borrow: E0507](#moving-out-of-a-borrow-e0507)
- [Use after move: E0382](#use-after-move-e0382)
- [Lifetimes too short: E0597, E0716, E0515](#lifetimes-too-short-e0597-e0716-e0515)
- [Closures and threads: E0373, E0521, E0596, E0525](#closures-and-threads-e0373-e0521-e0596-e0525)
- [async: futures that are not Send](#async-futures-that-are-not-send)
- [Edition-dependent borrow results](#edition-dependent-borrow-results)

## Choosing a fix

Read the three labels rustc attaches: where the first borrow occurs, where the conflicting use occurs, and where the first borrow is "later used". The fix is almost always about that last label: end the first borrow earlier, or make the two uses touch disjoint data.

Prefer, in order:

1. Reorder or narrow so the first borrow ends before the conflicting use (borrows end at their last use, not at the end of scope).
2. Borrow disjoint pieces: separate fields, `split_at_mut`, `get_disjoint_mut`.
3. Copy out a small `Copy` value, or use indices instead of references.
4. Take ownership temporarily: `mem::take`, `mem::replace`, `Option::take`.
5. Clone, when the data is small or the clone is the real semantics.
6. Shared ownership or interior mutability (`Rc`/`Arc`, `RefCell`/`Mutex`) only when the data really has several owners. Reaching for it to silence one error moves the failure to a runtime panic or a deadlock.

If none of these fit without contortion, the ownership design is the problem. Hand off to the `writing-rust` skill.

The compiler marks its `.clone()` suggestion `MachineApplicable`. That label means the edit compiles, not that it is the right fix.

## Conflicting borrows: E0499, E0502

| Situation | Error | Fix that compiles |
|---|---|---|
| `let first = &v[0]; v.push(x); use(first)` | E0502 | Copy the value out (`let first = v[0];`), or push before taking the reference |
| `for x in v.iter() { v.push(*x) }` | E0502 "cannot borrow `*v` as mutable because it is also borrowed as immutable" | Collect first, then extend: `let extra: Vec<_> = v.iter().copied().filter(…).collect(); v.extend(extra);` — or loop over indices `for i in 0..v.len()` |
| `for x in &self.items { self.add(*x) }` where `add(&mut self)` | E0502 on `*self` | Touch the field directly (`self.total += *x`), or `let items = mem::take(&mut self.items); …; self.items = items;` |
| `let a = self.a_mut(); a.extend(self.b_ref());` (getter methods borrow all of `self`) | E0502 on `*self` | Borrow fields, not methods: `let a = &mut self.a; a.extend(&self.b);`. A method call borrows the whole receiver; field access borrows only the field |
| `let a = &mut v[0]; let b = &mut v[1];` | E0499 "cannot borrow `*v` as mutable more than once at a time" | `v.swap(0, 1)`; `let (l, r) = v.split_at_mut(1);`; or `v.get_disjoint_mut([0, 1])` (returns `Result`) |
| Two `&mut` values from one `HashMap` | E0499 | `map.get_disjoint_mut([&k1, &k2])` returns `[Option<&mut V>; 2]` and panics if keys overlap. Slice and `HashMap` `get_disjoint_mut` have been stable since 1.86 |
| `if let Some(v) = map.get(&k) { return v; } map.insert(k, …); …` (conditional return of a borrow) | E0502, in both editions | This is rejected on stable even though it is sound (it needs the Polonius checker, which is not stable). Do not restructure the branch; use `map.entry(k).or_default()` / `or_insert_with`, or `if !map.contains_key(&k) { map.insert(…) } &map[&k]` |
| `v.push(v.len())` | compiles | Two-phase borrows already allow it; no fix needed |
| `let mut inc = \|\| n += 1; println!("{n}"); inc();` | E0502 "cannot borrow `n` as immutable because it is also borrowed as mutable" (the 1.99 index describes this case as E0501) | Finish using the closure before reading `n`, or pass `n` in as a parameter |

## Moving out of a borrow: E0507

| Situation | Error | Fix that compiles |
|---|---|---|
| `fn f(s: &mut S) -> String { s.name }` | E0507 "cannot move out of `s.name` which is behind a mutable reference" | `mem::take(&mut s.name)` (leaves `Default`), `mem::replace(&mut s.name, new)` |
| Same with an `Option` field | E0507 | `s.next.take()` |
| `match self.st { State::A(s) => … }` in a `&mut self` method, rebuilding `self.st` | E0507 "cannot move out of `self.st` as enum variant `A` which is behind a mutable reference" | `match mem::replace(&mut self.st, State::B) { … }` — swap a cheap placeholder in, then assign the result |
| `let x = v[0];` with `v: &Vec<String>` | E0507 "cannot move out of index of `Vec<String>`" | `&v[0]`, `.clone()`, or `v.into_iter()` when you own `v` |
| A non-`move` closure passed as `FnMut` (`sort_by_key`) consumes a captured value | E0507 "cannot move out of `value`, a captured variable in an `FnMut` closure" | Don't consume captured state; clone, or require `FnOnce`. A `move` closure that consumes its capture reports E0525 instead |
| `s.name` where `S: Drop`, by value | E0509 "cannot move out of type `S`, which implements the `Drop` trait" | `mem::take(&mut s.name)` |

## Use after move: E0382

- `for _ in 0..n { eat(s); }` reports "use of moved value: `s`" with "value moved here, in previous iteration of loop". Borrow (`eat(&s)` with a `&str`/`&T` parameter), clone per iteration, or move the creation inside the loop.
- `println!("{s}")` after a move reports "**borrow** of moved value": format macros borrow.
- A `move` closure moves every captured variable. To move a clone instead, shadow it before the closure: `let s2 = s.clone(); move || use(s2)`.
- `for x in vec` moves `vec`; iterate `&vec` to keep it.
- The note "consider implementing `Clone` for this type" is a hint, not a requirement. Check whether a borrow serves first.

## Lifetimes too short: E0597, E0716, E0515

| Situation | Error | Fix that compiles |
|---|---|---|
| `let r; { let x = 5; r = &x; } use(r)` | E0597 "`x` does not live long enough" | Declare `x` in the outer scope |
| `let p = id(&String::from("a")); use(p)` | E0716 "temporary value dropped while borrowed" | `let s = String::from("a"); let p = id(&s);` (the compiler's help writes exactly this) |
| `let s = &String::from("a");` and `let s = Some(&String::from("a"));` | compiles | Temporary lifetime extension applies when `&temp` sits directly in the `let` initializer, including inside a tuple, struct, or tuple-struct constructor such as `Some(..)`. It does not apply through a function call |
| `fn f() -> &str { let s = String::new(); &s }` | E0515 "cannot return reference to local variable `s`" | Return `String` |
| `fn f<'a>() -> Iter<'a, i32> { let v = vec![1]; v.iter() }` | E0515 "cannot return value referencing local variable `v`" | Return `v.into_iter()` (owned iterator) |

## Closures and threads: E0373, E0521, E0596, E0525

| Situation | Error | Fix that compiles |
|---|---|---|
| `thread::spawn(\|\| println!("{v:?}"))` on a local `v` | E0373 "closure may outlive the current function, but it borrows `v`…" | `move` |
| The same with `v: &Vec<_>` (a parameter) | E0521 "borrowed data escapes outside of function" plus E0373 | `std::thread::scope(\|s\| { s.spawn(\|\| …); });` borrows without `'static`; or pass owned data |
| `let inc = \|\| n += 1; inc();` | E0596 "cannot borrow `inc` as mutable, as it is not declared as mutable" | `let mut inc = …` — a mutating closure is itself mutated when called |
| `let c = \|\| drop(s); call(c)` where `call<F: Fn()>` | E0525 "expected a closure that implements the `Fn` trait, but this closure only implements `FnOnce`" | Loosen the bound to `FnOnce`, or don't move out of the capture |
| `let push = \|el: &str\| v.push(el);` with `v: Vec<&str>` | E0521 "borrowed data escapes outside of closure" | Remove the annotation (`\|el\| v.push(el)` compiles): writing `&str` introduces a fresh higher-ranked lifetime |

Joining the thread before returning does not satisfy E0373: the checker cannot see the join. Scoped threads are the stable answer.

## async: futures that are not Send

The error has no code: `future cannot be sent between threads safely`, with "note: future is not `Send` as this value is used across an await". It appears when a future holding `Rc`, `RefCell` borrows, or a `std::sync::MutexGuard` across `.await` goes to a `Send`-bound spawner (`tokio::spawn`).

Measured on 1.97.1:

- `let g = m.lock().unwrap(); let v = *g; drop(g); something().await;` **still fails**. `drop` does not end the value's scope for this analysis.
- `let v = { let g = m.lock().unwrap(); *g }; something().await;` compiles. End the guard's scope with a block.
- Replace `Rc` with `Arc`. Across `.await`, use an async-aware mutex (`tokio::sync::Mutex`) only when the lock must really be held over the await.

## Edition-dependent borrow results

| Code | 2021 | 2024 |
|---|---|---|
| `fn f() -> usize { let c = RefCell::new(vec![1]); c.borrow().len() }` | E0597 "`c` does not live long enough" (the tail expression's temporary outlives `c`) | compiles: tail-expression temporaries drop before locals |
| `fn f(x: &()) -> impl Sized { x }` | E0700, fix `+ use<'_>` | compiles: return-position `impl Trait` captures all in-scope lifetimes |
| `if let Some(x) = cell.borrow().first().copied() { … } else { cell.borrow_mut().push(2) }` | compiles, then panics at runtime with a `BorrowMutError` (the scrutinee's borrow lives through `else`) | runs: the scrutinee's temporaries drop before `else` |

Check the crate's `edition` before applying a fix found online: an answer written for 2021 may fix a problem 2024 does not have, or the reverse.
