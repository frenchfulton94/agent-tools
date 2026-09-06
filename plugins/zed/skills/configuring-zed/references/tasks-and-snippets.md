# Tasks and snippets

Live docs: tasks `https://zed.dev/docs/tasks.md` · snippets `https://zed.dev/docs/snippets.md` · terminal `https://zed.dev/docs/terminal.md` · environment `https://zed.dev/docs/environment.md`.

Contents:

- [Task files](#task-files)
- [Task template fields](#task-template-fields)
- [Variables](#variables)
- [Running and rerunning](#running-and-rerunning)
- [Binding tasks to keys and runnables](#binding-tasks-to-keys-and-runnables)
- [Hooks](#hooks)
- [Snippets](#snippets)

## Task files

`tasks.json` is an array of task templates. Global tasks live in `~/.config/zed/tasks.json` (`zed: open tasks`) and are available in every project; project tasks live in `.zed/tasks.json` (`zed: open project tasks`). Language extensions contribute tasks too, and the task modal accepts one-off commands that persist only for the session.

Zed can also read `.vscode/tasks.json`, where `label` is optional — it derives one from the type (`npm: start`, the raw command for shell tasks).

## Task template fields

```json
[
	{
		"label": "run tests",
		"command": "cargo",
		"args": ["test"],
		"env": { "RUST_BACKTRACE": "1" },
		"cwd": "$ZED_WORKTREE_ROOT",
		"use_new_terminal": false,
		"allow_concurrent_runs": false,
		"reveal": "always",
		"hide": "never",
		"save": "none",
		"tags": []
	}
]
```

- `reveal`: `always` (show and focus), `no_focus`, `never`.
- `hide`: what happens to the tab after the command exits — `never`, `always`, `on_success`.
- `save`: which dirty buffers to write first — `none`, `current`, `all`.
- `shell`: `"system"`, `{ "program": "sh" }`, or `{ "with_arguments": { "program": "/bin/bash", "args": ["--login"] } }`.
- `show_summary` / `show_command` control the header lines printed above the output.

Tasks run in a login shell, so shell rc files are sourced. When a command works in the terminal but not in a task, the cause is usually the environment Zed inherited at launch (Dock/launcher versus CLI), not the task definition.

## Variables

Task fields interpolate shell-style `$VAR`, including a set Zed injects from the editor state: `ZED_FILE`, `ZED_FILENAME`, `ZED_DIRNAME`, `ZED_RELATIVE_FILE`, `ZED_RELATIVE_DIR`, `ZED_STEM`, `ZED_ROW`, `ZED_COLUMN`, `ZED_SELECTED_TEXT`, `ZED_SYMBOL`, `ZED_LANGUAGE`, `ZED_WORKTREE_ROOT`, `ZED_MAIN_GIT_WORKTREE`. Git Graph command tasks get their own set (`ZED_GIT_SHA`, `ZED_GIT_REF`, …). The tasks page carries the current list.

Two behaviors that surprise people:

- **Quoting.** `"command": "stat $ZED_FILE"` breaks on paths with spaces. Pass the variable as its own entry in `args`, or escape the quotes inside the command string.
- **Filtering.** A task referencing a variable that has no value right now is hidden from the modal — a task using `$ZED_SELECTED_TEXT` appears only while text is selected. `${ZED_SELECTED_TEXT:default}` supplies a fallback and keeps the task listed.

## Running and rerunning

`task: spawn` opens the modal; `task: rerun` repeats the last one. With the defaults (`use_new_terminal: false`, `allow_concurrent_runs: false`) a rerun waits for the previous run to finish in the same terminal; setting `allow_concurrent_runs: true` cancels instead of waiting. Reruns replay the variables captured at first launch unless the rerun action passes `{ "reevaluate_context": true }`.

## Binding tasks to keys and runnables

```json
{ "context": "Workspace", "bindings": { "alt-t": ["task::Spawn", { "task_name": "run tests" }] } }
```

`reveal_target: "center"` puts the task in the center pane instead of the terminal dock — the way to run a TUI like lazygit as a task.

`tags` reroute the inline run buttons in the gutter: tag a template with a language's runnable tag (`rust-test`, `bash-script`, …) and it replaces the default action for that indicator. Precedence is project `tasks.json`, then global, then the language's own binding.

## Hooks

A `hooks` array makes a task fire on a Zed event instead of on demand. `create_worktree` runs after a linked git worktree is created, with `ZED_WORKTREE_ROOT` on the new worktree and `ZED_MAIN_GIT_WORKTREE` on the original — the standard use is copying untracked files like `.env`:

```json
[
	{
		"label": "copy .env into new worktree",
		"command": "cp",
		"args": ["$ZED_MAIN_GIT_WORKTREE/.env", "$ZED_WORKTREE_ROOT/.env"],
		"hooks": ["create_worktree"],
		"reveal": "no_focus",
		"hide": "on_success"
	}
]
```

Hook tasks stay spawnable by hand, and several tasks may share a hook.

## Snippets

Snippet files live in `~/.config/zed/snippets/`; `snippets: configure snippets` creates or opens the file for a scope, `snippets: open folder` opens the directory. JSON is the only supported format.

```json
{
	"Log to console": {
		"prefix": "log",
		"body": ["console.info(\"Hello, ${1:World}!\")", "$0"],
		"description": "Logs to console"
	}
}
```

- The object key is the name; `prefix` is the trigger and falls back to the name; `description` is optional.
- `$1`, `$2`, `${1:default}` are tab stops, repeated numbers stay linked, `$0` is the final cursor position. A literal `$` outside a placeholder needs escaping.
- Only the first prefix in a list is honored.

Scope comes from the filename: the language's display name in lowercase (`python.json`, `shell script.json`), with `snippets.json` for all languages, `plaintext.json` for Plain Text, and `javascript.json` for JSX — TSX and TypeScript follow the normal rule. VS Code snippet files can be copied straight into this folder.
