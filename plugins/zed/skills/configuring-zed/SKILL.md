---
name: configuring-zed
description: Configures and customizes the Zed editor — settings.json, keymap.json, themes and fonts, per-language and LSP options, formatters, tasks, snippets, installing extensions, and AI/agent config. Use when the user wants to change Zed's behavior or appearance, asks where a Zed config file lives or why an edit had no effect, shares a Zed config to debug or extend, or moves a VS Code, Vim, or JetBrains setup into Zed — including when they only say "my editor" and the project has a .zed/ directory.
license: MIT
---

# Configuring Zed

Zed is configured through a few JSONC files: `settings.json`, `keymap.json`, `tasks.json`, snippet files, and project-local `.zed/` overrides. Zed adds and renames settings almost every release, so this skill covers what stays stable — which file, what shape, how layers merge, what fails silently — and routes to the live docs for the values themselves. Writing an extension, building Zed from source, and using Zed's agent to do work are different jobs; this is about the config files.

## Confirm names against a live source

Setting keys, action names, and defaults drift between releases, and an unrecognized key does nothing: the edit looks successful and the behavior doesn't change. Before writing a setting key, action name, or default value into a config, confirm it against one of these:

1. **The user's own Zed** — matches their installed version, so this is the strongest source. `zed: open default settings` opens every setting with its current default; `zed: open keymap` (`cmd-k cmd-s`) lists every action with its bindings; the Settings Editor (`cmd-,`) searches settings with descriptions.
2. **The live docs as Markdown** — append `.md` to any docs page to get it without site chrome. `https://zed.dev/docs/reference/all-settings.md` is the full settings catalog; `https://zed.dev/docs/llms.txt` indexes every page. Fetch these when web access is available.

If neither source is reachable, or a lookup doesn't confirm a key, name the unverified keys instead of supplying a plausible-looking one. Guessing from VS Code or Neovim habits is the usual failure: Zed keys are unprefixed snake_case (`buffer_font_size`, not `editor.fontSize`).

## Which file

| Goal                               | User-level file         | Project-level        | Open with                                                                   |
| ---------------------------------- | ----------------------- | -------------------- | --------------------------------------------------------------------------- |
| Behavior, appearance, language, AI | `settings.json`         | `.zed/settings.json` | `zed: open settings file` (`cmd-alt-,`); UI: `zed: open settings` (`cmd-,`) |
| Key bindings                       | `keymap.json`           | —                    | `zed: open keymap file`; UI: `cmd-k cmd-s`                                  |
| Runnable commands                  | `tasks.json`            | `.zed/tasks.json`    | `zed: open tasks` / `zed: open project tasks`                               |
| Snippets                           | `snippets/<scope>.json` | —                    | `snippets: configure snippets`                                              |
| Hand-written themes                | `themes/<name>.json`    | —                    | drop the file in, then reload                                               |

User-level files live in `~/.config/zed/` on both macOS and Linux (`$XDG_CONFIG_HOME/zed/` if set) and `%APPDATA%\Zed\` on Windows. Installed extensions and downloaded language servers live somewhere else entirely — `~/Library/Application Support/Zed/`, `~/.local/share/zed/`, `%LOCALAPPDATA%\Zed\` — so don't look for config there.

## How settings layer

Defaults → user settings → project settings, with later layers overriding earlier ones. Objects merge key by key; arrays replace wholesale. Subdirectories inside a project can carry their own `.zed/settings.json` for finer scope.

Four rules that decide whether an edit takes effect at all:

- **Project files hold editor and language-tooling settings only.** `theme`, `vim_mode`, and other app-level keys are ignored in `.zed/settings.json` — they belong in user settings.
- **A project's settings stay dormant until its worktree is trusted.** Zed opens worktrees in Restricted Mode: `.zed/settings.json` is not parsed, and language and MCP servers are not started. An exclamation icon appears in the title bar; `workspace::ToggleWorktreeSecurity` grants trust. Check this first when a project config "does nothing".
- **Per-language overrides go under `languages`**, and only a subset of settings is language-scopable (see `references/languages.md`).
- **Release channels can diverge** via top-level `"nightly"` / `"preview"` blocks that override the root for those builds.

## Editing an existing config

These files are JSONC — `//` comments are legal and users keep notes in them. Edit in place with targeted insertions rather than regenerating the file, and preserve existing keys, comments, and formatting.

- Fold new keys into the existing block for that object. A second top-level `"terminal": {...}` doesn't merge with the first; it shadows it and quietly drops those settings.
- Array-valued settings replace the default array rather than extending it. Adding one glob to `file_scan_exclusions` discards every default exclusion unless the defaults are re-listed. The same trap applies to `languages.*.language_servers`.
- Say which file changed, and what the user should now see. A few settings need a language-server or app restart to take effect.

## Keymap shape

`keymap.json` is an array of blocks, each an optional `context` plus a `bindings` map:

```json
[
	{
		"context": "Editor && vim_mode == normal",
		"bindings": {
			"ctrl-right": "editor::SelectLargerSyntaxNode",
			"cmd-k cmd-s": "zed::OpenKeymap",
			"cmd-1": ["workspace::ActivatePane", 0],
			"cmd-r": null
		}
	}
]
```

Modifiers join with `-` and never `+`; a space separates the steps of a chord. Actions take a bare string, or an array when they need arguments; `null` disables a binding. Bindings on lower context nodes beat higher ones, and among equals the later definition wins — which is why user bindings override defaults. Contexts, precedence details, vim contexts, and keystroke remapping are in `references/keymap.md`.

## Where to look

- `references/keymap.md` — any keybinding work: contexts, chords, disabling defaults, vim/helix bindings, base keymaps, binding a task.
- `references/languages.md` — per-language settings, formatters and format-on-save, LSP options and binaries, file-type mapping, linting.
- `references/appearance.md` — themes and theme overrides, syntax colors, fonts and ligatures, UI chrome, settings profiles.
- `references/tasks-and-snippets.md` — task definitions, task variables and hooks, snippet files and scopes.
- `references/ai-and-extensions.md` — agent settings, models, MCP servers, edit prediction, installing and pinning extensions.

## Gotchas

- A `.zed/settings.json` that has no effect usually means an untrusted worktree, not a bad key.
- `lsp` options use nested objects. VS Code's dotted form (`"preferences.target": "ES2020"`) parses as a literal key name and is ignored.
- `languages.*.language_servers` replaces the default list, including its `!`-disabled entries; `"..."` then re-enables anything not explicitly excluded.
- Editor, UI, terminal, and agent fonts are separate settings — changing `buffer_font_family` leaves the interface font untouched.
- `zed: import vs code settings` migrates a large slice of a VS Code config; suggest it before hand-translating one.
- Tasks and terminals inherit different environments depending on whether Zed was launched from the CLI or from a Dock/launcher icon, which is the usual cause of "command not found" in a task but not in a shell. See `https://zed.dev/docs/environment.md`.
- An `.editorconfig` in the project overrides the corresponding Zed setting for line endings.

## Before finishing

- Every key written was confirmed against the reference or the user's own Zed, and any that weren't are named as unverified.
- The file is valid JSONC, existing comments and unrelated keys survived, and nothing re-declares an object that already existed.
- The setting is in a layer where it actually applies (app-level keys in user settings, not project settings).
- The user knows which file changed and whether a restart is needed.
