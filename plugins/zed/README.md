# zed

Configuring and customizing the Zed editor.

## Install

    claude plugin marketplace add YOUR-GITHUB-OWNER/agent-tools --scope project
    claude plugin install zed@agent-tools --scope project

Zed configuration is usually a workstation preference rather than a repository one, so `--scope
user` is often the better choice here — it writes to `~/.claude/settings.json` and follows you
between projects:

    claude plugin install zed@agent-tools --scope user

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/zed
claude plugin validate plugins/zed --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `configuring-zed` | Skill | `settings.json` and `keymap.json`, themes and fonts, per-language and LSP options, formatters, tasks, snippets, extensions, and AI and agent configuration |

## Why this is its own plugin

One skill is a thin plugin, and the alternative was folding it into `meta-skills` alongside the
authoring and tooling skills. It ships separately because the reason someone installs it —
"I use Zed" — is shared by nothing else in the catalog. A user installing `meta-skills` to write
a subagent has no use for keymap configuration, and bundling the two would put it in front of
every one of them.

## License

MIT.
