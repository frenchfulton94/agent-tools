# `clippy.toml` keys and defaults

Keys are kebab-case. The values below are the Clippy book's, checked against `cargo clippy --explain` on clippy 0.1.97 (the 1.97.1 toolchain), and they matched except where marked. A key the installed Clippy does not know is a hard error that stops the lint run. To list the keys a toolchain accepts, write a bogus key and read the "expected one of" list in the error. To see one lint's keys and defaults, run `cargo clippy --explain LINT`.

## Contents

- [Syntax that trips people](#syntax-that-trips-people)
- [Keys by purpose](#keys-by-purpose)
- [Keys newer than 1.97](#keys-newer-than-197)

## Syntax that trips people

- **Lists replace their default.** Add `".."` to keep it: `doc-valid-idents = ["MyCorp", ".."]`. Measured: `disallowed-names = ["toto"]` stopped flagging the default `foo`, and `["toto", ".."]` flagged both. Keys with a default to keep: `doc-valid-idents`, `disallowed-names`, `allowed-idents-below-min-chars`, `allowed-prefixes`, `allow-renamed-params-for`.
- **`msrv` is a string**: `msrv = "1.70"`. Unquoted, TOML reads a float (`1.7`) and Clippy fails.
- **`disallowed-methods`, `-types`, `-macros`, `-fields`** take a path string or an inline table:

  ```toml
  disallowed-methods = [
      { path = "std::env::var", reason = "read configuration through Settings", replacement = "crate::settings::get" },
      "std::process::exit",
  ]
  ```

  The warning then reads `help: read configuration through Settings: crate::settings::get`. A path that resolves to nothing is a **warning** on 1.97 ("does not refer to a reachable function"; the book says error). Add `allow-invalid = true` to an entry for a path that exists only under some features or targets. The four lints are warn by default, so the list is all it takes.
- **`await-holding-invalid-types`** entries are `"path"` or `{ path, reason }`. `enforced-import-renames` entries are `{ path = "serde_json::Value", rename = "JsonValue" }`. `standard-macro-braces` entries are `{ name = "vec", brace = "[" }`; also list the `crate::vec` form when the macro can be called by path.
- **`arithmetic-side-effects-allowed-binary`** takes pairs, which are asymmetric, and `"*"` is a wildcard: `[["SomeType", "*"]]`.
- **`module-item-order-groupings`** must name every item kind exactly once, or loading the file fails.

## Keys by purpose

**API and exported items**

| Key | Default | Effect |
|---|---|---|
| `avoid-breaking-exported-api` | `true` | Silences 19 lints on a library's public items: `box_collection`, `enum_variant_names`, `large_types_passed_by_value`, `linkedlist`, `needless_pass_by_ref_mut`, `option_option`, `owned_cow`, `rc_buffer`, `rc_mutex`, `redundant_allocation`, `ref_option`, `single_call_fn`, `trivially_copy_pass_by_ref`, `unnecessary_box_returns`, `unnecessary_wraps`, `unused_self`, `upper_case_acronyms`, `vec_box`, `wrong_self_convention`. Set `false` for a library with no outside users |
| `check-private-items` | `false` | Extends `missing_errors_doc`, `missing_panics_doc`, `missing_safety_doc`, `unnecessary_safety_doc` to private items |
| `missing-docs-in-crate-items` | `false` | `missing_docs_in_private_items` checks only crate-visible items such as `pub(crate)` |
| `missing-docs-allow-unused` | `false` | Exempts `_`-prefixed fields from `missing_docs_in_private_items` |
| `pub-underscore-fields-behavior` | `"PubliclyExported"` | `pub_underscore_fields` scope (or `"AllPubFields"`) |
| `upper-case-acronyms-aggressive` | `false` | By default only all-caps names (`HTTP`) fire, not `HTTPResponse` |
| `allow-renamed-params-for` | `From`, `TryFrom`, `FromStr` (`..` appends) | Traits whose impls may rename parameters (`renamed_function_params`) |
| `allowed-prefixes` | `to as into from try_into try_from` (`..` appends) | `module_name_repetitions` |
| `allow-exact-repetitions` | `true` | `module_name_repetitions` skips an item named exactly like its module |
| `allow-private-module-inception` | `false` | `module_inception` |
| `enum-variant-name-threshold` | `3` | `enum_variant_names` |
| `inherent-impl-lint-scope` | `"crate"` (`"file"`, `"module"`) | `multiple_inherent_impl` |

**Panic-free and test exemptions** (all `*-in-tests` default to `false`, so the restriction lints also flag tests)

| Key | Default | Lints |
|---|---|---|
| `allow-unwrap-in-tests`, `allow-expect-in-tests` | `false` | `unwrap_used`, `expect_used` |
| `allow-unwrap-in-consts`, `allow-expect-in-consts` | `true` | same |
| `allow-unwrap-types` | `[]`, e.g. `["std::sync::LockResult"]` | `unwrap_used`, `expect_used` |
| `allow-panic-in-tests` | `false` | `panic` |
| `allow-print-in-tests` | `false` | `print_stdout`, `print_stderr` |
| `allow-dbg-in-tests` | `false` | `dbg_macro` |
| `allow-indexing-slicing-in-tests`, `suppress-restriction-lint-in-const` | `false` | `indexing_slicing` |
| `allow-useless-vec-in-tests` | `false` | `useless_vec` |
| `allow-large-stack-frames-in-tests` | `true` | `large_stack_frames` |
| `check-incompatible-msrv-in-tests` | `false` | `incompatible_msrv` ignores test code by default |

**Thresholds**

| Key | Default | Lint |
|---|---|---|
| `too-many-arguments-threshold` | `7` | `too_many_arguments` (complexity, on) |
| `type-complexity-threshold` | `250` | `type_complexity` (complexity, on) |
| `large-error-threshold`, `large-error-ignored` | `128` bytes, `[]` | `result_large_err` (perf, on) |
| `enum-variant-size-threshold` | `200` bytes | `large_enum_variant` (perf, on) |
| `too-many-lines-threshold` | `100` | `too_many_lines` (pedantic) |
| `cognitive-complexity-threshold` | `25` | `cognitive_complexity` (restriction) |
| `excessive-nesting-threshold` | `0` (off) | `excessive_nesting`: set a value to turn it on |
| `max-struct-bools`, `max-fn-params-bools` | `3`, `3` | `struct_excessive_bools`, `fn_params_excessive_bools` |
| `struct-field-name-threshold` | `3` | `struct_field_names` |
| `max-trait-bounds` | `3` | `type_repetition_in_bounds` |
| `single-char-binding-names-threshold` | `4` | `many_single_char_names` |
| `min-ident-chars-threshold`, `allowed-idents-below-min-chars` | `1`, `i j x y z w n` (`..` appends) | `min_ident_chars` |
| `pass-by-value-size-limit` | `256` | `large_types_passed_by_value` |
| `trivial-copy-size-limit` | target pointer width | `trivially_copy_pass_by_ref` |
| `too-large-for-stack` | `200` | `boxed_local`, `useless_vec` |
| `vec-box-size-threshold` | `4096` | `vec_box` |
| `unnecessary-box-size` | `128` | `unnecessary_box_returns` |
| `array-size-threshold` | `16384` | `large_const_arrays`, `large_stack_arrays` |
| `future-size-threshold` | `16384` | `large_futures` |
| `stack-size-threshold` | `512000` | `large_stack_frames` |
| `max-include-file-size` | `1000000` | `large_include_file` |
| `literal-representation-threshold` | `16384` | `decimal_literal_representation` |
| `const-literal-digits-threshold` | `30` | `excessive_precision` |
| `verbose-bit-mask-threshold` | `1` | `verbose_bit_mask` |
| `max-suggested-slice-pattern-length` | `3` | `index_refutable_slice` |
| `absolute-paths-max-segments`, `absolute-paths-allowed-crates` | `2`, `[]` | `absolute_paths` |

**Lists of names and types**

| Key | Default | Lint |
|---|---|---|
| `doc-valid-idents` | ~80 words (GitHub, JavaScript, macOS, IPv4, OAuth, …); `..` appends. 1.97 lacks the docs' SQLite, MySQL, PostgreSQL, MariaDB, MongoDB | `doc_markdown` |
| `disallowed-names` | `foo baz quux` (`bar` deliberately absent; `..` appends) | `disallowed_names` |
| `disallowed-methods`, `-types`, `-macros`, `-fields` | `[]` | `disallowed_*` |
| `ignore-interior-mutability` | `["bytes::Bytes"]` | `mutable_key_type`, `borrow_interior_mutable_const`, `declare_interior_mutable_const`, `ifs_same_cond`. Add types whose `Hash`/`Ord` ignore the mutable part |
| `await-holding-invalid-types` | `[]` | `await_holding_invalid_type` |
| `enforced-import-renames` | `[]` | `missing_enforced_import_renames` |
| `allowed-wildcard-imports`, `warn-on-all-wildcard-imports` | `[]`, `false` | `wildcard_imports`. Paths with a `prelude` segment are always allowed, as are `pub use` and `use super::*` in test modules, unless the second key is `true` |
| `allowed-duplicate-crates` | `[]` | `multiple_crate_versions` |
| `allowed-scripts` | `["Latin"]` | `disallowed_script_idents` |
| `allowed-dotfiles` | `[]` | `path_ends_with_ext` |
| `arithmetic-side-effects-allowed`, `-allowed-binary`, `-allowed-unary` | `[]` | `arithmetic_side_effects` |
| `standard-macro-braces` | `[]` | `nonstandard_macro_braces` |

**Behaviour switches**

| Key | Default | Effect |
|---|---|---|
| `msrv` | `rust-version` from `Cargo.toml` | About 85 lints stay silent or change their suggestion below it |
| `allow-mixed-uninlined-format-args` | `true` | `uninlined_format_args` skips `format!("{} {}", a, foo.bar)`, where not every argument can be inlined |
| `allow-comparison-to-zero` | `true` | `modulo_arithmetic` skips `x % n == 0` |
| `allow-one-hash-in-raw-strings` | `false` | `needless_raw_string_hashes` |
| `accept-comment-above-attributes`, `accept-comment-above-statement` | `true`, `true` | Where `undocumented_unsafe_blocks` accepts the `// SAFETY:` comment |
| `warn-unsafe-macro-metavars-in-private-macros` | `false` | `macro_metavars_in_unsafe` checks only exported macros by default |
| `enable-raw-pointer-heuristic-for-send` | `true` | `non_send_fields_in_send_ty` |
| `enforce-iter-loop-reborrow` | `false` | `explicit_iter_loop` |
| `check-inconsistent-struct-field-initializers` | `false` | `inconsistent_struct_constructor`. Reordering initializers can change behaviour or break borrow checking |
| `lint-commented-code` | `false` | `collapsible_if`, `collapsible_else_if` |
| `matches-for-let-else` | `"WellKnownTypes"` (`"AllTypes"`, `"Never"`) | `manual_let_else`: which `match` expressions it suggests rewriting |
| `recursive-self-in-type-definitions` | `true` | `use_self` |
| `unreadable-literal-lint-fractions` | `true` | `unreadable_literal` |
| `semicolon-inside-block-ignore-singleline`, `semicolon-outside-block-ignore-multiline` | `false`, `false` | the two `semicolon_*_block` lints |
| `source-item-ordering`, `module-item-order-groupings`, `module-items-ordered-within-groupings`, `trait-assoc-item-kinds-order` | see `--explain arbitrary_source_item_ordering` | `arbitrary_source_item_ordering` |

`cargo-ignore-publish` and `third-party` are accepted but internal.

## Keys newer than 1.97

The book documents these, and clippy 1.97.1 rejects each as an unknown field, failing the run (**1.98+**): `check-grouped-late-init` (`needless_late_init`, default `true`), `min-ident-chars-lint-trait-impl` (`min_ident_chars`, default `false`), and `trait-impl-item-order` (`arbitrary_source_item_ordering`, default `"alphabetical"`). In a repository whose toolchain is not pinned, leave them out until `cargo clippy --version` shows 1.98 or later.
