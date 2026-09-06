# Trigger battery: mapping-project-tooling

Run per `references/evaluation.md` in the `authoring-skills` package: give a
clean-context agent the descriptions only, for this skill plus distractors
(`managing-project-memory`, `authoring-skills`, `authoring-hooks`), one query at a
time, and ask which applies or "none". Score positives and negatives separately.

## Should trigger (10)

1. "Set up a tools.md for this repo so Cursor stops guessing our stack."
2. "Claude keeps running `npm install` but we're a pnpm shop. How do I stop that for good?"
3. "Every session I re-explain our stack before the agent can do anything useful."
4. "The agent just installed a second date library when we already have date-fns."
5. "We moved to the App Router months ago and agents still write to `pages/api`."
6. "Generate a TOOLS.md from the repo — don't ask me questions, read the lockfile."
7. "Our TOOLS.md says Vitest but we moved to Jest in March. Fix it and stop it recurring."
8. "I want one project context file that works for Claude Code, Codex, and Cursor."
9. "we just swapped bun for pnpm, what else needs updating"
10. "audit the stack map at the root of this repo, half of it looks wrong now"

Numbers 2, 3, 4, 5, and 9 are the load-bearing positives: the user never names the
file. If those miss, the description is too artifact-focused and too symptom-thin.

## Should not trigger (10) — near-misses

1. "My CLAUDE.md is 400 lines, help me trim it." (project memory → `managing-project-memory`)
2. "Write a README for this project." (human-facing docs)
3. "Add a pre-commit hook that runs the linter." (→ `authoring-hooks`)
4. "Make me a skill for generating release notes from merged PRs." (→ `authoring-skills`)
5. "Audit our dependencies for CVEs." (security scanning, not context mapping)
6. "What's the difference between the App Router and the Pages Router?" (explanation)
7. "Should I use pnpm or bun for a new project?" (greenfield; no repo evidence exists)
8. "Write usage docs for our internal CLI so new engineers know the flags." (docs for humans)
9. "Set up an MCP server for our Postgres database." (configuring a tool, not inventorying one)
10. "Bump lodash from 4.17.20 to 4.17.21." (patch bump — deliberately not a staleness trigger)

Number 10 is the sharp boundary: the skill's maintenance trigger is major-version or
replacement changes, so a patch bump firing this skill means the description's
maintenance clause is too broad. Number 7 is the other sharp one — same vocabulary,
but nothing to read.
