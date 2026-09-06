# AI and extensions

This is the fastest-moving part of Zed's configuration — keys get added, renamed, and re-scoped between releases, and model lists change monthly. Treat everything here as shape, not as current values, and read the live pages before writing a config: AI overview `https://zed.dev/docs/ai/overview.md` · agent settings `https://zed.dev/docs/ai/agent-settings.md` · profiles `https://zed.dev/docs/ai/agent-profiles.md` · MCP `https://zed.dev/docs/ai/mcp.md` · tool permissions `https://zed.dev/docs/ai/tool-permissions.md` · providers `https://zed.dev/docs/ai/llm-providers.md` · edit prediction `https://zed.dev/docs/ai/edit-prediction.md` · instructions `https://zed.dev/docs/ai/instructions.md` · extensions `https://zed.dev/docs/extensions/installing-extensions.md`.

Contents:

- [Where AI settings live](#where-ai-settings-live)
- [MCP servers](#mcp-servers)
- [Agent profiles and tool permissions](#agent-profiles-and-tool-permissions)
- [Edit prediction](#edit-prediction)
- [Turning AI off](#turning-ai-off)
- [Extensions](#extensions)

## Where AI settings live

The Agent Panel's own settings UI (`agent: open settings`, or **Settings → AI**) writes to the same `settings.json` as everything else, so the UI is usually the faster and safer path — it produces correctly-shaped entries for the installed version. The relevant top-level keys are `agent` (panel placement, profiles, permissions), `language_models` (per-provider API URLs and options), `context_servers` (MCP), `edit_predictions` plus `features.edit_prediction_provider`, and `disable_ai`.

API keys are entered through the UI and stored outside `settings.json`; don't write credentials into the settings file.

## MCP servers

`context_servers` holds both local (spawned command) and remote (URL) servers:

```json
{
	"context_servers": {
		"local-server": { "command": "some-command", "args": ["--flag"], "env": {} },
		"remote-server": {
			"url": "https://example.com/mcp",
			"headers": { "Authorization": "Bearer <token>" }
		}
	}
}
```

A remote server with no `Authorization` header triggers Zed's OAuth flow instead. Many servers also ship as extensions, installable from `zed: extensions` or **Settings → AI → MCP Servers**, which is preferable when one exists — the extension carries its own setup prompts.

MCP servers defined in a project's `.zed/settings.json` are subject to worktree trust: they don't start until the worktree is trusted. Servers configured at the user level are unaffected.

## Agent profiles and tool permissions

A profile bundles a model choice with a set of enabled built-in and MCP tools, and `enable_all_context_servers: false` plus an explicit `context_servers` map is how to force the agent toward one server's tools:

```json
{
	"agent": {
		"profiles": {
			"focused": {
				"name": "Focused",
				"tools": { "edit_file": false, "terminal": false, "fetch": true },
				"enable_all_context_servers": false,
				"context_servers": { "my-server": { "tools": { "some_tool": true } } }
			}
		}
	}
}
```

Tool approval sits under `agent.tool_permissions.default` (`"confirm"`, `"allow"`, `"deny"`) in Zed v0.224 and later; older versions used the boolean `agent.always_allow_tool_actions`. Per-tool rules key MCP tools as `mcp:<server>:<tool_name>`. This area has already been renamed once — check the tool-permissions page against the user's version before writing it.

Persistent instructions for the agent are files, not settings: project `AGENTS.md` and the personal rules file described on the instructions page.

## Edit prediction

The provider is selected by `features.edit_prediction_provider` (Zed's own Zeta, Copilot, or none), while `edit_predictions` holds behavior: `mode` (`eager` shows predictions inline, `subtle` waits for a modifier) and `disabled_globs`, which _extends_ Zed's built-in list of secret-bearing paths rather than replacing it. `show_edit_predictions` toggles display globally or per language, and `edit_predictions_disabled_in` suppresses them inside given syntax scopes (`["comment", "string"]`).

## Turning AI off

`"disable_ai": true` switches off Zed's AI features wholesale. Narrower knobs exist — `agent.enabled`, `agent.button`, `features.edit_prediction_provider: "none"` — when the goal is only to hide the panel or stop inline predictions.

## Extensions

Install and manage from `zed: extensions` (`cmd-shift-x`) or the gallery at `https://zed.dev/extensions`. Two settings make the set reproducible across machines:

```json
{
	"auto_install_extensions": { "html": true, "dockerfile": true, "docker-compose": false },
	"auto_update_extensions": { "html": false }
}
```

`true` installs, `false` prevents installation, and an entry in `auto_update_extensions` set to `false` pins an extension at its installed version (which is also what "Install Another Version…" does). The ids are the directory names under the installed-extensions folder: `~/Library/Application Support/Zed/extensions/installed/` on macOS, `~/.local/share/zed/extensions/installed/` on Linux, `%LOCALAPPDATA%\Zed\extensions\installed\` on Windows. The sibling `work/` directory holds what extensions download at runtime and isn't config.

Writing an extension rather than configuring one is a separate topic: `https://zed.dev/docs/extensions/developing-extensions.md`.
