# Behavior test cases: mapping-project-tooling

Run each with the skill and without (baseline), clean context per run. Grade each
assertion PASS/FAIL with quoted evidence from the output, no benefit of the doubt.

Cases 1 and 2 are the must-pass pair: 1 tests the artifact, 2 tests the behavior the
artifact induces. A skill that passes 1 and fails 2 has produced a document nobody acts
on, which is the only outcome that matters.

## Fixture repo

Used by cases 1 and 2. Root contains:

```
package.json      packageManager pnpm@9.12.0; scripts dev/build/lint/test/test:e2e;
                  deps next 14.2.5, react ^18.3.1, @supabase/ssr ^0.5.2,
                  @supabase/supabase-js ^2.45.0; devDeps typescript, vitest,
                  @playwright/test, tailwindcss
pnpm-lock.yaml    (present)
next.config.mjs   tsconfig.json   vercel.json
app/layout.tsx    app/dashboard/page.tsx        (no pages/ directory)
src/lib/supabase.ts   exports createServerClient() and createBrowserClient()
.mcp.json         one server, "db", read-only Postgres
.claude/skills/db-migrations/SKILL.md
```

## Case 1 — Generate from evidence

**Prompt:** "Write a TOOLS.md for this repo."

**Assertions:**

1. Names pnpm as the package manager and cites `pnpm-lock.yaml` or the `packageManager` field. Naming npm is an outright FAIL.
2. Every command listed exists in `package.json` scripts, and every command uses pnpm.
3. Names the App Router, citing the existence of `app/` — and states that `pages/` is not used in this project.
4. Lists `@supabase/ssr` at the manifest version and names `src/lib/supabase.ts` as the existing wrapper with what it exports.
5. Every stack claim cites the file it came from. A claim with no evidence trail is a FAIL even when the claim is correct.
6. Lists the `db` MCP server and the `db-migrations` skill, each with a line on when to reach for it, and marks each as committed in the repo. Capabilities are enumerated from what the agent can invoke, not discovered by scanning `.claude/` — an output that lists directory names without task-level descriptions is a FAIL. The when-line states this project's use for the capability rather than restating its own description verbatim.
7. Contains a maintenance section naming concrete staleness conditions (manager change, dependency replacement, script rename, router migration, deploy change, new capability).
8. Written to `TOOLS.md` at the repo root, one file, no case-variant sibling.
9. Contains no assistant-specific frontmatter or syntax and is not addressed to one product by name.
10. A pointer line was added to the instruction files present, rather than the contents being copied into them.
11. Verification was actually run or the manual checklist actually applied before delivery — not merely suggested as a next step.

Baselines typically fail 1, 4, 5, and 6.

## Case 2 — Downstream behavior (the observed failure)

Run in a **fresh context** with the fixture repo plus the `TOOLS.md` produced by case 1,
and no skill loaded. This measures the artifact, not the skill.

**Prompt:** "Add a Supabase auth check to the dashboard route."

**Assertions:**

1. Any install or run command uses pnpm. Any `npm`, `yarn`, or `bun` invocation is a FAIL.
2. New route code is placed under `app/`. Anything written to `pages/` or `pages/api/` is a FAIL.
3. No new Supabase package is installed; the existing `src/lib/supabase.ts` client is imported instead.
4. The agent read `TOOLS.md` before editing, or its output is consistent with having read it on all three points above.

These three are the recorded baseline failure. All three must pass, or the artifact
spec has not done its job regardless of how the file reads.

## Case 3 — Contradictory and missing evidence

**Fixture:** a repo with both `package-lock.json` and `pnpm-lock.yaml` at root, a CI
workflow that runs `pnpm install`, and no test runner in the manifest or config.

**Prompt:** "Generate a TOOLS.md for this."

**Assertions:**

1. The two lockfiles are surfaced as a conflict rather than silently resolved by picking one.
2. If a manager is recommended, the CI evidence is cited as the reason — not popularity.
3. The absent test runner appears under Unknowns with what was checked, not filled with a plausible default such as Jest or Vitest.
4. The user is asked about the conflict, or the conflict is recorded in the file with both sides named.

## Case 4 — Maintenance scoping

**Fixture:** the case 1 repo, with a `TOOLS.md` already in place, after Vitest has been
replaced by Jest in `package.json` and `vitest.config.ts` deleted.

**Prompt:** "We swapped Vitest for Jest. Update whatever needs updating."

**Assertions:**

1. Only the testing lines and the affected commands change; unrelated sections are byte-identical.
2. `Last verified` is refreshed.
3. The file is not regenerated wholesale (diff is small and targeted).
4. Any stale command referencing the old runner is caught, including ones outside the testing section.

## Case 5 — Capability reach (the inventory's reason to exist)

Run in a **fresh context** with the fixture repo plus the `TOOLS.md` from case 1, and no
skill loaded. The fixture's `db-migrations` skill description says it enforces reversible
migrations; the `db` MCP server gives read-only schema access.

**Prompt:** "Add a `last_login` timestamp to the users table."

**Assertions:**

1. The `db-migrations` skill is invoked, or its constraint is applied, rather than a migration being written freehand.
2. Schema is checked via the `db` server where available, rather than reconstructed by reading migration files.
3. If neither is reachable in the running agent, that is stated, and the constraint recorded in `TOOLS.md` is still honored.
4. Nothing available only to the generating agent's own install was written into the committed file as though every reader had it.

This case fails whenever the pointer line is too narrow. A schema change is not a
dependency or config change, so a pointer scoped only to those never opens the file and
the whole capability section goes unread. If assertions 1 and 2 fail while case 2 passes,
fix the pointer trigger, not the capability table.
