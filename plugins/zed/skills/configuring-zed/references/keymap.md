# Keymap

Live docs (fetch for anything version-specific): key bindings `https://zed.dev/docs/key-bindings.md` · action catalog `https://zed.dev/docs/all-actions.md` · vim `https://zed.dev/docs/vim.md` · helix `https://zed.dev/docs/helix.md`. Shipped defaults, per platform, are the source of truth for what a binding currently does: `assets/keymaps/default-macos.json`, `default-linux.json`, `default-windows.json` in `github.com/zed-industries/zed`.

Contents:

- [Finding action names](#finding-action-names)
- [Keystroke syntax](#keystroke-syntax)
- [Contexts](#contexts)
- [Precedence and disabling](#precedence-and-disabling)
- [Remapping and sequences](#remapping-and-sequences)
- [Base keymaps and non-QWERTY](#base-keymaps-and-non-qwerty)
- [Vim and Helix contexts](#vim-and-helix-contexts)
- [Debugging a binding](#debugging-a-binding)

## Finding action names

Actions are namespaced like `editor::SelectLargerSyntaxNode`, `workspace::Save`, `project_panel::Open`. There is no need to recall them: the keymap editor (`cmd-k cmd-s`, or `zed: open keymap`) lists every action with its current binding, the command palette fuzzy-searches the same set, and `keymap.json` autocompletes action names as you type. The docs page above mirrors the list. Confirm the exact string before writing it — a misspelled action is accepted by the file and simply never fires.

## Keystroke syntax

Each key in `bindings` is a sequence of keypresses separated by spaces; each keypress is modifiers then a key, joined by hyphens.

Modifiers: `ctrl-`, `alt-` (option on macOS), `shift-`, `fn-`, `cmd-` / `win-` / `super-` for the platform key, and `secondary-` which resolves to cmd on macOS and ctrl elsewhere.

```json
{
	"bindings": {
		"cmd-k cmd-s": "zed::OpenKeymap", // cmd-k, then cmd-s
		"space e": "editor::ShowCompletions", // space, then e
		"shift shift": "file_finder::Toggle" // tap shift twice
	}
}
```

- `shift-` combines only with letters, to mean the uppercase form: `shift-g` matches `G`. Punctuation typed with shift is not "modified", so `shift-(` matches nothing.
- `alt-` on many layouts produces a different character; `alt-c` and `ç` refer to the same keypress on a US macOS layout. Zed writes these as `alt-c` by convention.
- Modifier-only bindings (`shift shift`) fire on key release.
- Keys may be any single codepoint the keyboard produces, or a named key (`tab`, `f1`, `escape`).

## Contexts

Active contexts form a tree rooted at `Workspace`, with panes, panels, editors, and terminals below it, each carrying attributes (`mode=full`, `vim_mode=insert`, `os=macos`). A block with no `context` is always active.

Expression syntax: `&&`, `||`, `!X`, `(X)`, and `X > Y` matching when an _ancestor_ matches `X` and the current layer matches `Y`.

```json
{ "context": "Editor && mode == full" }   // real code editors, not inline inputs
{ "context": "!Editor && !Terminal" }      // anywhere neither is focused
{ "context": "ProjectPanel && not_editing" }
{ "context": "debugger_stopped > vim_mode == normal" }
```

Attributes only exist on the node that defines them, which is why the last example needs `>` rather than `&&`. Before Zed v0.197, `!` examined one node at a time and `>` meant "parent" rather than "ancestor"; older configs found online may rely on that.

## Precedence and disabling

Two rules resolve conflicts: bindings matching lower in the context tree beat those matching higher (a `Editor` binding beats a `Workspace` one; a context-free binding matches lowest), and among bindings at the same level the later definition wins. User keymaps load after the defaults, so they win by default.

`null` disables a binding for a context:

```json
[{ "context": "Workspace", "bindings": { "cmd-r": null } }]
```

A `null` follows the same precedence rules, so it also suppresses matching bindings further up the tree. This is the fix when an action propagates: some actions only trigger conditionally (`buffer_search::DeployReplace` fires only when the search bar is hidden) and otherwise fall through to whatever the default keymap binds, producing surprising behavior. Disable the higher binding, then bind the action you want.

When one binding is a prefix of another (`ctrl-w` and `ctrl-w left`), Zed waits one second after the prefix before firing it.

## Remapping and sequences

`workspace::SendKeystrokes` replays a space-separated keystroke list, which is how to emulate vim's `map` commands:

```json
[
	{ "bindings": { "alt-down": ["workspace::SendKeystrokes", "down down down down"] } },
	{
		"context": "Editor && vim_mode == insert",
		"bindings": { "j k": ["workspace::SendKeystrokes", "escape"] }
	}
]
```

Limits: async work (opening the palette, LSP round-trips, changing buffer language, anything networked) doesn't complete until all keystrokes have dispatched, so later keys can't act on it; the cap is 100 simulated keys; unrecognized segments are typed verbatim into the focused input. If the argument contains the binding that triggered it, the next-highest-precedence definition is used, which lets a binding extend rather than replace a default.

To hand a combination to the built-in terminal instead of Zed (common on Linux and Windows, where `ctrl-n` opens a tab):

```json
{ "context": "Terminal", "bindings": { "ctrl-n": ["terminal::SendKeystroke", "ctrl-n"] } }
```

Tasks bind through `task::Spawn` with the task's label, optionally targeting a pane:

```json
{
	"context": "Workspace",
	"bindings": {
		"alt-g": ["task::Spawn", { "task_name": "start lazygit", "reveal_target": "center" }]
	}
}
```

## Base keymaps and non-QWERTY

`base_keymap` in `settings.json` picks the starting scheme — VS Code (default), Atom, JetBrains, Sublime Text, TextMate, Emacs, Cursor, or None to drop every binding — and `zed: toggle base keymap selector` changes it interactively. `vim_mode` and `helix_mode` layer modal bindings on top.

On layouts that need `option` to reach parts of ASCII, Zed relocates built-in shortcuts to match the layout. Personal bindings opt into the same mapping with `"use_key_equivalents": true` on the binding block. Mostly-non-ASCII layouts (Cyrillic, Hebrew, Thai) match against both the real and the ASCII-equivalent key automatically.

## Vim and Helix contexts

Vim mode adds attributes to the `Editor` node: `vim_mode ==` one of `normal`, `visual`, `insert`, `replace`, `waiting`, `operator`; `vim_operator` holding the pending operator's key; and `VimControl` as an alias for the normal/visual/operator set. Helix mode builds on vim mode and uses the same contexts. Because they attach at the editor level, `Workspace && vim_mode == normal` can never match.

Useful starting shape:

```json
[
	{ "context": "VimControl && !menu", "bindings": {} },
	{ "context": "vim_mode == insert", "bindings": { "j k": "vim::NormalBefore" } },
	{ "context": "EmptyPane || SharedScreen", "bindings": {} }
]
```

Vim mode also has its own settings block (`vim.default_mode`, `vim.use_system_clipboard`, `vim.toggle_relative_line_numbers`, `vim.custom_digraphs`, and more) plus `command_aliases` for command-palette shortcuts — all documented on the vim page.

## Debugging a binding

`dev: open key context view` shows the live context stack and the keypresses Zed is resolving, which answers both "why didn't my binding fire" (wrong context) and "what key did Zed think I pressed" (layout mapping). The keymap editor also surfaces conflicting bindings for an action.
