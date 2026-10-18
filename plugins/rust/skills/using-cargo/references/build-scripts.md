# Build scripts

Contents:
- [When and how it runs](#when-and-how-it-runs)
- [Directives](#directives)
- [Rerun rules](#rerun-rules)
- [The build-script environment](#the-build-script-environment)
- [Generating code](#generating-code)
- [Native libraries, `links`, and `*-sys` crates](#native-libraries-links-and--sys-crates)
- [Overriding a build script from config](#overriding-a-build-script-from-config)

## When and how it runs

- `build.rs` at the package root is compiled and run before the package; `build = "path.rs"` moves it, `build = false` disables discovery. Its working directory is the package root. A non-zero exit fails the build.
- It can use only `[build-dependencies]`. When cross-compiling, those are built for the host, separately from the target's copies.
- Output goes to `target/<profile>/build/<pkg>-<hash>/output` (and `stderr`). Cargo hides it unless the build fails or you pass `-vv`.
- `cargo::warning=` messages are shown only for local (path or workspace) packages unless `-vv`.
- Helper crates: `cc`, `pkg-config`, `cmake`, `bindgen`, `autocfg`, `build-rs` (typed access to the variables below, and it emits rerun directives for the Cargo variables it reads).

## Directives

Printed to stdout as `cargo::KEY=VALUE`. The double-colon form needs Rust 1.77; for a lower `rust-version`, use the old `cargo:KEY=VALUE`, where an unknown key is treated as metadata. Other stdout lines are ignored. Order can matter for link arguments.

| Directive | Effect |
|---|---|
| `rerun-if-changed=PATH` | Rerun when PATH's mtime changes; a directory is scanned recursively. |
| `rerun-if-env-changed=VAR` | Rerun when VAR changes. Cannot watch variables Cargo itself sets. |
| `rustc-cfg=KEY[="VALUE"]` | Sets `#[cfg(KEY)]`; cannot enable features or optional dependencies. |
| `rustc-check-cfg=cfg(KEY, values("a","b"))` | Declares the cfg for the `unexpected_cfgs` check (1.80). Declare every possible name and value, not just the one emitted. |
| `rustc-env=VAR=VALUE` | Visible to `env!` in the crate. |
| `rustc-link-lib=[KIND[:MODIFIERS]=]NAME[:RENAME]` | KIND `dylib`, `static`, or `framework`. Passed only to the library target if one exists. |
| `rustc-link-search=[KIND=]PATH` | KIND `dependency`, `crate`, `native`, `framework`, or `all`. |
| `rustc-link-arg=FLAG` | For bins, cdylibs, examples, tests, benches. Narrow it with `rustc-link-arg-bin=NAME=FLAG`, `-bins`, `-tests`, `-examples`, `-benches`, `-cdylib`. |
| `rustc-flags=FLAGS` | Only `-l` and `-L`. |
| `metadata=KEY=VALUE` | For `links` packages: direct dependents' build scripts get `DEP_<LINKS>_<KEY>`. |
| `warning=MESSAGE` | Shown as `warning: pkg@ver: MESSAGE`. |
| `error=MESSAGE` | Fails the build after the script exits (1.84). Measured: "error: flags@0.1.0: custom failure message", then "build script logged errors", exit 101. |

A custom cfg without `rustc-check-cfg` produces `warning: unexpected cfg condition name: has_foo` (measured). A library meant to be called from other build scripts should return `Result` rather than print `cargo::error`, so the caller decides.

## Rerun rules

- With no `rerun-if-*` directive, the script reruns when any file in the package changes. Emit at least one directive.
- `cargo::rerun-if-changed=build.rs` means "rerun only when the script itself changes".
- Once any `rerun-if-*` is emitted, nothing else is tracked. An environment variable the script reads is not tracked without `rerun-if-env-changed` (measured: changing it re-ran nothing).
- A `rerun-if-changed` path that never exists makes the script rerun on every build, a classic cause of perpetual rebuilds.
- `[env]` changes in config are detected (1.86).

## The build-script environment

Read with `std::env::var` at runtime, not `env!`.

- Target description: `TARGET`, `HOST`, and `CARGO_CFG_<CFG>` for every target cfg: `CARGO_CFG_TARGET_OS`, `_TARGET_ARCH`, `_TARGET_ENV`, `_TARGET_ABI`, `_TARGET_POINTER_WIDTH`, `_TARGET_ENDIAN`, `_TARGET_FEATURE`, `_TARGET_FAMILY` (multi-valued and comma-joined, e.g. `unix,wasm`), `CARGO_CFG_UNIX`, `CARGO_CFG_WINDOWS`, `CARGO_CFG_FEATURE` (1.85). `CARGO_CFG_DEBUG_ASSERTIONS` follows the profile (1.93; measured present and empty in dev, absent in release). `cfg(test)` is never available.
- **`cfg!()` and `#[cfg]` inside build.rs describe the host, not the target.**
- Profile: `OPT_LEVEL`, `DEBUG`, `PROFILE` (only `debug` or `release`, by inheritance, so prefer `OPT_LEVEL` and `DEBUG`).
- `OUT_DIR`: the only place a build script may write. It is not cleaned between builds.
- `CARGO_FEATURE_<NAME>`, `CARGO_MANIFEST_DIR`, `CARGO_MANIFEST_PATH`, `CARGO_MANIFEST_LINKS`, `CARGO_PKG_*`.
- `RUSTC`, `RUSTDOC`, `RUSTC_WRAPPER`, `RUSTC_WORKSPACE_WRAPPER`, `RUSTC_LINKER`, `CARGO_ENCODED_RUSTFLAGS`. **`RUSTFLAGS` is not set** (since 1.55; measured `None`).
- `CARGO_MAKEFLAGS` (jobserver; forward it as `MAKEFLAGS` to make), `NUM_JOBS` (historical). Each build script holds one job slot; use `cc` with its `parallel` feature for more.
- `DEP_<LINKS>_<KEY>` from dependencies' `metadata` (keyed by the `links` value, not the package name).

## Generating code

```rust
// build.rs
use std::{env, fs, path::Path};
fn main() {
    let out = Path::new(&env::var_os("OUT_DIR").unwrap()).join("gen.rs");
    fs::write(&out, "pub const N: u32 = 42;").unwrap();
    println!("cargo::rerun-if-changed=build.rs");
}
// src/lib.rs
include!(concat!(env!("OUT_DIR"), "/gen.rs"));
```

- Never write outside `OUT_DIR`. Registry sources must stay immutable, and `cargo package` verification fails a script that modifies the source tree.
- For generated files that are checked in, do not regenerate them in build.rs; add a test or CI step that regenerates to a temporary file and fails on a difference.
- Prefer `cc` to invoking `gcc` or `ar` yourself: it reads `TARGET`, `OPT_LEVEL`, `DEBUG`, and cross-compilation variables. Link from the build script rather than with `#[link]` in source.

## Native libraries, `links`, and `*-sys` crates

- A package with `links = "z"` must have a build script, and only one package per `links` value may exist in the graph. Two major versions of the same `-sys` crate therefore cannot coexist.
- Convention: `foo-sys` finds or builds `libfoo` and exposes raw declarations; a separate `foo` crate wraps them safely. Common shape: probe with `pkg-config`, fall back to a bundled source build, and let a feature or environment variable (e.g. `LIBZ_SYS_STATIC`) force the bundled build.
- Metadata passes only to direct dependents: `libz-sys` prints `cargo::metadata=include=...`, and a dependent's build script reads `DEP_Z_INCLUDE`.
- Version-dependent cfgs follow the openssl pattern: the `-sys` crate publishes a version number, and the dependent's script emits `rustc-check-cfg` and then `rustc-cfg` per capability.
- Edition 2024 FFI declarations are `unsafe extern "C" { ... }`.

## Overriding a build script from config

```toml
[target.x86_64-unknown-linux-gnu.foo]   # "foo" is the links value
rustc-link-lib = ["foo"]
rustc-link-search = ["/opt/foo/lib"]
rustc-cfg = ['key="value"']
metadata_key = "value"
```

With this, Cargo neither compiles nor runs that package's build script. `warning`, `rerun-if-changed`, and `rerun-if-env-changed` keys are ignored here.
