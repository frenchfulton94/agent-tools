<!-- Source: mattpocock-bridge/CLAUDE.md.fragment.md -->
<!-- Drop this into your project's CLAUDE.md (or AGENTS.md) so a fresh session -->
<!-- picks the right entry point without being told. -->

## Workflow routing

This repo plans with OpenSpec under the `mattpocock-bridge` schema, and builds with the
mattpocock skills. The schema handles everything from `grill` onward; this section covers
what happens before a change exists, and what never becomes one.

### Entry routing

| What you observe | Where it goes |
|---|---|
| A new feature, a capability change, anything with a contract | `/opsx:new <the work, in a sentence>`, then `/opsx:continue <change>` per artifact — the schema's `grill` artifact runs the interview first |
| Something is broken and you know it | `/opsx:new <what is broken>, using bugfix-flow` (terminal: `openspec new change <name> --schema bugfix-flow`). Drops the interview, gates the fix behind a written root cause. A fault whose fix is a redesign goes back to the default schema |
| Raw incoming bug reports or feature requests | `/triage` first. It produces `ready-for-agent` issues, which become the input to a change |
| Slices that `/to-tickets` already published | Straight to `/opsx:apply <change>`. They are agent-ready by construction — triaging them again is wasted work |
| An effort too big to hold in one session, still wrapped in fog | `/wayfinder`. When its map clears, its linked decisions collapse into `grill.md` and `proposal.md` — it hands off at the proposal, it does not build |
| An idea surfaced by codebase upkeep | `/improve-codebase-architecture`, then enter the flow at `grill` |
| Typo, lint fix, config value, docs, non-breaking dependency bump | Direct PR. Ceremony scales with risk |
| Mid-change already | `/opsx:continue <change>`, `/opsx:apply <change>`, or `/opsx:archive <change>` — name the change; with a cleared window there is nothing left to infer it from |

### Context hygiene

Keep `grill` through `tasks` in one unbroken window so the interview, the proposal, and the
slices build on the same thinking. Sessions degrade past roughly 150k tokens; at that point
compact at the nearest artifact boundary rather than pushing on. Changing model or effort at
an artifact boundary is free and does not break the window — `/effort`, or `/model` with
left/right for effort.

Once `tasks` is written, reset before implementing, and start each slice the same way — every
slice is self-contained, so the finished one's context is disposable:

1. `/clear` — the planning artifacts are files now; apply reads them off disk and needs the
   room. Clear **first**: a model switch made inside a full window still drags it along.
2. `/model` or `/effort` — down from planning depth to an implementation tier.
3. `/opsx:apply <change>` — with the name, because clearing removed what it would infer from.

### Design work

UI surfaces go through **impeccable**, which is both user-invocable and reachable by the
agent, so either of you can start it.

| Situation | Command |
|---|---|
| Planning a surface | `shape` — runs inside the change's `surface` artifact |
| A named dimension is off | `typeset`, `layout`, `colorize`, `animate`, `bolder`, `quieter` |
| Something is off and you can't name it | `live` — pick the element in the browser, get variants |
| "Is this any good?" | `critique` — design review, two isolated sub-agents |
| Pre-ship checks | `audit` → `harden`, and `clarify` for copy |
| Final pass | `polish` |
| Design debt | `extract` to consolidate drift, `document` to re-capture DESIGN.md |

`npx impeccable detect <path>` runs the deterministic rules with no LLM and a build-failing
exit code — use it in CI and turn the design hook on locally so it runs per edit.

**Leave Anthropic's `frontend-design` skill disabled.** Two design skills with different
vocabularies collide. Impeccable is the one this project uses.

Impeccable is an opinionated partner rather than a linter: push back with a reason and it
works with you, but overriding it silently gets you generic output.

**Motion is the one dimension impeccable does not cover**, and `animate` above changes how
an animation looks rather than deciding whether it should exist. Before writing one, invoke
`animating-interfaces` for the frequency tier, the purpose, the curve and duration or spring
config, and the reduced-motion behavior; `apple-design` for drag, swipe, and sheets; and
`reviewing-animations` on the diff afterwards. They do not collide with impeccable — the
vocabularies sit on different axes, and the frequency gate is the part that will tell you
to delete an animation impeccable would happily have polished.

### Security

Security review runs as hooks, not as a step anyone remembers: **security-guidance** warns
on dangerous patterns at `Edit`/`Write`, reviews the diff when a turn ends, and runs an
agentic reviewer on `git commit`. Expect it to fire during a slice's commit and address what
it reports before moving on. It covers an axis nothing else here does — injection, XSS, SSRF,
hardcoded secrets, IDOR, auth bypass — where `code-review` covers standards and spec, and
impeccable's `audit` covers accessibility and performance.

`/claude-security` is the deep pass: a full-repo or diff scan with its own agent panel, and
patches you apply when you choose. It is user-invoked and far too heavy per slice — run it
before a release, or when a change touches auth, uploads, or anything parsing untrusted
input.

### Web platform

`npx modern-web-guidance search "<what you're building>"` returns targeted guides on modern
browser APIs, retrieved on demand rather than held in context. The `design` artifact calls it
while choosing an approach, which is when it pays — the native answer is worth having before
a library gets picked, not after.

This complements impeccable rather than competing with it: impeccable judges whether a
surface is any good, modern-web-guidance supplies the platform-native way to build it.

### Reviewing

`code-review` is this project's reviewer, running per slice inside `apply` against the
slice's start commit. **Leave `pr-review-toolkit` and the standalone `code-simplifier`
disabled** — both review the working diff against CLAUDE.md, which is `code-review`'s
Standards axis, and both are written to fire proactively before a commit. Two reviewers with
different bars on the same diff produce contradictory verdicts and twice the cost.

If you would rather run `pr-review-toolkit`, it replaces `code-review`'s Standards axis
rather than joining it — say so in `apply` so only one reviewer owns that job.

### Where things get written

Five stores outlive a change: `openspec/specs/` for behaviour, `CONTEXT.md` for vocabulary,
`docs/adr/` for decisions that still bind the next change, `PRODUCT.md` for product truth,
and `DESIGN.md` for visual tokens. Impeccable's own working files live under `.impeccable/`
— surface briefs, critique snapshots, mocks, review screenshots — also outside the change.
Everything inside
`openspec/changes/<name>/` archives with it — including any `research/` or `issues/`
subfolder you add, which is the reason to put them there.

Two consequences worth remembering:

- On a **local-markdown issue tracker**, point `docs/agents/issue-tracker.md` at
  `openspec/changes/<change-name>/issues/NN-<slug>.md`. The default `.scratch/<slug>/` sits
  outside the change and is left behind at archive.
- `/handoff` writes to the OS temp dir by design. When you take one mid-change, name the
  change in the doc and tell the next session to run
  `openspec status --change <name> --json` first.

### Skills the agent can reach on its own

`grilling`, `domain-modeling`, `codebase-design`, `tdd`, `code-review`, `prototype`,
`research`, `diagnosing-bugs`.

Everything else in that repo is user-invoked — `/grill-with-docs`, `/to-spec`, `/to-tickets`,
`/implement`, `/triage`, `/wayfinder`, `/handoff` — so only a human typing the name fires it.
The schema carries their discipline in prose and offers you the command where it would help.
