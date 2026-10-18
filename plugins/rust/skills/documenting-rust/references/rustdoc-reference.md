# rustdoc reference

The rustdoc book, Reference, and Cargo book (Rust 1.99 docs). Items marked *measured* were checked on rustdoc/cargo 1.97.1. Doctest syntax lives in `doctests.md`.

Contents:
- [Doc comment forms](#doc-comment-forms)
- [Crate-level `#![doc(...)]` keys](#crate-level-doc-keys)
- [Item-level `#[doc(...)]`](#item-level-doc)
- [Re-exports in detail](#re-exports-in-detail)
- [Intra-doc links in detail](#intra-doc-links-in-detail)
- [doc(cfg) and auto_cfg](#doccfg-and-auto_cfg)
- [Lint diagnostics](#lint-diagnostics)
- [Markdown](#markdown)
- [What rustdoc shows](#what-rustdoc-shows)
- [cargo doc and cargo rustdoc](#cargo-doc-and-cargo-rustdoc)
- [rustdoc flags](#rustdoc-flags)
- [docs.rs](#docsrs)
- [Search syntax](#search-syntax)

## Doc comment forms

- `///` and `/** */` are outer docs for the next item. `//!` and `/*! */` are inner docs for the enclosing item, such as the crate root or a module. `////`, `/***`, and `/**/` are plain comments.
- `/// text` is `#[doc = " text"]`, with the leading space kept. Several `#[doc]` attributes join with `\n`, which is how macros generate docs.
- `#[doc = include_str!("../docs/x.md")]` on an item, or `#![doc = include_str!("../README.md")]` at the crate root, pulls docs from a file.
- A doc comment with no item after it is an error. A doc comment on a statement is ignored with `unused_doc_comments`.

## Crate-level `#![doc(...)]` keys

| Key | Effect |
|---|---|
| `html_logo_url = "…"` / `html_favicon_url = "…"` | Sidebar logo (rendered 100 px wide) and favicon |
| `html_playground_url = "…"` | Adds Run buttons. The request carries `code`, `version`, and `edition` |
| `html_root_url = "https://docs.rs/name/1.0"` | Where other crates' docs link to this crate |
| `html_no_source` | No source pages and no `[src]` links |
| `issue_tracker_base_url = "…"` | Links unstable features to tracking issues (std) |
| `test(no_crate_inject)` / `test(attr(...))` | Doctest settings. See `doctests.md` |

Links to items in other crates resolve, in order: docs already in the output directory, then `--extern-html-root-url` (nightly), then that crate's `html_root_url`, and otherwise no link.

## Item-level `#[doc(...)]`

- `#[doc(hidden)]` keeps the item public but undocumented. Neither `--document-private-items` nor anything else on stable shows it. The nightly `--document-hidden-items` does.
- `#[doc(inline)]` and `#[doc(no_inline)]` go on `pub use`. See below.
- `#[doc(alias = "name")]` adds a search alias. It is repeatable, and the list form `#[doc(alias("a", "b"))]` works. A space inside an alias is allowed. A leading or trailing space is an error: "`#[doc(alias = "...")]` cannot start or end with ' '" (measured). Quotes are rejected. Use an alias for the C name on an FFI wrapper.
- Nightly-only: `doc(cfg)` and `doc(auto_cfg)` (below), `#[doc(notable_trait)]` (`doc_notable_trait`), and `#[doc(masked)]`. `#[doc(keyword = …)]` and `#[doc(attribute = …)]` need `rustdoc_internals`.

## Re-exports in detail

Measured on 1.97.1:

| Re-export | Rendered as |
|---|---|
| A local public item through a public path (`pub use local::Item;`) | A "Re-exports" line |
| A local item from a private module (`pub use hidden::Item;`) | Inlined |
| An item or module from another crate (`pub use dep::Item;`, `pub use dep::module;`) | Inlined |
| A whole crate (`pub use dep;`) | A "Re-exports" line, unless `#[doc(inline)]` |

Further rules from the book:

- `#[doc(inline)]` on a re-export of an item that is already public shows it in both places. `#[doc(no_inline)]` forces a "Re-exports" line.
- An item whose own `#[doc(hidden)]` is set stays invisible through the re-export. An item hidden only by an ancestor module is inlined at the re-export.
- When an item is inlined, the doc comments along the re-export chain are concatenated, and cfgs are inherited. `doc(alias)`, `doc(hidden)`, `doc(inline)`, and `doc(no_inline)` are not inherited. In a chain, a `#[doc(hidden)]` re-export contributes nothing.
- When an item is not inlined, the attributes on the `pub use` are ignored. A `#[cfg(x)]` on it is not displayed.
- Docs written on a `pub use` resolve their intra-doc links in the re-exporting module, which suits proc-macro crates re-exported from a facade. The item's own docs resolve where the item was defined.

## Intra-doc links in detail

- Forms: `[Foo]`, `` [`Foo`] ``, `[text](Foo)`, `[text][Foo]` with no reference definition needed, `[text][r]` with `[r]: Foo`. Paths may use `crate`, `self`, `super`, and `Self`.
- Targets: items, associated items, enum variants, fields, primitives, and URL fragments (`[x](std::fmt#formatting-parameters)`). Not resolvable: items from blanket impls (`String::to_string` comes from `impl<T: Display> ToString for T`, measured) and fully qualified paths (measured).
- Disambiguators, written as `kind@Name`: `struct`, `enum`, `trait`, `union`, `mod`/`module`, `const`/`constant`, `fn`/`function`, `field`, `variant`, `method`, `derive`, `type`, `value`, `macro`, `tyalias`/`typealias`, `prim`/`primitive`. Suffix forms: `name()` for a function, `name!`, `name!()`, `name![]`, or `name!{}` for a macro. Disambiguators do not appear in the rendered text.
- Text with `/` or `[]` inside does not look like a link and is silently left alone. When a target cannot be resolved (for example, it is cfg'd out), `[a]` and `[b][c]` render as literal text, while `[d](e)` and `[f]` with `[f]: g` become plain relative URLs.
- Links in another crate's docs that fail to resolve give no warning.
- A `#[macro_export]` macro defined inside a module resolved a link to a sibling item in that module (measured). The book's statement that macro docs resolve from the crate root did not reproduce on 1.97.1.

## doc(cfg) and auto_cfg

Nightly only. Enable with `#![cfg_attr(docsrs, feature(doc_cfg))]`. On stable, every form below is E0658 (measured). `feature(doc_auto_cfg)` was removed in 1.92 and merged into `doc_cfg` (E0557, measured). `doc(cfg_hide(...))` no longer exists. Use `auto_cfg(hide(...))`.

- `auto_cfg` is on by default once `doc_cfg` is enabled. Every `#[cfg(...)]` item gets an "Available on …" badge, e.g. "Available on **crate feature `fancy`** only" (measured).
- `#[doc(cfg(feature = "x"))]` sets the badge text explicitly and overrides `auto_cfg` for that item. It only documents: `#[doc(cfg(not(windows)))]` does not hide anything.
- `#[doc(auto_cfg = false)]` turns badges off for an item and its children. Bare `#[doc(auto_cfg)]` means `= true`.
- `#![doc(auto_cfg(hide(unix)))]` hides the value-less `unix` from badges, so `any(unix, windows)` renders as "Windows" (measured). `hide(feature, target_os)` hides only the value-less forms of those keys. `values("a", "b")` applies to every key in that `hide(...)`, so use two groups for different keys. `values(any())` hides every value. Only identifiers and `values()` are accepted, so `not(...)` is invalid. `test`, `doc`, and `doctest` are hidden by default.
- `#[doc(auto_cfg(show(...)))]` reverses `hide` for an item and its descendants. `show` and `hide` of the same cfg on one item is an error.
- A re-export's cfg merges with the item's only when the re-export has `#[doc(inline)]`. Re-exporting a foreign item without it drops the item's badge.
- These attributes go on modules or the crate root and are inherited. Parent and child cfgs combine, e.g. "Available on (Windows or Unix) and non-Unix only."

## Lint diagnostics

| Lint (default) | Message |
|---|---|
| `rustdoc::broken_intra_doc_links` (warn) | "unresolved link to `X`". Ambiguity: "`Bar` is both a function and a struct", with help to add parentheses or prefix `struct@` (measured) |
| `rustdoc::private_intra_doc_links` (warn) | "public documentation for `mycrate` links to private item `helper`", with the note "this link will resolve properly if you pass `--document-private-items`" (measured) |
| `rustdoc::invalid_codeblock_attributes` (warn) | "unknown attribute `should-panic`". Help: use `should_panic` (measured) |
| `rustdoc::invalid_html_tags` (warn) | "unclosed HTML tag `u8`" for an unbackticked `Vec<u8>` (measured), or "unopened HTML tag" |
| `rustdoc::invalid_rust_codeblocks` (warn) | "Rust code block is empty", "could not parse code block as Rust code" |
| `rustdoc::bare_urls` (warn) | "this URL is not a hyperlink". Fix: `<https://…>` (measured) |
| `rustdoc::redundant_explicit_links` (warn) | "redundant explicit link target" (measured) |
| `missing_docs` (allow) | "missing documentation for a function", "… for the crate" (measured) |
| `rustdoc::missing_crate_level_docs` (allow) | "no documentation found for this crate's top-level module" (measured) |
| `rustdoc::unescaped_backticks` (allow) | "unescaped backtick" (measured) |
| `rustdoc::private_doc_tests` (allow) | "Documentation test in private item" |
| `rustdoc::missing_doc_code_examples` | Nightly only. Stable: "unknown lint … the lint is unstable" (measured) |

`invalid_doc_attributes` is a rustc lint (warn) for misplaced `#[doc]` keys. `rustdoc::` lints are unknown to plain rustc until rustdoc runs. The rustc lint for a misspelled tool name is E0710.

## Markdown

CommonMark, plus strikethrough (`~~x~~`), footnotes (`[^n]` with `[^n]: text`), GFM tables, task lists, and smart punctuation (`--` becomes an en dash, `---` an em dash, `...` an ellipsis). A warning box is `<div class="warning">…</div>`. Markdown inside an HTML block is parsed only when blank lines separate the tags from the content. Headings inside doc comments start at `#`, because rustdoc nests them under the item.

## What rustdoc shows

- Only publicly reachable items. A `pub fn` in a private module is not documented unless re-exported.
- rustdoc sees code as if `--cfg doc` were set, for the host target (or `--target`), and skips some compiler passes, so some invalid function bodies compile under rustdoc.
- `#[repr(...)]` is shown only when every field is public and not hidden and no variant is hidden. `#[repr(transparent)]` is shown when its non-1-ZST field is public. Hiding a repr with `cfg_attr(not(doc), …)` is not guaranteed to work. If the repr is private, say so in prose.

## cargo doc and cargo rustdoc

- Output goes to `target/doc/<crate>/index.html`. Docs are cumulative: pages for deleted items persist until `cargo clean --doc`. Since 1.93, a toolchain change clears only the requested targets.
- Default targets: the lib and all bins. A bin with the same name as the lib is skipped, and `doc = false` on a target excludes it. Binaries get `--document-private-items` and `-A rustdoc::private_intra_doc_links` automatically (measured).
- `--open` uses the `doc.browser` config, then `BROWSER`. `--no-deps` skips dependencies.
- `cargo rustdoc [target] -- ARGS` passes ARGS to the final rustdoc call only, and does not document dependencies. For every rustdoc call, set `RUSTDOCFLAGS` or `build.rustdocflags` (precedence: `using-cargo`).
- `cargo doc --output-format json` and `cargo rustdoc --output-format json` are nightly-only.
- Scraped examples (calls from `examples/` shown in item docs) are nightly-only: `cargo doc -Zunstable-options -Zrustdoc-scrape-examples`.

## rustdoc flags

Stable: `-o/--out-dir`, `--crate-name`, `--crate-version` (sidebar "Version …"), `--document-private-items`, `--edition` (**defaults to 2015** when run directly, measured), `--cfg`, `--check-cfg`, `-C opt=val` (passed to doc and doctest compiles), `--target`, `-L`, `--extern`, `--remap-path-prefix`, `--default-theme=ayu`, `--theme FILE.css`, `--check-theme FILE.css` (a separate mode that ignores the other flags), `-e/--extend-css`, `--html-in-header` / `--html-before-content` / `--html-after-content`, `--emit=html-static-files,html-non-static-files,dep-info[=PATH]` (measured), `@argfile`, and `-` (stdin input). A `.md` input is rendered as standalone Markdown, with `--markdown-css`, `--markdown-playground-url`, and `--markdown-no-toc`. `--passes`, `--no-defaults`, and `--input-format` are deprecated.

Nightly, behind `-Z unstable-options` (measured as rejected on stable where marked): `--output-format json` (measured) (std's JSON ships in the `rust-docs-json` component), `--show-coverage` (measured), `--document-hidden-items` (measured), `--extern-html-root-url`, `--check`, `--index-page`, `--enable-index-page`, `--static-root-path`, `--resource-suffix`, `--show-type-layout`, `--sort-modules-by-appearance`, `--generate-link-to-definition`, `--generate-macro-expansion`, `--playground-url`, `--markdown-before-content`/`--markdown-after-content`, and `--write-doc-meta-dir`/`--read-doc-meta-dir`.

## docs.rs

docs.rs builds with a nightly toolchain and sets `cfg(docsrs)` for the crate being documented, not for its dependencies. `[package.metadata.docs.rs]` keys: `features`, `all-features`, `no-default-features`, `default-target`, `targets`, `additional-targets`, `rustc-args`, `rustdoc-args`, and `cargo-args`. Because docs.rs uses nightly, a `#![cfg_attr(docsrs, feature(...))]` naming a removed feature (`doc_auto_cfg`) fails the docs.rs build while every local stable build passes.

## Search syntax

- Name search: a space means `::`. Matching is fuzzy, and a quoted name (`"HashMap"`) matches exactly. Filter by kind with `kind:name` (`fn:`, `struct:`, `macro:`, `trait:`, `mod:`, …).
- Type search: `params -> return`, e.g. `usize -> vec` or `option<T>, (T -> bool) -> option<T>`. Parameter order does not matter, but order inside generics does. An unknown name becomes a generic, so force one with `generic:T` or `struct:T`. References, `Box`, `Rc`, `Arc`, `Option`, and `Result` may be omitted from the query. There are no where-clauses, lifetimes, or array lengths. Fields act as getters, and consts as nullary functions.
- `S` focuses search. A URL such as `…/std/?search=%s&go_to_first=true` jumps to the first result.
