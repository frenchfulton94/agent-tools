# Schema & Relations (Drizzle v1)

Live docs for deep dives: `/docs/pg/sql-schema-declaration`, `/docs/pg/column-types`, `/docs/pg/indexes-constraints`, `/docs/relations-schema-declaration`, `/docs/pg/relations` (swap `pg` for the user's dialect at `https://orm.drizzle.team`).

## Contents

- Table declaration (three equivalent styles)
- Column naming and casing
- Reusable column helpers
- Indexes, constraints, enums, pg schemas
- Full worked schema example
- Relations v2 (`defineRelations`) — one, many, many-to-many, self-reference
- Legacy v0 relations (recognize, don't write)

## Table declaration

Import from the dialect core package — there is no dialect-agnostic table builder:

```ts
import { integer, pgTable, varchar } from 'drizzle-orm/pg-core';
// mysql: drizzle-orm/mysql-core (mysqlTable), sqlite: drizzle-orm/sqlite-core (sqliteTable)

export const usersTable = pgTable('users', {
	id: integer().primaryKey().generatedAlwaysAsIdentity(),
	name: varchar().notNull(),
	email: varchar().notNull().unique()
});
```

Equivalent styles: callback form `pgTable("users", (t) => ({ id: t.integer()... }))` and namespace import `import * as p from "drizzle-orm/pg-core"`. Pick one per project and stay consistent.

Everything must be **exported** — drizzle-kit imports the schema files and diffs only what it can see.

## Column naming and casing

By default the TS key IS the DB column name. Three options, in order of preference for new projects:

1. `snakeCase` builder — automatic mapping for the whole table:

```ts
import { snakeCase } from 'drizzle-orm/pg-core';
export const users = snakeCase.table('users', {
	fullName: text(), // → full_name in DB
	createdAt: timestamp() // → created_at
});
// also: snakeCase.view / .materializedView / .schema, and a camelCase twin
```

2. Explicit per-column alias: `firstName: varchar('first_name')`.
3. Accept TS-key naming (fine for greenfield solo projects, unusual for SQL conventions).

`drizzle-kit pull` has the mirror setting: `introspect.casing: "camel" | "preserve"` in config.

## Reusable column helpers

```ts
// columns.helpers.ts
export const timestamps = {
	createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
	updatedAt: timestamp('updated_at', { withTimezone: true }),
	deletedAt: timestamp('deleted_at', { withTimezone: true })
};

// any table
export const posts = pgTable('posts', {
	id: integer().primaryKey().generatedAlwaysAsIdentity(),
	...timestamps
});
```

## Indexes, constraints, enums, pg schemas

Table extras use the **array** form:

```ts
export const posts = pgTable(
	'posts',
	{
		id: t.integer().primaryKey().generatedAlwaysAsIdentity(),
		slug: t.varchar().$default(() => generateUniqueString(16)), // app-side default
		title: t.varchar({ length: 256 }),
		ownerId: t.integer('owner_id').references(() => users.id)
	},
	(table) => [t.uniqueIndex('slug_idx').on(table.slug), t.index('title_idx').on(table.title)]
);
```

- Enums (pg): `export const rolesEnum = pgEnum("roles", ["guest", "user", "admin"]);` then `role: rolesEnum().default("guest")`.
- Self-reference needs an explicit type: `invitee: t.integer().references((): AnyPgColumn => users.id)` (`AnyPgColumn` from `drizzle-orm/pg-core`).
- Composite PK (junction tables): `(t) => [primaryKey({ columns: [t.userId, t.groupId] })]`.
- Postgres schemas: `export const custom = pgSchema('custom'); export const users = custom.table('users', {...})`.
- `.references()` creates a real FK constraint. Teams on PlanetScale/sharded/high-write systems sometimes skip FKs deliberately — if so, relations still work (see below) since v2 relations are defined independently of FKs.
- `$default(() => ...)` runs in the app at insert time; `.default(...)`/`.defaultNow()` is a database-level default. Use `$onUpdate(() => new Date())` style helpers for updatedAt if desired.

## Full worked example (Postgres)

```ts
import type { AnyPgColumn } from 'drizzle-orm/pg-core';
import { pgEnum, pgTable as table } from 'drizzle-orm/pg-core';
import * as t from 'drizzle-orm/pg-core';

export const rolesEnum = pgEnum('roles', ['guest', 'user', 'admin']);

export const users = table(
	'users',
	{
		id: t.integer().primaryKey().generatedAlwaysAsIdentity(),
		firstName: t.varchar('first_name', { length: 256 }),
		lastName: t.varchar('last_name', { length: 256 }),
		email: t.varchar().notNull(),
		invitee: t.integer().references((): AnyPgColumn => users.id),
		role: rolesEnum().default('guest')
	},
	(table) => [t.uniqueIndex('email_idx').on(table.email)]
);

export const posts = table(
	'posts',
	{
		id: t.integer().primaryKey().generatedAlwaysAsIdentity(),
		title: t.varchar({ length: 256 }),
		ownerId: t.integer('owner_id').references(() => users.id)
	},
	(table) => [t.index('title_idx').on(table.title)]
);
```

## Relations v2 — `defineRelations`

Relations live in their own file, defined over the whole schema, and are passed to `drizzle()` at init. They power `db.query` and are independent of FK constraints.

```ts
// relations.ts
import { defineRelations } from 'drizzle-orm';
import * as schema from './schema';

export const relations = defineRelations(schema, (r) => ({
	users: {
		posts: r.many.posts(), // inverse side can be bare
		invitee: r.one.users({
			// self-relation
			from: r.users.invitedBy,
			to: r.users.id
		}),
		groups: r.many.groups({
			// many-to-many THROUGH junction
			from: r.users.id.through(r.usersToGroups.userId),
			to: r.groups.id.through(r.usersToGroups.groupId)
		})
	},
	posts: {
		author: r.one.users({ from: r.posts.authorId, to: r.users.id }),
		comments: r.many.comments()
	},
	comments: {
		post: r.one.posts({ from: r.comments.postId, to: r.posts.id }),
		author: r.one.users({ from: r.comments.creator, to: r.users.id })
	}
}));
```

```ts
// db.ts
import { relations } from './relations';
import { drizzle } from 'drizzle-orm/node-postgres'; // driver-specific path

export const db = drizzle(process.env.DATABASE_URL, { relations });
```

Notes:

- The side that holds the FK column gets the explicit `{ from, to }`; the inverse side can be a bare `r.many.x()`.
- `.through()` on both `from` and `to` lets `db.query.users.findMany({ with: { groups: true } })` return groups directly — never hand-join the junction table in relational queries.
- Relation names (`author`, `comments`) are the keys used in `with: {}` — name them from the perspective of the table that owns them.

## Legacy v0 relations (recognize only)

Pre-v1 code uses `relations(users, ({ one, many }) => ({...}))` per table and passes `{ schema }` to `drizzle()`. If you see this, the project is on v0.x: either stay consistent with v0 idioms or guide the user through `/docs/upgrade-v1` and `/docs/relations-v1-v2`. Do not mix the two APIs.
