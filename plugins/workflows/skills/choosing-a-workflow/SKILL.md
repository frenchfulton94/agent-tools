---
name: choosing-a-workflow
description: Routes a piece of work to the right OpenSpec workflow schema among the seven this plugin installs — feature-flow, bugfix-flow, refactor-flow, spike-flow, upgrade-flow, setup-flow, and rapid-flow — or to impeccable when the work is only about how a surface looks or reads, and returns the change-creation command, the artifact chain it commits you to, and the guardrail most likely to force a reclassification later. Use when an OpenSpec change is about to be created, when asked which workflow or schema a task belongs to, when a change already underway now looks like the wrong kind of work, or on the raw request with no workflow named at all — "prod is down", "bump us past the EOL version", "extract this duplicated helper", "add tests for billing", "try both libraries and see", "fix the footer typo", "the settings page feels cluttered" — because nothing selects a schema automatically. For editing config.yaml, authoring a new schema, or CLI setup, prefer configuring-openspec.
license: MIT
compatibility: Requires the openspec CLI and a repository configured by /workflows:setup.
metadata:
  author: workflows
  version: "2.0"
---

# Choosing a workflow

Nobody remembers seven artifact chains and the work that belongs to none of them, so ask.

OpenSpec has **no schema auto-selection**. The schema is fixed at the moment a change is created, and everything downstream — which artifacts exist, which gates must pass, what apply tracks — follows from that one word. A change created without a schema silently gets the project default, `feature-flow`, whatever kind of work it actually is.

**This skill recommends and stops.** It returns the schema, the command to type, what the chain will ask, and the guardrail to watch. It does not create the change, write an artifact, or start the work.

## Preflight

Route only to a schema this repository actually has:

```bash
openspec schemas
```

- **The command is missing or errors** → the repository is not set up. Say so and point at `/workflows:setup`, then stop.
- **The seven `-flow` schemas are present** → route below.
- **Only other schemas are present** (`feature`, `hotfix`, `craft-driven`, and the like) → the repository was set up by a release before 0.10.0, which shipped two more levels. Those schemas still work and this skill no longer routes to them. Say so, and point at `/workflows:setup` to install the seven flows.
- **A schema you were about to recommend is absent** → recommend the nearest one that is present and say which is missing, rather than naming a schema that does not exist here.

Read `openspec/ROUTING.md` when it exists. A repository may have edited its own router, and the edited version wins over this skill.

## Work that never becomes a change

Check this first.

- **Surface-only work** — how a page, screen, or component looks or reads: layout, copy, colour, motion, accessibility, polish → impeccable, directly: `/impeccable <command> <surface>`. No change. Functionality the work turns out to need becomes a `feature-flow` change, which builds its own surface through impeccable.
- **An effort too big and foggy for one change** → `/wayfinder`. Its cleared map enters `feature-flow` at the proposal.
- **A survey for places to deepen the codebase** → `/improve-codebase-architecture`. Each accepted candidate becomes a `refactor-flow` change.
- **A raw bug report or feature request nobody has verified** → `/triage`. Its `ready-for-agent` briefs become changes.
- **Typos, docs, and lint fixes** → a direct commit.

`/wayfinder`, `/improve-codebase-architecture`, and `/triage` are user-invoked: offer them, because only the user can run them.

## Route — first match wins

The order is triage order, not preference. Take the first branch that matches and stop reading.

1. **Production is broken now** — incident, outage, users blocked → mitigate first (roll back or flip the flag), then `bugfix-flow` with its Incident section
2. **New repository or project bootstrap** — "init", "scaffold", "set up the project" → `setup-flow`
3. **Something behaves wrong versus intent** — bug, error, crash, regression, "too slow" → `bugfix-flow`
   - Performance work is a bugfix. A measured baseline and a numeric target come before any code changes.
4. **Dependency, framework, or platform version change** — bump, EOL, CVE, "migrate to vN" → `upgrade-flow`
5. **Structure changes but behaviour must not** — clean up, extract, rename, de-dupe, tech debt → `refactor-flow`
   - Coverage backfill is a refactor with no restructure. The guard tests are the deliverable.
6. **An open question answered by building or reading** — "try", "compare", "POC", "feasibility", "which library" → `spike-flow`
7. **New capability or intentional behaviour change**, including removals and deprecations → `feature-flow`
8. **A small code change, one decision wide, touching no contract** → `rapid-flow`

Two branches catch most misroutes. An incident is also a bug, and rule 1 comes first because mitigation comes before diagnosis. A removal feels like a deletion, and rule 7 owns it because removing a capability changes promised behaviour.

## What to return

Answer in five lines and stop. Longer than that and the person stops reading before the guardrail, which is the part that saves them.

1. **The schema**, and the rule number that chose it.
2. **The command**, filled in — never a template:
   ```
   /openspec-new-change <the work, in a sentence>, using <schema>
   ```
   Chat-native, because the rest of the chain lives there too. `/openspec-new-change` takes a kebab-case name **or** a description it derives one from, and passes `--schema` through only when a schema is named — so naming it in the sentence is what makes this routing decision stick. Give the terminal equivalent, `openspec new change <slug> --schema <schema>`, only when they are scripting or already have the slug; slugs are lowercase kebab-case, and a leading number is allowed.
3. **The chain**, as artifact ids in order, so they can see what they are committing to.
4. **The gate** — the one artifact that blocks the rest, named in `references/chains.md`.
5. **The guardrail most likely to fire**, from the list below.

For work that never becomes a change, the answer is shorter: where it goes, the command, and what would turn it into a change.

Then offer the next step rather than taking it: creating the change is one command, and it is theirs to run. If they ask what follows, it is `/openspec-continue-change <change>` once per artifact — one line, not a walkthrough.

When two branches genuinely both match, ask **one** multiple-choice question naming the two candidates and what distinguishes them, then route. Do not route on a guess and do not present a survey.

## Guardrails — the reclassifications

Routing is not a decision to defend. Say which of these is most likely to fire, because the cost of missing one is an entire chain done under the wrong discipline.

- **`rapid-flow` → `feature-flow`** the moment a contract appears (specified behaviour, a public API, a data schema, a config key) or a decision grows real alternatives. Stop and recreate.
- **`refactor-flow` → `feature-flow`** when a guard assertion at the external seam has to change. Shallow tests are replaced by design, so only guard tests count.
- **`bugfix-flow` → `feature-flow`** when the fix changes promised behaviour rather than restoring it.
- **`upgrade-flow` → `feature-flow`** for any deliberate behaviour change; an unknown surface gets a `spike-flow` change first.
- **`spike-flow`** code is throwaway and never merges. Learnings graduate through a new `feature-flow` change.
- **Any flow → impeccable** for the surface: a flow builds up to its presentation seam and calls impeccable for everything in front of it. A flow that starts writing surface code itself has left its lane.

De-escalate as readily as you escalate. A `feature-flow` grill that shrinks to one decision should be recreated as `rapid-flow`; one that reveals a question in disguise, as `spike-flow`. One command against hours of ceremony.

## Where to look

- `references/chains.md` — the seven chains: artifacts and their real `requires` edges, the gate, the escape hatches, which skill each step calls, and the subagent it dispatches. Load once a schema is chosen and the person wants to run it, or to fill in the chain and gate lines of the answer above.
- `references/model-effort.md` — which model and effort each phase wants, the one pin that already executes, and the two settings that silently defeat it. Load when asked about models, effort, cost, or why a gate produced something shallow.

For configuring OpenSpec itself — `config.yaml` fields, authoring a schema, `.openspec.yaml`, CLI setup, or a config that is being ignored — hand over to `configuring-openspec` rather than answering here.

## Guardrails for this skill

- **Never invent a schema name.** Seven exist. If nothing fits, say the work does not match any installed schema and name the closest.
- **Route on the work, not the words.** "Add tests" sounds like new work and is a `refactor-flow`; "make it faster" sounds like a feature and is a `bugfix-flow`; "rework the layout" sounds like a feature and is impeccable's. The classification follows what changes, not how the request is phrased.
- **Recommend, then stop.** Creating the change, writing an artifact, and starting the work are separate acts the person chooses. This skill ends at the command.
