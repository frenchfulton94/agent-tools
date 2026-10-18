# rustfmt options and the Rust Style Guide

Option lists and every behaviour marked measured come from rustfmt 1.9.0-stable (the 1.97.1 toolchain): each option was set in a `rustfmt.toml` and checked for the nightly-channel warning. Style rules come from the Rust Style Guide, read in full on 2026-10-17.

## Contents

- [Stable options](#stable-options)
- [Nightly-only options](#nightly-only-options)
- [Editions and style editions](#editions-and-style-editions)
- [Skipping code](#skipping-code)
- [Style Guide rules rustfmt does not apply](#style-guide-rules-rustfmt-does-not-apply)
- [Naming](#naming)
- [`Cargo.toml` conventions](#cargotoml-conventions)

## Stable options

These 28 are all that stable rustfmt accepts. `rustfmt --help=config` prints them with their defaults; `rustfmt --print-config default` also prints the unstable ones without saying which is which.

| Option | Default | Notes |
|---|---|---|
| `edition` | `2015` | Parsing edition for bare `rustfmt`. `cargo fmt` overrides it with `Cargo.toml`'s edition |
| `style_edition` | follows `edition` | `2015`, `2018`, `2021`, `2024`. `2027` is listed as unstable. Overrides both editions |
| `max_width` | `100` | Line width |
| `use_small_heuristics` | `"Default"` | `"Max"` lets constructs use the full `max_width` before breaking; `"Off"` turns the "small" heuristics off |
| `fn_call_width`, `attr_fn_like_width`, `struct_lit_width`, `struct_variant_width`, `array_width`, `chain_width` | `60`, `70`, `18`, `35`, `60`, `60` | Per-construct widths before breaking vertically |
| `single_line_if_else_max_width`, `single_line_let_else_max_width` | `50`, `50` | |
| `short_array_element_width_threshold` | `10` | Arrays of elements this short pack several per line |
| `hard_tabs`, `tab_spaces` | `false`, `4` | |
| `newline_style` | `"Auto"` | `"Unix"` pins LF regardless of the checkout |
| `reorder_imports`, `reorder_modules` | `true`, `true` | Within a group only; see below |
| `remove_nested_parens` | `true` | `((x))` → `(x)`. Never touches single parentheses |
| `match_arm_leading_pipes` | `"Never"` | Removes a leading `\|` |
| `match_block_trailing_comma` | `false` | |
| `fn_params_layout` | `"Tall"` | `"Compressed"`, `"Vertical"` |
| `merge_derives` | `true` | Merges **adjacent** `#[derive]`s only |
| `use_field_init_shorthand`, `use_try_shorthand` | `false`, `false` | `Foo { a: a }` → `Foo { a }`; `try!(x)` → `x?` |
| `force_explicit_abi` | `true` | `extern fn` → `extern "C" fn` |
| `disable_all_formatting` | `false` | |
| `print_misformatted_file_names` | `false` | Same as `-l` |

`rustfmt.toml` and `.rustfmt.toml` are found by walking up from each file. `.rustfmt.toml` wins silently when both exist. An unknown key warns and is ignored (exit 0). A value of the wrong type is an error (exit 1).

## Nightly-only options

On stable each prints "Warning: can't set `X = …`, unstable features are only available in nightly channel", exits 0, and is ignored, so a CI that only checks the exit code never notices. The ones people reach for:

- Imports: `imports_granularity` (merge or split `use`), `group_imports` (std / external / crate groups), `imports_layout`, `imports_indent`.
- Comments and docs: `wrap_comments`, `comment_width`, `normalize_comments`, `normalize_doc_attributes`, `format_code_in_doc_comments`, `doc_comment_code_block_width`.
- Literals and strings: `hex_literal_case`, `float_literal_trailing_zero`, `format_strings`.
- Layout: `brace_style`, `control_brace_style`, `indent_style`, `trailing_comma`, `trailing_semicolon`, `where_single_line`, `fn_single_line`, `struct_lit_single_line`, `empty_item_single_line`, `overflow_delimited_expr`, `combine_control_expr`, `match_arm_blocks`, `match_arm_indent`, `force_multiline_blocks`, `binop_separator`, `type_punctuation_density`, `space_before_colon`, `space_after_colon`, `spaces_around_ranges`, `struct_field_align_threshold`, `enum_discrim_align_threshold`, `blank_lines_upper_bound`, `blank_lines_lower_bound`, `inline_attribute_width`, `reorder_impl_items`, `condense_wildcard_suffixes`.
- Macros: `format_macro_matchers`, `format_macro_bodies`, `skip_macro_invocations`.
- Tooling: `ignore`, `required_version`, `format_generated_files`, `generated_marker_line_search_limit`, `skip_children`, `error_on_line_overflow`, `error_on_unformatted`, `show_parse_errors`, `unstable_features`, `version`, `color`, `emit_mode`, `make_backup`.

To use them, the whole team and CI must run `cargo +nightly fmt`. Mixing stable and nightly runs flips the output back and forth.

## Editions and style editions

Measured precedence, highest first:

1. `style_edition` (in `rustfmt.toml`, or `--style-edition`).
2. The edition `cargo fmt` passes from `Cargo.toml` (`rustfmt --edition 2021 …`, visible with `cargo fmt -v`). It overrides `edition` in `rustfmt.toml`.
3. `edition` in `rustfmt.toml`, which only bare `rustfmt` reads.
4. The default, 2015.

Editions 2015, 2018 and 2021 share one style. 2024 is the first new style edition, and it is stable on 1.97 even though the Style Guide still calls it nightly-only. Measured differences from the 2021 style:

- **Sorting is "version sorting"**: non-lowercase before lowercase, digit runs compared as numbers. `use x::{u16, u8, U8, Zeta, alpha, _priv, self}` becomes `{self, _priv, U8, Zeta, alpha, u8, u16}` (2021: `{self, _priv, alpha, u16, u8, Zeta, U8}`).
- Nested groups and globs sort **last** in a list import. 2021 put `hash_map::{self, Entry}` first.
- A short `if`/`else` that is a block's tail expression stays on one line: `if x { 0 } else { 1 }`. The 2021 style broke it over five lines. `let y = if x { 0 } else { 1 };` is one line in every style.

So a 2024-edition crate formatted with a 2021-style habit fails `cargo fmt --check`. Switch style editions in a commit that contains only the reformat.

Version sorting in full: split names into digit and non-digit runs. Compare digit runs by numeric value; on a tie, the run with more leading zeros sorts first. Compare other runs by Unicode, except that `_` sorts just after space and before every other character, and non-lowercase sorts before lowercase. The resulting order runs `_ZYXW, _abcd, A2, ABCD, Z_YXW, ZYXW, a1, abcd, u8, u16, u32, u64, u128, usize, x86, x86_64`.

## Skipping code

- `#[rustfmt::skip]` on an item, statement, or expression.
- `#[rustfmt::skip::macros(name)]` leaves calls to the macro `name` unformatted inside the item; `rustfmt::skip::attributes(name)` does the same for attributes. Both measured on stable.
- A whole file: `#[rustfmt::skip]` on its `mod name;` declaration (measured). Inner `#![rustfmt::skip]` is `error[E0658]: custom inner attributes are unstable` and breaks the build.
- Generated code: rustfmt 1.9.0 formatted a file starting `// @generated` (measured; `format_generated_files` is unstable and its effective value was `true`). Protect it with the `mod` attribute, or `include!` it, since rustfmt does not follow `include!` (measured).

## Style Guide rules rustfmt does not apply

The guide is the default for rustfmt, and rustfmt applies its layout rules (indentation, breaking, trailing commas, chains, match arms, `where` clauses). These rules it does not apply. Each item marked measured was left unchanged by rustfmt 1.9.0.

- **Comments.** Prefer `//` to `/* */`, with one space after `//`. Put comments on their own line where possible. Write them as sentences (capital letter, closing period). Keep comment-only lines within 80 characters, or the maximum width if smaller (measured: a 110-character comment stayed). Keep comments out of function signatures and off brace lines.
- **Doc comments**: `///`, not `/** */`. `//!` only for module and crate docs. Put doc comments **before** attributes (measured: a `///` between two `#[derive]`s stopped them merging).
- **Attributes**: one per line, a single `derive` per item, derive order preserved when merging by hand.
- **Unit structs**: `struct Foo;`, not `struct Foo {}` or `struct Foo();` (measured: `{}` kept). A tuple struct with more than a few fields should have named fields.
- **Imports**: rustfmt sorts within a group and never across a blank line, an attribute, or an item. It never merges or splits `use` lines. Hand normalisations: `use a::self;` → `use a;`, `use a::{b};` → `use a::b;`, delete `use a::{};`. Order: `extern crate`, then `use`, then `mod` declarations, before other items. Do not move a `#[macro_use]` module.
- **Parentheses**: use them liberally for clarity in arithmetic and logic (`(x * 15) + (y * 20)`), and parenthesise compound range bounds (`0..(x - 10)`). Never around an `if` or `while` condition (measured: `if (x)` kept; rustc's `unused_parens` warns). Do not use spaces to show precedence.
- **Hex literals**: one case per literal, and one case across the project (measured: `0xAbCd` kept; Clippy's `mixed_case_hex_literals` flags it).
- **Comparisons**: with `t: &T` and `u: U`, write `*t == u`, not `t == &u` (Clippy's `op_ref` covers part of this).
- **Semicolons**: end a unit-typed expression statement with `;` even when it is the tail (`fn bar() { foo(); }`). Pedantic `semicolon_if_nothing_returned` enforces this.
- **Enum variants**: qualify them (`Foo::Bar(a)`) unless the enum is in the prelude (`Some`, `Ok`). Pedantic `enum_glob_use` flags `use Enum::*`.
- **Expressions over statements**: `let x = if y { 1 } else { 0 };`, not `let x;` assigned in each branch.
- **Generics**: single-letter type parameters. Inline a very short bound; prefer a `where` clause to a multi-line generic list. No `where` clauses on `type` aliases, which are not enforced (rustc's `type_alias_bounds` warns).
- **Modules**: avoid `#[path]`.
- **Applied by rustfmt, not to do by hand** (measured): it writes `extern "C"` explicitly, removes braces from single-expression closures, removes leading match-arm pipes, and drops the comma after a block arm.

## Naming

- `UpperCamelCase` for types and enum variants; `snake_case` for functions, methods, fields, locals, and macros; `SCREAMING_SNAKE_CASE` for `const` and immutable `static`.
- A name that collides with a keyword takes a raw identifier (`r#type`, `r#gen`) or a trailing underscore. Never misspell it (`krate`). For `crate`, `self`, `super` and `Self`, only the underscore works: `r#crate` is an error, "`crate` cannot be a raw identifier" (measured), although the guide offers it.

## `Cargo.toml` conventions

`cargo fmt` formats only `.rs` files, so these are manual:

- Same width (100) and indentation (4 spaces) as code. One blank line between sections, none between a header and its keys or between keys. Unindented keys, `key = value` with single spaces, bare keys unless quoting is required.
- `[package]` first: `name`, then `version`, then other keys, with `description` last. Every other section's keys in version-sorted order.
- Arrays and inline tables on one line if they fit. Otherwise an array is block-indented, one item per line, with a trailing comma, and an inline table becomes its own `[dependencies.name]` section.
- Multi-line values such as `description` use multi-line strings, not `\n`. `description` wraps at 80 columns, does not start with the crate name, and leads with a one-sentence summary on its own line.
- `license` is an SPDX expression: `"MIT OR Apache-2.0"`. The guide still allows `MIT/Apache-2.0`, but the `/` form is deprecated (`using-cargo`).
- `authors`, if present, as `Full Name <email@address>`. The field is deprecated (`using-cargo`).
