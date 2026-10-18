# rust

Rust development on the 2024 edition, for Claude Code. It packages the know-how as nine skills, build triage and API review as two agents, and two hooks: a confirmation before registry changes, and a gate that keeps a session from ending on a broken build.

The material comes from the official documentation, read in full from the live stable docs (Rust 1.99.1) on 2026-10-17:

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [The Rust Reference](https://doc.rust-lang.org/reference/index.html)
- [The standard library](https://doc.rust-lang.org/std/index.html): every module, primitive, macro, and keyword page the index links
- [The Cargo Book](https://doc.rust-lang.org/cargo/index.html)
- [The rustc book](https://doc.rust-lang.org/rustc/index.html)
- [The rustdoc book](https://doc.rust-lang.org/rustdoc/index.html)
- [The error codes index](https://doc.rust-lang.org/error_codes/error-index.html)
- [Command Line Applications in Rust](https://rust-cli.github.io/book/index.html)

`designing-rust-apis` comes from the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), and `linting-and-formatting-rust` comes from the [Clippy book](https://doc.rust-lang.org/clippy/), the [stable Clippy lint list](https://rust-lang.github.io/rust-clippy/stable/index.html) (all 830 lints), and the [Rust Style Guide](https://doc.rust-lang.org/style-guide/). All were read in full on 2026-10-17. The API Guidelines predate edition 2024, and the lint list describes clippy's latest stable, which is newer than the 1.97 installed here. Every guideline that current Rust changed, and every recommended lint and config key, was checked against clippy and rustfmt 1.97.1.

`using-atomics-and-locks` comes from Mara Bos's [*Rust Atomics and Locks*](https://mara.nl/atomics/), read in full on 2026-10-17, including every table and figure description. The book targets roughly Rust 1.66. Its claims about std's current implementation were checked against the std source at the 1.97.1 tag, and its claims about codegen and orderings were measured on ARM64.

Behaviour the skills assert was measured on rustc and cargo 1.97.1. Material that is stable only in 1.98 or 1.99 is marked as such, because it could not be measured on 1.97.1. Where the docs and a measurement disagreed, the skills follow the measurement. The CLI book's crate code is partly out of date, so `building-rust-clis` was checked against the crates' current releases rather than against the book.

## Components

| Component | Shape | Why this shape |
|---|---|---|
| `skills/writing-rust` | Skill | The language, the edition-2024 changes, unsafe and UB rules, and std APIs stabilised through 1.99. A capable model already writes Rust, but often in pre-2024 forms. The skill corrects those forms and does not teach the language |
| `skills/using-cargo` | Skill | Manifests, features, workspaces, profiles, build scripts, config, the resolver and MSRV, publishing and SemVer, targets and cross-compilation |
| `skills/designing-rust-apis` | Skill | Naming, conversions, trait choice, error types, and future-proofing for public APIs, with the full API Guidelines checklist for reviews. Kept apart from `writing-rust` because it applies to a crate's public surface, not to code in general |
| `skills/linting-and-formatting-rust` | Skill | Which Clippy groups and lints to enable, `clippy.toml`, Clippy in CI, and rustfmt configuration. Kept apart from `fixing-rust-compile-errors`, which owns what a lint means, and from `using-cargo`, which owns the `[lints]` table syntax |
| `skills/fixing-rust-compile-errors` | Skill | Diagnostics, the current and retired error codes, the order errors surface in, borrow-checker patterns, and lints |
| `skills/using-atomics-and-locks` | Skill | Memory ordering, fences, and building or reviewing spin locks, channels, Arc, mutexes, condvars, and rwlocks on futex-style wait and wake, plus what x86-64 and ARM64 actually do. Its trigger vocabulary (`Ordering::Acquire`, `compare_exchange`, false sharing) is distinct from everyday concurrency, which stays in `writing-rust` |
| `skills/testing-rust` | Skill | The test harness, its stable and unstable flags, test organisation, and running doctests |
| `skills/documenting-rust` | Skill | Doc comments, intra-doc links, doctest syntax and edition-2024 merging, doc attributes, and rustdoc lints |
| `skills/building-rust-clis` | Skill | Arguments, errors and exit codes, output and piping, signals, configuration, and testing and shipping a binary, on current crate versions |
| `agents/rust-build-triage.md` | Subagent | A failing build can print hundreds of cascading diagnostics, and only the root causes are worth keeping in the conversation. The agent works from cargo's JSON message stream and reports in fix order |
| `agents/rust-api-reviewer.md` | Subagent | A full API review applies a 54-item checklist and a pedantic Clippy run to every public item. That output is long, and the caller only needs the findings, ordered by how costly each is to fix after release. The agent reads the checklist from `designing-rust-apis` rather than keeping its own copy |
| `hooks/hooks.json` + `scripts/cargo-registry-guard.pl` | Hook | `cargo publish` asks for no confirmation, and a published version can never be overwritten or deleted. An instruction can be reasoned around, but a hook cannot |
| `hooks/hooks.json` + `scripts/rust-check-gate.pl` | Hook | "It compiles" is the one best practice that is never a judgement call, and a session that ends on a broken build hands the breakage to the user. An instruction to run `cargo check` before finishing is skipped under pressure; a Stop hook is not |

No formatting hook: rustfmt run on every edit rewrites files under Claude, so its next edit fails on stale text, and bare `rustfmt` parses as edition 2015 (measured). `cargo fmt` in CI or a pre-commit hook does the same job without that friction. No LSP server: the official marketplace's rust-analyzer plugin already provides one, and Claude Code uses the first server registered for an extension. A second copy would only drift. No MCP server: cargo and rustc already give Bash everything one would add.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install rust@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/rust
claude plugin validate plugins/rust --strict
```

## The guard

The guard runs on every `Bash` call. A command that does not contain `cargo` is allowed after one regex check. A command that does contain it is split into shell statements and words. The split handles quotes, `$(…)` and backticks, `bash -c`, `eval`, `cd`, leading `VAR=value` assignments, and the `sudo`/`env`/`nice`/`time`/`xargs` wrappers. The guard then finds cargo's subcommand the way cargo does: after `+toolchain` and the global options, and through aliases.

| Command | Decision | Why |
|---|---|---|
| `cargo publish` without `--dry-run` / `-n`, including `--workspace` | ask | Permanent: a version can never be overwritten, and its code cannot be deleted |
| `cargo yank`, with or without `--undo` | ask | Changes what every downstream project without a lockfile entry resolves to |
| `cargo owner --add` / `--remove` | ask | Changes who can publish the crate |
| Everything else, including `cargo publish --dry-run`, `cargo package`, `cargo owner --list`, and `echo "cargo publish"` | allow | A guard that fires on safe commands gets switched off |

The guard never denies. Each of these commands is right when the user means it, so the guard hands the decision to a person.

Aliases are read from the `[alias]` table of every `.cargo/config.toml` (and legacy `.cargo/config`) from the working directory up to the root, from `$CARGO_HOME/config.toml`, and from `CARGO_ALIAS_<NAME>`. As cargo does, the guard ignores an alias that shadows a built-in command. Measured on cargo 1.97.1, cargo does not honour an alias passed as `--config alias.NAME=…`, so the guard does not model that form either.

The guard is written in Perl, using only core modules. Perl is present on macOS and on practically every Linux system that has git, and it parses JSON without jq.

**Known limits.** The guard does not see a publish run from a script file, a Makefile or `just` recipe, or a third-party release tool (`cargo-release`, `cargo-workspaces`, `release-plz`). It does not evaluate variables or command substitutions used as the subcommand (`cargo $CMD`). It fails open on a malformed payload or an internal error.

## The check gate

Two hook entries, one script. On `PostToolUse` for `Edit`, `Write`, and `MultiEdit`, it records each edited `.rs` file and `Cargo.toml` for the session. Edits under `target/` and to dependency sources in `~/.cargo` are ignored. On `Stop`, if the session edited Rust, it finds each file's Cargo workspace (`cargo locate-project --workspace`) and runs `cargo check --workspace --all-targets` there. `--all-targets` matters: a rename that breaks only a test fails here and nowhere else.

| Outcome | Decision |
|---|---|
| Errors located in a source file | block, quoting up to 8 error lines and the number of blocks left |
| Warnings only, or a clean build | allow; the session's record is cleared |
| cargo cannot answer: not on PATH, an offline fetch, a held lock, a 240 s timeout | allow, with a notice to the user |
| Still failing after 2 blocks in a row | allow, with a notice. A crate that was already broken, or code the user asked to leave broken, cannot hold the session |

Warnings never block: they are the project's policy, set through its `[lints]` and `build.warnings`. Errors that do not name a file and line, such as resolver or network failures, never block either, so an environment problem cannot trap a session. `RUST_CHECK_GATE=0` in the environment turns the gate off. State lives in `${CLAUDE_PLUGIN_DATA}/rust-check-gate/`.

Measured in headless sessions on this plugin. Asked to rename a function without touching the test module, Claude was blocked by the E0425 in the test target, reported it, and the session ended at the cap. Asked to make a function return the wrong type, it was blocked, said so, and stopped.

**Known limits.** It checks the default features only. It does not see Rust edited through Bash (`sed`, a generator) or through a tool other than `Edit`, `Write`, and `MultiEdit`. A workspace slower than 240 s to check passes with a notice.

## Testing

```bash
bun test tests/rust-guard.test.ts tests/rust-check-gate.test.ts    # from the marketplace root
```

The suite runs the real script against fixed command lists: 44 commands that must ask and 28 that must be allowed. Further cases run against a fixture project with aliases in `.cargo/config.toml`, a fixture `CARGO_HOME`, and environment aliases. Every case also asserts a clean exit and an empty stderr with `RUST_GUARD_DEBUG=1` set, so an internal error cannot pass as "allow".

`rust-check-gate.test.ts` runs the real gate against real fixture crates and the installed cargo: what `track` records and ignores, a located error blocking with its file and line, warnings and fixed builds passing, the two-block cap and its countdown, a workspace checked from an edit in one member, and failing open without cargo or outside any crate. It skips when cargo is unavailable.

The guard also takes a payload directly:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cargo publish"},"cwd":"/tmp"}' \
  | perl plugins/rust/scripts/cargo-registry-guard.pl
```

Empty output means allow. Otherwise a JSON body carries the decision. The script always exits 0.

## Skill evals

Each skill's `evals/triggers.md` holds a 20-query trigger battery: 10 queries that should trigger the skill and 10 near-misses, mostly from the other eight Rust skills. The batteries are for A/B runs against a baseline and are never loaded automatically.
