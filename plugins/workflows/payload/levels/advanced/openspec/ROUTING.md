# Schema Router

Read this before creating any OpenSpec change. Classify the request, then create it
in chat, naming the schema in the sentence:

    /opsx:new <the work, in a sentence>, using <schema>

/opsx:new takes a kebab-case name or a description it derives one from, and passes
--schema through only when a schema is named - so naming it is what makes the routing
decision stick. The terminal equivalent, for scripts or when the slug is already
decided, is:

    openspec new change <slug> --schema <schema>

After creation, drive the chain with /opsx:continue <change>, one artifact per call,
naming the change every time. Before implementing: /clear, then /model (effort with
left/right) or /effort, then /opsx:apply <change> - clearing first, and with the name,
because clearing removes what apply would otherwise infer it from.

## Decision tree (first match wins)

1. Production is broken **now** (incident, outage, users blocked) → **hotfix**
2. Shipping a build to TestFlight or the App Store → **app-release**
   (installed only in Apple-native app repos; if the schema is absent, this entry does not apply)
3. New repository or project bootstrap ("init", "set up the project", "scaffold") → **setup**
4. Something behaves wrong vs. intent (bug, error, crash, regression, "too slow") → **bugfix**
   - Performance work is a bugfix: measure a baseline and set a numeric target before changing code.
5. Dependency/framework/platform version change (bump, EOL, CVE, "migrate to vN") → **upgrade**
6. Structure changes but behavior must not ("clean up", extract, rename, de-dupe, tech debt) → **refactor**
   - Coverage backfill ("add tests", "improve coverage", no behavior change) is a refactor: characterization is the deliverable.
7. An open question answered by building ("try", "compare", "POC", "feasibility", "which library") → **spike**
8. New capability or intentional behavior change, including removals and deprecations → **feature**
9. Trivial, low-risk, no contract impact (typo, copy, config value, docs) → **rapid**

## Prompt signals

- "X is broken / throws / returns the wrong thing" → bugfix
- "prod is down / urgent / do we roll back?" → hotfix
- "cut a release / submit to the App Store / push to TestFlight" → app-release
- "upgrade to <framework> vN / Node LTS / patch the CVE" → upgrade
- "no behavior change" stated or implied → refactor
- "prototype / spike / see if / which of A or B" → spike
- "new repo / greenfield project / bootstrap" → setup
- "add tests for X / raise coverage" → refactor
- "add / build / support / let users…" → feature
- "remove feature X" → feature (REMOVED delta specs + migration/sunset plan)

## Escalation and guardrails

- **rapid → feature**: the moment a public API, URL, analytics event, data
  schema, or config contract is touched, stop and recreate as feature.
- **spike**: code is throwaway — never merged. Learnings graduate through a new
  feature change.
- **hotfix**: must spawn a follow-up bugfix (durable root-cause fix) or feature
  change; postmortem.md links it.
- **app-release**: a code defect discovered mid-release stops the release and
  spawns a bugfix change — the release chain never absorbs code fixes. An
  urgent fix already live in the store routes its code work through hotfix;
  the expedited-review submission still goes through app-release, referencing it.
- **refactor → feature**: if any test assertion has to change, behavior is
  changing — stop and reclassify.
- Work too big for one change (an epic)? If the mattpocock pack is installed,
  ask the user to run /wayfinder (user-invoked) to map it as decision
  tickets, then create one
  OpenSpec change per resolved chunk - a change is a single unit of work.
- refactor changes may also originate from the user running
  /improve-codebase-architecture (user-invoked)
  (codebase scan for deepening opportunities); each accepted opportunity
  becomes its own refactor change.
- Standing-doc upkeep (CLAUDE.md/AGENTS.md audit, TOOLS.md refresh, glossary
  maintenance) routes to rapid and invokes the owning skill:
  managing-project-memory, mapping-project-tooling, or
  controlled-engineering-english's setup flow.
- When installing this router into AGENTS.md, let managing-project-memory
  decide placement (root file, @import, or rules file) - memory lines cost
  context every turn, and adherence drops past ~200 lines. Guidance that
  must fire every time belongs in a hook, not a memory line.
- De-escalate as readily as you escalate: when a feature brainstorm reveals
  bounded work, recreate under rapid; when it reveals a question in
  disguise, recreate under spike - one command against hours of ceremony.
- Ambiguous between two schemas? Ask one multiple-choice question, then route.
