# OpenSpec Troubleshooting

Symptom first, then the cause, then the fix. Diagnose before editing — most "config ignored" reports are a dropped field or a precedence surprise, and a guessed fix leaves the real cause in place.

Contents:
- [Diagnosing in three commands](#diagnosing-in-three-commands)
- [Install and setup](#install-and-setup)
- [Slash commands missing](#slash-commands-missing)
- [Config not applied](#config-not-applied)
- [Schema problems](#schema-problems)
- [Change and artifact problems](#change-and-artifact-problems)
- [Validation messages](#validation-messages)
- [Archive problems](#archive-problems)
- [Poor artifact quality](#poor-artifact-quality)
- [Migration from the legacy workflow](#migration-from-the-legacy-workflow)

## Diagnosing in three commands

```bash
openspec --version                                        # is the CLI there, and how old
openspec schema which --all                               # which schema wins, from where
openspec instructions <artifact> --change <name> --json    # what the assistant actually receives
```

The third is decisive for anything about context, rules, or templates. If a value is absent from that payload, the problem is upstream of the assistant.

Run diagnostics in a plain terminal, not piped: dropped-field warnings go to stderr and are easy to lose.

## Install and setup

**`openspec: command not found`** — not installed, or the global bin directory is not on `PATH`. Install with `npm install -g @fission-ai/openspec@latest`, then `npm prefix -g` to find where globals live (binaries in that directory's `bin/` on macOS/Linux, directly in it on Windows). With nvm or fnm the CLI is tied to the Node version active at install time; with asdf or volta a shim may need regenerating.

**"Requires Node.js 20.19.0 or higher"** — check `node --version`. Installing via bun still requires Node on `PATH`, since OpenSpec runs on Node.

**`openspec init` didn't configure my tool** — the tool was not selected. Re-run interactively, or `openspec init --tools claude,cursor`. Copilot is `github-copilot`; Zoo Code is `roocode`; `windsurf` is accepted as an alias for `devin`.

**An older version answers after upgrading** — an earlier copy shadows it on `PATH`. Recent `openspec update` output names the directory the running CLI was loaded from; compare it against the install location.

## Slash commands missing

In order, fastest first:

1. **Wrong half of the product.** `/opsx:propose` goes in the assistant's chat, not a shell.
2. **Wrong spelling for that tool.** Skills-only tools never autocomplete `/opsx` even on a healthy install — Codex needs `$openspec-propose`, Kimi `/skill:openspec-propose`, Amazon Q `@opsx-propose`. See the table in `using-openspec.md`.
3. **Stale or missing files.** Run `openspec update` from the project root — but upgrade the package first, or an outdated CLI reports everything up to date without writing newer workflows.
4. **Never initialized here.** Skills are per project. After cloning or switching folders, run `openspec init` (update only refreshes files that already exist).
5. **Assistant not restarted.** Most tools scan for skills at startup.
6. **Confirm the files.** For Claude Code, `.claude/skills/` should contain `openspec-*` folders.

## Config not applied

| Cause | Fix |
|---|---|
| File is not at `openspec/config.yaml` | Only `openspec/config.yaml` and `openspec/config.yml` are probed. A root-level or misplaced file is invisible |
| Invalid YAML | The whole config is ignored with a warning. Run it through a validator |
| A field failed its type check | Parsing is per-field and resilient — the bad field is dropped with a `console.warn` and everything else loads. Read stderr |
| `context` over 50KB | The entire field is dropped. Summarize, or link out instead of pasting |
| Expected a restart | None is needed; config is read fresh on every command |
| Used `openspec config set` | That writes the **machine** JSON config, not the project YAML. Edit `openspec/config.yaml` by hand |
| Rules present but not injected | The key must match an artifact id in the schema that change uses. `openspec schemas --json` lists ids per schema |

**"Unknown artifact ID in rules: X"** — the key matches no artifact in *any* available schema. For `spec-driven` the valid ids are `proposal`, `specs`, `design`, `tasks`. This commonly appears after adopting a custom schema that renamed artifacts.

**Context appearing inside generated artifacts** — `<context>` and `<rules>` are constraints for the assistant, never content for the file. Their presence in `proposal.md` is an assistant-side mistake; the fix is in the workflow, not the config.

## Schema problems

**"Schema not found"** — the name in `config.yaml`, `--schema`, or `.openspec.yaml` does not resolve. `openspec schemas` lists what exists; `openspec schema which <name>` shows which of project/user/package won.

**`Invalid schema: artifacts.N.<field>: … is required`** — an artifact is missing one of the four required fields. `description` and `template` are required even though the docs' table implies otherwise.

**`Template not found: …`** — an artifact names a template file that does not exist under the schema's `templates/` directory. `openspec schema validate <name>` catches this before runtime.

**"must be a relative path inside its allowed directory"** — a `generates` or `template` value is absolute, has a drive letter, or contains `..`.

**"Cyclic dependency detected: a → b → a"** — `requires` edges form a loop. The message names the full path.

**"Duplicate artifact ID"** / **"Invalid dependency reference"** — two artifacts share an id, or a `requires` entry names an id that does not exist.

**A forked schema has no effect** — forking does not adopt. Set `schema: <name>` in `openspec/config.yaml`, or pass `--schema <name>` on `openspec new change`.

**A project schema is not discovered** — it must be `openspec/schemas/<name>/schema.yaml`, with a name free of path separators and dots. Dot-bearing directories (`.fork-staging-*`, `*.fork-backup-*`) are fork temp dirs and are skipped by discovery.

**Archive stopped merging specs after a schema change** — the custom schema no longer has an artifact with `id: specs`, or its `generates` moved out from under `specs/`. Archive and sync find deltas through `artifactPaths.specs.existingOutputPaths`; `skip_specs` matches on the path prefix. Restore both.

## Change and artifact problems

**"Change not found"** — name it explicitly (`/opsx:apply add-dark-mode`), confirm it exists with `openspec list`, and confirm you are in the right project directory.

**"No artifacts ready"** — everything is done or blocked. `openspec status --change <name>` shows what is blocking; create the missing dependency first.

**An artifact reads `done` but its dependencies were never written** — status is filesystem existence only, so writing `tasks.md` by hand marks `tasks` done with no `specs`. Build the required set by walking each artifact's `requires` edges transitively from `applyRequires`, not by trusting status.

**An artifact shows as `skipped`** — the change declares `skip_specs: true`. Its files must not exist; do not create them. To reinstate specs, remove the marker from `.openspec.yaml` and rerun.

## Validation messages

**Zero-delta change rejected** — either the change genuinely changes behavior and needs a delta spec, or it does not and should declare `skip_specs: true`. Do not invent a requirement to satisfy validation.

**`skip_specs` declared *and* spec files present** — a deliberate conflict, so a stale marker cannot linger. Remove whichever is wrong.

**`MODIFIED "<req>" omits scenario(s) the current spec still has`** — a MODIFIED requirement replaces the whole block, so it must carry every surviving scenario. Copy the named ones back from `openspec/specs/<capability-path>/spec.md`. This often surfaces on an older change after someone else's change added a scenario to the same requirement.

**A scenario is silently ignored** — scenarios need exactly four hashes (`#### Scenario:`). Three hashes or a bullet does not parse.

**Purpose reported as too brief under `--strict`** — a new capability's `## Purpose` wants 50+ characters. Omitting it entirely leaves a `TBD` placeholder in the created main spec.

## Archive problems

**"User force closed the prompt with 0 null"** — archive was run where nothing can answer its confirmations: an agent, CI, or a shell with stdin closed. Pass the change name and `--yes`, keeping any flags you were already using (`--skip-specs` and `--no-validate` change behavior, so a bare `--yes` rerun is not the same command).

**Archive warns about incomplete tasks** — it warns but does not block. Finish the tasks, or proceed deliberately if filing a partial change.

**Archive aborts on a capability it cannot write** — the change's REMOVED entries take a capability's last requirement. That deletion is opt-in: add `retire_capabilities: true` to the change's `.openspec.yaml` next to `schema:`.

**Escape codes bloating captured output** — older versions drew interactive prompts into redirected output. Current versions read confirmations as plain text when stdout is not a terminal; passing `--yes` with a change name avoids prompts entirely.

## Poor artifact quality

Not a bug — a context problem. In order of leverage:

1. Add project `context:` so the stack and conventions reach every request.
2. Add per-artifact `rules:` for guidance that only applies to one artifact.
3. Give a more detailed description when proposing.
4. Use the expanded `/opsx:continue` to create and review one artifact at a time instead of drafting everything at once.
5. Edit the schema's `instruction` field or its template — both take effect immediately, making tune-and-retest the fastest loop available.

Do not edit the generated skill files: `openspec update` overwrites them.

## Migration from the legacy workflow

**"Legacy files detected in non-interactive mode"** — `openspec init --force` approves cleanup automatically.

**Commands missing after migrating** — restart the IDE; skills are detected at startup. Then `openspec update`.

**`openspec/project.md` was not migrated** — intentional, because it may hold hand-written content. Move the useful parts into `config.yaml`'s `context:` and `rules:`, then delete it. The change exists for reliability: `project.md` was passively read, while `context` is actively injected into every planning request.

**Wanting a dry run** — run `openspec init` and decline the cleanup prompt to see the full detection summary with nothing changed.
