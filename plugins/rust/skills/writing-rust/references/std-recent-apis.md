# Standard library: recent APIs and precise behaviour

Versions for 1.80–1.97 come from the release notes shipped with rustc 1.97.1, and a sample of each was compiled on 1.97.1. Items marked **1.98+** come from the 1.99 std docs and fail with E0658 on 1.97; check `rustc --version` and the crate's `rust-version` before using any of them.

## Contents

- [Stabilised by version](#stabilised-by-version)
- [1.98 and later (docs only)](#198-and-later-docs-only)
- [Deprecations](#deprecations)
- [Still unstable: do not suggest on stable](#still-unstable-do-not-suggest-on-stable)
- [Integer arithmetic families](#integer-arithmetic-families)
- [Floating point](#floating-point)
- [Strings and chars](#strings-and-chars)
- [Slices and sorting](#slices-and-sorting)
- [Collections](#collections)
- [Formatting and I/O](#formatting-and-io)

## Stabilised by version

Language features are listed in `SKILL.md`; this table is library APIs.

| Version | APIs |
|---|---|
| 1.97 | `{integer}::bit_width`, `isolate_highest_one`, `isolate_lowest_one`, `highest_one`, `lowest_one` (also on `NonZero`); `Default for RepeatN`; `char::is_control` const |
| 1.96 | `assert_matches!`, `debug_assert_matches!` (import with `use std::assert_matches;`); `core::range::{Range, RangeFrom, RangeToInclusive}` and their iterators; `From<T>` for `LazyCell`, `LazyLock`, `AssertUnwindSafe` |
| 1.95 | `cfg_select!`; `mod core::range` and `RangeInclusive`; `hint::cold_path`; atomic `update`/`try_update`; `Vec::push_mut`, `insert_mut`, `VecDeque::push_front_mut`/`push_back_mut`/`insert_mut`; `<*const T>::as_ref_unchecked`, `<*mut T>::as_mut_unchecked`; `bool: TryFrom<{integer}>`; `Layout::repeat`, `extend_packed`, `dangling_ptr` |
| 1.94 | `<[T]>::array_windows::<N>()`, `element_offset`; `LazyCell`/`LazyLock::get`, `get_mut`, `force_mut`; `Peekable::next_if_map`; `TryFrom<char> for usize`; `f32/f64::consts::EULER_GAMMA`, `GOLDEN_RATIO` |
| 1.93 | `<[T]>::as_array::<N>()`, `as_mut_array`; `[MaybeUninit<T>]::write_copy_of_slice`, `write_clone_of_slice`, `assume_init_ref`/`_mut`/`_drop`; `String::into_raw_parts`, `Vec::into_raw_parts`; `VecDeque::pop_front_if`/`pop_back_if`; `fmt::from_fn`; `char::MAX_LEN_UTF8`, `MAX_LEN_UTF16`; `Duration::from_nanos_u128`; `unchecked_shl`/`unchecked_shr`/`unchecked_neg` |
| 1.92 | `Box`/`Rc`/`Arc::new_zeroed`, `new_zeroed_slice`; `RwLockWriteGuard::downgrade`; `btree_map::Entry::insert_entry`; `NonZero<u{N}>::div_ceil` |
| 1.91 | `strict_*` integer family; unsigned `carrying_add`, `borrowing_sub`, `carrying_mul`, `carrying_mul_add`, `checked_signed_diff`; `str::floor_char_boundary`, `ceil_char_boundary`; `Path::file_prefix`; `PathBuf::add_extension`, `with_added_extension`; `PartialEq` between `Path`/`PathBuf` and `str`/`String`; `Duration::from_mins`, `from_hours`; `iter::chain`; `array::repeat`; `BTreeMap`/`BTreeSet::extract_if`; `PanicHookInfo::payload_as_str`; `Ipv4Addr::from_octets`; `Cell::as_array_of_cells` |
| 1.90 | unsigned `checked_sub_signed`, `wrapping_sub_signed`, `saturating_sub_signed`, `overflowing_sub_signed`; `CStr`/`CString`/`Cow<CStr>` comparisons; float `floor`/`ceil`/`round`/`trunc` const |
| 1.89 | `File::lock`, `lock_shared`, `try_lock`, `try_lock_shared`, `unlock`; `Result::flatten`; `NonNull::from_ref`, `from_mut`, `without_provenance`; `NonZero<char>`; `OsString::leak`, `PathBuf::leak` |
| 1.88 | `<[T]>::as_chunks::<N>()`, `as_rchunks`, `as_chunks_mut`, `as_chunks_unchecked`; `HashMap`/`HashSet::extract_if(pred)`; `Cell::update`; `hint::select_unpredictable`; `Default` for raw pointers; `proc_macro::Span::line`/`column`/`file` |
| 1.87 | `Vec::extract_if(range, pred)`, `LinkedList::extract_if`; `<[T]>::split_off`, `split_off_first`, `split_off_last` (+ `_mut`); `io::pipe`; `str::from_utf8` and friends as inherent `str::` functions; `String::extend_from_within`; `OsStr::display`; `offset_from_unsigned`; `cast_signed`/`cast_unsigned`; `is_multiple_of`; `unbounded_shl`/`unbounded_shr`; signed `midpoint`; `TryFrom<Vec<u8>> for String`; `env::home_dir` un-deprecated |
| 1.86 | `<[T]>::get_disjoint_mut`, `HashMap::get_disjoint_mut`; `Vec::pop_if`; `Once::wait`, `OnceLock::wait`; float `next_up`/`next_down`; `str::split_at_checked` const |
| 1.85 | float and unsigned `midpoint`; `ptr::fn_addr_eq`; `Waker::noop`; `FromIterator`/`Extend` for tuples up to 12; `AsyncFn*` in the prelude |
| 1.84 | strict provenance: `addr`, `with_addr`, `map_addr`, `expose_provenance`, `ptr::without_provenance`, `ptr::with_exposed_provenance`, `ptr::dangling`; `isqrt`, `checked_isqrt`; `Pin::as_deref_mut` |
| 1.83 | `Option::get_or_insert_default`; `hash_map::Entry::insert_entry`; `char::MIN`; many `io::ErrorKind` variants (`NotADirectory`, `IsADirectory`, `StorageFull`, …); `ControlFlow::break_value`; `BufRead::skip_until`; `&mut` in const |
| 1.82 | `Option::is_none_or`; `iter::repeat_n`; `<[T]>::is_sorted`, `is_sorted_by`, `is_sorted_by_key`; `Box`/`Rc`/`Arc::new_uninit`; `thread::Builder::spawn_unchecked` |
| 1.81 | `core::error::Error`; `hint::assert_unchecked`; `fs::exists`; `PanicHookInfo` (rename of `PanicInfo` in hooks); `Duration::abs_diff`; new sort implementations that may panic on a non-total order |
| 1.80 | `LazyCell`, `LazyLock`; `Option::take_if`; `split_at_checked`; `str::trim_ascii` and the `[u8]` forms; `<[[T; N]]>::as_flattened`, `Vec::into_flattened`; `IntoIterator for Box<[T]>`; `size_of`/`align_of` in the prelude; `Ipv4Addr::to_bits` |

Older but often missed: `OnceLock` 1.70, `IsTerminal` 1.70, `Option::is_some_and` 1.70, `thread::scope` 1.63, `let … else` 1.65, `div_ceil` (unsigned) 1.73, `first_chunk`/`chunk_by` 1.77, `async fn` in traits 1.75, associated type bounds 1.79.

## 1.98 and later (docs only)

Not measurable on 1.97; each gives E0658 there (*measured*).

- 1.98: `bool::ok_or(e)` / `ok_or_else(|| e)` → `Result<(), E>` (`cond.ok_or(MyError)?`); `str::strip_circumfix(prefix, suffix)` and the slice form (`None` when either is missing or they overlap); `str::substr_range(sub)` and `slice::subslice_range(sub)`, returning `core::range::Range<usize>` by pointer arithmetic; `{integer}::format_into(&mut core::fmt::NumBuffer::new())` for allocation-free decimal formatting; `f32`/`f64::algebraic_add`/`sub`/`mul`/`div`/`rem` (reassociating "fast-math" operations with non-deterministic results).
- 1.99: integer module constants and `min_value()`/`max_value()` become `deprecated` warnings.
- The 1.99 docs also list rustc lints absent from 1.97: `raw_borrows_via_references`, `method_call_on_diverging_infer_var`, `c_void_returns`.

## Deprecations

- `std::i32::MAX`, `std::u8::MIN` and the other integer-module constants → `i32::MAX`, `u8::MIN`. `i32::max_value()` / `min_value()` → `i32::MAX` / `MIN`. `std::f64::EPSILON`, `NAN`, `INFINITY`, `MAX` … → `f64::EPSILON` etc. (`std::f64::consts::PI` is fine). `std::char::from_u32`, `std::char::MAX` → `char::from_u32`, `char::MAX`. On 1.97 all of these trigger only the allow-by-default `deprecated_in_future` (*measured*); the 1.99 docs mark the integer ones `deprecated` since 1.99.
- Long deprecated: `try!` → `?`; `mem::uninitialized` → `MaybeUninit`; `hash::SipHasher`; `AsciiExt`; `str::trim_left`/`trim_right` → `trim_start`/`trim_end`; `[T]::connect` → `join`; `lines_any` → `lines`; `thread::sleep_ms` → `thread::sleep`; `PanicInfo` in hooks → `PanicHookInfo`; `f32::abs_sub` (it was C `fdim`).

## Still unstable: do not suggest on stable

E0658 on stable: signed `div_ceil`, `div_floor`, `next_multiple_of` (`int_roundings`); `widening_mul`; integer `saturating_cast`/`checked_cast`; `Iterator::array_chunks`, `map_windows`, `intersperse`; `slice::split_once`; `<[f32]>::sort_floats`; `std::sync::nonpoison`, `mpmc`, `oneshot`; `OnceLock::get_or_try_init`; `Error::provide`/`Report`; `std::async_iter`; `future::join!`; `hash_map!`; `String::into_chars`; `impl Trait` in `let` bindings; `!` as a nameable type; `f16`/`f128`; `std::simd`; `try` blocks; defining C-variadic functions.

## Integer arithmetic families

| Family | On overflow | Note |
|---|---|---|
| `a + b` | panics if overflow checks are on (debug default), wraps otherwise (release default) | relying on the wrap is a bug |
| `checked_*` | `None` | the only family that never panics on division by zero |
| `wrapping_*` | wraps | `wrapping_div(MIN, -1) == MIN` |
| `saturating_*` | clamps | `saturating_div(MIN, -1) == MAX` |
| `overflowing_*` | `(wrapped, true)` | |
| `strict_*` (1.91) | **always panics**, release included (*measured*) | |
| `unsafe unchecked_*` | UB | to avoid the debug panic, use `wrapping_*`, not this |

- `i32::MIN / -1` and `% -1` panic "attempt to divide with overflow" in **every** build, regardless of `overflow-checks` (*measured* in release). Every division variant except `checked_*` panics on a zero divisor.
- `i32::MIN.abs()` panics in debug and returns `i32::MIN` in release (*measured*). Use `unsigned_abs()` or `abs_diff` (returns unsigned, never overflows).
- **Shifts:** `wrapping_shl`/`wrapping_shr` and `overflowing_*` take the shift amount modulo the bit width: `42i32.wrapping_shl(32) == 42`, `42u8.wrapping_shl(8) == 42` (*measured*). Plain `<<` does the same when overflow checks are off. `unbounded_shl`/`unbounded_shr` (1.87) shift everything out (`42i32.unbounded_shl(32) == 0`). `checked_shl` returns `None` only when the amount is at least the bit width; bits shifted out are not overflow.
- `ilog`, `ilog2`, `ilog10` panic on zero or negative input; use `checked_ilog*`. Prefer `ilog2` to `leading_zeros` arithmetic.
- `midpoint(a, b)` never overflows and rounds toward zero (`(-7).midpoint(0) == -3`, *measured*).
- `is_multiple_of` (1.87): `0.is_multiple_of(0) == true`, `6.is_multiple_of(0) == false`, no panic (*measured*).
- `next_multiple_of` and `next_power_of_two` panic in debug and wrap in release on overflow; use the `checked_` forms.
- `cast_signed()` / `cast_unsigned()` (1.87) reinterpret at the same width, unlike `as`, which can change width silently.
- `from_str_radix` and `parse` reject surrounding whitespace and `_`. `-1i32.abs()` is `-(1i32.abs())` = `-1`.
- `to_be_bytes`/`from_le_bytes` are the portable byte conversions; `_ne_bytes` is native-endian. `usize` byte arrays have target-dependent length.

## Floating point

- `round` rounds half away from zero (4.5 → 5); `round_ties_even` rounds half to even. `as` float → int truncates toward zero and saturates; NaN becomes 0 (`f32::NAN as i32 == 0`, `1e20 as i32 == i32::MAX`, `-1.9 as u8 == 0`, *measured*). `to_int_unchecked` is UB on NaN, infinity or out of range.
- `min`/`max` ignore a single NaN; with `+0.0` and `-0.0`, either may be returned. `clamp` panics if `min > max` or either bound is NaN.
- `signum(0.0) == 1.0` and `signum(-0.0) == -1.0`, not 0.
- Precision of `powf`, `powi`, `exp`, `ln`, `log*`, `sin`/`cos`/`tan` and the other transcendental functions is unspecified and may differ between platforms, Rust versions, and even calls. `sqrt`, `mul_add`, `floor`, `ceil`, `round`, `trunc`, `abs`, `rem_euclid` are exact. Do not assert exact bits for the former in tests.
- NaN sign and payload from arithmetic are non-deterministic; `f32::NAN` is guaranteed quiet (1.88). `is_sign_negative()` on a NaN is therefore unreliable.
- Sort floats with `v.sort_by(f32::total_cmp)`. `total_cmp` orders `-0.0 < +0.0` and places NaNs by their sign bit.
- `MIN_POSITIVE` is the smallest **normal** value; subnormals are smaller. `EPSILON` is the gap above 1.0 only.
- `to_bits()` is a transmute, not a numeric cast: `1.0f32.to_bits() != 1`.

## Strings and chars

- `len()` counts bytes. Slicing at a non-character boundary panics ("byte index 1 is not a char boundary"). `str::get(range)` returns `None` instead; `floor_char_boundary(i)` (1.91) truncates to a byte budget safely. There is no grapheme segmentation in std; use a crate.
- `chars()` yields Unicode scalar values, not user-perceived characters.
- `trim`, `split_whitespace` and `char::is_whitespace` use Unicode `White_Space`; `trim_ascii`, `split_ascii_whitespace` and `u8::is_ascii_whitespace` use the WhatWG set, which **excludes** U+000B vertical tab.
- `"bananas".starts_with(&['a', 'b'][..])` is `true`: a char-slice pattern matches any one of the characters.
- `split` keeps empty pieces (`"".split('x')` yields `[""]`; `"a,,b".split(',')` yields an empty middle). `split_terminator` drops one trailing empty piece. `lines()` splits on `\n` and `\r\n`; a lone `\r` stays in the line.
- `trim_matches` takes a `char`, `&[char]` or closure, not `&str`; `trim_start_matches(&str)` removes repeatedly; `strip_prefix` removes once.
- `str::to_lowercase` handles final sigma; `char::to_lowercase` cannot. Neither handles Turkish dotless i. `to_uppercase` can lengthen (`"ß"` → `"SS"`).
- `char::is_numeric` is Unicode-wide (`'½'` is numeric); for ASCII digits use `is_ascii_digit`. `to_digit`/`is_digit` panic if the radix is above 36.
- Build `String`s with `format!` or `push_str`. `s1 + &s2` moves `s1` and reuses its buffer.

## Slices and sorting

- Prefer `sort_unstable*` (in place, no allocation) unless you need stability. Since 1.81, sorting with a comparator that is not a total order **may panic**. All elements remain in the slice even after a panic.
- `sort_by_cached_key` calls the key function once per element; `sort_by_key` calls it O(n log n) times.
- `binary_search` on equal elements returns any matching index; use `partition_point` for the first or last insertion point.
- `is_sorted_by` (1.82) takes a closure returning `bool`, not `Ordering`.
- Fixed-size pieces: `as_chunks::<N>()` (1.88) returns `(&[[T; N]], &[T])`; `array_windows::<N>()` (1.94) yields overlapping `&[T; N]`; `as_array::<N>()` (1.93) returns `Some` only for an exact length. `chunks(0)`, `windows(0)` and `as_chunks::<0>()` panic.
- Two mutable elements at once: `get_disjoint_mut([i, j])` (1.86) returns `Err` on overlap or out of range; or `split_at_mut`.
- `copy_from_slice` and `clone_from_slice` panic on a length mismatch.
- `[expr; N]` needs `Copy` or a constant (`[const { Vec::new() }; N]`); `vec![x; n]` clones `x`, so `vec![Rc::new(1); 5]` is five handles to one value.
- `Default` for arrays is implemented only up to length 32; tuple traits (`PartialEq`, `Debug`, `Hash`, …) only up to arity 12.

## Collections

- The docs' advice: use `Vec` or `HashMap` unless you need ordering (`BTreeMap`), a queue at both ends (`VecDeque`), a priority queue (`BinaryHeap`), or are certain you need a `LinkedList`.
- Collections never shrink automatically; call `shrink_to_fit`.
- `HashMap::insert` with an equal existing key replaces the **value** but keeps the **old key**.
- `HashMap` uses SipHash with a random seed (DoS-resistant). Swap the hasher via `BuildHasher` only after profiling. Build from literals with `HashMap::from([(k, v), …])`. Iteration order is arbitrary.
- Use the entry API for insert-or-update: `*map.entry(k).or_insert(0) += 1;`.
- `BTreeMap::append` may panic if `Ord` is inconsistent (1.96).
- Removing while iterating: `Vec::retain`, `extract_if` (`Vec`/`LinkedList` take a range first, 1.87; `HashMap`/`HashSet` 1.88 and `BTreeMap`/`BTreeSet` 1.91 take only the predicate).

## Formatting and I/O

- Inline arguments: `format!("{name}: {value:>8.2}")`; only identifiers can be captured, not expressions. Every argument must be used.
- `{:?}` output generally ignores width, fill and alignment; format to a `String` first if you need padding. Implement `Debug` for every public type.
- In a `Display` impl, `write!(f, ..)` ignores the caller's width and precision; use `f.pad(..)` or `f.pad_integral(..)` to honour them. Return `Err` only when the `Formatter` did.
- `fmt::from_fn(|f| write!(f, ..))` (1.93) makes an ad-hoc `Display`/`Debug` value without a wrapper type.
- `BufWriter` flushes on drop but silently loses any error; call `flush()` and handle it.
- `println!` panics on a write error and locks stdout per call; for CLI output handling see `building-rust-clis`.
- `fs::File::create_new` creates atomically and fails if the file exists; checking `exists()` first is a race. `fs::exists` (1.81) returns `io::Result<bool>`.
