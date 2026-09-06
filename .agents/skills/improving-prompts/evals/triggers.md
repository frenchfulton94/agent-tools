# Trigger battery: improving-prompts

## Should trigger (10)

1. "Can you make this system prompt better? [pasted prompt]"
2. "My support agent keeps escalating tickets it should handle itself — here are its instructions."
3. "This prompt worked great on the old model but the outputs got weird after we upgraded."
4. "Review my summarization prompt — the summaries are too generic."
5. "The model ignores the part where I tell it to answer in French. Why?"
6. "Tighten this up, it's 400 lines of instructions and half get ignored: [prompt]"
7. "My slash command's output is way too chatty, how do I fix the instructions?"
8. "Claude keeps refactoring code when I only asked it to fix the bug. Here's my agent config."
9. "Draft me a really solid prompt for extracting invoice fields into JSON — this one's going into production."
10. "why does the model make up citations when i ask it to cite sources?? my prompt literally says be accurate"

## Should not trigger (10) — near-misses

1. "Audit this SKILL.md for our team." (Agent Skill → authoring-skills)
2. "My CLAUDE.md keeps getting ignored, fix it." (project memory → managing-project-memory)
3. "What's the best model to use for coding?" (model selection, no prompt artifact)
4. "Write me a prompt injection payload to test my app's defenses." (security testing, different task)
5. "Improve this blog post about prompt engineering." (editing prose about prompts, not a prompt)
6. "What does temperature do in the API?" (API docs question)
7. "Summarize this paper on chain-of-thought prompting." (reading task with prompt keywords)
8. "Set up a subagent that reviews PRs." (agent architecture, not prompt rewriting — acceptable either way but prefer none)
9. "Why is my API call returning a 400 error?" (debugging, likely config not prompt)
10. "Translate this prompt into Spanish for our LatAm team." (translation, not improvement)
