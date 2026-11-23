## Incident

<!-- Only when production broke and someone already mitigated. Delete otherwise.
     Timeline (detected, mitigated, stable), the mitigation taken, and who
     approved it. -->

## Feedback loop

<!-- The one command, already run, and its red output, redacted. -->

**Command:**

**Red output:**

- [ ] Red-capable: it asserts the user's exact symptom
- [ ] Deterministic: the same verdict every run, or a pinned high reproduction rate
- [ ] Fast: seconds, not minutes
- [ ] Agent-runnable: unattended, or driven by the skill's human-in-the-loop script

## Minimised reproduction

<!-- Every remaining element is load-bearing: removing any one turns the loop green. -->

**Observed:**

**Expected:**

## Hypotheses

<!-- Three to five, ranked, each falsifiable: "If <X> is the cause, then changing
     <Y> makes the bug disappear." Shown to the user on <date> before testing.
     Mark the survivor and the evidence that confirmed it. -->

1.

## Debug tag

<!-- The [DEBUG-xxxx] prefix every temporary log carries. -->

## Fix layer

<!-- Symptom or cause, with the reasoning. A symptom fix states what the cause
     fix needs. -->

## Seam

<!-- The correct seam for the regression test, agreed with the user on <date>,
     or "No correct seam" and why. -->

## Also found

<!-- Same-cause faults, which become task groups; unrelated faults, filed with
     their references; a new state the surface must show. Delete if none. -->

## Domain terms settled

<!-- Only when domain-modeling ran: the terms and ADRs written, matching the git
     diff of GLOSSARY.md and docs/adr/. Delete otherwise. -->
