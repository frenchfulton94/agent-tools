# Trigger battery: configuring-openspec

Run per the description-only routing protocol: give a clean-context agent this skill's description plus several distractor descriptions, one query at a time, and ask which skill applies or "none". Score positives and negatives separately; 3 reps each where feasible.

Useful distractors: a generic YAML/config-editing skill, a git workflow skill, a technical-writing skill, and a requirements-engineering skill. Misrouting to or from a neighbor is the failure mode worth catching.

## Should trigger (10)

1. Our proposals keep ignoring that we're on Prisma and Vitest. How do I make the AI actually know our stack every time?
2. I forked spec-driven but `openspec new change foo` still uses the old workflow.
3. Can I add a security review step between design and tasks?
4. What goes in `openspec/config.yaml` versus `.openspec.yaml`?
5. `openspec schema validate` says template field is required — I copied the example from the docs.
6. We need our specs generated in Brazilian Portuguese. Is there a language setting?
7. Archive stopped merging anything into specs after I renamed some artifacts in our workflow file.
8. My rules block for `requirements:` isn't doing anything and I get "Unknown artifact ID".
9. How do I set this up on a 90k-line Rails app without documenting the whole thing first?
10. Our CI job that files completed changes just exits 1 with something about a prompt.

Notes: 1, 9, and 10 never name OpenSpec or a config file — they are the symptom-phrased positives. 8 names an artifact id that does not exist in `spec-driven`, which is exactly the reported-symptom shape.

## Should not trigger (10)

1. Write a proposal for adding dark mode to our settings page. *(using the workflow to do work, not configuring it)*
2. Review this requirement and tell me if it's testable enough. *(spec-writing craft; a requirements skill owns this)*
3. My `docker-compose.yaml` isn't picking up the env file. *(YAML config, wrong product)*
4. How do I resolve this merge conflict in `specs/auth/spec.md`? *(git, despite the OpenSpec path)*
5. Set up a JSON schema to validate our API request bodies. *("schema" keyword, unrelated domain)*
6. What's the difference between SHALL and SHOULD in RFC 2119? *(general knowledge)*
7. Create a Claude Code skill for our deployment runbook. *(authoring-skills owns this)*
8. Our npm global install isn't on PATH. *(generic Node tooling; only OpenSpec-specific if they name it)*
9. Turn this PRD into user stories for Jira. *(requirements work, different tooling)*
10. Add a pre-commit hook that runs our linter. *(hooks, unrelated)*

Notes: 3, 4, and 5 are the near-misses that matter — they share vocabulary (`yaml`, `spec.md`, `schema`) with genuine triggers. 7 tests the boundary against `authoring-skills`, which is the most likely sibling to steal or be stolen from.

## Scoring

Record should-trigger and should-not accuracy separately. If positives fail, the description is under-specified on symptom phrasings; if negatives fail, it is over-broad on the words "schema", "config", or "spec". Revise from failures on a frozen ~60/40 train/validation split, generalize rather than pasting failed queries' keywords, keep the description under 1024 characters, and keep the iteration with the best validation score.
