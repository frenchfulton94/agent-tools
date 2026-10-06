# Model and effort per phase

Which model and effort a phase of a change wants, what is already pinned in files, and the
two settings that silently defeat every pin.

Contents:

- [The rule](#the-rule)
- [The six pins](#the-six-pins)
- [What is recommended](#what-is-recommended)
- [Tier changes the budget, not the pick](#tier-changes-the-budget-not-the-pick)
- [Two silent defeats](#two-silent-defeats)
- [Answering a model question](#answering-a-model-question)

## The rule

1. **Planning gets depth.** Specs, root cause, refactor strategy, migration plan — durable
   multi-step judgement at the lowest token volume in the chain. A wrong plan is the most
   expensive error there is.
2. **Implementation gets speed.** Apply is a long loop of edits, commands, and test runs:
   latency- and output-dominated. The cheap tier wins, except where the implementation is
   genuinely hard (novel behaviour, a tricky migration).
3. **Interactive means `high`, not `xhigh`.** When the reasoning happens between short
   turns — a grill round, a shape interview, a seam sign-off — the top setting mostly buys
   latency the user sits through. Reserve `xhigh` for deep artifacts that run without a
   human in the loop.
4. **Escalate on evidence.** A shallow spec from a strong model, or repeated rework from a
   cheap implementation pass, justifies going up. Nothing else does — spraying the top
   setting across a chain multiplies cost without commensurate quality.

Effort values are `low`, `medium`, `high`, `xhigh`, `max`; available levels depend on the
model. Model values are `haiku`, `sonnet`, `opus`, `fable`, a full model id, or `inherit`.

## The six pins

These are `model:` and `effort:` lines in agent files this plugin installs. They execute
whether or not anyone reads this file.

| Level | Agent | Runs at | Model | Effort |
|---|---|---|---|---|
| `minimal` | `flow-design` | `feature-flow` and `refactor-flow` · design | `opus` | `xhigh` |
| `standard` | `craft-design-gate` | `craft-driven` · design | `opus` | `xhigh` |
| `standard` | `verification-reviewer` | `craft-driven` · verification step 3 | `opus` | `xhigh` |
| `advanced` | `design-gate` | `feature` · design | `opus` | `xhigh` |
| `advanced` | `review-gate` | `feature` · review | `opus` | `xhigh` |
| `advanced` | `taste-preflight` | `feature` · review, UI pre-flight | `sonnet` | `medium` |

Three patterns, all deliberate:

- **Every design gate is top tier at `xhigh`.** The `design` artifact only exists when the
  change is cross-cutting, adds a dependency, or carries security or migration complexity —
  so the trigger *is* the tier signal. When the artifact exists at all, it is the hard case.
  At `minimal`, design always exists but shrinks to the Seams table for a one-module change;
  `flow-design` stays pinned because the hard cases still arrive there.
- **Review splits differently per level.** At `advanced`, `taste-preflight` is a cheap
  mechanical pass and the review gate is judgement. At `minimal`, review is `code-review`'s
  own two sub-agents on the session's model, which is why apply tells the user to review
  from a fresh session on a strong model.
- **The expensive work is pushed out of the main session on purpose.** The schemas say so:
  dispatch the gate "so this session can stay on the cheap tier".

## What is recommended

For `standard`, a per-artifact recommendation exists and agrees with the pins above almost
exactly:

| Artifact | `craft-driven` | `surface-driven` |
|---|---|---|
| opening | brainstorm · Opus high | design-brief · Opus high for a new visual world, Sonnet medium for a refinement |
| proposal | Opus high | Sonnet medium |
| surface / design-brief | Sonnet medium, Opus high for a new world | (leads) |
| specs | Opus high | Sonnet medium, Opus high if the surface is broad |
| design | top tier xhigh | — |
| tasks | Opus high | Opus high |
| apply | Sonnet workers, Haiku mechanical, Opus on BLOCKED | Sonnet medium; surface tasks stay off Haiku |
| review | (in verification) | (in quality) |
| closing gate | verification Sonnet medium plus an Opus xhigh reviewer | quality Sonnet medium, Opus high verdict on a large redesign |

For the `minimal` seven, the rows follow the `advanced` table below for the same kind of
work, plus the `flow-design` pin:

| Flow | Planning | Implementation |
|---|---|---|
| `feature-flow` | Opus high — **xhigh at design, through the `flow-design` pin** | Sonnet medium; review from a fresh session on Opus high |
| `bugfix-flow` | **Opus xhigh at diagnose** — root cause | Sonnet medium; Opus high review when the fix touched shared code |
| `refactor-flow` | Opus high — **xhigh at design, through the pin** | Sonnet medium; Haiku for mechanical migrate batches |
| `upgrade-flow` | Opus high; `research` runs in the background | Sonnet medium; Haiku for codemod batches |
| `setup-flow` | Opus high | Sonnet medium |
| `spike-flow` | Sonnet low–medium | Sonnet medium |
| `rapid-flow` | Sonnet low–medium | Sonnet medium |

For the `advanced` eight, a per-schema table exists in Claude model names. Source pins
three points of it — `design-gate`, `review-gate`, `taste-preflight`, all in `feature`;
the rest are switches the user makes in their own session.

| Schema | Planning | Implementation |
|---|---|---|
| `feature` | Opus 5 high — **xhigh at the design gate** | Sonnet 5 medium — **xhigh at the review gate**; Haiku mechanical |
| `bugfix` | **Opus 5 xhigh** — root cause | Sonnet 5 medium |
| `refactor` | Opus 5 high | Sonnet 5 medium; Haiku bulk |
| `upgrade` | Opus 5 high | Sonnet 5 medium; Haiku bulk |
| `setup` | Opus 5 high | Sonnet 5 medium; Haiku file generation |
| `hotfix` | Sonnet 5 low–medium triage · **Opus 5 xhigh postmortem** | Sonnet 5 medium |
| `spike` | Sonnet 5 low–medium | Sonnet 5 medium; Haiku explore |
| `rapid` | Sonnet 5 low–medium | Sonnet 5 medium |

**Four cells carry the premium spend on every tier:** the feature design gate, the feature
review gate, bugfix root cause, and the hotfix postmortem. The plugin pins the first two.

## Tier changes the budget, not the pick

All three consumer tiers can select every model; the differences are the weekly usage
bucket and how Fable is billed.

| Tier | Fable 5 | Adaptation |
|---|---|---|
| Pro | Not in-plan — usage credits only | Opus 5 xhigh replaces Fable at both feature gates, which is what this plugin ships. `opusplan` for planning-heavy schemas. Protect bugfix root cause and the hotfix postmortem at xhigh; drop marginal `refactor`/`upgrade` planning to Sonnet when the bucket is tight |
| Max 5x | In-plan, ≤50% of weekly limits | Opus 5 default; Opus-plan plus Sonnet-implement holds across a disciplined workweek. A Fable session weighs about twice an Opus one, so the cap arrives in roughly half the sessions the figure suggests — gates only |
| Max 20x | In-plan, same 50% cap | Nothing downgraded; Opus planning daily is fine. Gate-only Fable stays inside the cap |

`opusplan` — Opus in plan mode, Sonnet in execution, switched at the boundary — is rules 1
and 2 expressed as one alias, and the first burn control to reach for on Pro. Default
effort is `high` on every current model and `xhigh` must be opted into, so the deliberate
moves are down to `medium` for mechanical loops and up to `xhigh` at a gate. Hitting a
usage limit never triggers a model switch: rate-limit, billing, auth, request-size and
transport errors are all excluded from the fallback machinery.

## Two silent defeats

- **`CLAUDE_CODE_SUBAGENT_MODEL`** sits at the top of the resolution order, above the
  per-invocation model and above frontmatter `model:`. Set it and all six pins collapse to
  one tier, with no warning — the review split at `advanced` stops being a split. `inherit`
  is equivalent to unset.
- **The organisation's model allowlist.** A `model:` value is checked against
  `availableModels`, and an excluded value is *skipped*: the agent runs on the inherited
  model instead. If `opus` is unavailable, a design gate runs on the session's model while
  the schema still reads as though a stronger one had judged it. There is no fallback
  ladder.

Resolution order, highest first: `CLAUDE_CODE_SUBAGENT_MODEL` → the per-invocation model →
frontmatter `model:` → the main conversation's model. Subagents inherit the main
conversation's extended-thinking configuration; there is no per-subagent thinking setting.

`/status` reports the live model and effort, which is the cheapest available check that a
switch actually took.

## Answering a model question

Name the phase first, then the model and effort, then whether it is a pin or a
recommendation. Conflating those two is the error worth avoiding: a pin runs on its own,
while a recommendation needs the user to set it at an artifact boundary. Mention their
subscription tier only if it changes the answer — on Pro it does, at the two feature gates.

**How a recommendation is actually applied**, when they ask or when the answer is "switch":

1. `/clear` — **first**, not after. A model or effort switch made inside a full window
   still drags that window into every following turn, so switching without clearing buys
   much less than it looks like.
2. `/model` — model with up/down, that model's effort with left/right, one dialog.
   `/effort` alone covers the common case where only the depth is wrong.
3. The `opsx` command, **with the change name** — `/opsx:apply <change>` or
   `/opsx:continue <change>`. Both infer the change from the conversation when the name is
   omitted, and clearing is precisely what removes what they infer from.

The biggest single switch in any chain is the gap between the last planning artifact and
the first line of code — rules 1 and 2 above are that gap, and clearing there is universal.
Between *planning* artifacts, only step 2 travels alone: re-picking is always free, while
clearing is per chain — `feature-flow` wants its planning run in one unbroken window,
`feature` says to compact at artifact boundaries. Clearing costs the chain nothing either
way, because artifact status is pure filesystem existence. Confirm the result on the status
line rather than assuming it.

One piece of general tier advice does **not** apply in a repository this plugin configured:
setting `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` for cheap fan-out would collapse the
pinned gates. The plugin already achieves that saving per agent — `taste-preflight` is
`sonnet` by design; the gates and `flow-design` are not. Say so if the user raises it.

Sources: the six agent files under `payload/levels/*/agents/`;
`plugins/meta-skills/skills/authoring-subagents/references/frontmatter.md` for the
resolution order, allowlist behaviour, and the `AskUserQuestion` restriction; the
`standard` table from the mattpocock model-and-effort guide; the `minimal` table, derived
from the `advanced` one for the same kinds of work; and the `advanced` table, tier
adaptation, and burn-control facts from the Claude Code subscription-tier guide. Usage
limits, prices and promotional windows in that guide are dated — point the user at
`/usage` and Anthropic's own pages rather than quoting figures.
