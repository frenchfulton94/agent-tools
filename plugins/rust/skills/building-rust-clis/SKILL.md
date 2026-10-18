---
name: building-rust-clis
description: Builds, tests, and ships Rust command-line programs — clap 4 derive parsing, exit codes, error reporting from `main` with anyhow, stdout versus stderr, `BufWriter` and locking, `BrokenPipe` when piped into `head`, terminal and color detection, stdin, progress bars and logging, config files, Ctrl-C and signals, assert_cmd and snapshot tests, man pages and completions, and `cargo install` and releases, with current crate versions in place of the stale ones in the Command Line Applications in Rust book. Use when the user is writing, reviewing, testing, or packaging a Rust CLI or cargo subcommand, or asks which crate to use for one. Also use for symptoms that never say "CLI" - a "failed printing to stdout" panic, a tool that exits 101, or 0 after failing, a `NotFound` error from `main` that never names the file, output lost after `process::exit`, a tool slow only when piped, a progress bar that prints nothing when redirected, logs mixed into stdout, or `IntoResettable` and `cargo_bin_cmd!` compile errors.
license: MIT
---

# Building Rust CLIs

Sourced from the Rust 1.99 stable documentation, including the *Command Line Applications in Rust* book. Every behaviour marked *measured* was checked on rustc/cargo **1.97.1** (aarch64-apple-darwin) in a real CLI built against current crates. Crate versions were checked 2026-10-17 with `cargo info` and crates.io. Nothing below depends on 1.98 or 1.99.

The CLI book is partly stale. Its crate versions, API forms, and sample output are leads, not facts. Use the forms here, which compile. Re-check a version with `cargo info <crate>` before you pin it.

Hand-offs: designing error types (thiserror against anyhow, `From`, `?`) belongs to `writing-rust`. `Cargo.toml`, profiles, and cross-compilation flags belong to `using-cargo`. The test harness and `cargo test` filters belong to `testing-rust`. An unreadable compiler error belongs to `fixing-rust-compile-errors`.

## The `main` that gets the details right

```rust
use std::io::{self, BufWriter, Write};
use std::path::PathBuf;
use std::process::ExitCode;

use anyhow::{Context, Result};
use clap::Parser;

/// Print a file's lines.
#[derive(Parser)]
#[command(version, about)]
struct Cli {
    /// File to read
    path: PathBuf,
}

fn main() -> ExitCode {
    let cli = Cli::parse(); // usage error: message on stderr, exit 2
    match run(&cli) {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) if is_broken_pipe(&err) => ExitCode::SUCCESS, // `| head` closed the pipe
        Err(err) => {
            eprintln!("error: {err:#}");
            ExitCode::FAILURE
        }
    }
}

fn run(cli: &Cli) -> Result<()> {
    let text = std::fs::read_to_string(&cli.path)
        .with_context(|| format!("could not read file `{}`", cli.path.display()))?;
    let mut out = BufWriter::new(io::stdout().lock());
    for line in text.lines() {
        writeln!(out, "{line}")?;
    }
    out.flush()?; // dropping would flush too, but would discard a write error
    Ok(())
}

fn is_broken_pipe(err: &anyhow::Error) -> bool {
    err.chain().any(|cause| {
        cause
            .downcast_ref::<io::Error>()
            .is_some_and(|e| e.kind() == io::ErrorKind::BrokenPipe)
    })
}
```

Measured: a missing file prints `error: could not read file `nope.txt`: No such file or directory (os error 2)` and exits 1. `tool big.txt | head -2` exits 0 with nothing on stderr. No arguments exits 2. Keep logic in `run` (or in `lib.rs`), so that tests can call it with any `impl Write`.

## Output

- **stdout is line-buffered even when it is a pipe** (measured: a line reached the pipe reader while the program slept, and `print!` without `\n` was held until the newline). Each `println!` therefore costs one `write` call. **`BufWriter` is the fix. Locking alone is not.** For 2,000,000 lines into a pipe (release build), `println!` took 0.68 s, `stdout().lock()` with `writeln!` took 0.71 s, and `BufWriter::new(stdout().lock())` took 0.12 s (measured). Lock once as well, so that other threads cannot interleave.
- Call `flush()` after a `print!` prompt, before reading the answer, and before any `process::exit`.
- **`println!` panics when the reader goes away.** `tool | head -1` prints `thread 'main' (…) panicked at …/library/std/src/io/stdio.rs:…: failed printing to stdout: Broken pipe (os error 32)` and exits 101 (measured). Rust's runtime ignores `SIGPIPE`, so a write returns `EPIPE` instead of killing the process. `fn main() -> io::Result<()>` with `writeln!(…)?` is no better: it prints `Error: Os { code: 32, kind: BrokenPipe, message: "Broken pipe" }` and exits 1. Write with `writeln!`, propagate the error, and map `ErrorKind::BrokenPipe` to success in `main`, as above. Under anyhow, search `err.chain()`, because context wraps the `io::Error`.
  - `-Zon-broken-pipe=kill` is nightly-only. Stable rejects it with "the option `Z` is only accepted on the nightly compiler".
  - On Unix only, `unsafe { libc::signal(libc::SIGPIPE, libc::SIG_DFL) }` as the first line of `main` restores the default action. The process then dies silently with status 141 (measured), which skips destructors and any unflushed buffer.
- **stdout carries data only.** Errors, warnings, progress, logs, and prompts go to stderr. `eprintln!`, `dbg!`, panics, `env_logger`, and `indicatif` already write there. **`tracing_subscriber::fmt()` writes to stdout by default** (measured). Add `.with_writer(std::io::stderr)`.
- **`indicatif` hides its bar when stderr is not a terminal, and `ProgressBar::println` then prints nothing** (measured: 0 bytes). For a line that must survive redirection, use `pb.suspend(|| eprintln!(…))`.
- **Terminal detection is in std:** `use std::io::IsTerminal; io::stdout().is_terminal()` (stable since 1.70). `atty` is unmaintained (RUSTSEC-2021-0145, RUSTSEC-2024-0375). `ansi_term` is unmaintained (RUSTSEC-2021-0139).
- **Color** only on a terminal, and honour `NO_COLOR` and `CLICOLOR_FORCE`. `anstream` (the crate clap uses) does all three and strips escape codes otherwise (measured). Offer `--color auto|always|never`.
- **Stdin:** accept `-` as the path for standard input. If no input was given and `io::stdin().is_terminal()`, print help and exit 2 instead of waiting on the keyboard.

## Exit codes

| What happens | Status (measured) |
|---|---|
| `main` returns `()`, `Ok(..)`, or `ExitCode::SUCCESS` | 0 |
| `main` returns `Err(e)` | 1, after `Error: {e:?}` on stderr |
| Uncaught panic | 101 |
| clap usage error, or no arguments under `arg_required_else_help` | 2 |
| `--help`, `--version` | 0, printed on stdout |
| Killed by Ctrl-C with no handler installed | 130, as the shell reports it |
| `process::exit(256)` | **0**, because Unix keeps the low 8 bits. `exit(-1)` gives 255 |
| `SIGPIPE` restored to default, then the reader closes | 141 |

- Return `std::process::ExitCode` from `main` (stable since 1.61) instead of calling `process::exit`. **`process::exit` runs no destructors.** A `BufWriter` that holds output is never flushed: the output is lost and the status is still 0 (measured). `ExitCode::from(u8)` cannot wrap. `main` may also return `Result<ExitCode, E>`, such as `anyhow::Result<ExitCode>` (measured).
- The conventions are 0 for success, 1 for failure, and 2 for a usage error (clap's own). grep-style tools use 1 for "no match" and 2 for an error. The book suggests the `exitcode` crate for sysexits values (64–78). Its last release was in 2017, and it holds only constants, so `const EX_DATAERR: u8 = 65;` does the same job without a dependency.

## Error reporting from `main`

- `fn main() -> Result<(), Box<dyn Error>>` prints the **Debug** form, `Error: Os { code: 2, kind: NotFound, message: "No such file or directory" }`, and the file name is lost (measured).
- `fn main() -> anyhow::Result<()>` prints `Error: could not read file `x``, a blank line, `Caused by:`, and the indented cause (measured). With two or more causes, they are numbered `0:`, `1:`.
- For output that users see, print the error yourself. `{err:#}` prints the whole chain on one line, such as `loading config: could not read file `x`: No such file or directory (os error 2)`. `{err}` prints **only the outermost context** and loses the cause. `{err:?}` prints the `Caused by:` block (all measured).
- Add context that names the path or input at every I/O boundary: `.with_context(|| format!("could not read file `{}`", path.display()))`.
- A panic is for a bug, not for bad input. The current panic message starts with an empty line, then `thread 'main' (12345) panicked at src/main.rs:1:51:`, with the message on the next line (measured). The book's `panicked at 'msg', src/main.rs:2:5` form predates 1.73. `human-panic` 2 replaces the message with "<name> had a problem and crashed…" and writes a report `.toml` to the temp directory. It does so only in release builds with `RUST_BACKTRACE` unset, and the status stays 101 (measured).

## Arguments (clap 4.6)

- `short` takes a `char`: `#[arg(short = 'n')]`. The book's man-page chapter has `short = "n"`, which fails with E0277 ``the trait bound `&str: IntoResettable<char>` is not satisfied`` (measured).
- `#[arg(env = "VAR")]` needs clap's `env` feature. Without it the error is E0599 ``no method named `env` found for struct `Arg` `` (measured).
- **A `bool` flag with `env` accepts only `true` or `false` from the variable.** `VAR=1`, `VAR=yes`, and `VAR=` are usage errors that exit 2 (measured). Add `value_parser = clap::builder::FalseyValueParser::new()`: empty, `0`, `false`, `no`, and `off` then mean false, and anything else means true. The Rust Book's `env::var("X").is_ok()` treats even `X=0` as on.
- `Cli::parse()` prints and exits: help and version go to stdout with status 0, and errors go to stderr with status 2. Use `Cli::try_parse()` where the process must not exit, such as a REPL, a library, or a unit test. Then inspect `err.kind()` and `err.exit_code()`, or call `err.exit()`.
- **Non-UTF-8 arguments:** `std::env::args()` panics with ``called `Result::unwrap()` on an `Err` value: "\xFF"`` (status 101), and `args_os()` does not. In clap, a `String` field rejects such an argument with `error: invalid UTF-8 was detected in one or more arguments` (status 2), and a `PathBuf` or `OsString` field accepts it (measured). Use `PathBuf` for paths.
- The clap 4 error text is `error: the following required arguments were not provided:`, then `Usage: …`, then `For more information, try '--help'.`. A typo gets `tip: a similar argument exists: '--json'` (measured). The book's `USAGE:` and `For more information try --help` text is clap 2 and 3.
- Do not assert the exact layout of `--help`. Assert that the key flags appear.
- **A cargo subcommand** `cargo-foo` receives `foo` as its first argument. Model it as `#[derive(Parser)] #[command(name = "cargo", bin_name = "cargo")] enum Cli { Foo(FooArgs) }`. Measured: `cargo foo --flag` parses, and a direct `cargo-foo --flag` is rejected.

## Signals

- Without a handler, Ctrl-C ends the process at once with status 130, and the OS reclaims everything. Install a handler only when there is something to undo, such as temp files, terminal modes, or a half-written output file.
- `ctrlc` 3.5 handles Ctrl-C on Unix and Windows. Its `termination` feature adds SIGTERM and SIGHUP. In the handler, set an `AtomicBool` and poll it between units of work. A blocking `read` does not wake up for the signal.
- **A second Ctrl-C must quit at once.** In the handler, `if flag.swap(true, SeqCst) { std::process::exit(130) }` (measured: status 130). After a graceful stop, exit 130 as well, or a script reads the interrupted run as success.
- For other signals, and for the double-signal pattern without ctrlc, use `signal-hook` 0.4 (see the crates reference). The book's `tokio-support` feature and `.into_async()` were signal-hook 0.1 APIs and no longer exist. Use `signal-hook-tokio` or `tokio::signal` instead.
- Windows has no signals. A GUI binary that sets `#![windows_subsystem = "windows"]` has no console, so it has no stdout either.

## Where to look

Read only the file that the question touches.

- `references/crates-and-current-apis.md`: read it before you add a crate to a CLI, pin a version, or copy an API form from the CLI book. It has every crate the book names, with the version checked 2026-10-17, its maintenance state, and a replacement for each stale one. It also has compiled snippets for clap derive (subcommands, counted `-v`, ranges, conflicts), completions and man pages, `--verbose` with env_logger or tracing, color, progress, JSON-lines output, signals, config files, and human-panic.
- `references/testing-and-packaging.md`: read it when you write tests that run the binary, or when you prepare a release. It covers assert_cmd 2.2 and when `cargo_bin_cmd!` arrived, predicates, assert_fs, snapshot testing with snapbox, trycmd, and insta, and `CARGO_BIN_EXE_<name>`. It also covers how `cargo install` treats `Cargo.lock`, a release profile for small binaries, and distribution tools.
