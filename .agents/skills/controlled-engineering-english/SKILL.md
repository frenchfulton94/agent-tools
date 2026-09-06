---
name: controlled-engineering-english
description: Writes and reviews documentation in Controlled Engineering English, a controlled language with register-specific rules and a project glossary. Use when the user is drafting, rewriting, or reviewing a README, CONTRIBUTING guide, API reference, architecture overview, runbook, onboarding guide, ADR or design-doc prose, code review comment, release note, status update, executive summary, incident summary, user guide, or the prose layer of a spec. Also use on symptoms the user names without naming documentation — docs that drift between synonyms for one concept, jargon a non-engineer cannot read, a README whose commands no longer match the repo, requirements that bury implementation detail, or SHOULD used where the requirement is absolute. Also use when the user wants a project glossary set up or maintained. For UI labels and in-product copy prefer the impeccable clarify flow; for code identifiers, neither.
license: MIT
---

# Controlled Engineering English

Controlled Engineering English (CEE) is a standard for documents humans read.
It has two halves: rules that bind how sentences are built, and a dictionary
that binds which words are used. This skill applies both, then checks the
result.

The rules in `references/rules.md` are authoritative. The digest below carries
each rule in one line so a normal run needs no file load. Read
`references/rules.md` when you need a rule's examples, its exact wording to
quote, or the waiver format.

## Step 1: Classify the document

| The reader is... | Register | Meaning |
|---|---|---|
| An engineer, including future-you and new joiners | **R1-E** | Assume the stack, not the project |
| A non-technical stakeholder or end user | **R1-S** | Assume neither the stack nor the project |
| An engineer or agent implementing this later | **Spec prose** | R1-E plus G-N1 and E-4 |

Mixed-audience documents split by section, not by averaging. An incident
report is R1-S in its executive summary and R1-E in its technical timeline. State the classification in the report.

One document, one register per section. A README written half in stakeholder
register reads as marketing; a release note written in engineer register is
the failure this standard exists to fix.

## Step 2: Find the project glossary

Follow this chain, in order, and stop at the first hit:

1. A pointer line in `AGENTS.md` or the harness's memory-file equivalent
   (`CLAUDE.md` is one alias): `Glossary: <path>`. Whatever it points at is
   the glossary.
2. `docs/GLOSSARY.md`.
3. No glossary. Say so, apply the rules without it, and offer to run setup.
   Never block on a missing glossary.

Read the glossary before writing. Its terms win over any synonym, including
one already in the document. Where the pointer targets a file another skill owns — a `CONTEXT.md` under
domain-modeling, for example — read it and use it. Recommend that skill for
the edit; do not edit the file here.

Editing the glossary is never a side effect of writing a document. New terms
are proposed in the report and written only through the setup or proposal
flow, after the user approves them. Read `references/setup.md` when the task
is to build or extend the glossary.

## Step 3: Apply the rules

Rules that bind every register:

- **G-W1** One term per concept. Where the glossary defines a term, use it
  exactly and write no synonym for it.
- **G-W2** Define every acronym and coined term at first use. Do not invent an
  expansion for an acronym you cannot source; flag it and ask.
- **G-S1** Active voice. One idea per sentence. No sentence over 25 words.
- **G-C1** Point at the environment instead of caching it. Link or name the
  script, config, or command's home rather than restating values that go
  stale.
- **G-P1** Delete any sentence that does not change what the reader knows or
  does.
- **G-N1** MUST and SHALL mark absolute requirements, SHOULD marks a
  recommendation with allowed exceptions, MAY marks an option. These words
  carry no other use.
- **G-X1** Waive a rule where it applies, with a reason and a date.

Engineer documents (R1-E):

- **E-1** Stack terms are allowed and stay untranslated. Project concepts take
  their glossary term and link to the glossary.
- **E-2** Every runbook step ends in an observable check: what the reader
  should see if it worked.
- **E-3** Reference docs are structured for lookup; onboarding docs are
  structured for sequence.
- **E-4** Specs state behavior; design states implementation. If the
  implementation can change without changing observable behavior, the sentence
  belongs in design.

Stakeholder documents (R1-S):

- **S-1** Translate or cut stack jargon. Gloss each glossary term inline at
  first use, using the glossary's own gloss column.
- **S-2** Answer, in this order: what changed, why it matters to this reader,
  what happens next.
- **S-3** Report failures as problem, then impact, then next step.
- **S-4** Every number carries its comparison. A bare number is jargon.

## Step 4: Check the result

Run the deterministic pass if Vale is installed:

    vale --config scripts/vale/.vale.ini <file>

If the glossary exists, regenerate its substitution rules first, so glossary
enforcement is deterministic rather than remembered:

    python3 scripts/glossary-to-vale.py <glossary-path> \
      scripts/vale/styles/CEE/Glossary.yml

Vale is optional. Where it is absent, unavailable, or fails to run, apply the
same rules by review and say in the report which pass ran. Every rule in this
standard is applicable by review alone; Vale sharpens enforcement, it does not
gate it.

Then read the rewrite once more against these, in order:

- Every sentence under 25 words.
- Every glossary term spelled as the glossary spells it, and no banned synonym
  anywhere.
- R1-S only: no untranslated stack term survives, and every number has its
  comparison.
- Spec prose only: every MUST, SHOULD, and MAY carries its G-N1 meaning, and
  no requirement names a class, table, or library.

## Step 5: Report

The response after the document contains, in this order:

1. **Register** — which one, and why, in one sentence.
2. **Glossary** — the path used, or that none was found and setup is
   available.
3. **Changes** — one line each, every line naming its rule ID.
4. **Glossary candidates** — terms this document needed and the glossary
   lacks, as proposals, with no file written.
5. **Waivers** — each as rule ID, reason, date (G-X1). Say "none" when there
   are none.

## Before and after, one per register

**R1-E** — G-C1, the environment cached instead of named:

> Before: Start the dev server with `npm run start -- --port 3000`.
> After: Start the dev server with the `dev` script in `package.json`.

The before-version drifts the day someone changes the port. The after-version
cannot.

**R1-S** — S-3 and S-4, a failure reported cause-first with bare numbers:

> Before: Lock contention in the advisory lock layer caused queuing during the
> nightly run. Payout latency is 340ms.
> After: Some payouts arrived a day late on 14 August (problem). Payments
> under £500 were unaffected (impact). Every delayed payout has now settled,
> and payouts complete in 340ms, down from 2.1s (next step, with the
> comparison).

**Spec prose** — G-N1 and E-4, a recommendation keyword on an absolute and
implementation inside a requirement:

> Before: The system should reject refunds after 90 days by taking an advisory
> lock and writing two rows to the transaction log.
> After: The system MUST reject a refund request made more than 90 days after
> the payment. (The lock and the two-row write move to design: both can change
> without changing what a caller observes.)

## Where the rest lives

- `references/rules.md` — every rule with a violating and a conforming
  example, and the `version:` line. Read it to quote a rule or to check an
  edge case the digest does not settle.
- `references/dictionary.md` — the core word list, the glossary table format,
  and the admission rules for new terms. Read it before proposing a glossary
  entry.
- `references/setup.md` — the run-once flow that builds a glossary. Read it
  when the task is setup rather than a document.
- `references/background.md` — where the rules come from. Read it only when
  the user asks why a rule exists.
- `assets/distillation.md` — the compiled core of the rules, for ambient use
  in a session.
- `scripts/vale/` — the optional deterministic backend: `.vale.ini` and the
  `styles/CEE` rule files. Nothing here loads into context; Vale reads it.
- `scripts/tests/` — maintainer tests. Run `python3
  scripts/tests/test_frontmatter.py`, `python3
  scripts/tests/test_glossary_to_vale.py`, and `python3
  scripts/tests/test_vale_rules.py` after changing a script, a rule file, or
  any frontmatter.

## Installing the ambient style

The distillation makes the core rules apply to every reply, not only to
document tasks. It is compiled to one file per harness by
`scripts/compile-targets.py`; edit `assets/distillation.md` and recompile
rather than editing a target.

| Harness | Install |
|---|---|
| Claude Code | Copy `assets/controlled-english.output-style.md` to `.claude/output-styles/` (project) or `~/.claude/output-styles/` (user), then select it under `/config` |
| claude.ai | Paste `assets/distillation.md` into a personal style or the preferences field. Use that file, not a compiled target: the targets carry a terminal line-wrap rule that fights a browser's own reflow |
| Any agents-file harness | Paste `assets/agents-fragment.md` into `AGENTS.md` |
| SDK, CI, headless | `claude --append-system-prompt "$(cat assets/system-prompt-append.md)"`, or point `--system-prompt-file` at it |
| Subagents | Paste `assets/subagent-prompt-block.md` into the subagent's prompt |

Output styles reach the main conversation only. A subagent that writes
documents needs the skill or the paste-in block; it inherits neither the style
nor the session's register.

Run `python3 scripts/compile-targets.py --check` after any rule change. It
fails when a target has drifted from the distillation.

Each compiled target ends in a terminal addendum that wraps prose at about 80
characters. It sits outside the distillation because line width belongs to the
surface, not to the language. Edit it in `scripts/compile-targets.py` and
recompile.
