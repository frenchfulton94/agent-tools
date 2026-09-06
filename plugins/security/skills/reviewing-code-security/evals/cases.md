# Behavioural cases

Each states a fixture, the assertion, and how to grade it. Grade against quoted evidence from the
output — no benefit of the doubt.

## Case 1: Every finding is cited

**Fixture:** any repository with at least one real flaw.
**Assert:** every entry under a severity heading names a file under `owasp/`.
**Grade:** fail if any finding has no `**Source:**` line, or names a file not in the corpus.

## Case 2: The corpus is never read whole

**Fixture:** "audit this repository".
**Assert:** at most 3 sheets are read for a diff review, at most 10 for a baseline.
**Grade:** count Read calls against `owasp/`. Fail on a glob or directory-wide read.

## Case 3: A clean target produces a clean report

**Fixture:** this marketplace repository, whose `.github/workflows/test.yml` already pins actions
to full commit SHAs.
**Assert:** unpinned-action is not reported; the coverage statement names what was not examined.
**Grade:** fail if the report raises SHA pinning, or pads with invented Low findings.

## Case 4: Ungrounded observations are segregated

**Fixture:** a repository using a technology no sheet covers (e.g. a bespoke binary protocol).
**Assert:** observations about it appear under "Unverified observations", not as findings.
**Grade:** fail if an uncited claim appears under a severity heading.

## Case 5: Scope discipline on a diff

**Fixture:** a branch touching one file that has a pre-existing unrelated flaw.
**Assert:** the flaw is one line under "pre-existing, out of scope" unless the diff made it
reachable.
**Grade:** fail if the review expands into a baseline audit of the whole file.
