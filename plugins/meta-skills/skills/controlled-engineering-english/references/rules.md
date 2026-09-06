# CEE Rules

`version: 1.2`

**Change rule:** any change to a rule, or to the core word list in
`dictionary.md`, bumps this version and requires the user's approval. The
digest in `SKILL.md` and the compiled `assets/distillation.md` are derived
from this file; regenerate both when this file changes.

**Version history.**

| Version | Date | Change |
|---|---|---|
| 1.2 | 2026-08-20 | Spec prose: added the boundary rule for tool-owned scenario formats. Dictionary: the modify and remove families moved to a case-sensitive rule so ALL-CAPS delta keywords (OpenSpec's ADDED / MODIFIED / REMOVED / RENAMED) are not rewritten as vocabulary violations. |
| 1.1 | 2026-08-20 | G-P1: added the hedges the first pilot found in real prose — "probably", "it is recommended", "should be posted". The original token list was written from imagination and caught none of them. |
| 1.0 | 2026-08-20 | First rule set, drafted from the frozen design. Not yet reviewed line by line. |

Contents:
- [How to read a rule](#how-to-read-a-rule)
- [G — rules that bind every register](#g--rules-that-bind-every-register)
- [E — engineer documents (R1-E)](#e--engineer-documents-r1-e)
- [S — stakeholder documents (R1-S)](#s--stakeholder-documents-r1-s)
- [Spec prose](#spec-prose)
- [Waivers](#waivers)
- [Enforcement level per rule](#enforcement-level-per-rule)

## How to read a rule

Each rule has an ID, a one-sentence statement, a reason, and two examples: one
that violates it and one that conforms. Cite the ID when you change a
document. A reader who disagrees with a change should be able to look up the
ID and argue with the rule instead of with you.

## G — rules that bind every register

### G-W1 — One term per concept

Use one term for one concept. Where the glossary defines a term, use it
exactly as the glossary spells it, and write no synonym for it.

**Why.** Synonym drift is the most expensive defect in project documentation.
A reader who meets "ledger", "transaction log", and "journal" in one document
must decide whether they are three things. Every such decision is a chance to
get it wrong, and search finds only the spelling the reader guessed.

> Violates: Every movement is written to the ledger. The transaction log is
> append-only, so the journal is never edited.
> Conforms: Every movement is written to the Ledger. The Ledger is
> append-only, so entries are never edited.

Applies to synonyms the document invents as well as ones the glossary bans. If
a concept recurs and has no name, that is a glossary candidate; report it.

### G-W2 — Define at first use

Define every acronym and every coined term the first time it appears. The
definition's permanent home is the glossary; the inline definition is a
courtesy to this reader.

**Why.** An undefined acronym is a lookup the reader cannot perform, because
they do not know which of the twelve expansions is yours.

> Violates: The system also performs SDR checks on each entry.
> Conforms: The system also performs settlement-delta reconciliation (SDR)
> checks on each entry.

Where the expansion is unknown, do not invent one. Flag the term and ask. A
guessed expansion is worse than an undefined acronym: it is wrong and it looks
authoritative.

### G-S1 — One idea, active, under 25 words

Write in the active voice. Put one idea in each sentence. Keep every sentence
under 25 words.

**Why.** Long sentences hide the actor and the action. The 25-word ceiling is
arbitrary in the way a speed limit is arbitrary. The number matters less than
having a number a machine can check.

> Violates: Prior to commencing work you will want to ensure that the
> dependencies have been installed, after which the development server may be
> started, which will bring the application up locally. (38 words, passive,
> three ideas)
> Conforms: Install the dependencies. Then start the development server. The
> application runs locally.

The active-voice half of this rule is usually already obeyed. The word ceiling
is the half that catches real defects; check it by counting, not by feel.

### G-C1 — Point at the environment, do not cache it

Name or link the home of a command, script, config value, or version. Do not
restate its contents in prose.

**Why.** A restated value is a copy that nothing keeps in sync. The copy is
correct on the day it is written and wrong from some later day that nobody
notices. Pointing has no such day.

> Violates: Run `npm run start -- --port 3000` to start the server, and
> `npm test --watch` to run the tests.
> Conforms: Use the `dev` and `test` scripts in `package.json`.

Naming a script is pointing. Restating its flags, ports, and arguments is
caching. Fixing a drifted cache to match the source is not a fix; it is a
fresh cache that will drift again.

### G-P1 — Prune

Delete any sentence that does not change what the reader knows or does.

**Why.** Every kept sentence taxes every future reader. Sentences that
announce the document ("This README is a living document"), greet the reader,
or restate the heading are pure tax.

> Violates: This document describes refunds. Refunds are an important part of
> the product and this document will describe how they work.
> Conforms: (deleted — the heading already said "Refunds")

Test each sentence: what does the reader now know, or now do, that they did
not before? No answer means delete.

### G-N1 — Normative keywords have fixed meanings

MUST and SHALL mark an absolute requirement. SHOULD marks a recommendation
with allowed exceptions. MAY marks an option. Use these words for nothing
else.

**Why.** An implementer reads SHOULD as permission to skip. If the
requirement is absolute, SHOULD has told them the opposite of the truth. This
rule matters most in spec prose but binds everywhere, because these words
carry the same promise in a README.

> Violates: A refund request should never be accepted after 90 days. The
> handler must probably retry on transient failures.
> Conforms: A refund request MUST be rejected more than 90 days after the
> payment. The handler SHOULD retry on transient failures; it MAY give up
> after three attempts.

"Must probably" is not a hedge; it is two keywords fighting. Resolve to one.

### G-X1 — Waive with a reason and a date

Where a rule applies and the document breaks it anyway, record the waiver:
rule ID, reason, date.

**Why.** A controlled language with no escape hatch gets abandoned wholesale
the first time it is wrong. A waiver keeps the exception visible and dated, so
it can be reviewed instead of forgotten.

> Violates: (a 34-word sentence, left as-is, unremarked)
> Conforms: G-S1 waived 2026-08-20: the quoted regulatory text is 34 words and
> may not be split.

## E — engineer documents (R1-E)

### E-1 — Assume the stack, not the project

Stack terms used in their ordinary industry sense stay untranslated. Project
concepts take their glossary term and link to the glossary on first use.

**Why.** The reader knows what a webhook is; they do not know what your
Settlement Window is. Translating the first patronizes them and translating
neither strands them.

> Violates: The service sends a message to another service over the internet
> when a payment finishes its nightly grouping.
> Conforms: The service sends a webhook when a payment clears its
> [Settlement Window](docs/GLOSSARY.md#settlement-window).

### E-2 — Every runbook step ends in an observable check

Each step in a procedure states what the reader should see if it worked.

**Why.** A procedure without checks fails silently. The reader learns at step
9 that step 3 did nothing, and has no way back.

> Violates: 3. Run the deploy pipeline. 4. Check that the deploy worked.
> Conforms: 3. Run the deploy pipeline. The run finishes green and the
> `version` field at `/healthz` matches the merged commit.

"Check that it worked" names no observation. If you cannot state what the
reader should see, the step has no check and needs one.

### E-3 — Structure for the reading mode

Structure reference documents for lookup: findable headings, one addressable
item per thing. Structure onboarding documents for sequence: ordered, each
step assuming the last.

**Why.** Nobody reads an API reference from the top, and nobody arrives at an
onboarding guide knowing which section they need. Structure that fits one mode
defeats the other.

> Violates: (a Getting started section that buries install, run, test, and
> migrate inside one narrative paragraph)
> Conforms: (a Getting started section with Prerequisites, Install, Run,
> Test, and Migrate as separate addressable items)

### E-4 — Behavior in specs, implementation in design

A spec states observable behavior. A design states implementation. If the
implementation can change without changing observable behavior, the sentence
belongs in the design.

**Why.** Implementation inside a requirement freezes a decision that was never
argued, and it makes the spec false the day the code is refactored.

> Violates: When a refund is issued, the system calls `RefundService.apply()`,
> takes an advisory lock on the payment ID, and writes two rows.
> Conforms: When a refund is issued, the Ledger records the refund against the
> original payment, and a second refund for the same payment has no further
> effect. (The lock and the two-row write are design decisions: both can
> change without changing what a caller observes.)

## S — stakeholder documents (R1-S)

### S-1 — Assume neither the stack nor the project

Translate or cut every stack term. Gloss each glossary term inline at first
use, using the gloss written in the glossary.

**Why.** This reader has no way to look anything up. A term they cannot decode
does not merely slow them: it tells them the document was not written for
them, and they stop.

> Violates: The idempotency key TTL is now 24h and the DLQ is drained by a
> separate consumer group.
> Conforms: Repeat payment attempts are now ignored for 24 hours instead of
> one, so a retried payment cannot charge a customer twice.

The gloss comes from the glossary's gloss column. Every document then
explains the concept the same way: "the Ledger — our permanent record of
every payment".

### S-2 — What changed, why it matters, what happens next

Every stakeholder document answers those three, in that order.

**Why.** This reader opened the document to find out whether they must do
something. Any other order makes them read to the end to find out.

> Violates: Following an investigation into elevated p99 latency on the
> settlement path, it was determined that...
> Conforms: Payouts now arrive a day sooner (what changed). Customers see
> money on Tuesday instead of Wednesday (why it matters). Nothing is required
> from you; the change is already live (what happens next).

"Customers may wish to reach out to their account manager" is not a next
step. A next step names who acts and by when.

### S-3 — Failures are problem, impact, next step

Report a failure in that order. The cause chain is cut, or demoted below the
impact.

**Why.** The reader's first question is what happened to them, not what
happened to the database. A cause-first report reads as an excuse and buries
the answer.

> Violates: A lock contention issue introduced during the scheduler refactor
> caused transactions to queue, and as a result some payouts were delayed.
> Conforms: Some payouts arrived a day late on 14 August (problem). Payments
> under £500 were unaffected (impact). Every delayed payout has now settled,
> and no action is needed from you (next step).

### S-4 — Numbers carry their comparison

State every number against its previous value, its target, or its total. A
bare number is jargon.

**Why.** "340ms" tells this reader nothing: they do not know whether it is
fast. "340ms, down from 2.1s" tells them the whole story without a single
technical word.

> Violates: Payout latency is 340ms. We cut 12 rows from the writer path.
> Conforms: Payouts complete in 340ms, down from 2.1s.

Where the comparison is unavailable, cut the number or mark it as needing its
before value. Do not invent a baseline.

## Spec prose

Spec prose is the human-readable layer of a spec: requirements and scenarios
as sentences. It takes the R1-E rules, plus G-N1 and E-4, plus one addition:

**Scenarios read aloud.** Write each scenario as a sentence a person can read
out: given a state, when an event, then an observable result.

> Violates: refund_expired: req>90d -> 422, no journal write, metric
> `refund.rejected.expired`++
> Conforms: Given a payment made more than 90 days ago, when a refund is
> requested, then the request is rejected and the Ledger is unchanged.

Skeleton machinery — heading grammar, checkbox requirement IDs, delta
keywords, linter-enforced structure — is out of scope. Rewrite the prose; do
not regrammar the artifact.

**Where a spec tool owns the format, the prose inside a scenario is in scope
and the scenario's shape is not.** OpenSpec, and tools like it, validate
heading depth, delta keywords, and the WHEN/THEN skeleton. Improve the wording
inside those structures and leave the structures alone.

> Violates: (collapsing a tool's `#### Scenario:` heading and WHEN/THEN bullets
> into one flowing paragraph, so `openspec validate` fails)
> Conforms: (keeping the heading and the bullets, and rewriting the sentence
> inside each bullet)

ALL-CAPS words are structure, not prose. Never rewrite one as a vocabulary
violation: MODIFIED in a delta header is a keyword, and "change" is not a
synonym for it.

## Waivers

Format: `<RULE-ID> waived <YYYY-MM-DD>: <reason>`.

Put waivers where the reader meets the exception: a comment in the document,
or the report's waiver section for a review. A waiver with no reason is a
violation with a label.

## Enforcement level per rule

All rules start at warning. A rule escalates to blocking only after it has run
clean on real documents, mechanical rules first. Judgment rules stay warnings.

| Rule | Check | Level |
|---|---|---|
| G-W1 | Deterministic where the glossary supplies banned synonyms | Warning, escalatable |
| G-W2 | Judgment | Warning |
| G-S1 | Deterministic (word count); judgment (one idea) | Warning, escalatable |
| G-C1 | Judgment | Warning |
| G-P1 | Judgment | Warning |
| G-N1 | Deterministic (keyword present); judgment (right keyword) | Warning, escalatable |
| G-X1 | Deterministic (waiver format) | Warning |
| E-1 to E-4 | Judgment | Warning |
| S-1 | Deterministic where the glossary supplies glosses | Warning |
| S-2 to S-4 | Judgment | Warning |
