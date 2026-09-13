# Apple-Native Workflows Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the workflows plugin to detect Apple-native repositories, install the apple-studio layer, ship an `app-release` schema and HIG design gate at the advanced level, and sweep apple-studio's Apple documentation links to their `.md` form.

**Architecture:** Two-tier detection in `detect.mjs` (Swift signals gate a plugin manifest; app signals gate advanced-level payload content nested at `payload/levels/advanced/apple/`). `buildPlan` composes the apple manifest and unions the apple subtree into its shipped-name lists; `classify` and the I2/I6 ownership machinery run unchanged over the merged lists. Verification delegates to TOOLS.md rather than per-stack template variants.

**Tech Stack:** Node ESM scripts (`.mjs`), Bun test (`bun:test`), OpenSpec schema YAML, static HTML learn material.

**Spec:** `docs/superpowers/specs/2026-09-13-workflows-apple-native-design.md` — read it alongside this plan; the decision log there is binding.

## Global Constraints

- Gates before ANY commit touching `plugins/`: `bun test` AND `bun run audit` (repo CLAUDE.md).
- Version bumps: `plugins/workflows/.claude-plugin/plugin.json` `0.6.0` → `0.7.0`; `plugins/apple-studio/.claude-plugin/plugin.json` `0.9.0` → `0.9.1`. No version field anywhere else.
- Before editing anything under `plugins/apple-studio/`: read `authoring/apple-studio/CONVENTIONS.md`. `.claude/rules/apple-studio.md` applies.
- Required skills per surface (spec §14) — load BEFORE editing:
  - OpenSpec schema/templates/ROUTING.md → `configuring-openspec`
  - Prompt-bearing prose (schema `instruction:`, gate agent, template rewording) → `improving-prompts`
  - `apple-design-gate.md` → `authoring-subagents`
  - SKILL.md edits → `authoring-skills`
  - Plugin manifests/READMEs/versions → `authoring-plugins`
  - Marketplace entry → `maintaining-plugin-marketplaces`
- Match the codebase's comment style: `detect.mjs`/`plan.mjs` carry constraint-explaining comments; keep new comments in that register, and never narrate what a line does.
- **Known drift (verified 2026-09-13, binding for this plan):** the workflows README's Development section describes a test harness that never traveled from the plugin's source repo. There are NO existing `tests/workflows-*.test.ts` files, NO `ci-workflows.test.ts`, NO `test:workflows:e2e` or `learn:*` package scripts, NO `.github/workflows/pages.yml`. This plan CREATES `tests/workflows-detect.test.ts` and `tests/workflows-plan.test.ts` covering the new behavior only. The spec's "e2e opt-in fixture" item is satisfied by an integration-style test (real `detect` on a temp fixture piped into `buildPlan`) in Task 5. The spec's `.agents/skills/` re-sync ride-along is VOID: `skills-lock.json` vendors only meta-skills and typescript skills, no apple-studio skills.
- Execution isolation: use `superpowers:using-git-worktrees`. Branch from `phase-8-apple-studio` (it carries the spec commit `a847da0`). Do not touch that branch's staged Phase 8 files.

---

### Task 1: Apple detection in detect.mjs

**Files:**
- Modify: `plugins/workflows/scripts/detect.mjs` (add `appleSignals` + `xcodeMcpConfigured` after `webSignals` at line ~47; add `apple` field to the return object at line ~184)
- Create: `tests/workflows-detect.test.ts`

**Interfaces:**
- Consumes: existing `dirNames(dir)` (guarded readdir, directories only), `detect(repoRoot, { run })` with injectable `run`.
- Produces: `detection.apple = { app: boolean, swift: boolean, signals: string[], xcodeMcpConfigured: boolean }`. Signal strings are `'app:<relpath>'` or `'swift:Package.swift'`, sorted. `swift` is true whenever ANY signal exists (app signals imply tier 1). Tasks 2, 3, 5, 7 rely on these exact names.

**Required skills:** none (plain code).

- [ ] **Step 1: Write the failing tests**

```ts
// tests/workflows-detect.test.ts
import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';

/** Never spawn during tests: openspec/bun version probes return "absent". */
const stubRun = () => null;

function repo(build: (root: string) => void = () => {}): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-apple-'));
	build(root);
	return root;
}

const apple = (root: string) => detect(root, { run: stubRun }).apple;

describe('appleSignals', () => {
	test('empty repo has no apple signals', () => {
		expect(apple(repo())).toEqual({ app: false, swift: false, signals: [], xcodeMcpConfigured: false });
	});

	test('bare Package.swift is tier 1 only', () => {
		const a = apple(repo((r) => writeFileSync(join(r, 'Package.swift'), '// swift-tools-version:6.0')));
		expect(a.swift).toBe(true);
		expect(a.app).toBe(false);
		expect(a.signals).toEqual(['swift:Package.swift']);
	});

	test('a root .xcodeproj bundle is an app signal and implies tier 1', () => {
		const a = apple(repo((r) => mkdirSync(join(r, 'App.xcodeproj'))));
		expect(a.app).toBe(true);
		expect(a.swift).toBe(true);
		expect(a.signals).toEqual(['app:App.xcodeproj']);
	});

	test('an .xcodeproj one directory deep is found; two deep is not', () => {
		const a = apple(repo((r) => {
			mkdirSync(join(r, 'ios', 'App.xcodeproj'), { recursive: true });
			mkdirSync(join(r, 'apps', 'ios2', 'Deep.xcodeproj'), { recursive: true });
		}));
		expect(a.signals).toEqual(['app:ios/App.xcodeproj']);
	});

	test('node_modules and dot-directories are not scanned', () => {
		const a = apple(repo((r) => {
			mkdirSync(join(r, 'node_modules', 'Fake.xcodeproj'), { recursive: true });
			mkdirSync(join(r, '.build', 'Fake.xcodeproj'), { recursive: true });
		}));
		expect(a.signals).toEqual([]);
	});

	test('Tuist, Project.swift, project.yml, and .xcworkspace are app signals', () => {
		expect(apple(repo((r) => mkdirSync(join(r, 'Tuist')))).app).toBe(true);
		expect(apple(repo((r) => writeFileSync(join(r, 'Project.swift'), ''))).app).toBe(true);
		expect(apple(repo((r) => writeFileSync(join(r, 'project.yml'), 'name: App'))).app).toBe(true);
		expect(apple(repo((r) => mkdirSync(join(r, 'App.xcworkspace')))).app).toBe(true);
	});
});

describe('xcodeMcpConfigured', () => {
	test('absent .mcp.json reads as not configured', () => {
		expect(apple(repo()).xcodeMcpConfigured).toBe(false);
	});

	test('an xcode server in .mcp.json reads as configured', () => {
		const a = apple(repo((r) =>
			writeFileSync(join(r, '.mcp.json'), JSON.stringify({ mcpServers: { xcode: { command: 'xcrun' } } })),
		));
		expect(a.xcodeMcpConfigured).toBe(true);
	});

	test('unparseable .mcp.json reads as not configured, never crashes', () => {
		const a = apple(repo((r) => writeFileSync(join(r, '.mcp.json'), '{ nope,')));
		expect(a.xcodeMcpConfigured).toBe(false);
	});
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bun test tests/workflows-detect.test.ts`
Expected: FAIL — `apple` is `undefined` on the detection object.

- [ ] **Step 3: Implement in detect.mjs**

Insert after `webSignals` (below line 47). The comment register matches the file: say why, not what.

```js
/**
 * Two tiers, consumed separately by plan.mjs: app signals gate the advanced-level
 * Apple content; any signal at all gates the apple plugin manifest. The xcodeproj
 * scan goes one directory deep (monorepos put the app in ios/ or apps/) and no
 * deeper — node_modules alone makes a full walk unaffordable, and the skip list
 * below is why a vendored fixture can never masquerade as the user's app.
 */
const APPLE_SCAN_SKIP = new Set(['node_modules']);

function appleSignals(repoRoot) {
	const signals = [];
	const bundles = (dir) =>
		dirNames(dir).filter((n) => n.endsWith('.xcodeproj') || n.endsWith('.xcworkspace'));
	for (const name of bundles(repoRoot)) signals.push(`app:${name}`);
	for (const sub of dirNames(repoRoot)) {
		if (sub.startsWith('.') || APPLE_SCAN_SKIP.has(sub)) continue;
		for (const name of bundles(join(repoRoot, sub))) signals.push(`app:${sub}/${name}`);
	}
	if (existsSync(join(repoRoot, 'Project.swift'))) signals.push('app:Project.swift');
	if (existsSync(join(repoRoot, 'Tuist'))) signals.push('app:Tuist');
	if (existsSync(join(repoRoot, 'project.yml'))) signals.push('app:project.yml');
	if (existsSync(join(repoRoot, 'Package.swift'))) signals.push('swift:Package.swift');
	return signals.sort();
}

/**
 * Read, never spawn: `claude mcp list` would be a subprocess for a question one JSON
 * read answers. An unparseable .mcp.json counts as "not configured" — the human step
 * this feeds errs toward telling the user how to connect Xcode, which costs nothing
 * when it turns out already done.
 */
function xcodeMcpConfigured(repoRoot) {
	const p = join(repoRoot, '.mcp.json');
	if (!existsSync(p)) return false;
	try {
		return Boolean(JSON.parse(readFileSync(p, 'utf8'))?.mcpServers?.xcode);
	} catch {
		return false;
	}
}
```

Then inside `detect()`, next to the web fields (after line ~176 `const signals = webSignals(repoRoot);`):

```js
	const appleSigs = appleSignals(repoRoot);
```

and in the returned object, directly after `webSignals: signals,`:

```js
		apple: {
			app: appleSigs.some((s) => s.startsWith('app:')),
			swift: appleSigs.length > 0,
			signals: appleSigs,
			xcodeMcpConfigured: xcodeMcpConfigured(repoRoot),
		},
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bun test tests/workflows-detect.test.ts`
Expected: PASS (9 tests).

- [ ] **Step 5: Run the full gates**

Run: `bun test && bun run audit`
Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add plugins/workflows/scripts/detect.mjs tests/workflows-detect.test.ts
git commit -m "feat(workflows): two-tier Apple-native detection in detect.mjs"
```

---

### Task 2: Apple plugin manifest and tier-1 composition

**Files:**
- Create: `plugins/workflows/payload/base/settings.base.apple.json`
- Modify: `plugins/workflows/scripts/plan.mjs` (manifest push at line ~153; `apple` field in the return object at line ~211)
- Create: `tests/workflows-plan.test.ts`

**Interfaces:**
- Consumes: `detection.apple.swift` (Task 1); `buildPlan(detection, { level, payloadRoot })` (existing, `payloadRoot` is a TEST-ONLY seam).
- Produces: plan JSON gains `apple: { app: boolean, swift: boolean }`; `plugins.install` gains `'apple-studio@agent-tools'` on tier 1. The `makeDetection` test helper — Tasks 3 and 5 reuse it.

**Required skills:** `authoring-plugins` (manifest file).

- [ ] **Step 1: Write the failing tests**

```ts
// tests/workflows-plan.test.ts
import { describe, expect, test } from 'bun:test';
// @ts-expect-error untyped .mjs module
import { buildPlan } from '../plugins/workflows/scripts/plan.mjs';

/** Minimal valid detection; override per test. Workflows include new/continue so no profile warning noise. */
export function makeDetection(overrides: Record<string, unknown> = {}) {
	return {
		repoRoot: '/tmp/fake',
		web: false,
		webSignals: [],
		apple: { app: false, swift: false, signals: [], xcodeMcpConfigured: false },
		openspec: { present: true, hasSpecs: false, hasChanges: false, schemas: [], schemaHashes: {}, configPath: null },
		agents: { files: [], hashes: {} },
		settings: { present: false, status: 'absent', decided: [] },
		runtime: { node: 'v0.0.0', bun: null },
		openspecCli: { version: null, profile: 'custom', workflows: ['propose', 'explore', 'apply', 'update', 'sync', 'archive', 'new', 'continue'] },
		humanArtifacts: { issueTracker: true, product: true, design: true, tools: false },
		priorRun: false,
		prior: null,
		...overrides,
	};
}

const APPLE = { app: true, swift: true, signals: ['app:App.xcodeproj'], xcodeMcpConfigured: false };
const SWIFT_ONLY = { app: false, swift: true, signals: ['swift:Package.swift'], xcodeMcpConfigured: false };

describe('tier-1 apple manifest', () => {
	test('a Swift signal installs apple-studio', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'minimal' });
		expect(plan.plugins.install).toContain('apple-studio@agent-tools');
		expect(plan.plugins.marketplaces.map((m: { name: string }) => m.name)).toContain('agent-tools');
	});

	test('no Swift signal, no apple-studio', () => {
		const plan = buildPlan(makeDetection(), { level: 'minimal' });
		expect(plan.plugins.install).not.toContain('apple-studio@agent-tools');
	});

	test('a decided apple-studio is skipped, never overridden (I3)', () => {
		const plan = buildPlan(
			makeDetection({ apple: SWIFT_ONLY, settings: { present: true, status: 'ok', decided: ['apple-studio@agent-tools'] } }),
			{ level: 'minimal' },
		);
		expect(plan.plugins.install).not.toContain('apple-studio@agent-tools');
		expect(plan.plugins.skip.map((s: { id: string }) => s.id)).toContain('apple-studio@agent-tools');
	});

	test('the plan carries the apple field', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'standard' });
		expect(plan.apple).toEqual({ app: true, swift: true });
	});

	test('a detection with no apple field (older build) degrades to false, not a crash', () => {
		const d = makeDetection();
		delete (d as Record<string, unknown>).apple;
		const plan = buildPlan(d, { level: 'minimal' });
		expect(plan.apple).toEqual({ app: false, swift: false });
	});
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bun test tests/workflows-plan.test.ts`
Expected: FAIL — no apple manifest is pushed, `plan.apple` is `undefined`.

- [ ] **Step 3: Create the manifest and wire it in**

`plugins/workflows/payload/base/settings.base.apple.json` (tabs, matching the sibling manifests):

```json
{
	"enabledPlugins": {
		"apple-studio@agent-tools": true
	},
	"extraKnownMarketplaces": {
		"agent-tools": {
			"source": { "repo": "frenchfulton94/agent-tools", "source": "github" }
		}
	}
}
```

In `plan.mjs`, directly after the web line (line 153):

```js
	if (detection.apple?.swift) manifests.push(readJson(join(payloadRoot, 'base', 'settings.base.apple.json')));
```

In the return object, directly after `web: detection.web,`:

```js
		apple: { app: Boolean(detection.apple?.app), swift: Boolean(detection.apple?.swift) },
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bun test tests/workflows-plan.test.ts`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/workflows/payload/base/settings.base.apple.json plugins/workflows/scripts/plan.mjs tests/workflows-plan.test.ts
git commit -m "feat(workflows): apple plugin layer composes on any Swift signal"
```

---

### Task 3: The app-release schema and templates

**Files:**
- Create: `plugins/workflows/payload/levels/advanced/apple/openspec/schemas/app-release/schema.yaml`
- Create: `.../app-release/templates/release-scope.md`
- Create: `.../app-release/templates/preflight.md`
- Create: `.../app-release/templates/tasks.md`
- Create: `.../app-release/templates/post-release.md`

**Interfaces:**
- Consumes: nothing from other tasks (pure payload content).
- Produces: the `app-release` schema directory name — Task 5's composition tests and Task 7's SKILL.md copy step reference it by exactly this name. Artifact ids: `release-scope`, `preflight`, `tasks`, `post-release`.

**Required skills:** `configuring-openspec` (read `references/custom-schemas.md` for the schema contract), `improving-prompts` (every `instruction:` block is a prompt).

- [ ] **Step 1: Read the format authorities**

Read `plugins/workflows/skills/configuring-openspec/references/custom-schemas.md` and `plugins/workflows/payload/levels/advanced/openspec/schemas/hotfix/schema.yaml` (the closest sibling in spirit: chain discipline under pressure). The new schema MUST match hotfix's field set exactly: `name`, `version`, `description`, `artifacts[]` (`id`, `generates`, `description`, `template`, `instruction`, `requires`), `apply` (`requires`, `tracks`, `instruction`).

- [ ] **Step 2: Write schema.yaml**

```yaml
name: app-release
version: 1
description: >
  Workflow for shipping an Apple-platform build to TestFlight or the App
  Store. Release work is checklist-and-evidence work, not code work: the
  chain gates submission on preflight evidence and closes with a monitored
  rollout. Without this schema, releases ride ad hoc checklists and the
  steps the App Store punishes get skipped. Sources: the apple-studio
  app-release skill (mechanics); the hotfix schema (verification-signal
  discipline).

artifacts:
  - id: release-scope
    generates: release-scope.md
    description: What ships, as what version and build, decided and owned
    template: release-scope.md
    instruction: |
      Record what this release contains and what number it ships as.
      Decide marketing version against build number explicitly and say
      why. List what merged since the last release from the archive and
      git history — a decision record, not a changelog dump. Name the
      phased-release intent and the go/no-go owner. Invoke the
      apple-studio app-release skill for versioning rules (fallback:
      CFBundleShortVersionString is user-facing, CFBundleVersion only
      ever increases).
    requires: []

  - id: preflight
    generates: preflight.md
    description: Pre-submission checklist with named evidence per item
    template: preflight.md
    instruction: |
      Work the checklist the App Store punishes you for skipping: signing
      and provisioning, privacy manifest and nutrition-label answers
      checked against what the code actually does, screenshots and
      metadata, export compliance, review notes with a working demo
      account. Every item names the evidence checked — a command run, a
      screenshot, an App Store Connect page state — never a bare
      checkbox. Invoke the apple-studio app-release skill for the current
      requirements (fallback: the template lists the stable core).
    requires: [release-scope]

  - id: tasks
    generates: tasks.md
    description: Submission steps, each with its verification signal
    template: tasks.md
    instruction: |
      List the archive, upload, TestFlight, and submission steps in
      order. Every step names the observable signal proving it worked —
      the build appears in App Store Connect processing, TestFlight
      installs on a physical device, the review state transitions.
      "It uploaded" without the signal is how releases stall silently. A
      code defect discovered here stops the release: create a bugfix
      change, link it, and resume only when it ships. The release chain
      never absorbs code fixes.
    requires: [preflight]

  - id: post-release
    generates: post-release.md
    description: Phased-release monitoring plan, completed before archiving
    template: post-release.md
    instruction: |
      Complete after the release ships and before archiving. Record the
      monitoring plan: the crash-rate and key-metric thresholds that
      pause the rollout, who watches them, and for how long. Link every
      follow-up change this release surfaced. A release without a
      monitoring plan is a release you learn about from reviews.
    requires: [tasks]

apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Execute the submission steps now, verifying each step's signal before
    the next. Drive builds and uploads with the apple-studio xcode-loop
    and app-release skills (fallback: xcodebuild archive, then upload via
    Xcode's Organizer). A code defect stops the release and spawns a
    bugfix change — fix nothing inline. Once released: complete
    post-release.md with the monitoring plan before archiving. An urgent
    fix already live in the store routes its code work through hotfix;
    the expedited-review submission still goes through this chain,
    referencing it.
```

- [ ] **Step 3: Write the four templates**

`templates/release-scope.md`:

```markdown
<!-- A decision record, not a changelog dump. -->

## Version and Build

<!-- Marketing version and build number, and why this pair. -->

## Contents

<!-- What merged since the last release — from the archive and git history. -->

## Rollout Intent

<!-- Phased release or all-at-once, and the go/no-go owner by name. -->
```

`templates/preflight.md`:

```markdown
<!-- Every item names the evidence checked — a command run, a screenshot,
an App Store Connect page state. A bare checkbox is not preflight. -->

## Signing and Provisioning

<!-- Certificate validity, profile match, evidence. -->

## Privacy

<!-- Privacy manifest and nutrition-label answers against actual code behavior. -->

## Store Metadata

<!-- Screenshots current, description, what's-new, export compliance. -->

## Review Notes

<!-- A demo account that works; anything reviewers cannot reach on their own. -->
```

`templates/tasks.md`:

```markdown
<!-- Each step ends with the observable signal proving it worked. A code
defect discovered here stops the release and spawns a bugfix change. -->

- [ ] Archive the release build — signal: archive succeeds with the release configuration
- [ ] Upload — signal: build appears in App Store Connect processing
- [ ] TestFlight internal — signal: installs and launches on a physical device
- [ ] TestFlight external (when used) — signal: external build approved and installable
- [ ] Submit for review — signal: review state transitions to In Review
```

`templates/post-release.md`:

```markdown
<!-- Completed after the release ships, before archiving the change. -->

## Monitoring

<!-- Thresholds that pause the rollout, who watches them, for how long. -->

## Follow-ups

<!-- Every change this release surfaced, linked. -->
```

- [ ] **Step 4: Verify shape against a sibling**

Run: `diff <(grep -E '^\S|^  - id:' plugins/workflows/payload/levels/advanced/openspec/schemas/hotfix/schema.yaml | grep -oE '^\S+') <(grep -E '^\S|^  - id:' plugins/workflows/payload/levels/advanced/apple/openspec/schemas/app-release/schema.yaml | grep -oE '^\S+') | head`
Expected: top-level key order identical (`name:`, `version:`, `description:`, `artifacts:`, `apply:`); only artifact counts differ.

- [ ] **Step 5: Commit**

```bash
git add plugins/workflows/payload/levels/advanced/apple/
git commit -m "feat(workflows): app-release schema and templates for Apple app repos"
```

---

### Task 4: The apple-design-gate agent

**Files:**
- Create: `plugins/workflows/payload/levels/advanced/apple/agents/apple-design-gate.md`

**Interfaces:**
- Consumes: the frontmatter shape of `plugins/workflows/payload/levels/advanced/agents/design-gate.md` — read it FIRST and mirror its exact frontmatter fields (whatever it declares: name, description, and any tools/model fields).
- Produces: the file name `apple-design-gate.md` — Task 5's composition tests reference it exactly.

**Required skills:** `authoring-subagents` (frontmatter contract, description-driven delegation), `improving-prompts` (the body is a prompt).

- [ ] **Step 1: Read the sibling gate**

Read `plugins/workflows/payload/levels/advanced/agents/design-gate.md` end to end. Mirror its frontmatter field set and its overall section structure. The body below is the content; adapt its shape to the sibling's, not vice versa.

- [ ] **Step 2: Write the agent**

Frontmatter: `name: apple-design-gate`, and this description (adjust only if the sibling's frontmatter carries additional fields to mirror): `Design gate for Apple-platform surfaces — reviews a change's UI against the HIG and platform idioms, then verifies on a built, running app before approving. Delegate to it before archiving any advanced-level change that touches SwiftUI, AppKit, or UIKit surfaces.` Body content:

```markdown
You are the design gate for Apple-platform surfaces. A change that touches
UI does not pass until you have reviewed it against the platform's own
rules and seen it running.

Ground every judgment in the apple-studio skills:

- `apple-design` — HIG conformance, platform idioms, accessibility.
- `apple-macos` — when the surface is a Mac window, menu, or settings scene.
- `xcode-loop` — build, run, and screenshot the actual surface.

Fallback when a skill is unavailable: name it as unavailable in the
report, review from the diff alone, and mark the verdict provisional.

Review in this order:

1. Read the change's design intent from its artifacts.
2. Review the diff for HIG violations: non-standard controls where
   standard ones exist, hard-coded colors or type instead of semantic
   styles, missing Dynamic Type or VoiceOver support, the wrong platform
   idiom for the target.
3. Build and run via xcode-loop. Screenshot the changed surface in light
   and dark appearance. If the change ships motion, run it and judge
   duration and interruptibility — a still frame cannot show either.
4. Verdict: pass, or each blocker named with the HIG section or skill
   reference it violates. The verdict follows the evidence.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/workflows/payload/levels/advanced/apple/agents/apple-design-gate.md
git commit -m "feat(workflows): HIG-grounded apple-design-gate agent"
```

---

### Task 5: buildPlan union composition, guard, and human step

**Files:**
- Modify: `plugins/workflows/scripts/plan.mjs` (composition at lines ~165-171, guard near line ~133, human step near line ~194)
- Modify: `tests/workflows-plan.test.ts` (extend)

**Interfaces:**
- Consumes: `detection.apple` (Task 1), `makeDetection`/`APPLE` (Task 2), payload subtree (Tasks 3-4), existing `classify`, `subdirs`.
- Produces: plan schema/agent lists include apple names when `level === 'advanced' && detection.apple.app`; the mcpbridge human step. Task 7's SKILL.md prose describes exactly this behavior.

**Required skills:** none (plain code).

- [ ] **Step 1: Write the failing tests** (append to `tests/workflows-plan.test.ts`)

```ts
import { cpSync, mkdirSync as mk, mkdtempSync as mkd, rmSync, writeFileSync as wf } from 'node:fs';
import { tmpdir as tmp } from 'node:os';
import { join as j } from 'node:path';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';

const PAYLOAD = j(import.meta.dir, '..', 'plugins', 'workflows', 'payload');

describe('advanced apple content composition', () => {
	test('advanced + app ships app-release and apple-design-gate', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'advanced' });
		expect(plan.schemas.copy).toContain('app-release');
		expect(plan.agents.copy).toContain('apple-design-gate.md');
	});

	test('advanced without app signals ships neither', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'advanced' });
		expect(plan.schemas.copy).not.toContain('app-release');
		expect(plan.agents.copy).not.toContain('apple-design-gate.md');
	});

	test('standard + app ships neither (advanced only)', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'standard' });
		expect(plan.schemas.copy).not.toContain('app-release');
	});

	test('a user-owned app-release schema collides, never silently replaced (I2)', () => {
		const plan = buildPlan(
			makeDetection({
				apple: APPLE,
				openspec: { present: true, hasSpecs: false, hasChanges: false, schemas: ['app-release'], schemaHashes: { 'app-release': 'abc' }, configPath: null },
			}),
			{ level: 'advanced' },
		);
		expect(plan.schemas.collide).toContain('app-release');
		expect(plan.schemas.copy).not.toContain('app-release');
	});

	test('missing apple subtree throws instead of shipping a silently thinner plan', () => {
		const stripped = mkd(j(tmp(), 'wf-payload-'));
		cpSync(PAYLOAD, stripped, { recursive: true });
		rmSync(j(stripped, 'levels', 'advanced', 'apple'), { recursive: true });
		expect(() => buildPlan(makeDetection({ apple: APPLE }), { level: 'advanced', payloadRoot: stripped })).toThrow(/apple/);
	});
});

describe('mcpbridge human step', () => {
	const stepText = (plan: { humanSteps: string[] }) => plan.humanSteps.join('\n');

	test('app repo without an xcode MCP server gets the step', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'minimal' });
		expect(stepText(plan)).toContain('xcrun mcpbridge');
	});

	test('already-configured xcode server suppresses it', () => {
		const plan = buildPlan(makeDetection({ apple: { ...APPLE, xcodeMcpConfigured: true } }), { level: 'minimal' });
		expect(stepText(plan)).not.toContain('mcpbridge');
	});

	test('tier-1-only repos do not get it', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'minimal' });
		expect(stepText(plan)).not.toContain('mcpbridge');
	});
});

describe('integration: detect → buildPlan on a real fixture (spec §12 e2e stand-in)', () => {
	test('an Apple app monorepo plans the full apple surface', () => {
		const root = mkd(j(tmp(), 'wf-fixture-'));
		mk(j(root, 'ios', 'App.xcodeproj'), { recursive: true });
		wf(j(root, 'Package.swift'), '// swift-tools-version:6.0');
		const d = detect(root, { run: () => null });
		const plan = buildPlan(d, { level: 'advanced' });
		expect(plan.apple).toEqual({ app: true, swift: true });
		expect(plan.plugins.install).toContain('apple-studio@agent-tools');
		expect(plan.schemas.copy).toContain('app-release');
		expect(plan.agents.copy).toContain('apple-design-gate.md');
		expect(plan.humanSteps.join('\n')).toContain('xcrun mcpbridge');
	});
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bun test tests/workflows-plan.test.ts`
Expected: the new describe blocks FAIL; Task 2's tests still pass.

- [ ] **Step 3: Implement in plan.mjs**

After the `levelDir` existence guard (line ~135):

```js
	// Ruling 48's lesson applies here too: a payload missing content the detection says
	// this plan must ship is a defect, and the empty-but-plausible plan it would produce
	// is the exact failure the level guard above exists to prevent.
	const appleActive = level === 'advanced' && Boolean(detection.apple?.app);
	const appleDir = join(levelDir, 'apple');
	if (appleActive && !existsSync(appleDir)) {
		throw new Error(
			`payloadRoot ${JSON.stringify(payloadRoot)} has no levels/advanced/apple directory — refusing to build a plan that omits the Apple content it claims to ship.`,
		);
	}
```

Replace the `shippedSchemas` line (~165):

```js
	const shippedSchemas = [
		...subdirs(join(levelDir, 'openspec', 'schemas')),
		...(appleActive ? subdirs(join(appleDir, 'openspec', 'schemas')) : []),
	].sort();
```

Replace the `shippedAgents` block (~168-170):

```js
	const agentFilesIn = (dir) =>
		existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')) : [];
	const shippedAgents = [
		...agentFilesIn(join(levelDir, 'agents')),
		...(appleActive ? agentFilesIn(join(appleDir, 'agents')) : []),
	].sort();
```

In the human-steps block, after the `/impeccable init` push (~line 196):

```js
	if (detection.apple?.app && !detection.apple.xcodeMcpConfigured) {
		humanSteps.push(
			'Enable "Allow external agents to use Xcode tools" in Xcode → Settings → Intelligence, then run ' +
				'`claude mcp add --transport stdio xcode -- xcrun mcpbridge`. Verification then drives Xcode ' +
				'directly; without it, xcode-loop falls back to headless xcodebuild.',
		);
	}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bun test tests/workflows-plan.test.ts && bun test tests/workflows-detect.test.ts`
Expected: PASS, all tests.

- [ ] **Step 5: Full gates and commit**

```bash
bun test && bun run audit
git add plugins/workflows/scripts/plan.mjs tests/workflows-plan.test.ts
git commit -m "feat(workflows): compose apple content at advanced, guard the subtree, add the mcpbridge human step"
```

---

### Task 6: ROUTING.md entry and verification-template delegation

**Files:**
- Modify: `plugins/workflows/payload/levels/advanced/openspec/ROUTING.md`
- Modify: `plugins/workflows/payload/levels/advanced/openspec/schemas/feature/templates/verification.md:19-28` (Surface Quality section)
- Modify: `plugins/workflows/payload/levels/advanced/openspec/schemas/upgrade/templates/verification.md:3-5` (Verification Suite section)

**Interfaces:**
- Consumes: schema name `app-release` and its guardrails (Task 3, spec §5.3).
- Produces: router text Task 8's chains.md and Task 9's router-card must agree with verbatim.

**Required skills:** `configuring-openspec`, `improving-prompts`.

- [ ] **Step 1: Add the router entry**

In ROUTING.md's decision tree, insert as item 2 (after hotfix — a store-live emergency is still hotfix first) and renumber the rest:

```markdown
2. Shipping a build to TestFlight or the App Store → **app-release**
   (installed only in Apple-native app repos; if the schema is absent, this entry does not apply)
```

Add to Prompt signals:

```markdown
- "cut a release / submit to the App Store / push to TestFlight" → app-release
```

Add to Escalation and guardrails:

```markdown
- **app-release**: a code defect discovered mid-release stops the release and
  spawns a bugfix change — the release chain never absorbs code fixes. An
  urgent fix already live in the store routes its code work through hotfix;
  the expedited-review submission still goes through app-release, referencing it.
```

- [ ] **Step 2: Reword the two verification templates**

`feature/templates/verification.md` — replace the Surface Quality comment's first paragraph:

```markdown
<!-- Anti-slop pre-flight against RENDERED state, using the checks for the
stack this change touches as recorded in TOOLS.md — browser tool for web
surfaces, simulator screenshots via xcode-loop for Apple surfaces. States
from the specs - loading, empty, error, keyboard-only - confirmed rendering
correctly. -->
```

`upgrade/templates/verification.md` — replace the Verification Suite comment:

```markdown
<!-- Command, exit code, counts, pasted verbatim. Run the checks for the
stack this change touches, as recorded in TOOLS.md. -->
```

- [ ] **Step 3: Verify no other template names a stack-specific tool**

Run: `grep -rn "browser\|playwright\|xcodebuild\|npm run" plugins/workflows/payload/levels/advanced/openspec/schemas/*/templates/`
Expected: only the feature/verification.md line edited above (now reading "browser tool for web surfaces"). Any other hit: apply the same TOOLS.md delegation treatment.

- [ ] **Step 4: Commit**

```bash
git add plugins/workflows/payload/levels/advanced/openspec/
git commit -m "feat(workflows): route app-release; verification delegates stack checks to TOOLS.md"
```

---

### Task 7: Setup SKILL.md updates

**Files:**
- Modify: `plugins/workflows/skills/setup/SKILL.md` (lines ~35, ~66-75, ~112, ~162-188, ~189-190, ~360-370)

**Interfaces:**
- Consumes: plan fields `apple.app`/`apple.swift` (Task 2), the copy mechanics for `payload/levels/advanced/apple/` (Tasks 3-5), the human step text (Task 5 — the SKILL.md prose must not contradict the exact step `buildPlan` emits).
- Produces: nothing downstream.

**Required skills:** `authoring-skills`.

- [ ] **Step 1: Make the six edits**

1. Line ~35 ("whether this repo is a web project"): extend to "whether this repo is a web or Apple-native project (and which Apple tier — a bare `Package.swift` is the plugin layer only; app signals ship workflow content at `advanced`)".
2. Interview section (~66-75): after the web-leaning sentence add: "A repo detected as an Apple-native app: say when recommending that the Apple workflow content (`app-release`, the Apple design gate) ships only at `advanced`."
3. Plan rendering (~112): "the detected web answer" → "the detected web and Apple answers (both tiers)".
4. Apply step 2 (Schemas, ~162): after the existing copy block add: "When the plan's `apple.app` is true and the level is `advanced`, repeat the copy from `${CLAUDE_PLUGIN_ROOT}/payload/levels/advanced/apple/openspec/schemas` into the same destination, with the same `overwrite` rules — the plan's name lists already include the apple names, so nothing else changes."
5. Apply step 3 (Agents, ~180): the same sentence for `${CLAUDE_PLUGIN_ROOT}/payload/levels/advanced/apple/agents` into `$REPO/.claude/agents`.
6. Step 4 (TOOLS.md, ~189): append: "In an Apple-native repository, confirm the build, test, and simulator commands land in TOOLS.md — the verification templates delegate to it."
7. Human steps (~360): add the bullet: "**Connect Xcode's MCP bridge** on an Apple-native app repo (when the plan lists it): enable 'Allow external agents to use Xcode tools' in Xcode → Settings → Intelligence, then `claude mcp add --transport stdio xcode -- xcrun mcpbridge`. The toggle is a user act; nothing here can flip it."

- [ ] **Step 2: Verify prose against code**

Run: `grep -n "mcpbridge" plugins/workflows/scripts/plan.mjs plugins/workflows/skills/setup/SKILL.md`
Expected: the command string `claude mcp add --transport stdio xcode -- xcrun mcpbridge` is byte-identical in both.

- [ ] **Step 3: Commit**

```bash
git add plugins/workflows/skills/setup/SKILL.md
git commit -m "docs(workflows): setup skill covers Apple detection, copy, TOOLS.md, and mcpbridge"
```

---

### Task 8: choosing-a-workflow, README, marketplace, version bump

**Files:**
- Modify: `plugins/workflows/skills/choosing-a-workflow/references/chains.md`
- Modify: `plugins/workflows/skills/choosing-a-workflow/evals/cases.md`
- Modify: `plugins/workflows/skills/choosing-a-workflow/evals/triggers.md`
- Modify: `plugins/workflows/README.md` (levels table ~line 32-36; learn line ~113-115)
- Modify: `plugins/workflows/.claude-plugin/plugin.json` (version + description)
- Modify: `.claude-plugin/marketplace.json` (workflows description)

**Interfaces:**
- Consumes: chain `release-scope → preflight → tasks → post-release` (Task 3), router text (Task 6).
- Produces: nothing downstream.

**Required skills:** `authoring-skills` (chains/evals), `authoring-plugins` (plugin.json/README), `maintaining-plugin-marketplaces` (marketplace.json).

- [ ] **Step 1: chains.md**

Title: "The twelve chains" → "The twelve chains (thirteen in Apple-native app repos)". Contents list gains `- [`advanced` — Apple app repos: app-release](#advanced--apple-app-repos)`. Add the section, following the established format (chain line, artifact table, gate and hatch lines):

```markdown
## `advanced` — Apple app repos

### `app-release` — 4 artifacts, installed only where app signals were detected

`release-scope → preflight → tasks → post-release`, then `apply` (after `tasks`).

| Artifact | `requires` | Carries |
|---|---|---|
| `release-scope` | — | Version/build decision, contents since last release, rollout intent, go/no-go owner |
| `preflight` | `release-scope` | Store checklist with named evidence per item — signing, privacy, metadata, review notes |
| `tasks` | `preflight` | Archive → upload → TestFlight → submit, each step with its observable signal |
| `post-release` | `tasks` | Monitoring thresholds that pause the rollout; linked follow-ups. Completed before archiving |

**Gate:** a code defect discovered mid-release stops the release and spawns a
bugfix change; the chain never absorbs code fixes.
**Hatch:** an urgent fix already live in the store routes code work through
`hotfix`; the expedited-review submission still goes through this chain.
Skills: `apple-studio:app-release`, `apple-studio:xcode-loop` (fallback:
follow the templates manually).
```

- [ ] **Step 2: evals**

`evals/cases.md`, appended in the established case format:

```markdown
## Case N — Apple release routing (repo at `advanced`, Apple-native)

**Prompt:** The build's ready — get 1.4.0 out to TestFlight and then the App Store.

**Assertions:**

1. Routes to `app-release`, not `feature` and not ad hoc release steps. *[baseline: starts archiving or writes a release checklist inline]*
2. Names the chain as `release-scope → preflight → tasks → post-release`.
3. Returns a filled-in chat command — `/opsx:new <the work>, using app-release` — with the schema named.
4. Names the guardrail: a code defect discovered mid-release spawns a bugfix change; the release chain never absorbs code fixes.
5. Does **not** create the change, archive a build, or touch App Store Connect.
```

(Replace N with the next case number.) `evals/triggers.md`: read its format first, then add one trigger row for release-shipping prompts pointing at `app-release`.

- [ ] **Step 3: README, plugin.json, marketplace.json**

- README levels table advanced row: `| \`advanced\` | 8 | 10 artifacts | yes |` → `| \`advanced\` | 8 (9 in Apple-native app repos) | 10 artifacts | yes |`.
- README "What setup does" list item 1: append "including whether the repo is Apple-native (two tiers: any Swift signal adds the apple-studio plugin layer; app signals add the `app-release` schema and Apple design gate at `advanced`)".
- README learn paragraph (~113): "thirteen lessons" → "fourteen lessons"; "all twelve workflows" → "all twelve core workflows plus the Apple-only thirteenth".
- `plugin.json`: version `0.6.0` → `0.7.0`; in the description, after "among the twelve it installs", insert ", detects Apple-native repos and adds the apple-studio layer plus an app-release workflow at the advanced level".
- `marketplace.json` workflows entry: make its description text byte-identical to the new plugin.json description (`bun test` pins registration consistency; check whether it also pins description equality by running it).

- [ ] **Step 4: Gates and commit**

```bash
bun test && bun run audit && bun run audit --since HEAD~6
git add plugins/workflows/ .claude-plugin/marketplace.json
git commit -m "docs(workflows): route, document, and version the Apple-native surface"
```

Expected: `audit --since` names `workflows` as changed-and-bumped. If it names any other unbumped plugin, stop and investigate.

---

### Task 9: Learn lesson 0014 and reference cards

**Files:**
- Create: `plugins/workflows/learn/lessons/0014-apple-native-repos.html`
- Modify: `plugins/workflows/learn/index.html` (lesson tables, "thirteen lessons" phrasing)
- Modify: `plugins/workflows/learn/reference/workflow-atlas.html` (ninth schema card)
- Modify: `plugins/workflows/learn/reference/router-card.html` (routing line)

**Interfaces:**
- Consumes: detection tiers (Task 1), chain and guardrails (Tasks 3, 6, 8 — keep wording consistent with chains.md).
- Produces: nothing downstream.

**Required skills:** none of the authoring set (static HTML content); follow the lesson conventions below.

- [ ] **Step 1: Read the format authorities**

Read `lessons/0009-standard-end-to-end.html` end to end for the markup shell (head, nav, section structure, quiz component, source-citation links written as `../../` relative paths — the build rewrites them to blob URLs). Read `learn/NOTES.md` for authoring conventions. Public-site check: the lesson quotes payload source; confirm nothing sensitive (schema and gate content is already public-by-design here).

- [ ] **Step 2: Write the lesson**

`0014-apple-native-repos.html`, mirroring 0009's shell. Content sections:

1. **Two tiers of detection** — what trips each tier (`Package.swift` vs `.xcodeproj`/`.xcworkspace`/Tuist/XcodeGen, root or one deep); tier 1 adds the `apple-studio` plugin layer at every level; tier 2 adds workflow content at `advanced` only. Cite `../../payload/base/settings.base.apple.json`.
2. **The app-release chain** — walk `release-scope → preflight → tasks → post-release` the way 0009 walks its chains: what each artifact carries, the evidence-per-item rule, the code-defect guardrail. Cite `../../payload/levels/advanced/apple/openspec/schemas/app-release/schema.yaml`.
3. **Connecting Xcode** — the mcpbridge human step: the toggle, the `claude mcp add` one-liner, and the headless fallback.

Two quizzes (check-answers rule: every choice the SAME word count, within 4 characters of each other, exactly one `data-correct`):

Quiz 1 prompt: "A repo has only a root Package.swift. What does setup add for it?"
- `the plugin layer` (data-correct)
- `the app schemas`
- `the gate agents`

Quiz 2 prompt: "Which level installs the app-release schema when app signals fire?"
- `advanced` (data-correct)
- `standard`
- `everyone`

(All three are one word and 8 characters — the check-answers rule; `everyone` reads as "every level". `minimal` is excluded deliberately: at 7 characters it passes the 4-char spread, but two plausible-sounding wrong answers beat one plausible and one obviously-wrong.)

- [ ] **Step 3: Wire index.html and the cards**

- `index.html`: add the 0014 row after the 0013 row, matching the table-row markup at lines 215-225; update "thirteen lessons" copy to "fourteen lessons" wherever index.html states a count.
- `workflow-atlas.html`: add an `app-release · 4` card mirroring the `hotfix · 3` card structure (line ~407), with the qualifier line "Apple app repos · advanced only" and the four artifacts.
- `router-card.html`: add the routing line using the exact ROUTING.md wording from Task 6.

- [ ] **Step 4: Run the authoring checks**

```bash
cd plugins/workflows/learn
node assets/check-structure.mjs
node assets/check-answers.mjs lessons/0014-apple-native-repos.html
```

Expected: both exit 0 ("nesting well-formed", no quiz violations). NOTE: no build/deploy script exists in this repo (Global Constraints drift note) — do not create one; the citation-link contract is honored by using `../../` relative paths that resolve from `lessons/` in a checkout. Verify each cited path exists: `ls ../../payload/levels/advanced/apple/openspec/schemas/app-release/schema.yaml`.

- [ ] **Step 5: Commit**

```bash
git add plugins/workflows/learn/
git commit -m "docs(workflows): learn lesson 0014 covers Apple-native repos"
```

---

### Task 10: apple-studio — link sweep, README, version bump

**Files:**
- Modify: ~120 files under `plugins/apple-studio/` (every file containing a page-form `/documentation/` link)
- Modify: `plugins/apple-studio/README.md` (Install section)
- Modify: `plugins/apple-studio/.claude-plugin/plugin.json` (version)
- Create: `tests/apple-doc-links.test.ts`
- Create (scratchpad, throwaway): `sweep-links.mjs`, `verify-links.sh`

**Interfaces:**
- Consumes: nothing from other tasks (independent; may run in parallel with Tasks 1-9).
- Produces: the link-form invariant the regression test pins.

**Required skills:** `authoring-plugins` (version/README). FIRST ACTION: read `authoring/apple-studio/CONVENTIONS.md` end to end (repo CLAUDE.md requirement; `.claude/rules/apple-studio.md` loads with these files).

- [ ] **Step 1: Write the failing regression test**

```ts
// tests/apple-doc-links.test.ts
import { expect, test } from 'bun:test';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', 'plugins', 'apple-studio');
const URL_RE = /https:\/\/developer\.apple\.com\/documentation\/[^\s"'<>\]]+/g;

/** Trim characters that belong to the prose, not the URL: trailing .,;: and
 *  unbalanced closing parens (symbol URLs contain balanced ones). */
function trimUrl(raw: string): string {
	let url = raw;
	for (;;) {
		if (/[.,;:]$/.test(url) && !url.endsWith('.md')) { url = url.slice(0, -1); continue; }
		if (url.endsWith(')')) {
			const open = (url.match(/\(/g) ?? []).length;
			const close = (url.match(/\)/g) ?? []).length;
			if (close > open) { url = url.slice(0, -1); continue; }
		}
		return url;
	}
}

function* walk(dir: string): Generator<string> {
	for (const name of readdirSync(dir)) {
		const p = join(dir, name);
		if (statSync(p).isDirectory()) yield* walk(p);
		else if (/\.(md|json|html)$/.test(name)) yield p;
	}
}

test('every page-form Apple documentation link in apple-studio ends in .md', () => {
	const offenders: string[] = [];
	for (const file of walk(ROOT)) {
		for (const m of readFileSync(file, 'utf8').matchAll(URL_RE)) {
			const url = trimUrl(m[0]);
			if (url.includes('#')) continue;
			if (url.endsWith('.md') || url.endsWith('.json')) continue;
			offenders.push(`${file}: ${url}`);
		}
	}
	expect(offenders).toEqual([]);
});
```

Note the regex deliberately does NOT match `/tutorials/data/` URLs (different path segment), so the provenance citations are structurally out of scope.

- [ ] **Step 2: Run it to verify it fails**

Run: `bun test tests/apple-doc-links.test.ts`
Expected: FAIL with ~1,000+ offenders listed.

- [ ] **Step 3: Write and run the sweep script** (in the session scratchpad, never committed)

```js
// sweep-links.mjs — run: node sweep-links.mjs <repo-root>
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(process.argv[2], 'plugins', 'apple-studio');
const URL_RE = /https:\/\/developer\.apple\.com\/documentation\/[^\s"'<>\]]+/g;

function trimUrl(raw) {
	let url = raw;
	for (;;) {
		if (/[.,;:]$/.test(url) && !url.endsWith('.md')) { url = url.slice(0, -1); continue; }
		if (url.endsWith(')')) {
			const open = (url.match(/\(/g) ?? []).length;
			const close = (url.match(/\)/g) ?? []).length;
			if (close > open) { url = url.slice(0, -1); continue; }
		}
		return url;
	}
}

function* walk(dir) {
	for (const name of readdirSync(dir)) {
		const p = join(dir, name);
		if (statSync(p).isDirectory()) yield* walk(p);
		else if (/\.(md|json|html)$/.test(name)) yield p;
	}
}

const rewritten = new Set();
for (const file of walk(ROOT)) {
	const text = readFileSync(file, 'utf8');
	const out = text.replace(URL_RE, (raw) => {
		const url = trimUrl(raw);
		const tail = raw.slice(url.length);
		if (url.includes('#') || url.endsWith('.md') || url.endsWith('.json')) return raw;
		rewritten.add(`${url}.md`);
		return `${url}.md${tail}`;
	});
	if (out !== text) writeFileSync(file, out);
}
writeFileSync('rewritten-urls.txt', [...rewritten].sort().join('\n'));
console.log(`${rewritten.size} unique URLs rewritten`);
```

Run it, then verify EVERY rewritten URL resolves as markdown (spec §9: no sampling):

```bash
node sweep-links.mjs /path/to/repo
xargs -P 8 -I{} sh -c 'ct=$(curl -s -o /dev/null -w "%{content_type}" -L "{}"); case "$ct" in text/markdown*) ;; *) echo "FAIL $ct {}";; esac' < rewritten-urls.txt | tee failures.txt
test ! -s failures.txt && echo ALL RESOLVE
```

Expected: `ALL RESOLVE`, ~1,045 unique URLs. ANY failure: revert that specific URL's rewrite (it stays page-form) and record it in the commit message.

- [ ] **Step 4: Run the regression test to verify it passes**

Run: `bun test tests/apple-doc-links.test.ts`
Expected: PASS.

- [ ] **Step 5: README and version**

`plugins/apple-studio/README.md` Install section, after the local-testing block:

```markdown
Or install inside Xcode (26+): Xcode → Settings → Intelligence → Plug-ins →
Add Plug-in → Add from URL, using this repository's URL, then select the
apple-studio components. Configuration for agents launched inside Xcode
lives in `~/Library/Developer/Xcode/CodingAssistant/` and is machine-global.

To let a terminal session drive Xcode itself, enable "Allow external agents
to use Xcode tools" in Xcode → Settings → Intelligence, then:

    claude mcp add --transport stdio xcode -- xcrun mcpbridge

`xcode-loop` prefers the bridge when connected and falls back to headless
`xcodebuild` — see its `references/mcpbridge.md`.
```

`plugins/apple-studio/.claude-plugin/plugin.json`: `"version": "0.9.0"` → `"0.9.1"`.

- [ ] **Step 6: Gates and commit**

```bash
bun test && bun run audit
git add plugins/apple-studio/ tests/apple-doc-links.test.ts
git commit -m "docs(apple-studio): Apple doc links to .md form; Xcode install paths; v0.9.1"
```

---

### Task 11: Final verification

**Files:** none created; read-only checks.

- [ ] **Step 1: Full gates**

```bash
bun test
bun run audit
claude plugin validate . 
bun run audit --since <branch-base-ref>
```

Expected: tests pass; audit exits 0; validate passes; `--since` names exactly `workflows` and `apple-studio` as changed, both bumped.

- [ ] **Step 2: Spec walk**

Open the spec and check each numbered section against the diff: §3→Task 1, §4→Task 2, §5→Tasks 3-5, §6→Tasks 6-7, §7→Tasks 2+5, §8→Tasks 5+7+10, §9→Task 10, §10→Task 9, §11→Tasks 7-8, §12→Tasks 1/5/10, §13→Tasks 8+10, §14→every task's Required skills line, §15 untouched, §16 invariants: confirm no diff under any `openspec/specs/` or `openspec/changes/` path and no write to machine-global paths.

- [ ] **Step 3: Report**

Report deviations discovered during execution (expected ones are pre-recorded in Global Constraints: no e2e suite, no learn build script, no `.agents/skills` sync). Then use `superpowers:finishing-a-development-branch`.
