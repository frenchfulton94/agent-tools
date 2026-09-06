# Plugin manifest reference

Contents:
- [Full schema](#full-schema)
- [Required and metadata fields](#required-and-metadata-fields)
- [Component path fields](#component-path-fields)
- [userConfig](#userconfig)
- [dependencies](#dependencies)
- [Per-component config files](#per-component-config-files)

## Full schema

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "plugin-name",
  "displayName": "Plugin Name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": { "name": "Author Name", "email": "author@example.com", "url": "https://github.com/author" },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "skills": "./custom/skills/",
  "commands": ["./custom/commands/special.md"],
  "agents": ["./custom/agents/reviewer.md"],
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "outputStyles": "./styles/",
  "lspServers": "./.lsp.json",
  "experimental": { "themes": "./themes/", "monitors": "./monitors.json" },
  "dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }]
}
```

## Required and metadata fields

| Field | Type | Notes |
|---|---|---|
| `name` | string | The only required field. Kebab-case, no spaces. Namespaces components as `plugin:component`. If the marketplace entry uses a different name, **the marketplace entry name is what `enabledPlugins` and `/plugin` key on.** |
| `$schema` | string | Ignored at load time; editor tooling only |
| `displayName` | string | v2.1.143+. UI only — never used for namespacing or lookup. Falls back to `name` |
| `version` | string | Optional semver. See versioning in SKILL.md |
| `description` | string | |
| `author` | object | `{name, email?, url?}` |
| `homepage`, `repository`, `license`, `keywords` | | `keywords` is an array — a string here is a load error |
| `defaultEnabled` | boolean | v2.1.154+. Default `true`; `false` installs the plugin disabled |

Unrecognized top-level fields are ignored, so one file can double as an npm `package.json` or an MCPB/DXT manifest. `claude plugin validate` reports them as warnings with did-you-mean suggestions; `--strict` promotes those warnings to errors.

`defaultEnabled` precedence, highest first: the user's own `enabledPlugins` entry in any scope (persists across updates and reinstalls) → a dependency requirement → the marketplace entry's `defaultEnabled` → the manifest's `defaultEnabled` → `true`.

## Component path fields

| Field | Type | Replace or add? |
|---|---|---|
| `skills` | string \| array | **Adds to** the default `skills/` scan |
| `commands` | string \| array | **Replaces** `commands/` |
| `agents` | string \| array | **Replaces** `agents/` |
| `workflows` | string \| array | **Replaces** `workflows/` |
| `outputStyles` | string \| array | **Replaces** `output-styles/` |
| `hooks` | string \| array \| object | Own merge rules |
| `mcpServers` | string \| array \| object | Own merge rules |
| `lspServers` | string \| array \| object | Own merge rules |
| `experimental.themes` | string \| array | **Replaces** |
| `experimental.monitors` | string \| array | **Replaces** |

All paths are relative to the plugin root and must start with `./`. Absolute paths fail with `Path errors → All paths must be relative and start with ./`.

To keep a default directory *and* add another for a replacing field, list both: `"commands": ["./commands/", "./extras/"]`.

One exception to the `skills` add-behavior: for a marketplace entry whose `source` resolves to the marketplace root, declaring specific subdirectories replaces the default scan instead of adding to it.

Since v2.1.140, `claude plugin list` and the `/plugin` detail view warn when a plugin has both a default folder and the matching manifest key — the manifest wins. No warning is emitted when the manifest key points inside the default folder.

## userConfig

Values prompted at enable time and substituted into configs.

```json
{
  "userConfig": {
    "api_endpoint": { "type": "string", "title": "API endpoint", "description": "Your team's API endpoint" },
    "api_token": { "type": "string", "title": "API token", "description": "API authentication token", "sensitive": true }
  }
}
```

Keys must be valid identifiers. Per-key fields: `type` (required — `string`, `number`, `boolean`, `directory`, `file`), `title` (required), `description` (required), plus optional `sensitive`, `required`, `default`, `multiple`, `min`, `max`.

Substitution is `${user_config.KEY}` in MCP and LSP configs and in hook commands; non-sensitive values also substitute in skill and agent content. Every value is exported to hook processes as `CLAUDE_PLUGIN_OPTION_<KEY>` with the key uppercased.

Since v2.1.207, `${user_config.KEY}` is **rejected with an error** rather than substituted in fields that execute a shell:

| Rejected in | Use instead |
|---|---|
| Shell-form hook commands | Exec form with `args`, or read `CLAUDE_PLUGIN_OPTION_<KEY>` |
| Monitor commands | Read from a config file |
| MCP `headersHelper` | Read from a config file |

Storage: non-sensitive values land in `pluginConfigs[<plugin-id>].options` in user settings; sensitive values go to the macOS Keychain or `~/.claude/.credentials.json`, which is shared with OAuth tokens and capped at roughly 2 KB total. `pluginConfigs` is read only from user settings, `--settings`, and managed settings — project and local settings entries are ignored (v2.1.207+), though `enabledPlugins` still honors them.

`channels` binds a message-injection channel to one of the plugin's own MCP servers; its `server` field must match a key in `mcpServers`.

## dependencies

```json
{ "dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }] }
```

Entries are a bare plugin name or `{name, version}`. Installing or enabling a plugin writes `true` into `enabledPlugins` for its dependencies. Cross-marketplace dependencies require the depended-on marketplace to list the dependent in `allowCrossMarketplaceDependenciesOn`.

## Per-component config files

**`hooks/hooks.json`** — an optional top-level `description`, then a `hooks` object identical in shape to the one in `settings.json`, so migrating is a straight copy:

```json
{
  "description": "Automatic code formatting",
  "hooks": {
    "PostToolUse": [
      { "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh", "timeout": 30 }] }
    ]
  }
}
```

A malformed `hooks/hooks.json` prevents the entire plugin from loading, not just its hooks.

**`.mcp.json`** — standard MCP server definitions. Plugin-bundled tools are exposed under a scoped name: plugin `my-plugin` + server key `db` + tool `query` becomes `mcp__plugin_my-plugin_db__query`. A hook matcher written against the bare server key never fires; use `mcp__plugin_my-plugin_db__.*`. An `mcp_tool` hook's `server` field takes `plugin:my-plugin:db`.

**`.lsp.json`** — keyed by language. `command` and `extensionToLanguage` required; optional `args`, `transport` (`stdio` default or `socket`), `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash` (default true), `maxRestarts`, `diagnostics` (default true). `restartOnCrash` and `shutdownTimeout` need v2.1.205+ — on older versions setting either silently skips the whole server. The first server registered for an extension wins.

**`monitors/monitors.json`** — an array of `{name, command, description}` with optional `when` (`"always"` default, or `"on-skill-invoke:<skill-name>"`). Every stdout line reaches Claude as a notification. Interactive CLI only. Disabling the plugin mid-session does not stop a running monitor, and monitors do not receive `CLAUDE_PLUGIN_OPTION_*` variables.

**`settings.json`** at the plugin root supports only `agent` and `subagentStatusLine`; unknown keys are silently ignored. It takes priority over a `settings` block in `plugin.json`.

**`themes/*.json`** — `{name, base, overrides}`, persisted as `custom:<plugin-name>:<slug>` and read-only.

**Plugin agent frontmatter** supports `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, and `isolation`. `hooks`, `mcpServers`, and `permissionMode` are ignored for plugin-shipped agents for security reasons. A same-named agent in `.claude/agents/` or `~/.claude/agents/` overrides the plugin's.
