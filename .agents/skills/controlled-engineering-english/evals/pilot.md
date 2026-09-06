# Pilot protocol (Phase 7)

Phases 1 to 6 are built and verified. Phase 7 needs a real repo and the user's
judgment, so it is written here as a protocol rather than executed.

## Task 15.3 — setup first

Run the setup flow on the target repo before the document pilot, so the
document runs have a glossary:

    Ask the skill: "set up a glossary for this repo."

The user approves the seed entries. Expect the harvest to over-propose;
trimming is the point of the review round. Record which candidates the user
rejected — a rejection pattern is a fix to the admission rules in
`dictionary.md`, not a fix to the individual entry.

## Task 15.1 — one real document per register

Run the skill on one real README, one real release note, and one real spec.
Save the before and after. Grade each against the same rubric shape used in
`evals.json`, then ask the user one question per document: what did it get
wrong, and what did it change that should have stayed?

## Task 15.2 — the style for a week

Install `assets/controlled-english.output-style.md` and work normally. Keep a
running note in three columns:

| Catch | Noise | Annoyance |
|---|---|---|
| The rule fired and the output was better | The rule fired and was wrong | The rule fired, was right, and was unwelcome |

Noise means the rule is mis-scoped: fix its wording. Annoyance means the rule
is right and badly placed: consider moving it from the distillation into the
skill, where it fires only on documents.

## Task 16 — closing the loop

Every complaint from the pilot becomes exactly one of three things:

1. A rule change. Bump `version:` in `references/rules.md`, get the user's
   approval, then rerun `python3 scripts/compile-targets.py` and both test
   scripts.
2. A rubric change in `evals.json`, with the baseline rerun to confirm the new
   line is not a no-op.
3. A documented waiver, with its reason and date.

Rerun all evals after any rule change. Then run the deletion pass again: for
each line of SKILL.md and each line of the distillation, ask whether the
agent would get it wrong without that line. Sediment collects fastest right
after a pilot.

## Deferred-work trigger to watch for

Design Appendix A promotes this skill to a plugin with an edit-time hook once
the detector proves useful enough to want on every markdown edit. The signal
is the catch column filling with cases the user would have wanted caught
automatically. Record the date that becomes true; it is the re-entry
condition.
