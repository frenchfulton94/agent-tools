<!--
FIXTURE CONTEXT (not part of the document under test).

Audience: engineers and agents implementing this later. Register: spec prose
(R1-E rules + G-N1 + E-4).

The repo's AGENTS.md contains the line:

  Glossary: docs/GLOSSARY.md

docs/GLOSSARY.md contains:

  | Term | POS | Meaning | Banned synonyms | Stakeholder gloss |
  |---|---|---|---|---|
  | Ledger | noun | The append-only record of every money movement. | transaction log, money record, journal | the Ledger — our permanent record of every payment |
  | Settlement Window | noun | The nightly period when payments are sent to the bank. | batch window, cutoff, nightly run | the Settlement Window — the nightly slot when payments go to your bank |

Planted defects: SHOULD used for absolute requirements and MUST used for a
recommendation (G-N1), implementation detail inside requirements (E-4),
scenarios that cannot be read aloud as sentences, synonym drift against the
glossary (G-W1), an undefined acronym (G-W2), hedged 30-word sentences and
passive voice (G-S1), no-op sentences (G-P1).

Out of scope for this fixture: skeleton grammar (heading depth, checkbox IDs,
delta keywords). Those are deferred to design Appendix A.
-->

# Spec: Refund handling

## Purpose

This spec describes refunds. Refunds are an important part of the product and
this document will describe how they should work in the system going forward.

## Requirements

1. A refund request should never be accepted after 90 days, and the system
   should reject it.
2. The refund handler must probably retry on transient failures where that
   seems reasonable.
3. When a refund is issued, the system should call
   `RefundService.apply()`, which will open a transaction against the
   `refunds` table using the Drizzle client, take an advisory lock on the
   payment ID, and write two rows to the transaction log with opposite signs
   before committing.
4. It is intended that refunds should be visible in the money record within
   one settlement cycle, assuming nothing has gone wrong upstream.
5. The RRN should be stored.

## Scenarios

- refund_expired: req>90d -> 422, no journal write, metric
  `refund.rejected.expired`++
- refund_ok: valid req -> 2 rows (dr/cr), status=SETTLED after cutoff
- refund_dup: same idem key twice -> second is no-op, 200
