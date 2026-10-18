# Crates for Rust CLIs: current versions and verified forms

Versions were checked 2026-10-17 with `cargo info <crate>` (latest version, MSRV, features) and the crates.io API (release dates). Every snippet below compiled on rustc 1.97.1, edition 2024, against those versions, and the stated output was measured. Re-run `cargo info <crate>` before pinning, because these numbers move.

## Contents

- [Crate table](#crate-table)
- [Book forms that no longer work](#book-forms-that-no-longer-work)
- [clap derive](#clap-derive)
- [Completions and man pages](#completions-and-man-pages)
- [Logging and `--verbose`](#logging-and---verbose)
- [Color](#color)
- [Progress bars](#progress-bars)
- [Machine-readable output](#machine-readable-output)
- [Signals](#signals)
- [Config files](#config-files)
- [Friendly panics](#friendly-panics)

## Crate table

"Last release" is the upload date of the newest version on crates.io.

| Crate | Use | Version (checked 2026-10-17) | Last release | Status |
|---|---|---|---|---|
| `clap` | Argument parsing. Enable `derive`, plus `env` for `#[arg(env)]` | 4.6.7 (MSRV 1.85) | 2026-09-14 | Active |
| `clap_complete` | Shell completion scripts | 4.6.11 | 2026-09-15 | Active. Runtime completion (`CompleteEnv`) is behind `unstable-dynamic` |
| `clap_mangen` | Man page from the clap definition | 0.3.3 | 2026-08-12 | Active |
| `clap-verbosity-flag` | `-v`/`-q` flags mapped to a log level | 3.0.4 | 2025-08-19 | Active. Features `log` (default) or `tracing` |
| `anyhow` | Application errors with context | 1.0.104 | 2026-07-18 | Active |
| `thiserror` | Error enums in a library crate | 2.0.21 | 2026-09-23 | Active. Design questions go to `writing-rust` |
| `log` + `env_logger` | Logging facade and an adapter configured by `RUST_LOG` | 0.4.34 and 0.11.11 | 2026-08 and 2026-06 | Active |
| `tracing` + `tracing-subscriber` | Structured logging, spans | 0.1.44 and 0.3.23 | 2025-12 and 2026-03 | Active. `fmt` writes to **stdout** by default |
| `indicatif` | Progress bars and spinners | 0.18.6 | 2026-07-01 | Active |
| `anstream` + `anstyle` | Color that strips itself off a terminal | 1.0.0 and 1.0.14 | 2026-02 and 2026-03 | Active. clap's own stack |
| `owo-colors` | Color formatting | 4.4.0 | 2026-08-27 | Active. Terminal checks need feature `supports-colors` |
| `console` | Terminal styling and size, used by indicatif | 0.16.6 | 2026-09-10 | Active |
| `ansi_term` | (named by the book) | 0.12.1 | 2019-09-02 | **Unmaintained**, RUSTSEC-2021-0139. Use `anstyle`/`anstream` or `owo-colors` |
| `atty` | (old answer for TTY checks) | 0.2.14 | 2020-01-05 | **Unmaintained**, RUSTSEC-2021-0145 and RUSTSEC-2024-0375. Use `std::io::IsTerminal` |
| `is-terminal` | TTY check | 0.4.17 | 2025-10-23 | Needed only below Rust 1.70. Use `std::io::IsTerminal` |
| `ctrlc` | Ctrl-C on Unix and Windows | 3.5.2 | 2026-02-10 | Active. Feature `termination` adds SIGTERM and SIGHUP |
| `signal-hook` | Any Unix signal | 0.4.5 | 2026-10-04 | Active. Default features `channel`, `iterator` |
| `signal-hook-tokio` | signal-hook as a tokio stream | 0.4.0 | 2026-01-01 | Active. Replaces the book's `into_async()` |
| `crossbeam-channel` | `select!` over a signal channel and a ticker | 0.5.17 | 2026-09-05 | Active |
| `confy` | Zero-boilerplate config file | 2.0.0 | 2025-10-27 | Active, low traffic. API changed since the book's 0.3.1 |
| `dirs` / `directories` / `etcetera` | Platform config and cache directories | 7.0.0 / 6.0.0 / 0.11.0 | 2026-09 / 2025-01 / 2025-10 | `dirs` and `directories` moved to codeberg.org/dirs; the GitHub repository is archived |
| `serde_json` | JSON output | 1.0.154 | 2026-10-11 | Active |
| `human-panic` | Crash report instead of a panic trace | 2.0.8 (MSRV 1.88) | 2026-04-02 | Active. Pulls in `sysinfo`, `uuid`, `toml` |
| `exitcode` | sysexits constants | 1.1.2 | 2017-06-18 | Dormant; constants only. Define `const`s instead |
| `assert_cmd`, `predicates`, `assert_fs`, `snapbox`, `trycmd`, `insta`, `proptest` | Testing | see `testing-and-packaging.md` | | |

## Book forms that no longer work

| The book shows | Current form | Evidence |
|---|---|---|
| `#[arg(short = "n", default_value = "5")]` | `#[arg(short = 'n', default_value_t = 5)]` | E0277 ``&str: IntoResettable<char>`` (measured) |
| clap error text `USAGE:` / `For more information try --help` | `Usage: …` / `For more information, try '--help'.` | measured on 4.6.7 |
| `let cfg: MyConfig = confy::load("my_app")?;` with `io::Error` | `confy::load("my_app", None)?`, returning `Result<T, confy::ConfyError>` and needing `T: Default` | confy 2.0.0 source |
| signal-hook feature `tokio-support` and `.into_async()` | `signal-hook-tokio` 0.4, or `tokio::signal` | signal-hook 0.4.5 has neither |
| `ansi_term` for escape codes | `anstyle` + `anstream`, or `owo-colors` | RUSTSEC-2021-0139 |
| `assert_cmd = "2.0.14"` with `cargo_bin_cmd!` | `assert_cmd = "2.2"`. The macro arrived in 2.1.0 | see `testing-and-packaging.md` |
| human-panic prints "Well, this is embarrassing." | Prints "<name> had a problem and crashed. …" | measured on 2.0.8 |
| panic text `panicked at 'msg', src/main.rs:2:5` | blank line, `thread 'main' (ID) panicked at src/main.rs:2:5:`, message on the next line | measured on 1.97.1 |
| `MACOSX_DEPLOYMENT_TARGET=10.7` | rustc's floor is 10.12 on x86_64 and 11.0 on aarch64 | `rustc --print deployment-target` |
| Travis CI, AppVeyor, `trust`; `cross` at rust-embedded/cross | GitHub Actions, `cargo-dist`; `cross` lives at cross-rs/cross | `trust` has had no commits since 2022 |

## clap derive

Doc comments become help text. `#[command(version, about)]` reads `CARGO_PKG_VERSION` and the struct's doc comment.

```rust
use std::path::PathBuf;

use clap::{ArgAction, Args, Parser, Subcommand};

/// A tool with subcommands.
#[derive(Debug, Parser)]
#[command(version, about, arg_required_else_help = true)]
struct Cli {
    /// More output (-v, -vv, -vvv)
    #[arg(short, long, action = ArgAction::Count, global = true)]
    verbose: u8,

    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Add files
    Add(AddArgs),
    /// Remove files
    #[command(alias = "rm")]
    Remove {
        #[arg(required = true)]
        paths: Vec<PathBuf>,
        #[arg(long, value_parser = clap::value_parser!(u16).range(1..=10))]
        retries: Option<u16>,
    },
}

#[derive(Debug, Args)]
struct AddArgs {
    paths: Vec<PathBuf>,
    #[arg(long, conflicts_with = "all")]
    only: Option<String>,
    #[arg(long)]
    all: bool,
}
```

Measured: `--retries 11` gives `error: invalid value '11' for '--retries <RETRIES>': 11 is not in 1..=10`, and `--only x --all` gives `error: the argument '--only <ONLY>' cannot be used with '--all'`. Both exit 2. A `bool` field is a `SetTrue` flag, and repeating it is an error (`the argument '--json' cannot be used multiple times`). An `Option<T>` field is optional, a `Vec<T>` field takes many values, and a field with a default uses `default_value_t`.

A flag that an environment variable can also set:

```rust
/// Match case-insensitively
#[arg(short, long, env = "LGREP_IGNORE_CASE",
      value_parser = clap::builder::FalseyValueParser::new())]
ignore_case: bool,
```

Without the `value_parser` line, the variable accepts only `true` and `false` (measured). `BoolishValueParser` also accepts `yes`/`no`/`on`/`off`/`1`/`0`, but rejects unknown values and an empty value. A flag on the command line beats the variable.

Parsing without exiting:

```rust
match Cli::try_parse() {
    Ok(cli) => run(cli),
    Err(e) => {
        // e.kind(): MissingRequiredArgument, DisplayHelp, … ; e.exit_code(): 2 or 0
        e.exit(); // prints to stderr (or stdout for help) and exits
    }
}
```

## Completions and man pages

Generate completions at runtime from a flag or a hidden subcommand:

```rust
#[arg(long, value_name = "SHELL", exclusive = true)]
completions: Option<clap_complete::Shell>,
// in run():
if let Some(shell) = cli.completions {
    clap_complete::generate(shell, &mut Cli::command(), "lgrep", &mut std::io::stdout());
}
```

`Cli::command()` needs `use clap::CommandFactory;`.

A man page from `build.rs`, which the book shows. Put the `Cli` definition in its own file and include it with `#[path]`:

```rust
// build.rs
use std::path::PathBuf;

use clap::CommandFactory;

#[path = "src/cli.rs"]
mod cli;

fn main() -> std::io::Result<()> {
    println!("cargo::rerun-if-changed=src/cli.rs");
    let out_dir = PathBuf::from(std::env::var_os("OUT_DIR").ok_or(std::io::ErrorKind::NotFound)?);
    let mut buffer = Vec::new();
    clap_mangen::Man::new(cli::Cli::command()).render(&mut buffer)?;
    std::fs::write(out_dir.join("lgrep.1"), buffer)?;
    Ok(())
}
```

- **Every crate and feature that `cli.rs` uses must also be a `[build-dependencies]` entry**, including `clap` with `derive` and `env`, `clap-verbosity-flag`, and `clap_complete`. Otherwise the build script fails with E0433 ``cannot find module or crate `clap_verbosity_flag` `` or E0599 ``no method named `env` `` (measured).
- The page lands in `target/<profile>/build/<pkg>-<hash>/out/lgrep.1`, not in the project directory as the book's prose says. To ship it, generate it from an `xtask` or a hidden subcommand instead (`clap_mangen::Man::new(cmd).render(&mut io::stdout())`).
- `clap_mangen::generate_to(cmd, dir)` writes one page per subcommand.

## Logging and `--verbose`

`clap-verbosity-flag` with env_logger. `Verbosity<WarnLevel>` makes warnings visible by default, `-v` adds info, and `-q` removes levels:

```rust
#[command(flatten)]
verbosity: clap_verbosity_flag::Verbosity<clap_verbosity_flag::WarnLevel>,
// in main():
env_logger::Builder::new()
    .filter_level(cli.verbosity.log_level_filter())
    .init();
```

- `Builder::new()` ignores `RUST_LOG`. `env_logger::init()` reads it, and shows **only errors** when it is unset (measured). To read the variable with a default, use `Builder::from_env(env_logger::Env::default().default_filter_or("info"))`.
- The output goes to stderr as `[2026-10-18T01:44:45Z INFO  lgrep] message`. The target is the crate name with `-` changed to `_`.

tracing instead of log:

```rust
use tracing_subscriber::EnvFilter; // feature "env-filter"

tracing_subscriber::fmt()
    .with_writer(std::io::stderr) // the default writer is stdout
    .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("warn")))
    .init();
```

Measured: `tracing_subscriber::fmt::init()` with `RUST_LOG=warn` wrote its line to stdout, 89 bytes, and nothing to stderr.

## Color

```rust
use anstyle::{AnsiColor, Style};

const ERROR: Style = AnsiColor::Red.on_default().bold();

anstream::eprintln!("{ERROR}error:{ERROR:#} something failed");
```

- The `anstream` print macros and `anstream::AutoStream` drop the escape codes when the stream is not a terminal, when `NO_COLOR` is set, or when `TERM=dumb`. `CLICOLOR_FORCE=1` turns them on (measured: plain text when piped, `\x1b[1m\x1b[31m` with the force variable).
- For `--color`, use `anstream::AutoStream::new(io::stdout().lock(), anstream::ColorChoice::Always)`, or `Never`, or `Auto`. Wrap the result in `BufWriter` for speed.
- `{style}` opens a style and `{style:#}` resets it.

## Progress bars

```rust
use indicatif::{ProgressBar, ProgressStyle};
use std::time::Duration;

let pb = ProgressBar::new(len);
pb.set_style(ProgressStyle::with_template("{spinner} [{bar:30}] {pos}/{len} {msg}")?);
pb.enable_steady_tick(Duration::from_millis(100));
// per item:
pb.suspend(|| eprintln!("processed {name}")); // survives redirection; pb.println does not
pb.inc(1);
// at the end:
pb.finish_with_message("done"); // takes impl Into<Cow<'static, str>>
```

- `ProgressBar::new` draws to stderr, at most 20 times a second. When stderr is not a terminal, it draws nothing and `println` is a no-op (measured).
- `ProgressStyle::with_template` returns a `Result`.
- `ProgressBar::hidden()` turns the bar off for `--quiet`.

## Machine-readable output

Use line-delimited JSON behind a `--json` flag: one object per line, each with a `type` field. This is ripgrep's model (`begin`, `match`, `end`, `summary`).

```rust
use serde::Serialize;
use std::io::{self, BufWriter, Write};

#[derive(Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum Message<'a> {
    Match { path: &'a str, line_number: usize, text: &'a str },
    Summary { matches: usize },
}

let mut out = BufWriter::new(io::stdout().lock());
serde_json::to_writer(&mut out, &Message::Summary { matches: 1 })?;
out.write_all(b"\n")?;
```

The output is `{"type":"summary","matches":1}` (measured). With derive, fields keep their declared order. With `serde_json::json!`, keys come out sorted, as the book shows.

## Signals

ctrlc, with a second Ctrl-C that quits at once:

```rust
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

let stop = Arc::new(AtomicBool::new(false));
let flag = Arc::clone(&stop);
ctrlc::set_handler(move || {
    if flag.swap(true, Ordering::SeqCst) {
        std::process::exit(130);
    }
})?;
// in loops: if stop.load(Ordering::Relaxed) { break }
```

- `set_handler` runs the closure on a dedicated thread, so it may lock and allocate. It replaces any existing handler. `try_set_handler` fails instead of replacing.
- Measured: with one SIGINT, the loop stopped at the next line and the buffered output was flushed. With two, the status was 130.

signal-hook 0.4, which needs no extra thread for the flag pattern:

```rust
use signal_hook::consts::{SIGINT, SIGTERM, TERM_SIGNALS};
use signal_hook::flag;
use signal_hook::iterator::Signals;

let term = Arc::new(AtomicBool::new(false));
for sig in TERM_SIGNALS {
    // Registered first: exits with 130 if `term` is already set (the second signal).
    flag::register_conditional_shutdown(*sig, 130, Arc::clone(&term))?;
    // Registered second: sets `term` on the first signal.
    flag::register(*sig, Arc::clone(&term))?;
}

// Or receive signals on a thread:
let mut signals = Signals::new([SIGINT, SIGTERM])?;
std::thread::spawn(move || {
    for sig in signals.forever() {
        eprintln!("received signal {sig}");
    }
});
```

The registration order matters. If the two calls are swapped, the first signal both arms and fires the shutdown (signal-hook's docs). Measured: two SIGINTs gave status 130.

## Config files

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(default)] // without this, a file missing any field fails to load
struct MyConfig {
    name: String,
    comfy: bool,
}

let cfg: MyConfig = confy::load("my-app", None)?; // None = "default-config"
let path = confy::get_configuration_file_path("my-app", None)?;
```

- **`load` writes a file with the defaults when none exists** (measured). A read-only command therefore creates files.
- With the default strategy, the macOS path is `~/.config/my-app/default-config.toml`, not `~/Library/Application Support` (measured). `confy::change_config_strategy(confy::ConfigStrategy::Native)` switches to the platform convention.
- Measured: a file that lacks a field fails with ``BadTomlData(… "missing field `comfy`" …)`` unless the struct has `#[serde(default)]`.
- TOML is the default format. Exactly one format feature must be on (`toml_conf`, `basic_toml_conf`, `yaml_conf`, `ron_conf`).
- Precedence is the program's own choice, and the usual order is flag over environment variable over config file over default. clap's `env` covers the first two.

## Friendly panics

```rust
fn main() {
    human_panic::setup_panic!(); // first line of main
    // ...
}
```

`setup_panic!()` reads the package name, version, authors, homepage, and repository from Cargo's environment at compile time. To override them, pass `human_panic::metadata!().homepage("…")`. A debug build, or `RUST_BACKTRACE` set, keeps the normal panic output.
