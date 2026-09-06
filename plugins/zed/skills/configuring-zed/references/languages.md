# Languages, LSP, and formatting

Live docs: `https://zed.dev/docs/configuring-languages.md` · supported languages `https://zed.dev/docs/languages.md` · one page per language at `https://zed.dev/docs/languages/<name>.md` (rust, typescript, python, go, …) with that language's server names and options · settings catalog `https://zed.dev/docs/reference/all-settings.md`. Language-server options themselves belong to the server, not Zed — check the server's own docs for what goes inside `initialization_options` / `settings`.

Contents:

- [Per-language settings](#per-language-settings)
- [File associations](#file-associations)
- [Choosing language servers](#choosing-language-servers)
- [Configuring a language server](#configuring-a-language-server)
- [Formatters](#formatters)
- [Linting on save](#linting-on-save)
- [Highlighting and hints](#highlighting-and-hints)
- [When something doesn't apply](#when-something-doesnt-apply)

## Per-language settings

Keys under `languages` are language _display names_ as Zed shows them in the status bar — `"Python"`, `"JavaScript"`, `"Shell Script"`, `"C++"` — not file extensions or lowercase ids.

```json
{
	"languages": {
		"Python": { "tab_size": 4, "formatter": "language_server", "format_on_save": "on" },
		"Markdown": { "enable_language_server": false, "format_on_save": "off" }
	}
}
```

Only a subset of settings is language-scopable: indentation and wrapping (`tab_size`, `hard_tabs`, `soft_wrap`, `preferred_line_length`), save behavior (`format_on_save`, `formatter`, `ensure_final_newline_on_save`, `remove_trailing_whitespace_on_save`, `line_ending`), completions and prediction visibility, whitespace rendering, autoclose behavior, and the language-server toggles. The authoritative list is the `languages` section of the settings reference; anything outside it has to be set globally.

## File associations

`file_types` maps a language name to extensions, filenames, or globs:

```json
{ "file_types": { "C++": ["c"], "TOML": ["MyLockFile"], "Dockerfile": ["Dockerfile*"] } }
```

Zed's own defaults route `.zed/**/*.json` and `.vscode/**/*.json` to JSONC so comments parse; overriding `file_types` wholesale can undo that, so re-list the defaults if the goal is to add rather than replace.

For per-file overrides without touching settings, Zed reads a subset of Vim and Emacs modelines (`https://zed.dev/docs/modelines.md`).

## Choosing language servers

When several servers can serve one language, `language_servers` sets the order and disables the unwanted ones:

```json
{ "languages": { "PHP": { "language_servers": ["intelephense", "!phpactor", "..."] } } }
```

- Names listed plainly run, in the order given.
- `!name` disables that server.
- `"..."` expands to every remaining registered server at that position, so new extensions get picked up automatically. Omit it for a closed list.

The list replaces Zed's default entirely — including the `!`-prefixed entries in that default. A language whose default disables three servers will re-enable them under `["..."]` unless the `!` entries are repeated. Language pages show each default list.

## Configuring a language server

Two channels, and picking the wrong one means the setting is ignored:

- `initialization_options` — sent once at startup; changes need a server restart. rust-analyzer and clangd take configuration only this way.
- `settings` — queried at runtime by servers that support workspace configuration, which is most of them.

```json
{
	"lsp": {
		"rust-analyzer": { "initialization_options": { "check": { "command": "clippy" } } },
		"tailwindcss-language-server": { "settings": { "tailwindCSS": { "emmetCompletions": true } } }
	}
}
```

Options nest as objects. VS Code's dotted style (`"preferences.strictNullChecks": true`) is read as a key literally named `preferences.strictNullChecks` and does nothing — write `"preferences": { "strictNullChecks": true }`.

To point at a specific binary rather than the one Zed downloads:

```json
{
	"lsp": {
		"rust-analyzer": {
			"binary": {
				"ignore_system_version": false,
				"path": "/path/to/bin",
				"arguments": ["--flag"],
				"env": { "FOO": "BAR" }
			}
		}
	}
}
```

Zed stores servers it downloads under its data directory (`~/Library/Application Support/Zed/languages`, `~/.local/share/zed/languages`) and updates them itself. Servers that Zed looks up on `$PATH` — Go, Zig, C, TypeScript, and Rust when configured that way — resolve against the _project_ environment, which depends on how Zed was launched; see `https://zed.dev/docs/environment.md`.

Some languages need a selected toolchain (a Python virtualenv, for instance) before the server behaves: `toolchain: select`, documented at `https://zed.dev/docs/toolchains.md`.

## Formatters

`formatter` accepts several shapes, and an array runs them in sequence (a later failure doesn't cancel the earlier ones):

```json
{
	"formatter": "language_server",
	"formatter": {
		"external": { "command": "prettier", "arguments": ["--stdin-filepath", "{buffer_path}"] }
	},
	"formatter": [
		{ "code_action": "source.fixAll.eslint" },
		{ "language_server": { "name": "rust-analyzer" } }
	],
	"formatter": "none"
}
```

External formatters receive the buffer on stdin and must write to stdout; `{buffer_path}` exists so tools like Prettier can infer a parser, not so the formatter can read the file itself.

`format_on_save` takes `"on"`, `"off"`, `"modifications"` (only lines with unstaged changes, requires git plus LSP range formatting), and `"modifications_if_available"` (same, falling back to a full format). `"none"` on `formatter` still lets `code_actions_on_format` run.

## Linting on save

Linting comes from language servers. Configure the rules in `lsp`, and run fixes through a code-action formatter:

```json
{
	"languages": {
		"JavaScript": {
			"formatter": [
				{ "code_action": "source.fixAll.eslint" },
				{
					"external": { "command": "prettier", "arguments": ["--stdin-filepath", "{buffer_path}"] }
				}
			],
			"format_on_save": "on"
		}
	}
}
```

## Highlighting and hints

Syntax colors come from tree-sitter captures styled by the theme; override them per theme with `theme_overrides` (see `references/appearance.md`). `semantic_tokens` (`"off"`, `"combined"`, `"full"`) layers language-server tokens over or in place of tree-sitter and may need a server restart. `inlay_hints` is off by default and configurable globally or per language; several languages ship preconfigured hint options documented on their pages.

## When something doesn't apply

- The project's worktree is untrusted, so `.zed/settings.json` was never parsed and no server started.
- The setting isn't language-scopable and was written under `languages`.
- The option went into `initialization_options` without a restart, or into `settings` for a server that only reads init options.
- The language name doesn't match Zed's display name for that language.
- `zed: open log` shows server startup errors, missing binaries, and rejected configuration.
