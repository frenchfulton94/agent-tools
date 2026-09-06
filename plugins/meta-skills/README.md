# meta-skills

Skills for building and maintaining the things Claude Code itself runs on — skills, subagents,
hooks, plugins, and the marketplace that distributes them — plus the writing and memory skills
that keep a repository legible to the next agent that opens it.

## Install

    claude plugin marketplace add YOUR-GITHUB-OWNER/agent-tools --scope project
    claude plugin install meta-skills@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/meta-skills
claude plugin validate plugins/meta-skills --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `authoring-skills` | Skill | `SKILL.md` packages — references, scripts, evals, and descriptions that trigger reliably |
| `authoring-subagents` | Skill | Agent markdown, frontmatter, tool grants, and the descriptions that drive delegation |
| `authoring-hooks` | Skill | Event selection, matcher syntax, and the exit-code and JSON output contracts |
| `authoring-plugins` | Skill | One plugin's manifest, layout, and local install-and-validate loop |
| `maintaining-plugin-marketplaces` | Skill | The catalog above those four — registration, version discipline, curation |
| `improving-prompts` | Skill | Reviewing and rewriting prompts of any kind for current models |
| `managing-project-memory` | Skill | `CLAUDE.md` and the rest of the instruction files agents load at session start |
| `mapping-project-tooling` | Skill | `TOOLS.md`, an assistant-neutral map of a project's commands and conventions |
| `controlled-engineering-english` | Skill | Documentation prose in a controlled language, with a project glossary |
| `controlled-english` | Output style | The compiled always-on form of the skill above |

The five authoring skills are split rather than merged because each owns one artifact. They route
to each other explicitly, and `maintaining-plugin-marketplaces` owns the relationships between
them — the split is scope, not difficulty.

## The output style

`output-styles/controlled-english.output-style.md` is compiled from the
`controlled-engineering-english` skill. An output style ships with its plugin, so it does not
appear under `/config` until this plugin is active — install, run `/reload-plugins`, then select
it. Nothing can select it for you; choosing an output style is a preference.

Edit the skill, not the compiled style.

## License

MIT.
