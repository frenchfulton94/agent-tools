# Trigger battery: authoring-hooks

## Should trigger (10)

1. "I want prettier to run automatically every time Claude writes a file."
2. "My hook runs but the tool call goes through anyway. Why isn't it blocking?"
3. "Claude keeps committing without running the tests, no matter how many times I tell it not to."
4. "Stop Claude from ever touching anything under `vendor/`."
5. "Can you review the hooks in my settings.json? Half of them might be dead."
6. "How do I get the current git branch into context at the start of every session?"
7. "my formatting hook fires on notebook edits too and i only wanted regular edits"
8. "The hook's additionalContext never shows up. The script runs fine when I test it by hand."
9. "Set something up that pings me when Claude needs permission."
10. "Which event do I use to check something right before a Bash command runs?"

## Should not trigger (10) — near-misses

1. "Add a git pre-commit hook that runs eslint." (git hook, unrelated to Claude Code)
2. "Set up a GitHub Actions workflow to run tests on PRs." (CI, different automation system)
3. "Write a React component with a useEffect hook." (React hooks, keyword collision)
4. "Add a webhook so our Slack channel gets deploy notifications." (webhook, different concept)
5. "Package my hooks and skills into a plugin for the team." (packaging → authoring-plugins)
6. "Write a skill that teaches Claude our code review process." (advisory workflow → authoring-skills)
7. "Give my code-reviewer subagent access to fewer tools." (agent tool grants → authoring-subagents)
8. "How do I deny Bash access entirely in this project?" (static permission rule, not a hook)
9. "Explain what happens between a tool call and its result." (docs question, no artifact to author)
10. "Trim my CLAUDE.md, it's grown to 400 lines." (project memory → managing-project-memory)
