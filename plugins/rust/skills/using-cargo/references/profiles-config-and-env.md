# Profiles, configuration, and environment

Contents:
- [Profiles](#profiles)
- [Profile overrides](#profile-overrides)
- [Config file discovery and merging](#config-file-discovery-and-merging)
- [Key catalogue](#key-catalogue)
- [RUSTFLAGS and rustdoc flags](#rustflags-and-rustdoc-flags)
- [Output directories](#output-directories)
- [Environment variables Cargo reads](#environment-variables-cargo-reads)
- [Environment variables Cargo sets for crates](#environment-variables-cargo-sets-for-crates)

## Profiles

Which profile a command uses by default:

| Command | Profile | Output directory |
|---|---|---|
| `build`, `check`, `run`, `rustc` | `dev` | `target/debug` |
| `test` | `test` (inherits `dev`) | `target/debug` |
| `bench` | `bench` (inherits `release`) | `target/release` |
| `install` | `release` | temporary directory |

`--release` means `--profile release`; combining it with `--profile` is an error. A custom profile needs `inherits` and builds into `target/<name>`. `cargo check --profile test` checks `#[cfg(test)]` code. `debug` is a reserved profile name on 1.97 (measured); the 1.99 docs describe it as a built-in debugger profile (**1.98+**).

| Key | `dev` | `release` | Notes |
|---|---|---|---|
| `opt-level` | `0` | `3` | `1`, `2`, `3`, `"s"`, `"z"`. 3 is not always faster than 2, and `"z"` is not always smaller than `"s"`; measure. |
| `debug` | `true` (`2`, `"full"`) | `false` | Also `"line-tables-only"` (file:line backtraces only, the cheap choice for dev), `"limited"` (`1`), `"line-directives-only"`. Named levels need 1.71. |
| `strip` | `"none"` | `"none"` | `"debuginfo"`, `"symbols"`; `true` = `"symbols"`. When `debug` is off and `strip` unset, Cargo strips debuginfo (measured `-C strip=debuginfo` in release), except on Windows MSVC. |
| `split-debuginfo` | `unpacked` on macOS | | Otherwise rustc's platform default. |
| `debug-assertions`, `overflow-checks` | on | off | |
| `lto` | `false` | `false` | `true`/`"fat"`, `"thin"`, `"off"`. `false` still does thin-local LTO across codegen units; only `"off"` disables LTO. |
| `panic` | `"unwind"` | `"unwind"` | `"abort"` is ignored for tests, benches, build scripts, and proc macros. |
| `codegen-units` | 256 | 16 | `1` gives the best code and the slowest build. |
| `incremental` | on | off | Only for workspace members and path dependencies. Defaults off when the `CI` environment variable is set. |

Build scripts, proc macros, and their dependencies build with `opt-level = 0` and no debuginfo, even in release (measured: no `opt-level` flag on `build_script_build` under `--release`). Raise it with `[profile.release.build-override]` when a build script does heavy work.

A recipe from the Cargo Book for faster dev builds:

```toml
[profile.dev]
debug = "line-tables-only"
[profile.dev.package."*"]
debug = false
[profile.debugging]          # cargo build --profile debugging, for a real debugger session
inherits = "dev"
debug = true
```

## Profile overrides

- `[profile.dev.package.foo]` (a package spec, may include a version), `[profile.dev.package."*"]` (every non-member dependency), `[profile.dev.build-override]`.
- Precedence: named package > `"*"` > `build-override` > `[profile.dev]` > defaults. Overrides cannot set `panic`, `lto`, or `rpath`.
- Generic code is compiled in the crate that instantiates it, so raising `opt-level` for a generic-heavy dependency may change nothing.
- Profiles are read only from the root manifest. Config (`[profile.release]` in `.cargo/config.toml`) and `CARGO_PROFILE_RELEASE_LTO=true` override the manifest; `profile.<name>.package.<pkg>` cannot be set by environment variable.

## Config file discovery and merging

- Cargo reads `.cargo/config.toml` in the current directory and every parent, then `$CARGO_HOME/config.toml`. The current directory, not the manifest location, decides: running from the workspace root does not read a member's `.cargo/config.toml`. `cargo install` ignores project config unless given `--path`.
- Deeper files win for scalars; arrays are concatenated. Keys that hold a program plus arguments (`target.*.runner`, `credential-provider`, `doc.browser`, `credential-alias.*`) are replaced, not concatenated (1.86).
- Precedence: `--config` > environment variables > files. `--config KEY=VALUE` takes TOML (`--config 'build.rustflags=["-C","target-cpu=native"]'`), or a path to a `.toml` file; it repeats and merges left to right.
- Environment form: `build.jobs` is `CARGO_BUILD_JOBS`; dots and dashes become `_`, all uppercase. `CARGO_TARGET_<TRIPLE>_LINKER` needs the triple uppercased with `-` and `.` turned to `_`.
- The extensionless `.cargo/config` is deprecated (1.78); when both exist, Cargo reads the extensionless one.
- Paths in config files are relative to the parent of the `.cargo` directory; paths in `--config KEY=VALUE` and environment variables are relative to the current directory.
- **`include`** (stable 1.94; the "Stabilized" page says 1.93, the changelog lists it under 1.94) loads more config files before the file's own keys, which then override them. Measured forms on 1.97.1:
  - `include = ["extra.toml"]` and `include = [{ path = "extra.toml" }]` work; the path is relative to the including file.
  - `include = "extra.toml"` (a bare string) is rejected.
  - A missing file is an error unless `{ path = "...", optional = true }`.
  - The path must end in `.toml`.

## Key catalogue

| Key | Env | Meaning |
|---|---|---|
| `build.warnings` | `CARGO_BUILD_WARNINGS` | `warn` (default), `allow`, `deny`. Local packages' lint warnings only. Stable 1.97. |
| `build.jobs` | `CARGO_BUILD_JOBS` | Default: logical CPUs; negative counts back; `"default"` resets; never 0. |
| `build.target` | `CARGO_BUILD_TARGET` | Triple, array of triples, `"host-tuple"` (1.91), or a path to a target JSON (nightly). |
| `build.target-dir` | `CARGO_TARGET_DIR` | Final artifacts. Default `target/` at the workspace root. |
| `build.build-dir` | `CARGO_BUILD_BUILD_DIR` | Intermediate artifacts (stable 1.91). Templates `{workspace-root}`, `{cargo-cache-home}`, `{workspace-path-hash}`. Its layout is unstable. |
| `build.rustc-wrapper` | `RUSTC_WRAPPER` | For example `sccache`. An empty value disables a configured wrapper. |
| `build.rustc-workspace-wrapper` | `RUSTC_WORKSPACE_WRAPPER` | Members only; artifacts cached separately. |
| `build.rustflags`, `build.rustdocflags` | | Lowest-precedence flag source; see below. |
| `build.incremental` | `CARGO_INCREMENTAL` | |
| `resolver.incompatible-rust-versions` | `CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS` | `allow` or `fallback`. Default follows the resolver version. |
| `resolver.lockfile-path` | `CARGO_RESOLVER_LOCKFILE_PATH` | Stable 1.97. Must end in `Cargo.lock` (measured error otherwise). Ignored by `cargo install`. For read-only source trees. |
| `[env]` | | `FOO = "x"` or `{ value, force = true, relative = true }`. Does not override an existing variable without `force`. Cannot set `CARGO_HOME`, `RUSTUP_HOME`, `RUSTUP_TOOLCHAIN`, or variables Cargo sets. |
| `[alias]` | `CARGO_ALIAS_<NAME>` | Built-ins `b c d t r rm`. An alias cannot redefine a built-in command. |
| `target.<triple>.linker`, `.runner`, `.rustflags`, `.rustdocflags` | `CARGO_TARGET_<TRIPLE>_*` | A triple beats a cfg. Two matching cfg `linker` or `runner` entries is an error. `runner` applies to `run`, `test`, and `bench`. |
| `target.<triple>.<links>` | | Replaces a `links` package's build script; see `build-scripts.md`. |
| `net.offline`, `net.git-fetch-with-cli`, `net.retry` | | `git-fetch-with-cli = true` shells out to `git` for SSH config and credential helpers Cargo does not support. |
| `cache.auto-clean-frequency` | | Automatic cache cleanup, stable 1.88: unused downloads go after 3 months, regenerable files after 1 month. `"never"` disables it. |
| `registries.<name>.index`, `registry.default`, `registry.global-credential-providers` | | See `publishing-and-semver.md`. |
| `term.color`, `term.verbose`, `term.progress.when` | `CARGO_TERM_COLOR`, ... | |

Stable Cargo ignores an `[unstable]` table silently (measured).

## RUSTFLAGS and rustdoc flags

Exactly one source applies, the first present (measured on 1.97.1):

1. `CARGO_ENCODED_RUSTFLAGS` (arguments separated by `0x1f`; use it when an argument contains a space)
2. `RUSTFLAGS`
3. every matching `target.<triple>.rustflags` and `target.'cfg(..)'.rustflags`, joined
4. `build.rustflags`

rustdoc has the same chain (`CARGO_ENCODED_RUSTDOCFLAGS`, `RUSTDOCFLAGS`, `target.*.rustdocflags`, `build.rustdocflags`).

- With `--target` (or `build.target`), none of these reach build scripts or proc macros. Without it, they reach every rustc call. `target.<host>.linker` still applies to host artifacts under `--target`.
- `target.'cfg(..)'` matches only rustc's built-in cfgs plus `--cfg` from RUSTFLAGS; it never matches `feature`, `test`, `debug_assertions`, or cfgs from build scripts.
- Do not pass what a profile manages (`-C opt-level`, `-C debuginfo`, `-C lto`) through RUSTFLAGS.
- To fail CI on warnings, use `build.warnings = "deny"`, not `RUSTFLAGS=-Dwarnings`; the latter recompiles everything and differs from local builds.

## Output directories

- `target/debug`, `target/release`, `target/<profile>`; with `--target T`, `target/T/<profile>` (measured with `--target host-tuple`: `target/aarch64-apple-darwin/`). Examples in `<profile>/examples`; `target/doc`; `target/package`.
- With `build.build-dir` set, `deps/`, `build/`, and `incremental/` move there while executables stay in the target directory (measured).
- `cargo clean` refuses a `--target-dir` that does not look like a Cargo target directory (1.97, measured: "cleaning has been aborted to prevent accidental deletion of unrelated files"). `cargo clean --workspace` (1.93) cleans members only. `cargo clean --doc` removes stale docs; `cargo doc` output accumulates otherwise.
- `cargo clean` never touches `$CARGO_HOME`. In CI, cache `$CARGO_HOME/{bin,registry/index,registry/cache,git/db}` and `.crates.toml`/`.crates2.json`, not `registry/src` or `git/checkouts`.

## Environment variables Cargo reads

`CARGO_HOME`, `CARGO_TARGET_DIR`, `CARGO_LOG` (for example `cargo::resolver=trace`; not `RUST_LOG`), `RUSTC`, `RUSTDOC`, `RUSTC_WRAPPER`, `RUSTC_WORKSPACE_WRAPPER`, `RUSTFLAGS`, `CARGO_ENCODED_RUSTFLAGS`, `RUSTDOCFLAGS`, `CARGO_INCREMENTAL`, `CARGO_BUILD_*` and the other config mirrors, `CARGO_REGISTRY_TOKEN`, `CARGO_REGISTRIES_<NAME>_TOKEN`, `HTTPS_PROXY`, `HTTP_TIMEOUT`, `CARGO_TERM_COLOR`, `CI` (turns off the progress bar and incremental by default).

## Environment variables Cargo sets for crates

At compile time (read with `env!`; unset manifest fields give `""`):

- `CARGO_PKG_NAME`, `CARGO_PKG_VERSION` (and `_MAJOR`, `_MINOR`, `_PATCH`, `_PRE`), `CARGO_PKG_AUTHORS`, `CARGO_PKG_DESCRIPTION`, `CARGO_PKG_HOMEPAGE`, `CARGO_PKG_REPOSITORY`, `CARGO_PKG_LICENSE`, `CARGO_PKG_LICENSE_FILE`, `CARGO_PKG_README`, `CARGO_PKG_RUST_VERSION` (the package's MSRV, not the running toolchain).
- `CARGO_MANIFEST_DIR`, `CARGO_MANIFEST_PATH` (1.83), `CARGO_CRATE_NAME` (with `_`), `CARGO_BIN_NAME`, `CARGO_PRIMARY_PACKAGE`, `OUT_DIR` (when the package has a build script).
- Integration tests and benches only: `CARGO_BIN_EXE_<name>` (exact binary name, e.g. `CARGO_BIN_EXE_my-tool`; at runtime too since 1.94), `CARGO_TARGET_TMPDIR`.
- `cargo run` and `cargo test` also set the dynamic-library search path (`DYLD_FALLBACK_LIBRARY_PATH`, `LD_LIBRARY_PATH`, `PATH` on Windows) to include `target/<profile>/deps` and build-script search paths inside the target directory.

`env!` and `option_env!` variables are tracked for rebuilds automatically (since 1.46). For the build-script environment, see `build-scripts.md`.
