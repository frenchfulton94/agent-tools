# OpenSpec Change-Type Schema Set

Eight OpenSpec schemas organized by **change type**, plus a router the agent reads
before creating a change. This set **replaces** the earlier
greenfield/brownfield/rapid set: `feature` absorbs greenfield and brownfield
(its constraints and migration artifacts scale from near-trivial for net-new
code to full rigor for existing systems), and `rapid` carries over unchanged.

## Which schema, when

| Schema   | Use when                                                                   | Artifact chain                                                                                          |
| -------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| setup    | Bootstrapping a new repository/project                                     | decisions → conventions → tasks                                                                         |
| feature  | New capability or intentional behavior change, incl. removals/deprecations | brainstorm → constraints → proposal → specs → design → migration → review → tasks → plan → verification |
| bugfix   | Behavior deviates from intent (incl. performance regressions)              | reproduction → rootcause → fix → tasks                                                                  |
| refactor | Structure changes, behavior must not (incl. coverage backfill)             | characterization → strategy → tasks                                                                     |
| spike    | Timeboxed exploration to answer one question                               | question → findings                                                                                     |
| upgrade  | Dependency / framework / platform version change                           | inventory → surfaces → migration → tasks → verification                                                 |
| hotfix   | Production incident: ship first, document after                            | triage → tasks → postmortem                                                                             |
| rapid    | Tiny, low-risk change with no contract impact                              | proposal → tasks                                                                                        |

## Install

    cp -r schemas/* your-project/openspec/schemas/
    cp config.yaml   your-project/openspec/config.yaml   # merge if one exists
    # Append ROUTING.md to your AGENTS.md (or paste it into config `context`)

Validate after copying (CLI behavior varies by version):

    openspec schema validate feature   # repeat per schema

## Routing

OpenSpec has no built-in schema auto-selection: the schema is chosen at change
creation, by naming it. The agent can route correctly only if it reads ROUTING.md
before creating a change — install it where your agent reads instructions
(AGENTS.md / CLAUDE.md / config context).

    /opsx:new <the work, in a sentence>, using <schema>   # chat; derives the slug
    openspec new change <slug> --schema <schema>          # terminal; you write the slug

Then `/opsx:continue <change>` per artifact, and before implementing: `/clear`,
`/model` or `/effort`, `/opsx:apply <change>`.

Guardrails baked into the set: rapid escalates to feature the moment a public
contract is touched; spike code never merges; hotfix always spawns a follow-up
bugfix or feature change. Post-apply artifacts (spike findings, hotfix
postmortem) are gated by checkboxes in the tracked file, because the CLI's
archive warning counts tracked checkboxes, not artifact files.

## Standing documents and their owning skills

| Standing doc                          | Owning skill                                    | Read by                               |
| ------------------------------------- | ----------------------------------------------- | ------------------------------------- |
| CONTEXT.md (domain language)          | mattpocock-skills:domain-modeling                      | feature constraints                   |
| TOOLS.md (stack/command facts)        | mapping-project-tooling (user-installed)        | feature constraints, upgrade surfaces |
| AGENTS.md / CLAUDE.md (+ this router) | managing-project-memory (user-installed)        | every change, at session start        |
| DESIGN.md (design tokens)             | impeccable                                      | feature design                        |
| docs/GLOSSARY.md (bound terms)        | controlled-engineering-english (user-installed) | all prose-bearing artifacts           |

## Skill integration

Every schema invokes installed skills by name where one applies, drawn from
obra/superpowers, addyosmani/agent-skills, mattpocock/skills, impeccable,
taste-skill, the design-engineering plugin, and three user-installed skills
(managing-project-memory, controlled-engineering-english,
mapping-project-tooling). Pack skills are
written pack:skill; user-installed skills by bare name - confirm exact
prefixes in your agent's skill list. Every invocation carries a fallback
chain and degrades to the template when the skill is absent. Design credit
for the bridge pattern: JiangWay's superpowers-bridge (prior art, reused
not copied).

Motion is split out because nothing else in the set covers it. Impeccable
and taste-skill judge the static surface - tokens, contrast, palette, copy -
and neither has an opinion on whether an element should animate, how long,
or on what curve. `animating-interfaces` settles that at design time,
`apple-design` covers gesture-driven surfaces, and `reviewing-animations`
checks the result - at the design document in the pre-flight, and again at
the diff and the running interaction in verification, because a still frame
shows neither duration nor easing. They are installed only on web projects,
so on a backend repo the motion clauses simply never fire.

Two more ship with that plugin and are deliberately not wired into any
artifact: `improving-animations` surveys a whole codebase's motion into
plans, and `finding-animation-opportunities` sweeps for motion that is
missing. Both produce work rather than living inside a change, so they run
the way `/improve-codebase-architecture` does - ahead of the chain, with
each accepted plan becoming its own change. They are model-invoked, so
unlike that command they need no router line to be reachable; ask for a
motion audit and they fire.
