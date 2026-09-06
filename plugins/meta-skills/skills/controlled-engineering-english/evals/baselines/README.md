# Baselines

## Why this directory exists

Every rubric line must be one that baseline Claude — no skill, no style —
already fails. A rubric line the baseline passes is a no-op: it grades the
model, not the skill, and it hides regressions behind guaranteed points. The
rule that produced a no-op line is suspect too, and gets flagged for the
deletion pass (`SKILL.md` Task 6.4, `rules.md` Task 7).

## Procedure (rerun this after any fixture change)

For each fixture, in a session with no CEE skill and no CEE output style
loaded, with only the fixture body (the HTML comment header removed):

    Rewrite this document.

Save the reply to `evals/baselines/<fixture>-baseline.md`. Then grade the
reply against the candidate rubric and delete every line it already passes.

## Status in this build

Transcripts were not generated here: this container has no clean-context
agent runner and no API credentials, so a transcript produced by the same
session that wrote the fixtures would be contaminated by knowing the planted
defects. The no-op pass below was therefore done by judgment against known
default behavior, and is marked as such. Regenerate real transcripts before
trusting the eval numbers.

## No-op findings (judgment pass, 2026-08-20)

Candidate rubric lines deleted as no-ops — baseline Claude does these
unprompted, so they cannot show the skill working:

| Deleted line | Register | Why it was a no-op |
|---|---|---|
| Converts passive voice to active | all three | Default rewrites already prefer active voice. |
| Adds markdown headings and structure | all three | Default rewrites already impose headings. |
| Fixes spelling and grammar | all three | Baseline behavior. |
| Splits the wall-of-text setup paragraph into steps | R1-E | Baseline reliably converts narrative instructions into a numbered list; what it does *not* do is drop the cached commands or restructure for lookup, and those lines survive. |
| Removes the closing pleasantries | R1-E | Baseline trims "we hope you find this useful" without being asked. |
| Shortens the longest sentences | all three | Baseline shortens sentences, but not to a stated ceiling; the surviving line is the measurable one (no sentence over 25 words). |

Rules flagged by this pass, to re-test in the deletion passes: **G-S1**
(active voice half is a no-op; the ≤25-word half is not), **G-P1** (baseline
prunes pleasantries but not restated-environment sentences).

Lines kept precisely because the baseline fails them: pointing at
`package.json` instead of restating commands, collapsing synonym clusters to
one glossary term, glossing terms inline for non-technical readers,
what-changed/why-it-matters/what-next ordering, problem→impact→next-step
failure reporting, numbers carrying comparisons, G-N1 keyword correction, and
moving implementation out of requirements.
