---
name: using-cargo
description: Configures and drives Cargo on current stable Rust — Cargo.toml and dependency specs, features, workspaces and inheritance, the MSRV-aware resolver and Cargo.lock, profiles, build scripts, .cargo/config.toml and environment variables, RUSTFLAGS and rustc codegen options, targets and cross-compilation, SemVer compatibility, and publishing to crates.io or another registry. Use when the user edits or asks about Cargo.toml, a workspace, a feature flag, a [patch], the lockfile, rust-version, a profile, build.rs, config.toml, RUSTFLAGS, --target, or cargo publish, yank, or owner. Also use for symptoms that point at Cargo without naming it - a dependency resolved at the wrong version or built twice, a feature turned on that nobody asked for, a crate that rebuilds every time, compiler flags that silently stop applying, a CI job that keeps rewriting the lockfile, a build that breaks on an older toolchain, a cross build that cannot find std or a linker, or a release that broke downstream users.
license: MIT
---

# Using Cargo

Cargo changed a great deal between 1.74 and 1.97, and most of the change is invisible in training data: an MSRV-aware resolver that is the default for edition 2024, a lockfile that is always published, `build.warnings`, `build.build-dir`, config `include`, and stricter workspace rules. This skill corrects the stale defaults first and keeps the reference material in `references/`.

**Version basis.** Sourced from the Rust 1.99 stable documentation (Cargo Book, rustc book), fetched 2026-10-17. Every behaviour marked *measured* was run on rustc/cargo **1.97.1**. Items marked **1.98+** come from the 1.99 docs and could not be measured. Run `cargo --version` before relying on one of them.

Out of scope: what a lint *means* and how to fix a compiler error (`fixing-rust-compile-errors`), the test harness and `cargo test` filters (`testing-rust`), doc comments and `cargo doc` flags (`documenting-rust`), language semantics (`writing-rust`), which Clippy lints to enable and `clippy.toml` (`linting-and-formatting-rust`), public API design (`designing-rust-apis`).

## Corrections to carry into every answer

### Resolver, MSRV, and the lockfile

- **Edition 2024 implies `resolver = "3"`**, which is MSRV-aware: it prefers dependency versions whose `rust-version` is no newer than yours, and falls back to an incompatible version rather than failing (`resolver.incompatible-rust-versions = "fallback"`). Measured with `rust-version = "1.70"` and `clap = "4"`: resolver 3 locks clap 4.4.18 ("available: v4.6.7, requires Rust 1.85"); resolver 2 locks 4.6.7. Edition 2021 means resolver 2, which ignores `rust-version` when resolving.
- **A virtual workspace never infers the resolver.** Without `workspace.resolver` it uses resolver **1**, even when every member is edition 2024 (measured warning: "virtual workspace defaulting to `resolver = "1"` despite one or more workspace members being on edition 2024"). Always write `resolver = "3"` under `[workspace]`.
- `rust-version` newer than the toolchain is a hard error ("rustc 1.97.1 is not supported by the following package"); `--ignore-rust-version` overrides it. `cargo add` also respects it (measured: "ignoring tokio@1.53.3 (which requires rustc 1.71) to maintain msrv's rust-version of 1.70").
- The lockfile format follows `rust-version`: v4 with no `rust-version` or with 1.83+, v3 for 1.82 and below (measured at 1.70, 1.77, 1.78, 1.82, 1.83), although Cargo reads v4 from 1.78.
- **Commit `Cargo.lock` for libraries too** (the documented default since 1.74). It never affects your dependents; only `Cargo.toml` does.
- **`cargo package` and `cargo publish` always include `Cargo.lock`** (1.84), even for a library with no binary. Measured: `cargo package --list` on a fresh `--lib` prints `Cargo.lock`. `cargo install` ignores the packaged lockfile unless `--locked`.
- CI that checks latest dependencies sets `CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=allow` before `cargo update`, otherwise the MSRV-aware resolver holds versions back.

### Warnings, flags, and rebuilds

- **`build.warnings = "deny"` replaces `RUSTFLAGS=-Dwarnings` (stable 1.97).** Values are exactly `warn | allow | deny`. Measured: it fails the build with exit 101 and "warnings are denied by `build.warnings` configuration" without recompiling anything, while `RUSTFLAGS=-Dwarnings` recompiled the whole graph. It covers local packages only, path dependencies included. Add `--keep-going` to see every crate's warnings before it fails. Set it as `CARGO_BUILD_WARNINGS=deny` in CI.
- **RUSTFLAGS sources do not merge; the first one present wins**: `CARGO_ENCODED_RUSTFLAGS` > `RUSTFLAGS` > every matching `target.<triple>.rustflags` and `target.<cfg>.rustflags` (joined) > `build.rustflags`. Measured: setting `RUSTFLAGS` silently dropped `build.rustflags`, and `target.'cfg(unix)'.rustflags` dropped `build.rustflags`.
- **With `--target`, build scripts and proc macros get no RUSTFLAGS** (measured: the flag reached the crate but not `build_script_build`). Without `--target` the flags reach everything. Pass `--target <host triple>` to keep flags such as `-C target-cpu=native` or PGO instrumentation off host artifacts.
- Changing RUSTFLAGS no longer discards the cache (1.85): switching back rebuilt nothing (measured).

### Features and workspaces

- **Features unify across everything selected in one invocation.** Measured with members `a` and `b` enabling `shared/fa` and `shared/fb`: `cargo run -p a` saw `fa`; after `cargo build --workspace` the same `a` binary saw `fa+fb`. Running at a virtual workspace root selects every member, and so does every path dependency inside the workspace directory, because those become members automatically.
- **`--all-targets` changes your normal binary.** Dev-dependency features unify into normal dependencies whenever a target that needs them is built. Measured: a feature enabled only in `[dev-dependencies]` was off after `cargo build -p a` and on in the `a` binary after `cargo build -p a --all-targets`.
- **Inherited `default-features` on 1.97:** in an edition 2024 member, `dep = { workspace = true, default-features = false }` is a hard error ("`default-features = false` cannot override workspace's `default-features`"). In edition 2021 it is ignored with a warning, and the defaults stay on. The rule that works on every version: put `default-features = false` in `[workspace.dependencies]`, and let a member that needs the defaults write `default-features = true`. The 1.99 docs allow the member-level override in edition 2024 (**1.98+**).
- **`[workspace.lints]` is not inherited implicitly.** Each member needs `[lints] workspace = true` (measured: a member without it ignored a workspace-level `unsafe_code = "forbid"`). A `[lints]` table in a virtual root is an error.
- **A lint group needs a lower priority than the lints that override it**: `pedantic = { level = "warn", priority = -1 }`. Measured: equal priorities make `cargo clippy` fail with "lint group `pedantic` has the same priority (0) as a lint".
- **`dep:` removes the implicit feature.** Once `[features]` mentions `dep:foo`, `--features foo` is an error ("the `features` table includes it with the "dep:" syntax"). Use it to keep optional dependencies out of your public feature set.
- `cfg(feature = ...)`, `cfg(test)`, and `cfg(debug_assertions)` do nothing in `[target.'cfg(..)'.dependencies]`. Cargo warns "This key is not supported for selecting dependencies". Use `[features]` with optional dependencies.

### Build scripts

- Directives are `cargo::KEY=VALUE` (1.77; requires `rust-version` ≥ 1.77, otherwise use the old `cargo:` form). `cargo::error=MSG` (1.84) fails the build.
- **Every custom cfg needs `cargo::rustc-check-cfg=cfg(name)`**, or the crate gets `unexpected cfg condition name` warnings (measured). For static cfgs, use `[lints.rust] unexpected_cfgs = { level = "warn", check-cfg = ['cfg(name)'] }`.
- **`cfg!` and `#[cfg]` in build.rs describe the host.** Read the target from `CARGO_CFG_TARGET_OS` and the other `CARGO_CFG_*` variables. `RUSTFLAGS` is not in the build-script environment (measured); read `CARGO_ENCODED_RUSTFLAGS`.
- An environment variable that the script reads is not tracked unless the script prints `cargo::rerun-if-env-changed=VAR` (measured: without it, setting the variable re-ran nothing).

### Nightly-only, even though models present them as stable

`cargo -C <dir>` ("the `-C` flag is unstable", measured; use `--manifest-path`, or `-m` since 1.97), `-Zbuild-std`, single-file `cargo script` (`-Zscript`), `[lints.cargo]` (measured: "unused manifest key"), profile `trim-paths`, artifact dependencies (`-Zbindeps`), `public = true` dependencies, `--artifact-dir`, `cargo config get`, `-Zminimal-versions` / `-Zdirect-minimal-versions`, `cargo update --breaking`, `resolver.feature-unification` (measured: "ignoring ... without `-Zfeature-unification`"), `[host]` config, `panic = "immediate-abort"`, `#[bench]`. Stable Cargo **silently ignores** an `[unstable]` table in config (measured), so its presence proves nothing.

### Smaller corrections

- `cargo fix` fixes only the default targets since 1.89. Pass `--all-targets` to reach tests and examples (measured: an unused import in `tests/` was untouched without it). `--edition` still implies all targets.
- `--release` and `--profile` together are an error. `--timings=html` is rejected; plain `--timings` writes `target/cargo-timings/cargo-timing.html`.
- `--profile debug` fails on 1.97 ("profile name `debug` is reserved"). The 1.99 docs describe a built-in `debug` profile (**1.98+**). On 1.97, define a custom `[profile.debugging] inherits = "dev"`.
- The `test` profile is unoptimized with full debuginfo (measured "Finished `test` profile [unoptimized + debuginfo]"). The `cargo test` page's claim that it "enables some optimizations" is wrong.
- Edition 2024 manifests reject `[project]` and underscore keys such as `dev_dependencies` (measured).
- `cargo publish --token` is soft-deprecated and hidden from `--help`. Positional `cargo login <token>` is hidden too; the token comes from stdin or a credential provider.
- Default symbol mangling is v0 (measured, no `_ZN` symbols). `-C symbol-mangling-version=legacy` requires `-Z unstable-options`.

## Publishing

Publishing is permanent: a version can never be overwritten, and a yank only hides it from new resolution. Before uploading, run `cargo publish --dry-run` (`-n`) and read `cargo package --list`. This plugin ships a hook that asks the user before `cargo publish` without `--dry-run`, `cargo yank`, and `cargo owner --add/--remove`. Expect that prompt, and do not try to route around it.

For the publish checklist, multi-package publishing, yanking, owners, registries and credential providers, and the SemVer rules, read `references/publishing-and-semver.md`.

## Diagnose before editing

| Symptom | Command |
|---|---|
| Why is this crate in the graph? | `cargo tree -i CRATE --workspace --target all --all-features` |
| Which dependency turned feature X on? | `cargo tree -e features -i CRATE` |
| Two versions of one crate | `cargo tree -d` (add `--target all`), then `cargo update CRATE --precise VER` |
| Why does this rebuild every time? | `CARGO_LOG=cargo::compiler::fingerprint=info cargo build` on the run that rebuilds; `cargo build -v` also names the reason |
| Why was the newer version not chosen? | `CARGO_LOG=cargo::resolver=trace cargo update -p CRATE` (log target names can change) |
| What flags did rustc get? | `cargo build -v` |
| Effective metadata for a tool | `cargo metadata --format-version 1` (omitting the flag warns) |

The usual cause of perpetual rebuilds is a build script that prints `rerun-if-changed` for a path that never exists, or alternating feature sets between commands (`-p one` and then `--workspace`).

## Where to look

Read only the file the question touches.

- `references/manifest-and-dependencies.md`: `[package]` fields, target auto-discovery, version requirements, git, path, and renamed dependencies, `[patch]`, source replacement and vendoring, how the resolver picks versions and duplicates, `rust-version` policy. Read it when editing a dependency entry or debugging resolution.
- `references/features-and-workspaces.md`: feature syntax and unification rules, workspace layout, inheritance, package selection, and the `[lints]` table. Read it for any feature or multi-crate question.
- `references/profiles-config-and-env.md`: profile defaults and overrides, which command uses which profile, `.cargo/config.toml` discovery and merging, `include`, the key catalogue (`build.warnings`, `build-dir`, `resolver.lockfile-path`, `[env]`, `[alias]`), and environment variables Cargo reads and sets. Read it when tuning builds, CI, or configuration.
- `references/build-scripts.md`: every `cargo::` directive, the build-script environment, `links` and `*-sys` crates, code generation into `OUT_DIR`, and overriding a build script from config. Read it before writing or debugging `build.rs`.
- `references/publishing-and-semver.md`: package contents, publish and yank behaviour, owners, alternate registries and credential providers, and the SemVer compatibility rules. Read it before a release or when judging whether a change is breaking.
- `references/commands.md`: options shared by all commands (once), then what is specific to each command, including defaults that differ between commands. Read it when a flag is in doubt.
- `references/targets-and-cross-compilation.md`: platform tiers, renamed targets, the cross-compilation recipe, linkers and runners, rustc `-C` codegen options, LTO, PGO, sanitizer targets, WebAssembly, Apple, and bare metal. Read it for `--target`, linker, or codegen questions.
