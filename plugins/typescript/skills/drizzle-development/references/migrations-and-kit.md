# Migrations & Drizzle Kit

Live docs for deep dives: `/docs/migrations` (fundamentals), `/docs/kit-overview`, `/docs/drizzle-kit-generate`, `/docs/drizzle-kit-migrate`, `/docs/drizzle-kit-push`, `/docs/drizzle-kit-pull`, `/docs/drizzle-kit-export`, `/docs/kit-custom-migrations`, `/docs/kit-migrations-for-teams`, `/docs/kit-web-mobile`, `/docs/drizzle-config-file` at `https://orm.drizzle.team`.

## Contents

- drizzle.config.ts — the minimum and the useful options
- Choosing a migration workflow (decision guide)
- The generate → migrate flow in detail
- push, pull, and runtime migrations
- Team practices and custom SQL migrations

## drizzle.config.ts

Lives at project root. Minimum viable config:

```ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
	dialect: 'postgresql', // required: postgresql | mysql | sqlite | turso | singlestore | mssql | cockroach
	schema: './src/db/schema.ts', // file, folder, glob, or array — e.g. "./src/db/schema/*" or "./src/**/*.sql.ts"
	out: './drizzle', // migrations folder (default "drizzle")
	dbCredentials: { url: process.env.DATABASE_URL! }
});
```

Options worth knowing (full reference: `/docs/drizzle-config-file`):

- `driver` — only for exception drivers: `"pglite"`, `"aws-data-api"`. Otherwise drizzle-kit auto-detects from the installed packages.
- `migrations: { table, schema }` — rename the applied-migrations log (default `__drizzle_migrations` in schema `drizzle`).
- `tablesFilter` / `schemaFilter` / `extensionsFilters` — scope push/pull; `extensionsFilters: ["postgis"]` stops kit trying to drop postgis's own tables.
- `introspect: { casing: "camel" | "preserve" }` — column key casing for `pull`.
- `entities.roles` — enable role management; `{ provider: 'neon' | 'supabase' }` ignores provider-managed roles.
- `verbose`, `breakpoints` (statement breakpoints needed for MySQL/SQLite multi-DDL), `strict`.
- Multiple configs per environment: `drizzle-kit generate --config=drizzle-prod.config.ts`.

## Choosing a migration workflow

Ask which of these matches the project, then commit to it — mixing `push` and `generate` histories against the same database causes drift:

| Situation                                                                 | Workflow                                                                           |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Database is managed elsewhere (DBA, external tool); code just needs types | **Database-first**: `drizzle-kit pull` generates the TS schema from the live DB    |
| Rapid prototyping, solo dev, local/preview databases                      | `drizzle-kit push` — diffs TS schema against DB and applies directly, no SQL files |
| Team, CI/CD, production — need reviewable, versioned SQL                  | `drizzle-kit generate` + `drizzle-kit migrate`                                     |
| Same as above, but migrations run at app boot / deploy step               | `generate` + runtime `migrate()` from `drizzle-orm/<driver>/migrator`              |
| SQL applied by an external migrator (Bytebase, Liquibase, Atlas)          | `generate` (they consume the SQL files) or `drizzle-kit export` (prints SQL DDL)   |

`push` is legitimately production-viable for solo/small projects (the docs endorse it), but the moment multiple people or environments share a database, switch to generate/migrate.

## generate → migrate in detail

```bash
npx drizzle-kit generate   # diff schema vs. previous snapshot → drizzle/<timestamp>_<name>/migration.sql + snapshot.json
npx drizzle-kit migrate    # apply unapplied migrations, record them in __drizzle_migrations
```

- `generate` prompts about ambiguous changes (rename vs drop+create) — answer carefully; a "rename" answered as "create" drops the column's data.
- Commit the whole `out` folder (SQL + snapshots + journal) to version control.
- `drizzle-kit check` validates migration consistency (race detection for teams); `drizzle-kit up` upgrades old snapshot formats.
- Runtime application:

```ts
import { drizzle } from 'drizzle-orm/node-postgres';
import { migrate } from 'drizzle-orm/node-postgres/migrator';

const db = drizzle(process.env.DATABASE_URL);
await migrate(db, { migrationsFolder: './drizzle' });
```

## push and pull

- `push`: pulls current DB schema, diffs against TS schema, applies ALTERs. Use `verbose: true` to print SQL before applying. Destructive changes prompt for confirmation.
- `pull`: introspects the DB and writes a `schema.ts` into `out`. Use for database-first projects or a one-time import of an existing DB, then usually switch to codebase-first.

## Team practices

- One migration per PR where possible; regenerate rather than hand-editing generated SQL.
- Need custom SQL (data backfills, triggers, RLS policies, concurrent index creation)? `drizzle-kit generate --custom` creates an empty timestamped migration to fill in — keeps custom SQL in the same ordered history. See `/docs/kit-custom-migrations`.
- Merge conflicts in the journal/snapshots mean two branches generated concurrently — regenerate on the merged branch and run `drizzle-kit check`. See `/docs/kit-migrations-for-teams`.
- Expo/React Native and browser targets can't run the Node migrator — they bundle migrations via a babel/metro plugin. See `/docs/kit-web-mobile`.
- Never point `push` at production while teammates use `migrate` on it. Pick one source of truth per database.
