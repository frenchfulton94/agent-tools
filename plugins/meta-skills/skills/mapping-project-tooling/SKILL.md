---
name: mapping-project-tooling
description: Creates and maintains TOOLS.md, a repo-root assistant-neutral map of a project's package manager, framework and layout conventions, commands, key dependencies, and available agent capabilities, derived from evidence found in the repository. Use when the user wants a TOOLS.md or tools.md stack-context file for coding agents, wants one audited or refreshed after it drifted from the code, or is swapping the package manager, replacing a dependency, or migrating framework, router, or deploy target in a repo that has one. Also use on symptoms where the file is never named — agents running the wrong package manager, writing to the wrong directory for the project's router, installing a deprecated or duplicate library when one is already installed, or re-asking about the stack every session. Also for setting up shared project context across Claude Code, Codex, and Cursor.
license: MIT
---

# Mapping Project Tooling

Produces and maintains `TOOLS.md` at a repository root: a short, assistant-neutral map of the project's package manager, layout conventions, commands, key dependencies, and available agent capabilities. Every line in it is traceable to a file in the repo, so a later agent reads facts instead of guessing defaults.

Three layers stay distinct: **this skill** (how to build the file), **`TOOLS.md`** (the artifact), and **the later agent** that reads `TOOLS.md` before touching dependencies, scripts, or config. Instructions aimed at that later agent belong in the file, not in this skill.

## Artifact name

`TOOLS.md`, uppercase, at the repository root, next to `README.md`, `AGENTS.md`, and `CLAUDE.md` where root metadata already lives.

If the repo already has one under any casing (`tools.md`, `Tools.md`), update that file in place and keep its name. Never add a second file that differs only by case: case-insensitive filesystems collide on it, and case-sensitive ones carry two maps that quietly diverge.

## Before starting

This skill derives everything from files on disk. If there is no manifest, lockfile, or source tree yet, say so and stop — a greenfield project has no evidence to map, and a `TOOLS.md` written from intentions is the stale-file failure on day one.

Route elsewhere: architecture prose, review policy, and coding style go in the memory file (`CLAUDE.md` / `AGENTS.md`). `TOOLS.md` holds tool, version, command, and capability facts.

## Stage 1: Read the evidence

One rule governs the whole file: **every claim names the file it came from, and you have opened that file.** A stack inferred from the language, from a framework's popularity, or from what the repo resembles is a guess, and guesses are the thing `TOOLS.md` exists to stop.

| Fact | Read this | Do not infer from |
|---|---|---|
| Package manager | Lockfile at root; `packageManager` field; `.tool-versions`, `mise.toml` | Language, README install line, habit |
| Runtime version | `.nvmrc`, `engines`, `.python-version`, `go.mod`, `rust-toolchain.toml` | Latest release |
| Framework | Manifest dependency **and** its config file | Directory names alone |
| Layout / routing convention | Directories that actually exist, plus framework config | The framework's most common convention |
| Commands | Manifest `scripts`, `Makefile`, `justfile`, `Taskfile.yml` | Remembered command names |
| Library per capability | Manifest dependency **and** where it is imported in source | Ecosystem popularity or your prior |
| Installed version | Version the lockfile resolved, falling back to the manifest range | Latest published version |
| Test tooling | Test dependency, its config file, the script that runs it | A `tests/` directory existing |
| Deploy target | CI workflows, `vercel.json`, `fly.toml`, `Dockerfile`, `serverless.yml` | Hosting fashion |
| Local wrappers | Modules under `src/lib`, `internal/`, `app/utils` that already wrap a dependency | Assuming none exist |

The last row is high value and usually skipped: recording that `src/lib/supabase.ts` already exports the clients is what stops a later agent installing a second package for a capability the repo already has.

Lockfile to package manager, the single most-missed fact:

| Lockfile at root | Manager | Install | Add |
|---|---|---|---|
| `pnpm-lock.yaml` | pnpm | `pnpm install` | `pnpm add <pkg>` |
| `package-lock.json` | npm | `npm install` | `npm install <pkg>` |
| `yarn.lock` | Yarn | `yarn install` | `yarn add <pkg>` |
| `bun.lock` / `bun.lockb` | Bun | `bun install` | `bun add <pkg>` |
| `uv.lock` | uv | `uv sync` | `uv add <pkg>` |
| `poetry.lock` | Poetry | `poetry install` | `poetry add <pkg>` |
| `Pipfile.lock` | Pipenv | `pipenv install` | `pipenv install <pkg>` |
| `Cargo.lock` | Cargo | `cargo build` | `cargo add <crate>` |
| `go.sum` | Go modules | `go mod download` | `go get <mod>` |
| `Gemfile.lock` | Bundler | `bundle install` | `bundle add <gem>` |
| `composer.lock` | Composer | `composer install` | `composer require <pkg>` |

Read `references/evidence-map.md` when detecting framework, routing, test, or deploy facts beyond the package manager, when the repo is a monorepo or polyglot, or when two pieces of evidence disagree.

When evidence is missing, thin, or contradictory, do not settle it by picking the popular option. Ask the user if they are available; otherwise record the fact as unknown with what you checked. An honest gap costs one question, while a confident wrong line costs a broken change plus the time to work out why.

## Stage 2: Inventory agent capabilities

Start from what you can actually invoke. The skills, tools, MCP servers, and subagents available to you are already in your context — enumerate those. Do not scan `.claude/` to discover them: a directory scan returns names without descriptions, misses everything provided outside the repo, and lists things that may not be loadable at all.

The repo answers one question only: whether each capability travels with the project.

| Available to you and… | Record it as |
|---|---|
| Declared in repo config (`.mcp.json`, `.claude/skills/<name>`, `.claude/agents/`) | An unconditional entry, citing that file |
| Provided by your harness or your own install | Omit it, or mark it as not committed to this repo |

That split matters because `TOOLS.md` is committed. A capability you happen to have is not one a teammate has, and an unconditional entry for it makes the file wrong for every other reader. When such a capability is load-bearing for work here, the fix is to commit it to the repo and then list it.

The reverse case is just as common: repo config declares capabilities your agent cannot load. Record those from the config, marked conditional, because another agent on the same repo will have them.

Give each entry this project's policy on when to reach for it rather than a copy of the description you already have — "writing or altering a migration; it enforces the reversible-migration rule this repo requires." An entry you cannot phrase in terms of a task in this repo does not belong in the file.

Rules and memory files (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md`) get a line here too, naming what each governs, so a later agent knows they exist. Linters and type checkers are commands; they belong under Commands.

## Stage 3: Write the file

Fill `assets/TOOLS.template.md`. It carries the section order, the evidence-citation format, and the maintenance section that later agents read. Keep its sections; drop rows inside a section when the repo has no evidence for them rather than padding with plausible defaults.

Match this granularity — package, resolved version, evidence, existing wrapper, and the one policy line that follows from them:

    ### Data and auth
    - **Package:** `@supabase/ssr` `^0.5.2` — package.json; pnpm-lock.yaml resolves 0.5.2
    - **Local wrapper:** `src/lib/supabase.ts` exports `createServerClient()` and `createBrowserClient()`
    - Import the wrapper. This project has one Supabase package; do not add another.

Keep the whole file to roughly one or two screens. It competes for the same context window as the code, and a long file gets skimmed — which is the failure it was written to prevent.

## Stage 4: Point at it, then decide enforcement

Add one line to each instruction file the repo already has. This pointer is what actually gets `TOOLS.md` read:

    Read ./TOOLS.md before starting work in this repo, and again before changing dependencies, scripts, build config, test setup, or deploy settings. It is the canonical map of this project's stack, commands, and available agent capabilities.

The trigger has to be broader than config changes or the capability inventory is never read on the tasks it exists for: writing a migration is not a dependency change, and an inventory nobody opens is worse than no inventory, since it looks like coverage.

Put it in `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, and `.github/copilot-instructions.md` — whichever exist. One line each, pointing at the file, with the path matching the file's actual casing if you adopted an existing lowercase one. Copying the contents into them creates the second copy that goes stale.

Default to this advisory pointer rather than a hook. It is the one mechanism that works across every agent, and the failure being fixed is missing information rather than a rule being deliberately skipped: once the facts exist and are pointed at, the agent has something to read. Escalate only when advisory has demonstrably failed — a change landed that contradicts the file. Read `references/enforcement.md` when the user asks for enforcement or reports drift; it covers the portable CI drift check and the Claude Code hook wiring.

## Keeping it current

A stale `TOOLS.md` is worse than none, because it produces confidently wrong instructions with an authoritative file behind them. The staleness triggers live in the file's own maintenance section, supplied by the template, so the agent making a change reads them there rather than needing this skill loaded. That placement is deliberate: maintenance fires as a side effect of other work, and nobody asks for it by name.

When a change you are making hits one of those triggers, update the affected lines in the same change and refresh `Last verified`. Scope the edit to what changed — a full regeneration churns unrelated lines and buries the real diff in review.

## Verify

If you can execute code, run `python3 scripts/check_tools_md.py <repo-root>` (stdlib only, no install). It reports commands that no longer exist, dependency and version mismatches, package-manager contradictions, directory claims that do not match the tree, and whether the manifest changed more recently than `TOOLS.md`. Exit 0 clean, 1 drift found, 2 error. Add `--json` for machine-readable output.

Otherwise, or as a final pass, check by hand:

- [ ] Every command in the file exists in the manifest scripts, Makefile, or task file
- [ ] The package manager matches the lockfile, and no command anywhere in the file uses a different one
- [ ] Every dependency named is in the manifest, at the version the lockfile resolved
- [ ] Every directory convention named matches directories that exist
- [ ] Each capability entry has a when-to-reach-for-it line
- [ ] Unknowns are marked unknown, not filled with a plausible default
- [ ] Nothing is addressed to one assistant by name; no product-specific frontmatter or syntax
- [ ] The pointer line is in every instruction file the repo has

## Output contract

Report: the path written, the facts established with the file each came from, anything recorded as unknown and what you checked for it, which instruction files got the pointer line, and the verification result. Keep it to a short list — the file is the deliverable, not the narration.
