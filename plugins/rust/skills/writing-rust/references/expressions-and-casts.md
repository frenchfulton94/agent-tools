# Expressions, precedence and casts

From the Rust Reference (1.99). Results marked *measured* were compiled and run on rustc 1.97.1.

## Contents

- [Operator precedence](#operator-precedence)
- [Evaluation order](#evaluation-order)
- [`as` casts](#as-casts)
- [Literals](#literals)
- [Blocks, loops and `?`](#blocks-loops-and-)
- [Arrays and places](#arrays-and-places)

## Operator precedence

Highest to lowest:

| Operators | Associativity |
|---|---|
| paths, method calls, field access | left to right |
| function calls, indexing | |
| `?` | |
| unary `-` `!` `*` `&` `&mut` | |
| `as` | left to right |
| `*` `/` `%` | left to right |
| `+` `-` | left to right |
| `<<` `>>` | left to right |
| `&` | left to right |
| `^` | left to right |
| `\|` | left to right |
| `==` `!=` `<` `>` `<=` `>=` | require parentheses; cannot chain |
| `&&` | left to right |
| `\|\|` | left to right |
| `..` `..=` | require parentheses |
| `=` and compound assignment | right to left |
| `return`, `break`, closures | |

Where this differs from C or from intuition:

- **Bitwise operators bind tighter than comparisons.** `x & 1 == 0` is `(x & 1) == 0` (*measured*). In C it would be `x & (1 == 0)`.
- **Method calls bind tighter than unary minus.** `-1i32.abs()` is `-(1i32.abs())`, which is `-1` (*measured*). Write `(-1i32).abs()`.
- `?` binds tighter than unary operators: `*x?` is `*(x?)`; `&x?` is `&(x?)`.
- `as` binds tighter than arithmetic: `a * b as u64` is `a * (b as u64)`; `-x as u32` is `(-x) as u32`.
- `a == b == c` and `a < b < c` are errors ("comparison operators cannot be chained", *measured*). `a..b..c` also fails to parse.
- Ranges sit below `||`: `a..b + 1` is `a..(b + 1)`.
- A closure body extends as far right as possible: `|x| x + 1` captures all of `x + 1`.
- `!` is both logical and bitwise NOT; there is no `~`. `&&x` is two borrows, `& &x`.
- Only operators backed by a `std::ops` trait can be overloaded. `=`, `&&`, `||` and the borrow operators cannot.
- The result type of `<<` and `>>` on integers is the type of the left operand.

## Evaluation order

- Operands evaluate left to right for calls, method calls, binary operators, arrays, tuples and struct expressions (*measured* for `+`).
- **Assignment evaluates the right-hand side first**, then the place on the left.
- **Compound assignment depends on the types.** When both operands are primitive types known before monomorphisation, the right side is evaluated first; otherwise (a `Wrapping<u8>`, any generic `T`) the left side is evaluated first and the call is `AddAssign::add_assign(&mut lhs, rhs)`. *Measured*: `a[{push(1); 0}] += {push(2); 1}` records `[2, 1]` for `[u8; 1]` and `[1, 2]` for `[Wrapping<u8>; 1]`. The Reference says not to depend on this.
- Comparison operators take their operands by shared reference (`a == b` is `PartialEq::eq(&a, &b)`), so they never move. Arithmetic operators take operands by value.
- Destructuring assignment `(a, b) = (b, a);` desugars to a `let` of the right side followed by assignments. It must be irrefutable, and default binding modes do not apply.
- Assignment yields `()`, so `x = y = 6` does not do what it does in C.

## `as` casts

- **Integer to integer:** same width reinterprets the bits; narrowing truncates (`300i32 as u8 == 44`, *measured*); widening sign-extends when the **source** is signed and zero-extends when it is unsigned.
- **Float to integer:** truncates toward zero and saturates; NaN becomes 0 (`f32::NAN as i32 == 0`, `1e20f64 as i32 == i32::MAX`, `-1.9f64 as u8 == 0`, *measured*).
- **Integer to float:** rounds to nearest, ties to even; only `u128 as f32` can overflow to infinity.
- **`f64 as f32`** rounds to nearest; an overflow gives infinity.
- **To `char`:** only `u8 as char`. For any other integer use `char::from_u32(x)` (returns `Option`) or `char::try_from(x)`.
- **Enums:** a field-less enum casts to its discriminant, unless it implements `Drop` (an error since 1.86). Outside the defining crate, an enum with a `#[non_exhaustive]` variant cannot be cast.
- **Pointers:** prefer `.cast()`, `.cast_mut()`, `.cast_const()`, `.addr()` and `ptr::with_exposed_provenance` to `as`. Casting `*const [u16]` to `*const [u8]` keeps the element count, so it covers half the bytes. A trait-object pointer cast may drop auto traits but may not change the principal trait.
- Prefer lossless conversions: `u64::from(x)`, `i32::try_from(x)?`, `x.cast_unsigned()` (1.87). Avoid `as _`, which breaks when inference changes.

## Literals

- An unsuffixed integer defaults to `i32` and a float to `f64` when inference cannot decide. An out-of-range literal (`256u8`) is the deny-by-default `overflowing_literals`; `-128i8` is fine.
- `0x01_f32` is the **integer** 7986: `f32` is hex digits here. `2.f64` is a method call on `2`; write `2.0f64` or `2_f64`. `1.` is a float unless followed by `.`, `_` or an identifier, so `1..2` is a range.
- `-1i8` is two tokens: unary minus applied to `1i8`.
- `b"abc"` is `&'static [u8; 3]`, an array reference, not a slice. `c"abc"` is `&'static CStr` (edition 2021+), with no interior NUL allowed.
- `"\x41"` escapes go up to `\x7F` in `str` literals; byte literals allow any `\xHH`. A trailing `\` at the end of a line in a string skips the newline and all following whitespace.
- There are no `inf`/`NaN` literals; use `f64::INFINITY`, `f64::NAN`.
- Tuple indices are plain decimal: `t.0`, never `t.00` or `t.0usize`.

## Blocks, loops and `?`

- A block's value is its tail expression; a trailing `;` makes it `()`. E0308 with "remove this semicolon to return this value" means exactly that.
- `loop` and labelled blocks can produce values: `let v = loop { break 42; };`, `let v = 'b: { if c { break 'b 1; } 2 };`. `while` and `for` always produce `()`. `break` inside a labelled block must name the label.
- `return`, `break`, `continue`, `panic!` and a `loop` without `break` have type `!` and coerce to any type. `!` itself is not a nameable type on stable outside function return types.
- A struct literal cannot appear directly in the condition of `if`, `while`, `match` or `for`; wrap it in parentheses.
- `for pat in expr` calls `IntoIterator::into_iter(expr)` and keeps temporaries in `expr` alive for the whole loop.
- **`?` works on** `Result` (the error converts through `From::from`), `Option`, `ControlFlow`, and `Poll<Result<..>>` / `Poll<Option<Result<..>>>` (on `Pending` it evaluates to `Pending` without returning). It never converts between `Option` and `Result`. The `Try` trait is unstable, so user types cannot support `?`.
- Inside a closure or `async` block, `?` and `return` exit that closure or block, not the enclosing function.
- `_ = expr;` discards a value, like `let _ = expr;`.

## Arrays and places

- `[expr; N]` with `N > 1` needs `expr: Copy`, a `const { }` block, or a path to a `const` item: `[const { String::new() }; 2]` (*measured*). A const operand is evaluated `N` times.
- `[expr; 0]` still evaluates `expr` once and drops the result (*measured*).
- A constant out-of-bounds index on an array is the deny-by-default `unconditional_panic`.
- Calling a closure stored in a field needs parentheses: `(s.f)()`.
- Arrays implement `IntoIterator` by value (edition 2021+), `Default` up to length 32, and `From<(T, T, …)>` for homogeneous tuples up to 12. A slice converts to an array with `<[T; N]>::try_from(slice)` or `slice.as_array::<N>()` (1.93).
- `array.map(f)` is eager and can use a lot of stack for large arrays; prefer `array.into_iter().map(f)` unless you need an array back.
