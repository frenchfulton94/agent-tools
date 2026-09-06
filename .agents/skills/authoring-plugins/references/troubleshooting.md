# Plugin troubleshooting reference

Contents:
- [Symptom table](#symptom-table)
- [Verbatim error strings](#verbatim-error-strings)
- [Debugging](#debugging)
- [Cache, updates, and symlinks](#cache-updates-and-symlinks)

## Symptom table

| Symptom | Likely cause | Check |
|---|---|---|
| Plugin appears in `/plugin` but has no skills, agents, or hooks | Component directories nested inside `.claude-plugin/` | Only `plugin.json` belongs there; everything else at plugin root |
| Plugin does not load at all | Invalid `plugin.json`, or a malformed `hooks/hooks.json` | `claude plugin validate ./my-plugin` |
| Skills missing but commands present | A `commands` or `agents` manifest key replaced the default directory | Component path fields replace, except `skills` which adds |
| Hooks never fire | Script not executable, or event name miscased | `chmod +x`, and check `PostToolUse` not `postToolUse` — names are case-sensitive |
| MCP server fails to start after install | Relative or absolute path instead of `${CLAUDE_PLUGIN_ROOT}` | Every bundled path goes through the placeholder |
| MCP hook matcher never matches | Bare server key used instead of the scoped plugin name | `mcp__plugin_<plugin>_<server>__.*` |
| Works locally, breaks after install | A path escaping the plugin directory (`../shared`) | Installed plugins are copied to the cache and cannot reach outside themselves |
| Agent frontmatter silently ignored | `hooks`, `mcpServers`, or `permissionMode` in a plugin-shipped agent | Those three are dropped for plugin agents; copy the agent to `.claude/agents/` if you need them |
| `/plugin update` says "already at the latest version" | An explicit `version` in `plugin.json` that was not bumped | Bump it, or omit `version` entirely to track commits |
| Users never receive an update | Same as above | |
| LSP server silently skipped | `restartOnCrash` or `shutdownTimeout` set on a version below v2.1.205 | Remove the field or raise the version floor |
| Single-skill plugin invoked under a version-string name | No frontmatter `name` in the root `SKILL.md` | Marketplace installs use a version-string directory that changes on every update — always set `name` |

## Verbatim error strings

These appear in the terminal or in `claude --debug` output. Matching on them is faster than reasoning from symptoms.

```text
Invalid JSON syntax: Unexpected token } in JSON at position 142
Plugin <name> has an invalid manifest file at .claude-plugin/plugin.json.
  Validation errors: name: Invalid input: expected string, received undefined
Plugin <name> has a corrupt manifest file at .claude-plugin/plugin.json. JSON parse error: ...
Warning: No commands found in plugin my-plugin custom directory: ./cmds.
  Expected .md files or SKILL.md in subdirectories.
Plugin directory not found at path: ./plugins/my-plugin.
  Check that the marketplace entry has the correct path.
Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.
```

Marketplace-level errors:

```text
File not found: .claude-plugin/marketplace.json
Duplicate plugin name "x" found in marketplace
plugins[0].source: Path contains ".."
YAML frontmatter failed to parse: ...
```

Warnings (these still pass validation without `--strict`): `Marketplace has no plugins defined`, `No marketplace description provided`, and `Plugin name "x" is not kebab-case`. The last one matters more than it reads — Claude Code accepts non-kebab-case names, but claude.ai marketplace sync rejects them.

## Debugging

```bash
claude --debug                      # logs to ~/.claude/debug/<session-id>.txt
claude --debug-file /tmp/claude.log # then tail -f /tmp/claude.log
```

`--debug` covers plugin loading, manifest errors, skill/agent/hook registration, and MCP initialization. `/debug` turns it on mid-session and prints the log path.

Inside a session, `/plugin` has an **Errors** tab that collects load failures — a `--plugin-url` fetch that fails starts the session without the plugin and records the reason there rather than aborting.

`/hooks` is a read-only browser of every registered hook, grouped by event, labeled by source (`User`, `Project`, `Local`, `Plugin`, `Session`, `Built-in`). It is the fastest confirmation that a plugin's hooks registered at all.

Version-floor checks are worth doing early when behavior contradicts the docs: several plugin behaviors changed across v2.1.x, including boolean frontmatter accepting `yes`/`no`/`on`/`off` (v2.1.218+, `true`/`false` only before), single-skill plugin auto-loading (v2.1.142+), and `displayName` (v2.1.143+).

## Cache, updates, and symlinks

Marketplace plugins are copied into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Consequences worth designing around:

- `${CLAUDE_PLUGIN_ROOT}` changes on every update. The previous version's directory lingers roughly 14 days before cleanup. Never write state there — use `${CLAUDE_PLUGIN_DATA}`, which resolves to `~/.claude/plugins/data/{id}/` where `{id}` is the plugin identifier with any character outside `a-zA-Z0-9_-` replaced by `-`. It is deleted on uninstall from the last scope unless `--keep-data` is passed.
- When a plugin updates mid-session, hooks, monitors, MCP, and LSP keep pointing at the old path. `/reload-plugins` switches hooks, MCP, and LSP; monitors need a full session restart.
- Symlinks on the cache copy: a target inside the plugin directory is preserved as a relative symlink, a target elsewhere in the same marketplace is dereferenced and its content copied, and a target outside the marketplace is skipped for security. With `--plugin-dir` and other local installs, only within-plugin symlinks survive.

A dependency-installation pattern that survives updates, using both placeholders:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command",
        "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\"" }] }
    ]
  }
}
```

On Windows PowerShell, Claude Code rewrites `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, and `${CLAUDE_PLUGIN_DATA}` to `${env:NAME}` in shell-form commands as of v2.1.198 — inside double-quoted strings, not single-quoted ones. A bare `$CLAUDE_PROJECT_DIR` in PowerShell resolves to `$null`.
