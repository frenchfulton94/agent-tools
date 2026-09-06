# Querying (Drizzle v1)

Live docs for deep dives: `/docs/rqb` (relational queries), `/docs/select`, `/docs/insert`, `/docs/update`, `/docs/delete`, `/docs/operators`, `/docs/joins`, `/docs/sql` (magic sql operator), `/docs/dynamic-query-building`, `/docs/transactions`, `/docs/batch-api` at `https://orm.drizzle.team`.

## Contents

- Choosing between the two query APIs
- SQL-like builder essentials
- Relational queries (`db.query`) — filters, nesting, extras, prepared statements
- The callback rule (critical)
- The magic sql`` operator — safety and typing
- Dynamic/optional filters
- Transactions and performance notes

## Choosing the API

- **Relational queries (`db.query.x.findMany/findFirst`)** — reads returning nested/related data. One SQL statement always; no manual joins or row de-duplication. Serverless-friendly.
- **SQL-like builder (`db.select/insert/update/delete`)** — everything else: writes, aggregations, GROUP BY/HAVING, set operations, fine-grained join control. If you know SQL, you know this API.

Both can coexist freely in one codebase.

## SQL-like builder essentials

```ts
import { eq, and, lte, ilike, desc } from 'drizzle-orm';

await db
	.select()
	.from(posts)
	.leftJoin(comments, eq(posts.id, comments.postId))
	.where(eq(posts.id, 10));

await db.insert(users).values({ email: 'user@gmail.com' }).returning(); // returning: pg/sqlite
await db.update(users).set({ email: 'x@y.z' }).where(eq(users.id, 1));
await db.delete(users).where(eq(users.id, 1));
```

Subqueries are composable values:

```ts
const sub = db
	.select()
	.from(internalStaff)
	.leftJoin(customUser, eq(internalStaff.userId, customUser.id))
	.as('internal_staff');

await db.select().from(ticket).leftJoin(sub, eq(sub.internal_staff.userId, ticket.staffId));
```

## Relational queries

Filters are plain objects in v1 (no operator imports needed for common cases):

```ts
const users = await db.query.users.findMany({
	where: {
		id: { gt: 10 }, // column operators: eq ne gt gte lt lte in notIn
		name: { like: 'John%' }, // like ilike notLike notIlike isNull isNotNull
		OR: [{ age: 15 }, { age: { gt: 60 } }], // OR / AND / NOT combinators
		posts: { content: { like: 'M%' } } // filter by RELATED table
	},
	columns: { id: true, name: true }, // partial select (or exclude: { content: false })
	with: {
		posts: {
			where: { createdAt: { lt: new Date() } },
			limit: 3,
			offset: 3, // offset works on nested relations too
			orderBy: { id: 'desc' },
			columns: { authorId: false },
			with: { comments: true } // nest as deep as needed
		}
	},
	limit: 5,
	orderBy: { id: 'asc' }
});
```

- `where: { posts: true }` = "has at least one post".
- When both `true` and `false` appear in `columns`, the `false` entries are ignored.
- `findFirst()` = `findMany` + `limit 1`.

### The callback rule (critical)

Any clause that accepts custom SQL inside a relational query — `orderBy` callbacks, `where.RAW`, `extras`, and subqueries inside extras — **must reference columns via the callback parameter**, never the imported table object. The callback provides the aliased table for the current query scope; the imported table breaks nested/self-referential SQL.

```ts
// ❌ wrong — imported table
await db.query.posts.findMany({
  orderBy: sql`${posts.id} asc`,
  with: { comments: { orderBy: sql`${comments.id} desc` } },
});

// ✅ right — callback parameter
await db.query.posts.findMany({
  orderBy: (t) => sql`${t.id} asc`,
  with: { comments: { orderBy: (t, { desc }) => desc(t.id) } },
});

// same rule for RAW and extras:
where: { RAW: (t) => sql`LOWER(${t.name}) LIKE 'john%'` }
extras: {
  loweredName: (t, { sql }) => sql<string>`lower(${t.name})`,
  totalPostsCount: (t) => db.$count(posts, eq(posts.authorId, t.id)),
}
```

### extras

- Add computed fields per row; typed via `sql<T>`.
- **Aggregations are not supported in extras** — `db.$count(...)` is the sanctioned subquery-count helper; anything else aggregate-shaped belongs in `db.select()`.
- `.as('alias')` on an extras field is ignored — the object key is the field name.

### Prepared statements

```ts
const prepared = db.query.users
	.findMany({
		where: { id: { eq: sql.placeholder('id') } },
		limit: sql.placeholder('limit')
	})
	.prepare('users_by_id');

await prepared.execute({ id: 1, limit: 10 });
```

Placeholders work in `where`, `limit`, and `offset`, including nested relations. Use prepared statements on hot paths — see `/docs/perf-queries`.

## The magic sql`` operator

```ts
import { sql } from 'drizzle-orm';

await db.execute(sql`select * from ${usersTable} where ${usersTable.id} = ${id}`);
// → select * from "users" where "users"."id" = $1   [id]
```

- Interpolated tables/columns become escaped identifiers; interpolated values become **parameters** — injection-safe by construction.
- `sql.raw(str)` inserts text verbatim with **no** parameterization. Only ever for trusted static fragments; never user input.
- `sql<T>` types the expression at compile time only. Runtime conversion needs `.mapWith(Number)` / `.mapWith(someColumn)` (e.g., pg returns `count(*)` as a string).
- `.as('alias')` names a selected expression.
- Compose incrementally with `sql.empty()` + `.append()`, or `sql.join(chunks, sql.raw(' '))`.
- Usable in partial selects, `where`, `orderBy` (`sql\`${t.id} desc nulls first\``), `groupBy`, `having`.

```ts
await db
	.select({
		id: usersTable.id,
		lowerName: sql<string>`lower(${usersTable.name})`.as('lower_name'),
		count: sql<number>`count(*)`.mapWith(Number)
	})
	.from(usersTable);
```

## Dynamic / optional filters

The canonical pattern — collect conditions, spread into `and()`:

```ts
import { SQL, and, eq, ilike, lte } from 'drizzle-orm';

async function getProductsBy({
	name,
	category,
	maxPrice
}: {
	name?: string;
	category?: string;
	maxPrice?: number;
}) {
	const filters: SQL[] = [];
	if (name) filters.push(ilike(products.name, name));
	if (category) filters.push(eq(products.category, category));
	if (maxPrice) filters.push(lte(products.price, maxPrice));
	return db
		.select()
		.from(products)
		.where(and(...filters));
}
```

`and()` with zero args is a no-op where-clause, so the function works with no filters set. For reusable query fragments across a codebase (pagination helpers, `$dynamic()` mode), see `/docs/dynamic-query-building`.

## Transactions and performance notes

- Transactions: `await db.transaction(async (tx) => { await tx.insert(...); await tx.update(...); })` — use `tx`, not `db`, inside; throw to roll back. Full API incl. isolation levels: `/docs/transactions`.
- Batch API (D1, LibSQL, Neon HTTP): send multiple statements in one round trip — `/docs/batch-api`.
- Relational queries emit exactly one SQL statement (lateral joins + json aggregation). Great default; for very wide `with` trees on hot paths, check the generated SQL (`.toSQL()`) and measure.
