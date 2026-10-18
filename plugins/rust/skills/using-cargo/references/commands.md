# The cargo command surface

Contents:
- [Options shared by most commands](#options-shared-by-most-commands)
- [Defaults that differ between commands](#defaults-that-differ-between-commands)
- [Build commands](#build-commands)
- [Manifest and lockfile commands](#manifest-and-lockfile-commands)
- [Package and install commands](#package-and-install-commands)
- [Machine-readable output](#machine-readable-output)
- [Not on stable](#not-on-stable)

Every command exits `0` on success and `101` on failure.

## Options shared by most commands

- **Global:** `+toolchain` (rustup; first argument), `--config KEY=VALUE|FILE`, `-v`/`-vv` (`-vv` adds dependency warnings and build-script output), `-q`, `--color`, `--locked` (fail if `Cargo.lock` is missing or would change), `--offline`, `--frozen` (both), `-Z` (nightly). `cargo -C DIR` is nightly-only (measured "the `-C` flag is unstable"); on stable use `--manifest-path PATH` or its short form `-m` (1.97; `cargo check -m path/Cargo.toml` measured).
- **Package selection:** `-p SPEC` (repeatable; quoted globs), `--workspace`, `--exclude SPEC`. SPEC is a package ID spec: `name`, `name@1.4`, `name@1.4.3`, or a fully qualified `registry+https://...#name@1.4.3`.
- **Target selection:** `--lib`, `--bin NAME`, `--bins`, `--example NAME`, `--examples`, `--test NAME`, `--tests`, `--bench NAME`, `--benches`, `--all-targets` (lib, bins, tests, benches, examples; never doctests). `--test NAME` selects a test *target* (a file in `tests/`), not a test function.
- **Features:** `-F`/`--features`, `--all-features`, `--no-default-features`.
- **Compilation:** `--target TRIPLE` (repeatable; `host-tuple` since 1.91), `-r`/`--release`, `--profile NAME`, `--target-dir`, `-j N`, `--keep-going` (1.74; not on `test` or `bench`), `--timings` (HTML in `target/cargo-timings/`; `--timings=html` and `=json` are rejected, measured), `--message-format human|short|json|json-render-diagnostics|...`, `--future-incompat-report`, `--ignore-rust-version`.

## Defaults that differ between commands

| Question | Answer |
|---|---|
| Which targets build by default? | `build`, `check`, `doc`, `rustc`: lib and bins. `test`: also examples (compile only), integration tests, lib doctests. `fix`: default targets since 1.89 (measured). |
| Which `--target` by default? | Host for build commands; **every platform** for `cargo fetch`; host for `cargo tree` (`--target all` for every one); every platform in `cargo metadata`'s `resolve` unless `--filter-platform`. |
| Working directory of the program | `cargo run`: your current directory. `cargo test` and `cargo bench`: the package root. |
| Is `Cargo.lock` used? | Everywhere except `cargo install` without `--locked`. `cargo info` and `cargo generate-lockfile` create or rewrite it. |
| Does project config apply? | Yes, from the current directory upward; `cargo install` ignores it unless `--path`. |

## Build commands

- **`cargo check`:** no codegen. Some errors (linker errors, some lints and const evaluation) appear only in `cargo build`. Checks no tests unless `--all-targets` or `--profile test`.
- **`cargo build`:** bins missing `required-features` are skipped silently. `--artifact-dir` is nightly-only.
- **`cargo run`:** `cargo run [--bin NAME | --example NAME] -- ARGS`. With several binaries and no `default-run`, it asks you to choose. One package only.
- **`cargo rustc -- FLAGS`:** the flags go to the final crate only, never to dependencies, and need exactly one target selected. Trailing flags take precedence (1.85). `--crate-type lib,cdylib` overrides the manifest. `--print cfg` is nightly-only.
- **`cargo fix`:** refuses a dirty or VCS-less tree without `--allow-dirty` (which implies `--allow-staged`, 1.86) or `--allow-no-vcs`. Only code compiled in the chosen configuration is fixed, so repeat with `--all-features`, `--all-targets`, and each `--target` that gates code. Edition migration: `cargo fix --edition`, then change `edition` in `Cargo.toml` yourself (the flag does not edit the manifest), then build and test.
- **`cargo clean`:** `-p`, `--workspace` (1.93), `--release`, `--profile`, `--doc`, `--dry-run` (`-n`).
- **`cargo test`, `cargo bench`:** see `testing-rust`. Cargo-side facts: one positional filter only (measured: `cargo test foo bar` fails with "unexpected argument 'bar' found"; put more after `--`), `--no-fail-fast` instead of `--keep-going` (measured: "unexpected argument '--keep-going'").
- **`cargo doc`:** see `documenting-rust`.
- External, installed as rustup components: `cargo clippy`, `cargo fmt`, and `cargo miri` (nightly).

## Manifest and lockfile commands

- **`cargo add`:** `cargo add serde -F derive`, `cargo add tokio@1`, `cargo add --dev trybuild`, `--build`, `--target 'cfg(unix)'`, `--optional` (creates `name = ["dep:name"]`, 1.76), `--rename`, `--path`, `--git`, `--dry-run`, `-p MEMBER`. It picks the newest version compatible with `rust-version` (1.79). An already-present dependency is updated in place.
- **`cargo remove`:** `--dev`, `--build`, `--target`. It suggests the right table when the dependency lives elsewhere (1.95).
- **`cargo update`:** `cargo update` (everything), `cargo update foo` (conservative), `--precise VER` (a yanked version is allowed; a pre-release outside the requirement is nightly-only), `--recursive` (not with `--precise`, measured), `-w`, `--dry-run`. `--breaking` is nightly-only.
- **`cargo generate-lockfile`:** re-resolves everything to latest.
- **`cargo tree`:** `-i CRATE`, `-d`, `-e features`, `-e normal,build` (roughly what `cargo build` builds; plain `cargo tree` approximates `cargo test`), `--depth N`, `--depth workspace` (1.85), `--prune`, `--no-dedupe`, `-f "{p} {f}"`, `--target all`. `(*)` marks a subtree printed earlier.
- **`cargo info CRATE[@VER]`** (1.82): registry metadata; it picks a version compatible with `rust-version` (measured: "version: 4.4.18 (latest 4.6.7)").
- **`cargo metadata --format-version 1`:** always pass the flag (omitting it warns, measured). Tolerate new fields and do not parse `source` or `id` strings; parse with the `cargo_metadata` crate. `--no-deps` lists members only.
- **`cargo locate-project --workspace --message-format plain`:** prints the root manifest path; useful in scripts.
- **`cargo vendor`:** see `manifest-and-dependencies.md`.

## Package and install commands

- **`cargo new` / `cargo init`:** `--lib`, `--bin` (default), `--edition` (default 2024; 2015, 2018, 2021, 2024), `--vcs none|git|...` (no new repository inside an existing one), `--name`. `cargo init` refuses to run in your home directory (1.95). Inside a workspace, `cargo new` adds the member.
- **`cargo install`:** from crates.io, `--git`, or `--path .`. Builds **release** in a temporary target directory (set `CARGO_TARGET_DIR` to cache in CI). `--version 1.2.3` installs exactly that version, not a caret range. It ignores the packaged lockfile unless `--locked`. `--root`, `--force`, `--list`. Installed into `$CARGO_HOME/bin`. Reinstalls automatically when the version, features, profile, or target changed. `cargo uninstall NAME` removes it.
- **`cargo package`, `cargo publish`, `cargo yank`, `cargo owner`, `cargo login`, `cargo logout`:** see `publishing-and-semver.md`.
- **`cargo search QUERY`**, **`cargo pkgid`** (needs a lockfile), **`cargo report future-incompatibilities --id N`** (detail for the end-of-build "will be rejected by a future version of Rust" notice).
- `cargo verify-project` and `cargo read-manifest` are deprecated; use `cargo metadata`.

## Machine-readable output

- `--message-format json`: one JSON object per line on stdout with `reason` = `compiler-message`, `compiler-artifact` (`filenames`, `executable`, `fresh`, `profile`, `features`), `build-script-executed`, or `build-finished`. `package_id` is a package ID spec (1.77). Programs run by Cargo and proc macros can print to the same stream, so treat only lines starting with `{` as JSON.
- Test executables are not copied into `target/debug`; take their paths from the `executable` field of `cargo test --no-run --message-format json`.
- A custom subcommand is an executable `cargo-NAME` on `PATH`. It receives `NAME` as its first argument, finds Cargo through the `CARGO` variable, and should call `cargo metadata` rather than link the `cargo` crate.

## Not on stable

On 1.97.1, all of these need nightly and a `-Z` flag, `-Z unstable-options`, or `cargo-features`, whatever older posts say: `cargo -C`, `--artifact-dir`, `--unit-graph`, `--build-plan` (removed in 1.93), `cargo config get`, `cargo update --breaking`, `cargo install --dry-run`, `cargo rustc --print`, `cargo doc --output-format json`, `-Zbuild-std`, `-Zscript`, `-Zminimal-versions`, `-Zdirect-minimal-versions`, `-Zpublic-dependency`, `-Zbindeps`, `-Ztrim-paths`, `-Zcargo-lints`, `-Zgc` subcommands, `-Zhost-config`, `-Zfeature-unification`, `-Zsbom`, `-Zpanic-abort-tests`, `-Zmin-publish-age`, `-Zhint-msrv`. Measured: `-Z` on stable fails with "the `-Z` flag is only accepted on the nightly channel of Cargo".
