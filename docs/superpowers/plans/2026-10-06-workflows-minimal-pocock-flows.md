# Pocock-Driven Minimal Flows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `workflows` plugin's `minimal` level (`mattpocock-bridge` + `bugfix-flow` + three agents) with seven `-flow` OpenSpec schemas driven only by mattpocock-skills 1.3.1, one `flow-design` agent, a router, and a guarded installer retirement step for the names the level no longer ships.

**Architecture:** Payload content (schemas, templates, agent, router, config) is pinned by a new Bun test that parses every schema, checks its graph, and checks every skill call and slash command against a fixed 1.3.1 roster. The installer gains one detection fact (`openspec.changeSchemas`), one plan section (`retire`), and one record rule (drop deleted retired names). Routing and setup prose follow.

**Tech Stack:** OpenSpec 1.14.0 schema YAML and Markdown templates; Node ESM scripts (`.mjs`) with hand-written `.d.mts` declarations; Bun 1.4.2 test runner (`bun:test`, `Bun.YAML.parse`).

**Spec:** `docs/superpowers/specs/2026-10-06-workflows-minimal-pocock-flows-design.md` — read it alongside this plan. Its decision log (§2) is binding; a change to any decision reopens the design.

## Global Constraints

- **Branch:** `workflows-minimal-pocock-flows` (carries the spec commit `8e2940f`). Execute in an isolated worktree via `superpowers:using-git-worktrees`.
- **Gates before any commit touching `plugins/`:** `bun test` AND `bun run audit` (repo `CLAUDE.md`). Both MUST pass.
- **Version:** `plugins/workflows/.claude-plugin/plugin.json` `0.7.0` → `0.8.0`, in Task 11 only. No version field anywhere else.
- **Required skills per surface (spec §15) — load BEFORE editing:**
  - schemas, templates, `ROUTING.md`, `config.yaml.example` → `configuring-openspec`
  - schema `instruction:` blocks, the agent prompt, template wording → `improving-prompts`
  - `flow-design.md` → `authoring-subagents`
  - `SKILL.md` edits → `authoring-skills`
  - payload layout, version bump, plugin README → `authoring-plugins`
  - marketplace entry → `maintaining-plugin-marketplaces`
  A loaded skill that surfaces a defect in this plan's text: fix it, and say what changed in the commit message.
- **Skill-call phrasing (pinned by the Task 1 test):** a model-invoked skill is called only as `Call the Skill tool with "<name>"`, `Call the Skill tool twice, for "<a>" and "<b>"`, or the same with a lowercase `call`. The word `invoke` MUST NOT appear in minimal schema or agent text. A user-invoked skill is offered to the human as `/<name>`.
- **Allowed slash commands in minimal schema, agent, and router text:** the 16 user-invoked Pocock skills, `/opsx:*`, `/clear`, `/compact`, `/model`, `/effort`, `/impeccable …`, and `/mattpocock-skills:<user-invoked skill>`.
- **Retired terms** MUST NOT appear anywhere under `payload/levels/minimal/` except `retired.json`: `CONTEXT.md`, `CONTEXT-MAP.md`, `to-prd`, `to-issues`, `/diagnose`, `mattpocock-bridge`. Beware paths: `<change>/diagnose.md` contains `/diagnose`; write `diagnose.md` alone.
- **Version stamp:** every minimal schema `description` ends with the sentence `Written against mattpocock-skills 1.3.1.`
- **Checkbox form:** every checkbox line in a template starts with exactly `- [ ] `.
- **Names:** schemas `feature-flow`, `bugfix-flow`, `refactor-flow`, `spike-flow`, `upgrade-flow`, `setup-flow`, `rapid-flow`; agent file `flow-design.md`.
- **JSON style:** tabs, as in the existing `settings.json` files.
- **Code comments:** match `plan.mjs` / `record.mjs` — constraint-explaining comments in that register; never narrate what a line does.
- **No `typecheck` script exists** despite the `.d.mts` headers mentioning one. Keep every `.d.mts` in sync by hand.
- **Known drift, out of scope (spec §17):** `learn/` (about 30 files) still names `mattpocock-bridge` and "twelve"; the plugin README's Learn paragraph is left as is. Do not edit `learn/`.
- **OpenSpec facts verified 2026-10-06 on 1.14.0:** `openspec new change` writes `.openspec.yaml` as `schema: <name>`, `created: <date>`, and adds `skip_specs: true` by itself when the schema has no `specs` artifact; `openspec validate <change> --strict` accepts such a change.
- **Schema validation snippet** (run from the worktree root; used by Tasks 1–4):

  ```bash
  validate_flow() {  # usage: validate_flow <schema-name>
    local d; d="$(mktemp -d)"
    ( cd "$d" && git init -q \
      && OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec init --tools claude >/dev/null 2>&1 \
      && mkdir -p openspec/schemas \
      && cp -R "$OLDPWD/plugins/workflows/payload/levels/minimal/openspec/schemas/$1" openspec/schemas/ \
      && OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec schema validate "$1" )
  }
  ```

  Expected: `✓ Schema '<name>' is valid`.

## Review Focus

Inputs the spec implies that would bite a real user, each pinned by a test in the owning task:

1. **An `.openspec.yaml` whose `schema:` value is quoted or carries a trailing comment** (`schema: 'bugfix-flow' # router pick`). Detection must still read the bare name, or retirement deletes a schema an open change uses. → Task 6, "reads each open change's schema, quoted or not".
2. **An archived change under `openspec/changes/archive/` that used a retired schema.** It must not keep the retired schema alive forever. → Task 6, "archived changes are not open".
3. **An open change whose `.openspec.yaml` names no schema.** It may resolve against the old default, so every retired schema and its agents must be kept. → Task 7, "an open change naming no schema keeps it".
4. **A schema that calls a skill with non-canonical phrasing** ("invoke `tdd`"), which would slip past the roster check. → Task 1, "calls only model-invoked Pocock skills, in the canonical phrasing" asserts no `invoke`.
5. **A detection object with no `changeSchemas` field** (an older saved detection piped into a newer plan). It must not read as "no open changes". → Task 7, "a detection without changeSchemas keeps retired schemas".

## File Map

| Path | Task | Responsibility |
|---|---|---|
| `tests/workflows-minimal-flows.test.ts` | 1, 2, 5 | Pins minimal payload: roster, phrasing, retired terms, structure, agent, level shape |
| `plugins/workflows/payload/levels/minimal/openspec/schemas/bugfix-flow/**` | 1 | Rewritten defect flow |
| `.../schemas/feature-flow/**` | 2 | Feature flow, config default |
| `plugins/workflows/payload/levels/minimal/agents/flow-design.md` | 2 | Design agent |
| `.../schemas/refactor-flow/**`, `.../schemas/spike-flow/**` | 3 | Refactor and spike flows |
| `.../schemas/upgrade-flow/**`, `.../schemas/setup-flow/**`, `.../schemas/rapid-flow/**` | 4 | Upgrade, setup, rapid flows |
| `.../minimal/openspec/ROUTING.md`, `README.md`, `config.yaml.example`, `.../minimal/retired.json` | 5 | Router, level docs, config, retirement list |
| `plugins/workflows/scripts/detect.mjs`, `detect.d.mts`, `tests/workflows-detect.test.ts` | 6 | `openspec.changeSchemas` |
| `plugins/workflows/scripts/plan.mjs`, `plan.d.mts`, `tests/workflows-plan.test.ts` | 7 | `plan.retire` |
| `plugins/workflows/scripts/record.mjs`, `record.d.mts`, `tests/workflows-record.test.ts` | 8 | Record drops deleted retired names |
| `plugins/workflows/skills/setup/SKILL.md`, `scripts/config-facts.mjs` | 9 | Setup prose: level row, retirement step, router install |
| `plugins/workflows/skills/choosing-a-workflow/**` | 10 | Routing skill, chains, model-effort, evals |
| `plugins/workflows/README.md`, `.claude-plugin/plugin.json`, `/.claude-plugin/marketplace.json` | 11 | Counts, version |

Removed in Task 5: `.../schemas/mattpocock-bridge/`, `.../agents/bridge-design-gate.md`, `.../agents/code-review-spec.md`, `.../agents/code-review-standards.md`, `.../minimal/openspec/CLAUDE.md.fragment.md`. Removed in Task 1: `.../schemas/bugfix-flow/README.md`.

---

### Task 1: Minimal-flow test harness and the bugfix-flow rewrite

**Files:**
- Create: `tests/workflows-minimal-flows.test.ts`
- Modify: `plugins/workflows/payload/levels/minimal/openspec/schemas/bugfix-flow/schema.yaml` (full rewrite)
- Modify: `.../bugfix-flow/templates/diagnose.md`, `.../templates/spec.md`, `.../templates/tasks.md` (full rewrites)
- Delete: `.../bugfix-flow/README.md` (it names the retired schema; the level README in Task 5 replaces it)

**Interfaces:**
- Consumes: nothing.
- Produces: the test file's helpers, which Tasks 2 and 5 extend in place: `ROSTER`, `RETIRED_TERMS`, `MINIMAL`, `SCHEMAS`, `AGENTS`, `subdirs(d)`, `filesUnder(d)`, `readSchema(name): Schema`, `schemaText(name): string`, `skillCalls(text): string[]`, `slashCommands(text): string[]`, `isAllowedCommand(cmd): boolean`, and the `describe.each(flows)` structure block, which automatically covers every `*-flow` schema directory that exists.

**Required skills:** `configuring-openspec` (read `plugins/workflows/skills/configuring-openspec/references/custom-schemas.md`), `improving-prompts`.

- [ ] **Step 1: Write the test file**

```ts
// tests/workflows-minimal-flows.test.ts
import { describe, expect, test } from 'bun:test';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

/**
 * The minimal level is pinned to one release of mattpocock-skills. The two lists are the
 * upstream plugin manifest's skills split by each SKILL.md's `disable-model-invocation`, at
 * the version below. Re-checking the level against a new release means updating this
 * object and every schema's "Written against" stamp together.
 */
const ROSTER = {
	version: '1.3.1',
	modelInvoked: [
		'tdd', 'diagnosing-bugs', 'domain-modeling', 'codebase-design', 'code-review', 'prototype',
		'research', 'pr', 'wizard', 'grilling', 'writing-for-agents',
	],
	userInvoked: [
		'ask-matt', 'grill-with-docs', 'grill-me', 'implement', 'implement-spec',
		'improve-codebase-architecture', 'retro', 'setup-matt-pocock-skills', 'to-spec', 'to-tickets',
		'triage', 'wayfinder', 'handoff', 'to-questionnaire', 'teach', 'wait-what',
	],
};

/** Harness built-ins a flow may offer the human; every other command is a Pocock skill, OpenSpec, or impeccable. */
const HARNESS_COMMANDS = new Set(['clear', 'compact', 'model', 'effort']);
/** Names upstream renamed or this level retired. Their presence means an instruction rotted. */
const RETIRED_TERMS = ['CONTEXT.md', 'CONTEXT-MAP.md', 'to-prd', 'to-issues', '/diagnose', 'mattpocock-bridge'];

const LEVELS = join(import.meta.dir, '..', 'plugins', 'workflows', 'payload', 'levels');
const MINIMAL = join(LEVELS, 'minimal');
const SCHEMAS = join(MINIMAL, 'openspec', 'schemas');
const AGENTS = join(MINIMAL, 'agents');

const subdirs = (d: string): string[] =>
	existsSync(d) ? readdirSync(d).filter((n) => statSync(join(d, n)).isDirectory()).sort() : [];
const filesUnder = (d: string): string[] =>
	readdirSync(d).flatMap((n) => {
		const p = join(d, n);
		return statSync(p).isDirectory() ? filesUnder(p) : [p];
	});

interface Artifact {
	id: string;
	generates: string;
	template: string;
	instruction: string;
	requires?: string[];
}
interface Schema {
	name: string;
	version: number;
	description: string;
	artifacts: Artifact[];
	apply: { requires: string[]; tracks: string; instruction: string };
}

const readSchema = (name: string): Schema =>
	Bun.YAML.parse(readFileSync(join(SCHEMAS, name, 'schema.yaml'), 'utf8')) as Schema;
const textOf = (paths: string[]): string => paths.map((p) => readFileSync(p, 'utf8')).join('\n');
const schemaText = (name: string): string => textOf(filesUnder(join(SCHEMAS, name)));

/** Every skill a text calls, read from the one phrasing minimal schemas may use. */
function skillCalls(text: string): string[] {
	const flat = text.replace(/\s+/g, ' ');
	const calls: string[] = [];
	for (const m of flat.matchAll(/[Cc]all the Skill tool (?:with|twice, for|three times, for) ((?:"[a-z0-9-]+"(?:,? (?:and )?)?)+)/g)) {
		for (const n of m[1].matchAll(/"([a-z0-9-]+)"/g)) calls.push(n[1]);
	}
	return calls;
}

/**
 * Every slash command a text offers. The lookbehind rejects path separators (`docs/adr`,
 * `<change>/research`, `https://`) so only a command a person would type is returned.
 */
function slashCommands(text: string): string[] {
	return [...text.matchAll(/(?<![\w/.:<>\]-])\/([a-z][a-z0-9-]*(?::[a-z0-9-]+)?)/g)].map((m) => m[1]);
}

function isAllowedCommand(cmd: string): boolean {
	const bare = cmd.replace(/^mattpocock-skills:/, '');
	return (
		ROSTER.userInvoked.includes(bare) || cmd.startsWith('opsx:') || HARNESS_COMMANDS.has(cmd) || cmd === 'impeccable'
	);
}

const flows = subdirs(SCHEMAS).filter((n) => n.endsWith('-flow'));

describe('the scanners themselves', () => {
	test('skillCalls reads one and two-skill calls, across line breaks', () => {
		expect(skillCalls('Call the Skill tool twice, for "grilling" and\n      "domain-modeling". Then call the Skill tool with "tdd".')).toEqual([
			'grilling',
			'domain-modeling',
			'tdd',
		]);
	});

	test('slashCommands finds commands and ignores paths and URLs', () => {
		expect(
			slashCommands('Offer `/retro`, then /opsx:apply <change>. Not docs/adr/, <change>/research/, or https://x.dev/a.'),
		).toEqual(['retro', 'opsx:apply']);
	});
});

describe('minimal schema and agent names stay disjoint from the other levels', () => {
	test('no name a minimal schema or agent uses is shipped by standard or advanced', () => {
		const others = new Set<string>();
		for (const level of ['standard', 'advanced', join('advanced', 'apple')]) {
			for (const s of subdirs(join(LEVELS, level, 'openspec', 'schemas'))) others.add(s);
			const agents = join(LEVELS, level, 'agents');
			if (existsSync(agents)) for (const a of readdirSync(agents)) others.add(a);
		}
		const mine = [...subdirs(SCHEMAS), ...(existsSync(AGENTS) ? readdirSync(AGENTS) : [])];
		expect(mine.filter((n) => others.has(n))).toEqual([]);
	});
});

test('bugfix-flow keeps its name and its diagnose artifact, so in-flight changes resolve', () => {
	expect(flows).toContain('bugfix-flow');
	expect(readSchema('bugfix-flow').artifacts[0].id).toBe('diagnose');
});

describe.each(flows)('%s', (name) => {
	const schema = readSchema(name);
	const ids = schema.artifacts.map((a) => a.id);

	test('name matches its directory', () => {
		expect(schema.name).toBe(name);
	});

	test('description stamps the roster version', () => {
		expect(schema.description).toContain(`Written against mattpocock-skills ${ROSTER.version}.`);
	});

	test('artifact ids are unique', () => {
		expect(new Set(ids).size).toBe(ids.length);
	});

	test('each artifact requires only artifacts declared before it, so the graph is acyclic', () => {
		const seen = new Set<string>();
		for (const a of schema.artifacts) {
			expect((a.requires ?? []).filter((r) => !seen.has(r))).toEqual([]);
			seen.add(a.id);
		}
	});

	test('every referenced template exists', () => {
		const missing = schema.artifacts.filter((a) => !existsSync(join(SCHEMAS, name, 'templates', a.template)));
		expect(missing.map((a) => a.template)).toEqual([]);
	});

	test('apply requires declared artifacts and tracks a generated file', () => {
		expect(schema.apply.requires.filter((r) => !ids.includes(r))).toEqual([]);
		expect(schema.artifacts.map((a) => a.generates)).toContain(schema.apply.tracks);
	});

	test('a specs artifact, when present, generates under specs/', () => {
		const specs = schema.artifacts.find((a) => a.id === 'specs');
		if (specs) expect(specs.generates).toBe('specs/**/*.md');
	});

	test('every checkbox in a template uses the exact "- [ ] " form', () => {
		const bad: string[] = [];
		for (const p of filesUnder(join(SCHEMAS, name, 'templates'))) {
			for (const line of readFileSync(p, 'utf8').split('\n')) {
				if (/^\s*[-*]\s*\[/.test(line) && !/^- \[ \] /.test(line)) bad.push(`${relative(SCHEMAS, p)}: ${line}`);
			}
		}
		expect(bad).toEqual([]);
	});

	test('calls only model-invoked Pocock skills, in the canonical phrasing', () => {
		const text = schemaText(name);
		expect(skillCalls(text).filter((s) => !ROSTER.modelInvoked.includes(s))).toEqual([]);
		expect(text.match(/\binvoke\b/gi) ?? []).toEqual([]);
		expect(text.match(/Skill tool with "impeccable"/g) ?? []).toEqual([]);
	});

	test('offers only Pocock user-invoked commands, OpenSpec, harness built-ins, or impeccable', () => {
		expect(slashCommands(schemaText(name)).filter((c) => !isAllowedCommand(c))).toEqual([]);
	});

	test('names no retired term', () => {
		const text = schemaText(name);
		expect(RETIRED_TERMS.filter((t) => text.includes(t))).toEqual([]);
	});
});
```

- [ ] **Step 2: Run the tests to confirm the old bugfix-flow fails them**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: FAIL. At least these `bugfix-flow` tests fail: "description stamps the roster version", "calls only model-invoked Pocock skills, in the canonical phrasing" (the old text says `Invoke`), and "names no retired term" (`CONTEXT.md`, `mattpocock-bridge`). The scanner tests and the disjointness test pass.

- [ ] **Step 3: Rewrite `bugfix-flow/schema.yaml`**

```yaml
name: bugfix-flow
version: 2
description: >
  Defect fixes, where the problem is known and the cause is not.
  diagnose -> specs -> tasks -> apply. The fix waits for a red feedback
  loop and a confirmed hypothesis: diagnosing-bugs' phases 1 to 4 run in
  diagnose, and phases 5 and 6 run at apply. Incidents arrive here after
  someone has mitigated them. Written against mattpocock-skills 1.3.1.

artifacts:
  - id: diagnose
    generates: diagnose.md
    description: Red feedback loop, minimised reproduction, confirmed cause, fix layer, and the regression seam
    template: diagnose.md
    instruction: |
      Find the cause before anyone writes a fix.

      Route first:
      - A raw incoming report nobody has verified goes to /triage before a
        change exists. Offer it to the human.
      - A fix that changes behaviour the product promises, rather than
        restoring it, is a feature. Say so and offer
        /opsx:new <the change>, using feature-flow.
      - Layout, contrast, copy, and polish problems belong to impeccable,
        not to this flow.

      Call the Skill tool with "diagnosing-bugs". Work its phases 1 to 4
      here and stop when phase 4 confirms a cause; phases 5 and 6 run at
      apply. Follow its Redact rule in everything this file records.

      Fill the template:
      - Incident: only when production broke and someone already
        mitigated. Record the timeline, the mitigation, and who approved
        it. Delete the section otherwise.
      - Feedback loop: the one command, already run, and its red output.
        Tick the skill's four bars. No red command means no phase 2.
      - Minimised reproduction: observed versus expected, cut until every
        remaining element is load-bearing.
      - Hypotheses: three to five, ranked and falsifiable. Show the list to
        the user before testing. Mark the survivor and the evidence that
        confirmed it.
      - Debug tag: the [DEBUG-xxxx] prefix your instrumentation used, so
        cleanup is one grep even after a /clear.
      - Fix layer: symptom or cause, with the reasoning. A symptom fix
        states what the cause fix needs, so the next person inherits the
        choice rather than the surprise.
      - Seam: a correct seam exercises the real bug pattern the way its
        call site does. Agree it with the user; AskUserQuestion suits the
        approve-or-adjust. Where none exists, write "No correct seam" and
        why. That is a finding, not a gap.
      - Also found: faults that share this cause become task groups.
        Unrelated faults get their own change; file them and note the
        reference.

      Where a term the diagnosis depends on is fuzzy, call the Skill tool
      with "domain-modeling" and write the term to GLOSSARY.md as it
      settles. Then fill Domain terms settled from the git diff of
      GLOSSARY.md and docs/adr/. Delete that section when the skill did
      not run.
    requires: []

  - id: specs
    generates: "specs/**/*.md"
    description: The case the spec missed or got wrong, with the reproduction as its scenario
    template: spec.md
    instruction: |
      Decide whether this fault changes what the system promises, and
      write the delta when it does. Read the capability's spec under
      openspec/specs/ and compare it with the fault:
      - The spec covered the case and the code disagreed: no delta is
        owed. Set skip_specs: true in the change's .openspec.yaml and write
        no file here. The regression test holds the line.
      - The spec was silent about the case that broke: add the case as an
        ADDED requirement. Expect this outcome most often.
      - The spec said something the fault proves wrong: use MODIFIED. Copy
        the whole requirement block from the main spec, header included,
        then edit it. Archive replaces the block by matching that header.

      Write to specs/<capability-path>/spec.md at the exact existing path.
      A fix that seems to need a new capability is probably a feature.

      Format: "### Requirement: <name>" stated with SHALL or MUST, then
      "#### Scenario: <name>" with WHEN and THEN bullets. Scenarios take
      exactly four hashtags; the parser drops other levels without a
      warning. Write the scenario so the minimised reproduction satisfies
      it: the scenario is the reproduction made permanent. Assert the error
      kind, never the wording a user reads.
    requires:
      - diagnose

  - id: tasks
    generates: tasks.md
    description: Failing test, fix, cleanup, and the Ship group
    template: tasks.md
    instruction: |
      Write the work as checkboxes in test-first order. Most fixes are one
      group: the failing test at the seam from diagnose.md, the fix, any
      same-cause extras, and cleanup. Checkboxes take the exact "- [ ] "
      form; apply cannot see any other shape.

      Add a second group only when the cause spans modules, or when a
      symptom fix ships now and the cause fix follows. Give the cause fix
      its own tracker issue so it outlives the urgency.

      Write the session shape on the Session line. A fix that fits one
      context window is single-session and needs no tracker issue. For a
      multi-session fix, read docs/agents/issue-tracker.md and publish one
      issue per group, labelled ready-for-agent, in dependency order. If
      that file is missing, ask the human to run /setup-matt-pocock-skills.

      Where diagnose.md's Seam says "No correct seam", replace the failing
      test item with "Record the missing seam in the commit message", and
      keep the Ship group's /improve-codebase-architecture item.

      Where the fix makes the surface show a new state, add the Ship item
      "Surface hand-off: impeccable presents <state> from <seam>".
    requires:
      - specs

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Fix it test-first at the agreed seam. Read diagnose.md first: the
    reproduction tells you when you are done, and the fix layer tells you
    where you may work. This is diagnosing-bugs' phases 5 and 6.

    1. Note the start commit. Call the Skill tool with "tdd". Turn the
       minimised reproduction into a failing test at the seam, and watch it
       fail for the diagnosed reason, not a nearby one.
    2. Make the smallest fix at the agreed layer. Watch the test pass.
    3. Re-run the feedback-loop command against the original, unminimised
       scenario.
    4. Clean up: grep the debug tag until nothing remains, and delete any
       throwaway harness.
    5. Typecheck and run the full suite.
    6. Commit. The message names the hypothesis that turned out correct.
    7. Call the Skill tool with "code-review". The fixed point is the start
       commit; the spec source is diagnose.md and the delta specs. Fix the
       findings in one follow-up commit; do not loop the review.
    8. Tick tasks.md and update any issue.

    Where diagnose.md says "No correct seam", skip the test in step 1 and
    record why in the commit message; the feedback loop still proves the
    fix.

    When the work goes up as a pull request, call the Skill tool with "pr"
    and give it diagnose.md and the delta specs as well as the diff.

    When the fix does not hold, diagnose.md is wrong. Update it, not the
    code. code-review judges best from a fresh session on a strong model;
    tell the user so. Finish by offering the human /retro in this session,
    framed as "what would have prevented this bug?". Where there was no
    correct seam, also offer /improve-codebase-architecture. Run neither
    yourself.
```

- [ ] **Step 4: Rewrite the three templates**

`templates/diagnose.md`:

```markdown
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
     their references. Delete if none. -->

## Domain terms settled

<!-- Only when domain-modeling ran: the terms and ADRs written, matching the git
     diff of GLOSSARY.md and docs/adr/. Delete otherwise. -->
```

`templates/spec.md`:

```markdown
## ADDED Requirements

<!-- The case the spec was silent about. Use MODIFIED instead where the fault
     proves an existing requirement wrong, copying the whole block first. Where
     the spec was already right, set skip_specs: true and delete this file. -->

### Requirement: <!-- requirement name -->
<!-- The behaviour, using SHALL or MUST. -->

#### Scenario: <!-- scenario name -->
<!-- The minimised reproduction, made permanent. Assert the error kind, not the wording. -->
- **WHEN** <!-- condition -->
- **THEN** <!-- observable outcome -->
```

`templates/tasks.md`:

```markdown
**Session:** <!-- single-session | multi-session -->

## 1. <!-- what is being fixed --> (<!-- tracker reference, or local -->)

- [ ] 1.1 Failing test at <!-- seam from diagnose.md --> reproducing the fault
- [ ] 1.2 <!-- the fix, at the agreed layer -->
- [ ] 1.3 <!-- a same-cause extra from Also found, or delete this line -->
- [ ] 1.4 Cleanup: the debug tag greps to nothing, and throwaway harnesses are deleted

<!-- A second group only when the cause spans modules, or when a symptom fix
     ships now and the cause fix follows with its own tracker issue. -->

## Ship

- [ ] The commit or PR names the hypothesis that turned out correct
- [ ] code-review findings resolved in one follow-up commit
- [ ] /retro offered to the human
- [ ] /improve-codebase-architecture offered <!-- only when there was no correct seam; delete otherwise -->
```

- [ ] **Step 5: Delete the per-schema README**

Run: `git rm plugins/workflows/payload/levels/minimal/openspec/schemas/bugfix-flow/README.md`

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS, every test.

- [ ] **Step 7: Validate the schema with OpenSpec**

Run: `validate_flow bugfix-flow` (snippet in Global Constraints)
Expected: `✓ Schema 'bugfix-flow' is valid`

- [ ] **Step 8: Run the repository gates**

Run: `bun test && bun run audit`
Expected: both exit 0.

- [ ] **Step 9: Commit**

```bash
git add tests/workflows-minimal-flows.test.ts plugins/workflows/payload/levels/minimal/openspec/schemas/bugfix-flow
git commit -m "Pin the minimal flows to mattpocock-skills 1.3.1 and rewrite bugfix-flow

bugfix-flow now follows diagnosing-bugs' six phases: a red feedback loop,
ranked hypotheses, a debug tag, and a no-correct-seam finding, with an
optional Incident section. A new test pins every minimal schema's skill
calls, slash commands, and structure to the 1.3.1 roster.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: feature-flow and the flow-design agent

**Files:**
- Create: `plugins/workflows/payload/levels/minimal/openspec/schemas/feature-flow/schema.yaml`
- Create: `.../feature-flow/templates/grill.md`, `proposal.md`, `spec.md`, `design.md`, `tasks.md`
- Create: `plugins/workflows/payload/levels/minimal/agents/flow-design.md`
- Modify: `tests/workflows-minimal-flows.test.ts` (append the agent block)

**Interfaces:**
- Consumes: Task 1's helpers (`AGENTS`, `ROSTER`, `RETIRED_TERMS`, `skillCalls`, `slashCommands`, `isAllowedCommand`). The `describe.each(flows)` block picks up `feature-flow` with no edit.
- Produces: schema name `feature-flow` with artifact ids `grill`, `proposal`, `specs`, `design`, `tasks` (Task 5's config test requires `proposal`). Agent file `flow-design.md`, run by name from `feature-flow` and `refactor-flow` design instructions (Task 3). The agent's two schema modes are selected by the prompt naming `feature-flow` or `refactor-flow`.

**Required skills:** `configuring-openspec`, `improving-prompts`, `authoring-subagents` (for `flow-design.md`).

- [ ] **Step 1: Append the agent tests**

Add at the end of `tests/workflows-minimal-flows.test.ts`:

```ts
describe('flow-design agent', () => {
	const path = join(AGENTS, 'flow-design.md');

	test('exists', () => {
		expect(existsSync(path)).toBe(true);
	});

	test('frontmatter pins the top model and names its tools', () => {
		const raw = readFileSync(path, 'utf8');
		const fm = Bun.YAML.parse(raw.split(/^---$/m)[1]) as Record<string, string>;
		expect(fm.name).toBe('flow-design');
		expect(fm.description.length).toBeGreaterThan(0);
		expect(fm.tools).toContain('Read');
		expect(fm.tools).toContain('Skill');
		expect(fm.model).toBe('opus');
		expect(fm.effort).toBe('xhigh');
	});

	test('calls only model-invoked Pocock skills and names no retired term', () => {
		const text = readFileSync(path, 'utf8');
		expect(skillCalls(text).filter((s) => !ROSTER.modelInvoked.includes(s))).toEqual([]);
		expect(text.match(/\binvoke\b/gi) ?? []).toEqual([]);
		expect(slashCommands(text).filter((c) => !isAllowedCommand(c))).toEqual([]);
		expect(RETIRED_TERMS.filter((t) => text.includes(t))).toEqual([]);
	});
});
```

- [ ] **Step 2: Run the tests to verify the agent block fails**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: FAIL — `flow-design agent > exists` fails and the frontmatter test throws `ENOENT`. Everything else passes.

- [ ] **Step 3: Write `feature-flow/schema.yaml`**

```yaml
name: feature-flow
version: 1
description: >
  A new capability or an intentional behaviour change, in the shape of
  Matt Pocock's main flow: grill -> proposal -> specs -> design -> tasks
  -> apply. The flows own functionality up to a presentation seam;
  impeccable owns UI/UX. The config default. Written against
  mattpocock-skills 1.3.1.

artifacts:
  - id: grill
    generates: grill.md
    description: Decision log from the interview, with the glossary and ADRs written inline
    template: grill.md
    instruction: |
      Interview the user until you share an understanding, then record what
      was settled.

      Classify the work first, and reroute when it is not a feature:
      - a defect: /opsx:new <what is broken>, using bugfix-flow;
      - one decision wide, touching no contract: recreate under rapid-flow;
      - a question in disguise: recreate under spike-flow;
      - too big and foggy for one change: stop and offer the human
        /wayfinder. Its cleared map re-enters this flow at the proposal.
      Read the source the change started from before asking anything: a
      /triage agent brief, a wayfinder map, or an impeccable brief.

      Call the Skill tool twice, for "grilling" and "domain-modeling". Ask
      in grilling's own rounds. Write each term to GLOSSARY.md, and each ADR
      to docs/adr/, in the round that settles it: a term pinned in round
      one is one that rounds two and three can use precisely.

      Two detours leave files; put them where they survive:
      - A logic or state question that needs a runnable answer: call the
        Skill tool with "prototype". It keeps the code on a prototype/<name>
        branch. Record the verdict, the question it settled, and the branch.
      - A question that needs facts from outside the repository: call the
        Skill tool with "research". Save its file at
        openspec/changes/<change>/research/<topic>.md and cite it.

      Look and feel belong to impeccable. When the change has a surface,
      write "look and feel: impeccable" under Handed downstream and ask
      only behaviour questions.

      Ask what changes the shape of the problem. Module placement, typing,
      and seams belong to design; slicing and sequencing belong to tasks.
      Record each such question under Handed downstream with the artifact
      that owns it, and move on.

      Done when the user confirms you share an understanding, and Domain
      terms settled matches the git diff of GLOSSARY.md and docs/adr/, or
      says "none". The human may run /grill-with-docs instead; save what it
      settles here. Where the user waives the interview, write grill.md as
      one line holding the reason and the date.
    requires: []

  - id: proposal
    generates: proposal.md
    description: Why and what, in the /to-spec shape, kept inside the change
    template: proposal.md
    instruction: |
      Synthesise grill.md into the proposal without a new interview. A
      statement the user never made is a defect: every statement must trace
      to grill.md.

      Sections:
      - Problem and Solution, from the user's perspective.
      - User Stories: a long numbered list, "As a <actor>, I want <feature>,
        so that <benefit>", covering every behaviour this change adds. Specs
        turns each story into requirements, so a missing story is a missing
        requirement.
      - Capabilities: read openspec/specs/ first. Each new capability
        becomes specs/<capability-path>/spec.md, kebab-case, following the
        existing layout. Each modified capability names its exact existing
        path and which requirement changes or goes. A change with no
        capability to add or modify belongs in refactor-flow or rapid-flow.
      - Out of Scope.
      - Impact: affected modules and systems. Name any ADR this contradicts
        and make the case for reopening it.

      Use GLOSSARY.md's terms. Describe modules and behaviour, not file
      paths, which go stale. Inline a prototype snippet only when it encodes
      a decision more precisely than prose can. Keep it to one or two
      pages: why and what, never how.

      This is /to-spec's shape, kept in the change folder so it archives
      with the change. Do not offer /to-spec here: it publishes a
      ready-for-agent issue that AFK pollers would build.
    requires:
      - grill

  - id: specs
    generates: "specs/**/*.md"
    description: Delta specs, the behaviour contract this change adds, modifies, or removes
    template: spec.md
    instruction: |
      Turn the proposal into delta specs: what the system must do,
      observably, once this change lands. Write one file per capability in
      the proposal, at specs/<capability-path>/spec.md. The CLI reports this
      output as the glob specs/**/*.md; expand it to real files.

      Two sources:
      - ADDED requirements come from the user stories. Every story maps to
        at least one requirement, and every ADDED requirement traces to a
        story. Walk both directions before finishing.
      - MODIFIED and REMOVED requirements come from the main spec at
        openspec/specs/<capability-path>/spec.md.

      A spec states observable behaviour: inputs, outputs, error kinds, and
      constraints such as security and compatibility. If the implementation
      can change without changing what a caller observes, it belongs in
      design. For a change a surface consumes, specify the states the module
      emits, such as empty, error, and permission denied, and its error
      kinds. How a state looks and reads belongs to impeccable: never assert
      wording a user reads.

      Format:
      - Group under ## ADDED, ## MODIFIED, ## REMOVED, or ## RENAMED
        Requirements.
      - "### Requirement: <name>", stated with SHALL or MUST.
      - "#### Scenario: <name>" with WHEN and THEN bullets. Exactly four
        hashtags; the parser drops other levels without a warning.
      - Every requirement carries at least one scenario.
      - MODIFIED copies the whole requirement block from the main spec,
        header included. Archive replaces the block by its header.
      - REMOVED gives a Reason and a Migration. When it removes a
        capability's last requirement, set retire_capabilities: true in the
        change's .openspec.yaml and tell the user archive will delete that
        main spec.
      - RENAMED uses FROM: and TO: lines.
      - A new capability opens with ## Purpose, at least 50 characters.

      Write each scenario so it could become a test at a seam.
    requires:
      - proposal

  - id: design
    generates: design.md
    description: Module shape, the seams tests are written at, and the decisions behind both
    template: design.md
    instruction: |
      Decide how to build it and where it is tested from.

      Run the flow-design agent (.claude/agents/flow-design.md). Its prompt
      names the change directory and says the schema is feature-flow; an
      agent inherits nothing else. It returns a design.md draft, ADR
      candidates, and caller actions. Then:
      1. Write the draft here.
      2. Put each ADR candidate to the user as a yes or no. For each one
         accepted, call the Skill tool with "domain-modeling" and write it
         to docs/adr/ in that skill's format.
      3. Resolve with the user every returned question that would change
         the specs or the tasks. Only questions that change neither may stay
         under Open Questions.
      4. Put the Seams table to the user through AskUserQuestion: approve,
         or adjust. tdd writes tests only at agreed seams.
      5. Where a surface consumes this change, confirm the Presentation seam
         block names the consumer surface and its brief path.

      If the agent is missing or fails, say so, call the Skill tool with
      "codebase-design", and draft the same sections inline.

      Never skip this artifact. A one-module change shrinks design.md to the
      Seams table, because apply cannot test without agreed seams. Fill
      Domain terms settled from the git diff of GLOSSARY.md and docs/adr/,
      or write "none".
    requires:
      - proposal
      - specs

  - id: tasks
    generates: tasks.md
    description: Tracer-bullet slices, published when the build spans sessions, mirrored as checkboxes
    template: tasks.md
    instruction: |
      Break the work into tracer-bullet slices, agree them with the user,
      and mirror them here as checkboxes.

      1. Choose the session shape and write it on the Session line.
         Single-session: the whole build fits one fresh context window;
         apply continues in this window and tasks live only here.
         Multi-session: anything larger; slices go to the tracker.
      2. Draft slices. Each cuts a narrow, complete path through every layer
         it touches, so a finished slice is demoable alone. Size each to one
         fresh context window. Put prefactoring first: make the change easy,
         then make the easy change. Give each slice its blocking edges. A
         wide refactor, one mechanical change whose blast radius fans out,
         runs expand, migrate, contract instead; batches that cannot stay
         green alone share an integration branch, and a final
         integrate-and-verify slice, blocked by every batch, promises green.
      3. Present the slices as a numbered list: title, blocked by, and what
         it delivers. Put the verdict to the user through AskUserQuestion:
         approve, or name what to merge, split, or resequence. Iterate until
         approved.
      4. Multi-session only: read docs/agents/issue-tracker.md, or ask the
         human to run /setup-matt-pocock-skills if it is missing. Publish one
         issue per slice in dependency order, labelled ready-for-agent, with
         the tracker's native blocking edges. When the change started from
         an issue, make each slice its sub-issue. The human may run
         /to-tickets instead; then mirror what it published.
      5. Mirror the slices here in the same order, as
         "## N. <title> (<tracker reference, or local>)" with
         "- [ ] N.M <acceptance criterion>" lines. Apply tracks only the
         exact "- [ ] " form.
      6. Keep the template's Ship group. Where a surface consumes this
         change and must ship with it, add
         "Surface hand-off: impeccable builds <surface> against <seam>".

      Done when every slice has a group, and every multi-session group
      names a real tracker reference.
    requires:
      - specs
      - design

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Build one slice at a time, test-first, reviewed before it lands.

    Read tasks.md's Session line. Single-session: continue in this window.
    Multi-session: work one slice per fresh session, and fetch its tracker
    issue for the acceptance criteria. Take any slice whose blockers are
    done. The human may run /implement-spec over the whole ticket graph
    instead; after it returns, tick tasks.md from the closed tickets. For
    most unattended work, Matt Pocock recommends a deterministic loop that
    runs one slice per fresh session over /implement-spec.

    For each slice:
    1. Note the start commit. Call the Skill tool with "tdd". Write tests
       only at seams design.md agreed. A wrong seam stops the slice: agree
       a new one with the user and update design.md first.
    2. Typecheck and run the affected tests as you go.
    3. Run the full suite.
    4. Commit.
    5. Call the Skill tool with "code-review". The fixed point is the start
       commit; the spec source is proposal.md and the delta specs. It
       judges best from a fresh session on a strong model; tell the user so.
    6. Fix the findings in one follow-up commit. Do not loop the review.
    7. Tick the slice's boxes and update its issue.

    Surface work is impeccable's. Build up to the presentation seam and
    leave the surface to the hand-off item.

    When the work goes up as a pull request, call the Skill tool with "pr"
    and give it the delta specs as well as the diff.

    After the last slice, tick the Ship group and offer the human /retro;
    never run it yourself. Pause and ask when a slice is unclear, when the
    design proves wrong (name the artifact to update), or when an error
    will not resolve.
```

- [ ] **Step 4: Write the five templates**

`templates/grill.md`:

```markdown
## Question

<!-- What this change set out to settle, in one or two lines. -->

## Decisions

<!-- One entry per question the interview resolved, in the order asked:
     ❓ Q1, <title>: <question>
     ✅ <the user's answer>
     ↩ <alternatives ruled out, and why> -->

## Domain terms settled

<!-- Terms added or changed in GLOSSARY.md and ADRs written under docs/adr/,
     matching the git diff, or "none". -->

## Detours

<!-- Prototype verdicts with their prototype/<name> branch; research files and
     what they said. Delete if none. -->

## Handed downstream

<!-- Questions that belong to a later artifact, each naming it: design, tasks,
     or "look and feel: impeccable". Delete if none. -->

## Still open

<!-- What the user deferred, and what a different answer would change. Delete if
     none. -->
```

`templates/proposal.md`:

```markdown
## Problem

<!-- The problem, from the user's perspective. -->

## Solution

<!-- The solution, from the user's perspective. -->

## User Stories

<!-- A long numbered list covering every behaviour this change adds. Specs turns
     each story into requirements. -->

1. As a <actor>, I want <feature>, so that <benefit>

## Capabilities

### New Capabilities
<!-- Each becomes specs/<capability-path>/spec.md. Kebab-case new segments;
     follow the existing layout under openspec/specs/. -->
- `<capability-path>`: <what this capability covers>

### Modified Capabilities
<!-- The exact existing path, and which requirement changes or goes. -->
- `<existing-capability-path>`: <which requirement is changing>

## Out of Scope

<!-- What this change deliberately does not do. -->

## Impact

<!-- Affected modules and systems. Name any ADR this contradicts and make the
     case for reopening it. -->
```

`templates/spec.md`:

```markdown
## Purpose
<!-- New capabilities only: one or two sentences, at least 50 characters, on what
     this capability is for. Delete this section for an existing capability. -->

## ADDED Requirements

### Requirement: <!-- requirement name -->
<!-- The behaviour, using SHALL or MUST. Assert error kinds, never user-facing wording. -->

#### Scenario: <!-- scenario name -->
- **WHEN** <!-- condition -->
- **THEN** <!-- observable outcome -->
```

`templates/design.md`:

```markdown
## Context

<!-- Current state and the constraints that shape the approach. Point at
     proposal.md for motivation rather than restating it. -->

## Goals / Non-Goals

**Goals:**

**Non-Goals:**

## Decisions

<!-- Each choice, its rationale, and the alternatives weighed, in codebase-design's
     vocabulary: module, interface, implementation, depth, seam, adapter,
     leverage, locality. Carry grill-settled decisions forward with their
     reasoning. -->

## Seams

<!-- The public boundaries this change is tested at. Every scenario in specs/ is
     observable from exactly one seam. Agreed with the user on <date>. -->

| Seam | Exposes | Covers scenarios |
|---|---|---|
|  |  |  |

<!-- One regression row per REMOVED requirement: the check and the seam it sits at. -->

## Presentation seam

<!-- Only when a surface consumes this module; delete otherwise. Impeccable builds
     the surface against this block. -->

- **Interface:**
- **Emitted states:**
- **Error kinds:**
- **Fixtures:** <!-- one per emitted state -->
- **Consumer surface:** <!-- its name and its brief under .impeccable/surfaces/ -->

## Risks / Trade-offs

<!-- [Risk] -> Mitigation -->

## Migration

<!-- Expand, migrate, contract for schema and data changes; the rollback; any
     point of no return. Delete when not applicable. -->

## Open Questions

<!-- Only questions whose answer changes neither the specs, the approach, nor the
     tasks. Delete if none. -->

## Domain terms settled

<!-- Terms and ADRs written during design, matching the git diff, or "none". -->
```

`templates/tasks.md`:

```markdown
**Session:** <!-- single-session | multi-session -->

## 1. <!-- slice title --> (<!-- tracker reference, or local -->)
<!-- Blocked by: none -->

- [ ] 1.1 <!-- acceptance criterion -->
- [ ] 1.2 <!-- acceptance criterion -->

## Ship

- [ ] code-review findings resolved in one follow-up commit
- [ ] Shipped: a PR whose body came from the pr skill, or a direct merge (say which)
- [ ] /retro offered to the human
```

- [ ] **Step 5: Write `agents/flow-design.md`**

```markdown
---
name: flow-design
description: Drafts design.md for a feature-flow or refactor-flow change in codebase-design's deep-module vocabulary - decisions, the Seams table, the Presentation seam block, guard tests for a refactor, and ADR candidates. Use when a feature-flow or refactor-flow change reaches its design artifact.
tools: Read, Grep, Glob, Skill, Bash
model: opus
effort: xhigh
---

You draft design.md for one OpenSpec change. You run in a fresh context: you
have this prompt, the change directory you are given, and the repository. You
cannot ask the user anything, so return your questions for the caller to ask.

## Input

The prompt that started you names the change directory and its schema,
feature-flow or refactor-flow. Read, in order:

1. `grill.md`: decisions already settled. Carry each forward with its
   reasoning; never re-argue one.
2. For feature-flow only: `proposal.md` for scope and capabilities, then every
   file under `specs/`. Every scenario must land in the Seams table.
3. `GLOSSARY.md`, or `GLOSSARY-MAP.md` and the relevant `GLOSSARY.md`, and the
   ADRs under `docs/adr/` that touch this area. Use the glossary's terms
   exactly. Name any ADR a decision contradicts, and make the case for
   reopening it.
4. The touched code. Prefer seams the codebase already has.

If `grill.md` is missing, or a feature-flow change lacks `proposal.md` or its
specs, return only caller actions naming what is missing. Never design against
a partial chain.

## Skills

Call the Skill tool with "codebase-design", and use its terms exactly: module,
interface, implementation, depth, seam, adapter, leverage, locality. Call the
Skill tool with "domain-modeling" for the ADR format and its three-part test.

## Deliverable

Return three parts, clearly separated.

**1. design.md**, following the template already in the change directory.

For feature-flow:

- Context, Goals / Non-Goals, and Decisions with rationale and alternatives.
- Seams: the public boundaries this change is tested at. Every scenario in
  `specs/` is observable from exactly one seam, named by scenario. A scenario
  no seam reaches is either a missing seam or an unobservable requirement; say
  which, and never leave the row blank. Add a regression row for each REMOVED
  requirement, naming the check and its seam. Prefer existing seams, as high as
  possible and as few as possible; one is the ideal.
- Presentation seam, only when a user interface consumes this module: the
  interface, every state the module emits, the error kinds, one fixture per
  emitted state, and the consumer surface with its brief under
  `.impeccable/surfaces/`. The flow stops at this seam; impeccable builds the
  surface against it.
- Risks / Trade-offs as `[Risk] -> Mitigation`. Migration, for schema or data
  changes, as expand, migrate, contract with the rollback. Open Questions only
  for answers that would change nothing in the specs, the approach, or the
  tasks.

For refactor-flow:

- Context; Target interface with its invariants, ordering, and error modes;
  Seam and adapters with the dependency category; Guard tests at the external
  seam that must stay green with no assertion changed, or a note that the
  first task writes them; Tests to replace; Decisions; Risks / Trade-offs.
- Introduce no seam that nothing varies across: one adapter is a hypothetical
  seam, two make a real one.

**2. ADR candidates**, zero or more, in domain-modeling's format: a title and
one to three sentences giving the context, the decision, and why. Include only
decisions that pass all three tests: hard to reverse, surprising without
context, and the result of a real trade-off. State how each passes. The caller
writes the ones the user accepts.

**3. Caller actions:** every question whose answer would change the specs, the
approach, or the tasks; the reminder that the Seams table, or the Guard tests
for a refactor, needs the user's approval before the artifact is done; and,
when a Presentation seam exists, confirmation of the consumer surface.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS, including the new `feature-flow` block from `describe.each` and the `flow-design agent` block.

- [ ] **Step 7: Validate the schema with OpenSpec**

Run: `validate_flow feature-flow`
Expected: `✓ Schema 'feature-flow' is valid`

- [ ] **Step 8: Run the repository gates**

Run: `bun test && bun run audit`
Expected: both exit 0.

- [ ] **Step 9: Commit**

```bash
git add tests/workflows-minimal-flows.test.ts \
  plugins/workflows/payload/levels/minimal/openspec/schemas/feature-flow \
  plugins/workflows/payload/levels/minimal/agents/flow-design.md
git commit -m "Add feature-flow and the flow-design agent to the minimal level

feature-flow runs Matt Pocock's main flow inside OpenSpec: grill, a
/to-spec-shaped proposal, delta specs, a design whose Seams table is never
skipped, and tasks that record a single- or multi-session shape. Review
runs after the commit. flow-design drafts the design on the top model.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 3: refactor-flow and spike-flow

**Files:**
- Create: `.../minimal/openspec/schemas/refactor-flow/schema.yaml` and `templates/grill.md`, `templates/design.md`, `templates/tasks.md`
- Create: `.../minimal/openspec/schemas/spike-flow/schema.yaml` and `templates/question.md`, `templates/findings.md`

**Interfaces:**
- Consumes: Task 1's `describe.each(flows)` block (covers both schemas with no test edit); Task 2's `flow-design` agent, run by `refactor-flow`'s design with the schema named `refactor-flow`.
- Produces: `refactor-flow` ids `grill`, `design`, `tasks`; `spike-flow` ids `question`, `findings`, with `apply.tracks: question.md`.

**Required skills:** `configuring-openspec`, `improving-prompts`.

- [ ] **Step 1: Confirm the test baseline**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS. Neither schema exists yet, so `describe.each` has nothing new to cover. The schemas' tests appear in Step 5.

- [ ] **Step 2: Write `refactor-flow/schema.yaml`**

```yaml
name: refactor-flow
version: 1
description: >
  Structure changes while behaviour at the external seam does not:
  deepening a module, in codebase-design's deep-module vocabulary.
  grill -> design -> tasks -> apply. No specs artifact, so changes archive
  without a spec merge. Coverage backfill is a refactor with no
  restructure. Written against mattpocock-skills 1.3.1.

artifacts:
  - id: grill
    generates: grill.md
    description: The deepening candidate, what moves behind the seam, and the behaviour that must not change
    template: grill.md
    instruction: |
      Settle what is being deepened and what must not move.

      Guard first: if behaviour a caller can observe at the external seam
      has to change, this is a feature. Say so and offer
      /opsx:new <the change>, using feature-flow.

      Read the change's source first: a candidate from the human's
      /improve-codebase-architecture report, a bugfix that found no correct
      seam, or the request itself. When /improve-codebase-architecture
      already grilled this candidate in this window, record its decisions
      here instead of asking again.

      Otherwise call the Skill tool twice, for "grilling" and
      "domain-modeling", and call the Skill tool with "codebase-design" for
      the vocabulary. Settle, in rounds:
      - the module being deepened, and what moves behind its seam;
      - the dependency category: in-process, local-substitutable, ports and
        adapters, or mock;
      - the external behaviour that must not change, stated so a test can
        pin it.
      Coverage backfill with no restructure is valid here: say so, and the
      guard tests become the whole deliverable.

      Done when the user confirms you share an understanding, and Domain
      terms settled matches the git diff of GLOSSARY.md and docs/adr/, or
      says "none".
    requires: []

  - id: design
    generates: design.md
    description: Target interface, seam and adapters, the guard tests, and the tests to replace
    template: design.md
    instruction: |
      Design the deepened module and the tests that prove nothing moved.

      When the user wants alternative interfaces, run codebase-design's
      design-it-twice here in the main session before anything else. It
      fans out its own parallel sub-agents, so it cannot run inside an
      agent. Record the chosen interface in grill.md's Decisions.

      Run the flow-design agent (.claude/agents/flow-design.md). Its prompt
      names the change directory and says the schema is refactor-flow. Write
      its draft here. Then:
      1. Put each ADR candidate to the user as a yes or no. For each one
         accepted, call the Skill tool with "domain-modeling" and write it
         to docs/adr/.
      2. Put the Guard tests and the Seam and adapters section to the user
         through AskUserQuestion: approve, or adjust.
      3. Resolve every returned question that would change the tasks.

      If the agent is missing or fails, say so, call the Skill tool with
      "codebase-design", and draft the same sections inline.

      Two rules from codebase-design bind this design. One adapter means a
      hypothetical seam and two mean a real one, so introduce no seam that
      nothing varies across. And replace, don't layer: list the shallow
      tests that the new interface tests make redundant, for deletion once
      their replacements pass. Fill Domain terms settled from the git diff,
      or write "none".
    requires:
      - grill

  - id: tasks
    generates: tasks.md
    description: Ordered slices, each green and committable, ending in deletion of the old form
    template: tasks.md
    instruction: |
      Sequence the restructure so the guard tests stay green after every
      slice.

      Write the session shape on the Session line. Single-session work
      continues in this window. Multi-session work publishes one issue per
      slice to the tracker in docs/agents/issue-tracker.md, labelled
      ready-for-agent, with native blocking edges; ask the human to run
      /setup-matt-pocock-skills if that file is missing.

      Order:
      1. Guard tests first, where design.md says they are missing.
      2. Prefactoring that makes the move easy.
      3. The deepening itself: vertical slices where it can be, or expand,
         migrate, contract where one mechanical change fans out. Expand adds
         the new interface beside the old. Migrate moves call sites in
         batches sized by blast radius, each blocked by the expand. Contract
         deletes the old form and the replaced shallow tests, blocked by
         every batch.
      4. The Ship group.

      Every slice's last criterion is "Guard tests green, no guard
      assertion changed". Present the slices as a numbered list and get
      them approved through AskUserQuestion. Checkboxes take the exact
      "- [ ] " form.
    requires:
      - design

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Restructure one slice at a time, with the guard tests green throughout.

    For each slice:
    1. Note the start commit. Call the Skill tool with "tdd" for new tests
       at the seam design.md agreed.
    2. Run the guard tests and the affected tests as you go. A guard
       assertion that has to change means behaviour moved: stop, revert
       the slice, and offer /opsx:new <the change>, using feature-flow.
    3. Delete a shallow test only once its replacement at the new interface
       passes.
    4. Run the full suite, then commit.
    5. Call the Skill tool with "code-review". The fixed point is the start
       commit; the spec source is grill.md and design.md. Fix the findings
       in one follow-up commit.
    6. Tick the slice and update its issue.

    A refactor that leaves both the old and the new form is unfinished;
    the contract slice deletes the old one. When the work goes up as a pull
    request, call the Skill tool with "pr". Finish by offering the human
    /retro; never run it yourself.
```

- [ ] **Step 3: Write the refactor-flow templates**

`templates/grill.md`:

```markdown
## Candidate

<!-- Where this came from: an /improve-codebase-architecture report, a bugfix with
     no correct seam, or the request. -->

## Decisions

<!-- One entry per question the interview resolved, in the order asked:
     ❓ Q1, <title>: <question>
     ✅ <the user's answer>
     ↩ <alternatives ruled out, and why> -->

## Module and seam

<!-- The module being deepened, what moves behind its seam, and the dependency
     category: in-process, local-substitutable, ports and adapters, or mock. -->

## Must not change

<!-- The external behaviour the guard tests pin, stated so a test can assert it. -->

## Domain terms settled

<!-- Terms and ADRs written, matching the git diff, or "none". -->

## Handed downstream

<!-- Questions that belong to design or tasks, each naming its artifact. Delete if
     none. -->
```

`templates/design.md`:

```markdown
## Context

<!-- The current shape and why it is shallow. -->

## Target interface

<!-- Types, invariants, ordering, and error modes: everything a caller must know. -->

## Seam and adapters

<!-- Where the interface lives, the adapters at it, and the dependency category.
     New tests go here. Agreed with the user on <date>. -->

## Guard tests

<!-- Tests at the external seam that stay green with no assertion changed. If none
     exist, the first task writes them. Agreed with the user on <date>. -->

| Guard test | Pins |
|---|---|
|  |  |

## Tests to replace

<!-- Shallow tests the new interface tests make redundant. Delete each once its
     replacement passes. -->

## Decisions

<!-- Each choice, its rationale, and the alternatives weighed. -->

## Risks / Trade-offs

<!-- [Risk] -> Mitigation -->

## Domain terms settled

<!-- Terms and ADRs written during design, matching the git diff, or "none". -->
```

`templates/tasks.md`:

```markdown
**Session:** <!-- single-session | multi-session -->

## 1. Guard tests (<!-- tracker reference, or local -->)
<!-- Delete this group when the guard tests already exist. -->

- [ ] 1.1 <!-- guard test --> passes against the current code

## 2. <!-- slice title --> (<!-- tracker reference, or local -->)
<!-- Blocked by: 1 -->

- [ ] 2.1 <!-- what moved -->
- [ ] 2.2 Guard tests green, no guard assertion changed

## Ship

- [ ] The old form and the replaced shallow tests are deleted
- [ ] code-review findings resolved in one follow-up commit
- [ ] Shipped: a PR whose body came from the pr skill, or a direct merge (say which)
- [ ] /retro offered to the human
```

- [ ] **Step 4: Write `spike-flow/schema.yaml` and its templates**

```yaml
name: spike-flow
version: 1
description: >
  A timeboxed question answered by building or reading: logic, state,
  feasibility, library choice, or outside facts. question -> findings,
  with apply tracking question.md. Prototype code never merges. A "what
  should it look like" question belongs to impeccable. Written against
  mattpocock-skills 1.3.1.

artifacts:
  - id: question
    generates: question.md
    description: One question, the decision it informs, a timebox, and the experiments
    template: question.md
    instruction: |
      Frame one question and the decision it informs.

      Route first. A "what should it look like" question goes to
      impeccable's generate or live variants; say so and stop. A question
      that turns out to be an already-settled decision is a feature-flow or
      rapid-flow change.

      Where the question is fuzzy, call the Skill tool twice, for
      "grilling" and "domain-modeling", to sharpen it. Then fill Domain
      terms settled from the git diff of GLOSSARY.md and docs/adr/; delete
      that section when the skills did not run.

      Record:
      - the question, and the decision it informs;
      - a hard timebox. At expiry, findings get written with whatever
        evidence exists;
      - the answer criteria: what evidence would count as an answer;
      - the experiments, as checkboxes, each tagged prototype, research, or
        measurement.
      Keep the template's last box, "Write findings.md". Archive warns while
      it is open, which is what stops a spike ending with no findings.
      Checkboxes take the exact "- [ ] " form.
    requires: []

  - id: findings
    generates: findings.md
    description: Answer, evidence, recommendation, and disposition
    template: findings.md
    instruction: |
      Write this after the experiments end or the timebox expires, and
      before archive. Lead with the answer. Back it with evidence: branch
      links, research files, and measurements. Then recommend.

      The disposition is mandatory:
      - the prototype stays on its prototype/<name> branch as a primary
        source and never merges;
      - name any validated pure module worth lifting into real code;
      - name the follow-up change, usually feature-flow, or record a
        decision not to proceed.
      Tick question.md's last box only once this file exists.
    requires:
      - question

apply:
  requires: [question]
  tracks: question.md
  instruction: |
    Run the experiments and stop at the timebox.

    - A prototype experiment: call the Skill tool with "prototype". A logic
      question gets one self-contained HTML file around a pure module;
      feasibility code goes on a prototype/<name> branch. It never merges.
    - A research experiment: call the Skill tool with "research". It runs
      as a background agent; save its file at
      openspec/changes/<change>/research/<topic>.md.
    - A measurement: record the command and its output.

    Tick each experiment as its evidence lands. At the timebox, stop
    building, write findings.md, and only then tick the last box.
```

`templates/question.md`:

```markdown
## Question

<!-- One primary question, and the decision it informs. -->

## Timebox

<!-- A hard limit. At expiry, write findings.md with whatever evidence exists. -->

## Answer criteria

<!-- What evidence would count as an answer. -->

## Experiments

- [ ] <!-- experiment --> (<!-- prototype | research | measurement -->): evidence to capture: <!-- what -->
- [ ] Write findings.md: answer, evidence, recommendation, disposition

## Domain terms settled

<!-- Only when grilling ran: terms and ADRs written, matching the git diff. Delete
     otherwise. -->
```

`templates/findings.md`:

```markdown
## Answer

<!-- The direct answer to the question. -->

## Evidence

<!-- Measurements, snippets, prototype/<name> branch links, research files.
     Evidence over impressions. -->

## Recommendation

<!-- What to do with this answer. -->

## Disposition

<!-- Mandatory. The prototype stays on its prototype/<name> branch and never
     merges. A validated pure module worth lifting, and where. The follow-up
     change's name, or a decision not to proceed. -->
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS, with `refactor-flow` and `spike-flow` blocks now present.

- [ ] **Step 6: Validate both schemas with OpenSpec**

Run: `validate_flow refactor-flow && validate_flow spike-flow`
Expected: two `✓ Schema '<name>' is valid` lines.

- [ ] **Step 7: Run the repository gates**

Run: `bun test && bun run audit`
Expected: both exit 0.

- [ ] **Step 8: Commit**

```bash
git add plugins/workflows/payload/levels/minimal/openspec/schemas/refactor-flow \
  plugins/workflows/payload/levels/minimal/openspec/schemas/spike-flow
git commit -m "Add refactor-flow and spike-flow to the minimal level

refactor-flow deepens a module behind guard tests at the external seam,
replacing shallow tests rather than layering on them. spike-flow answers
one timeboxed question with prototype and research experiments whose
code stays on its branch.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: upgrade-flow, setup-flow, and rapid-flow

**Files:**
- Create: `.../minimal/openspec/schemas/upgrade-flow/schema.yaml` and `templates/inventory.md`, `templates/surfaces.md`, `templates/tasks.md`
- Create: `.../minimal/openspec/schemas/setup-flow/schema.yaml` and `templates/decisions.md`, `templates/tasks.md`
- Create: `.../minimal/openspec/schemas/rapid-flow/schema.yaml` and `templates/proposal.md`, `templates/tasks.md`

**Interfaces:**
- Consumes: Task 1's `describe.each(flows)` block.
- Produces: `upgrade-flow` ids `inventory`, `surfaces`, `tasks`; `setup-flow` ids `decisions`, `tasks`; `rapid-flow` ids `proposal`, `tasks`. `proposal` is shared with `feature-flow`, so Task 5's one config rule must read correctly in both.

**Required skills:** `configuring-openspec`, `improving-prompts`.

- [ ] **Step 1: Write `upgrade-flow/schema.yaml`**

```yaml
name: upgrade-flow
version: 1
description: >
  A dependency, framework, or platform version change, where success
  means behaviour does not change. inventory -> surfaces -> tasks ->
  apply. No specs artifact. Written against mattpocock-skills 1.3.1.

artifacts:
  - id: inventory
    generates: inventory.md
    description: The version jump and its breaking changes, from cited primary sources
    template: inventory.md
    instruction: |
      Record what changes between the versions, from sources, never from
      memory.

      Call the Skill tool with "research". Point it at primary sources only:
      official release notes, changelogs, migration guides, and source code
      for every version between current and target. Save its file at
      openspec/changes/<change>/research/<package>-<from>-<to>.md. It runs
      as a background agent; wait for the file before writing any verdict.
      Facts are the agent's job, never the user's.

      Record the current and target versions, the motivation (end of life,
      a CVE, a needed feature), any stepping-stone versions across several
      majors, and one row per breaking change with an applies-to-us verdict
      and a link into the research file.

      A breaking change that forces a behaviour change users would see is a
      feature-flow change of its own: note it and split it out.
    requires: []

  - id: surfaces
    generates: surfaces.md
    description: Search-verified call sites per breaking change, each classified
    template: surfaces.md
    instruction: |
      Find where each applicable break lands, by search, with paths and
      counts. Memory of a codebase is not evidence.

      Classify each surface:
      - mechanical: a codemod or a find-and-replace handles it;
      - behavioural: it needs an equivalence check at a named seam. Prefer
        a differential loop: run the same input through the old and the new
        version and diff the output. Name the command;
      - unknown: answer it with a spike-flow change before this one goes on.

      List any step only a human can take, such as rotating a credential,
      a provider dashboard, or a CI secret. Apply turns those into a wizard
      script.
    requires:
      - inventory

  - id: tasks
    generates: tasks.md
    description: Bump, codemods, surface batches, and shim removal, each green
    template: tasks.md
    instruction: |
      Sequence the upgrade so every group lands green:
      1. Bump, or run both versions side by side when the jump is large.
      2. Run the codemods.
      3. Fix the mechanical surfaces in batches sized by blast radius.
      4. Fix each behavioural surface with its equivalence check written
         and run first.
      5. Delete the compatibility shims once nothing needs them.
      6. The Ship group.

      Fill the template's Rollback section: the revert procedure, usually
      the lockfile, and any point of no return, such as a migrated data
      format. Write the session shape on the Session line. Single-session
      work continues in this window. Multi-session work publishes one issue
      per group to the tracker in docs/agents/issue-tracker.md, labelled
      ready-for-agent, with blocking edges. Get the groups approved through
      AskUserQuestion. Checkboxes take the exact "- [ ] " form.
    requires:
      - surfaces

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Upgrade in tasks.md order, with behaviour held still.

    For each group:
    1. Note the start commit. For a behavioural surface, call the Skill
       tool with "tdd" and write its equivalence check first.
    2. Make the change. Run the affected tests and checks as you go.
    3. Run the full suite, then commit, with the lockfile in the same
       commit as the code it resolves.
    4. Call the Skill tool with "code-review". The fixed point is the start
       commit; the spec source is inventory.md and surfaces.md. Fix the
       findings in one follow-up commit.
    5. Tick the group.

    Where a step needs a human, call the Skill tool with "wizard" to
    generate the script, and hand it over; never run it yourself.

    An unexplained behavioural diff stops the upgrade: fix forward or roll
    back per tasks.md. A deliberate behaviour change is a feature-flow
    change, never part of an upgrade. When the work goes up as a pull
    request, call the Skill tool with "pr": its evidence is the equivalence
    checks' before and after output, and a migrated data format makes it a
    one-way door. Finish by offering the human /retro.
```

- [ ] **Step 2: Write the upgrade-flow templates**

`templates/inventory.md`:

```markdown
## Current -> Target

<!-- The package, exact versions, and any stepping-stone versions. -->

## Motivation

<!-- End of life, a CVE, or a needed feature. -->

## Research

<!-- Link the research file under openspec/changes/<change>/research/. -->

## Breaking changes

| Change | Source | Applies to us? |
|---|---|---|
|  |  | yes / no / unknown |
```

`templates/surfaces.md`:

```markdown
## Usage scan

<!-- Per applicable breaking change: search-verified call sites, with paths and
     counts. -->

## Classification

| Surface | Class | Equivalence check (behavioural only) |
|---|---|---|
|  | mechanical / behavioural / unknown |  |

<!-- An unknown surface gets a spike-flow change before this one goes on. -->

## Human-only steps

<!-- Steps only a person can take; apply turns them into a wizard script. Delete if
     none. -->
```

`templates/tasks.md`:

```markdown
**Session:** <!-- single-session | multi-session -->

## 1. Bump to <!-- version --> (<!-- tracker reference, or local -->)

- [ ] 1.1 Dependencies resolve and the project builds
- [ ] 1.2 Codemods run

## 2. <!-- surface batch --> (<!-- tracker reference, or local -->)
<!-- Blocked by: 1 -->

- [ ] 2.1 <!-- mechanical surfaces fixed, or a behavioural surface with its equivalence check passing -->

## Rollback

<!-- The revert procedure, usually the lockfile, and any point of no return. -->

## Ship

- [ ] Compatibility shims deleted
- [ ] Full suite and equivalence checks green, with no unexplained behavioural diff
- [ ] code-review findings resolved in one follow-up commit
- [ ] Shipped: a PR whose body came from the pr skill, or a direct merge (say which)
- [ ] /retro offered to the human
```

- [ ] **Step 3: Write `setup-flow/schema.yaml`**

```yaml
name: setup-flow
version: 1
description: >
  Bootstrapping a new project: stack decisions, the first glossary terms,
  standards, guardrails, and a walking skeleton green in CI.
  decisions -> tasks -> apply. No specs artifact, because no behaviour
  exists yet. Written against mattpocock-skills 1.3.1.

artifacts:
  - id: decisions
    generates: decisions.md
    description: Stack choices with ADRs, the glossary seed, standards, guardrails, and human-only steps
    template: decisions.md
    instruction: |
      Decide the foundations with the user, and write each where it lives.

      Call the Skill tool twice, for "grilling" and "domain-modeling". Ask
      in grilling's rounds, each question carrying a recommended default.
      Cover the language, framework, datastore, test framework, package
      manager, and deploy target. At bootstrap nearly every stack choice
      passes the ADR test (hard to reverse, surprising without context, and
      a real trade-off), so write each to docs/adr/ in the round that
      settles it.

      Record:
      - Stack: each choice, linked to its ADR.
      - Glossary seed: the first domain terms, written to GLOSSARY.md.
      - Standards: judgement calls only, for CODING_STANDARDS.md, which
        code-review's Standards axis reads.
      - Guardrails: the lint, typecheck, and test commands, wired into a
        pre-commit hook or CI. A mechanical rule becomes a check, not a
        standard.
      - Human-only steps: provisioning, credentials, CI secrets, and
        dashboards. Each becomes a wizard stage.
      - Deferred decisions, and what will trigger each.

      Done when the user confirms, and Domain terms settled matches the git
      diff of GLOSSARY.md and docs/adr/.
    requires: []

  - id: tasks
    generates: tasks.md
    description: Bootstrap checklist through a walking skeleton green in CI
    template: tasks.md
    instruction: |
      List the bootstrap as checkboxes, in the template's order. The first
      task asks the human to run /setup-matt-pocock-skills; no task
      publishes to a tracker before it has run. The exit criterion is a
      walking skeleton: the thinnest end-to-end slice, with one real test,
      building and passing in CI. Keep the impeccable hand-off item only
      when the project has a user interface. Checkboxes take the exact
      "- [ ] " form.
    requires:
      - decisions

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Bootstrap per decisions.md, in tasks.md order.

    - Ask the human to run /setup-matt-pocock-skills first. It writes the
      tracker, label, and domain-doc configuration the other flows read,
      and only a human can run it.
    - Scaffold the project and its manifest.
    - Call the Skill tool with "tdd" for the walking skeleton's one real
      test, at a seam you agree with the user.
    - Wire the guardrails from decisions.md into pre-commit or CI, and
      prove each one fails on a deliberate violation before it passes.
    - Call the Skill tool with "wizard" for the human-only steps. Hand the
      script over and never run it.
    - Write CODING_STANDARDS.md from the Standards section.
    - Add navigation pointers to CLAUDE.md, and only pointers: to
      GLOSSARY.md, docs/adr/, CODING_STANDARDS.md, and openspec/ROUTING.md.
    - On a project with a user interface, ask the human to run
      /impeccable init and then /impeccable document. Impeccable owns the
      files they write.

    Commit as each task lands. Prove the skeleton green in CI before
    ticking its box. Then call the Skill tool with "code-review" over the
    whole bootstrap, from the first commit, with decisions.md as the spec
    source. Offer the human /retro.
```

- [ ] **Step 4: Write the setup-flow templates**

`templates/decisions.md`:

```markdown
## Stack

<!-- Language, framework, datastore, test framework, package manager, and deploy
     target. Each choice links its ADR under docs/adr/. -->

## Glossary seed

<!-- The first domain terms, as written to GLOSSARY.md. -->

## Standards

<!-- Judgement calls only, for CODING_STANDARDS.md. -->

## Guardrails

<!-- The lint, typecheck, and test commands, and where each is wired: pre-commit
     or CI. -->

## Human-only steps

<!-- Provisioning, credentials, CI secrets, dashboards. Each becomes a wizard
     stage. -->

## Deferred decisions

<!-- Choices postponed, and what will trigger each. -->

## Domain terms settled

<!-- Terms and ADRs written, matching the git diff. -->
```

`templates/tasks.md`:

```markdown
## Tasks

- [ ] The human runs /setup-matt-pocock-skills: docs/agents/issue-tracker.md exists
- [ ] Scaffold and manifest: dependencies install clean
- [ ] Walking skeleton with one real test: the test passes locally
- [ ] Guardrails wired: a deliberate violation fails each check
- [ ] CI pipeline: the build and the real test pass in CI
- [ ] Human-only steps scripted with wizard: the script is handed over
- [ ] CODING_STANDARDS.md and the CLAUDE.md pointers written: each pointer resolves
- [ ] Surface hand-off: the human runs /impeccable init and /impeccable document <!-- UI projects only; delete otherwise -->

## Ship

- [ ] code-review findings resolved in one follow-up commit
- [ ] /retro offered to the human
```

- [ ] **Step 5: Write `rapid-flow/schema.yaml` and its templates**

```yaml
name: rapid-flow
version: 1
description: >
  A small code change, one decision wide, touching no contract, done in
  one context window. proposal -> tasks -> apply. No specs artifact.
  Typos, docs, and lint fixes need no change at all. Written against
  mattpocock-skills 1.3.1.

artifacts:
  - id: proposal
    generates: proposal.md
    description: What and why, plus the contract check
    template: proposal.md
    instruction: |
      Write one or two paragraphs on what changes and why. Then fill the
      Contract check line. Recreate the change under feature-flow when
      either holds:
      - a decision here has real alternatives worth weighing;
      - the change touches a contract: specified behaviour in
        openspec/specs/, a public API, a data schema, or a config key.
    requires: []

  - id: tasks
    generates: tasks.md
    description: The steps, each with its acceptance criterion, and the Ship group
    template: tasks.md
    instruction: |
      List the steps as checkboxes, each with an acceptance criterion, and
      a test where the behaviour is testable. A copy or configuration change
      may have none; say so. Checkboxes take the exact "- [ ] " form. Keep
      the template's Ship group.
    requires:
      - proposal

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Do it in this window. Note the start commit. Where behaviour is
    testable, call the Skill tool with "tdd" and write the test first. Run
    the full suite, then commit. Call the Skill tool with "code-review",
    with the start commit as the fixed point and proposal.md as the spec
    source, and fix the findings in one follow-up commit. When the change
    goes up as a pull request, call the Skill tool with "pr". If the change
    grew a contract or a real decision on the way, stop and recreate it
    under feature-flow. Offer the human /retro only if the change went
    sideways.
```

`templates/proposal.md`:

```markdown
## What & Why

<!-- One or two paragraphs: the change and the reason. -->

**Contract check:** <!-- "No contract touched", or stop and recreate under feature-flow. -->
```

`templates/tasks.md`:

```markdown
## Tasks

- [ ] <!-- step -->: <!-- acceptance criterion -->

## Ship

- [ ] code-review findings resolved in one follow-up commit
- [ ] Shipped: a PR whose body came from the pr skill, or a direct merge (say which)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS, with `upgrade-flow`, `setup-flow`, and `rapid-flow` blocks present.

- [ ] **Step 7: Validate the three schemas with OpenSpec**

Run: `validate_flow upgrade-flow && validate_flow setup-flow && validate_flow rapid-flow`
Expected: three `✓ Schema '<name>' is valid` lines.

- [ ] **Step 8: Run the repository gates**

Run: `bun test && bun run audit`
Expected: both exit 0.

- [ ] **Step 9: Commit**

```bash
git add plugins/workflows/payload/levels/minimal/openspec/schemas/upgrade-flow \
  plugins/workflows/payload/levels/minimal/openspec/schemas/setup-flow \
  plugins/workflows/payload/levels/minimal/openspec/schemas/rapid-flow
git commit -m "Add upgrade-flow, setup-flow, and rapid-flow to the minimal level

upgrade-flow inventories breaking changes through research over primary
sources and proves behavioural surfaces equivalent before shipping.
setup-flow bootstraps to a walking skeleton with guardrails and wizard
stages. rapid-flow is the single-session path for one-decision changes.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Router, level docs, config, retirement list; delete the old payload

**Files:**
- Create: `plugins/workflows/payload/levels/minimal/openspec/ROUTING.md`
- Create: `plugins/workflows/payload/levels/minimal/openspec/README.md`
- Create: `plugins/workflows/payload/levels/minimal/retired.json`
- Modify: `plugins/workflows/payload/levels/minimal/openspec/config.yaml.example` (full rewrite)
- Delete: `.../minimal/openspec/schemas/mattpocock-bridge/`, `.../minimal/agents/bridge-design-gate.md`, `.../minimal/agents/code-review-spec.md`, `.../minimal/agents/code-review-standards.md`, `.../minimal/openspec/CLAUDE.md.fragment.md`
- Modify: `tests/workflows-minimal-flows.test.ts` (append the level block)

**Interfaces:**
- Consumes: Task 1's helpers; the seven schemas from Tasks 1–4.
- Produces: `retired.json` with exactly `{ "schemas": ["mattpocock-bridge"], "agents": ["bridge-design-gate.md", "code-review-spec.md", "code-review-standards.md"] }`, read by `planRetirement` in Task 7. `openspec/ROUTING.md` at the payload path `payload/levels/minimal/openspec/ROUTING.md`, which Task 9's setup step copies to `$REPO/openspec/ROUTING.md`. Config default `schema: feature-flow`.

**Required skills:** `configuring-openspec`, `improving-prompts` (the router and the config `context:` are prompts), `authoring-plugins` (payload layout).

- [ ] **Step 1: Append the level tests**

Add at the end of `tests/workflows-minimal-flows.test.ts`:

```ts
describe('minimal level as shipped', () => {
	const EXPECTED = ['bugfix-flow', 'feature-flow', 'rapid-flow', 'refactor-flow', 'setup-flow', 'spike-flow', 'upgrade-flow'];

	test('ships exactly the seven flows', () => {
		expect(subdirs(SCHEMAS)).toEqual(EXPECTED);
	});

	test('ships exactly the flow-design agent', () => {
		expect(readdirSync(AGENTS).sort()).toEqual(['flow-design.md']);
	});

	test('the config default exists, defines proposal, and carries the one proposal rule', () => {
		const cfg = Bun.YAML.parse(readFileSync(join(MINIMAL, 'openspec', 'config.yaml.example'), 'utf8')) as {
			schema: string;
			rules: Record<string, string[]>;
		};
		expect(cfg.schema).toBe('feature-flow');
		expect(readSchema(cfg.schema).artifacts.map((a) => a.id)).toContain('proposal');
		expect(Object.keys(cfg.rules)).toEqual(['proposal']);
	});

	test('retired.json lists what the level no longer ships', () => {
		const retired = JSON.parse(readFileSync(join(MINIMAL, 'retired.json'), 'utf8'));
		expect(retired).toEqual({
			schemas: ['mattpocock-bridge'],
			agents: ['bridge-design-gate.md', 'code-review-spec.md', 'code-review-standards.md'],
		});
		expect(retired.schemas.filter((s: string) => subdirs(SCHEMAS).includes(s))).toEqual([]);
	});

	test('no file outside retired.json names a retired term', () => {
		const hits: string[] = [];
		for (const p of filesUnder(MINIMAL)) {
			if (p.endsWith('retired.json')) continue;
			const text = readFileSync(p, 'utf8');
			for (const t of RETIRED_TERMS) if (text.includes(t)) hits.push(`${relative(MINIMAL, p)}: ${t}`);
		}
		expect(hits).toEqual([]);
	});

	test('the router offers only allowed commands and names every shipped flow and no other', () => {
		const text = readFileSync(join(MINIMAL, 'openspec', 'ROUTING.md'), 'utf8');
		expect(slashCommands(text).filter((c) => !isAllowedCommand(c))).toEqual([]);
		const named = [...text.matchAll(/`([a-z]+-flow)`/g)].map((m) => m[1]);
		expect([...new Set(named)].sort()).toEqual(EXPECTED);
	});
});
```

- [ ] **Step 2: Run the tests to verify the level block fails**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: FAIL in `minimal level as shipped`: the seven-flows test sees `mattpocock-bridge`, the agent test sees four files, the config test sees `mattpocock-bridge`, `retired.json` and `ROUTING.md` are missing (`ENOENT`), and the retired-term scan hits `CLAUDE.md.fragment.md`, `config.yaml.example`, and the old schema.

- [ ] **Step 3: Delete the old payload**

```bash
git rm -r plugins/workflows/payload/levels/minimal/openspec/schemas/mattpocock-bridge
git rm plugins/workflows/payload/levels/minimal/agents/bridge-design-gate.md \
  plugins/workflows/payload/levels/minimal/agents/code-review-spec.md \
  plugins/workflows/payload/levels/minimal/agents/code-review-standards.md \
  plugins/workflows/payload/levels/minimal/openspec/CLAUDE.md.fragment.md
```

- [ ] **Step 4: Write `retired.json`**

`plugins/workflows/payload/levels/minimal/retired.json`:

```json
{
	"schemas": ["mattpocock-bridge"],
	"agents": ["bridge-design-gate.md", "code-review-spec.md", "code-review-standards.md"]
}
```

- [ ] **Step 5: Rewrite `config.yaml.example`**

```yaml
# Copy to openspec/config.yaml, or let /workflows:setup write it.
#
# `context:` is injected into every artifact prompt and `rules:` only into the
# matching artifact. Every gate lives in the schema instructions, so nothing
# here is load-bearing and a schema upgrade never strands a rule.

schema: feature-flow

context: |
  Before creating a change, read openspec/ROUTING.md and name the schema it
  picks: /opsx:new <the work>, using <schema>.

  Before exploring, read GLOSSARY.md (or GLOSSARY-MAP.md, then the relevant
  GLOSSARY.md) and the ADRs under docs/adr/ that touch the area in play.
  Proceed silently where they are absent. Use the glossary's terms, never the
  synonyms it lists under Avoid. Where output contradicts an ADR, say so and
  make the case for reopening it.

  Each fact has one home: behaviour in openspec/specs/, vocabulary in
  GLOSSARY.md, binding decisions in docs/adr/, and judgement-call standards in
  CODING_STANDARDS.md. PRODUCT.md, DESIGN.md, and .impeccable/ belong to
  impeccable: read them, never write them. The issue tracker is configured in
  docs/agents/issue-tracker.md. Anything inside openspec/changes/<name>/
  archives with the change as history.

  Interview in grilling's text rounds. Use AskUserQuestion only to approve or
  adjust a proposal: seams, a ticket breakdown, or an ADR. Take commands from
  the repository's own manifests and scripts.

rules:
  proposal:
    - "Name domain concepts with GLOSSARY.md terms."
```

- [ ] **Step 6: Write `openspec/ROUTING.md`**

````markdown
# Workflow router

Read this before creating any OpenSpec change. Classify the work, then create
the change with the schema named in the sentence:

    /opsx:new <the work, in a sentence>, using <schema>

Naming the schema is what makes the choice stick: OpenSpec selects nothing on
its own. The terminal form is `openspec new change <slug> --schema <schema>`.
Then run `/opsx:continue <change>` once per artifact, naming the change each
time.

## Decision tree (first match wins)

1. **Production is broken now.** Mitigate first: roll back or flip the flag.
   Then open `bugfix-flow` and fill its Incident section.
2. **A new project bootstrap** → `setup-flow`.
3. **Behaviour deviates from spec or intent**, including performance
   regressions → `bugfix-flow`. A raw incoming report goes to `/triage` first.
4. **A dependency, framework, or platform version change** → `upgrade-flow`.
5. **Structure changes and external behaviour must not** → `refactor-flow`.
   Coverage backfill is a refactor with no restructure.
6. **An open question answered by building or reading** → `spike-flow`.
7. **A new capability or intentional behaviour change**, including removals →
   `feature-flow`, the config default.
8. **A small code change, one decision wide, touching no contract** →
   `rapid-flow`. Typos, docs, and lint fixes are a direct commit with no
   change.

## Work that never becomes a change

| Work | Where it goes |
|---|---|
| UI/UX: look, feel, layout, copy, accessibility, polish | impeccable. See "The UI boundary" |
| An effort too big and foggy for one change | `/wayfinder`. Its cleared map enters `feature-flow` at the proposal |
| A survey for deepening opportunities | `/improve-codebase-architecture`. Each accepted candidate becomes a `refactor-flow` change |
| Raw bug reports and feature requests | `/triage`. Its `ready-for-agent` briefs become changes |
| A decision only someone else can answer | `/to-questionnaire` |
| Which Pocock skill fits | `/ask-matt` |

Tickets a flow published are agent-ready already; never triage them.

## The UI boundary

The UI is an adapter at a presentation seam. A flow owns everything behind the
seam: domain state, data fetching and mutation, validation, permissions, and
the interface the surface consumes. Impeccable owns the surface: components,
layout, presentation-only state, copy, accessibility, and motion.

- A behavioural state, such as "permission denied returns an error", is a spec
  scenario. How that state looks and reads is impeccable's.
- An error kind is behaviour; the message a user reads is presentation. Specs
  assert the kind, never the wording.
- When an impeccable command finds a behaviour gap (a retry policy, a state the
  module does not emit, validation, persistence, analytics), name the gap and
  open or extend a flow change. Impeccable presents only what the seam already
  emits.
- A change a surface consumes carries a Presentation seam block in design.md and
  one fixture per emitted state. Build the surface against that block.
- UI/UX-led work starts in impeccable. When `/impeccable shape` reveals missing
  functionality, open a `feature-flow` change for it; its grill reads the brief
  and asks only behaviour questions.
- During a flow's apply, surface work waits for the hand-off item; it never
  happens mid-slice.
- Impeccable's design hook also scans `.ts` and `.js` edits. Exclude engineering
  directories with `/impeccable hooks ignore-file <glob>`.

## Guardrails

- `rapid-flow` → `feature-flow` when a contract appears or a decision grows real
  alternatives.
- `refactor-flow` → `feature-flow` when a guard assertion has to change.
- `bugfix-flow` → `feature-flow` when the fix changes promised behaviour rather
  than restoring it.
- `upgrade-flow` → `feature-flow` for any deliberate behaviour change.
- De-escalate as readily: a feature grill that shrinks to one decision becomes
  `rapid-flow`, and one that turns into a question becomes `spike-flow`.
- When two schemas fit, ask one question naming both, then route.

## Sessions

- Run the planning artifacts in one unbroken window. Changing model or effort at
  an artifact boundary is free.
- At a phase boundary, prefer in order: continue, `/clear`, `/handoff`, a
  subagent, `/compact`.
- The tasks artifact records the session shape. Single-session work continues in
  the same window. Multi-session work runs each slice in a fresh session:
  `/clear`, then `/model` or `/effort`, then `/opsx:apply <change>`, naming the
  change because clearing removed it.
- `/handoff` writes to the OS temp directory. Name the change in it, and start
  the next session with `openspec status --change <name> --json`.
- `/retro` is offered after a build, never run automatically.
````

- [ ] **Step 7: Write `openspec/README.md`**

```markdown
# The minimal level: seven flows driven by Matt Pocock's skills

OpenSpec schemas whose every artifact is driven by a skill from
mattpocock-skills 1.3.1. OpenSpec owns which documents a change has and how
behaviour merges into `openspec/specs/`. The skills own how a change is decided,
named, tested, built, and reviewed. Impeccable owns UI/UX.

| Schema | Use when | Chain |
|---|---|---|
| `feature-flow` | A new capability or intentional behaviour change (the default) | grill → proposal → specs → design → tasks |
| `bugfix-flow` | Behaviour deviates from spec or intent; incidents after mitigation | diagnose → specs → tasks |
| `refactor-flow` | Structure changes and external behaviour must not | grill → design → tasks |
| `spike-flow` | A timeboxed question answered by building or reading | question → findings |
| `upgrade-flow` | A dependency, framework, or platform version change | inventory → surfaces → tasks |
| `setup-flow` | Bootstrapping a new project | decisions → tasks |
| `rapid-flow` | A small code change, one decision wide, touching no contract | proposal → tasks |

`ROUTING.md` picks between them. `/workflows:setup` installs the schemas, the
`flow-design` agent, the router, and the config.

## Prerequisites

1. The mattpocock-skills plugin. `/workflows:setup` enables it.
2. `/setup-matt-pocock-skills`, run once by a human, so `docs/agents/` exists.
3. On a project with a user interface: impeccable, set up with `/impeccable init`.

## What the flows call

Model-invoked skills, called through the Skill tool: grilling, domain-modeling,
codebase-design, prototype, research, diagnosing-bugs, tdd, code-review, pr, and
wizard. User-invoked skills, offered to the human because no skill can call
them: `/triage`, `/wayfinder`, `/improve-codebase-architecture`, `/to-tickets`,
`/implement-spec`, `/grill-with-docs`, `/setup-matt-pocock-skills`, and `/retro`.

The `flow-design` agent drafts the design artifact for `feature-flow` and
`refactor-flow` on the top model, so the planning session can stay cheaper.

## Escape hatches

- `skip_specs: true` in a `bugfix-flow` change whose spec already covered the
  case. OpenSpec sets it by itself for a schema with no `specs` artifact.
- `retire_capabilities: true` when a change removes a capability's last
  requirement.
- Skipping an interview writes a one-line stub file holding the reason and the
  date. The CLI reads no other skip flag.

## Upgrading from the previous minimal level

The previous level shipped a single feature schema and three review agents, now
listed in `../retired.json`. Setup offers to delete each one only when this
plugin installed it, nobody has edited it, and no open change still uses it.
`bugfix-flow` keeps its name and its `diagnose` artifact, so in-flight bugfix
changes keep resolving.
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `bun test tests/workflows-minimal-flows.test.ts`
Expected: PASS, every block.

- [ ] **Step 9: Run the repository gates**

Run: `bun test && bun run audit`
Expected: both exit 0. `tests/workflows-plan.test.ts` still passes: it never names a minimal schema or agent.

- [ ] **Step 10: Commit**

```bash
git add -A plugins/workflows/payload/levels/minimal tests/workflows-minimal-flows.test.ts
git commit -m "Ship the minimal level's router, config, and retirement list

ROUTING.md routes work to the seven flows and draws the UI boundary with
impeccable. The config defaults to feature-flow and carries nothing
load-bearing. mattpocock-bridge, the three old agents, and the CLAUDE.md
fragment are removed and listed in retired.json for setup to offer.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Detection reads each open change's schema

**Files:**
- Modify: `plugins/workflows/scripts/detect.mjs` (new function after `hashesFor`, near line 198; one new field in the returned `openspec` object, near line 242)
- Modify: `plugins/workflows/scripts/detect.d.mts` (`OpenspecDetection`)
- Modify: `tests/workflows-detect.test.ts` (append a block)

**Interfaces:**
- Consumes: `dirNames(dir)` (already in `detect.mjs`).
- Produces: `detection.openspec.changeSchemas: Record<string, string | null>` — one key per directory under `openspec/changes/` except `archive`; the value is the bare schema name from `.openspec.yaml`, or `null` when the file or its `schema:` line is missing. Task 7 relies on this exact name and shape.

**Required skills:** none (plain code).

- [ ] **Step 1: Write the failing tests**

Append to `tests/workflows-detect.test.ts`:

```ts
describe('open change schemas', () => {
	const changeSchemas = (root: string) => detect(root, { run: stubRun }).openspec.changeSchemas;
	const change = (root: string, name: string, body?: string) => {
		mkdirSync(join(root, 'openspec', 'changes', name), { recursive: true });
		if (body !== undefined) writeFileSync(join(root, 'openspec', 'changes', name, '.openspec.yaml'), body);
	};

	test('no changes directory means no entries', () => {
		expect(changeSchemas(repo())).toEqual({});
	});

	test("reads each open change's schema, quoted or not", () => {
		const root = repo((r) => {
			change(r, 'add-a', 'schema: feature-flow\ncreated: 2026-10-06\n');
			change(r, 'fix-b', "schema: 'bugfix-flow' # chosen by the router\n");
			change(r, 'old-c', 'created: 2026-09-01\nschema: "mattpocock-bridge"\n');
		});
		expect(changeSchemas(root)).toEqual({ 'add-a': 'feature-flow', 'fix-b': 'bugfix-flow', 'old-c': 'mattpocock-bridge' });
	});

	test('a change with no .openspec.yaml, or no schema line, names null', () => {
		const root = repo((r) => {
			change(r, 'bare');
			change(r, 'no-line', 'created: 2026-10-06\n');
		});
		expect(changeSchemas(root)).toEqual({ bare: null, 'no-line': null });
	});

	test('archived changes are not open', () => {
		const root = repo((r) => {
			change(r, join('archive', '2026-01-01-old'), 'schema: mattpocock-bridge\n');
			change(r, 'add-a', 'schema: feature-flow\n');
		});
		expect(changeSchemas(root)).toEqual({ 'add-a': 'feature-flow' });
	});
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `bun test tests/workflows-detect.test.ts`
Expected: FAIL — `changeSchemas` is `undefined` in all four new tests.

- [ ] **Step 3: Add the function to `detect.mjs`**

Insert after the `hashesFor` function:

```js
/**
 * `{ changeName: schemaName | null }` for every open change: each directory under
 * openspec/changes except `archive`. Read straight off `.openspec.yaml` rather than through
 * the CLI, for the same reason the machine config is: every subcommand writes and transmits.
 * Retirement (plan.mjs) needs one answer from this — does an open change still resolve
 * against a schema setup is about to offer for deletion — and `null` (no file, or no
 * `schema:` line) is "cannot tell", which plan.mjs treats as "it might".
 */
function openChangeSchemas(openspecDir) {
	const out = {};
	for (const name of dirNames(join(openspecDir, 'changes'))) {
		if (name === 'archive') continue;
		let schema = null;
		try {
			const match = readFileSync(join(openspecDir, 'changes', name, '.openspec.yaml'), 'utf8').match(
				/^schema:\s*['"]?([^'"\s#]+)/m,
			);
			if (match) schema = match[1];
		} catch {
			// No .openspec.yaml: the change names no schema of its own.
		}
		out[name] = schema;
	}
	return out;
}
```

- [ ] **Step 4: Report it from `detect()`**

In `detect()`'s returned `openspec` object, replace:

```js
			configPath: existsSync(configYaml) ? configYaml : existsSync(configYml) ? configYml : null,
		},
```

with:

```js
			configPath: existsSync(configYaml) ? configYaml : existsSync(configYml) ? configYml : null,
			changeSchemas: openChangeSchemas(openspecDir),
		},
```

- [ ] **Step 5: Declare it in `detect.d.mts`**

In `interface OpenspecDetection`, after `configPath: string | null;`, add:

```ts
	/**
	 * `{ changeName: schemaName | null }` for each open change (every directory under
	 * openspec/changes except `archive`), read from its `.openspec.yaml`. `null` means the
	 * change names no schema, so plan.mjs keeps every retired schema it might be using.
	 */
	changeSchemas: Record<string, string | null>;
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-detect.test.ts tests/workflows-plan.test.ts`
Expected: PASS, both files.

- [ ] **Step 7: Run the repository gates, then commit**

Run: `bun test && bun run audit`
Expected: both exit 0.

```bash
git add plugins/workflows/scripts/detect.mjs plugins/workflows/scripts/detect.d.mts tests/workflows-detect.test.ts
git commit -m "Detect which schema each open OpenSpec change uses

Retirement must never delete a schema an in-flight change resolves
against. detect.mjs now reads each open change's .openspec.yaml schema
line, skips the archive, and reports null when it cannot tell.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: The plan offers retired names for deletion

**Files:**
- Modify: `plugins/workflows/scripts/plan.mjs` (new `planRetirement` after `classify`; one new field in the returned plan)
- Modify: `plugins/workflows/scripts/plan.d.mts` (`PlanDetectionOpenspec`, three new interfaces, `Plan`)
- Modify: `tests/workflows-plan.test.ts` (import `recordRun`; append a block)

**Interfaces:**
- Consumes: Task 5's `payload/levels/minimal/retired.json`; Task 6's `detection.openspec.changeSchemas`; existing `detection.openspec.schemas`, `schemaHashes`, `detection.agents.files`, `hashes`, `detection.prior.schemas`, `agents`.
- Produces: `plan.retire = { schemas: { retire: string[], keep: { name: string, reason: string }[] }, agents: { … same … } }`. The four reason strings, verbatim, which Task 9's prose and Task 8 rely on:
  - `'not installed by this plugin'`
  - `'edited since this plugin installed it'`
  - `'an open change uses it'`, `'an open change names no schema, so it may use this one'`, `'open changes were not checked, so one may use it'` (schemas)
  - `'a retired schema it serves is being kept'` (agents)

**Required skills:** none (plain code).

- [ ] **Step 1: Write the failing tests**

In `tests/workflows-plan.test.ts`, add this import below the existing `detect` import:

```ts
// @ts-expect-error untyped .mjs module
import { recordRun } from '../plugins/workflows/scripts/record.mjs';
```

Append this block:

```ts
describe('retirement', () => {
	const RETIRED_AGENTS = ['bridge-design-gate.md', 'code-review-spec.md', 'code-review-standards.md'];
	const ourAgents = Object.fromEntries(RETIRED_AGENTS.map((a) => [a, 'a1']));
	const onDisk = (o: { schemaHash?: string; recorded?: boolean; changes?: Record<string, string | null> | null } = {}) =>
		makeDetection({
			openspec: {
				present: true,
				hasSpecs: false,
				hasChanges: false,
				schemas: ['mattpocock-bridge'],
				schemaHashes: { 'mattpocock-bridge': o.schemaHash ?? 'h1' },
				configPath: null,
				...(o.changes === null ? {} : { changeSchemas: o.changes ?? {} }),
			},
			agents: { files: RETIRED_AGENTS, hashes: ourAgents },
			priorRun: true,
			prior: o.recorded === false ? { schemas: {}, agents: {} } : { schemas: { 'mattpocock-bridge': 'h1' }, agents: ourAgents },
		});
	const keptFor = (reason: string) => RETIRED_AGENTS.map((name) => ({ name, reason }));

	test('recorded, untouched, and unused: the schema and its agents retire', () => {
		const plan = buildPlan(onDisk(), { level: 'minimal' });
		expect(plan.retire.schemas).toEqual({ retire: ['mattpocock-bridge'], keep: [] });
		expect(plan.retire.agents).toEqual({ retire: RETIRED_AGENTS, keep: [] });
	});

	test('edited since install: kept, and its agents with it', () => {
		const plan = buildPlan(onDisk({ schemaHash: 'h2' }), { level: 'minimal' });
		expect(plan.retire.schemas).toEqual({
			retire: [],
			keep: [{ name: 'mattpocock-bridge', reason: 'edited since this plugin installed it' }],
		});
		expect(plan.retire.agents).toEqual({ retire: [], keep: keptFor('a retired schema it serves is being kept') });
	});

	test("never recorded: kept as the user's own", () => {
		const plan = buildPlan(onDisk({ recorded: false }), { level: 'minimal' });
		expect(plan.retire.schemas.keep).toEqual([{ name: 'mattpocock-bridge', reason: 'not installed by this plugin' }]);
		expect(plan.retire.agents.keep).toEqual(keptFor('not installed by this plugin'));
	});

	test('an open change uses it: kept', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': 'mattpocock-bridge' } }), { level: 'minimal' });
		expect(plan.retire.schemas.keep).toEqual([{ name: 'mattpocock-bridge', reason: 'an open change uses it' }]);
	});

	test('an open change naming no schema keeps it', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': null } }), { level: 'minimal' });
		expect(plan.retire.schemas.keep).toEqual([
			{ name: 'mattpocock-bridge', reason: 'an open change names no schema, so it may use this one' },
		]);
	});

	test('a detection without changeSchemas keeps retired schemas', () => {
		const plan = buildPlan(onDisk({ changes: null }), { level: 'minimal' });
		expect(plan.retire.schemas.keep).toEqual([
			{ name: 'mattpocock-bridge', reason: 'open changes were not checked, so one may use it' },
		]);
	});

	test('an open change on another schema does not block', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': 'feature-flow' } }), { level: 'minimal' });
		expect(plan.retire.schemas.retire).toEqual(['mattpocock-bridge']);
	});

	test('a retired name not on disk is not mentioned', () => {
		const plan = buildPlan(makeDetection(), { level: 'minimal' });
		expect(plan.retire).toEqual({ schemas: { retire: [], keep: [] }, agents: { retire: [], keep: [] } });
	});

	test('a level with no retired.json retires nothing', () => {
		const plan = buildPlan(onDisk(), { level: 'standard' });
		expect(plan.retire).toEqual({ schemas: { retire: [], keep: [] }, agents: { retire: [], keep: [] } });
	});

	test('integration: a recorded retired schema an open change uses is kept', () => {
		const root = mkd(j(tmp(), 'wf-retire-'));
		mk(j(root, 'openspec', 'schemas', 'mattpocock-bridge'), { recursive: true });
		wf(j(root, 'openspec', 'schemas', 'mattpocock-bridge', 'schema.yaml'), 'name: mattpocock-bridge\n');
		recordRun(root, { level: 'minimal', schemas: ['mattpocock-bridge'], date: '2026-10-06T00:00:00.000Z' });
		mk(j(root, 'openspec', 'changes', 'add-x'), { recursive: true });
		wf(j(root, 'openspec', 'changes', 'add-x', '.openspec.yaml'), 'schema: mattpocock-bridge\n');
		const plan = buildPlan(detect(root, { run: () => null }), { level: 'minimal' });
		expect(plan.retire.schemas).toEqual({ retire: [], keep: [{ name: 'mattpocock-bridge', reason: 'an open change uses it' }] });
	});
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `bun test tests/workflows-plan.test.ts`
Expected: FAIL — `plan.retire` is `undefined` in every new test.

- [ ] **Step 3: Add `planRetirement` to `plan.mjs`**

Insert after the `classify` function:

```js
/**
 * Names this level used to ship and no longer does, from `levels/<level>/retired.json`.
 * Setup deletes nothing on its own, so without this a renamed schema or a dropped agent
 * stays on disk indefinitely — and a dropped agent keeps loading, its description still
 * telling the model to reach for it. A retired name is offered for deletion only when the
 * record says this plugin wrote it, its bytes still match what was written, and nothing
 * still needs it. Everything else is kept with its reason, because a file the user edited,
 * or one an in-flight change resolves against, is theirs to delete.
 *
 * An open change whose schema detection could not read (`null`) might be any of them, and
 * a detection with no `changeSchemas` at all never looked; both keep every retired schema.
 * Retired agents stay while any retired schema stays, because the old schemas dispatch them.
 */
function planRetirement(levelDir, detection) {
	const retired = readJson(join(levelDir, 'retired.json'));
	const changes = detection.openspec?.changeSchemas;

	const sweep = (names, onDisk, hashes, recorded, blocker) => {
		const out = { retire: [], keep: [] };
		for (const name of names ?? []) {
			if (!(onDisk ?? []).includes(name)) continue;
			let reason;
			if (!recorded?.[name]) reason = 'not installed by this plugin';
			else if (!hashes?.[name] || hashes[name] !== recorded[name]) reason = 'edited since this plugin installed it';
			else reason = blocker(name);
			if (reason) out.keep.push({ name, reason });
			else out.retire.push(name);
		}
		return out;
	};

	const schemas = sweep(
		retired.schemas,
		detection.openspec?.schemas,
		detection.openspec?.schemaHashes,
		detection.prior?.schemas,
		(name) => {
			if (!changes) return 'open changes were not checked, so one may use it';
			const open = Object.values(changes);
			if (open.includes(name)) return 'an open change uses it';
			if (open.includes(null)) return 'an open change names no schema, so it may use this one';
			return null;
		},
	);
	const agents = sweep(retired.agents, detection.agents?.files, detection.agents?.hashes, detection.prior?.agents, () =>
		schemas.keep.length > 0 ? 'a retired schema it serves is being kept' : null,
	);
	return { schemas, agents };
}
```

- [ ] **Step 4: Return it from `buildPlan`**

Replace:

```js
		schemas,
		agents,
		config: {
```

with:

```js
		schemas,
		agents,
		retire: planRetirement(levelDir, detection),
		config: {
```

- [ ] **Step 5: Declare it in `plan.d.mts`**

In `interface PlanDetectionOpenspec`, after `configPath: string | null;`, add:

```ts
	/**
	 * `{ changeName: schemaName | null }` for each open change. Optional so an older detection
	 * still type-checks; absent is treated as "not checked", which keeps every retired schema.
	 */
	changeSchemas?: Record<string, string | null>;
```

After `interface PlanEntries`, add:

```ts
export interface PlanRetireKeep {
	name: string;
	reason: string;
}

/** `retire`: safe to offer for deletion at the gate. `keep`: left on disk, each with its reason. */
export interface PlanRetireSide {
	retire: string[];
	keep: PlanRetireKeep[];
}

/** Names this level no longer ships (`levels/<level>/retired.json`), split for the gate. */
export interface PlanRetirement {
	schemas: PlanRetireSide;
	agents: PlanRetireSide;
}
```

In `interface Plan`, after `agents: PlanEntries;`, add `retire: PlanRetirement;`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-plan.test.ts`
Expected: PASS, every test in the file.

- [ ] **Step 7: Run the repository gates, then commit**

Run: `bun test && bun run audit`
Expected: both exit 0.

```bash
git add plugins/workflows/scripts/plan.mjs plugins/workflows/scripts/plan.d.mts tests/workflows-plan.test.ts
git commit -m "Offer names a level no longer ships for guarded deletion

The plan now carries a retire section from the level's retired.json. A
name is offered only when this plugin recorded it, it is unedited, and
no open change uses it; anything else is kept with its reason, and
retired agents stay while any retired schema stays.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: The record drops retired names setup deleted

**Files:**
- Modify: `plugins/workflows/scripts/record.mjs` (`recordRun` signature and `merged`; `ownedFromPlan` return; CLI call)
- Modify: `plugins/workflows/scripts/record.d.mts` (`RecordRunOptions`, `OwnedFromPlan`)
- Create: `tests/workflows-record.test.ts`

**Interfaces:**
- Consumes: Task 7's `plan.retire.{schemas,agents}.retire`.
- Produces: `recordRun(repoRoot, { …, retired?: { schemas?: string[], agents?: string[] } })` deletes a retired name from the record when it is gone from disk, and leaves it when it is still there. `ownedFromPlan(plan).retired: { schemas: string[], agents: string[] }`, empty for a plan with no `retire`.

**Required skills:** none (plain code).

- [ ] **Step 1: Write the failing tests**

```ts
// tests/workflows-record.test.ts
import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { ownedFromPlan, recordRun } from '../plugins/workflows/scripts/record.mjs';

/** A repo whose record already claims `recorded`, with schema directories for `onDisk`. */
function repoWithRecord(recorded: Record<string, string>, onDisk: string[]): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-record-'));
	mkdirSync(join(root, '.claude'), { recursive: true });
	writeFileSync(
		join(root, '.claude', 'workflows.json'),
		JSON.stringify({ level: 'minimal', version: '0.7.0', date: '2026-01-01T00:00:00.000Z', installed: { schemas: recorded, agents: {} } }),
	);
	for (const name of onDisk) {
		mkdirSync(join(root, 'openspec', 'schemas', name), { recursive: true });
		writeFileSync(join(root, 'openspec', 'schemas', name, 'schema.yaml'), `name: ${name}\n`);
	}
	return root;
}

const EMPTY_SIDE = { copy: [], update: [], collide: [] };

describe('retirement in the record', () => {
	test('a retired schema setup deleted leaves the record', () => {
		const root = repoWithRecord({ 'mattpocock-bridge': 'h1' }, ['feature-flow']);
		const { record } = recordRun(root, {
			level: 'minimal',
			schemas: ['feature-flow'],
			retired: { schemas: ['mattpocock-bridge'], agents: [] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(Object.keys(record.installed.schemas)).toEqual(['feature-flow']);
	});

	test('a retired schema the user kept stays recorded as ours', () => {
		const root = repoWithRecord({ 'mattpocock-bridge': 'h1' }, ['mattpocock-bridge']);
		const { record } = recordRun(root, {
			level: 'minimal',
			schemas: [],
			retired: { schemas: ['mattpocock-bridge'], agents: [] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(record.installed.schemas['mattpocock-bridge']).toBe('h1');
	});

	test("ownedFromPlan carries the plan's retire lists", () => {
		const plan = {
			level: 'minimal',
			schemas: EMPTY_SIDE,
			agents: EMPTY_SIDE,
			retire: {
				schemas: { retire: ['mattpocock-bridge'], keep: [] },
				agents: { retire: ['bridge-design-gate.md'], keep: [{ name: 'code-review-spec.md', reason: 'edited since this plugin installed it' }] },
			},
		};
		expect(ownedFromPlan(plan).retired).toEqual({ schemas: ['mattpocock-bridge'], agents: ['bridge-design-gate.md'] });
	});

	test('a plan from before retirement existed retires nothing', () => {
		expect(ownedFromPlan({ level: 'minimal', schemas: EMPTY_SIDE, agents: EMPTY_SIDE }).retired).toEqual({ schemas: [], agents: [] });
	});
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `bun test tests/workflows-record.test.ts`
Expected: FAIL — the first test still records `mattpocock-bridge`, and `ownedFromPlan(...).retired` is `undefined`.

- [ ] **Step 3: Teach `recordRun` to drop deleted retired names**

Replace the signature line:

```js
export function recordRun(repoRoot, { level, schemas = [], agents = [], version = pluginVersion(), date = new Date() } = {}) {
```

with:

```js
export function recordRun(repoRoot, { level, schemas = [], agents = [], retired = {}, version = pluginVersion(), date = new Date() } = {}) {
```

Replace:

```js
	const merged = (previous, names, toPath) => {
		const out = { ...previous };
		for (const name of [...names].sort()) {
```

with:

```js
	const merged = (previous, names, toPath, drop = []) => {
		const out = { ...previous };
		// A retired name setup deleted is gone from disk, so it leaves the record. One the
		// user chose to keep is still there and still ours, so it stays.
		for (const name of drop) if (!hashEntry(toPath(repoRoot, name))) delete out[name];
		for (const name of [...names].sort()) {
```

Replace:

```js
			schemas: merged(prior?.schemas, schemas, schemaPath),
			agents: merged(prior?.agents, agents, agentPath),
```

with:

```js
			schemas: merged(prior?.schemas, schemas, schemaPath, retired.schemas),
			agents: merged(prior?.agents, agents, agentPath, retired.agents),
```

- [ ] **Step 4: Carry the retire lists through `ownedFromPlan` and the CLI**

In `ownedFromPlan`'s returned object, after `agents: [...agents.copy, ...agents.update, ...agentApproved],`, add:

```js
		// Read from the plan, never from the caller: what setup may delete was decided when the
		// plan was built, and a plan from before retirement existed simply retires nothing.
		retired: { schemas: plan.retire?.schemas?.retire ?? [], agents: plan.retire?.agents?.retire ?? [] },
```

In the CLI block, replace:

```js
			schemas: owned.schemas,
			agents: owned.agents,
		});
```

with:

```js
			schemas: owned.schemas,
			agents: owned.agents,
			retired: owned.retired,
		});
```

- [ ] **Step 5: Declare it in `record.d.mts`**

In `interface RecordRunOptions`, after the `agents?: string[];` line, add:

```ts
	/**
	 * Names the plan offered for retirement. Each one that is gone from disk leaves the record;
	 * one the user kept is still on disk and stays recorded.
	 */
	retired?: { schemas?: string[]; agents?: string[] };
```

In `interface OwnedFromPlan`, after `agents: string[];`, add:

```ts
	/** `plan.retire.*.retire`, or empty lists for a plan built before retirement existed. */
	retired: { schemas: string[]; agents: string[] };
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `bun test tests/workflows-record.test.ts tests/workflows-plan.test.ts`
Expected: PASS, both files.

- [ ] **Step 7: Run the repository gates, then commit**

Run: `bun test && bun run audit`
Expected: both exit 0.

```bash
git add plugins/workflows/scripts/record.mjs plugins/workflows/scripts/record.d.mts tests/workflows-record.test.ts
git commit -m "Drop retired names setup deleted from the install record

A retired schema or agent the user approved deleting leaves
.claude/workflows.json; one they kept stays recorded as ours. The retire
lists come from the approved plan, never from the caller.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Setup prose — the minimal level, retirement, and the router

**Files:**
- Modify: `plugins/workflows/skills/setup/SKILL.md` (eight edits below)
- Modify: `plugins/workflows/scripts/config-facts.mjs` (one comment line, near line 126)

**Interfaces:**
- Consumes: Task 7's `plan.retire` shape and reason strings; Task 8's record behaviour; Task 5's payload `ROUTING.md` path.
- Produces: the human-facing procedure for retirement and router installation. No code consumes it.

**Required skills:** `authoring-skills` (SKILL.md edits), `improving-prompts`.

Each edit replaces text you can find verbatim in the current file. If a line wraps differently from what is shown, match on the sentence and keep the file's existing wrap width (about 90 columns).

- [ ] **Step 1: Level heuristics (section 2a)**

Replace:

```markdown
- **Five or more kinds, especially dependency bumps or incidents** → `advanced`. Those two
  are the ones that get mangled when a repository only knows how to do features and bugs.
```

with:

```markdown
- **Five or more kinds, especially dependency bumps or incidents** → `minimal` or
  `advanced`. Both route each kind to its own chain. `advanced` adds written plans, a
  pre-implementation review gate, verification evidence, and a dedicated `hotfix` chain;
  recommend it when the history shows that ceremony already happening (reviewed design
  docs, postmortems), and `minimal` otherwise.
```

- [ ] **Step 2: The minimal row of the level table (section 2b)**

Replace the row beginning `` | `minimal` | `mattpocock-bridge` and `bugfix-flow`. `` with:

```markdown
| `minimal` | One `-flow` chain per kind of work (features, defects, cleanups, spikes, upgrades, bootstraps, small changes), all driven by Matt Pocock's skills, with a router between them. Work usually starts as an unclear idea that an interview turns into a plan; impeccable owns UI/UX |
```

- [ ] **Step 3: "Setup deletes nothing" (end of section 2b)**

Replace `Setup deletes nothing, so a later run at a different level adds that` with `Setup deletes nothing without asking, so a later run at a different level adds that`, and rewrap the paragraph.

- [ ] **Step 4: Name the retire group in the plan (section 3)**

After the `collide` bullet (the one ending `"approve all"` / `is not an answer to this question.`), add:

```markdown
- `retire` — names this level used to ship and no longer does, from its `retired.json`.
  `retire.*.retire` lists the ones safe to delete: recorded as ours, unedited, and used
  by no open change. `retire.*.keep` lists the rest, each with its reason. Name both.
```

- [ ] **Step 5: The retirement step (end of step 3, "Agents")**

Immediately before the line that starts `4. **TOOLS.md.**`, insert:

````markdown
   **Then retired names.** Leave every `plan.retire.*.keep` entry alone and report its
   reason. Ask about each name in `plan.retire.schemas.retire` and
   `plan.retire.agents.retire` individually, and delete only the ones the user approves:

   ```bash
   rm -r "$REPO/openspec/schemas/$NAME"     # an approved retired schema
   rm "$REPO/.claude/agents/$NAME"          # an approved retired agent file
   ```

   When the user keeps a retired schema, keep every retired agent too: the old schemas
   dispatch them. Step 8 drops the deleted names from the record by itself.
````

- [ ] **Step 6: Install the router (step 6)**

Replace:

```markdown
6. **CLAUDE.md.** Invoke `managing-project-memory`. On `advanced`, let it decide where
   `ROUTING.md` belongs; the router only works from somewhere memory reliably loads it.
```

with:

```markdown
6. **Router and CLAUDE.md.** On `minimal`, install the router at `openspec/ROUTING.md`:
   copy `${CLAUDE_PLUGIN_ROOT}/payload/levels/minimal/openspec/ROUTING.md` when the file
   is absent; when it exists and differs, show the diff and replace it only if the user
   approves. Then invoke `managing-project-memory`. On `minimal`, it adds one pointer line
   to `openspec/ROUTING.md`; on `advanced`, it decides where `ROUTING.md` belongs. The
   router only works from somewhere memory reliably loads it.
```

- [ ] **Step 7: The record and retired names (step 8)**

After the paragraph ending `collision that never happened.`, add:

```markdown
   Retired names step 3 deleted leave the record; a retired name the user kept is still
   on disk, so it stays recorded as ours.
```

- [ ] **Step 8: The rule-sorting example (section 5) and the report (section 6)**

Replace `` that level's default schema is `mattpocock-bridge` `` with `` that level's default schema is `feature-flow` ``.

Replace `- what was created, updated, replaced, and backed up, with paths` with `- what was created, updated, replaced, backed up, and retired, with paths`.

- [ ] **Step 9: The matching comment in `config-facts.mjs`**

Replace `` * `mattpocock-bridge`; testing membership against only the default schema's ids would `` with `` * `feature-flow`; testing membership against only the default schema's ids would ``.

- [ ] **Step 10: Confirm no stale name survives in setup**

Run: `grep -n "mattpocock-bridge\|bridge-design-gate\|code-review-spec\|code-review-standards\|CLAUDE.md.fragment" plugins/workflows/skills/setup/SKILL.md plugins/workflows/scripts/*.mjs`
Expected: no output.

- [ ] **Step 11: Run the repository gates, then commit**

Run: `bun test && bun run audit`
Expected: both exit 0.

```bash
git add plugins/workflows/skills/setup/SKILL.md plugins/workflows/scripts/config-facts.mjs
git commit -m "Teach setup the seven-flow minimal level, retirement, and its router

Setup now describes the minimal level by kinds of work, asks about each
retired name before deleting it, installs the minimal router at
openspec/ROUTING.md with a CLAUDE.md pointer, and names feature-flow as
the default in its rule-sorting example.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Routing skill, chains, model-effort, and evals

**Files:**
- Modify: `plugins/workflows/skills/choosing-a-workflow/SKILL.md`
- Modify: `plugins/workflows/skills/choosing-a-workflow/references/chains.md`
- Modify: `plugins/workflows/skills/choosing-a-workflow/references/model-effort.md`
- Modify: `plugins/workflows/skills/choosing-a-workflow/evals/cases.md`

**Interfaces:**
- Consumes: the seven schema names and chains from Tasks 1–4; the router from Task 5; the `flow-design` pin from Task 2.
- Produces: nothing code consumes. `tests/marketplace-integrity.test.ts` reads the SKILL.md description.

**Required skills:** `authoring-skills`, `improving-prompts`.

As in Task 9: match on the sentence when a wrap differs, and keep each file's wrap width.

- [ ] **Step 1: SKILL.md frontmatter**

Replace the `description:` line with:

```yaml
description: Routes a piece of work to the right OpenSpec workflow schema among the seventeen this plugin installs — advanced's feature, bugfix, refactor, rapid, setup, spike, upgrade, hotfix; minimal's seven -flow schemas driven by Matt Pocock's skills; standard's craft-driven and surface-driven — and returns the change-creation command, the artifact chain it commits you to, and the guardrail most likely to force a reclassification later. Use when an OpenSpec change is about to be created, when asked which workflow or schema a task belongs to, when a change already underway now looks like the wrong kind of work, or on the raw request with no workflow named at all — "prod is down", "bump us past the EOL version", "extract this duplicated helper", "add tests for billing", "try both libraries and see", "fix the footer typo" — because nothing selects a schema automatically. For editing config.yaml, authoring a new schema, or CLI setup, prefer configuring-openspec.
```

Keep every schema name un-backticked: the marketplace integrity test reads a backticked hyphenated name as a skill pointer. Change `version: "1.0"` to `version: "1.1"`.

Run: `bun -e 'const t=await Bun.file("plugins/workflows/skills/choosing-a-workflow/SKILL.md").text(); console.log(t.match(/^description: (.*)$/m)[1].length)'`
Expected: `962` (the limit is 1024).

- [ ] **Step 2: SKILL.md body — opening line and preflight**

Replace `Nobody remembers twelve artifact chains, so ask.` with `Nobody remembers seventeen artifact chains, so ask.`

Replace the two bullets beginning `- **Two schemas listed**` and `- **Eight schemas listed**` with:

```markdown
- **Schemas ending in `-flow`** (`feature-flow`, `bugfix-flow`, and the rest) → this is `minimal`. Use "Route — `minimal`" below.
- **`craft-driven` and `surface-driven`** → this is `standard`. Use the two-way call below.
- **`feature`, `bugfix`, and the rest of the advanced eight** → this is `advanced`. Use the tree.
- **Sets from more than one level** → setup adds a level beside the last one rather than replacing it. Route with the set that holds `openspec/config.yaml`'s `schema:` default, and say the other set is installed too.
```

- [ ] **Step 3: SKILL.md body — the minimal route and the standard call**

Replace the whole ``## Route — two-way calls at `minimal` and `standard` `` section (heading, the sentence `Neither level ships a router…`, and the two-row table, up to but not including the paragraph beginning `The default is already in`) with:

```markdown
## Route — `minimal`

Walk `openspec/ROUTING.md`. Its tree keeps the order of the one above, with `-flow` names,
two different rules, and one addition:

- **Rule 1 differs.** Production broken now → mitigate first (roll back or flip the flag),
  then `bugfix-flow` with its Incident section. There is no `hotfix` chain.
- **Rule 8 differs.** A small code change touching no contract → `rapid-flow`. Typos, docs,
  and lint fixes are a direct commit with no change.
- **UI/UX-led work** (look, feel, layout, copy, accessibility, polish) goes to impeccable,
  not to a flow. Functionality it turns out to need becomes a `feature-flow` change.

If `ROUTING.md` is missing, use the tree above and map each schema to its `-flow` twin.

## Route — two-way call at `standard`

`standard` ships no router; with two schemas, one question decides it.

| Repo has | Default | The other one | The question |
|---|---|---|---|
| `craft-driven`, `surface-driven` | `craft-driven` | `surface-driven` | Is the change *primarily* a user-facing surface — landing page, dashboard, flow, redesign, component system? Then design leads |
```

- [ ] **Step 4: SKILL.md body — guardrails**

Replace the bullet beginning `` - **`bugfix-flow` → `mattpocock-bridge`** `` with:

```markdown
- **`rapid-flow`, `refactor-flow`, `bugfix-flow`, `upgrade-flow` → `feature-flow`** at `minimal`: a contract or a real decision appears in a rapid change; a guard assertion at the external seam has to change in a refactor (shallow tests are replaced by design, so only guard tests count); a fix changes promised behaviour rather than restoring it; an upgrade turns out to need a deliberate behaviour change.
```

Replace the bullet beginning `` - **`spike`** code is throwaway `` with:

```markdown
- **`spike`** and **`spike-flow`** code is throwaway and never merges. Learnings graduate through a new `feature` or `feature-flow` change.
```

In the paragraph beginning `De-escalate as readily as you escalate.`, append: `` At `minimal`, the same moves land on `rapid-flow` and `spike-flow`. ``

- [ ] **Step 5: SKILL.md body — "When it is not one change", "Where to look", and the self-guardrails**

Replace the three bullets under `## When it is not one change` with:

```markdown
- **An epic, too big for one change.** A change is a single unit of work. Where the mattpocock pack is installed, ask the user to run `/wayfinder` — it is user-invoked, so only they can fire it — to map the effort as decision tickets. At `minimal`, the cleared map enters `feature-flow` at its proposal; elsewhere, create one change per resolved chunk.
- **A codebase-wide cleanup.** `/improve-codebase-architecture` (also user-invoked) surfaces opportunities; each accepted one becomes its own `refactor` change, or `refactor-flow` at `minimal`.
- **UI/UX-led work at `minimal`** goes to impeccable, not to a change; see "Route — `minimal`".
- **Standing-doc upkeep** — a `CLAUDE.md` audit, a `TOOLS.md` refresh, glossary maintenance — routes to `rapid` at `advanced` and invokes the owning skill: `managing-project-memory`, `mapping-project-tooling`, or `controlled-engineering-english`. At `minimal` it is a direct commit.
```

Under `## Where to look`, replace `all twelve chains` with `all seventeen chains`, and `the eight pins that already execute` with `the six pins that already execute`.

Replace the self-guardrail bullet beginning `- **Never invent a schema name.**` with:

```markdown
- **Never invent a schema name.** Seventeen exist: seven at `minimal`, two at `standard`, and eight at `advanced` (plus `app-release` in Apple-native app repos). If nothing fits, say the work does not match any installed schema and name the closest.
```

- [ ] **Step 6: chains.md — title, contents, and the fallback paragraph**

Replace `# The twelve chains (thirteen in Apple-native app repos)` with `# The seventeen chains (eighteen in Apple-native app repos)`.

Replace `` - [`minimal` — mattpocock-bridge, bugfix-flow](#minimal) `` with `` - [`minimal` — the seven flows](#minimal) ``.

After the paragraph beginning `**Every skill invocation carries a fallback chain**`, add:

```markdown
The `minimal` flows are the exception. They call only mattpocock-skills, which that level
installs, so they carry no fallback chain beyond the `flow-design` agent's inline one.
```

- [ ] **Step 7: chains.md — replace the minimal section**

Replace everything from the line `` ## `minimal` `` up to, but not including, the line `` ## `standard` `` with:

```markdown
## `minimal`

Seven flows, every artifact driven by a skill from mattpocock-skills 1.3.1. Impeccable owns
UI/UX; the flows own functionality up to a presentation seam. `openspec/ROUTING.md` routes
between them.

### `feature-flow` — 5 artifacts, the config default

`grill → proposal → specs → design → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `grill` | — | Interview in grilling's rounds; `GLOSSARY.md` and ADRs written inline and listed under Domain terms settled |
| `proposal` | `grill` | Problem / Solution / User Stories / Capabilities, every statement traceable to the grill |
| `specs` | `proposal` | Delta specs: `ADDED` from the stories, `MODIFIED`/`REMOVED` from the main spec |
| `design` | `proposal`, `specs` | The Seams table, every scenario covered; a Presentation seam block when a surface consumes the change |
| `tasks` | `specs`, `design` | Session shape, tracer-bullet slices (published when multi-session), and the Ship group |

- **Gate:** the grill. Facts are the agent's job; decisions are the user's.
- **Hatch:** a one-line `grill.md` stub when the user waives the interview.
- **Dispatches:** `flow-design` at `design`.
- **Apply:** `tdd` at agreed seams → full suite → **commit** → `code-review` from the
  slice's start commit → one follow-up commit for findings. Multi-session slices each take a
  fresh session; the human may run `/implement-spec` instead.
- **Reroute:** a defect → `bugfix-flow`; one decision wide → `rapid-flow`; a question →
  `spike-flow`; fog → `/wayfinder`.

### `bugfix-flow` — 3 artifacts

`diagnose → specs → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `diagnose` | — | diagnosing-bugs phases 1–4: the red feedback loop, minimised reproduction, ranked hypotheses, debug tag, fix layer, and seam; an optional Incident section |
| `specs` | `diagnose` | The case the spec missed or got wrong; the scenario is the reproduction made permanent |
| `tasks` | `specs` | Failing test, fix, cleanup, Ship |

- **Gate:** a red feedback loop. No red command, no hypotheses.
- **Hatch:** `skip_specs` when the spec already covered the case.
- **Apply:** phases 5–6. Watch the test fail *for the diagnosed reason*, fix at the agreed
  layer, re-run the loop on the original scenario, and grep the debug tag away. Offers
  `/retro`, and `/improve-codebase-architecture` when there was no correct seam.
- **Reroute:** a fix that changes promised behaviour → `feature-flow`. If the fix does not
  hold, update `diagnose.md`, not the code.

### `refactor-flow` — 3 artifacts

`grill → design → tasks`, then `apply`. No `specs` artifact.

| Artifact | `requires` | Carries |
|---|---|---|
| `grill` | — | The module being deepened, its dependency category, and the external behaviour that must not change |
| `design` | `grill` | Target interface, seam and adapters, guard tests, and tests to replace |
| `tasks` | `design` | Guard tests first, then slices, or expand → migrate → contract |

- **Gate:** agreed guard tests at the external seam.
- **Dispatches:** `flow-design` at `design`; design-it-twice runs in the main session first
  when the user wants alternatives.
- **Apply:** replace, don't layer. A shallow test goes only once its replacement passes.
- **Reroute:** a guard assertion that has to change → `feature-flow`.

### `spike-flow` — 2 artifacts

`question → findings`; `apply` tracks `question.md`.

- **Gate:** a hard timebox and answer criteria.
- **Apply:** `prototype` and `research` experiments. The prototype stays on its branch and
  never merges.
- **Post-apply:** `findings.md`, gated by `question.md`'s last checkbox.
- **Scope:** "what should it look like" goes to impeccable, not here.

### `upgrade-flow` — 3 artifacts

`inventory → surfaces → tasks`, then `apply`. No `specs` artifact.

| Artifact | `requires` | Carries |
|---|---|---|
| `inventory` | — | Breaking changes from `research` over primary sources, each with an applies-to-us verdict |
| `surfaces` | `inventory` | Search-verified call sites, classed mechanical / behavioural / unknown |
| `tasks` | `surfaces` | Bump → codemods → batches → behavioural surfaces with equivalence checks → shims deleted |

- **Gate:** the research file. Verdicts wait for it.
- **Apply:** the lockfile commits with its code; `wizard` scripts the human-only steps.
- **Reroute:** an unknown surface → `spike-flow`; a deliberate behaviour change →
  `feature-flow`.

### `setup-flow` — 2 artifacts

`decisions → tasks`, then `apply`. No `specs` artifact.

- **Gate:** the stack decisions, each with its ADR.
- **Apply:** the human runs `/setup-matt-pocock-skills` first; a walking skeleton with one
  real `tdd` test green in CI; guardrails wired; `wizard` for secrets and provisioning.

### `rapid-flow` — 2 artifacts

`proposal → tasks`, then `apply`, in one window. No `specs` artifact.

- **Gate:** the contract check in `proposal.md`.
- **Reroute:** a contract or a real decision → `feature-flow`.
```

- [ ] **Step 8: chains.md — the shared rules and sources**

In `## Rules that apply to every chain`:

- Replace `` `mattpocock-bridge` wants `grill` through `tasks` in one unbroken window `` with `` `feature-flow` wants `grill` through `tasks` in one unbroken window ``.
- In the post-apply bullet, replace `` `spike`'s `findings` `` with `` `spike`'s and `spike-flow`'s `findings` ``.
- Replace the sentence `` it does not read `skip_grill` or `skip_surface`, so those need a one-line stub file to unblock the graph. `` with `` it reads no other skip key, so `skip_grill` needs a one-line stub file to unblock the graph. ``

In the closing `Sources:` paragraph, replace `the twelve` with `the seventeen`, replace `` `payload/levels/advanced/openspec/ROUTING.md` `` with `` `payload/levels/minimal/openspec/ROUTING.md`, `payload/levels/advanced/openspec/ROUTING.md` ``, and replace `the eight agent files` (or `the\neight agent files`) with `the six agent files`.

- [ ] **Step 9: model-effort.md — the pins**

Replace `## The eight pins` with `## The six pins`.

In the pins table, replace the three `minimal` rows (`bridge-design-gate`, `code-review-standards`, `code-review-spec`) with:

```markdown
| `minimal` | `flow-design` | `feature-flow` and `refactor-flow` · design | `opus` | `xhigh` |
```

At the end of the bullet beginning ``**Every design gate is top tier at `xhigh`.**``, append: `` At `minimal`, design always exists but shrinks to the Seams table for a one-module change; `flow-design` stays pinned because the hard cases still arrive there. ``

Replace the bullet beginning `**Review splits by axis onto different tiers.**` with:

```markdown
- **Review splits differently per level.** At `advanced`, `taste-preflight` is a cheap
  mechanical pass and the review gate is judgement. At `minimal`, review is `code-review`'s
  own two sub-agents on the session's model, which is why apply tells the user to review
  from a fresh session on a strong model.
```

- [ ] **Step 10: model-effort.md — the recommendation tables**

Replace the `## What is recommended` paragraph and its five-column table (from ``For `minimal` and `standard`, a per-artifact recommendation exists`` through the `| closing gate |` row) with:

```markdown
For `standard`, a per-artifact recommendation exists and agrees with the pins above almost
exactly:

| Artifact | `craft-driven` | `surface-driven` |
|---|---|---|
| opening | brainstorm · Opus high | design-brief · Opus high for a new visual world, Sonnet medium for a refinement |
| proposal | Opus high | Sonnet medium |
| surface / design-brief | Sonnet medium, Opus high for a new world | (leads) |
| specs | Opus high | Sonnet medium, Opus high if the surface is broad |
| design | top tier xhigh | — |
| tasks | Opus high | Opus high |
| apply | Sonnet workers, Haiku mechanical, Opus on BLOCKED | Sonnet medium; surface tasks stay off Haiku |
| review | (in verification) | (in quality) |
| closing gate | verification Sonnet medium plus an Opus xhigh reviewer | quality Sonnet medium, Opus high verdict on a large redesign |

For the `minimal` seven, the rows follow the `advanced` table below for the same kind of
work, plus the `flow-design` pin:

| Flow | Planning | Implementation |
|---|---|---|
| `feature-flow` | Opus high — **xhigh at design, through the `flow-design` pin** | Sonnet medium; review from a fresh session on Opus high |
| `bugfix-flow` | **Opus xhigh at diagnose** — root cause | Sonnet medium; Opus high review when the fix touched shared code |
| `refactor-flow` | Opus high — **xhigh at design, through the pin** | Sonnet medium; Haiku for mechanical migrate batches |
| `upgrade-flow` | Opus high; `research` runs in the background | Sonnet medium; Haiku for codemod batches |
| `setup-flow` | Opus high | Sonnet medium |
| `spike-flow` | Sonnet low–medium | Sonnet medium |
| `rapid-flow` | Sonnet low–medium | Sonnet medium |
```

- [ ] **Step 11: model-effort.md — the remaining mentions**

- Replace `` `mattpocock-bridge` wants its planning run in one unbroken window `` with `` `feature-flow` wants its planning run in one unbroken window ``.
- Replace `` `code-review-spec` and `taste-preflight` are `sonnet` by design, the gates are not. `` with `` `taste-preflight` is `sonnet` by design; the gates and `flow-design` are not. ``
- In `Sources:`, replace `the eight agent files` with `the six agent files`, and replace `` the `minimal`/`standard` table from the mattpocock model-and-effort guide `` with `` the `standard` table from the mattpocock model-and-effort guide; the `minimal` table, derived from the `advanced` one for the same kinds of work ``.

- [ ] **Step 12: evals/cases.md**

Replace the Case 3 heading with `` ## Case 3 — Wrong level (repo at `standard`, two schemas installed) ``. Its assertions stand: `standard` has no upgrade schema.

Insert before `## Grading notes`:

```markdown
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
```

Replace the first sentence of `## Grading notes` with: `Cases 1, 2, 4, 8, and 9 test routing accuracy; case 3 tests that the preflight actually runs; case 5 tests the sibling boundary; case 6 tests the one-question rule; case 7 tests the model reference; case 10 tests the UI boundary at minimal.`

- [ ] **Step 13: Confirm no stale name survives in the skill**

Run: `grep -rn "mattpocock-bridge\|bridge-design-gate\|code-review-spec\|code-review-standards\|twelve\|eight pins\|eight agent" plugins/workflows/skills/choosing-a-workflow`
Expected: no output.

- [ ] **Step 14: Run the repository gates, then commit**

Run: `bun test && bun run audit`
Expected: both exit 0. `tests/marketplace-integrity.test.ts` passes, which confirms the description names no unshipped skill.

```bash
git add plugins/workflows/skills/choosing-a-workflow
git commit -m "Route to the seven minimal flows by name

choosing-a-workflow now detects the level from schema names rather than a
count, walks the minimal router, and states the minimal guardrails and
the impeccable boundary. chains.md, model-effort.md, and the evals follow.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: README, manifests, and the version bump

**Files:**
- Modify: `plugins/workflows/README.md` (levels table; "What setup does" step 4)
- Modify: `plugins/workflows/.claude-plugin/plugin.json` (description, version)
- Modify: `.claude-plugin/marketplace.json` (the `workflows` entry's description)

**Interfaces:**
- Consumes: everything above.
- Produces: release `0.8.0`.

**Required skills:** `authoring-plugins`, `maintaining-plugin-marketplaces`.

- [ ] **Step 1: README levels table**

Replace `` | `minimal` | 2 | 6 artifacts | no | `` with `` | `minimal` | 7 | 5 artifacts | yes | ``.

- [ ] **Step 2: README "What setup does", step 4**

Replace `→ schemas → agents → TOOLS.md →` with `→ schemas → agents → retired names, each approved →`, keeping `TOOLS.md →` after it, and replace `` `config.yaml` → CLAUDE.md → `` with `` `config.yaml` → router and CLAUDE.md → ``. Rewrap to the file's width. Leave the Learn section as it is (spec §17).

- [ ] **Step 3: Manifests**

In `plugins/workflows/.claude-plugin/plugin.json`, replace `among the twelve it installs` with `among the seventeen it installs`, and `"version": "0.7.0"` with `"version": "0.8.0"`.

In `.claude-plugin/marketplace.json`, make the same `twelve` → `seventeen` replacement in the `workflows` entry. The two descriptions MUST stay byte-identical.

- [ ] **Step 4: Confirm nothing stale survives outside `learn/`**

Run: `grep -rn "mattpocock-bridge\|bridge-design-gate\|code-review-spec\|code-review-standards\|CLAUDE.md.fragment" plugins/workflows .claude-plugin README.md | grep -v "/learn/" | grep -v "retired.json"`
Expected: no output.

- [ ] **Step 5: Run every gate**

Run: `bun test && bun run audit && claude plugin validate . && bun run audit --since main`
Expected: all exit 0. The `--since main` audit reports `workflows` as changed **and** bumped, and names no other plugin.

- [ ] **Step 6: Commit**

```bash
git add plugins/workflows/README.md plugins/workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release workflows 0.8.0: seven Pocock-driven minimal flows

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: End-to-end dry run in a scratch repository

**Files:** none in the repository. Everything below writes under a temporary directory.

**Interfaces:**
- Consumes: the whole branch.
- Produces: evidence for spec §16 — the seven schemas validate in a real project, `verify.mjs` reports green, and a no-specs change validates.

**Required skills:** `superpowers:verification-before-completion`.

- [ ] **Step 1: Set up the scratch repository**

```bash
WT="$(git rev-parse --show-toplevel)"
SCRATCH="$(mktemp -d)/app"; mkdir -p "$SCRATCH"
export OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1
git -C "$SCRATCH" init -q && git -C "$SCRATCH" commit -q --allow-empty -m init
(cd "$SCRATCH" && openspec init --tools claude >/dev/null)
BEFORE="$(node -e 'const {join}=require("node:path"),{pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({hashTree})=>console.log(JSON.stringify({specs:hashTree(join(process.argv[2],"openspec","specs")),changes:hashTree(join(process.argv[2],"openspec","changes"))})))' "$WT/plugins/workflows/scripts/lib/tree.mjs" "$SCRATCH")"
node "$WT/plugins/workflows/scripts/detect.mjs" "$SCRATCH" | node "$WT/plugins/workflows/scripts/plan.mjs" minimal > "$SCRATCH/../plan.json"
```

Expected: `plan.json` lists the seven flows under `schemas.copy`, `flow-design.md` under `agents.copy`, and `retire` with four empty lists.

- [ ] **Step 2: Copy the payload and validate every schema**

```bash
COPY='const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({copyAdditive})=>{require("node:fs").mkdirSync(process.argv[3],{recursive:true});console.log(JSON.stringify(copyAdditive(process.argv[2],process.argv[3],{overwrite:[]})))})'
node -e "$COPY" "$WT/plugins/workflows/scripts/lib/tree.mjs" "$WT/plugins/workflows/payload/levels/minimal/openspec/schemas" "$SCRATCH/openspec/schemas"
node -e "$COPY" "$WT/plugins/workflows/scripts/lib/tree.mjs" "$WT/plugins/workflows/payload/levels/minimal/agents" "$SCRATCH/.claude/agents"
cp "$WT/plugins/workflows/payload/levels/minimal/openspec/config.yaml.example" "$SCRATCH/openspec/config.yaml"
cp "$WT/plugins/workflows/payload/levels/minimal/openspec/ROUTING.md" "$SCRATCH/openspec/ROUTING.md"
for s in bugfix-flow feature-flow rapid-flow refactor-flow setup-flow spike-flow upgrade-flow; do (cd "$SCRATCH" && openspec schema validate "$s"); done
```

Expected: seven `✓ Schema '<name>' is valid` lines.

- [ ] **Step 3: Record and verify**

```bash
node "$WT/plugins/workflows/scripts/record.mjs" "$SCRATCH" < "$SCRATCH/../plan.json"
node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({verify})=>{const r=verify(process.argv[2],{before:JSON.parse(process.argv[3]),expectRules:JSON.parse(process.argv[4]),expectPlugins:[]});console.log(JSON.stringify(r,null,2));process.exit(r.ok?0:1)})' \
  "$WT/plugins/workflows/scripts/verify.mjs" "$SCRATCH" "$BEFORE" '["Name domain concepts with GLOSSARY.md terms."]'
```

Expected: the record lists seven schemas and `flow-design.md`, and `verify` prints `"ok": true` and exits 0. If a check fails, report its name and detail verbatim and stop. A failing check is a result, not an obstacle to route around.

- [ ] **Step 4: A change under a schema with no specs artifact validates**

```bash
cd "$SCRATCH"
openspec new change try-rapid --schema rapid-flow
cat openspec/changes/try-rapid/.openspec.yaml
printf '## What & Why\n\nRename one internal helper so its name says what it returns.\n\n**Contract check:** No contract touched.\n' > openspec/changes/try-rapid/proposal.md
printf '## Tasks\n\n- [ ] Rename the helper: the suite passes\n\n## Ship\n\n- [ ] code-review findings resolved in one follow-up commit\n' > openspec/changes/try-rapid/tasks.md
openspec validate try-rapid --strict
openspec instructions proposal --change try-rapid | grep -q "Name domain concepts with GLOSSARY.md terms." && echo injected
rm -r openspec/changes/try-rapid
cd "$WT"
```

Expected: `.openspec.yaml` contains `schema: rapid-flow` and `skip_specs: true`; `openspec validate` reports `Change 'try-rapid' is valid`; the rule check prints `injected`. If `validate` rejects the change, stop and report: spec §7.3–7.7 depends on it.

- [ ] **Step 5: Final gates on the branch**

Run: `bun test && bun run audit && claude plugin validate .`
Expected: all exit 0.

- [ ] **Step 6: Finish the branch**

Invoke `superpowers:finishing-a-development-branch` to choose between a PR, a merge, or keeping the branch.
