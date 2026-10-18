---
name: fixing-rust-compile-errors
description: Diagnoses and fixes rustc and Cargo build errors and warnings on current stable Rust — reading diagnostics and their notes, error codes (current, retired, and renamed), the order in which errors surface, borrow-checker errors and their standard fixes, lint levels, groups, attributes and what the common lints mean, rustc --explain, cargo fix and clippy --fix, and JSON diagnostics. Use when the user pastes a rustc or cargo error or warning, names an error code such as E0382 or E0277, asks why code does not compile, why a lint fires or will not go away, or how to silence, deny, or expect a lint. Also use for symptoms without a code - "cannot borrow as mutable", "does not live long enough", "future cannot be sent between threads safely", "the trait bound is not satisfied", new errors appearing right after others were fixed, cargo check passing while cargo build fails, a warning that #[allow] or Cargo.toml [lints] does not silence, or an error code the compiler no longer emits.
license: MIT
---

# Fixing Rust compile errors

You already read rustc diagnostics well. This skill corrects what goes stale: which codes exist, how messages are now worded, which errors hide which, and how lint levels combine. Fixes that turn out to be design questions (who should own this data, should this be a trait object) belong to the `writing-rust` skill.

**Version basis.** Sourced from the Rust 1.99 stable documentation (error index, rustc book, Reference, Book), fetched 2026-10-17. Every behaviour marked *measured* was compiled on rustc/cargo/clippy **1.97.1**. Items marked **1.98+** come from the 1.99 docs and could not be measured: run `rustc --version` before relying on one.

## Large output goes to the triage agent

When a build or test run produces more than a handful of diagnostics, or fails after a dependency or toolchain change, delegate to the plugin's **`rust-build-triage`** agent rather than reading the output here. It runs cargo with JSON output, groups diagnostics by code, orders them by the phase that must be fixed first, and returns about 40 lines. Name the project directory and the failing command in the request. Fix what it returns, then run it again: more errors are normal after each round (next section).

For one or two errors, read them directly.

## Errors surface in rounds

rustc does not report everything at once. Measured on 1.97.1:

- **Per function body**, a resolution or type error (E0425, E0433, E0308, E0277, …) stops borrow checking of that body and hides its `unused_variables`/`unused_assignments` warnings. A body with an E0308 *and* a use-after-move reports only the E0308. Other bodies are still borrow-checked, so E0382 in one function and E0308 in another both appear.
- **Crate-wide**, `dead_code` is not reported while any error exists anywhere in the crate.
- Parse errors are recovered from, and later phases still report (a parse error, an E0425, and an E0308 appeared together). Recovery can produce spurious follow-ups, so fix syntax first.
- **`cargo check` passing does not mean `cargo build` passes.** Errors found during monomorphization never appear under `check`: a generic const assertion (`const OK: () = assert!(N > 0)` used from `make::<0>()`) passed `cargo check` and failed `cargo build` with E0080 "evaluation panicked". Linker errors are likewise build-only.

So fix in this order, and expect new diagnostics after each round:

1. Syntax, then imports and names: E0432, E0433, E0425. One wrong `use` produces a cascade.
2. Types and traits: E0308, E0277, E0599, E0282/E0283/E0284, E0061.
3. Borrowing and lifetimes: E0382, E0499, E0502, E0505, E0506, E0507, E0597, E0716, E0106, E0373.
4. Warnings, last, unless one explains an error (an `unused_must_use` on a dropped `Result`).

Within one body, the first error is usually the cause and the rest the cascade.

## Reading one diagnostic

- **`rustc --explain E0502`** prints the code's page, including for retired codes. With `--error-format=json`, the same text is already in each diagnostic's `code.explanation`. `--explain` takes E-codes only: `rustc --explain unused_variables` fails; use `cargo clippy --explain LINT` for Clippy lints.
- **E0277 chains** read bottom-up. The `required for X to implement Y` and `required by a bound in …` notes end at the impl that is really missing.
- **E0599** with "the following trait bounds were not satisfied" means the method exists but its impl's bounds fail. "items from traits can only be used if the trait is in scope" means add a `use`.
- **Compiler suggestions carry an applicability.** `MachineApplicable` means the edit compiles, not that it is right: rustc marks its `.clone()` suggestion for E0382 `MachineApplicable`. The E0106 help puts the new lifetime on every reference parameter; tie the output only to the input it really borrows from.
- **Some errors have no code**, so a filter on the code misses them: `future cannot be sent between threads safely`, `extern blocks must be unsafe`, `unsafe attribute used without unsafe`, `` `#[inline]` attribute cannot be used on structs ``, and parse errors.
- **Reproduce outside Cargo with an edition.** Bare `rustc file.rs` compiles as edition 2015 (measured). Use `rustc --edition 2024 --crate-type lib file.rs`.

## Stale knowledge to correct

Measured on 1.97.1 unless marked:

- **E0412 is retired.** An unknown type name is E0425 "cannot find type `Foo` in this scope". `rustc --explain E0412` still prints a page headed "no longer emitted".
- **E0433 is worded differently.** `HashMap::new()` without a `use` is "cannot find type `HashMap` in this scope". An unknown module is "cannot find module or crate `x` in this scope". "failed to resolve: use of undeclared type" is the old wording.
- **"dyn compatible", not "object safe".** E0038 reads "the trait `T` is not dyn compatible". An `async fn` in the trait is one cause ("because method `a` is `async`").
- **E0700 is mostly gone in edition 2024**, where return-position `impl Trait` captures every in-scope lifetime. In ≤2021 the fix is `+ use<'x>` (precise capturing), which the compiler now suggests in place of `+ 'x`. In 2024 it still appears when a `use<..>` list omits a lifetime the value needs.
- **Retirements still in progress.** The 1.99 docs retire E0232, E0517, E0537, E0552, E0693, E0718 and E0734, but 1.97.1 still treats them as live (`rustc --explain` carries no "no longer emitted" header): `#[repr(D)]` is E0552 and `#[repr(align=8)]` is E0693 on 1.97.1, and E0539 in the 1.99 docs. Accept either.
- **Codes that became lints.** `static mut` references are the `static_mut_refs` lint, deny in 2024. The 2024 docs call it a hard error, but `#[allow(static_mut_refs)]` silences it. A binding named like a variant is error E0170, reported by the deny-by-default lint `bindings_with_variant_name`. E0133 also appears as a *warning* inside `unsafe fn` bodies in 2024 (`unsafe_op_in_unsafe_fn`).
- **E0282, E0283 and E0284 differ.** E0282 means nothing constrains the type (`let v = Vec::new();`). E0283 means several impls fit (`collect()`, `into()`). E0284 means a projection cannot be resolved: `"42".parse()` with no target type is E0284 ("cannot satisfy `<_ as FromStr>::Err == _`"), not E0282.
- **A misleading E0624.** `o.len()` on `Option<String>` reports "method `len` is private" (a private std method). The real fix, as the help says, is to unwrap the `Option` first.
- **Not every borrow error is fixable by reshaping.** Returning a borrow from one branch and mutating in another (`if let Some(v) = map.get(&k) { return v; } map.insert(..)`) is still rejected on stable (it needs Polonius). Use the entry API.
- **`drop(guard)` before `.await` does not make the future `Send`.** End the guard's scope with a block instead.

`references/error-codes.md` has every code with its current meaning, and the retired list with where each code went.

## Borrow-checker errors

Read the three labels (where the first borrow occurs, the conflicting use, and where the first borrow is "later used"). Then prefer, in order: reorder so the first borrow ends earlier; borrow disjoint parts (fields, `split_at_mut`, `get_disjoint_mut`); copy out or use indices; take ownership temporarily (`mem::take`, `mem::replace`, `Option::take`); clone. Use `Rc<RefCell<_>>` or `Arc<Mutex<_>>` only when the data really has several owners. Used to silence one error, they move the failure to a runtime panic or deadlock.

A method call borrows the whole receiver, and a field access borrows only that field. So `self.a_mut().extend(self.b_ref())` fails while `(&mut self.a).extend(&self.b)` compiles.

Read `references/borrow-checker-patterns.md` when a borrow error resists the first fix you try. It has the measured error and the fix that compiles for each recurring shape, plus the 2021-versus-2024 differences.

## Automatic fixes

- **`cargo fix`** applies rustc's machine-applicable suggestions. Measured on 1.97.1:
  - It covers the **default targets only** (since 1.89), like `cargo check`. Tests, examples, and benches need `--all-targets`. Older docs say it implies `--all-targets`.
  - It refuses a dirty working tree: "the working directory of this package has uncommitted changes". Pass `--allow-dirty` only after the user agrees.
  - It changes nothing while the crate has errors. `--broken-code` applies the fixes anyway.
  - `cargo fix --edition` migrates source to the next edition but leaves `edition` in `Cargo.toml` unchanged. Edit that yourself, then build again.
- **`cargo clippy --fix`** does the same with Clippy's suggestions. Its `--help` says it implies `--all-targets`, but on 1.97.1 it fixed only the library; tests needed `--all-targets`.
- Commit or stash first, and review the diff. A machine-applicable fix can still be the wrong design.

## Lints

Levels are `allow`, `expect`, `warn`, `force-warn` (CLI only), `deny`, `forbid`. The rules that trip people, all measured:

- An attribute in the source beats a command-line `-D`/`-W`/`-A`. Cargo's `[lints]` table is passed as such flags, so a source `#[allow]` beats it too.
- In `[lints]`, the order of keys is ignored. To let `unused_variables = "allow"` override `unused = "deny"`, give the group `priority = -1`.
- `#![forbid(group)]` does not forbid: an inner `#[allow]` only warns (`forbidden_lint_groups`) and wins. Use `#![deny(warnings)]`.
- `#[expect(lint)]` warns when the lint stops firing. Prefer it to `allow` for temporary suppressions.
- Dependency warnings never show: Cargo passes `--cap-lints allow` to them.
- For CI, `build.warnings = "deny"` (Cargo 1.97) fails on local warnings without `RUSTFLAGS=-Dwarnings`.
- `rustc -W help` lists defaults without edition adjustments. `static_mut_refs` shows as warn but is deny in 2024.

Read `references/lints.md` for precedence in full, edition-dependent defaults, groups, Clippy's levels, the common lints with their fixes, renamed lints, and the lints newer than 1.97.

## JSON diagnostics

- `rustc --error-format=json` writes one JSON object per line to **stderr**. `cargo … --message-format=json` writes to stdout, wrapping each in `{"reason":"compiler-message","message":{…}}`. Other formats are `short`, `json-diagnostic-short`, `json-diagnostic-rendered-ansi`, and `json-render-diagnostics`.
- In each diagnostic, `code` is `{code, explanation}` or null, and `code.code` is an E-code or a lint name (`"unused_variables"`). `level` is `error`, `warning`, `note`, `help`, `failure-note`, or `error: internal compiler error`. Each `spans[]` entry has `is_primary`, 1-based lines, and columns that count Unicode scalar values, not bytes. `children[]` nest one level, and `rendered` is the human text.
- Suggestions sit in `spans[].suggested_replacement` with `suggestion_applicability`: `MachineApplicable`, `MaybeIncorrect`, `HasPlaceholders`, or `Unspecified`.
- Tools must tolerate nulls, new fields, and new `level` values.

A one-line summary per diagnostic:

```bash
cargo check --message-format=json 2>/dev/null | jq -r 'select(.reason=="compiler-message") | .message
  | select(.level=="error" or .level=="warning")
  | "\(.level)\t\(.code.code // "-")\t\(.spans[0].file_name // "-"):\(.spans[0].line_start // "-")\t\(.message)"'
```

## Where to look

Read only the file the question needs.

- `references/error-codes.md`: when a code is unfamiliar, seems not to match the code, or is not emitted any more. It has the most-hit codes with their 1.97.1 wording, every current code by family with its usual fix, errors that have no code, and every retired code with where it went.
- `references/borrow-checker-patterns.md`: when a borrow, move, or lifetime error resists a first fix, or behaves differently between editions.
- `references/lints.md`: when a lint fires unexpectedly, will not go away, or needs configuring.

## Hand-offs

- The `[lints]` table syntax, `RUSTFLAGS`, and dependency resolution errors ("failed to select a version"): `using-cargo`.
- Redesigning ownership, choosing between trait objects and generics, error-type design: `writing-rust`; for a library's public API, `designing-rust-apis`.
- Which Clippy lints to enable, `clippy.toml`, Clippy in CI, rustfmt: `linting-and-formatting-rust`.
- Failing tests, as opposed to tests that do not compile: `testing-rust`. Doctest attributes and rustdoc lints: `documenting-rust`.
