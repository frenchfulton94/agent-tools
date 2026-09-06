<!--
FIXTURE CONTEXT (not part of the document under test).

Audience: customer-facing release note, read by account managers and by
customers with no engineering background.

The repo's AGENTS.md contains the line:

  Glossary: docs/GLOSSARY.md

docs/GLOSSARY.md contains:

  | Term | POS | Meaning | Banned synonyms | Stakeholder gloss |
  |---|---|---|---|---|
  | Ledger | noun | The append-only record of every money movement. | transaction log, money record, journal | the Ledger — our permanent record of every payment |
  | Settlement Window | noun | The nightly period when payments are sent to the bank. | batch window, cutoff, nightly run | the Settlement Window — the nightly slot when payments go to your bank |

Planted defects: untranslated stack and project jargon with no glosses (S-1),
no what-changed / why-it-matters / what-next ordering (S-2), failure reported
cause-chain-first (S-3), bare numbers with no comparison (S-4), synonym drift
against the glossary (G-W1), hedged passive sentences over 25 words (G-S1).
-->

# Release 4.2.0

## Changelog

Following an investigation into elevated p99 latency on the settlement path,
it was determined that a lock contention issue in the Postgres advisory lock
layer, which was introduced when the batch window scheduler was refactored to
use a cron-based trigger instead of the previous polling loop, was causing
transactions to queue behind one another during the nightly run, and as a
result some customer payouts were delayed. A fix has now been shipped.

The idempotency key TTL is now 24h. Payout latency is 340ms. We also cut 12
rows from the journal writer hot path and the money record now uses a
covering index.

Additionally, the webhook retry backoff has been changed to exponential with
jitter, and the DLQ is now drained by a separate consumer group.

Customers who were affected may wish to reach out to their account manager.
