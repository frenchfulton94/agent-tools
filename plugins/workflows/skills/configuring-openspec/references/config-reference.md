# OpenSpec Configuration Reference

Contents:
- [The three config surfaces](#the-three-config-surfaces)
- [Project config: openspec/config.yaml](#project-config-openspecconfigyaml)
- [How context and rules are injected](#how-context-and-rules-are-injected)
- [Resilient parsing: what happens to bad fields](#resilient-parsing-what-happens-to-bad-fields)
- [Change metadata: .openspec.yaml](#change-metadata-openspecyaml)
- [Machine config: openspec config](#machine-config-openspec-config)
- [Precedence rules](#precedence-rules)
- [Recipes](#recipes)
- [Manual validation checklist](#manual-validation-checklist)

## The three config surfaces

| Surface | Path | Edited by | Scope |
|---|---|---|---|
| Project config | `openspec/config.yaml` | Hand, or `openspec init` | One repo |
| Change metadata | `openspec/changes/<change>/.openspec.yaml` | Hand, or `openspec new change` | One change |
| Machine config | `~/.config/openspec/config.json` (XDG; `%APPDATA%` on Windows) | `openspec config` subcommands | Every project on this machine |

`openspec config set …` writes the **machine** config. It cannot set `schema:` or `context:` for a project — those live in `openspec/config.yaml` and are edited directly.

## Project config: openspec/config.yaml

Only these top-level keys exist. Anything else is ignored without comment.

| Key | Type | Required | Notes |
|---|---|---|---|
| `schema` | string | Effectively yes | Default workflow schema for new changes. Non-empty. |
| `context` | string | No | Injected into **every** artifact's instructions. Hard cap 50KB. |
| `rules` | map of string → string[] | No | Keyed by artifact id; injected only for that artifact. |
| `operations` | object | No | `apply` and `archive` only, each with a `guidance: [string]` array. |
| `references` | array | No | Referenced store ids (beta). String entries or `{id, remote}` maps. |
| `store` | string | No | Declares a default store for a config-only repo (beta). |
| `githubCopilot` | object | No | `cloudAgent: true\|false`. Set by `openspec init`'s prompt. |

A representative file:

```yaml
schema: spec-driven

context: |
  Tech stack: TypeScript, React 18, Node.js 20, PostgreSQL via Prisma
  Testing: Vitest for unit, Playwright for e2e
  API: RESTful, documented in docs/api.md
  We maintain backwards compatibility for all public APIs

rules:
  proposal:
    - Include a rollback plan for risky changes
    - Identify affected teams
  specs:
    - Use Given/When/Then for scenarios
    - Reference existing patterns before inventing new ones
  design:
    - Include a sequence diagram for cross-service flows
  tasks:
    - Keep each task completable in one session

operations:
  apply:
    guidance:
      - Run focused tests before the full suite
  archive:
    guidance:
      - Keep the completion summary concise
```

**Only the file at `openspec/config.yaml` (or `openspec/config.yml`, probed second) is read.** A `.yml` file in the repo root, or a `config.yaml` one directory up, is invisible.

### operations vs rules

They are deliberately distinct and are never relabeled into each other:

- `rules` constrain **artifact content**, and reach only the artifact whose id matches the key.
- `operations.<apply|archive>.guidance` is **advisory** input for how an agent conducts that operation. Agents consider every entry and follow only those applicable and compatible with the built-in workflow; conflicting or inapplicable guidance is skipped with an explanation. Neither field is an enforceable check.

Both are fetched fresh at execution time:

```bash
openspec instructions apply   --change my-feature --json
openspec instructions archive --change my-feature --json
```

`instructions archive` is read-only: it returns `context` and `operationGuidance` and does not inspect deltas, write specs, or move anything.

### references and store (stores beta)

```yaml
references:
  - team-plans
  - { id: platform-reqs, remote: "git@github.com:acme/platform-reqs.git" }
```

References are read-only context. They add an index of the referenced store's specs — id, one-line summary, and the exact `openspec show <spec-id> --type spec --store <id>` fetch command — to `openspec instructions` output. They never change where a command acts, and spec content is never copied in. An unresolvable reference degrades to a warning with a pasteable clone-and-register fix. The index shares the 50KB budget and truncates (`reference_index_truncated`) beyond it.

```yaml
# Only for a repo whose planning is fully externalized (no local specs/ or changes/)
store: team-plans
```

The `store:` pointer is a fallback, never an override: `--store` wins, and a directory with real planning folders ignores the pointer with a warning. `openspec init` refuses to scaffold while the pointer is present.

Do not confuse the `context:` **field** (project background injected into instructions) with the `openspec context` **command** (which assembles the working set of root plus referenced stores).

## How context and rules are injected

The assistant receives, per artifact:

```xml
<context>
…the project config's context field, verbatim…
</context>

<rules>
- …only the rules whose key matches this artifact id…
</rules>

<template>
…the schema's template file for this artifact…
</template>
```

Consequences worth stating to users:

- Context appears in every request, so cost scales with its length. Summarize; link out rather than pasting long docs.
- Rules are cheap because they are scoped, so artifact-specific guidance belongs in `rules`, not `context`.
- Neither should ever be copied into the generated file. If `<context>` blocks show up inside `proposal.md`, that is an assistant-side error, not a config error.

## Resilient parsing: what happens to bad fields

`readProjectConfig` validates each field independently with `safeParse` and drops what fails, keeping the rest. Every drop emits a `console.warn` — visible in terminal output, easy to miss when a command's output is piped or read by an agent.

| Situation | Behavior |
|---|---|
| `schema` not a non-empty string | Dropped, warning; schema falls back down the precedence chain |
| `context` over 50KB | **Entire field dropped**, warning naming the size |
| `context` not a string | Dropped, warning |
| `rules` not an object | Dropped, warning |
| One artifact's rules not an array of strings | That artifact's rules dropped, others kept |
| Empty strings inside a rules array | Filtered out, warning |
| `rules` key matching no artifact in **any** available schema | Kept, but `validateConfigRules` warns "Unknown artifact ID in rules: X" |
| Unknown key under `operations.<id>` | Warning naming supported field (`guidance`) |
| Unknown operation id | Warning listing supported ids (`apply`, `archive`) |
| Invalid `references` entry | Dropped, warning; valid entries kept |
| File is unparseable YAML | Whole config ignored with a warning; commands continue with defaults |

Because a malformed pointer would silently move where work lands, the `store:` key is read by a separate strict path that reports rather than drops it.

**Diagnostic move:** when a config appears ignored, run a command in a plain terminal (not piped) and read stderr, then confirm with `openspec instructions <artifact> --change <name> --json` that `context` and `rules` are present in the payload.

## Change metadata: .openspec.yaml

Lives inside a change folder. Created by `openspec new change`; edited by hand for the two declarations.

| Field | Type | Notes |
|---|---|---|
| `schema` | string | Required. Which workflow schema this change uses. |
| `created` | string | `YYYY-MM-DD`. |
| `goal` | string | Non-empty when present. |
| `affected_areas` | string[] | Non-empty strings. |
| `initiative` | `{store, id}` | Both kebab-case. Strict object — no extra keys. |
| `skip_specs` | boolean | This change intentionally has no spec deltas. |
| `retire_capabilities` | boolean | Allow archive to delete a capability's spec file. |

```yaml
schema: spec-driven
skip_specs: true
```

`skip_specs: true` is for pure refactors, tooling, and docs work. Without it, `openspec validate` rejects a change with zero deltas; with it, `openspec status` renders the specs stage as `[~] specs (skipped: change declares skip_specs)` and excludes it from the progress count. Declaring the marker *and* writing spec files is a validation conflict, so a stale marker cannot linger unnoticed. Archiving a marked change needs no extra flag.

`retire_capabilities: true` is required when a change's `REMOVED` entries take a capability's last requirement — archive then deletes `openspec/specs/<capability-path>/spec.md` instead of aborting. It is opt-in because the deletion is recoverable only from git; archive names each retirement in its warnings and, for a spec in the caller's checkout, prints the restoring `git checkout`.

## Machine config: openspec config

```bash
openspec config path                       # where the JSON config lives
openspec config list
openspec config get telemetry.enabled
openspec config set telemetry.enabled false
openspec config set user.name "My Name" --string
openspec config unset defaultStore
openspec config edit                       # opens $EDITOR
openspec config profile                    # interactive profile/delivery wizard
openspec config profile core               # fast preset
openspec config reset --all --yes
```

Recognized keys include `profile` (`core` | `custom`), `delivery` (`both` | `skills` | `commands`), `workflows` (string array), `defaultStore`, `openers` (workset launchers), and `telemetry`.

Telemetry is opt-out and collects command name and version only. `OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1`, and a truthy `CI` override the config value. The same signals disable the `openspec update` version check.

`openspec config profile` writes config only — run `openspec update` in each project to apply the selection to that project's files.

## Precedence rules

**Which schema a change uses:**

1. `--schema <name>` on the command
2. The change's `.openspec.yaml`
3. `openspec/config.yaml`
4. `spec-driven`

**Where a schema's files are found:**

1. Project: `openspec/schemas/<name>/`
2. User: `~/.local/share/openspec/schemas/<name>/`
3. Package built-ins

**Which OpenSpec root a command acts on:**

1. `--store <id>` → that store (`source: "store"`)
2. Nearest ancestor `openspec/` with planning shape → that repo (`source: "nearest"`; a `store:` pointer there is ignored with a warning)
3. Config-only dir with a valid `store:` pointer → that store (`source: "declared"`)
4. Machine `defaultStore` → that store (`source: "global_default"`)
5. Otherwise: error if stores are registered, else the cwd (`source: "implicit"`)

Human-mode commands print `Using OpenSpec root: <id> (<path>)` to stderr; `--json` payloads carry a `root` block with the same `source`.

## Recipes

### Teach OpenSpec your stack

Put durable, always-relevant facts in `context`; put artifact-shaped guidance in `rules`. Good candidates for `context`: languages and frameworks, architectural pattern, non-obvious constraints ("we cannot use library X because …"), conventions that get ignored otherwise. Leave out general best practices the model already knows.

### Generate artifacts in another language

Language is an ordinary context instruction — there is no `language:` key.

```yaml
context: |
  Language: Portuguese (pt-BR)
  All artifacts must be written in Brazilian Portuguese.
  Keep technical terms like "API", "REST", and "GraphQL" in English;
  code examples and file paths remain in English.

  Tech stack: TypeScript, React, Node.js
```

Verify with `openspec instructions proposal --change <name>` and confirm the language line appears in the context block.

### Migrating a legacy openspec/project.md

`project.md` is never deleted automatically because it may hold hand-written content. Distill it: durable stack and constraint facts into `context`, artifact-specific formatting into `rules`, and drop generic advice entirely. Delete the file once moved. The reason for the change is reliability — `project.md` was passively read, while `context` is actively injected into every planning request.

## Manual validation checklist

Use when the CLI is unavailable:

- [ ] The file is at `openspec/config.yaml` (or `.yml`), not the repo root
- [ ] It parses as YAML and the root is a mapping
- [ ] Only the seven known top-level keys are present
- [ ] `schema` names a schema that exists (`openspec schemas` when available)
- [ ] `context` is a single string (block scalar `|`) and comfortably under 50KB
- [ ] Every `rules` key matches an artifact id in the schema that change will use
- [ ] Every `rules` value is a list of non-empty strings
- [ ] `operations` contains only `apply` and/or `archive`, each with only `guidance`
- [ ] No `<context>` or `<rules>` blocks have been copied into any generated artifact
