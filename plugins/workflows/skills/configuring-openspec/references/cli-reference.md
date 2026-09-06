# OpenSpec CLI Reference

The commands that matter for setup, configuration, and driving OpenSpec programmatically. `openspec` runs in a terminal; `/opsx:*` runs in the assistant's chat.

Contents:
- [Setup](#setup)
- [Browsing and validation](#browsing-and-validation)
- [Workflow commands](#workflow-commands)
- [Schema commands](#schema-commands)
- [Archive](#archive)
- [Stores, doctor, context, worksets](#stores-doctor-context-worksets)
- [JSON output for agents](#json-output-for-agents)
- [Exit codes and environment variables](#exit-codes-and-environment-variables)

## Setup

### openspec init

```
openspec init [path] [options]
```

| Option | Description |
|---|---|
| `--tools <list>` | Non-interactive tool setup: `all`, `none`, or comma-separated ids |
| `--force` | Auto-clean legacy files without prompting |
| `--profile <core\|custom>` | Override the global profile for this run |
| `--no-animation` | Static welcome screen |
| `--copilot-cloud` / `--no-copilot-cloud` | Opt in/out of GitHub Copilot cloud agent files without prompting |

Creates `openspec/{specs,changes}` and `config.yaml`, then writes skill and/or command files into each selected tool's directory. Tool ids include `claude`, `cursor`, `codex`, `gemini`, `github-copilot`, `devin` (alias `windsurf`), `roocode`, `agents`, and roughly thirty more; `openspec init --help` prints the live list.

An existing `openspec/` folder is not a problem — init refreshes it and leaves specs and changes alone.

### openspec update

```
openspec update [path] [--force]
```

Regenerates tool files from the **installed** CLI using the current profile, workflow selection, and delivery mode. Upgrade the package first; otherwise it truthfully reports everything up to date while never writing newer workflows. Recent versions check the registry and offer to run the upgrade for you when npm owns the install.

How "up to date" is decided: skill files carry the generating version and are compared by that stamp, so a hand-edited skill whose version still matches is left alone (`--force` rewrites it). Command files carry no stamp, so under `delivery: commands` their content is compared and any local edit counts as drift and is overwritten. Either way, generated files belong to OpenSpec — keep your own instructions elsewhere.

## Browsing and validation

```bash
openspec list                       # active changes  (--specs for specs, --json)
openspec show <item>                # a change or spec (--type change|spec, --json)
openspec view                       # interactive dashboard (human only)
openspec validate <item>            # one item
openspec validate --all --strict    # everything, stricter, good for CI
openspec validate --archived        # fail if any archived change has unchecked tasks
```

`validate` options also include `--changes`, `--specs`, `--type`, `--json`, `--concurrency <n>` (default 6, or `OPENSPEC_CONCURRENCY`), and `--no-interactive`. It exits 1 when any item fails.

A change with zero spec deltas fails validation unless its `.openspec.yaml` declares `skip_specs: true`.

One message worth recognizing:

```
MODIFIED "<requirement>" omits scenario(s) the current spec still has: "<scenario>"
```

A `MODIFIED` requirement replaces the whole block, so it must carry every surviving scenario. Copy the named scenarios back into the delta from `openspec/specs/<capability-path>/spec.md`.

## Workflow commands

```bash
openspec new change <name> [--description <text>] [--goal <text>] [--schema <name>] [--store <id>] [--json]
openspec status  [--change <id>] [--schema <name>] [--json]
openspec instructions [artifact|apply|archive] --change <id> [--schema <name>] [--json]
openspec templates [--schema <name>] [--json]
openspec schemas [--json] [--store <id>]
```

Change names must be lowercase kebab-case — letters, digits, single hyphens. No spaces, underscores, uppercase, doubled hyphens, or leading/trailing hyphens. A leading number is allowed, so `100-add-feature` works for ordering.

`openspec status` text output:

```
Change: add-dark-mode
Schema: spec-driven
Progress: 2/4 artifacts complete

[x] proposal
[x] specs
[ ] design
[-] tasks (blocked by: design)
```

A change declaring `skip_specs: true` renders `[~] specs (skipped: change declares skip_specs)` and excludes it from the count.

`openspec instructions` returns the template, project context, dependency content, and per-artifact rules — the payload the assistant works from. `instructions apply` adds task state and context files; `instructions archive` is a read-only fetch of `context` and `operationGuidance`. For an artifact skipped via `skip_specs`, the output is a warning with `skipped`/`warning` fields and the artifact must not be created.

## Schema commands

```bash
openspec schema fork <source> [name] [--force] [--json]
openspec schema init <name> [--description <text>] [--artifacts <list>] [--default] [--force] [--json]
openspec schema validate [name] [--verbose] [--json]
openspec schema which [name] [--all] [--json]
```

`schema init --artifacts` accepts only `proposal`, `specs`, `design`, `tasks`. For anything else, fork and hand-edit. Every schema command prints an experimental-status note to stderr.

## Archive

```
openspec archive [change-name] [options]
```

| Option | Description |
|---|---|
| `-y, --yes` | Skip confirmations. Required whenever nothing can answer them |
| `--skip-specs` | Skip spec updates for this run only |
| `--no-validate` | Skip validation (requires confirmation; also disables capability retirement) |

What it does, in order: validates the change; prompts for confirmation; claims the archive destination before touching any main spec; validates and merges active delta specs into `openspec/specs/`; moves the change folder to `openspec/changes/archive/YYYY-MM-DD-<name>/`; restores specs and leaves the change at its active path if a mutation or the final move fails.

A capability whose last requirement the change removes is retired and its spec file deleted — but only when `.openspec.yaml` declares `retire_capabilities: true`.

**Non-interactive runs:** an agent, a CI job, or any shell with stdin closed cannot answer the confirmation, so archive stops before touching anything and exits 1, naming the command to rerun. Pass the change name and `--yes` up front, carrying any other flags you were already using — `--skip-specs` and `--no-validate` change behavior, so a bare `--yes` rerun is not the same command.

A change that permanently has no deltas should declare `skip_specs: true` rather than pass `--skip-specs` every time; it then archives with no flag at all.

## Stores, doctor, context, worksets

Beta surface — names, flags, and JSON shapes may change between releases. Relevant only when planning spans repos or teams.

```bash
openspec store setup <id> --path <dir> [--remote <url>] [--no-init-git] [--json]
openspec store register <path> [--id <id>] [--yes] [--json]
openspec store unregister <id> [--json]
openspec store remove <id> [--yes] [--json]
openspec store list [--json]
openspec store doctor [id] [--json]

openspec doctor  [--store <id>] [--json]     # root + reference health, read-only
openspec context [--store <id>] [--json] [--code-workspace <path> [--force]]

openspec workset create [name] [--member <path>]... [--tool <id>] [--json]
openspec workset list [--json]
openspec workset open <name> [--tool <id>]
openspec workset remove <name> [--yes] [--json]
```

Non-interactive `store setup` must pass both the id and `--path`. `store remove` requires `--yes` for agents and scripts, and refuses a folder without matching store metadata. OpenSpec never clones, pulls, or pushes on its own — sharing a store is ordinary git.

`--store <id>` is accepted by the root-resolving commands (`list`, `show`, `validate`, `status`, `instructions`, `new change`, `archive`, `doctor`, `context`, `schemas`). `templates` and the deprecated noun forms are cwd-based and do not take it.

## JSON output for agents

Human prose, spinners, and the store banner go to stderr; `--json` puts exactly one JSON document on stdout. Key casing splits by family: store/doctor/context payloads use `snake_case`, workflow payloads (`status`, `instructions`, `new change`, `validate`, `list`) use `camelCase` — except the embedded `root` object, which is always `store_id`. Optional keys are usually omitted rather than null.

Every machine-readable diagnostic shares one envelope:

```json
{ "severity": "error|warning|info", "code": "snake_case_string", "message": "…", "target": "…", "fix": "…" }
```

Diagnostics appear in `status` arrays for health findings, and as a single-element `status` array on command failure. A root-resolution failure in `--json` mode prints the command's null shape plus `status: [diagnostic]` and exits 1.

Useful shapes:

- `status --json` → `changeName`, `schemaName`, `changeRoot`, `artifactPaths` (per id: `outputPath`, `resolvedOutputPath`, `existingOutputPaths`), `applyRequires`, `artifacts[]` with `status` of `done|skipped|ready|blocked` plus `requires` and `missingDeps`, `isPlanningComplete` (`isComplete` is a compatibility alias with the same value).
- `instructions <artifact> --json` → `template`, `instruction`, `context`, `rules`, `references`, `dependencies[]`, `unlocks`, `resolvedOutputPath`, plus `skipped`/`warning` when applicable.
- `archive --json` → `archive: { change, archivedAs, path, specsUpdated, totals?, warnings? }`, or `archive: null` with `status` on failure. JSON mode is strictly non-interactive: every prompt point becomes an `archive_*` diagnostic code.
- `schemas --json` → a bare array of `{name, description, artifacts, source}` on success (a deliberate compatibility shape).

## Exit codes and environment variables

| Code | Meaning |
|---|---|
| 0 | Success, including health findings from `doctor`/`context`/`store doctor` |
| 1 | Error: validation failure, unresolved root, missing files |
| 130 | Prompt cancellation in the `store` command group |

| Variable | Effect |
|---|---|
| `OPENSPEC_TELEMETRY=0` | Disables telemetry and the update version check |
| `DO_NOT_TRACK=1` | Same |
| `OPENSPEC_CONCURRENCY` | Default parallelism for bulk validation (6) |
| `OPENSPEC_NO_UPDATE_CHECK` | Skips the newer-CLI check on `openspec update` |
| `OPENSPEC_NO_ANIMATION` | Skips the `init` welcome animation |
| `NO_COLOR` | Disables color |
| `EDITOR` / `VISUAL` | Editor for `openspec config edit` |
| `npm_config_registry` | Registry the update check asks; no `.npmrc` is read |
