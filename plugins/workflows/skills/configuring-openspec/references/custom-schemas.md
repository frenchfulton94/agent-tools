# Custom Schemas and Templates

Contents:
- [What a schema is](#what-a-schema-is)
- [Fork, don't init](#fork-dont-init)
- [schema.yaml field reference](#schemayaml-field-reference)
- [The specs artifact contract](#the-specs-artifact-contract)
- [Templates](#templates)
- [Dependency graph semantics](#dependency-graph-semantics)
- [Worked examples](#worked-examples)
- [Validating and adopting](#validating-and-adopting)
- [Debugging resolution](#debugging-resolution)
- [Community schemas](#community-schemas)
- [Manual validation checklist](#manual-validation-checklist)

## What a schema is

A schema declares which artifacts a change contains and how they depend on one another. The built-in `spec-driven` schema defines `proposal → specs → design → tasks` plus an `apply` phase that tracks `tasks.md` checkboxes.

Everything the assistant is told about an artifact comes from the schema (`instruction`, `template`) merged with project config (`context`, `rules`). Editing a template changes output immediately — no rebuild, no release.

Schemas live in one of three places, searched in this order: project `openspec/schemas/<name>/`, user `~/.local/share/openspec/schemas/<name>/`, package built-ins. Prefer project-local: it is version-controlled alongside the code it governs.

```
openspec/schemas/my-workflow/
├── schema.yaml
└── templates/
    ├── proposal.md
    ├── spec.md
    ├── design.md
    └── tasks.md
```

## Fork, don't init

```bash
openspec schema fork spec-driven my-workflow      # name defaults to <source>-custom
```

Fork copies the whole schema, templates included, into `openspec/schemas/<name>/` where it can be edited freely. This is almost always the right starting point.

`openspec schema init <name>` exists, but **its `--artifacts` flag only accepts the four built-in ids** — `proposal`, `specs`, `design`, `tasks` — and errors on anything else. It cannot scaffold a novel artifact such as `research` or `review`, despite documentation that reads as though it can. To add one: fork, then hand-edit `schema.yaml` and hand-write the template file.

Two further differences worth knowing if a project was scaffolded with `init` rather than `fork`: `init` points the specs artifact's template at `templates/specs/spec.md` (the built-in uses `templates/spec.md`), and it wires `design` to require `specs`, where the built-in has `design` require only `proposal`. Both are valid; just don't assume one when reading the other.

Schema commands print `Note: Schema commands are experimental and may change.` on every run. That is expected, not an error.

## schema.yaml field reference

Top level:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Non-empty. Match the directory name. |
| `version` | integer | Yes | Positive integer. `1` for a new schema. |
| `description` | string | No | Shown by `openspec schemas`. |
| `artifacts` | array | Yes | At least one. |
| `apply` | object | No | The implementation phase. |

Each artifact:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | **Yes** | Unique. Used in `rules:` keys, commands, and status output. |
| `generates` | string | **Yes** | Output path relative to the change dir. Globs allowed (`specs/**/*.md`). |
| `description` | string | **Yes** | Short human description. |
| `template` | string | **Yes** | Path relative to the schema's `templates/` dir. |
| `instruction` | string | No | The authoritative guidance the assistant follows for this artifact. |
| `requires` | string[] | No | Defaults to `[]`. Ids that must exist first. |

`description` and `template` being required is the trap. The customization docs present a field table that reads as optional-by-default; the runtime Zod schema rejects an artifact missing either, with `Invalid schema: artifacts.N.template: template field is required`.

`apply`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `requires` | string[] | **Yes**, min 1 | Artifact ids needed before implementation can start. |
| `tracks` | string \| null | No | Checkbox file for progress, relative to change dir. |
| `instruction` | string | No | Guidance for the implementation phase. |

Both `generates` and `template` must be **relative paths that stay inside their directory**. Absolute paths, drive letters, and `..` segments are rejected at parse time.

Parsing additionally rejects duplicate artifact ids, a `requires` entry naming a non-existent id, and any dependency cycle (reported with the full path, e.g. `Cyclic dependency detected: a → b → a`).

## The specs artifact contract

Two separate mechanisms both depend on the specs artifact, and they key off **different things**. A custom schema must satisfy both or archiving quietly stops working.

| Mechanism | Keys off | Consequence if broken |
|---|---|---|
| `skip_specs: true` in a change | Any artifact whose `generates` starts with `specs/` (leading `./` tolerated) | Marker ignored; the graph blocks dependents on files that must not exist |
| Archive / sync / bulk-archive delta discovery | The artifact **id** `specs`, via `artifactPaths.specs.existingOutputPaths` in `openspec status --json` | Nothing to sync; the change archives with no spec merge |

So: **keep an artifact with `id: specs` whose `generates` stays under `specs/`.** Renaming it to `contracts` breaks archive discovery; moving output to `contracts/**/*.md` breaks `skip_specs`. Adding artifacts around it is fine.

The CLI's own `openspec archive` also reads `<changeDir>/specs` directly, reinforcing the same layout.

## Templates

A template is a Markdown file injected into the prompt as the structure the assistant fills in. It typically contains section headers plus HTML comments carrying guidance:

```markdown
## Why

<!-- Explain the motivation. What problem does this solve? Why now? -->

## What Changes

<!-- Be specific about new capabilities, modifications, or removals. -->

## Impact

<!-- Affected code, APIs, dependencies, systems -->
```

Rules of thumb:

- The template is the *output shape*; `instruction` is the *reasoning guidance*. Put structure in one and judgment in the other.
- A template referenced by an artifact must exist on disk. `openspec schema validate` catches a missing one; the runtime raises `TemplateLoadError: Template not found: …`.
- Template paths may nest (`specs/spec.md`), but must resolve inside the schema's `templates/` directory.
- Edits take effect on the next command. Iterating on a template and re-running `openspec instructions <artifact> --change <name>` is the fastest tuning loop available.

## Dependency graph semantics

Artifacts form a DAG. `requires` are **enablers, not gates** — they describe what becomes possible, not what is mandatory next. Status is pure filesystem existence:

```
BLOCKED ──────────► READY ──────────► DONE
missing deps      all deps done     file exists
```

`openspec status --json` lists artifacts in dependency order, breaking ties between simultaneously-ready artifacts by **the order they are declared in `artifacts:`** — never alphabetically. So the first `ready` entry is the artifact to write next, and declaration order is a real authoring decision.

Because status is existence-only, an artifact can read `done` while its dependencies were never written (writing `tasks.md` by hand marks `tasks` done with no `specs`). Agents should build the required set by walking each artifact's `requires` edges transitively from `applyRequires`, not by trusting `status`.

## Worked examples

### Add a review gate between design and tasks

```bash
openspec schema fork spec-driven with-review
```

Then in `openspec/schemas/with-review/schema.yaml`, add the artifact and re-point `tasks`:

```yaml
  - id: review
    generates: review.md
    description: Pre-implementation review checklist
    template: review.md
    instruction: |
      Create a review checklist based on the design.
      Cover security, performance, and testing considerations.
      Flag anything that should change before implementation starts.
    requires:
      - design

  - id: tasks
    generates: tasks.md
    description: Implementation checklist with trackable tasks
    template: tasks.md
    requires:
      - specs
      - design
      - review
```

Create `openspec/schemas/with-review/templates/review.md`. Note what this does and does not do: OpenSpec only checks that the artifact file **exists**. It does not read a verdict or block on content. Enforcing a real gate needs CI or a hook.

### Research-first workflow

```yaml
name: research-first
version: 1
description: Investigate before proposing
artifacts:
  - id: research
    generates: research.md
    description: Findings from investigating the problem space
    template: research.md
    instruction: |
      Investigate the codebase and record findings, options, and tradeoffs.
      No decisions yet - this artifact exists to inform the proposal.
    requires: []

  - id: proposal
    generates: proposal.md
    description: Change proposal informed by research
    template: proposal.md
    requires: [research]

  - id: specs
    generates: "specs/**/*.md"
    description: Delta specifications for the change
    template: spec.md
    requires: [proposal]

  - id: tasks
    generates: tasks.md
    description: Implementation checklist
    template: tasks.md
    requires: [specs]

apply:
  requires: [tasks]
  tracks: tasks.md
```

Note `specs` is retained with its id and path, so archive and `skip_specs` both keep working.

### Rapid iteration, minimal ceremony

```yaml
name: rapid
version: 1
description: Fast iteration with minimal overhead
artifacts:
  - id: proposal
    generates: proposal.md
    description: Quick proposal
    template: proposal.md
    instruction: |
      Brief proposal for this change. Focus on what and why; skip detailed specs.
    requires: []

  - id: tasks
    generates: tasks.md
    description: Implementation checklist
    template: tasks.md
    requires: [proposal]

apply:
  requires: [tasks]
  tracks: tasks.md
```

A schema with **no `specs` artifact** has nothing to sync — every change under it archives without touching main specs. That is a deliberate tradeoff, not a bug: say so explicitly when recommending this shape, because the user loses the source-of-truth accumulation that motivates OpenSpec.

## Validating and adopting

```bash
openspec schema validate my-workflow      # or omit the name to validate all
openspec schema validate my-workflow --verbose
```

Validation checks YAML syntax, that every referenced template exists inside the templates directory, that artifact ids are valid and unique, and that there are no cycles.

A schema is inert until something selects it:

```yaml
# openspec/config.yaml
schema: my-workflow
```

or per change:

```bash
openspec new change my-feature --schema my-workflow
```

The change's `.openspec.yaml` records the schema, so a change keeps its workflow even if the project default later changes.

After adopting a schema with new artifact ids, revisit `rules:` in `config.yaml` — keys that matched the old ids now warn as unknown and inject nothing.

## Debugging resolution

```bash
openspec schemas                      # names, descriptions, artifact flow, source
openspec schemas --json               # artifact ids per schema - the source of truth for rules keys
openspec schema which my-workflow     # which of project/user/package won
openspec schema which --all
openspec templates --schema my-workflow          # resolved template path per artifact
openspec instructions <artifact> --change <name> --json   # what the assistant actually gets
```

`openspec templates` is cwd-based and ignores `--store`.

If a project schema is not picked up: confirm the directory is `openspec/schemas/<name>/` with `schema.yaml` directly inside it, and that the name has no path separators or dots. Directories with dots in the name (`.fork-staging-*`, `*.fork-backup-*`) are treated as fork temp dirs and skipped by discovery.

## Community schemas

Community schemas are distributed as standalone repositories, not vendored into OpenSpec. Install by copying the bundle into `openspec/schemas/<schema-name>/` and following that repo's README. Published examples include `intent-driven` (adds ADR review), `superpowers-bridge` (bridges to obra/superpowers execution skills, adds a retrospective artifact), `nanopm` (PM-first planning pipeline upstream of implementation), `e2e-runbooks` (capability-level test runbooks with timestamped run records), and `anvil` (TDD plus an adversarial review step emitting a `VERDICT:` line). Verify the current catalog in the project's customization docs before recommending one — the list moves.

## Manual validation checklist

Use when the CLI is unavailable:

- [ ] `schema.yaml` sits directly inside `openspec/schemas/<name>/`, and `name` matches that directory
- [ ] `version` is a positive integer; `artifacts` has at least one entry
- [ ] Every artifact has all four of `id`, `generates`, `description`, `template`
- [ ] Every `template` file exists under the schema's `templates/` directory
- [ ] No `generates` or `template` value is absolute or contains `..`
- [ ] Artifact ids are unique; every `requires` entry names an existing id
- [ ] Following `requires` from every artifact terminates (no cycle)
- [ ] An artifact with `id: specs` exists and its `generates` starts with `specs/`
- [ ] `apply.requires` lists at least one id, and `apply.tracks` points at the checkbox file
- [ ] Artifacts are declared in the order they should be written
- [ ] `rules:` keys in `openspec/config.yaml` still match this schema's artifact ids
