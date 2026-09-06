# Evals for reviewing-code-security

Test material for maintainers, not users. Rerun after editing SKILL.md or its references.

- `triggers.md` — the 20-probe battery for the frontmatter `description`, with measured rates
- `cases.md` — behavioural assertions for the body
- `battery.ts` — assembles and tallies the trigger battery
- `manifest.json` — the competitor lineup every probe is measured against, plus the shipped skills
  that lineup knowingly omits
- `decoys/` — descriptions for competitors that are not shipped skills
- `results/` — raw trial records, one file per (date, model). A run with an unresolved trial is
  written as `<date>-<model>-rejected.json` instead, so a partial run cannot be mistaken for a
  complete one; re-dispatch and re-tally rather than committing it. The two names are mutually
  exclusive: whichever one a run writes, `tally` removes the other and says so, so one (date, model)
  never leaves two files behind for a committer to choose between. A model id containing anything
  outside `[A-Za-z0-9._-]` — a provider prefix such as `anthropic/claude-opus-5` — is sanitised for
  the *filename* only; the id inside the file is always the exact one that was dispatched. Because
  that sanitising can make two ids share a filename, no run destroys a file it cannot show is its
  own: the removal happens only when the other file records the same model id, and a write that
  would land on an existing file belonging to a different model (or to nobody this script can
  identify) is refused with exit 3 and both ids named, rather than overwriting it. A re-tally of the
  same model overwrites its own file as usual. Each file also records the `promptVersion` it was
  measured under — **a results file with no `promptVersion` field was produced by prompt version 1**,
  because that field was added with version 2. See _The prompt is an instrument_ below.

## Running the trigger battery

```bash
bun run battery:prompts --model <model-id> --scratch /path/outside/this/repo
bash /path/outside/this/repo/dispatch.sh --dry-run
bash /path/outside/this/repo/dispatch.sh
bun run battery:tally --scratch /path/outside/this/repo
```

`tally` prints rate lines to paste under each probe in `triggers.md` and writes the raw records to
`results/`. It refuses to produce a rate for any probe with a malformed or missing trial: re-dispatch
that trial and tally again. `dispatch.sh` skips trials that already have a non-empty response, so
re-running it is safe.

`dispatch.sh` costs real money the moment it calls `claude`, so run it with `--dry-run` first to see
what would fire without paying for it. The real run then asks for confirmation before the first call;
pass `--yes` to skip that prompt for a non-interactive run.

To escalate a probe from three trials to five:

```bash
bun run battery:prompts --model <model-id> --scratch /path/outside/this/repo --probe nofire-1 --trials 5
```

## Method

Each trial gives a fresh `claude -p` invocation one probe query plus the whole lineup — the target
and the competitors in `manifest.json`, 13 descriptions at present — and asks which, if any, it
would load. The answer
is a forced three-field object: `would_load`, `skill_named`, `reason`. A trial counts as firing only
when `skill_named` is `reviewing-code-security`; loading any other skill counts as not firing.

**Not firing happens in four distinguishable ways**, recorded as each trial's `outcome` in
`results/` and summarised per probe by `tally` under _what each probe reached for_. Only the first
can also be a fire:

| `outcome` | What the probe did | Reads as |
|---|---|---|
| `in-lineup` | Named one of the lineup | A fire if it named the target; otherwise it lost a discrimination it was offered |
| `out-of-lineup` | Named a skill that was not on offer | Evidence about the run's environment, not about the target's description |
| `unnamed` | `would_load: true` with an empty `skill_named` | Under prompt version 1, it wanted something outside the list and obeyed the instruction to name only listed skills; under version 2 that instruction is gone, so it would not or could not name what it reached for |
| `declined` | `would_load: false` with an empty `skill_named` | None of the lineup fit |

`fired` is unchanged and is still what every rate is computed from. `out-of-lineup` and `unnamed`
were both rejected as malformed until the first real run showed they are not: see **Environment**.
What stays malformed is what is genuinely broken — a non-boolean `would_load`, a non-string
`skill_named`, a missing or empty `reason`, no JSON object at all, and `would_load: false` alongside
a non-empty `skill_named`, which declines to load while naming what it loaded.

**Descriptions are read from disk every run**, never transcribed, so the battery always measures the
string that ships.

**Position is rotated deterministically.** Trial *n* places the target at index (5·(*n*−1)) mod the
lineup size, so the first five trials land on five distinct positions. There is no RNG and no seed
to record. The modulus is the live lineup size, so a lineup whose size shares a factor with 5 would
revisit a position within those five trials — check that when changing the lineup.

**Three trials per probe, escalating to five when the three are not unanimous.** One trial would be
structurally blind to the defect the battery exists to find: the failure already on record fires 3/5,
and a single trial would have read it as clean 40% of the time.

**A malformed answer is a first-class outcome.** It is never dropped, never averaged around, and never
read as `would_load: false`.

### What these numbers are, and are not

Asking "which skill would you load?" measures **stated** routing, not observed routing. A script
cannot watch a real session load a skill, so every rate here is a proxy. It is the right proxy for
comparing two candidate descriptions against each other, which is the decision this battery feeds. It
is **not** evidence about absolute real-world trigger rates — do not quote a rate as a field
measurement.

## The lineup, and what invalidates these numbers

`manifest.json` records the 12 descriptions each probe competes against: 11 of this repository's
non-security skills, plus a synthetic generic `code-review` skill in `decoys/`, present because the
battery's first partial run had a probe load exactly that.

**That lineup was 13 when the recorded rates were measured, and the thirteenth is gone.** One decoy
was `manhattan-brand-artifacts`, a skill from a plugin this marketplace has since retired. Because
descriptions are read from disk every run, its removal did not leave a stale string in the lineup —
it left `loadCandidates` throwing `resolves to no description file`, so the battery could not run at
all until the name was dropped on 2026-09-05. Restoring the count was not an option: the recorded
rates competed against that plugin's real description, which is not in this repository any more, and
writing a replacement under `decoys/` would put a description into the lineup that no probe was ever
shown. So the count is 12 and the old rates do not carry forward — which costs nothing here, because
they already did not: they were measured under prompt version 1 and already required re-dispatching
all 20 probes.

**Changing the lineup invalidates every previously recorded rate.** A probe shown fewer competitors
faces an easier discrimination task, which inflates should-fire and should-not-fire results alike.
`tests/security-evals.test.ts` fails when a recorded name no longer resolves — that makes the numbers
wrong — and fails when this repository ships a skill that appears in none of the manifest's four
lists, which leaves it unsayable what task the numbers describe.

Adding a skill to this marketplace therefore has to be answered, but it does not have to be paid for.
The two valid answers are: re-run the battery and add the skill to `decoys`, replacing the recorded
rates; or add it to `acknowledgedOmissions`, which is one line of JSON and records permanently that
the existing rates never competed against it. Nothing in `acknowledgedOmissions` is ever loaded into
a lineup or shown to a probe — it is the record of an omission, not a quiet way to make one.

## The prompt is an instrument, and it has a version

The wording `buildPrompt` produces is the instrument every rate is measured with, so a rate is only
ever a measurement under one particular wording. `battery.ts` exports `PROMPT_VERSION`, `prompts`
writes it into `meta.json`, and `tally` copies it from there into the results file — from `meta.json`
rather than from the constant, because a tally can run after the prompt has been edited and the
number belongs to the version that built the prompts.

**Increment `PROMPT_VERSION` whenever `buildPrompt`'s text changes**, and treat results carrying
different versions the way you would treat results measured against different lineups: do not
compare them, do not average them, do not put them on one axis.

| Version | What it asks |
|---|---|
| 1 | `would_load` meant "would you load one of the listed skills", and `skill_named` had to be one of the listed names |
| 2 | `would_load` means "would you load a skill at all", and `skill_named` always names the skill — the exact listed name when it is one of them, the skill's own name when it is not |

**A results file with no `promptVersion` field was produced by prompt version 1.** The field arrived
with version 2, and `results/2026-07-30-claude-opus-5.json` predates it. That file is evidence and is
not edited to backfill the field.

**The rates recorded in `triggers.md` are version-1 measurements.** Version 2 was adopted because
version 1 had no legal way to express the answer `nofire-2` kept giving — see **Environment** — but
fixing that changed the question every probe was asked. So those 20 rates cannot be carried forward
and cannot be compared against anything measured under version 2. Re-running under version 2 means
re-dispatching all 20 probes and replacing the rates wholesale, not re-running the probes that look
interesting and reading the rest across versions.

## Environment

Runs happen in a scratch directory outside this repository, so no project memory or repo-local plugin
config is in scope. User-level memory (`~/.claude/CLAUDE.md`) and user-level installed plugins still
load — "clean" here means no repository-specific context, not a vacuum. Each results file records the
model id; the run log below records the rest, because a reader comparing two runs needs to know what
changed between them.

| Date | Model | User-level memory | User-level plugins | Notes |
|---|---|---|---|---|
| 2026-07-30 | `claude-opus-5` | `~/.claude/CLAUDE.md` present but **empty** (0 bytes); no repo-local memory in scope | User-level marketplaces installed and live, including `superpowers-marketplace` | 20 probes × 3 trials, all unanimous, no escalation. Probe `nofire-2` named `superpowers:systematic-debugging` — direct evidence that user-level skills are reachable from a trial. |

That limitation is not theoretical, and the first real run proved it. On `nofire-2` — "Why is my
auth broken? Users can't log in." — all three trials reached for `superpowers:systematic-debugging`,
a user-level installed skill that is in no lineup here and was never shown to the probe. One named
it outright; two left `skill_named` empty and named it in `reason`, having been told the name must
come from the list. So a user-level plugin can win a routing decision against all 14 descriptions,
and a reader comparing two runs needs the plugin column filled in for the same reason they need the
model id. The three answers were consistent and correct — none of them fired — but the validator of
the day required a `true` `would_load` to name one of the 14, and rejected all three as malformed.
That is what the `out-of-lineup` and `unnamed` outcomes above exist to record. Widening the validator
did not touch the prompt, so the 60 trials stayed interpretable and comparable with each other.

The prompt has since been changed anyway, as version 2: reading three correct answers back out of a
schema that could not express them is a repair, not a fix, and the next run should not need it. That
change is why the rates in `triggers.md` are marked as version-1 measurements above — they were taken
under a prompt that no longer exists, and nothing measured under version 2 may be compared with them.

## Running the behavioural cases

`cases.md` is graded by hand against quoted evidence from the output — no benefit of the doubt. It
tests the skill's body, which is a different thing from the description the battery measures.
