# typescript

The TypeScript toolchain, from the compiler settings a new project starts with to the errors an
old one emits.

## Install

    claude plugin marketplace add YOUR-GITHUB-OWNER/agent-tools --scope project
    claude plugin install typescript@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/typescript
claude plugin validate plugins/typescript --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `writing-typescript` | Skill | Compiler settings and type-level design for new code — tsconfig, strictness, API shape, `satisfies` |
| `refactoring-typescript` | Skill | Tightening code that already ships — removing `any`, staging strictness flags, JS-to-TS migration |
| `debugging-type-errors` | Skill | Reading error elaborations bottom-up, narrowing failures, why `tsc` resolved an import a given way |
| `vitest-testing` | Skill | Writing, running, and debugging Vitest suites — mocking, async, snapshots, coverage |
| `vite` | Skill | Configuring, debugging, and upgrading Vite projects |
| `configuring-biome` | Skill | Formatter, linter, and assist configuration; migration from ESLint and Prettier |
| `drizzle-development` | Skill | Typed schemas, relations, relational queries, and migrations with Drizzle ORM and Drizzle Kit |
| `bun` | Skill | Bun as the runtime, package manager, test runner, and bundler |

The three TypeScript skills are split by *when* you reach for them, not by topic: starting new
code, changing code that already ships, and reading an error that does not say what it means. A
single description covering all three fires imprecisely on each.

## Where the boundary with `frontend` sits

`typescript` is what the type system reaches — the compiler, the test runner, the bundler, and the
data layer whose whole value is that its schemas are typed. `frontend` is what renders. A question
about `tsconfig`, a failing Vitest run, or a Drizzle schema belongs here; a question about a Svelte
component, a Tailwind theme, or where a file goes under FSD belongs there.

`drizzle-development` sits here rather than with the app stack because Drizzle is used from a
TypeScript project of any shape — a SvelteKit route, a Bun HTTP server, a migration script — and
what makes it worth a skill is inference through schemas and relations, which is the same subject
as the rest of this plugin.

## License

MIT.
