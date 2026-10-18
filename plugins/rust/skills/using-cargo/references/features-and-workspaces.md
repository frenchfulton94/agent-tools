# Features and workspaces

Contents:
- [Feature syntax](#feature-syntax)
- [Unification: what actually gets enabled](#unification-what-actually-gets-enabled)
- [Designing features](#designing-features)
- [Workspace layout](#workspace-layout)
- [Inheritance from the workspace](#inheritance-from-the-workspace)
- [Package selection](#package-selection)
- [The `[lints]` table](#the-lints-table)

## Feature syntax

```toml
[features]
default = ["std"]
std = []
net = ["dep:hyper"]          # enables the optional dependency, hides the implicit feature
tls = ["hyper?/tls"]         # weak: enables hyper/tls only if something else enables hyper
full = ["net", "serde/derive"]   # "pkg/feat" also enables an optional pkg

[dependencies]
hyper = { version = "1", optional = true }
```

- An optional dependency defines an implicit feature of the same name, unless any feature mentions `dep:name`. Then `--features name` fails (measured: "the `features` table includes it with the "dep:" syntax so it does not have an implicit feature with that name").
- `dep:` and `?/` need Rust 1.60. Feature names may contain letters, digits, `_`, `-`, `+` (crates.io); `.` is accepted by Cargo but not crates.io.
- crates.io caps a new version at 300 features.
- CLI: `-F a,b` or `--features "a b"` (quoted; unquoted `--features a b` makes `b` a positional argument). `member/feat` targets a workspace member. `--all-features`, `--no-default-features`. Resolver 2+ applies `--no-default-features` to every selected member.
- Build scripts see `CARGO_FEATURE_<NAME>` (uppercase, `-` to `_`). Code sees `cfg(feature = "name")`; Cargo declares every feature to `--check-cfg`, so a typo in `cfg(feature = ...)` warns.

## Unification: what actually gets enabled

A dependency is compiled once per build with the union of every feature requested by every package built in that invocation. Consequences, all measured on 1.97.1:

- **Selection changes features.** `cargo build -p a` and `cargo build --workspace` can compile a shared dependency differently, so the same binary can behave differently depending on how it was built. Alternating between them rebuilds the shared crates each time.
- **At a virtual root, everything is selected**: every member, including path dependencies inside the workspace directory (they become members automatically), each with its own default features.
- **`--all-targets` (and `cargo test`) unify dev-dependency features into normal dependencies.** A feature enabled only under `[dev-dependencies]` appeared in the normal binary after `cargo build --all-targets`.
- **`default-features = false` does not guarantee the defaults are off.** Any other dependent that leaves defaults on turns them back on.

What resolver 2 and later do *not* unify: features of target-specific dependencies for targets not being built; build dependencies and proc macros versus normal dependencies (so a crate can be built twice, once per role); and dev-dependency features when no target needs them.

Investigate before changing anything: `cargo tree -e features -i CRATE` shows which dependent turned each feature on, and marks features from the command line `(command-line)`. `cargo tree -d` lists crates built in more than one version.

`resolver.feature-unification = "workspace" | "package"` is nightly-only; stable Cargo warns and ignores it (measured).

## Designing features

- Features must be additive. Provide a `std` feature (`#![no_std]` plus `#[cfg(feature = "std")] extern crate std;`), never a `no_std` feature.
- Avoid mutually exclusive features. If unavoidable, `compile_error!` on the forbidden combination, but prefer splitting packages or choosing at runtime.
- Removing a feature, or an optional dependency without `dep:`, is a SemVer-major change. Moving existing public items behind a new non-default feature is also major. Use `dep:` and semantic names (`net = ["dep:hyper"]`) so the dependency can change later.
- Tests, docs, and Clippy run with default features only. Check other combinations in CI (`--no-default-features`, `--all-features`, or `cargo hack --feature-powerset`).
- Document features in the crate-level docs; `[package.metadata.docs.rs]` controls which features docs.rs builds with.

## Workspace layout

```toml
# Virtual manifest (no [package])
[workspace]
members = ["crates/*"]
exclude = ["crates/scratch"]
default-members = ["crates/cli"]
resolver = "3"               # required: a virtual workspace never infers it
```

- One `Cargo.lock` and one `target/` at the root, even when you build from inside a member.
- `[patch]`, `[replace]`, and `[profile.*]` are honoured only in the root manifest. Members' copies are ignored.
- `[dependencies]`, `[features]`, and `[lints]` in a virtual manifest are errors.
- A member below the root needs nothing; a member outside it needs `package.workspace = "../path"`.
- `cargo new` inside a workspace adds the new package to `members`.
- The Cargo Book recommends a flat `crates/` directory with a glob.

## Inheritance from the workspace

```toml
[workspace.package]
version = "0.3.0"
edition = "2024"
rust-version = "1.85"
license = "MIT OR Apache-2.0"

[workspace.dependencies]
serde = { version = "1", default-features = false }

# member Cargo.toml
[package]
name = "core"
version.workspace = true
edition.workspace = true

[dependencies]
serde = { workspace = true, features = ["derive"] }
```

- Inheritable `[workspace.package]` keys: authors, categories, description, documentation, edition, exclude, homepage, include, keywords, license, license-file, publish, readme, repository, rust-version, version. `license-file` and `readme` are relative to the root; `include` and `exclude` to the member.
- A member's inherited dependency may add only `features` (additive with the workspace list), `optional`, and `default-features`. A workspace dependency cannot itself be `optional`.
- **`default-features` measured on 1.97.1:**

  | Workspace entry | Member entry | Edition 2024 member | Edition 2021 member |
  |---|---|---|---|
  | `default-features = false` | (none) | defaults off | defaults off |
  | (none) | `default-features = false` | hard error | warning, defaults stay **on** |
  | `default-features = true` | `default-features = false` | hard error | warning, defaults stay **on** |
  | `default-features = false` | `default-features = true` | defaults on | defaults on |

  The 1.99 docs say an edition 2024 member's `default-features` overrides the workspace value on Rust 1.99+ (**1.98+**, unmeasured). To work on any version, disable defaults in `[workspace.dependencies]` and opt back in per member.
- `[workspace.metadata]` is ignored by Cargo, like `[package.metadata]`.

## Package selection

- In a member directory, commands act on that member. At a root with `default-members`, on those. Otherwise a root package acts on itself only, and a virtual root acts on every member.
- `-p SPEC` (repeatable, globs if quoted: `-p 'serde*'`), `--workspace`, `--exclude SPEC` (with `--workspace`). `--all` is a deprecated alias for `--workspace`.
- `cargo run` and `cargo rustc` take a single package.
- `--package` naming a missing package together with `--workspace` is an error (1.86).

## The `[lints]` table

```toml
[lints.rust]
unsafe_code = "forbid"
unexpected_cfgs = { level = "warn", check-cfg = ['cfg(docsrs)'] }

[lints.clippy]
pedantic = { level = "warn", priority = -1 }
must_use_candidate = "allow"   # a pedantic lint many projects turn back off

# workspace-wide
[workspace.lints.rust]
missing_docs = "warn"
# and in each member:
[lints]
workspace = true
```

- Levels: `forbid`, `deny`, `warn`, `allow`. The table is the part before `::` (`clippy::foo` goes under `[lints.clippy]`); no prefix means `rust`.
- Lower `priority` is applied first, so the higher one wins. Groups need `priority = -1` to be overridable; equal priority makes Clippy fail with "lint group `pedantic` has the same priority (0) as a lint" (measured).
- `[lints]` applies only to the package's own code, never to dependents or dependencies (Cargo passes `--cap-lints allow` for non-path dependencies).
- `[workspace.lints]` applies to a member only if it says `[lints] workspace = true` (measured). To opt out explicitly, give the member an empty `[lints]`.
- `[lints.cargo]` (Cargo's own manifest lints such as `unused_dependencies`) is nightly-only; stable warns "unused manifest key `lints.cargo`" (measured).
- For what an individual lint means, see `fixing-rust-compile-errors`.
