# Starter Templates

Pruned templates by project type. Every line demonstrates the governing test — it names something an agent would otherwise get wrong; the closing section explains what was deliberately left out and why. Replace the examples with your repo's facts; delete any section with nothing non-obvious to say. Draw headers from this menu, keeping only those with something non-obvious to say: Commands, Architecture, Key files, Code style, Environment, Testing, Gotchas, Workflow. If you want to annotate your own file with per-line justifications, use HTML comments — they're stripped before the agent sees the file, so they cost nothing.

Contents:
- [Web application](#web-application)
- [Library / package](#library--package)
- [Monorepo root](#monorepo-root)
- [Monorepo package](#monorepo-package)
- [What was deliberately left out](#what-was-deliberately-left-out)

## Web application

```markdown
# Commands
- Dev server: `pnpm dev` (NOT npm — lockfile is pnpm)
- Tests: `pnpm test:unit` for fast loop; `pnpm test` runs e2e too (slow, needs Docker)
- Before committing: `pnpm typecheck && pnpm lint`

# Architecture
- App router pages in `app/`; legacy pages router still serves `/admin/*` — don't migrate without a ticket
- API handlers in `app/api/*/route.ts`; shared validation schemas in `lib/schemas/`
- Generated code in `src/gql/` — never edit by hand; regenerate with `pnpm codegen`

# Conventions
- Server components by default; add `"use client"` only for interactivity
- Feature flags via `flags.ts` helpers, never env checks inline

# Gotchas
- `DATABASE_URL` must point at the pooled port (6543), not 5432, or migrations hang
- User deletion is soft: every user query needs `deleted_at IS NULL`
```

## Library / package

```markdown
# Commands
- Build: `npm run build` (tsup; outputs dual ESM/CJS — check both in `dist/`)
- Tests: `npm test`; single file: `npx vitest run test/<file>.test.ts`
- Docs preview: `npm run docs:dev`

# Conventions
- Public API is exactly what `src/index.ts` exports; everything else is internal
- No new runtime dependencies without discussion — this ships to browsers
- Breaking changes need a changeset (`npx changeset`) and a major bump

# Gotchas
- `tsconfig.build.json` differs from `tsconfig.json`; editor may accept what the build rejects
```

## Monorepo root

```markdown
# Layout
- `apps/*` deployables, `packages/*` shared libs; per-package guidance lives in each package's own CLAUDE.md

# Commands
- Everything through turbo: `pnpm turbo test --filter=<pkg>` (bare `pnpm test` runs the world — slow)
- Adding a dependency: `pnpm add <dep> --filter=<pkg>`, never at the root

# Etiquette
- Branches: `<initials>/<ticket>-<slug>`; PRs squash-merge; commit style: conventional commits
- Changes spanning packages need a changeset

# Gotchas
- `packages/config` is consumed at build time by all apps — changes there rebuild everything
```

## Monorepo package

Lives at `packages/<name>/CLAUDE.md`; loads only when the agent works in this package.

```markdown
# This package
- Public interface in `src/index.ts`; consumed by `apps/web` and `apps/mobile`
- Tests colocated as `*.test.ts`; run just this package: `pnpm turbo test --filter=@acme/auth`

# Gotchas
- Session tokens here are opaque strings; `apps/web` calls the same concept `sid` — same value, different name
```

## What was deliberately left out

Every template omits, on purpose:

- Language/framework tutorials and standard conventions (the model knows them)
- File-by-file directory listings (derivable, goes stale)
- Code style rules a linter enforces (route to the linter; the agent reads linter config)
- API endpoint documentation (link it, or path-scope it to the API directory)
- Deploy runbooks and multi-step procedures (route to a skill)
- Aspirational statements ("we value clean code") — not actionable, costs adherence budget
