# Behavior cases: choosing-a-workflow

Run each case twice per repetition — once with the skill available, once without — in clean-context agents, in a fixture repository set up at the stated level. Grade every assertion PASS/FAIL with quoted evidence from the output; no benefit of the doubt. Assertions that pass in *both* configurations measure nothing and should be replaced.

The `[baseline]` note records what an unaided agent typically produces, which is what makes the assertion discriminating.

---

## Case 1 — Raw work, no vocabulary (repo at `advanced`)

**Prompt:** Coverage on the billing module is about 40%. We should add tests.

**Assertions:**

1. Routes to `refactor`, not `feature` and not a new test-writing task. *[baseline: usually treats "add tests" as new work, or does not mention a schema at all]*
2. States that coverage backfill is a refactor and that characterization is the deliverable.
3. Returns a filled-in chat command — `/opsx:new <the work>, using refactor` — with the schema actually named rather than left as a placeholder, not a bare `openspec new change` as the primary answer. *[baseline: gives the CLI form, often with `<schema>` unfilled]*
4. Names the chain as `characterization → strategy → tasks`.
5. Names the guardrail: a changed test assertion means behaviour changed, so reclassify as `feature`.
6. Does **not** create the change, write an artifact, or begin writing tests. *[baseline: frequently starts writing tests immediately]*

---

## Case 2 — Two rules compete (repo at `advanced`)

**Prompt:** Checkout is throwing 502s in production right now, customers can't pay.

**Assertions:**

1. Routes to `hotfix`, not `bugfix`.
2. Explains that rule 1 wins over rule 3 because production is down — i.e. states that first match wins, or equivalent. *[baseline: commonly routes to `bugfix`, since it is also genuinely a bug]*
3. Names the mandatory follow-up: a linked `bugfix` or `feature` change for the durable fix.
4. Mentions that triage takes minutes, or that rollback beats forward-fix when both are viable.
5. Stops at the recommendation rather than starting triage. *[baseline: tends to begin diagnosing]*

---

## Case 3 — Wrong level (repo at `standard`, two schemas installed)

**Prompt:** We need to bump the framework past its EOL version. Which workflow?

**Assertions:**

1. Runs or references `openspec schemas` — or otherwise establishes which schemas this repository has — before recommending. *[baseline: recommends `upgrade` from general knowledge]*
2. Does **not** recommend `upgrade`; it is not installed at this level.
3. Recommends one of the two present schemas, and says plainly that no dedicated upgrade schema exists here.
4. Does not invent a schema name.

---

## Case 4 — Mid-flight reclassification (repo at `advanced`)

**Prompt:** We opened this as a rapid change to update a config value, but it turns out the change renames an analytics event too.

**Assertions:**

1. States that the `rapid` → `feature` guardrail has fired, naming the analytics event as a public contract.
2. Says to stop and recreate the change under `feature`, rather than finishing in `rapid` with a note. *[baseline: often suggests documenting the contract change and continuing]*
3. Returns the recreate command with `feature` named in it — `/opsx:new <the work>, using feature`.
4. Does not offer to split the contract change into a second `rapid` change.

---

## Case 5 — Boundary against `configuring-openspec` (repo at `standard`)

**Prompt:** My `rules:` block keyed to `requirements:` isn't doing anything and I keep seeing "Unknown artifact ID in rules".

**Assertions:**

1. Hands over to `configuring-openspec` rather than answering the config diagnosis itself. *[baseline: n/a — this case tests restraint, so the discriminating outcome is the handover]*
2. Does not recommend a schema, since no change is being created.
3. If it says anything substantive, it is limited to naming the artifact ids the installed schemas actually define.

---

## Case 6 — Genuine ambiguity (repo at `advanced`)

**Prompt:** The export is slow and the code behind it is a mess. We want it faster and cleaner.

**Assertions:**

1. Recognizes that two branches match — `bugfix` (performance) and `refactor` (structure) — rather than silently picking one. *[baseline: picks one and proceeds]*
2. Asks exactly **one** question, offering the two candidates and what distinguishes them.
3. Does not present a survey of all eight schemas.
4. If it recommends splitting into two changes, it says which comes first and why — performance work needs a measured baseline before code changes.

---

## Case 7 — Model question inside a chain (repo at `standard`)

**Prompt:** We're at the design artifact on a craft-driven change. What model should I be on?

**Assertions:**

1. States that a subagent, `craft-design-gate`, is dispatched for this artifact and is already pinned — so the main session does not need the top tier. *[baseline: recommends switching the session to the strongest model]*
2. Identifies the pin as `opus` at `xhigh`, or says the pin is read from the agent file.
3. Distinguishes a pin from a recommendation, or otherwise makes clear that this one executes on its own.
4. Mentions at least one of the two silent defeats — `CLAUDE_CODE_SUBAGENT_MODEL`, or the organisation's model allowlist.

---

## Case 8 — Apple release routing (repo at `advanced`, Apple-native)

**Prompt:** The build's ready — get 1.4.0 out to TestFlight and then the App Store.

**Assertions:**

1. Routes to `app-release`, not `feature` and not ad hoc release steps. *[baseline: starts archiving or writes a release checklist inline]*
2. Names the chain as `release-scope → preflight → tasks → post-release`.
3. Returns a filled-in chat command — `/opsx:new <the work>, using app-release` — with the schema named.
4. Names the guardrail: a code defect discovered mid-release spawns a bugfix change; the release chain never absorbs code fixes.
5. Does **not** create the change, archive a build, or touch App Store Connect.

---

## Case 9 — Upgrade at `minimal` (repo at `minimal`, seven flows installed)

**Prompt:** We need to bump the framework past its EOL version. Which workflow?

**Assertions:**

1. Establishes which schemas this repository has before recommending.
2. Routes to `upgrade-flow`, not `upgrade` and not `feature-flow`. *[baseline: names advanced's `upgrade`, which is not installed here]*
3. Names the chain as `inventory → surfaces → tasks`.
4. Names the guardrail: a deliberate behaviour change splits out into a `feature-flow` change.
5. Stops at the recommendation.

---

## Case 10 — UI-led work at `minimal` (repo at `minimal`, web project)

**Prompt:** The settings page feels cluttered. Can you rework the layout?

**Assertions:**

1. Routes the layout work to impeccable, not to a flow. *[baseline: opens a feature change]*
2. Does not offer `/opsx:new` for the layout work itself.
3. Says that any functionality the rework turns out to need becomes its own `feature-flow` change.
4. Stops at the recommendation.

---

## Grading notes

Cases 1, 2, 4, 8, and 9 test routing accuracy; case 3 tests that the preflight actually runs; case 5 tests the sibling boundary; case 6 tests the one-question rule; case 7 tests the model reference; case 10 tests the UI boundary at minimal. Cases 1, 2, and 4 also each carry a "stops at the recommendation" assertion, because *recommends and stops* is the behaviour most likely to erode first — an agent that routes correctly and then starts the work has failed the case.
