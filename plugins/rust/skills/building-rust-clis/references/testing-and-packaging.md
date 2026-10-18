# Testing and shipping a Rust CLI

Versions were checked 2026-10-17 with `cargo info` and crates.io. Every test below passed on rustc/cargo 1.97.1 against those versions. How `cargo test` selects and filters tests belongs to `testing-rust`. Profile keys and cross-compilation flags belong to `using-cargo`. This file covers what is specific to a binary.

## Contents

- [Test crates](#test-crates)
- [assert_cmd: which form, which version](#assert_cmd-which-form-which-version)
- [An integration test file](#an-integration-test-file)
- [Snapshot testing](#snapshot-testing)
- [What to test](#what-to-test)
- [cargo install](#cargo-install)
- [A release profile for a small binary](#a-release-profile-for-a-small-binary)
- [Distribution](#distribution)

## Test crates

| Crate | Use | Version (checked 2026-10-17) | Last release |
|---|---|---|---|
| `assert_cmd` | Run the built binary and assert on its status, stdout, and stderr | 2.2.2 (MSRV 1.85) | 2026-05-11 |
| `predicates` | Matchers: `predicate::str::contains`, `is_empty`, `.and()` | 3.1.4 | 2026-02-11 |
| `assert_fs` | Temporary files and directories, deleted on drop | 1.1.4 | 2026-05-26 |
| `snapbox` | Inline or file snapshots of command output | 1.2.2 | 2026-05-26 |
| `trycmd` | Whole CLI sessions written as `.toml` or Markdown `console` blocks | 1.2.1 | 2026-07-21 |
| `insta` | Snapshots of any string or serialized value; review with the `cargo-insta` tool | 1.49.0 | 2026-10-03 |
| `proptest` | Property tests for parsers and other pure logic | 1.12.0 (MSRV 1.88) | 2026-10-10 |
| `escargot` | Builds a binary with chosen features or profile from inside a test | 1.0.1 | 2026-10-18 |

All go under `[dev-dependencies]`.

## assert_cmd: which form, which version

- **`cargo_bin_cmd!("name")` needs assert_cmd 2.1.0 or later** (released 2025-10-28). 2.0.17 has `cargo_bin!` but not `cargo_bin_cmd!`. Against 2.0.17, `use assert_cmd::cargo::cargo_bin_cmd;` fails with the misleading E0603 ``function `cargo_bin_cmd` is private`` (measured). The book pins `assert_cmd = "2.0.14"` and calls the macro. A fresh resolve of that caret requirement picks 2.2.2 and works, but a `Cargo.lock` that holds 2.0.x fails. Write `assert_cmd = "2.2"`.
- **`Command::cargo_bin("name")` is not deprecated in 2.2.** 2.1.0 to 2.1.2 deprecated it ("incompatible with a custom cargo build-dir, see instead `cargo::cargo_bin!`"). 2.1.3 (2026-03-10) removed the deprecation, because it now reads `CARGO_BIN_EXE_<name>` at runtime. Either form works on 2.2.2 (measured). The macro reads the variable at compile time and needs no `unwrap`.
- `assert_cmd::crate_name!` is deprecated since 2.1.0. Use `pkg_name!`.
- **`CARGO_BIN_EXE_<name>`** holds the path of each `[[bin]]` target. Cargo sets it only for integration tests and benches. `env!("CARGO_BIN_EXE_lgrep")` reads it at compile time. Since Cargo 1.94 it is also set at runtime (measured on 1.97.1). From a unit test inside `src/`, the variable is unset, and assert_cmd panics with "`CARGO_BIN_EXE_<name>` is unset … move it to an integration test". `<name>` is the binary's name exactly, hyphens included.
- `std::process::Command::new(env!("CARGO_BIN_EXE_lgrep"))` works with no test crate at all.

## An integration test file

`tests/cli.rs`:

```rust
use assert_cmd::cargo::cargo_bin_cmd;
use assert_fs::prelude::*; // write_str comes from the FileWriteStr trait
use predicates::prelude::*;

#[test]
fn missing_file_fails_with_message() {
    cargo_bin_cmd!("lgrep")
        .args(["foobar", "test/file/doesnt/exist"])
        .assert()
        .failure()
        .code(2)
        .stderr(predicate::str::contains("could not read file"));
}

#[test]
fn finds_content_in_file() -> Result<(), Box<dyn std::error::Error>> {
    let file = assert_fs::NamedTempFile::new("sample.txt")?;
    file.write_str("A test\nActual content\nMore content\nAnother test")?;
    cargo_bin_cmd!("lgrep")
        .arg("test")
        .arg(file.path())
        .assert()
        .success()
        .stdout("A test\nAnother test\n");
    Ok(())
}

#[test]
fn reads_stdin_and_exits_1_on_no_match() {
    cargo_bin_cmd!("lgrep")
        .arg("zzz")
        .write_stdin("abc\n")
        .assert()
        .code(1)
        .stdout(predicate::str::is_empty());
}

#[test]
fn env_var_turns_on_ignore_case() {
    cargo_bin_cmd!("lgrep")
        .args(["lorem", "-"])
        .env("LGREP_IGNORE_CASE", "1")
        .write_stdin("Lorem\n")
        .assert()
        .success()
        .stdout("Lorem\n");
}

#[test]
fn help_lists_key_flags() {
    cargo_bin_cmd!("lgrep")
        .arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("--json").and(predicate::str::contains("--max-count")));
}
```

- Without `use assert_fs::prelude::*`, `write_str` fails with E0599 and "trait `FileWriteStr` which provides `write_str` is implemented but not in scope" (measured). The book omits the import.
- `.stdout("…")` compares exactly. `.stdout(predicate::…)` matches.
- Unit-test the logic without a process. Give the function an `impl std::io::Write` parameter, pass `&mut Vec::new()` in the test, and compare against a byte string: `assert_eq!(out, b"lorem ipsum\n")`.

## Snapshot testing

snapbox, with expected output written inline:

```rust
use snapbox::cmd::{Command, cargo_bin};
use snapbox::str;

#[test]
fn usage_error() {
    Command::new(cargo_bin!("lgrep"))
        .assert()
        .failure()
        .stderr_eq(str![[r#"
error: the following required arguments were not provided:
  <PATTERN>

Usage: lgrep <PATTERN> [PATH]

For more information, try '--help'.

"#]]);
}
```

On a mismatch, the failure shows a diff and "Update with SNAPSHOTS=overwrite". `SNAPSHOTS=overwrite cargo test` rewrites the literal in the source file (measured).

trycmd, with each case written as a file:

```rust
#[test]
fn cli_cases() {
    trycmd::TestCases::new().case("tests/cmd/*.toml").case("tests/cmd/*.md");
}
```

````markdown
<!-- tests/cmd/usage.md -->
```console
$ lgrep zzz -
? 1

$ lgrep --max-count abc x
? 2
error: invalid value 'abc' for '--max-count <NUM>': invalid digit found in string

For more information, try '--help'.

```
````

```toml
# tests/cmd/version.toml
bin.name = "lgrep"
args = ["--version"]
stdout = "lgrep 0.1.0\n"
```

`? N` is the expected status. A bare `$ cmd` with no `?` line expects success. `TRYCMD=overwrite cargo test` rewrites the expected output (measured). The Markdown cases double as documentation, so a README example can be a test.

- Snapshot the messages that you write. For clap-generated `--help`, either assert on key flags or accept that a clap minor release will change the snapshot, then re-bless it with the overwrite variable.

## What to test

The book's minimum, plus the CLI-specific failure modes:

- the happy path, a missing file (non-zero status and a stderr message), no match, and missing arguments (status 2);
- stdin through `-` with `write_stdin`, and environment variables with `.env()` (also `.env_remove()` and `.env_clear()`);
- that diagnostics go to stderr and stdout stays clean: assert both streams;
- the exact exit codes that scripts rely on.

## cargo install

- `cargo install <crate>` builds with the release profile and installs into `$CARGO_HOME/bin` (default `~/.cargo/bin`). `--root DIR` puts it in `DIR/bin`. `cargo install --path .` installs the local checkout.
- **Without `--locked`, `cargo install` ignores `Cargo.lock` and resolves dependencies afresh** (measured with `--path .`: a lockfile that pinned `itoa` 1.0.15 was ignored, and a fresh lock was made with "Locking 139 packages to latest Rust 1.97.1 compatible versions". `--locked` built 1.0.15). Tell users to run `cargo install --locked <crate>` so that a new dependency release cannot break their build.
- The binary name is the package name, or the `[[bin]] name`. A binary named `cargo-<x>` becomes `cargo <x>`.
- `cargo install` suits users who already have Rust. Everyone else needs prebuilt binaries.

## A release profile for a small binary

Measured on aarch64-apple-darwin for a CLI with clap, anyhow, env_logger, indicatif, human-panic, and confy:

| `[profile.release]` settings | Binary size |
|---|---|
| defaults | 1,870,496 bytes |
| `strip = "symbols"` | 1,449,184 bytes |
| `strip = "symbols"`, `lto = "fat"`, `codegen-units = 1`, `panic = "abort"` | 965,984 bytes |

- With `panic = "abort"`, a panic exits with status **134** (SIGABRT) instead of 101. human-panic's message still prints (measured). Tests always build with unwind.
- Rust dependencies link statically. System libraries do not: `otool -L` on this binary listed `libSystem`, `libiconv`, and the Foundation, CoreFoundation, and IOKit frameworks (via `human-panic` → `sysinfo`). On Linux, glibc is dynamic. Build for `x86_64-unknown-linux-musl` for a fully static binary.
- Profile semantics (`strip` defaults, `lto = false` against `"off"`) belong to `using-cargo`.

## Distribution

Ship a README, license files, a man page, and shell completions with each binary.

| Tool | Does | Version (checked 2026-10-17) | Note |
|---|---|---|---|
| `cargo-dist` | Generates release CI, archives, shell and PowerShell installers, and Homebrew formulas | 0.32.0 (2026-05-22) | The installed binary is named `dist` |
| `cross` | Cross-compiles in containers | 0.2.5 on crates.io (2023-02-04) | The repository moved to cross-rs/cross and is active (2026-10). Install from git for current fixes |
| `cargo-binstall` | Installs prebuilt binaries for `cargo install` users | 1.26.0 (2026-10-17) | Finds release assets by naming convention, or by `[package.metadata.binstall]` |
| `cargo-deb` | Builds `.deb` packages | 3.8.0 (2026-09-01) | |
| `cargo-generate-rpm` | Builds `.rpm` packages | 0.21.1 (2026-10-17) | |
| `cargo-bundle` | Builds platform bundles, such as a macOS `.app` or a `.deb` | 0.12.0 (2026-09-20) | |
| `cargo-wix` | Builds Windows MSI installers | 0.3.9 (2025-03-13) | |
| `cargo-aur` | Builds an Arch PKGBUILD | 1.7.1 (2024-03-18) | Quiet since 2024 |

- The book names `trust` (CI templates for Travis CI and AppVeyor). It has had no commits since 2022. Use GitHub Actions, or have `cargo-dist` write the workflow.
- macOS: rustc's default `MACOSX_DEPLOYMENT_TARGET` is 10.12 on x86_64 and 11.0 on aarch64 (`rustc --print deployment-target --target <triple>`). The book's 10.7 is below the floor.
- The order the book recommends still holds: `cargo install` first, then binary releases, then system package managers such as a Homebrew tap.
- crates.io metadata (`description`, `license`, `categories = ["command-line-utilities"]`) and `cargo publish` belong to `using-cargo`.
