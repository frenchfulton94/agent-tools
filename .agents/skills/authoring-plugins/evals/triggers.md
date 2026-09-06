# Trigger battery: authoring-plugins

## Should trigger (10)

1. "I've got four skills in a folder — how do I package these so my team can install them?"
2. "My plugin installs fine but none of the skills show up. What's wrong?"
3. "Build me a plugin that bundles our deploy skill and a pre-commit hook."
4. "Can you review my plugin.json? Something about the paths feels wrong."
5. "How do I set up a marketplace repo so people can add it with one command?"
6. "The agent in my plugin ignores the permissionMode I set on it."
7. "Nobody's getting my plugin update even though I pushed the change."
8. "audit this plugin dir for me, it's grown messy and i think half the manifest keys are dead"
9. "What's the right way to reference a bundled script from a hook in my plugin?"
10. "Should this be one plugin with five skills or five separate plugins?"

## Should not trigger (10) — near-misses

1. "Write a skill for generating release notes." (single skill, no packaging → authoring-skills)
2. "My hook fires but doesn't block the tool call." (hook behavior, no plugin involved → authoring-hooks)
3. "Create a code-reviewer subagent for this repo." (single agent in .claude/agents/ → authoring-subagents)
4. "Add a git pre-commit hook that runs eslint." (plain git hook, unrelated to Claude Code)
5. "Install the PostHog plugin for me." (installing an existing plugin, not authoring one)
6. "Set up an MCP server for our internal API." (MCP server authoring, not plugin packaging)
7. "How do I publish this package to npm?" (npm publishing, different distribution system)
8. "Write a VS Code extension that formats our config files." (different editor's plugin system)
9. "What plugins are available in the official marketplace?" (discovery question, no artifact to author)
10. "Trim my CLAUDE.md, it's gotten enormous." (project memory → managing-project-memory)
