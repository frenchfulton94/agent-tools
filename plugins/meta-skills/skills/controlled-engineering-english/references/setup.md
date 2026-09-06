# Glossary Setup

Run once per repo, when the user asks for it. The output is a glossary file,
a pointer line, and a compiled linter rule set. Nothing here runs as a side
effect of writing a document.

The one rule that governs the whole flow: **detections are not decisions.**
Steps 1 to 3 produce proposals. Step 4 is the only step that writes.

## Step 1: Locate

Follow the discovery chain first: an `AGENTS.md` pointer line (or the
harness's memory-file equivalent), then `docs/GLOSSARY.md`.

- **A glossary exists.** Read it. Extend it; do not restructure it. If another
  skill owns it, say so and hand the edit to that skill.
- **None exists.** Propose `docs/GLOSSARY.md` and ask whether to use it or
  another path.

Write the pointer line `Glossary: <path>` to `AGENTS.md` once the path is
settled. The pointer is what makes discovery work for every later session.

## Step 2: Harvest

Read the README, the docs directory, specs, release notes, and identifier
names. Collect three kinds of candidate:

1. **Domain nouns** that recur and belong to this project.
2. **Synonym clusters** — several words orbiting one concept. These are the
   highest-value finds, because each one is a decision nobody has made yet.
3. **Recurring unnamed paraphrases** — a phrase of a dozen words that keeps
   reappearing. A concept people describe repeatedly rather than name is a
   term waiting to be coined, and naming it is the single biggest
   comprehensibility win available.

Apply the stack-term rule from `dictionary.md` while harvesting. An ordinary
industry word is not a candidate. It becomes one only where the project
narrowed its meaning, or where it surfaced in a stakeholder document and needs
a gloss.

Note which document each candidate came from. A candidate found in a release
note needs a stakeholder gloss; one found only in a spec does not yet.

## Step 3: Review round

Present every candidate in one table, then ask one batched round of closed
questions.

    | # | Proposed term | Draft meaning | Detected synonyms | Draft gloss |
    |---|---|---|---|---|
    | 1 | Ledger | The append-only record of every money movement. | transaction log, money record, journal | our permanent record of every payment |

Per row, the user answers accept, rename, or trim. Use the harness's question
tool where one exists. Where none exists, ask as numbered prose questions in a
single message.

One round, batched. A term-by-term interrogation makes setup expensive enough
that people skip it, and a skipped setup is the failure mode that matters.

Where a draft meaning needs a fact the repo does not settle, ask it as part of
the same round rather than guessing.

## Step 4: Write

Write only the approved rows, in the format defined in `dictionary.md`. Leave
the gloss cell empty for terms that have not surfaced in a stakeholder
document; it gets backfilled on first use.

Then compile the deterministic rules:

    python3 scripts/glossary-to-vale.py <glossary-path> \
      scripts/vale/styles/CEE/Glossary.yml

Where Vale is not installed, still write the glossary. The compile step is a
convenience; the glossary is the deliverable.

## Step 5: Hand off

State the standing maintenance rule to the user, in one line. New terms are
proposed in document reports and written only after approval.

Where another skill owns the glossary file, add that this skill will read and
flag it but will not edit it.

## Verify before reporting done

- Nothing was written before the approval turn.
- Only approved rows are in the file.
- The pointer line is in `AGENTS.md` and points at the real path.
- Glosses exist for exactly the terms that surfaced in stakeholder documents.
- No entry redefines an ordinary industry word.
