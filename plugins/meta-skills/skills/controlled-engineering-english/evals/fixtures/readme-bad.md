<!--
FIXTURE CONTEXT (not part of the document under test).

The repo's package.json contains exactly these scripts:

  "scripts": {
    "dev": "vite --port 5180",
    "test": "vitest run",
    "db:migrate": "drizzle-kit push",
    "build": "vite build"
  }

The repo's AGENTS.md contains no glossary pointer, and docs/GLOSSARY.md
does not exist.

Planted defects: cached commands that have drifted from package.json (G-C1),
four names for one concept (G-W1), an undefined coined term (G-W2), setup
buried in narrative rather than structured for lookup (E-3), runbook steps
with no observable check (E-2), long passive hedged sentences (G-S1), no-op
sentences (G-P1).
-->

# Paystream

Paystream is a service that was built by our team in order to handle the
movement of money between accounts, and it is currently utilized by both the
web application and the mobile clients, which means that it is a fairly
central piece of infrastructure that a lot of things depend on. Welcome to the
repository!

## Getting started

Prior to commencing work on Paystream you will want to make sure that you have
Node installed, and once that has been done the dependencies can be installed
by running `npm install`, after which the development server may be started by
running `npm run start -- --port 3000`, which will bring the application up
locally. It should be noted that the test suite is run with `npm test --watch`
and that database migrations are applied by running `npm run migrate:dev`,
though this is generally only necessary when the schema has been changed by
someone. There is also a build command, `npm run build:prod`.

## How it works

Every movement of money is written to the ledger. The transaction log is
append-only, so entries are never edited after the fact. When a payment is
confirmed, a row is added to the money record and a second row is added for
the counterparty. Reconciliation reads the journal each night and compares
totals against the bank feed.

The system also performs SDR checks on each entry before it is committed.

## Deploying

1. Merge to `main`.
2. Run the deploy pipeline.
3. Check that the deploy worked.
4. Post in the team channel.

## Notes

We hope you find this project useful. This README is a living document and
will be updated over time as things change. Please reach out to the team if
you have any questions at all — we are happy to help!
