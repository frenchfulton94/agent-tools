# Trigger Battery

Run each query into a clean-context agent that has this skill's `description` (and no body) available. Record whether the skill loads. Pass = all should-trigger load, all should-not don't.

## Should trigger

1. "Set up Biome in this repo."
2. "Add linting and formatting to my TypeScript project — I want one tool, not five."
3. "Write me a biome.json for a Next.js monorepo."
4. "We're on ESLint + Prettier. How do I switch?"
5. "Biome isn't picking up my ignore rules, everything in dist/ is getting linted."
6. "I upgraded Biome and now half my config does nothing."
7. "How do I get format-on-save working with Biome in VS Code?"
8. "Add a CI job that fails the build on unformatted code." _(no tool named — the setup task is the trigger)_
9. "Can you review our biome.json?"
10. "Make our pre-commit hook format staged files."

## Should not trigger (near misses)

1. "Format this file for me." — a single run, not a setup task.
2. "What's the difference between a linter and a formatter?" — conceptual.
3. "Write an ESLint rule that bans default exports." — authoring rules for a different tool.
4. "Why is `noFloatingPromises` flagging this function?" — a rule's semantics, not configuration.
5. "Set up Vitest in this project." — adjacent tooling setup, wrong tool.
6. "Configure Prettier to use 4-space indentation." — Prettier, and no migration asked for.
7. "Our tsconfig paths aren't resolving." — different config file.
8. "Add a GitHub Actions workflow that runs our tests." — CI setup, nothing to do with Biome.
9. "What does `biome check --write` do?" — a CLI question answerable directly.
10. "Rename this package in package.json." — touches a config file, unrelated task.

## Known ambiguity

Query 8 ("CI job that fails on unformatted code") should trigger only if the repo already uses Biome or the user has said so. In a repo using Prettier it's a false positive. Accept the miss rather than narrowing the description — the cost of loading the skill and routing away is lower than the cost of not loading it in a Biome repo.
