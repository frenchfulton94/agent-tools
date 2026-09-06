# Paystream

Paystream moves money between accounts. It runs as a Cloudflare Worker behind
our public API and calls out to the bank over a webhook.

Every movement of money is written to the ledger. The transaction log is
append-only. Reconciliation reads the journal each night during the batch
window and compares totals against the bank feed.

Merchants onboard through the dashboard. A seller who has completed KYC can
accept payments immediately; a vendor who has not is held in review.
