# CEE Dictionary

`version: 1.0`

The dictionary has two strata. The **core list** is general English and ships
with the skill. The **project glossary** is domain vocabulary and lives in the
project's own repo. No core list can predict a domain, so every controlled
language needs an escape hatch for the project's own names. The glossary is
that hatch, made enforceable.

Contents:
- [Core word list](#core-word-list)
- [Glossary file format](#glossary-file-format)
- [Discovery chain](#discovery-chain)
- [Admission rules](#admission-rules)
- [Stack terms](#stack-terms)
- [Who writes the glossary](#who-writes-the-glossary)

## Core word list

One approved word per meaning. The banned column lists what people write
instead. Grow this list only on drift observed in real documents, never on
speculation, and bump the `version:` line when it grows.

| Use | Not | Note |
|---|---|---|
| use | utilize, leverage, make use of | |
| before | prior to, in advance of, ahead of | |
| after | following, subsequent to | |
| start | commence, initiate, kick off, spin up | |
| stop | cease, halt, terminate | Reserve "terminate" for process termination |
| end | conclude, finalize | |
| build | construct, produce | |
| change | modify, alter, adjust, amend | |
| delete | remove, purge, drop, eliminate | "Drop" is allowed for SQL |
| add | append, introduce, incorporate | "Append" is allowed for append-only writes |
| show | surface, expose, render, display | "Expose" is allowed for a network interface |
| find | locate, discover, identify | |
| need | require, necessitate | |
| let | allow, enable, permit | "Enable" is allowed for a feature flag |
| send | transmit, dispatch, emit | "Emit" is allowed for events |
| get | obtain, retrieve, acquire, fetch | "Fetch" is allowed for HTTP |
| run | execute, perform, invoke | "Invoke" is allowed for a function call |
| set up | configure, provision, stand up | "Configure" is allowed for config files |
| about | regarding, concerning, with respect to | |
| because | due to the fact that, owing to, as a result of | |
| if | in the event that, in the case where | |
| now | at this time, currently, at present | |
| then | subsequently, thereafter | |
| many | numerous, a multitude of | |
| most | the majority of | |
| some | a number of, several | |
| can | is able to, has the ability to | |
| must | is required to, is obligated to | Keep MUST for G-N1 |
| may | is permitted to, has the option to | Keep MAY for G-N1 |
| help | assist, facilitate | |
| try | attempt, endeavor | |
| ask | request, inquire | "Request" is allowed as a noun |
| answer | respond, reply | "Reply" is allowed for an email or message |
| fix | remediate, resolve, address | |
| break | fail, error out | "Fail" is allowed for tests and jobs |
| check | verify, validate, confirm | "Validate" is allowed for schema validation |
| make sure | ensure, guarantee | |
| wait | pause, hold, block | "Block" is allowed for threads |
| keep | retain, preserve, maintain | |
| give | provide, supply, deliver | |
| take | consume, ingest | "Consume" is allowed for queues |
| write | persist, store, commit | "Commit" is allowed for git and transactions |
| read | load, ingest, pull | "Load" is allowed for loading a file |
| open | initiate, establish | |
| close | shut down, tear down | |
| new | novel, greenfield | |
| old | legacy, deprecated | "Deprecated" is allowed as a formal status |
| big | large-scale, substantial | |
| small | minimal, lightweight | |
| fast | performant, high-throughput | |
| slow | degraded, suboptimal | |
| every | each and every, all of the | |
| always | at all times, in every case | |
| never | at no time, under no circumstances | |

**Case matters for two families.** "modify" and "remove" are enforced by a
case-sensitive rule, because spec tools use their ALL-CAPS forms as structure.
OpenSpec's ADDED / MODIFIED / REMOVED / RENAMED delta headers are keywords, and
rewriting one breaks validation. Lowercase and capitalized forms are still
flagged; the ALL-CAPS form passes.

Where the note names an allowed technical use, the banned word is banned only
in its loose sense. "Commit the change to git" is fine; "commit the value to
the config file" is not.

## Glossary file format

A markdown table, one row per term. Plain markdown, so no tool owns it.

    | Term | POS | Meaning | Banned synonyms | Stakeholder gloss |
    |---|---|---|---|---|
    | Ledger | noun | The append-only record of every money movement. | transaction log, money record, journal | the Ledger — our permanent record of every payment |
    | Settlement Window | noun | The nightly period when payments are sent to the bank. | batch window, cutoff, nightly run | the Settlement Window — the nightly slot when payments go to your bank |
    | Worker | noun | Our Cloudflare Worker that runs the payment path. | the service, the edge function | |

Column rules:

- **Term** — spelled as it must be written, capitalization included.
- **POS** — one part of speech per term. A term used as both noun and verb is
  two entries or one decision, not one ambiguous row.
- **Meaning** — one sentence. If it needs two, the term covers two concepts.
- **Banned synonyms** — comma-separated, lowercase. These compile to
  deterministic linter rules, so an empty cell means no deterministic
  enforcement for that term.
- **Stakeholder gloss** — required only for terms that appear in an R1-S
  document, backfilled on first use. The gloss is written once here and reused
  in every document, so the concept is explained the same way everywhere.

## Discovery chain

1. A pointer line in `AGENTS.md` or the harness's memory-file equivalent:
   `Glossary: <path>`. Whatever it points at is the glossary.
2. `docs/GLOSSARY.md`.
3. None found: apply the rules without it, say so, offer setup, never block.

No ecosystem's filename is hardcoded. A `CONTEXT.md`, a `CLAUDE.md`, or a
wiki page are all valid pointer targets; none of them is the default.

## Admission rules

**Decisions, not detections.** A detected candidate is a proposal. It becomes
an entry when the user approves it. Harvesting finds candidates; only the
review round admits them.

**What earns an entry:**

- A domain concept the project names (Ledger, Settlement Window).
- A synonym cluster: several words orbiting one concept, where a decision is
  needed about which word wins.
- A recurring unnamed paraphrase: a phrase that keeps reappearing because the
  concept has no name. "A payment that has been authorized but not yet
  captured", written four times, is a term waiting to be coined.

**What does not:** a word used once, a word whose meaning is the industry's,
and anything whose home is upstream documentation.

## Stack terms

A stack term used with its ordinary industry meaning stays out of the
glossary. Upstream documentation owns "API", "webhook", "Postgres", and every
library name, and copying their definitions into your glossary caches the
environment (G-C1).

A stack term enters in exactly two cases:

1. **Narrowed meaning.** The project specialized it: "the Worker" means our
   Cloudflare Worker, not any worker; "migration" means only the generated
   kind. Record the narrowing and ban the looser usages.
2. **R1-S surfacing.** It appears in a stakeholder document and needs a gloss.
   This admits a **gloss-only entry**: term and stakeholder gloss, no banned
   synonyms, no redefinition of the industry's word.

## Who writes the glossary

Humans decide. Agents draft. This skill writes glossary entries only inside the setup or proposal flow in
`references/setup.md`, and only for entries the user has approved. Writing a
document never edits the glossary. A document
task that discovers a missing term reports it as a candidate and stops there.

Where the project's pointer targets a glossary another skill owns — a
`CONTEXT.md` under domain-modeling, for example — authorship defers to that
skill. Read the file, use its terms, flag what is missing, and recommend the
owning skill for the edit.
