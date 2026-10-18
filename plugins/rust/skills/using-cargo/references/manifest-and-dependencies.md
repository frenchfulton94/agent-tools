# Manifest and dependencies

Contents:
- [The `[package]` table](#the-package-table)
- [Targets and auto-discovery](#targets-and-auto-discovery)
- [Version requirements](#version-requirements)
- [Dependency sources](#dependency-sources)
- [Platform-specific, dev, and build dependencies](#platform-specific-dev-and-build-dependencies)
- [Overriding dependencies](#overriding-dependencies)
- [Source replacement and vendoring](#source-replacement-and-vendoring)
- [How the resolver chooses](#how-the-resolver-chooses)
- [rust-version (MSRV)](#rust-version-msrv)

## The `[package]` table

- Only `name` is required. `version` is optional since 1.75 and defaults to `0.0.0`. A package without a `version` cannot be published.
- `edition` absent means **2015**, with a warning (measured: "`package.edition` is unspecified, defaulting to `2015` while the latest is `2024`"). `cargo new` writes `edition = "2024"`. The per-target `edition` key (`[lib] edition = ...`) is deprecated (1.87).
- `authors` is deprecated (it still feeds `CARGO_PKG_AUTHORS`). `[badges]` is effectively deprecated and crates.io does not display badges.
- `description` is plain text, not Markdown. `license` is an SPDX 2.3 expression (`"MIT OR Apache-2.0"`); the `/` separator is deprecated. Use `license-file` for a non-SPDX license.
- `readme` auto-detects `README.md`, `README.txt`, or `README` when unset; `readme = false` disables detection.
- `keywords`: at most 5, ASCII, at most 20 characters each. `categories`: at most 5, each an exact slug from crates.io/category_slugs.
- `publish = false` or `publish = ["my-registry"]`. With exactly one registry listed, `cargo publish` uses it without `--registry`.
- `include` / `exclude` use gitignore syntax. They are mutually exclusive in practice (`include` wins; negate with `!` inside it). **When `include` is set, `.gitignore` rules are not applied.** Always packaged: `Cargo.toml`, a minimized `Cargo.lock`, `license-file`. Always excluded: the root `target/` directory and any subdirectory that holds its own `Cargo.toml`.
- `links = "foo"` names the native library a build script links; at most one package in the graph may use a given value.
- `[package.metadata.*]` is ignored by Cargo with no unused-key warning (tools such as docs.rs read `[package.metadata.docs.rs]`). Any other unknown key or table warns "unused manifest key" (measured).
- `default-run = "name"` picks the binary for `cargo run` when there are several.
- `[hints]` (1.90): unknown hints only warn, so they never raise your MSRV. No hint is stable yet.

## Targets and auto-discovery

- `src/lib.rs`, `src/main.rs`, `src/bin/*.rs`, `src/bin/<name>/main.rs`, and the same patterns under `examples/`, `tests/`, `benches/`. Target names use kebab-case by convention.
- The library name is the package name with `-` replaced by `_`. The default binary keeps the package name unchanged. One library per package.
- Target keys: `name`, `path`, `test`, `doctest` (library only), `bench`, `doc`, `harness`, `crate-type`, `required-features`, `proc-macro`.
- `crate-type` applies to libraries and examples only: `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, `proc-macro`. `dylib` with `cdylib` together is an error.
- `required-features` silently skips a target (bin, test, bench, or example) when the features are missing; it has no effect on `[lib]`.
- `autobins`, `autoexamples`, `autotests`, `autobenches`, and `autolib` (1.83) set to `false` disable discovery. Use `autobins = false` when a library has a module named `bin`. Since edition 2018, discovery stays on even when targets are listed manually.

## Version requirements

The bare form is a caret requirement. Cargo's caret differs from the SemVer spec for `0.x`: the left-most non-zero component is the compatibility boundary.

| Requirement | Range |
|---|---|
| `1.2.3` (= `^1.2.3`) | `>=1.2.3, <2.0.0` |
| `0.2.3` | `>=0.2.3, <0.3.0` |
| `0.0.3` | `>=0.0.3, <0.0.4` |
| `0` | `>=0.0.0, <1.0.0` |
| `~1.2.3` | `>=1.2.3, <1.3.0` |
| `~1` | `>=1.0.0, <2.0.0` |
| `1.2.*` | `>=1.2.0, <1.3.0` |

- crates.io rejects a bare `*` requirement in any published package.
- Pre-releases are matched only when requested: `"1.0"` never matches `1.0.0-alpha`. `"1.0.0-alpha"` may move to a later pre-release of the same version and to compatible releases. Build metadata (`+...`) is ignored.
- Recommendations from the Cargo Book: write all three components of the version whose API you actually use; raise the minimum when you start using a newer API. Avoid upper bounds below the next incompatible version (`">=2.0, <2.4"`, `~2.0`, `2.0.*`), because they make graphs unresolvable; pin with the lockfile instead. Use `=` only for a companion proc-macro crate that must match exactly, or for a binary nobody depends on.

## Dependency sources

- Registry: `foo = "1"`, or `{ version = "1", registry = "my-registry" }` with the registry defined in `.cargo/config.toml`. A crates.io package may not depend on another registry.
- Git: `{ git = "https://...", branch | tag | rev = "..." }`. Only one of the three. `rev` accepts any ref, such as `refs/pull/493/head`. With none, Cargo takes the default branch HEAD and pins it in `Cargo.lock` until `cargo update`. Cargo searches the whole repository for the named package. A `#fragment` in the URL is ignored with a warning. scp-style URLs (`git@host:org/repo.git`) are not supported; write `ssh://git@host/org/repo.git`.
- Path: `{ path = "../foo" }` must point at the directory that holds the dependency's `Cargo.toml`. A path or git dependency also needs `version` to be publishable; the path or git key is used locally and stripped on publish.
- `git` and `path` together is an error. Since 1.96, `git` may be combined with an alternate `registry`.
- Renaming: `bar = { package = "foo", version = "1" }`. Feature names follow the key: `bar/feat`, not `foo/feat`.
- `{ optional = true }` with no source is an error (1.79).

## Platform-specific, dev, and build dependencies

- `[target.'cfg(windows)'.dependencies]`, `[target.x86_64-pc-windows-gnu.dependencies]`. List the cfgs with `rustc --print cfg --target T`. Since 1.88, `cfg(true)` and `cfg(false)` are boolean literals.
- `feature = ...`, `test`, `debug_assertions`, and `proc_macro` do not work in these tables (Cargo warns). The resolver resolves target tables as if every platform were active, so a `cfg(false)` dependency is still resolved and locked; this is the documented way to keep a dependency only to constrain a transitive version.
- `[dev-dependencies]` serve tests, examples, and benches only, and never propagate to dependents. On publish only dev-dependencies with a `version` are kept.
- `[build-dependencies]` are visible to `build.rs` only; the build script cannot see `[dependencies]` and the crate cannot see build-dependencies.

## Overriding dependencies

- `[patch.crates-io] foo = { path = "../foo" }` (not `[patch.crates.io]`; Cargo hints at the typo). The patched version must satisfy the requirements, or `cargo update -p foo --precise VER` is needed. It applies to the whole graph and only in the root manifest; patches in dependencies are ignored.
- Patch a git source by URL: `[patch."https://github.com/org/repo"]`. Patch two versions of one crate with distinct keys and `package = "foo"`.
- `features` and `default-features` inside `[patch]` are ignored (warning).
- `[patch]` may also live in config or on the command line for an uncommitted local override: `--config 'patch.crates-io.rand.path="../rand"'`. A config patch beats a manifest patch for the same dependency.
- `[replace]` is deprecated; use `[patch]`. `paths = [...]` in config is a narrow legacy override that cannot change the graph.

## Source replacement and vendoring

- `[source.crates-io] replace-with = "vendored"` plus `[source.vendored] directory = "vendor"` (or `registry`, `local-registry`, `git`). A replacement must hold exactly the same code; it is not for patching or for private registries (use `[patch]` and `[registries]`).
- `cargo vendor` copies every registry and git dependency into `vendor/` and **prints the `[source]` config to stdout**; redirect it into `.cargo/config.toml`. Vendored sources are read-only: edit through `[patch]`. `.cargo-checksum.json` guards against accidents, not attacks.
- With crates-io replaced, commands that talk to the registry need `--registry`.

## How the resolver chooses

- It prefers the highest version, but versions already in `Cargo.lock` win while they still match. `--locked` makes a needed lockfile change an error; `--frozen` adds `--offline`.
- SemVer-compatible requirements unify to one version; incompatible ones (`0.6` and `0.7`) build two copies whose types are distinct, which surfaces as "expected `Foo`, found `Foo`" errors. Conflicting exact pins fail resolution.
- Two packages with the same `links` value cannot coexist; this is a common cause of "failed to select a version for ...".
- Yanked versions are skipped unless already locked or requested with `cargo update --precise`.
- The lockfile is computed as if all features of all members were on; real feature sets come later.
- `cargo update foo` updates only `foo` (and its dependencies if required). `--recursive` forces its dependencies too; it cannot combine with `--precise` (measured). `cargo update -w` updates only workspace members, for use after a version bump. `cargo generate-lockfile` re-resolves everything to latest.
- Dev-dependency cycles are allowed but make a library's unit tests link two copies of the crate.

## rust-version (MSRV)

- `rust-version = "1.85"`: a bare version, no operators. It applies to every target of the package.
- Resolver 3 is the default for edition 2024; for other editions opt in with `resolver = "3"` or `resolver.incompatible-rust-versions = "fallback"` in config (respected since 1.84). `--ignore-rust-version`, an explicit requirement higher than any compatible version, or `cargo update --precise` override the preference.
- Raising `rust-version` is treated as a minor change. The Cargo Book suggests publishing a policy (for example "latest stable" or "N-2") and checking it in CI with `cargo hack check --rust-version --workspace --all-targets --ignore-private`.
- In a workspace with mixed MSRVs, resolution is shared: one member's low `rust-version` can hold back versions for all members.
- Using TOML 1.1 syntax in `Cargo.toml` (parsed since 1.94) raises the MSRV needed to develop the package; the published, normalized manifest stays readable by older Cargo.
