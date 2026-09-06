# Evals for configuring-zed

Test material for maintainers of this skill, not for users. Rerun after editing the description or body.

## Should trigger

Run each in a clean context with only the description loaded; the skill should fire.

1. "How do I make Zed format on save for Python but not Markdown?"
2. "Where does Zed keep its settings file on Windows?"
3. "Rebind cmd-shift-p to something else in Zed."
4. "My `.zed/settings.json` isn't doing anything. Here's the file: …"
5. "Set up Zed so comments are italic and the background is a bit darker."
6. "I want jk to escape to normal mode in Zed's vim mode."
7. "Add a task that runs `cargo nextest` and bind it to a key."
8. "I just switched from VS Code — can I bring my settings and snippets over?"
9. "Point rust-analyzer at clippy in my editor." (project contains `.zed/`)
10. "Add the GitHub MCP server to Zed."

## Should not trigger

Near-misses from adjacent domains; the skill should stay closed.

1. "How do I turn on format on save in VS Code?"
2. "Set up conform.nvim to format on save in Neovim."
3. "Write a Zed extension in Rust that adds a language server." (extension _development_)
4. "This JSON file has a syntax error, can you fix it?"
5. "What's the fastest code editor?" — product comparison, not configuration
6. "Configure my Claude Code settings.json."
7. "Use Zed's agent to refactor this module." (using the editor, not configuring it)
8. "How do I install Zed on Fedora?"
9. "Explain how the Language Server Protocol works."
10. "Set up a tasks.json for a GitHub Actions workflow."

Item 3 and item 7 are the valuable negatives: both name Zed, and both should route elsewhere.

## Task cases

Run with and without the skill; grade against the assertions with quoted evidence.

**Case A — invented keys.** "In Zed, make the editor font 16px, the UI font 14px, and turn off ligatures."

- Uses `buffer_font_size`, `ui_font_size`, and `buffer_font_features.calt`, not VS Code-style names.
- Treats editor and UI fonts as separate settings rather than one.
- Doesn't claim a `ligatures` boolean exists.

**Case B — wrong layer.** "Put my theme and tab size in the project's `.zed/settings.json` so my team gets both."

- Flags that `theme` is user-level only and won't apply from project settings.
- Puts `tab_size` in the project file.
- Mentions worktree trust as a precondition for teammates.

**Case C — destructive merge.** Give a `settings.json` that already has a `"terminal"` block with comments, then: "Also make the terminal font Berkeley Mono."

- Adds the key inside the existing `terminal` block rather than declaring a second one.
- Preserves the existing comments and unrelated keys.

**Case D — array replacement.** "Exclude `**/node_modules` from Zed's file scanning."

- Notes that `file_scan_exclusions` replaces the defaults, and either re-lists them or says so explicitly.

**Case E — verification.** "What does `soft_wrap: prefer_line` do in Zed?" (deprecated value)

- Checks the live reference or the user's default settings rather than answering from memory.
- If it can't reach a source, says the value is unverified instead of inventing behavior.
