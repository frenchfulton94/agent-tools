---
name: drizzle-development
description: Professional development with Drizzle ORM and Drizzle Kit in TypeScript — defining schemas, relations, and relational queries; running migrations (generate/migrate/push/pull); configuring drizzle.config.ts; writing safe raw SQL with the sql`` operator; and upgrading to Drizzle v1. Use whenever the user works with Drizzle, drizzle-orm, drizzle-kit, drizzle-zod/drizzle-seed, or mentions pgTable/mysqlTable/sqliteTable, defineRelations, db.query, or db.select in a TypeScript project — even if they just say "my ORM" or "my database schema" in a project that uses Drizzle. Not for Prisma, TypeORM, Kysely, or raw SQL projects that don't use Drizzle.
metadata:
  docs-root: https://orm.drizzle.team
---

# Drizzle ORM Development

Drizzle is a TypeScript ORM (SQL-like query builder + relational queries) paired with Drizzle Kit (migration CLI). This skill captures the current (v1.x) APIs and the decisions that separate professional Drizzle work from copy-paste code. Drizzle's API changed significantly at v1.0, so knowledge from older tutorials and training data is often stale — when in doubt, fetch the live docs (see "Staying current" below).

## Staying current with the live docs

The bundled references cover the core concepts, but Drizzle evolves quickly. For anything version-sensitive, dialect-specific, or not covered here, fetch the official docs directly:

- Index of all doc pages: `https://orm.drizzle.team/llms.txt` — fetch this first when you need to find the right page.
- Docs are **dialect-scoped**. Prefer the URL for the user's dialect: `https://orm.drizzle.team/docs/pg/<topic>`, `/docs/mysql/<topic>`, `/docs/sqlite/<topic>`, `/docs/singlestore/<topic>`, `/docs/mssql/<topic>`, `/docs/cockroach/<topic>`. The unscoped `/docs/<topic>` pages default to PostgreSQL.
- Fetch live docs (rather than relying on memory) when: the user reports a type error or "X is not a function" against code that looks correct; the task involves a specific driver/platform (Neon, Supabase, D1, Turso, Expo, PlanetScale…); the user is upgrading versions; or you need an exhaustive option/column-type list.

Key deep-dive URLs (substitute the dialect segment as needed):

| Topic                         | URL                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| v1 upgrade & breaking changes | `/docs/upgrade-v1`, `/docs/v0-v1-changes`, `/docs/relations-v1-v2`                                     |
| Column types per dialect      | `/docs/pg/column-types` (or mysql/sqlite/…)                                                            |
| Indexes & constraints         | `/docs/pg/indexes-constraints`                                                                         |
| Relational queries (full API) | `/docs/rqb`                                                                                            |
| Select/Insert/Update/Delete   | `/docs/select`, `/docs/insert`, `/docs/update`, `/docs/delete`                                         |
| Filters & operators           | `/docs/operators`                                                                                      |
| drizzle-kit commands          | `/docs/kit-overview`, `/docs/drizzle-kit-generate`, `/docs/drizzle-kit-push`, `/docs/drizzle-kit-pull` |
| drizzle.config.ts reference   | `/docs/drizzle-config-file`                                                                            |
| Transactions, batch, caching  | `/docs/transactions`, `/docs/batch-api`, `/docs/cache`                                                 |
| Dynamic query building        | `/docs/dynamic-query-building`                                                                         |
| Validation integrations       | `/docs/zod`, `/docs/valibot`, `/docs/typebox`, `/docs/arktype`, `/docs/effect-schema`                  |
| Seeding                       | `/docs/seed-overview`                                                                                  |
| Connections per platform      | `/docs/connect-overview` and `/docs/connect-<provider>`                                                |

## Bundled references — read the one that matches the task

- **Schema, columns, relations** → [references/schema-and-relations.md](references/schema-and-relations.md). Read before writing or reviewing any table/relations definitions.
- **Querying (SQL-like builder, relational queries, sql`` operator, dynamic filters)** → [references/querying.md](references/querying.md). Read before writing non-trivial queries.
- **Migrations & drizzle-kit workflows** → [references/migrations-and-kit.md](references/migrations-and-kit.md). Read before setting up config, generating migrations, or advising on push vs generate.

## Core workflow for a Drizzle task

1. **Identify the dialect and driver first** (Postgres/MySQL/SQLite/…; node-postgres/Neon/D1/…). Every import path (`drizzle-orm/pg-core` vs `mysql-core` vs `sqlite-core`) and every doc URL depends on it. If it's not stated, check `drizzle.config.ts` (`dialect` field) or package.json before writing code.
2. **Check the Drizzle version** in package.json. v1.x uses `defineRelations` and object-style relational filters; v0.x uses the legacy `relations()` helper and callback-style filters. Mixing the two produces confusing type errors. If the project is v0 and the user wants new features, point them to `/docs/upgrade-v1`.
3. **Read the relevant bundled reference** for the task, then write the code.
4. **Verify against the gotchas below** — these are the mistakes that type-check less loudly or fail only at runtime.

## Gotchas (verify every one that applies before finishing)

These are current-API facts that defy reasonable assumptions and are the most common sources of subtle bugs:

- **Inside relational queries (`db.query...`), column references in `orderBy`, `where.RAW`, `extras`, and subqueries inside extras must go through the callback parameter, not the imported table object.** `orderBy: (t, { desc }) => desc(t.id)` is correct; `orderBy: desc(posts.id)` generates wrong SQL in nested or self-referential queries because the callback exposes the aliased table for the current scope.
- **Drizzle uses the TypeScript key as the database column name by default.** `firstName: varchar()` creates a column literally named `firstName`. Either pass an explicit name (`varchar('first_name')`) or use the `snakeCase` builder (`snakeCase.table(...)` from the dialect core package) so `firstName` maps to `first_name`. Decide this at project start — changing later means a rename migration.
- **Every schema model must be `export`ed**, or drizzle-kit silently won't see it and migrations will try to drop the "missing" table.
- **Table-level extras (indexes, composite PKs, checks) use the array form**: `(table) => [uniqueIndex('email_idx').on(table.email)]`. The old object-return form is deprecated.
- **`sql\`...\``parameterizes interpolations automatically;`sql.raw()`does not.** Never pass user input through`sql.raw()`— that's a SQL injection. Use`sql.raw()` only for trusted, static fragments (keywords, identifiers you generated).
- **`sql<T>` is a compile-time type hint only — no runtime conversion.** For runtime mapping (e.g., `count(*)` arriving as a string from pg), use `.mapWith(Number)` or `.mapWith(column)`.
- **`extras` in relational queries do not support aggregations.** Use `db.$count(...)` inside extras for counts, or drop to the core `db.select()` builder for other aggregations.
- **`drizzle-kit push` and `generate`/`migrate` are alternative workflows, not stages of one.** Push diffs schema↔database directly (great for prototyping and SQLite/local dev); generate+migrate produces versioned SQL files tracked in `__drizzle_migrations` (required for teams/CI/production). Mixing them against the same database causes drift. See the migrations reference for choosing.
- **Self-referencing foreign keys need an explicit return type**: `invitedBy: integer().references((): AnyPgColumn => users.id)` — otherwise TypeScript can't resolve the circular type.
- **For many-to-many, define the junction table in the schema but use `.through()` in `defineRelations`** so queries skip the junction: `r.many.groups({ from: r.users.id.through(r.usersToGroups.userId), to: r.groups.id.through(r.usersToGroups.groupId) })`.
- **Relational queries always emit exactly one SQL statement** (lateral-join based). This makes them safe for serverless round-trip costs, but it also means one giant query — for very wide `with` trees on hot paths, measure and consider splitting.

## Professional defaults

When the user hasn't specified otherwise, prefer these (mention alternatives only when relevant):

- Postgres primary keys: `integer().primaryKey().generatedAlwaysAsIdentity()` (the docs' current default, replacing `serial`).
- Timestamps: `timestamp('created_at', { withTimezone: true }).notNull().defaultNow()` on Postgres; share `createdAt/updatedAt/deletedAt` via a spread helper object across tables.
- Schema layout: `src/db/schema.ts` (or a `src/db/schema/` folder — every file must export its models), `relations.ts` beside it, `drizzle.config.ts` at project root with `dialect`, `schema`, `out`, and `dbCredentials.url` from `process.env`.
- Reads that return nested data → relational queries (`db.query`); everything else (aggregations, complex joins, inserts/updates/deletes, set operations) → the SQL-like builder.
- Optional/dynamic filters → build a `SQL[]` array and pass `and(...filters)`; don't concatenate strings.
- Runtime validation of insert/update payloads → `drizzle-zod` (`createInsertSchema`/`createSelectSchema`) or the equivalent for the user's validation library.

## Reviewing existing Drizzle code

When asked to review or debug, check in this order: (1) version/API mismatch (v0 idioms in a v1 project or vice versa), (2) the gotchas list above, (3) missing `.notNull()`/defaults that the application logic assumes, (4) missing indexes on foreign-key and frequently-filtered columns, (5) `sql.raw()` or string concatenation with user input, (6) N+1 patterns that a single relational query would replace.
