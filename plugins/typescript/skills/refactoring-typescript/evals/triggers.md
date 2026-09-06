# Trigger Battery: refactoring-typescript

Run per `references/evaluation.md`: give a clean-context agent the descriptions for all three
sibling skills plus 2–3 unrelated distractors, one query at a time, and ask which applies or
"none". Sibling misroutes are the failures that matter.

## Should trigger (10)

1. We have a big JS codebase and management wants it on TypeScript
2. Can you make this file stricter without breaking anything downstream
3. There are 60 `@ts-ignore` comments in here, help me work through them
4. How do I turn on `strictNullChecks` without a 3000-line PR
5. This function takes `any` and returns `any`, can we do better
6. We're on TypeScript 5.2, what's involved in getting to 6.0
7. I want to add a variant to this union without breaking every consumer
8. Is it safe to change this parameter type in a published package
9. These `!` assertions everywhere make me nervous
10. Half our files are `.js` and half are `.ts` and it's a mess

## Should not trigger (10)

Sibling misroutes — the valuable negatives:

1. Starting a new TypeScript project from scratch → `writing-typescript`
2. What's the right `module` setting for a library → `writing-typescript`
3. Explain this specific error message → `debugging-type-errors`
4. Why did narrowing stop working after the assignment → `debugging-type-errors`
5. `tsc --explainFiles` output is confusing, what am I looking at → `debugging-type-errors`

Near-misses from adjacent domains:

6. Refactor this function to be more readable (code structure, no type change)
7. Extract this component into its own file (organization, not typing)
8. Rename this variable everywhere (mechanical edit)
9. Migrate our database from MySQL to Postgres (different migration entirely)
10. Convert this class component to hooks (framework migration, not JS→TS)

## Note on negatives 6 and 10

Both use "refactor" and "convert" without any typing dimension. If the agent routes them
here, the description is triggering on the verb rather than on type-level content — add a
qualifier tying it to types specifically.
