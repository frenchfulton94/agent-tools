# mattpocock-bridge

An OpenSpec schema that drives [OpenSpec](https://github.com/Fission-AI/OpenSpec)'s artifact
governance with the discipline in [mattpocock/skills](https://github.com/mattpocock/skills).

`grill → proposal → surface → specs → design → tasks → apply`

OpenSpec owns what documents a change must have and how behaviour deltas merge into a source
of truth. The mattpocock skills own how you decide what to build, name it, choose where to
test it, and build it. This schema is the whole integration: prompt layer only, no fork of
either project.

## Prerequisites

1. `openspec init` in the project.
2. The mattpocock skills — the Claude Code plugin **or** skills.sh, [not both]
   (https://github.com/mattpocock/skills#installation-30-second-setup).
3. For UI work: `npx impeccable install`, then `/impeccable init` to write PRODUCT.md and
   DESIGN.md. Turn the design hook on with `/impeccable hooks on`. Leave Anthropic's
   `frontend-design` skill disabled — impeccable and it cancel each other out.
3. `/setup-matt-pocock-skills`, run once, so `docs/agents/issue-tracker.md` exists.

## Install

```bash
cp -R mattpocock-bridge <your-project>/openspec/schemas/mattpocock-bridge
cd <your-project>
openspec schema validate mattpocock-bridge
```

Then set `schema: mattpocock-bridge` in `openspec/config.yaml`, and merge in the
`context:` and `rules:` blocks from `config.yaml.example`.

Add the routing block from `CLAUDE.md.fragment.md` to your `CLAUDE.md` or `AGENTS.md`, and
switch to the expanded command profile so each interactive artifact gets its own step:

```bash
openspec config profile   # choose: expanded
openspec update
```

## Companion plugins

Recommended alongside, none requiring schema changes:

- **security-guidance** — hooks only. Covers injection, XSS, SSRF, and secrets, an axis
  neither `code-review` nor impeccable's `audit` touches.
- **claude-security** — user-invoked deep scan. Run before a release, not per slice.
- **modern-web-guidance** — CLI-backed retrieval of modern web platform guides; the `design`
  artifact calls it while choosing an approach.

Leave **pr-review-toolkit** and the standalone **code-simplifier** disabled: both review the
working diff against CLAUDE.md, which is what `code-review` already does per slice, and both
fire proactively before a commit.

## Companion schema

`bugfix-flow` handles defect fixes: `diagnose → specs → tasks`, no interview, no proposal,
and the fix gated behind a written root cause. Install it beside this one and select it per
change with `/opsx:new <what is broken>, using bugfix-flow` — or, in a terminal,
`openspec new change <name> --schema bugfix-flow`.

## Upgrading the bundle

`rules` and `context` live in your `openspec/config.yaml`, not in this bundle, so replacing
`openspec/schemas/mattpocock-bridge/` leaves them untouched. Re-merge `config.yaml.example`
by hand after an upgrade, or new rules silently never fire.

## What each artifact does

| Artifact | Skills it reaches | What it carries |
|---|---|---|
| `grill` | `grilling`, `domain-modeling`, `prototype`, `research` | Interview in rounds; CONTEXT.md and ADRs written inline |
| `proposal` | — (`/to-spec` shape in prose) | Problem / Solution / User Stories, plus OpenSpec's Capabilities contract |
| `surface` | `impeccable` (`shape`) | Design brief: visitor mode, states and ranges, direction, boundaries. Skipped on changes with no visible surface |
| `specs` | — | Delta specs. ADDED requirements come from the user stories; MODIFIED and REMOVED come from the existing main spec |
| `design` | `codebase-design`, `domain-modeling` | Deep-module vocabulary and the **Seams** table `/tdd` needs agreed up front — every spec scenario covered by name |
| `tasks` | — (`/to-tickets` shape in prose) | Tracer-bullet slices published to the tracker, mirrored as checkboxes |
| `apply` | `tdd`, `code-review` | One slice per session, test-first at agreed seams, two-axis review before commit |

Only the model-invoked skills are invoked from instructions. The user-invoked ones cannot be
reached by an agent by design, so the schema carries their discipline and offers you the
command instead.

## Escape hatches

- No spec-level behaviour change (refactor, tooling, docs)? Set `skip_specs: true` in the
  change's `.openspec.yaml` — `specs` then reports `skipped` and its files must not exist.
- No user-facing surface — backend, data, tooling, infrastructure? Set `skip_surface: true`
  and write the one-line stub.
- Change genuinely one decision wide? Set `skip_grill: true` in the same file. The CLI does
  not read this key, so `grill.md` is still written — as a single line giving the reason and
  the date. That stub unblocks the graph and records who waived the interview.
- One module, no new dependency, no security/performance/migration question? Skip `design`
  deliberately and say so.

## License

MIT, matching both upstreams.
