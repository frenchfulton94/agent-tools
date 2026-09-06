# Trigger Battery: debugging-type-errors

Run per `references/evaluation.md`: give a clean-context agent the descriptions for all three
sibling skills plus 2–3 unrelated distractors, one query at a time, and ask which applies or
"none". Sibling misroutes are the failures that matter.

## Should trigger (10)

1. `Argument of type '{ id: string; }' is not assignable to parameter of type 'User'` — no idea what it wants
2. This compiles in my editor but `tsc` fails in CI
3. Why is `bird` possibly undefined here, I literally just filtered the array
4. Getting `Type instantiation is excessively deep and possibly infinite` on this generic
5. After the upgrade I have 400 errors saying it can't find `process`
6. My output is going to `dist/src/index.js` instead of `dist/index.js`
7. The `if (typeof x === "object")` check isn't narrowing out null
8. Import works fine in dev, crashes with ERR_MODULE_NOT_FOUND in production
9. Why is TypeScript including this `.d.ts` file, I have it in `exclude`
10. It says the property doesn't exist but I can see it right there on the object

## Should not trigger (10)

Sibling misroutes — the valuable negatives:

1. What tsconfig should I use for a new React app? → `writing-typescript`
2. Should I use overloads or a union parameter here? → `writing-typescript`
3. Walk me through converting our JS codebase to TypeScript → `refactoring-typescript`
4. How do I roll out `strictNullChecks` across 200 files without a giant PR? → `refactoring-typescript`
5. Replace the `any` types in this module with something safer → `refactoring-typescript`

Near-misses from adjacent domains:

6. My Jest tests fail with a module resolution error (test runner config, not tsc)
7. Node throws `TypeError: undefined is not a function` at runtime (runtime error, no type error)
8. The build is slow, can you speed it up (performance, not a type error)
9. Why does this React component re-render twice (framework behavior)
10. Fix this failing unit test (test logic)

## Note on negatives 6 and 7

Both are runtime or tooling failures that _look_ like type errors in casual phrasing. If the
agent routes them here, the description is over-triggering on the word "error" — tighten it
toward "compiler error" and "tsc reports".
