# Unsafe code and undefined behaviour

From the Rust Reference (1.99), the std `ptr`, `pin`, `primitive` and `ffi` docs, and the Book. Results marked *measured* were compiled on rustc 1.97.1. The Reference states that Rust's memory model is "incomplete and not fully decided": treat everything here as necessary, not sufficient, and read the Rustonomicon for depth.

## Contents

- [What `unsafe` permits](#what-unsafe-permits)
- [Writing unsafe code](#writing-unsafe-code)
- [Behaviour considered undefined](#behaviour-considered-undefined)
- [Validity invariants](#validity-invariants)
- [Pointers, provenance and raw borrows](#pointers-provenance-and-raw-borrows)
- [Statics, unions, `MaybeUninit`, `transmute`](#statics-unions-maybeuninit-transmute)
- [FFI](#ffi)
- [Target features, inline and naked assembly](#target-features-inline-and-naked-assembly)
- [Constant evaluation](#constant-evaluation)
- [Lints and tools that catch UB](#lints-and-tools-that-catch-ub)
- [Not undefined behaviour](#not-undefined-behaviour)

## What `unsafe` permits

The complete list of operations that need an unsafe context:

1. Dereferencing a raw pointer.
2. Reading or writing a `static mut`, or any static declared in an `extern` block (unless marked `safe`).
3. Reading a union field (writing one is safe).
4. Calling an `unsafe fn`, including foreign functions not marked `safe`.
5. Calling a safe `#[target_feature]` function from a function that does not enable the same features.
6. Implementing an `unsafe trait` (`unsafe impl Send for T {}`).
7. Declaring an `extern` block (`unsafe extern`, required on edition 2024).
8. Applying an unsafe attribute: `#[unsafe(no_mangle)]`, `#[unsafe(export_name)]`, `#[unsafe(link_section)]`, `#[unsafe(naked)]`.

`unsafe` does not switch off the borrow checker or any other check. `unsafe fn` and `unsafe trait` **declare** an obligation; `unsafe { }`, `unsafe impl`, `unsafe extern` and `#[unsafe(..)]` **discharge** one. On edition 2024 an `unsafe fn` body is a safe context (warning `unsafe_op_in_unsafe_fn`, E0133).

Taking a raw pointer with `&raw const`/`&raw mut` is safe, including of a `static mut` or of `*ptr` (1.84). Only the dereference needs `unsafe`.

## Writing unsafe code

- Keep unsafe blocks small, and wrap them in a safe function whose checks make every call sound (the Book's `split_at_mut`: `assert!(mid <= len)`, then `slice::from_raw_parts_mut(ptr, mid)` and `ptr.add(mid)`).
- Document an `unsafe fn` or `unsafe trait` with a `# Safety` section stating what the caller or implementer must guarantee. Put a `// SAFETY:` comment before each unsafe block saying why those conditions hold.
- Soundness is a property of the safe API: code is unsound if any safe caller can trigger UB through it. A safe function taking a raw integer and using it as a file descriptor is unsound (I/O safety: use `OwnedFd` / `BorrowedFd<'_>`).
- Unsafe code may rely on `assert!` for its invariants but not on `debug_assert!`, which is compiled out in release.
- Unsafe code must not rely on a destructor running, on a `Hash`/`Eq`/`Ord` implementation being correct, or on any property of `f32::algebraic_*` results (1.98+).

## Behaviour considered undefined

The Reference's list, which "is not exhaustive; it may grow or shrink":

- **Data races.**
- **Accessing a dangling or misaligned place.** Misalignment is judged by the pointer actually dereferenced: with `ptr: *const S` and `S` 8-aligned, `(*ptr).f` needs `ptr` 8-aligned even when `f: u8`. A zero-sized access is never dangling, even through null, but must still be aligned.
- **An out-of-bounds place projection** (field, tuple-index or array-index past the allocation, by the same rules as `offset`).
- **Breaking the aliasing rules.** While a `&T` is live, its memory is not mutated except inside `UnsafeCell`. While a `&mut T` is live, its memory is accessed only through pointers derived from it. `Box<T>` counts as a `&'static mut T`. A reference passed to a function stays live for the whole call (unless it is a `&T` to something containing `UnsafeCell`). The rules apply to references in private fields too.
- **Mutating immutable bytes:** behind a shared reference, owned by an immutable binding or static, or produced by constant promotion. Writing the same value back still counts.
- **Calling a function with the wrong ABI, or unwinding out of a function whose ABI does not allow it.**
- **Producing an invalid value** (see the next section). "Producing" means assigning, reading from a place, passing or returning.
- **Executing code compiled with target features the CPU lacks.**
- **Misusing inline assembly**, including unwinding out of `asm!`.
- **Violating runtime assumptions**, for example freeing a stack frame without running its destructors (`longjmp` across Rust frames).
- **UB anywhere is UB everywhere**, across FFI in both directions.

## Validity invariants

A value must always satisfy these, even if never used again:

- `bool` is `0` or `1`. `char` is at most `0x10FFFF` and not a surrogate (`0xD800..=0xDFFF`); `char::from_u32_unchecked(0x110000)` is UB.
- Integers, floats and raw pointers must be initialised. An uninitialised byte is not a valid `u8`.
- References and `Box` are aligned, non-null, not dangling, and point to a valid value. Creating one is enough: `unsafe { &*(0 as *const u8) }` is UB even if unused.
- `fn` pointers and `NonNull` are non-null; `NonZero` is non-zero.
- An enum has a valid discriminant and a valid active variant; a struct, tuple or array has every field valid. A field-less Rust enum holding a value outside its discriminants is UB, which is why a C `enum` should usually be modelled as a newtype over an integer.
- `str` only needs initialised bytes, like `[u8]`. UTF-8 is a **library** invariant: building a non-UTF-8 `&str` is not immediately UB, but any `str` method may then cause UB.
- Wide-pointer metadata: a slice length such that the total size is at most `isize::MAX`; a vtable that matches the trait.
- `!` has no values.
- Uninitialised memory may be read only through unions and padding, or as `MaybeUninit<T>`.

## Pointers, provenance and raw borrows

- **Provenance.** A pointer carries the right to access a specific allocation, and pointers derived from it inherit it. Comparing pointers compares addresses only; dereferencing needs provenance.
- **Strict provenance APIs (1.84)** are preferred: `ptr.addr()` (an integer that does *not* expose provenance), `ptr.with_addr(a)`, `ptr.map_addr(|a| a | TAG)` for tagged pointers, `ptr::without_provenance(addr)` for sentinels that are never dereferenced, and `ptr::dangling()` / `NonNull::dangling()` for well-aligned non-null placeholders.
- **Exposed provenance** (`ptr.expose_provenance()`, `ptr::with_exposed_provenance(addr)`) is what `as` casts between pointers and integers do. Use it only for MMIO, bare metal or legacy interfaces.
- Integer-to-pointer `transmute` yields a pointer with no provenance that may never be dereferenced (warn `integer_to_ptr_transmutes`, 1.91). Whether transmuting a pointer to an integer type is valid is undecided.
- `ptr.add(n)` / `offset` are UB unless the whole range stays within one allocation (zero offsets are always fine, and `vec.as_ptr().add(vec.len())` is allowed). `wrapping_add` / `wrapping_offset` are always safe to compute; the result keeps the original provenance and may only be dereferenced inside the original allocation.
- `offset_from` requires both pointers in the same allocation and a distance that is a multiple of `size_of::<T>()`. `offset_from_unsigned` (1.87) additionally requires `self >= origin`.
- Prefer `.cast::<U>()`, `.cast_mut()`, `.cast_const()` to `as` between pointer types; they cannot change mutability or pointee by accident.
- `ptr.as_ref()` returns `Option<&T>`; `as_ref_unchecked` / `as_mut_unchecked` (1.95) return the reference directly when you already know the pointer is valid.
- **Raw borrows** `&raw const place` and `&raw mut place` (1.82) create a pointer without an intermediate reference. They are required for:
  - a `#[repr(packed)]` field: `&p.field` is error E0793 "reference to field of packed struct is unaligned" (*measured*); read it with `(&raw const p.field).read_unaligned()` or copy it with `{ p.field }`;
  - a field of uninitialised memory: `&raw mut (*uninit.as_mut_ptr()).field`;
  - any place where a reference would assert aliasing you cannot guarantee.
- `&raw mut (*ptr)[..16]` silently creates `&mut *ptr` through `IndexMut` (deny `dangerous_implicit_autorefs`). Write the reference explicitly or use `ptr::slice_from_raw_parts_mut`.
- A slice pointer must be non-null and aligned even when empty: use `NonNull::dangling()` for zero length, never null. `slice::from_raw_parts(ptr::null(), 0)` is UB (deny `invalid_null_arguments`).
- `slice.get_unchecked(len)` is UB even if the result is immediately turned into a pointer.

## Statics, unions, `MaybeUninit`, `transmute`

- **`static mut`**: every access is unsafe, any reference to it is denied on edition 2024, and access from two threads is a data race. Prefer a plain `static` holding an atomic, `Mutex`, `OnceLock` or `LazyLock`. If you must, go through `&raw const X` / `&raw mut X`.
- A plain `static` must be `Sync`, has one address, and is never dropped. A `const` is inlined at each use and may have a different address each time. A static inside a generic function is one static shared by every instantiation.
- **Unions**: fields are `Copy`, references, `ManuallyDrop<T>`, or tuples and arrays of those. Writing a field is safe, reading is unsafe, and there is no "active field": every read reinterprets the bytes. Without `#[repr(C)]` fields need not be at offset 0.
- **`MaybeUninit<T>`** is the only way to hold uninitialised data. `mem::uninitialized` is deprecated and UB for almost every type. Recent helpers: `Box::new_uninit` / `new_uninit_slice` (1.82), `Box::new_zeroed` (1.92), and on `[MaybeUninit<T>]` `write_copy_of_slice`, `write_clone_of_slice`, `assume_init_ref`, `assume_init_mut`, `assume_init_drop` (1.93).
- **`transmute`** requires equal sizes (checked at compile time) and a valid result. `&T` → `&mut T` is always UB (deny `mutable_transmutes`), as is writing through `&T as *const T as *mut T` without `UnsafeCell` (deny `invalid_reference_casting`). `UnsafeCell` is the only way to mutate through a shared reference.
- `Option<T>` has the same size and ABI as `T` for `&T`, `&mut T`, `Box<T>`, `NonNull<T>`, `NonZero*`, `fn` pointers, and `#[repr(transparent)]` wrappers of them; all-zero is `None`. `Result<T, E>` gets the same layout when one side qualifies and the other is a 1-ZST such as `()`.

## FFI

- Declare imports in `unsafe extern "C" { .. }` and always write the ABI: `extern` with no ABI string is deprecated (warn `missing_abi`, 1.86). Mark an import `safe fn` only when every possible argument is sound.
- ABIs available everywhere: `"Rust"` (no stability guarantee), `"C"`, `"system"` (stdcall on 32-bit Windows, C elsewhere; use it for the Windows API), and the unwinding variants `"C-unwind"` and `"system-unwind"`.
- **Unwinding across FFI.** A Rust panic reaching an `extern "C"` boundary aborts (since 1.81). A foreign exception (C++ `throw`, another Rust std's panic) unwinding into a non-`-unwind` function is UB. Use `extern "C-unwind"` for any foreign function that may unwind, in either direction. Lint `ffi_unwind_calls` (allow) finds calls to `-unwind` functions.
- Exporting: `#[unsafe(no_mangle)] pub extern "C" fn f()`. A nullable callback is `Option<extern "C" fn(..)>`.
- `Box<T>` is ABI-compatible with a C `T*` and fine in Rust functions exported to C, but do not put `Box<T>` in the signature of a C function imported into Rust; mirror the C types.
- Passing a value through a function pointer whose signature differs from the definition is UB unless the types are ABI-compatible. `i32`/`u32`, `bool`/`u8` and a non-transparent `struct Foo(u32)`/`u32` are **not** guaranteed compatible.
- `#[repr(C)]` enum discriminants must fit a C `int` or `unsigned int` (future-compatibility warning since 1.93); otherwise use `#[repr(i64)]` and similar.
- Strings: `CString` (owned, NUL-terminated) for Rust → C; `CStr` for C → Rust; `c"literal"` is a `&'static CStr` (edition 2021+). Rust `char` is not C `char`; use `core::ffi::c_char`. `std::os::raw` is kept for compatibility; use `core::ffi`.
- **C-variadic functions.** Declaring a variadic import (`fn printf(fmt: *const c_char, ...) -> c_int;`) is stable for `"C"` and `"cdecl"`, and since 1.91–1.93 also for `sysv64`, `win64`, `efiapi`, `aapcs` and `system`. **Defining** one in Rust is documented in the 1.99 Reference (with `VaList::next_arg`) but is E0658 "C-variadic functions are unstable" on 1.97 (*measured*).

## Target features, inline and naked assembly

- `#[target_feature(enable = "avx2")]` on a safe function (allowed since 1.86) makes it safe to call only from functions with the same features; elsewhere the call needs `unsafe` (error[E0133] "call to function `f` with `#[target_feature]` is unsafe and requires unsafe block", *measured*). Enabling the feature crate-wide with `-C target-feature` does not change this rule.
- Guard such calls with runtime detection: `if is_x86_feature_detected!("avx2") { unsafe { f() } }` (also `is_aarch64_feature_detected!`, and loongarch, riscv and s390x variants). These macros are compile errors on other architectures, so `#[cfg]`-gate them.
- `#[inline(always)]` with `#[target_feature]` is an error. A `#[target_feature]` function does not implement the `Fn` traits.
- `-C target-feature` does not rebuild std; mixing ABI-affecting features (such as `+soft-float` or `-sse` on x86) with the prebuilt std can crash.
- Most `std::arch` intrinsics without pointer arguments are safe to call from a function that enables their feature (1.87).
- **`asm!`** (`core::arch::asm`): operands are named or positional, with no implicit capture of variables; non-output registers must be restored; unwinding out of `asm!` is UB; the block may be duplicated or removed, so use numeric local labels (`2:`, `jmp 2f`). x86 uses Intel syntax unless `options(att_syntax)`. `pure` needs `nomem` or `readonly`.
- **Naked functions** (1.88): `#[unsafe(naked)] pub extern "C" fn f() -> u32 { core::arch::naked_asm!("mov w0, #42", "ret") }`. The body is exactly one `naked_asm!`; there is no prologue, so the code must follow the calling convention and must not fall off the end. Not allowed with the `"Rust"` ABI.

## Constant evaluation

- Const contexts: array lengths and repeat counts, `const`/`static` initialisers, enum discriminants, const generic arguments, and `const { }` blocks. Elsewhere a `const fn` runs at runtime like any function.
- Allowed in const evaluation: `let`, assignment, `if`, `match`, `loop`, `while`, float arithmetic (1.82), `&mut` and `*mut` (1.83), raw-pointer dereference, calls to `const fn`. Not allowed: `for` loops (E0015 "cannot use `for` loop on `&[u32]` in constant functions", *measured*; use `while` with an index), calls to non-`const` trait methods, heap allocation, casting a pointer to an integer.
- Overflow or an out-of-bounds index in a const context is a compile error. Elsewhere, a statically known overflow is the deny-by-default `arithmetic_overflow` / `unconditional_panic` lint and otherwise a runtime panic.
- Writing to a static from const evaluation is never allowed; reading a `static mut` or an interior-mutable static only inside another static's initialiser.
- `const C: &mut u8 = &mut 0;` and `const C: &AtomicU8 = &AtomicU8::new(0);` are errors: a mutable or interior-mutable borrow cannot be extended to `'static`.
- Const evaluation happens in the target's environment (`usize` is the target's width). NaN payloads from const evaluation may differ from runtime ones.

## Lints and tools that catch UB

Deny by default on 1.97 (*measured* with `rustc -W help`): `invalid_reference_casting`, `mutable_transmutes`, `invalid_null_arguments`, `deref_nullptr`, `dangerous_implicit_autorefs`, `invalid_from_utf8_unchecked`, `undropped_manually_drops`, `never_type_fallback_flowing_into_unsafe`. Warn: `static_mut_refs` (deny on 2024), `dangling_pointers_from_locals`, `integer_to_ptr_transmutes`, `function_casts_as_integer`. The 1.99 docs also list `raw_borrows_via_references` (allow; flags `&(*x).0 as *const _`), which is absent from 1.97 (**1.98+**).

**Miri** interprets the program and reports UB on the paths it executes: `rustup +nightly component add miri`, then `cargo +nightly miri test` (nightly only). Useful flags in `MIRIFLAGS`: `-Zmiri-strict-provenance`, `-Zmiri-backtrace=full`. A clean Miri run proves only that the executed paths had no detected UB.

## Not undefined behaviour

Deadlocks, memory leaks, `mem::forget`, exiting without running destructors, integer overflow (it panics with debug assertions and wraps otherwise; `i32::MIN / -1` panics in every build, *measured*), logic errors from inconsistent `Hash`/`Eq`/`Ord`, and mutating a key inside a `HashMap` or `BTreeMap`. These can give wrong results, panics or aborts, but never UB.
