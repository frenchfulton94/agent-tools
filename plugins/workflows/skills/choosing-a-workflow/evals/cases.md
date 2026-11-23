# Behavior cases: choosing-a-workflow

Run each case twice per repetition — once with the skill available, once without — in clean-context agents, in a fixture repository set up by `/workflows:setup` (seven flows installed) unless the case says otherwise. Grade every assertion PASS/FAIL with quoted evidence from the output; no benefit of the doubt. Assertions that pass in *both* configurations measure nothing and should be replaced.

The `[baseline]` note records what an unaided agent typically produces, which is what makes the assertion discriminating.

---

## Case 1 — Raw work, no vocabulary

**Prompt:** Coverage on the billing module is about 40%. We should add tests.

**Assertions:**

1. Routes to `refactor-flow`, not `feature-flow` and not a new test-writing task. *[baseline: usually treats "add tests" as new work, or does not mention a schema at all]*
2. States that coverage backfill is a refactor with no restructure and that the guard tests are the deliverable.
3. Returns a filled-in chat command — `/openspec-new-change <the work>, using refactor-flow` — with the schema actually named rather than left as a placeholder, not a bare `openspec new change` as the primary answer. *[baseline: gives the CLI form, often with `<schema>` unfilled]*
4. Names the chain as `grill → design → tasks`.
5. Names the guardrail: a guard assertion that has to change means behaviour changed, so reclassify as `feature-flow`.
6. Does **not** create the change, write an artifact, or begin writing tests. *[baseline: frequently starts writing tests immediately]*

---

## Case 2 — Two rules compete

**Prompt:** Checkout is throwing 502s in production right now, customers can't pay.

**Assertions:**

1. Says to mitigate first — roll back or flip the flag — before any change is opened. *[baseline: begins diagnosing]*
2. Routes to `bugfix-flow` with its Incident section, and does not name a `hotfix` schema. *[baseline: invents or assumes a hotfix workflow]*
3. Explains that rule 1 comes before rule 3, or equivalent.
4. Names the gate: a red feedback loop before any hypothesis.
5. Stops at the recommendation rather than starting to diagnose.

---

## Case 3 — A repository from before 0.10.0 (only `craft-driven` and `surface-driven` installed)

**Prompt:** We need to bump the framework past its EOL version. Which workflow?

**Assertions:**

1. Runs or references `openspec schemas` — or otherwise establishes which schemas this repository has — before recommending. *[baseline: recommends `upgrade-flow` from general knowledge]*
2. Does **not** present `upgrade-flow` as available; it is not installed here.
3. Says the installed schemas come from an earlier release and points at `/workflows:setup` to install the seven flows.
4. Does not invent a schema name.

---

## Case 4 — Mid-flight reclassification

**Prompt:** We opened this as a rapid change to update a config value, but it turns out the change renames an analytics event too.

**Assertions:**

1. States that the `rapid-flow` → `feature-flow` guardrail has fired, naming the analytics event as a contract.
2. Says to stop and recreate the change under `feature-flow`, rather than finishing in `rapid-flow` with a note. *[baseline: often suggests documenting the contract change and continuing]*
3. Returns the recreate command with `feature-flow` named in it — `/openspec-new-change <the work>, using feature-flow`.
4. Does not offer to split the contract change into a second `rapid-flow` change.

---

## Case 5 — Boundary against `configuring-openspec`

**Prompt:** My `rules:` block keyed to `requirements:` isn't doing anything and I keep seeing "Unknown artifact ID in rules".

**Assertions:**

1. Hands over to `configuring-openspec` rather than answering the config diagnosis itself. *[baseline: n/a — this case tests restraint, so the discriminating outcome is the handover]*
2. Does not recommend a schema, since no change is being created.
3. If it says anything substantive, it is limited to naming the artifact ids the installed schemas actually define.

---

## Case 6 — Genuine ambiguity

**Prompt:** The export is slow and the code behind it is a mess. We want it faster and cleaner.

**Assertions:**

1. Recognizes that two branches match — `bugfix-flow` (performance) and `refactor-flow` (structure) — rather than silently picking one. *[baseline: picks one and proceeds]*
2. Asks exactly **one** question, offering the two candidates and what distinguishes them.
3. Does not present a survey of all seven schemas.
4. If it recommends splitting into two changes, it says which comes first and why — performance work needs a measured baseline before code changes.

---

## Case 7 — Model question inside a chain

**Prompt:** We're at the design artifact on a feature-flow change. What model should I be on?

**Assertions:**

1. States that a subagent, `flow-design`, is dispatched for this artifact and is already pinned — so the main session does not need the top tier. *[baseline: recommends switching the session to the strongest model]*
2. Identifies the pin as `opus` at `xhigh`, or says the pin is read from the agent file.
3. Distinguishes a pin from a recommendation, or otherwise makes clear that this one executes on its own.
4. Mentions at least one of the two silent defeats — `CLAUDE_CODE_SUBAGENT_MODEL`, or the organisation's model allowlist.

---

## Case 8 — Upgrade

**Prompt:** We need to bump the framework past its EOL version. Which workflow?

**Assertions:**

1. Establishes which schemas this repository has before recommending.
2. Routes to `upgrade-flow`, not `feature-flow`. *[baseline: names a generic `upgrade` schema, which is not installed here]*
3. Names the chain as `inventory → surfaces → tasks`.
4. Names the guardrail: a deliberate behaviour change splits out into a `feature-flow` change.
5. Stops at the recommendation.

---

## Case 9 — Surface-only work

**Prompt:** The settings page feels cluttered. Can you rework the layout?

**Assertions:**

1. Routes the layout work to impeccable, not to a flow. *[baseline: opens a feature change]*
2. Does not offer `/openspec-new-change` for the layout work itself.
3. Says that any functionality the rework turns out to need becomes its own `feature-flow` change.
4. Stops at the recommendation.

---

## Case 10 — A feature with a surface

**Prompt:** Add an email preferences page so people can choose which notifications they get.

**Assertions:**

1. Routes to `feature-flow`. *[baseline: starts building the page]*
2. Says the surface is built through impeccable, in its own slice, after the behaviour behind it — or that the grill starts with impeccable's `shape`.
3. Returns `/openspec-new-change <the work>, using feature-flow`.
4. Does not route the whole request to impeccable: new behaviour is a change.

---

## Grading notes

Cases 1, 2, 4, and 8 test routing accuracy; case 3 tests that the preflight actually runs; case 5 tests the sibling boundary; case 6 tests the one-question rule; case 7 tests the model reference; cases 9 and 10 test the surface boundary from both sides. Cases 1, 2, and 4 also each carry a "stops at the recommendation" assertion, because *recommends and stops* is the behaviour most likely to erode first — an agent that routes correctly and then starts the work has failed the case.
