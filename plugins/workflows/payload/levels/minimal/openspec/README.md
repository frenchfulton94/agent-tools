# The minimal level: seven flows driven by Matt Pocock's skills

OpenSpec schemas whose every artifact is driven by a skill from
mattpocock-skills 1.3.1. OpenSpec owns which documents a change has and how
behaviour merges into `openspec/specs/`. The skills own how a change is decided,
named, tested, built, and reviewed. Impeccable owns UI/UX.

| Schema | Use when | Chain |
|---|---|---|
| `feature-flow` | A new capability or intentional behaviour change (the default) | grill → proposal → specs → design → tasks |
| `bugfix-flow` | Behaviour deviates from spec or intent; incidents after mitigation | diagnose → specs → tasks |
| `refactor-flow` | Structure changes and external behaviour must not | grill → design → tasks |
| `spike-flow` | A timeboxed question answered by building or reading | question → findings |
| `upgrade-flow` | A dependency, framework, or platform version change | inventory → surfaces → tasks |
| `setup-flow` | Bootstrapping a new project | decisions → tasks |
| `rapid-flow` | A small code change, one decision wide, touching no contract | proposal → tasks |

`ROUTING.md` picks between them. `/workflows:setup` installs the schemas, the
`flow-design` agent, the router, and the config.

## Prerequisites

1. The mattpocock-skills plugin. `/workflows:setup` enables it.
2. `/setup-matt-pocock-skills`, run once by a human, so `docs/agents/` exists.
3. On a project with a user interface: impeccable, set up with `/impeccable init`.

## What the flows call

Model-invoked skills, called through the Skill tool: grilling, domain-modeling,
codebase-design, prototype, research, diagnosing-bugs, tdd, code-review, pr, and
wizard. User-invoked skills, offered to the human because no skill can call
them: `/triage`, `/wayfinder`, `/improve-codebase-architecture`, `/to-tickets`,
`/implement-spec`, `/grill-with-docs`, `/setup-matt-pocock-skills`, and `/retro`.

The `flow-design` agent drafts the design artifact for `feature-flow` and
`refactor-flow` on the top model, so the planning session can stay cheaper.

## Escape hatches

- `skip_specs: true` in a `bugfix-flow` change whose spec already covered the
  case. OpenSpec sets it by itself for a schema with no `specs` artifact.
- `retire_capabilities: true` when a change removes a capability's last
  requirement.
- Skipping an interview writes a one-line stub file holding the reason and the
  date. The CLI reads no other skip flag.

## Upgrading from the previous minimal level

The previous level shipped a single feature schema and three agents, now
listed in `../retired.json`. Setup offers to delete each one only when this
plugin installed it, nobody has edited it, and no open change still uses it.
`bugfix-flow` keeps its name and its `diagnose` artifact, so in-flight bugfix
changes keep resolving.
