# Spec: Payouts

1. A payout MUST be written to the money record before it is sent.
2. Payouts are sent during the nightly run.
3. A payment that has been authorized but not yet captured is not payable.
4. A partner MUST be verified before their first payout.

## Notes

A payment that has been authorized but not yet captured may expire after
seven days. When a payment that has been authorized but not yet captured
expires, the hold is released and the merchant is notified.

The Worker retries failed payouts three times before the cutoff.
