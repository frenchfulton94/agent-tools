# Behavior test cases: authoring-subagents

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Create a subagent (must-pass set)

**Prompt:** "Make an agent that reviews our SQL migrations before we ship them. It should catch destructive operations and missing rollbacks. It must not be able to change any files — reading only. We ship it in our internal plugin."

**Assertions:**
1. Output is a complete markdown file with YAML frontmatter containing `name` and `description`.
2. `name` is lowercase with hyphens only.
3. The description states *when to delegate* rather than what the agent is, and includes proactive phrasing such as "use proactively" or "use immediately after". (Baselines reliably fail this: they write a title-style description, which is the top cause of an agent that is never invoked.)
4. `tools` grants read-only access using canonical names (`Read`, `Grep`, `Glob`) and does not include `Edit`, `Write`, or `NotebookEdit`.
5. Because the agent ships in a plugin, the response does not use `hooks`, `mcpServers`, or `permissionMode` — or it explicitly notes those are dropped for plugin-shipped agents.
6. The body is written to stand alone: it does not reference the conversation, files "we discussed", or prior context.
7. The body states what the agent returns and in what shape, since the caller sees only its final message.
8. The response says where the file goes (`<plugin>/agents/`), not just what it contains.
9. Mechanical validation was actually performed before delivery (the validator script run, or the frontmatter checked field by field) — not merely suggested.

## Case 2 — Audit a broken subagent

**Prompt:** "This agent barely works. Claude almost never picks it, and when it does the answers are useless. Can you tell me what's wrong?"
(File: `fixtures/broken-agent.md`.)

**Assertions:**
1. Identifies that the description describes the agent rather than stating when to delegate, and connects that to it never being picked.
2. Identifies that the body is too thin and references conversation context the subagent never receives, and connects that to the useless answers.
3. Identifies at least three of the mechanical faults: `name` is not lowercase-hyphenated, `model: gpt-4` is not a valid value, `permissionMode: yolo` is not a valid mode, `memory: shared` is not a valid scope, `bash` is miscased, and `AskUserQuestion` is removed from every subagent.
4. Notes that `LSP` is dropped when the agent runs in the background, which is the default.
5. Reports findings before rewriting, and does not claim a fault the fixture does not contain.

## Case 3 — Edge: a subagent is the wrong shape

**Prompt:** "I want a subagent that walks me through our incident response process step by step, asking me questions as it goes."

**Assertions:**
1. Response identifies that a subagent cannot ask the user questions — `AskUserQuestion` is removed from every subagent — and that its results return to Claude rather than to the user.
2. Recommends a skill (which runs in the main conversation and can interact) rather than delivering a subagent that would silently fail at the interactive part.
3. Response stays proportionate and does not scaffold a full agent file for a shape it just advised against.
