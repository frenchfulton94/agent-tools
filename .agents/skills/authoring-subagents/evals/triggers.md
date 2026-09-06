# Trigger battery: authoring-subagents

## Should trigger (10)

1. "Set up an agent that reviews our migrations before we deploy."
2. "Claude never uses my code-reviewer agent unless I name it explicitly. Why?"
3. "I want the test suite run somewhere that doesn't dump 4000 lines into my session."
4. "Make an agent that can read the codebase but can't write to it."
5. "Can you look over the agents in `.claude/agents/` and tell me which ones are worth keeping?"
6. "My agent errors out saying it would be spawned with zero tools."
7. "the mcpServers block in my plugin's agent just doesn't do anything"
8. "Should this be a subagent or a skill? It's a checklist we run before every release."
9. "Give my researcher agent access to the Playwright MCP server but nothing else."
10. "My reviewer agent runs fine but comes back with two vague sentences every time."

## Should not trigger (10) — near-misses

1. "Write a skill that teaches Claude our release checklist." (main-context workflow → authoring-skills)
2. "Bundle these agents into a plugin so the team gets them." (packaging → authoring-plugins)
3. "Add a hook that blocks edits to vendored files." (enforcement → authoring-hooks)
4. "Improve the system prompt for our customer support bot." (prompt work, not a Claude Code subagent → improving-prompts)
5. "Build me a LangChain agent that queries our warehouse." (different agent framework)
6. "How do I use the Explore agent to search this repo?" (using a built-in, not authoring one)
7. "Set up an MCP server for our internal API." (MCP server authoring)
8. "Spawn three agents to research this in parallel right now." (a dispatch request, not an authoring one)
9. "What's the token cost of running subagents?" (docs question, no artifact to author)
10. "My CLAUDE.md is 400 lines and half of it is stale." (project memory → managing-project-memory)
