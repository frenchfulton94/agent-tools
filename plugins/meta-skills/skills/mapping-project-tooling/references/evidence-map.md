# Evidence Map

Where each fact in `TOOLS.md` comes from, per ecosystem, plus the cases where evidence
is ambiguous. The package-manager table lives in SKILL.md; this file covers everything
after that.

Contents:
- [JavaScript and TypeScript](#javascript-and-typescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Ruby](#ruby)
- [JVM](#jvm)
- [PHP](#php)
- [Version currency](#version-currency)
- [Monorepos and polyglot repos](#monorepos-and-polyglot-repos)
- [Contradictory evidence](#contradictory-evidence)
- [What not to record](#what-not-to-record)

## JavaScript and TypeScript

| Fact | Evidence |
|---|---|
| Framework | Dependency in `package.json` plus its config: `next.config.*`, `vite.config.*`, `astro.config.*`, `nuxt.config.*`, `remix.config.*`, `angular.json` |
| Next.js router | `app/` with `app/layout.*` means App Router; `pages/` with `pages/_app.*` means Pages Router; both present means a migration in progress — record which one new code uses and say why |
| API routes | App Router: `app/**/route.ts`. Pages Router: `pages/api/*.ts`. Check which directory actually holds existing handlers |
| TypeScript | `tsconfig.json` plus `typescript` in devDependencies; note `strict` and path aliases from `compilerOptions.paths` |
| UI system | `tailwind.config.*`, `components.json` (shadcn/ui), `@mui/*`, `chakra-ui`, or a local `components/ui/` directory |
| Test tooling | `vitest.config.*`, `jest.config.*`, `playwright.config.*`, `cypress.config.*`, plus the script that invokes each |
| Lint and format | `eslint.config.*` or `.eslintrc.*`, `biome.json`, `.prettierrc*`, `oxlint.json` |
| Monorepo tooling | `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `workspaces` in `package.json` |

The `packageManager` field in `package.json` pins an exact manager version and outranks
a bare lockfile guess. When it disagrees with the lockfile present, that is a
contradiction — see below.

## Python

| Fact | Evidence |
|---|---|
| Manager | `uv.lock`, `poetry.lock`, `Pipfile.lock`, `pdm.lock`, or bare `requirements*.txt` with no lockfile |
| Dependencies | `[project.dependencies]` or `[tool.poetry.dependencies]` in `pyproject.toml`, else `requirements*.txt` |
| Python version | `.python-version`, `requires-python` in `pyproject.toml`, `python_requires` in `setup.cfg` |
| Framework | `django` plus `manage.py` and `settings.py`; `fastapi` plus an `app`/`main` module; `flask` plus an app factory |
| Task runner | `[tool.poe]`, `[tool.pdm.scripts]`, `Makefile`, `justfile`, `tox.ini`, `noxfile.py` |
| Test tooling | `pytest` plus `[tool.pytest.ini_options]`, `pytest.ini`, or `tox.ini`; `unittest` discovery in a script |
| Lint, format, types | `ruff.toml` or `[tool.ruff]`, `[tool.black]`, `mypy.ini` or `[tool.mypy]`, `pyrightconfig.json` |

Python has no scripts field by default, so commands usually come from a `Makefile`,
`justfile`, or a tool-specific scripts table. Do not invent `python -m` invocations
the repo never uses.

## Go

| Fact | Evidence |
|---|---|
| Module path and Go version | `go.mod` |
| Dependencies | `require` blocks in `go.mod`, resolved in `go.sum` |
| Layout | `cmd/`, `internal/`, `pkg/` as they actually exist |
| Commands | `Makefile` or `Taskfile.yml`; otherwise the standard `go build ./...`, `go test ./...` |
| Lint | `.golangci.yml` |

## Rust

| Fact | Evidence |
|---|---|
| Crate, edition, toolchain | `Cargo.toml`, `rust-toolchain.toml` |
| Dependencies and versions | `[dependencies]` in `Cargo.toml`, resolved in `Cargo.lock` |
| Workspace members | `[workspace]` in the root `Cargo.toml` |
| Commands | `Makefile.toml` (cargo-make), `justfile`, else standard cargo commands |

## Ruby

| Fact | Evidence |
|---|---|
| Ruby version | `.ruby-version`, `Gemfile` `ruby` directive |
| Dependencies | `Gemfile`, resolved in `Gemfile.lock` |
| Framework | `rails` gem plus `config/application.rb` |
| Commands | `Rakefile`, `bin/` scripts, `Procfile` |

## JVM

| Fact | Evidence |
|---|---|
| Build tool | `pom.xml` (Maven), `build.gradle` or `build.gradle.kts` (Gradle), wrapper scripts `mvnw` / `gradlew` |
| Java version | `maven.compiler.release`, `sourceCompatibility`, `.sdkmanrc` |
| Dependencies | Declared in the build file; Gradle lockfiles under `gradle/` when present |

Prefer the wrapper (`./gradlew`, `./mvnw`) in recorded commands when it exists, since it
pins the build tool version.

## PHP

| Fact | Evidence |
|---|---|
| Dependencies and PHP version | `composer.json`, resolved in `composer.lock` |
| Framework | `laravel/framework` plus `artisan`; `symfony/*` plus `bin/console` |
| Commands | `composer.json` `scripts`, `Makefile` |

## Version currency

A dependency being installed does not make it the right one to extend. Record what is
installed; also record which package the repo's own source imports for each capability,
found by searching the source tree for the import. When a project has both a superseded
package and its replacement installed, the imports settle which one is live — write that
down explicitly, because that ambiguity is exactly what makes a later agent pick wrong.

Do not label a package deprecated from memory. Either the repo shows it (an install
warning in a lockfile, a deprecation comment, a migration note) or you check the
registry if you have network access. If neither, record the installed package and
version without a currency claim.

## Monorepos and polyglot repos

- One `TOOLS.md` at the repo root, describing the workspace layout and the per-package differences that matter. Do not scatter copies into every package; the pointer indirection is what keeps them from diverging.
- Record the workspace tool and how to run a command scoped to one package (`pnpm --filter web build`, `turbo run test --filter=api`, `cargo test -p core`).
- When packages genuinely differ in framework or test runner, give each its own short subsection under Layout rather than flattening them into one claim.
- For a polyglot repo, list each ecosystem's manager and commands separately and say which directories each governs.

## Contradictory evidence

Two lockfiles at root, a `packageManager` field that disagrees with the lockfile, a
config that names a directory that does not exist, a CI workflow using a different
manager than the repo does. All of these are common and none should be resolved by
picking the more popular option.

Resolution order:

1. Ask the user if they are in the conversation. One question is cheaper than a wrong line.
2. Otherwise prefer evidence that something executes against — a CI workflow that passes, the lockfile that CI installs from — over declarative files nobody runs.
3. If it still does not resolve, record it under Unknowns with both sides named: "Two lockfiles present (`package-lock.json`, `pnpm-lock.yaml`); CI installs with pnpm. Confirm before running either."

A recorded contradiction is useful to the next agent. A silently picked winner is the
failure this file exists to prevent.

## What not to record

- Full dependency listings. `TOOLS.md` names the dependencies that shape decisions, not everything in the manifest — the manifest is already in the repo and is authoritative.
- Pricing, subscription tiers, or renewal dates. That belongs to a personal tool inventory, not a repo file.
- Architecture rationale, review policy, or coding style. Those go in the memory file.
- Facts that change every commit, such as exact patch versions of transitive dependencies.
- Anything you could not point to a file for.
