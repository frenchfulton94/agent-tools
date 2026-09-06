# Marketplace and distribution reference

Contents:
- [marketplace.json top level](#marketplacejson-top-level)
- [Plugin entries](#plugin-entries)
- [Source types](#source-types)
- [Strict mode](#strict-mode)
- [CLI surface](#cli-surface)
- [Team distribution](#team-distribution)

## marketplace.json top level

Lives at `.claude-plugin/marketplace.json` in the marketplace repository.

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team", "email": "devtools@example.com" },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting on save",
      "version": "2.1.0"
    },
    {
      "name": "deployment-tools",
      "source": { "source": "github", "repo": "company/deploy-plugin" },
      "description": "Deployment automation tools"
    }
  ]
}
```

Required: `name` (kebab-case, public-facing — one marketplace per name per user, so re-adding replaces), `owner` (`name` required, `email` and `url` optional), and `plugins`.

Optional: `$schema`, `description`, `version`, `metadata.pluginRoot` (a base directory prepended to relative plugin sources), `allowCrossMarketplaceDependenciesOn`, and `renames` (v2.1.193+, mapping an old plugin name to a new one, or to `null` when removed). `description` and `version` are also accepted under `metadata` for backward compatibility.

A set of marketplace names is reserved for first-party use and rejected for third parties — anything in the `claude-*`, `anthropic-*`, `agent-skills`, or first-party vertical families (`life-sciences`, `healthcare`, `claude-for-legal`, and similar), plus impersonating variants like `official-claude-plugins`. The check runs on every load, not only when the marketplace is added, so a rename does not grandfather in.

## Plugin entries

Required per entry: `name` (kebab-case) and `source`.

An entry may carry **any field from the plugin manifest schema**, plus the marketplace-only fields `source`, `category`, `tags`, `strict`, and `relevance` (v2.1.152+, honored only for admin-allowlisted marketplaces). `defaultEnabled` on an entry takes precedence over the value in `plugin.json`.

Component config fields (`skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`) are also valid on an entry — see strict mode below for how they interact with `plugin.json`.

## Source types

| Source | Shape | Fields | Notes |
|---|---|---|---|
| Relative path | string, `"./my-plugin"` | — | Must start with `./`. Resolved from the **marketplace root**, not `.claude-plugin/`. No `../` |
| `github` | object | `repo`, `ref?`, `sha?` | `repo` is `owner/repo` |
| `url` | object | `url`, `ref?`, `sha?` | Any git URL; `.git` suffix optional |
| `git-subdir` | object | `url`, `path`, `ref?`, `sha?` | Sparse partial clone; `url` accepts `owner/repo` shorthand or SSH |
| `npm` | object | `package`, `version?`, `registry?` | Installed via npm |

When both `ref` and `sha` are present, `sha` is the effective pin.

```json
{ "name": "github-plugin", "source": { "source": "github", "repo": "owner/plugin-repo", "ref": "v2.0.0" } }
```
```json
{ "name": "my-plugin", "source": { "source": "git-subdir", "url": "https://github.com/acme/monorepo.git", "path": "tools/claude-plugin" } }
```

Two distinctions worth holding onto:

- **Marketplace source and plugin source are different things.** The marketplace source (where `marketplace.json` itself lives, set by `claude plugin marketplace add`) supports `ref` but not `sha`. A plugin entry's source supports both.
- **Relative paths break in URL-hosted marketplaces.** Adding `https://example.com/marketplace.json` downloads only that one file, so relative sources fail with "path not found". Host the marketplace as a git repository, or use github/git/npm sources for its entries.

## Strict mode

| `strict` | Behavior |
|---|---|
| `true` (default) | `plugin.json` is authoritative; the marketplace entry supplements it and the two are merged |
| `false` | The marketplace entry is the entire definition. If the plugin also ships a `plugin.json` that declares components, the plugin **fails to load** |

The conflict surfaces as: `Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.`

## CLI surface

```bash
claude plugin init <name> [--with skills agents hooks mcp lsp output-style channel]
claude plugin install <plugin@marketplace> [-s user|project|local] [--config key=value]
claude plugin uninstall <plugin> [--keep-data] [--prune]
claude plugin enable|disable <plugin> [-s <scope>]
claude plugin update <plugin>
claude plugin list [--json] [--available]
claude plugin details <name>
claude plugin validate ./my-plugin [--strict]
claude plugin marketplace add <source> [--scope <scope>] [--sparse <paths...>]
claude plugin marketplace list|remove|update [name]
```

Notes that bite:

- `claude plugin init` scaffolds into `~/.claude/skills/<name>/` and loads next session as `<name>@skills-dir` with no marketplace or install step.
- `marketplace remove <name>` takes the `name` from `marketplace.json`, not the source string passed to `add`. Removing the last scope uninstalls the plugins that came from it.
- A marketplace URL must include its scheme — since v2.1.196 a bare `gitlab.example.com/team/plugins` is rejected as invalid shorthand. Pin with `@ref` for GitHub shorthand and `#ref` for git URLs.
- Install scopes map to `~/.claude/settings.json` (user, the default), `.claude/settings.json` (project), `.claude/settings.local.json` (local), and managed settings (read-only).

`claude plugin validate` run against a marketplace directory also checks the marketplace schema, duplicate plugin names, and source path traversal; for local-path entries it validates that plugin's own `plugin.json` and warns when the entry version differs from the manifest version. Per-entry problems are prefixed `plugins[2] plugin.json →`.

## Team distribution

Commit these to the project's `.claude/settings.json` so a clone gets the tooling automatically:

```json
{
  "extraKnownMarketplaces": {
    "company-tools": { "source": { "source": "github", "repo": "your-org/claude-plugins" } }
  },
  "enabledPlugins": {
    "code-formatter@company-tools": true,
    "deployment-tools@company-tools": true
  }
}
```

Administrators can constrain this through managed settings: `strictKnownMarketplaces` (undefined means no restriction, `[]` is a full lockdown, a list is an exact allowlist), `disableSideloadFlags` to reject `--plugin-dir` and `--plugin-url`, `blockedMarketplaces` (which accepts `{"source": "skills-dir"}` to block `plugin init`), and `pluginSuggestionMarketplaces` to allowlist contextual suggestions.

For containers, `CLAUDE_CODE_PLUGIN_SEED_DIR` seeds a read-only mirror of `~/.claude/plugins`. Seeded entries take precedence, and `remove` or `update` against a seed-managed marketplace fails.
