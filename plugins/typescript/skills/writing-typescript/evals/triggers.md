# Trigger Battery: writing-typescript

Run per `references/evaluation.md`: give a clean-context agent the descriptions for all three
sibling skills (`writing-typescript`, `debugging-type-errors`, `refactoring-typescript`) plus
2–3 unrelated distractors, one query at a time, and ask which applies or "none". Score
positives and negatives separately. The sibling misroutes are the failures that matter — this
battery weights them heavily.

## Should trigger (10)

1. Set up a new Node service in TypeScript, I want the config to be reasonable
2. What should go in my tsconfig for a library I'm publishing to npm?
3. Is `interface` or `type` better here, and does it matter for the public API?
4. I have five overloads for this function and it's getting silly
5. Writing a new package that has to work in both Vite and Node — how do I configure that?
6. Starting a fresh TS project, what strictness options do you recommend?
7. Should this be an enum or a union of string literals?
8. Building a routes table that I also need to read specific keys back from
9. My tsconfig has `"moduleResolution": "node"` — is that still right?
10. Adding a new module to our monorepo, need it to type-check the same way as the others

## Should not trigger (10)

Sibling misroutes — the valuable negatives:

1. `tsc` says `Type 'string' is not assignable to type 'number'` and I can't see why → `debugging-type-errors`
2. Narrowing works before the `.map()` and not inside it → `debugging-type-errors`
3. We're on 5.4 and want to get to 6.0 without breaking the build → `refactoring-typescript`
4. Convert this `.js` file to TypeScript → `refactoring-typescript`
5. Help me get rid of the `any` in this file → `refactoring-typescript`
6. Everything broke after I turned on `strict` → `debugging-type-errors` (diagnose) or `refactoring-typescript` (stage it)

Near-misses from adjacent domains:

7. Set up ESLint and Prettier for this repo (tooling config, not TS type config)
8. What's the difference between `npm ci` and `npm install`?
9. Write a debounce function (plain implementation request; no TS design decision)
10. Our Vite build is slow (bundler performance, not compiler configuration)

## Known ambiguity

Query 6 in the negatives is genuinely shared between siblings. Count it correct if the agent
picks either `debugging-type-errors` or `refactoring-typescript`; count it wrong only if it
picks `writing-typescript`.
