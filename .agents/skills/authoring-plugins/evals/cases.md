# Behavior test cases: authoring-plugins

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Create a plugin (must-pass set)

**Prompt:** "Package our tooling into a plugin called `release-tools`. It should ship the release-notes skill we already have, a subagent that reviews changelogs, and a hook that blocks `git push --force` on main. We'll distribute it from an internal GitHub marketplace repo."

**Assertions:**
1. Every component directory (`skills/`, `agents/`, `hooks/`) is placed at the plugin root, and only `plugin.json` is inside `.claude-plugin/`.
2. `plugin.json` includes a kebab-case `name`, and any component path field it sets starts with `./`.
3. The hook's command references the bundled script through `${CLAUDE_PLUGIN_ROOT}` rather than a relative or absolute path. (Baselines commonly emit `./scripts/check.sh`, which works locally and breaks after install.)
4. The hook event name is correctly cased (`PreToolUse`, not `pretooluse` or `PreToolUSE`).
5. The subagent file does not use `hooks`, `mcpServers`, or `permissionMode`, or the response explicitly notes those are ignored for plugin-shipped agents.
6. A marketplace entry is produced with both `name` and `source`, and the `source` is a form that works for a git-hosted marketplace.
7. The response states how to test the plugin locally (`--plugin-dir` or equivalent) before publishing.
8. Mechanical validation was actually performed before delivery (`claude plugin validate`, or the bundled validator script run) — not merely suggested as a next step.
9. The response does not invent manifest fields; every key used appears in the documented schema.

## Case 2 — Audit a broken plugin

**Prompt:** "This plugin installs but Claude doesn't see the skill, and the formatting hook never runs. Can you figure out why?"
(Working directory: `fixtures/broken-plugin/`.)

**Assertions:**
1. Identifies that `skills/` is nested inside `.claude-plugin/` and names this as the reason the skill is missing.
2. Identifies the miscased `postToolUse` event as the reason the hook never fires, and notes that event names are case-sensitive.
3. Identifies at least two of: the absolute path in the `agents` field, `keywords` given as a string rather than an array, the hook command using a relative `./scripts/format.sh` path instead of `${CLAUDE_PLUGIN_ROOT}`, and `permissionMode` in the plugin-shipped agent being ignored.
4. Reports findings before proposing edits, rather than silently rewriting the tree.
5. Does not attribute the failures to a cause the fixture does not contain (for example, a missing `version`, or the plugin not being enabled).

## Case 3 — Edge: not a plugin problem

**Prompt:** "Make a plugin so Claude always runs our linter before it edits any file."

**Assertions:**
1. Response identifies that the enforcement mechanism is a hook and routes to hook authoring, rather than treating "plugin" as the substance of the request.
2. If a plugin wrapper is discussed at all, it is framed as packaging for distribution, not as what produces the enforcement.
3. Response stays proportionate — it does not scaffold a full marketplace and manifest set for what is one hook the user could put in `.claude/settings.json`.
