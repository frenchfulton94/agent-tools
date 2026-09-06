# Trigger battery: choosing-a-workflow

Run per the description-only routing protocol: give a clean-context agent this skill's description plus several distractor descriptions, one query at a time, and ask which skill applies or "none". Score positives and negatives separately; 3 reps each where feasible.

Useful distractors: **`configuring-openspec`** (the nearest sibling and the likeliest misroute in both directions), a generic project-planning skill, a debugging skill, and an incident-response runbook skill. The debugging and incident distractors matter because half the positives below are phrased as raw work — "prod is down", "this is dropping rows" — which a debugging skill will also claim.

## Should trigger (10)

1. Checkout is returning 502s and nobody can pay. What do we do?
2. The CSV export drops the last row for accounts in Alaska.
3. Coverage on the billing module is 40%. Add tests.
4. Should this be a feature change or is it small enough for the quick one?
5. I'm about to `openspec new change` for a Node LTS bump — which schema?
6. Drizzle or Prisma for the new service? I want to build a slice of each and see.
7. We started this as a rapid change but it turns out we're renaming an analytics event.
8. Take out the legacy SAML login path.
9. The search page takes nine seconds and it needs to be under two.
10. What are all the workflows this repo has and when would I use each?

Notes: 1, 2, 3, 6, 8, and 9 never mention a workflow, a schema, or OpenSpec — they are the raw-work positives, and they are the reason this skill exists, since nothing selects a schema automatically. 3 and 9 are the two rules people reliably get wrong (coverage backfill is a refactor; performance is a bugfix). 7 is the mid-flight reclassification case.

## Should not trigger (10)

1. My `rules:` block for `requirements:` does nothing and I get "Unknown artifact ID". *(`configuring-openspec` — config diagnosis)*
2. Add a research artifact between proposal and specs in our workflow file. *(`configuring-openspec` — schema authoring)*
3. Set up OpenSpec in this repo for the first time. *(`/workflows:setup`, not a routing question)*
4. Write the proposal for the PDF export change. *(doing the work inside a chosen workflow)*
5. Is this requirement testable enough? *(spec-writing craft)*
6. Why is this test failing? Here's the stack trace. *(actual debugging, no change being created)*
7. Which npm workspace does this package belong in? *(the word "which" plus a project-structure question)*
8. Draft a runbook for our on-call rotation. *(incident process, not an OpenSpec change)*
9. Rename this variable across the file. *(too small to be any change at all)*
10. What model should I use for writing tests in general? *(model choice with no artifact or chain in play)*

Notes: 1 and 2 are the boundary against `configuring-openspec` and are the negatives most worth getting right — the descriptions share "schema", "workflow", and "OpenSpec". 6 is the sharpest near-miss: a debugging request that is *not* a routing request, distinguished only by whether a change is being created. 10 tests that the model-and-effort reference does not pull the whole skill in on a bare model question.

## Scoring

Record should-trigger and should-not accuracy separately.

- **Positives failing** → the description is under-specified on raw-work phrasings. Add symptom triggers, not more schema names.
- **Negatives failing on 1–2** → the boundary clause against `configuring-openspec` is too weak; sharpen it rather than deleting schema vocabulary, which the positives need.
- **Negatives failing on 6** → the description reads as a debugging skill. The distinguishing fact is that a change is about to be created.

Revise from failures on a frozen ~60/40 train/validation split, generalize rather than pasting failed queries' keywords, keep the description under 1024 characters, and keep the iteration with the best validation score.
