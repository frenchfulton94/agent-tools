---
name: authoring-plugins
description: Creates, audits, and packages Claude Code plugins — plugin.json manifests, component directories, marketplace entries, and the local install-and-validate loop. Use when the user wants to build a plugin, review or clean up one they already have, bundle existing skills, agents, or hooks into one distributable unit, publish or host a marketplace, or fix a plugin whose components load partially or not at all or whose updates never reach users. Also use when the user asks why a skill, agent, or hook inside their plugin is not being picked up, how a bundled script should be referenced, or how to distribute agent tooling to a team. For authoring the individual components, prefer the dedicated skills for skills, hooks, and subagents.
license: MIT
---

# Authoring Plugins

A plugin is a directory of components — skills, subagents, hooks, MCP servers, commands — plus an optional `.claude-plugin/plugin.json` manifest, distributed through a marketplace. Most plugin problems are not manifest problems: the plugin loads fine and its components are silently absent because they sit in the wrong directory.

## Which component?

Decide this before scaffolding. A plugin is packaging; it does not change what each component can do.

| The user wants... | Ship a... |
|---|---|
| Repeated multi-step know-how the agent applies in the main conversation | Skill (`skills/<name>/SKILL.md`) |
| Something enforced every time, with no chance of being reasoned around | Hook (`hooks/hooks.json`) |
| Isolated work whose verbose output should stay out of the main context | Subagent (`agents/<name>.md`) |
| Access to an external system or API | MCP server (`.mcp.json`) |
| A one-off prompt the user invokes by name | Skill with `disable-model-invocation`, not a plugin |

For the components themselves, use `authoring-skills`, `authoring-hooks`, and `authoring-subagents`. This skill covers the wrapper around them.

## Layout

```text
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # the ONLY file that belongs in this directory
├── skills/<name>/SKILL.md
├── agents/<name>.md
├── commands/<name>.md
├── hooks/hooks.json
├── scripts/               # hook and utility scripts
├── .mcp.json
└── bin/                   # added to the Bash tool PATH while enabled
```

Every component directory sits at the plugin root. Putting `skills/` or `hooks/` inside `.claude-plugin/` produces the single most common symptom: the plugin installs and appears in `/plugin`, and none of its components exist. The manifest itself is optional — with no `plugin.json`, components auto-discover from these default locations and the name derives from the directory.

Two more layout constraints:

- An installed plugin cannot reference files outside its own directory. `../shared-utils` works in development and breaks after install, because marketplace plugins are copied into `~/.claude/plugins/cache`. Symlinks pointing outside the marketplace are skipped entirely on that copy.
- A `CLAUDE.md` at the plugin root is not loaded as project context. Ship instructions as a skill.

## Manifest essentials

`name` is the only required field. It must be kebab-case, and it is what namespaces components (`my-plugin:code-reviewer`).

Component path fields are the part that surprises people. `skills` **adds to** the default `skills/` scan; `commands`, `agents`, `workflows`, and `outputStyles` **replace** their default directory. To keep the default and add another location, list both: `"commands": ["./commands/", "./extras/"]`.

Every path must be relative and start with `./` — an absolute path is a load error. Unrecognized top-level fields are ignored (so one file can double as an npm or VS Code manifest), but a wrong *type* on a known field is a hard load error: `keywords` as a string rather than an array stops the plugin loading.

Read `references/manifest.md` when the manifest needs anything past `name`, `version`, `description`, and `author` — `userConfig`, `dependencies`, `defaultEnabled` precedence, or the per-component config files.

## Plugin roots and data

Three placeholders are substituted in hook commands, monitor commands, MCP and LSP server definitions, and skill and agent content:

| Placeholder | Points at |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | The plugin's install directory — bundled scripts, binaries, configs |
| `${CLAUDE_PLUGIN_DATA}` | A persistent directory that survives updates — caches, `node_modules`, venvs |
| `${CLAUDE_PROJECT_DIR}` | The project root |

`${CLAUDE_PLUGIN_ROOT}` changes on every plugin update, so nothing writable belongs there; that is what `${CLAUDE_PLUGIN_DATA}` is for. In shell-form hook commands wrap the placeholder in double quotes before appending a path; in exec form each argument is passed through literally and needs no quoting.

## Dev loop

```bash
claude --plugin-dir ./my-plugin          # load a local plugin for one session
claude plugin validate ./my-plugin --strict
```

A `--plugin-dir` plugin shadows an installed plugin of the same name for that session, which is how you test a change against real usage. Inside a session, `/reload-plugins` picks up edits to `hooks/`, `agents/`, `.mcp.json`, and `output-styles/` without a restart — its summary line counts only `commands/` entries, so "0 skills" does not mean your skill failed to reload. Skill file edits take effect immediately with no reload at all.

When the `claude` CLI is not available, run `bun scripts/validate_plugin.ts <plugin-dir> --strict` for the layout, manifest, and hooks checks that catch the failures above.

## Versioning

Version resolves from the first of: `version` in `plugin.json`, `version` in the marketplace entry, the git commit SHA, then `unknown`. Setting an explicit version pins the plugin — users get updates only when you bump it, and `/plugin update` reports "already at the latest version" until you do. Omitting it from both places means every new commit ships. `plugin.json` wins over the marketplace entry when they disagree.

Read `references/marketplace.md` when publishing: the `marketplace.json` schema, the five source types, strict mode, install scopes, and the `claude plugin` CLI surface.

## Auditing an existing plugin

Work through in order and report findings before editing anything. The order matters — layout faults explain most "component missing" reports, so ruling them out first avoids chasing manifest ghosts.

- [ ] `.claude-plugin/` contains `plugin.json` and nothing else; every component directory is at the plugin root
- [ ] `plugin.json` parses, `name` is kebab-case, and known fields have the right types
- [ ] Every component path field starts with `./`, resolves, and escapes nothing via `../`
- [ ] Replace-vs-add semantics are intended: a `commands` or `agents` key silently replaces the default directory
- [ ] Bundled scripts, MCP servers, and hooks reference `${CLAUDE_PLUGIN_ROOT}` rather than a relative or absolute path, and write state to `${CLAUDE_PLUGIN_DATA}`
- [ ] `hooks/hooks.json` parses — a malformed one stops the whole plugin from loading — with correctly cased event names
- [ ] Plugin agents avoid `hooks`, `mcpServers`, and `permissionMode`, which are ignored when an agent loads from a plugin
- [ ] MCP matchers and `mcp_tool` hook `server` fields use the scoped plugin names, not the bare server key
- [ ] The manifest version and the marketplace entry version agree, and the version was bumped if behavior changed
- [ ] Components actually load: `claude --plugin-dir ./my-plugin --debug` and confirm each one registers
- [ ] Deletion pass, last: component directories and manifest keys that no longer carry anything

Read `references/troubleshooting.md` when a symptom survives this list — it maps the documented error strings back to causes.

## Verify

Before reporting done: the validator runs clean, the plugin loads under `--plugin-dir`, and each component appears where it should (a skill in the skill list, an agent in `@`-mention typeahead as `my-plugin:<agent>`, a hook in `/hooks`). Claim only what you observed.

## Output contract

- **Creating:** the full file tree with every file's content, plus one line on why each component is the shape it is (skill vs. hook vs. agent).
- **Auditing:** findings keyed to the checklist above first, then the proposed diffs, each with a one-line why. If the plugin is sound, say so and stop — do not invent findings.

## Related skills

- `authoring-skills` — for the `SKILL.md` files a plugin bundles. This skill is self-contained without it.
- `authoring-hooks` — for the contents of `hooks/hooks.json`. Self-contained without it.
- `authoring-subagents` — for the contents of `agents/*.md`. Self-contained without it.
