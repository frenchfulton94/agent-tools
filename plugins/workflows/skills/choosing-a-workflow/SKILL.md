---
name: choosing-a-workflow
description: Routes a piece of work to the right OpenSpec workflow schema among the seventeen this plugin installs — advanced's feature, bugfix, refactor, rapid, setup, spike, upgrade, hotfix; minimal's seven -flow schemas driven by Matt Pocock's skills; standard's craft-driven and surface-driven — and returns the change-creation command, the artifact chain it commits you to, and the guardrail most likely to force a reclassification later. Use when an OpenSpec change is about to be created, when asked which workflow or schema a task belongs to, when a change already underway now looks like the wrong kind of work, or on the raw request with no workflow named at all — "prod is down", "bump us past the EOL version", "extract this duplicated helper", "add tests for billing", "try both libraries and see", "fix the footer typo" — because nothing selects a schema automatically. For editing config.yaml, authoring a new schema, or CLI setup, prefer configuring-openspec.
license: MIT
compatibility: Requires the openspec CLI and a repository configured by /workflows:setup.
metadata:
  author: workflows
  version: "1.1"
---

# Choosing a workflow

Nobody remembers seventeen artifact chains, so ask.

OpenSpec has **no schema auto-selection**. The schema is fixed at the moment a change is created, and everything downstream — which artifacts exist, which gates must pass, what apply tracks — follows from that one word. A change created without a schema silently gets the project default, whatever kind of work it actually is.

**This skill recommends and stops.** It returns the schema, the command to type, what the chain will ask, and the guardrail to watch. It does not create the change, write an artifact, or start the work.

## Preflight

Route only to a schema this repository actually has:

```bash
openspec schemas
```

- **The command is missing or errors** → the repository is not set up. Say so and point at `/workflows:setup`, then stop.
- **Schemas ending in `-flow`** (`feature-flow`, `bugfix-flow`, and the rest) → this is `minimal`. Use "Route — `minimal`" below.
- **`craft-driven` and `surface-driven`** → this is `standard`. Use the two-way call below.
- **`feature`, `bugfix`, and the rest of the advanced eight** → this is `advanced`. Use the tree.
- **Sets from more than one level** → setup adds a level beside the last one rather than replacing it. Route with the set that holds `openspec/config.yaml`'s `schema:` default, and say the other set is installed too.
- **A schema you were about to recommend is absent** → recommend the nearest one that is present and say which is missing, rather than naming a schema that does not exist here.

Read `openspec/ROUTING.md` (or wherever memory holds it) when it exists — a repository may have edited its own router, and the edited version wins over this skill.

## Route — `advanced`, first match wins

The order is triage order, not preference. Take the first branch that matches and stop reading.

1. **Production is broken now** — incident, outage, users blocked → `hotfix`
2. **New repository or project bootstrap** — "init", "scaffold", "set up the project" → `setup`
3. **Something behaves wrong versus intent** — bug, error, crash, regression, "too slow" → `bugfix`
   - Performance work is a bugfix. A measured baseline and a numeric target come before any code changes.
4. **Dependency, framework, or platform version change** — bump, EOL, CVE, "migrate to vN" → `upgrade`
5. **Structure changes but behaviour must not** — clean up, extract, rename, de-dupe, tech debt → `refactor`
   - Coverage backfill is a refactor. Characterization is the deliverable.
6. **An open question answered by building** — "try", "compare", "POC", "feasibility", "which library" → `spike`
7. **New capability or intentional behaviour change**, including removals and deprecations → `feature`
8. **Trivial, low-risk, no contract impact** — typo, copy, config value, docs → `rapid`

Two branches catch most misroutes. An incident is also a bug, and rule 1 wins because production is down. A removal feels like a deletion, and rule 7 owns it because removing a capability changes promised behaviour.

## Route — `minimal`

Walk `openspec/ROUTING.md`. Its tree keeps the order of the one above, with `-flow` names, two different rules, and one addition:

- **Rule 1 differs.** Production broken now → mitigate first (roll back or flip the flag), then `bugfix-flow` with its Incident section. There is no `hotfix` chain.
- **Rule 8 differs.** A small code change touching no contract → `rapid-flow`. Typos, docs, and lint fixes are a direct commit with no change.
- **UI/UX-led work** (look, feel, layout, copy, accessibility, polish) goes to impeccable, not to a flow. Functionality it turns out to need becomes a `feature-flow` change.

If `ROUTING.md` is missing, use the tree above and map each schema to its `-flow` twin.

## Route — two-way call at `standard`

`standard` ships no router; with two schemas, one question decides it.

| Repo has | Default | The other one | The question |
|---|---|---|---|
| `craft-driven`, `surface-driven` | `craft-driven` | `surface-driven` | Is the change *primarily* a user-facing surface — landing page, dashboard, flow, redesign, component system? Then design leads |

The default is already in `openspec/config.yaml`, so recommending it still means naming it out loud — the person needs to know which chain they are entering, not just that they can omit a flag.

## What to return

Answer in five lines and stop. Longer than that and the person stops reading before the guardrail, which is the part that saves them.

1. **The schema**, and the rule number or question that chose it.
2. **The command**, filled in — never a template:
   ```
   /opsx:new <the work, in a sentence>, using <schema>
   ```
   Chat-native, because the rest of the chain lives there too. `/opsx:new` takes a kebab-case name **or** a description it derives one from, and passes `--schema` through only when a schema is named — so naming it in the sentence is what makes this routing decision stick. Give the terminal equivalent, `openspec new change <slug> --schema <schema>`, only when they are scripting or already have the slug; slugs are lowercase kebab-case, and a leading number is allowed.
3. **The chain**, as artifact ids in order, so they can see what they are committing to.
4. **The gate** — the one artifact that blocks the rest, named in `references/chains.md`.
5. **The guardrail most likely to fire**, from the list below.

Then offer the next step rather than taking it: creating the change is one command, and it is theirs to run. If they ask what follows, it is `/opsx:continue <change>` once per artifact — one line, not a walkthrough.

When two branches genuinely both match, ask **one** multiple-choice question naming the two candidates and what distinguishes them, then route. Do not route on a guess and do not present a survey.

## Guardrails — the reclassifications

Routing is not a decision to defend. Say which of these is most likely to fire, because the cost of missing one is an entire chain done under the wrong discipline.

- **`rapid` → `feature`** the moment a public API, URL, analytics event, data schema, or config contract is touched, or the change turns out non-trivial. Stop and recreate.
- **`refactor` → `feature`** if any test assertion has to change. A changed assertion means behaviour changed, so this was never a refactor.
- **`rapid-flow`, `refactor-flow`, `bugfix-flow`, `upgrade-flow` → `feature-flow`** at `minimal`: a contract or a real decision appears in a rapid change; a guard assertion at the external seam has to change in a refactor (shallow tests are replaced by design, so only guard tests count); a fix changes promised behaviour rather than restoring it; an upgrade turns out to need a deliberate behaviour change.
- **`spike`** and **`spike-flow`** code is throwaway and never merges. Learnings graduate through a new `feature` or `feature-flow` change.
- **`hotfix`** must spawn a follow-up `bugfix` or `feature` for the durable fix, linked from `postmortem.md`.

De-escalate as readily as you escalate. A `feature` brainstorm that reveals bounded work should be recreated as `rapid`; one that reveals a question in disguise, as `spike`. One command against hours of ceremony. At `minimal`, the same moves land on `rapid-flow` and `spike-flow`.

## When it is not one change

- **An epic, too big for one change.** A change is a single unit of work. Where the mattpocock pack is installed, ask the user to run `/wayfinder` — it is user-invoked, so only they can fire it — to map the effort as decision tickets. At `minimal`, the cleared map enters `feature-flow` at its proposal; elsewhere, create one change per resolved chunk.
- **A codebase-wide cleanup.** `/improve-codebase-architecture` (also user-invoked) surfaces opportunities; each accepted one becomes its own `refactor` change, or `refactor-flow` at `minimal`.
- **UI/UX-led work at `minimal`** goes to impeccable, not to a change; see "Route — `minimal`".
- **Standing-doc upkeep** — a `CLAUDE.md` audit, a `TOOLS.md` refresh, glossary maintenance — routes to `rapid` at `advanced` and invokes the owning skill: `managing-project-memory`, `mapping-project-tooling`, or `controlled-engineering-english`. At `minimal` it is a direct commit.

## Where to look

- `references/chains.md` — all seventeen chains: artifacts and their real `requires` edges, the gate, the escape hatches, and the subagents each dispatches. Load once a schema is chosen and the person wants to run it, or to fill in the chain and gate lines of the answer above.
- `references/model-effort.md` — which model and effort each phase wants, the six pins that already execute, and the two settings that silently defeat them. Load when asked about models, effort, cost, or why a gate produced something shallow.

For configuring OpenSpec itself — `config.yaml` fields, authoring a schema, `.openspec.yaml`, CLI setup, or a config that is being ignored — hand over to `configuring-openspec` rather than answering here.

## Guardrails for this skill

- **Never invent a schema name.** Seventeen exist: seven at `minimal`, two at `standard`, and eight at `advanced` (plus `app-release` in Apple-native app repos). If nothing fits, say the work does not match any installed schema and name the closest.
- **Route on the work, not the words.** "Add tests" sounds like new work and is a `refactor`; "make it faster" sounds like a feature and is a `bugfix`. The classification follows what changes, not how the request is phrased.
- **Recommend, then stop.** Creating the change, writing an artifact, and starting the work are separate acts the person chooses. This skill ends at the command.
