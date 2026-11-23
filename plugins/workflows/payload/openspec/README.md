# Seven flows, each job given to the skill that does it best

OpenSpec owns which documents a change has, validates them, and merges
behaviour into `openspec/specs/`. Matt Pocock's skills (mattpocock-skills 1.3.2)
own how a change is decided, named, designed, sliced, tested, and diagnosed.
Addy Osmani's agent-skills (0.6.17) do the six jobs Pocock's set has no skill
for. Impeccable (4.10.0) does all surface work.

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

1. The mattpocock-skills, agent-skills, and impeccable plugins.
   `/workflows:setup` enables all three, and nothing else.
2. `/setup-matt-pocock-skills`, run once by a human, so `docs/agents/` exists.
3. On a project with a user interface: `/impeccable init`, once. A flow stops
   rather than build a surface without impeccable.

## What the flows call

From mattpocock-skills, through the Skill tool: grilling, domain-modeling,
codebase-design, prototype, research, diagnosing-bugs, tdd, code-review, pr, and
wizard. Its user-invoked skills are offered to the human because no skill can
call them: `/triage`, `/wayfinder`, `/improve-codebase-architecture`,
`/to-tickets`, `/implement-spec`, `/grill-with-docs`,
`/setup-matt-pocock-skills`, and `/retro`.

From agent-skills, through the Skill tool, each at one fixed point:

| Skill | Job | Why not Pocock's |
|---|---|---|
| security-and-hardening | Threat model at specs, when a change crosses a trust boundary | No security skill |
| doubt-driven-development | A fresh reviewer attacks the design before sign-off | No design challenge |
| code-review-and-quality | One defect-hunting review per change, tests first | code-review checks standards and spec, not correctness |
| performance-optimization | Baseline, then keep or revert, for a performance fix | No measurement discipline |
| source-driven-development | Code written from current official documentation | research gathers facts; nothing binds the code to them |
| constraint-driven-development | CONSTRAINTS.md and gates proven to fail | No quality-bar skill |

The rest of agent-skills is deliberately not called. Its interview, planning,
TDD, and debugging skills overlap Pocock's stronger ones, and two skills at one
step compete.

From impeccable, through the Skill tool: `shape`, the surface build, `audit`,
`polish`, `extract`, `generate`, and `init`. `ROUTING.md` lists the point each
runs at.

The `flow-design` agent drafts the design artifact for `feature-flow` and
`refactor-flow` on the top model, so the planning session can stay cheaper.

## Escape hatches

- `skip_specs: true` in a `bugfix-flow` change whose spec already covered the
  case. OpenSpec sets it by itself for a schema with no `specs` artifact.
- `retire_capabilities: true` when a change removes a capability's last
  requirement.
- Skipping an interview writes a one-line stub file holding the reason and the
  date. The CLI reads no other skip flag.

## Upgrading from an earlier release

Earlier releases shipped a single bridge schema, then two further levels
(`standard` and `advanced`) beside this one. Their schemas and agents are listed
in the plugin's `retired.json`. Setup offers to delete each one only when this
plugin installed it, nobody has edited it, and no open change still uses it;
anything else stays and keeps working. `bugfix-flow` keeps its name and its
`diagnose` artifact, so in-flight bugfix changes keep resolving.
