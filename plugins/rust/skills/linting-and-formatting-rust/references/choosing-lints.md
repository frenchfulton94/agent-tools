# Choosing Clippy lints

Group membership and levels are from `clippy-driver -W help` on clippy 0.1.97 (the 1.97.1 toolchain). Reasons come from each lint's own documentation in the stable lint list, read 2026-10-17. Run `cargo clippy --explain NAME` before enabling a lint: it shows the installed version's text, its "Known issues", and its configuration keys.

## Contents

- [The groups](#the-groups)
- [Pedantic: what to keep and what to allow](#pedantic-what-to-keep-and-what-to-allow)
- [Restriction lints worth picking one by one](#restriction-lints-worth-picking-one-by-one)
- [Restriction lints that contradict each other](#restriction-lints-that-contradict-each-other)
- [Nursery lints that catch real bugs](#nursery-lints-that-catch-real-bugs)
- [The cargo group](#the-cargo-group)
- [Tempting lints with documented problems](#tempting-lints-with-documented-problems)
- [Installed 1.97.1 versus the documentation](#installed-1971-versus-the-documentation)
- [Renamed Clippy lints](#renamed-clippy-lints)

## The groups

| Group | Default | Lints on 1.97.1 | How the Clippy book says to use it |
|---|---|---|---|
| `correctness` | deny | 67 | Leave on. "Should be free of false positives"; allowing one is "not recommended" |
| `suspicious` | warn | 82 | Fix the code. If it is intentional, allow at that site with a reason |
| `complexity`, `perf` | warn | 139, 38 | Apply; allow case by case only for expressiveness |
| `style` | warn | 157 | "The most opinionated warn-by-default group". Allowing a style lint crate-wide is sanctioned |
| `pedantic` | allow | 143 | "Ready to be used in production", with deliberate false positives. Enable as a group and expect `allow`s; Clippy lints itself with it |
| `restriction` | allow | 132 | "Should, *emphatically*, not be enabled as a whole". Pick single lints |
| `nursery` | allow | 52 | "Buggy or need more work". Pick single lints |
| `cargo` | allow | 5 | Manifest metadata for publishing |

`clippy::all` is the five default groups (483 lints). Do not set it (see SKILL.md). The book's tone: "Clippy is meant to be used with a generous sprinkling of `#[allow(..)]`s". A project-wide `allow` of a lint the team disagrees with is normal.

Most lints skip code produced by macro expansion, so silence inside macro output is expected. A proc macro that emits tokens with the input's spans makes generated code look hand-written, and Clippy may lint code the user cannot change. Put `#[expect(clippy::…, reason = "…")]` on the item carrying the derive or attribute.

## Pedantic: what to keep and what to allow

With `pedantic = { level = "warn", priority = -1 }`, keep these. Each finds a real defect or an API mistake:

- `missing_errors_doc`, `missing_panics_doc`: `# Errors` and `# Panics` sections on public fns. Silence one infallible site with `#[expect(clippy::missing_panics_doc, reason = "…")]`, so a panic added later is still caught.
- `return_self_not_must_use`: builders and `with_*` methods need `#[must_use]`. Putting `#[must_use]` on the type covers every method.
- `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap`, `cast_lossless`: silent `as` truncation. Noisy, but this is where real bugs hide. `cast_signed()`/`cast_unsigned()` express intended wrapping.
- `manual_midpoint`: `(a + b) / 2` overflows; `u32::midpoint(a, b)`.
- `match_same_arms`, `match_wildcard_for_single_variants`: copy-paste arms, and a variant added later that a `_` would swallow.
- `ref_option`, `unnecessary_literal_bound`, `unnecessary_debug_formatting`, `format_push_string`, `implicit_clone`, `cloned_instead_of_copied`.
- `ptr_as_ptr`, `ptr_cast_constness`, `ref_as_ptr`, `borrow_as_ptr`: in unsafe-heavy crates, `.cast()`, `cast_mut()`, and `ptr::from_ref` in place of `as`.
- `unsafe_derive_deserialize`, `no_mangle_with_rust_abi`, `non_std_lazy_statics`, `unchecked_time_subtraction`, `case_sensitive_file_extension_comparisons`.
- `ignore_without_reason`, `should_panic_without_expect`: fire only when tests are linted (`--all-targets`).

Commonly allowed when pedantic is on:

- `must_use_candidate`: "Expect many false positives". Never fires in a binary crate.
- `similar_names` (allow it at module or crate scope; allowing it on the reported binding does not work), `too_many_lines`, `needless_pass_by_value`, `single_match_else`, `redundant_else`, `unreadable_literal`.
- `module_name_repetitions` is **not** pedantic. It is restriction, so `module_name_repetitions = "allow"` under pedantic is a no-op.
- `range_plus_one`: its own doc says inclusive ranges "are still slower to run than exclusive ranges", so following it can slow a loop.
- `trivially_copy_pass_by_ref`: a known false positive caused UB in unsafe code (#5953) where the argument's address matters.
- `inline_always`: "False positives, big time". Allow it in crates that measure performance.
- `nonminimal_bool`, `overly_complex_bool_expr`: "a big toll on performance; only enable sporadically". They slow Clippy itself.
- `map_unwrap_or`: `map_or`'s argument order is not execution order, which the doc lists as a known problem.
- `doc_markdown`: keep it, but extend `doc-valid-idents` with `".."` (see `clippy-toml.md`).

## Restriction lints worth picking one by one

Each one costs a line and documents a deliberate house rule.

| Purpose | Lints |
|---|---|
| Keep debug leftovers out of CI | `dbg_macro`, `todo`, `unimplemented`, `print_stdout`, `print_stderr` (libraries) |
| Justify every suppression | `allow_attributes_without_reason`; `allow_attributes` (pushes `allow` to `expect`; it checks outer `#[allow]` only) |
| Unsafe code | `undocumented_unsafe_blocks` (a `// SAFETY:` comment on the lines just above the block), `multiple_unsafe_ops_per_block`, `unnecessary_safety_comment`, `unnecessary_safety_doc` |
| Panic-free code | `unwrap_used`, `expect_used`, `panic`, `indexing_slicing`, `string_slice`, `unwrap_in_result`, `panic_in_result_fn`, `unreachable`. Set `allow-unwrap-in-tests` and its kin, which default to false |
| `no_std` readiness | `std_instead_of_core`, `std_instead_of_alloc`, `alloc_instead_of_core` |
| Published library API | `exhaustive_enums`, `exhaustive_structs`, `partial_pub_fields`, `missing_docs_in_private_items` |
| Error handling | `map_err_ignore` (`map_err(|_| …)` drops the source error), `unused_result_ok` |
| Determinism and arithmetic | `iter_over_hash_type`, `arithmetic_side_effects`, `float_arithmetic`, `as_conversions` (the `cast_*` pedantic lints are usually better), `float_cmp_const` |
| Process and filesystem | `exit`, `create_dir`, `mem_forget` |
| Tests | `redundant_test_prefix`, `tests_outside_test_module`, `cfg_not_test` |
| Unsafe-pointer pitfalls | `as_pointer_underscore`, `default_union_representation` |

A restriction lint can be scoped to part of the code: `#[forbid(clippy::float_arithmetic)]` on one module. `missing_trait_methods` is meant to be enabled on a single `impl`, not crate-wide.

## Restriction lints that contradict each other

Enabling the whole group turns on both halves of each pair. Enable one half at most.

| Pair | One wants | The other wants |
|---|---|---|
| `implicit_return` / `needless_return` (style, on) | `return x;` | `x` |
| `mod_module_files` / `self_named_module_files` | no `mod.rs` | only `mod.rs` |
| `semicolon_inside_block` / `semicolon_outside_block` | `unsafe { f(x); }` | `unsafe { f(x) };` |
| `separated_literal_suffix` / `unseparated_literal_suffix` | `1_i32` | `1i32` |
| `pub_with_shorthand` / `pub_without_shorthand` | `pub(super)` | `pub(in super)` |
| `pattern_type_mismatch` / `ref_patterns` | explicit `ref` and `&` patterns | no `ref` |
| `try_err` / `needless_return_with_question_mark` (style, on) | `return Err(x)` | `Err(x)?` |
| `inline_asm_x86_att_syntax` / `inline_asm_x86_intel_syntax` | AT&T | Intel |
| `big_endian_bytes` / `little_endian_bytes` / `host_endian_bytes` | pick one endianness policy | |
| `redundant_pub_crate` (nursery) / rustc `unreachable_pub` | drop `pub(crate)` | write it |

## Nursery lints that catch real bugs

Enable individually. None is on by default, so a model "fixing Clippy warnings" never sees them.

- `significant_drop_in_scrutinee`: a `MutexGuard` temporary in a `match` scrutinee lives to the end of the `match`, and locking again in an arm deadlocks. Edition 2024 changed `if let`, not `match`.
- `redundant_clone`: MIR-based and conservative.
- `read_zero_byte_vec`: `read(&mut Vec::with_capacity(n))` reads 0 bytes.
- `path_buf_push_overwrite`: `push("/bar")` replaces the whole path.
- `non_send_fields_in_send_ty`: `unsafe impl Send` over an `Rc` field or an unbounded `T`.
- `collection_is_never_read`, `debug_assert_with_mut_call`, `fallible_impl_from`, `suspicious_operation_groupings`, `coerce_container_to_any`, `future_not_send` (async libraries keeping futures `Send`).

Nursery lints with known problems: `missing_const_for_fn` (a `const` added to a `pub fn` cannot be removed without a breaking change, and it needs several runs), `derive_partial_eq_without_eq` (the same commitment for `Eq`), `transmute_undefined_repr` (moved to nursery after "multiple problems"), `needless_pass_by_ref_mut` (breaks callers that pass the fn as a `fn(&mut T)` value).

## The cargo group

`cargo_common_metadata` (the API Guidelines' C-METADATA), `negative_feature_names` (`no-`/`not-` prefixes), `redundant_feature_names` (`use-`/`with-` prefixes, `-support` suffix), `wildcard_dependencies`, `multiple_crate_versions`. The last is often unfixable; list accepted duplicates in `allowed-duplicate-crates`, or allow it.

## Tempting lints with documented problems

- `cognitive_complexity` (restriction): its doc says "We used to think it measured how hard a method is to understand". Use `too_many_lines` or `excessive_nesting` (set `excessive-nesting-threshold`; the default 0 means off).
- `default_numeric_fallback` (restriction): "many false positives and false negatives".
- `min_ident_chars` (restriction): "very noisy". Enable it only for a one-off sweep.
- `float_cmp` (pedantic): right to enable, but not to fix with `f64::EPSILON` as the tolerance. The docs say to use a margin suited to the domain or a relative error.
- `error_impl_error` (restriction): forbids an `Error` type named `Error`, against the `io::Error` convention.
- `arbitrary_source_item_ordering` (restriction): alphabetical enum variant order can cost performance. It can be disabled only per container.
- `string_lit_as_bytes` (nursery): `b"x"` is `&[u8; N]`, not `&[u8]`, and impls differ between them.
- `sliced_string_as_bytes` (perf, on by default): its rewrite of `s[1..5].as_bytes()` drops the char-boundary panic.
- `redundant_pattern_matching` (style, on by default): `if lock().is_ok()` drops the guard before the body, while `if let Ok(_) = lock()` held it.
- `needless_borrow`, `needless_borrows_for_generic_args`, `op_ref`: wrong when the `&T` and `T` impls differ.
- `ptr_arg` (style, on by default): changing `&Vec<T>` to `&[T]` on a public fn breaks callers that hold a `fn(&Vec<T>)` pointer.
- `mutex_atomic`, `mutex_integer` (restriction): false positive alongside a `Condvar`; `AtomicU64` is missing on some 32-bit targets.
- `await_holding_lock`, `await_holding_refcell_ref` (suspicious): false positive after `drop(guard)`. End the guard with a block scope instead.

## Installed 1.97.1 versus the documentation

The lint list on the website describes Clippy 1.99 and later. A diff of the list against `clippy-driver -W help` on 1.97.1 (830 live lints documented, 815 installed) gives:

**In the docs, absent from 1.97.1 (1.98+, unmeasurable here).** An entry for one in `[lints]` gives `warning[E0602]: unknown lint` under Clippy:

| Lint | Group in the docs | Catches |
|---|---|---|
| `block_scrutinee` | suspicious | `if let P = { f() }` on editions ≤2021 |
| `by_ref_peekable_peek` | suspicious | `iter.by_ref().peekable().peek()` consumes the element |
| `for_unbounded_range` | suspicious | `for i in 250u8..` overflows |
| `mismatched_bit_width_type` | suspicious | `u32::BITS - x_u64.leading_zeros()` |
| `manual_isolate_lowest_one`, `nonnull_unchecked_on_box_ptr`, `unnecessary_unwrap_unchecked`, `map_or_identity` | complexity | `x & x.wrapping_neg()`; `NonNull::new_unchecked(Box::into_raw(b))`; `from_utf8(..).unwrap_unchecked()`; `map_or(d, |v| v)` |
| `chunks_exact_to_as_chunks` | style | `chunks_exact(N)` with a constant `N` |
| `assert_is_empty`, `manual_bit_width`, `unused_async_trait_impl`, `with_capacity_zero` | pedantic | `assert!(v.is_empty())`; `T::BITS - x.leading_zeros()`; an `async fn` impl with no `.await`; `with_capacity(0)` |
| `definition_in_module_root`, `rest_pattern_accessible_field`, `unnecessary_rest_pattern` | restriction | definitions in `mod.rs`; `..` in struct patterns |

`map_or_identity` (docs: "Added in 1.97.0") and `chunks_exact_to_as_chunks` ("1.93.0") are absent from 1.97.1 despite their dates, so filter by the installed toolchain, never by "Added in".

**Group or level differs**, measured:

- `nonstandard_macro_braces`: nursery, allow on 1.97.1; **style, warn** in the docs. A toolchain bump turns it on.
- `empty_enums`: pedantic on 1.97.1; nursery in the docs, so newer `pedantic` stops firing it.
- `unnecessary_get_then_check`: suspicious on 1.97.1; complexity in the docs. Both warn.
- `from_iter_instead_of_collect`: a live pedantic lint on 1.97.1; deprecated in the docs (1.98, "proved problematic").

## Renamed Clippy lints

An old name in `[lints]` or an attribute still enables the new lint, with a `renamed_and_removed_lints` warning (measured: `unchecked_duration_subtraction` enabled `unchecked_time_subtraction`). Old → new:

`stutter` → `module_name_repetitions`; `integer_arithmetic` → `arithmetic_side_effects`; `cyclomatic_complexity` → `cognitive_complexity`; `blacklisted_name` → `disallowed_names`; `disallowed_method`, `disallowed_type` → `disallowed_methods`, `disallowed_types`; `option_unwrap_used`, `result_unwrap_used` → `unwrap_used`; `option_expect_used`, `result_expect_used` → `expect_used`; `logic_bug` → `overly_complex_bool_expr`; `needless_if` → `needless_ifs`; `box_vec` → `box_collection`; `unwrap_or_else_default` → `unwrap_or_default`; `identity_conversion` → `useless_conversion`; `if_let_redundant_pattern_matching` → `redundant_pattern_matching`; `blocks_in_if_conditions` → `blocks_in_conditions`; `filter_map` → `manual_filter_map`; `find_map` → `manual_find_map`; `option_map_unwrap_or`, `result_map_unwrap_or_else` → `map_unwrap_or`; `zero_width_space` → `invisible_characters`; `derive_hash_xor_eq` → `derived_hash_with_manual_eq`; `incorrect_clone_impl_on_copy_type` → `non_canonical_clone_impl`; `incorrect_partial_ord_impl_on_ord_type` → `non_canonical_partial_ord_impl`; `to_string_in_display` → `recursive_format_impl`; `eval_order_dependence` → `mixed_read_write_in_expression`; `thread_local_initializer_can_be_made_const` → `missing_const_for_thread_local`.

Removed lints warn "has been removed" and do nothing: `string_to_string` (use `implicit_clone`), `option_map_or_err_ok` (use `manual_ok_or`), `match_on_vec_items` (use `indexing_slicing`), `pub_enum_variant_names` and `wrong_pub_self_convention` (use `enum_variant_names` and `wrong_self_convention` with `avoid-breaking-exported-api = false`).
