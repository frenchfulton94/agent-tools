# Phase 8 Implementation Plan — apple-studio into the agent-tools catalog

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the apple-studio plugin into the agent-tools marketplace so it
ships from there alone, and archive the authoring repository.

**Architecture:** Three sequenced changes, each ending with a green catalog. The
colliding `apple-design` skill in `design-engineering` is renamed first, because
importing before the rename creates a duplicate skill name the test suite fails
on. The plugin and its authoring tools then move into agent-tools as a plain
copy. The authoring repository is stripped to its verification record and
archived.

**Tech Stack:** Bun (test runner, audit script), the `claude` CLI (plugin
validate, `--plugin-dir`), Python 3 stdlib (the apple-studio pipeline), git.

**Spec:** `docs/specs/2026-09-12-phase8-catalog-migration-design.md`

## Global Constraints

Copied verbatim from the spec. Every task's requirements implicitly include
this section.

- **Two repositories.** `~/Projects/agent-tools` is "the catalog";
  `~/Projects/apple-studio` is "the authoring repo". Every path in this plan is
  relative to one of those two roots and says which.
- **Version lives in `plugin.json` only.** Marketplace entries carry no version
  field. Never add one.
- **`plugins/` is the install unit.** Nothing that an installer does not need
  goes inside `plugins/apple-studio/`.
- **The plugin ships at `0.9.0`**, tagged `apple-studio-v0.9.0` in the catalog.
- **`bun test` and `bun run audit` are the gates.** Both must pass at the end of
  every task that touches the catalog.
- **`bun run audit:strict` is not a gate.** It already exits 1 on the catalog as
  it stands — 0 errors, 12 warnings. Record its delta; do not try to make it
  pass.
- **Base branch:** `phase-8-apple-studio`, branched from `main` at `cb24f86`.
  It is already created — do not create it again. The catalog has **9 plugins**
  on this base; `add-dokploy-plugin` carries a tenth that is not merged and is
  not part of this phase.
- **Baseline, measured 2026-09-12 on this base:** `bun test` → 74 pass, 0 fail.
  `bun run audit` → exit 0. `bun run audit:strict` → 0 errors, 12 warnings.
- **The authoring repo's tree stays clean.** `~/Projects/StudioFixture` is the
  eval fixture; leave its git tree clean after any run.
- **Commits:** `Phase 8 Task N: <summary>` in the authoring repo. In the catalog,
  the same per-commit convention with a descriptive pull request title.

---

### Task 1: Rename `apple-design` to `fluid-interfaces` across the catalog

The catalog forbids two skills sharing a name
(`tests/marketplace-integrity.test.ts:147-158`). This task removes the collision
before anything is imported. It ends with the catalog green and no skill named
`apple-design` anywhere in it.

**Repo:** the catalog, `~/Projects/agent-tools`.

**Files:**
- Rename: `plugins/design-engineering/skills/apple-design/` → `plugins/design-engineering/skills/fluid-interfaces/`
- Modify: `plugins/design-engineering/skills/fluid-interfaces/SKILL.md:2`
- Modify: `plugins/design-engineering/README.md:33,47,113`
- Modify: `plugins/design-engineering/NOTICE.md:17,32`
- Modify: `plugins/design-engineering/skills/design-engineering/SKILL.md:3,118`
- Modify: `plugins/design-engineering/skills/design-engineering/evals/routing.md:71`
- Modify: `plugins/design-engineering/skills/design-engineering/evals/cases.md:44`
- Modify: `plugins/design-engineering/skills/animating-interfaces/references/recipes.md:424`
- Modify: 9 files under `plugins/workflows/payload/levels/` (10 lines)
- Modify: `plugins/security/skills/reviewing-code-security/evals/manifest.json:22`
- Modify: `README.md:22`
- Modify: `plugins/design-engineering/.claude-plugin/plugin.json`, `plugins/workflows/.claude-plugin/plugin.json`, `plugins/security/.claude-plugin/plugin.json` (version)

**Interfaces:**
- Produces: the skill name `fluid-interfaces`, which Task 3 adds a scope clause
  to and which Task 2's `apple-animations` clause points at.

- [ ] **Step 1: Confirm the baseline is green before changing anything**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
bun run audit >/dev/null 2>&1; echo "audit exit=$?"
```

Expected: `74 pass`, `0 fail`, and `audit exit=0`. If either differs, stop and
report — the baseline in the Global Constraints is wrong and the plan needs
revising before any edit lands.

- [ ] **Step 2: Rename the directory with git so history follows**

```bash
cd ~/Projects/agent-tools
git mv plugins/design-engineering/skills/apple-design \
       plugins/design-engineering/skills/fluid-interfaces
```

- [ ] **Step 3: Run the test suite to watch it fail for the right reason**

```bash
bun test 2>&1 | grep -E "^\(fail\)|fail\]" | head
```

Expected: failures naming the frontmatter/directory mismatch
(`tests/marketplace-integrity.test.ts:138-143`) and the README skills column.
This is the failing state the rest of the task fixes. If the suite still passes,
the `git mv` did not take effect — stop and check.

- [ ] **Step 4: Update the frontmatter name**

`plugins/design-engineering/skills/fluid-interfaces/SKILL.md:2` currently reads
`name: apple-design`. Change it to:

```yaml
name: fluid-interfaces
```

Leave the `description` alone for now — Task 3 rewrites its closing clause.

- [ ] **Step 5: Update the seven other design-engineering references**

Do **not** run a blanket find-and-replace. `NOTICE.md:32` is a two-column
mapping from the upstream skill name to this catalog's name, and the left
column must keep saying `apple-design`:

```markdown
| `apple-design` | `fluid-interfaces` |
```

One more trap: **all but one occurrence is wrapped in backticks.**
`skills/design-engineering/SKILL.md:3` is the frontmatter description, and its
closing clause reads `use apple-design.` bare. A backtick-scoped replace skips
it and leaves a description pointing at a skill that no longer exists. It needs
its own line, below.

```bash
cd ~/Projects/agent-tools/plugins/design-engineering
sed -i '' 's/`apple-design`/`fluid-interfaces`/g' \
  README.md \
  skills/design-engineering/SKILL.md \
  skills/design-engineering/evals/routing.md \
  skills/design-engineering/evals/cases.md \
  skills/animating-interfaces/references/recipes.md
sed -i '' '3s/use apple-design\./use fluid-interfaces./' skills/design-engineering/SKILL.md
sed -i '' '17s/`apple-design`/`fluid-interfaces`/' NOTICE.md
sed -i '' '32s/| `apple-design` | `apple-design` |/| `apple-design` | `fluid-interfaces` |/' NOTICE.md
```

Confirm the bare one took:

```bash
sed -n '3p' skills/design-engineering/SKILL.md | grep -o "use fluid-interfaces\."
```

Expected: `use fluid-interfaces.` — an empty result means the line number moved
and the substitution missed.

- [ ] **Step 6: Verify NOTICE.md kept its upstream column**

```bash
sed -n '30,33p' ~/Projects/agent-tools/plugins/design-engineering/NOTICE.md
```

Expected, exactly:

```markdown
| `emil-design-eng` | `design-engineering` |
| `animation-vocabulary` | `animation-vocabulary` |
| `apple-design` | `fluid-interfaces` |
```

If the left column says `fluid-interfaces`, the blanket sed ran over line 32 —
revert that line and redo step 5.

- [ ] **Step 7: Update the ten `workflows` payload references**

```bash
cd ~/Projects/agent-tools/plugins/workflows/payload/levels
sed -i '' 's/apple-design/fluid-interfaces/g' \
  advanced/agents/design-gate.md \
  advanced/openspec/README.md \
  advanced/openspec/schemas/feature/schema.yaml \
  minimal/agents/bridge-design-gate.md \
  minimal/openspec/CLAUDE.md.fragment.md \
  minimal/openspec/schemas/mattpocock-bridge/schema.yaml \
  standard/agents/craft-design-gate.md \
  standard/openspec/schemas/craft-driven/schema.yaml \
  standard/openspec/schemas/surface-driven/schema.yaml
```

These are OpenSpec schemas and gate agents that other projects install. Nothing
in the catalog's tests reads schema YAML, so a missed one is silent — step 10
catches it.

- [ ] **Step 8: Update the security eval roster**

`plugins/security/skills/reviewing-code-security/evals/manifest.json:22` lists
`"apple-design"` inside `acknowledgedOmissions`, which is an alphabetically
sorted array. Replace it and re-sort: `"fluid-interfaces"` sorts after
`"feature-sliced-design"` and before `"hardening-dokploy"`.

`tests/security-evals.test.ts:51-53` fails on an omission naming a skill that no
longer ships, so leaving `"apple-design"` here breaks the suite.

This file is **tab**-indented, unlike the manifests — which is why `indent='\t'`
appears here and `indent=2` in step 11. Getting it backwards reformats the whole
file.

```bash
cd ~/Projects/agent-tools
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('plugins/security/skills/reviewing-code-security/evals/manifest.json')
m = json.loads(p.read_text())
m['acknowledgedOmissions'] = sorted(
    n for n in m['acknowledgedOmissions'] if n != 'apple-design'
) + ['fluid-interfaces']
m['acknowledgedOmissions'].sort()
p.write_text(json.dumps(m, indent='\t') + '\n')
PY
```

- [ ] **Step 9: Update the root README skills column**

`README.md:22` is the design-engineering row. Its skills cell lists seven names
in backticks, alphabetically. Replace `` `apple-design` `` with
`` `fluid-interfaces` `` and re-sort the cell so it reads:

```
`animating-interfaces` `animation-vocabulary` `design-engineering` `finding-animation-opportunities` `fluid-interfaces` `improving-animations` `reviewing-animations`
```

The row's "For" column ends "plus the judgement and the Apple fluid-interface
principles underneath it" — that prose stays accurate and needs no change.

- [ ] **Step 10: Confirm no reference survives**

```bash
cd ~/Projects/agent-tools
grep -rn "apple-design" --include="*.md" --include="*.json" --include="*.yaml" --include="*.ts" . | grep -v "^./.git/"
```

Expected: exactly one hit — `plugins/design-engineering/NOTICE.md:32`, the
upstream column of the name-mapping table. Any other hit is a missed reference;
fix it before continuing.

- [ ] **Step 11: Bump the three plugin versions**

Three plugins changed, so three versions move. In `plugin.json` only — the
marketplace entries carry no version field.

`plugin.json` files in this catalog are indented with **two spaces** and end
with a newline. Preserve both, or the diff buries one changed line under a
whole-file reformat.

```bash
cd ~/Projects/agent-tools
for p in design-engineering workflows security; do
  python3 - "$p" <<'PYEOF'
import json, pathlib, sys
p = pathlib.Path(f'plugins/{sys.argv[1]}/.claude-plugin/plugin.json')
m = json.loads(p.read_text())
major, minor, _ = (int(x) for x in m['version'].split('.'))
m['version'] = f'{major}.{minor + 1}.0'
p.write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
print(sys.argv[1], '->', m['version'])
PYEOF
done
git diff --stat plugins/*/.claude-plugin/plugin.json
```

Expected, exactly:

```
design-engineering -> 0.2.0
workflows -> 0.6.0
security -> 0.4.0
```

`security` was `0.3.1`, so a minor bump correctly drops the patch to `0`. The
`git diff --stat` must show **one insertion and one deletion per file**. More
than that means the indent was not preserved — revert and fix before
continuing.

- [ ] **Step 12: Run the full gate**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
bun run audit >/dev/null 2>&1; echo "audit exit=$?"
claude plugin validate . && echo "validate ok"
```

Expected: `74 pass`, `0 fail`, `audit exit=0`, `validate ok`. The test count
does not change — no plugin was added or removed.

- [ ] **Step 13: Confirm the renamed skill still loads**

```bash
cd ~/Projects/agent-tools
claude --plugin-dir plugins/design-engineering -p "List the names of every skill you can see from this plugin, one per line, and nothing else." --max-turns 2 </dev/null
```

Expected: seven names including `fluid-interfaces` and excluding `apple-design`.

- [ ] **Step 14: Commit**

The branch `phase-8-apple-studio` already exists and is checked out. Do not
create it.

```bash
cd ~/Projects/agent-tools
git add -A
git commit -m "Phase 8 Task 1: rename apple-design to fluid-interfaces

The name collides with apple-studio's HIG skill, which is arriving in the
catalog. This skill translates Apple's fluid-interface principles to the
web and the Svelte stack, so fluid-interfaces is what it covers and the
literal name goes to the plugin doing native Apple platform work.

Skill names live in no user setting, so no install breaks and no renames
entry is needed. design-engineering, workflows, and security all carry
references and all three bump.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Import the plugin and register it

Copies the eleven skills and two hooks into the catalog and does everything
required for the catalog to accept them. Ends green on both gates.

**Repo:** the catalog, `~/Projects/agent-tools`. Source is the authoring repo's
`plugin/` tree.

**Files:**
- Create: `plugins/apple-studio/` (copied tree)
- Create: `plugins/apple-studio/README.md`
- Create: `.gitignore` (the catalog's first)
- Modify: `plugins/apple-studio/.claude-plugin/plugin.json`
- Modify: `plugins/apple-studio/skills/apple-animations/SKILL.md:9-10`
- Modify: `plugins/apple-studio/skills/apple-intelligence/SKILL.md:10-11,50`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md` (new table row)
- Modify: `plugins/security/skills/reviewing-code-security/evals/manifest.json`

**Interfaces:**
- Consumes: `fluid-interfaces` from Task 1 — the rename must be committed first,
  or importing creates the duplicate-name failure.
- Produces: `plugins/apple-studio/` with eleven skills, which Task 3 edits two
  descriptions inside and Task 4's authoring tree documents.

- [ ] **Step 1: Write the catalog's first `.gitignore`**

The catalog has none. Without it the copy in step 2 brings two `.DS_Store`
files that are gitignored in the authoring repo, and Task 4's `corpus/` — 5.9M
of converted book text — would become committable.

Create `~/Projects/agent-tools/.gitignore`:

```gitignore
# Converted book text — copyrighted material, never committed
authoring/*/corpus/

# Source books, if ever copied here
*.epub
*.pdf

# macOS
.DS_Store

# Python bytecode — plugins/unraid-ops/scripts/ generates it on import
__pycache__/
*.pyc

# Pipeline scratch
authoring/*/pipeline/tmp/

# Instruments traces — hundreds of MB of binary bundles, and re-recordable from
# the run sheet beside them. Kept locally next to the report that cites them;
# a report citing a .trace means "on the machine that recorded it".
*.trace/
```

- [ ] **Step 2: Copy the plugin tree**

```bash
cd ~/Projects/agent-tools
mkdir -p plugins/apple-studio
rsync -a --exclude='.DS_Store' ~/Projects/apple-studio/plugin/ plugins/apple-studio/
find plugins/apple-studio -name '.DS_Store' | wc -l
```

Expected: `0`. `rsync` with a trailing slash on the source copies the contents,
not the directory itself.

- [ ] **Step 3: Verify the copy is complete**

```bash
cd ~/Projects/agent-tools
diff -r --exclude='.DS_Store' ~/Projects/apple-studio/plugin plugins/apple-studio && echo "identical"
ls plugins/apple-studio/skills | wc -l
```

Expected: `identical`, and `11`.

- [ ] **Step 4: Fill out `plugin.json`**

`plugins/apple-studio/.claude-plugin/plugin.json` carries four fields. Seven of
the catalog's nine manifests carry eight — `security` and `workflows` are the
existing exceptions. Replace the file with:

Two-space indent and a trailing newline, matching every other manifest here:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "apple-studio",
  "displayName": "Apple Studio",
  "version": "0.9.0",
  "description": "Studio-quality Apple app development: distilled architecture, concurrency, testing, design, release, on-device intelligence, and performance guidance for SwiftUI/Swift 6 apps.",
  "author": {
    "name": "Agent Tools",
    "email": "michael@frenchfultonjr.dev"
  },
  "license": "MIT",
  "keywords": [
    "swift",
    "swiftui",
    "ios",
    "macos",
    "xcode",
    "apple",
    "concurrency",
    "accessibility"
  ]
}
```

`author` changes from the personal name to `Agent Tools`, matching every other
catalog plugin; attribution moves to the plugin README in step 7. `version` is
`0.9.0`, not `0.8.0`, because Task 3 changes a description and users receive a
routing change only when the version moves.

- [ ] **Step 5: See the five citation errors for yourself**

```bash
cd ~/Projects/agent-tools
V=plugins/meta-skills/skills/authoring-skills/scripts/validate_skill.ts
for d in plugins/apple-studio/skills/*/; do bun "$V" "$d"; done 2>&1 | grep '^- ERROR'
```

Expected: five errors, naming `references/animation-taste.md`,
`references/accessibility.md`, `references/primers/foundation-models.md`,
`references/primers/app-intents.md`, and `references/profiling-workflow.md`.

Each of those files exists — in a *different* skill. `validate_skill.ts:175-179`
resolves every `references/…` mention against the skill's own directory, and
`bun run audit` reports validator errors as errors and exits non-zero. So these
block the import until the citation form changes.

- [ ] **Step 6: Rewrite the five cross-skill citations**

The fix is to stop writing a path that reads as local. Naming the file without
the `references/` prefix keeps the pointer useful and takes it out of the
validator's pattern.

In `plugins/apple-studio/skills/apple-animations/SKILL.md`, lines 9-11 currently
read:

```markdown
judgment and belongs to apple-design (`references/animation-taste.md`);
reduce-motion policy to apple-design (`references/accessibility.md`); the
build/run loop to xcode-loop.
```

Replace with:

```markdown
judgment and belongs to apple-design (its `animation-taste` reference);
reduce-motion policy to apple-design (its `accessibility` reference); the
build/run loop to xcode-loop.
```

In `plugins/apple-studio/skills/apple-intelligence/SKILL.md`, lines 10-11
currently read:

```markdown
apple-frameworks (`references/primers/foundation-models.md`,
`references/primers/app-intents.md`). Classical ML — Vision, Speech, Core ML —
```

Replace with:

```markdown
apple-frameworks (its `foundation-models` and `app-intents` primers).
Classical ML — Vision, Speech, Core ML —
```

And line 50 currently reads:

```markdown
  (`references/profiling-workflow.md`); Xcode ships a Foundation Models
```

Replace with:

```markdown
  (apple-performance's `profiling-workflow` reference); Xcode ships a
  Foundation Models
```

- [ ] **Step 7: Re-run the validator to confirm zero errors**

```bash
cd ~/Projects/agent-tools
V=plugins/meta-skills/skills/authoring-skills/scripts/validate_skill.ts
for d in plugins/apple-studio/skills/*/; do bun "$V" "$d"; done 2>&1 | grep -c '^- ERROR'
```

Expected: `0`. Warnings remain and are fine — around 70 of them, recorded in
step 14.

- [ ] **Step 8: Write the plugin README**

The audit checks three things in a plugin README that nothing else catches
(`audit_marketplace.ts:248-270`): the H1 matches the plugin name, the install
command names this plugin, and any `--plugin-dir` path points at the right leaf.

Create `plugins/apple-studio/README.md`:

````markdown
# apple-studio

Studio-quality Apple app development — distilled architecture, concurrency,
testing, design, release, on-device intelligence, and performance guidance for
SwiftUI and Swift 6 apps.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install apple-studio@agent-tools --scope project

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/apple-studio
claude plugin validate plugins/apple-studio --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `swift-architecture` | Skill | App architecture, state and dependency injection in SwiftUI, module boundaries, persistence choice, working safely in shipped code |
| `swift-concurrency` | Skill | Actor isolation, `Sendable`, structured concurrency, cancellation, migrating GCD and Combine to async/await |
| `swift-testing` | Skill | The Swift Testing framework, what to test at each layer, protocol-based doubles without a mocking framework |
| `apple-design` | Skill | Human Interface Guidelines conformance — layout, Dynamic Type, color and materials, navigation and modality, platform idioms, accessibility |
| `apple-animations` | Skill | SwiftUI motion — springs and timing, `Transaction`, phase and keyframe animators, transitions, `matchedGeometryEffect`, scroll effects, shader modifiers |
| `apple-macos` | Skill | Native Mac apps — scene structure, windows and restoration, menus and commands, AppKit interop, sandbox and entitlements |
| `apple-frameworks` | Skill | What Apple ships and what each framework costs — privacy, entitlements, availability, pitfalls — with primers for the sixteen most apps use |
| `apple-intelligence` | Skill | On-device generative AI — Foundation Models sessions, guided generation, tool calling, guardrails and refusals, App Intents |
| `apple-performance` | Skill | Why an app is slow and how to measure it — Instruments templates, `xctrace`, signposts, hangs against hitches, launch time, MetricKit |
| `app-release` | Skill | Signing and provisioning, TestFlight, App Store submission, privacy manifests, version and build numbering, push notifications, Xcode Cloud |
| `xcode-loop` | Skill | Build, test, run, and screenshot from the command line or Xcode's MCP bridge |
| `track_swift_edits.sh` | PostToolUse hook | Records that Swift files were edited this session |
| `stop_gate.sh` | Stop hook | Requires a green build before a session ends, if Swift files were edited |

## The Stop hook

This is the only plugin in the catalog that can block a session from ending.
If Swift files were edited and an Xcode project sits within three parent
directories of the working directory, `stop_gate.sh` builds the first scheme
and blocks on failure, reporting up to five compiler errors.

It fails open everywhere it can: no `jq`, no project, no scheme, or a
destination that does not apply to the project all let the session end
normally. The timeout is 180 seconds.

## Why this is its own plugin

Everything here serves one person: someone writing a native Apple app. That
audience shares nothing with the catalog's web and infrastructure plugins — a
SvelteKit developer installing `frontend` has no use for provisioning profiles,
and someone shipping to the App Store does not want Tailwind guidance arriving
alongside their signing help.

`design-engineering`'s `fluid-interfaces` skill covers the same Apple motion
principles for the web and Svelte. The two are separated by platform, not by
topic.

## Provenance

Authored by Michael French Fulton Jr. Built over eight phases against live
Apple documentation, the shipped SDK's `.swiftinterface` files, and runtime
measurement on Xcode 27 / macOS 27 / Swift 6.4. The distillation pipeline,
design specs, and phase plans live in `authoring/apple-studio/`.

## License

MIT.
````

- [ ] **Step 9: Register the plugin in the marketplace**

Add an entry to `.claude-plugin/marketplace.json`, in the `plugins` array. No
`version` field — the catalog records versions in `plugin.json` only.

Entries are indented four spaces for the brace and six for the keys:

```json
    {
      "name": "apple-studio",
      "source": "./plugins/apple-studio",
      "category": "development",
      "description": "Native Apple app development for SwiftUI and Swift 6 — architecture and state, strict concurrency, Swift Testing, Human Interface Guidelines conformance and accessibility, SwiftUI motion, native macOS apps, the first-party framework map, on-device generative AI with Foundation Models, performance diagnosis with Instruments, App Store release engineering, and the build-test-screenshot loop. Ships a build gate that blocks a session ending on a failed build after Swift edits."
    }
```

- [ ] **Step 10: Add the root README row**

`README.md` has a `## What ships` table. Add a row. The audit errors on a
shipped skill missing from the skills column (`audit_marketplace.ts:293-306`),
so all eleven names must appear:

```markdown
| [apple-studio](plugins/apple-studio) | `app-release` `apple-animations` `apple-design` `apple-frameworks` `apple-intelligence` `apple-macos` `apple-performance` `swift-architecture` `swift-concurrency` `swift-testing` `xcode-loop` | Native Apple app development — architecture, strict concurrency, testing, HIG conformance, motion, macOS, frameworks, on-device AI, performance, release. Ships a PostToolUse edit tracker and a Stop build gate |
```

- [ ] **Step 11: Add eleven entries to the security eval roster**

`tests/security-evals.test.ts:40-48` asserts every shipped skill appears in one
of the manifest's four lists. Omissions are the right list here: the battery's
lineup is target plus decoys plus synthetic, and
`tests/security-evals.test.ts:86-90` asserts omissions stay out of it.

```bash
cd ~/Projects/agent-tools
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('plugins/security/skills/reviewing-code-security/evals/manifest.json')
m = json.loads(p.read_text())
new = [
    'app-release', 'apple-animations', 'apple-design', 'apple-frameworks',
    'apple-intelligence', 'apple-macos', 'apple-performance',
    'swift-architecture', 'swift-concurrency', 'swift-testing', 'xcode-loop',
]
m['acknowledgedOmissions'] = sorted(set(m['acknowledgedOmissions']) | set(new))
p.write_text(json.dumps(m, indent='\t') + '\n')
print(len(m['acknowledgedOmissions']), 'omissions')
PY
```

- [ ] **Step 12: Run the full gate**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
bun run audit >/dev/null 2>&1; echo "audit exit=$?"
claude plugin validate . && echo "marketplace ok"
claude plugin validate plugins/apple-studio --strict && echo "plugin ok"
```

Expected: `0 fail`, `audit exit=0`, and both `ok` lines. The test count rises
above 74 — several suites are `test.each(pluginDirs)`, so a tenth plugin adds
cases.

- [ ] **Step 13: Confirm all eleven skills load**

```bash
cd ~/Projects/agent-tools
claude --plugin-dir plugins/apple-studio -p "List the names of every skill you can see from this plugin, one per line, and nothing else." --max-turns 2 </dev/null
```

Expected: all eleven names.

- [ ] **Step 14: Record the strict-audit delta**

```bash
cd ~/Projects/agent-tools
bun run audit:strict 2>&1 | tail -3
```

Expected: still `0 error(s)`, warnings risen from 12 to roughly 82. Record the
exact number in the task report. It is not a failure — `audit:strict` already
exited 1 before this phase began, and the new warnings are missing tables of
contents plus `apple-frameworks`' sixteen primers nesting a level deeper than
the validator expects. Deferred, per the spec.

- [ ] **Step 15: Validate the hooks**

```bash
cd ~/Projects/agent-tools
bun plugins/meta-skills/skills/authoring-hooks/scripts/validate_hooks.ts \
  plugins/apple-studio/hooks/hooks.json
```

Expected: no errors. If the script's path or name differs, find it with
`find plugins/meta-skills -name 'validate_hooks*'` and use what is there.

- [ ] **Step 16: Commit**

```bash
cd ~/Projects/agent-tools
git add -A
git commit -m "Phase 8 Task 2: import the apple-studio plugin at 0.9.0

Eleven skills and two hooks, copied from the authoring repo. The manifest
gains the four fields the catalog's other plugins carry, and author moves
to Agent Tools with attribution in the plugin README.

Five SKILL.md citations named a sibling skill's reference file with a
bare references/ path. validate_skill.ts resolves those against the
citing skill and errors, and the audit reports validator errors as
errors, so the import could not pass until they were rewritten.

Also adds the catalog's first .gitignore, without which the authoring
tree arriving in Task 4 would make corpus/ committable.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Settle the routing between the three Apple skills

The only change in this phase that alters which skill fires. It gets its own
task so a reviewer can weigh it on its own, and its own eval run.

**Repo:** the catalog.

**Files:**
- Modify: `plugins/apple-studio/skills/apple-animations/SKILL.md:3` (description)
- Modify: `plugins/design-engineering/skills/fluid-interfaces/SKILL.md:3` (description)

**Interfaces:**
- Consumes: `fluid-interfaces` (Task 1) and `plugins/apple-studio/` (Task 2).
  Both must exist, or each description points at a skill the catalog lacks.
- Produces: nothing later tasks read.

- [ ] **Step 1: Add the platform clause to `apple-animations`**

Its description currently ends:

```
..., general layout and styling (apple-design), or the build/run loop (xcode-loop).
```

Append one sentence so it ends:

```
..., general layout and styling (apple-design), or the build/run loop (xcode-loop). For motion on the web or the Svelte stack, use fluid-interfaces.
```

Change the `description:` line in the frontmatter only. The body stays as it is.

- [ ] **Step 2: Add the mirror clause to `fluid-interfaces`**

Its description currently ends:

```
... For the animation decision sequence and the everyday recipes use animating-interfaces.
```

Append one sentence so it ends:

```
... For the animation decision sequence and the everyday recipes use animating-interfaces. For native SwiftUI motion use apple-animations.
```

The description is single-quoted YAML containing apostrophes escaped as `''`.
Keep that quoting intact.

- [ ] **Step 3: Confirm both files still parse**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
```

Expected: `0 fail`. The suite reads both frontmatter blocks, so a broken quote
shows up here.

- [ ] **Step 4: Run the apple-animations trigger evals**

```bash
cd ~/Projects/apple-studio
python3 pipeline/run_evals.py \
  plugin/skills/apple-animations/evals/triggers.md \
  /tmp/phase8-evals-animations
```

If `run_evals.py` expects a `.tsv` rather than the trigger file, build one from
`triggers.md` first — the file lists prompts with their expected outcome. Check
its `--help` before improvising.

Expected: every should-fire prompt reaches `apple-animations`, every
should-not-fire prompt leaves it silent, and the driver reports the
StudioFixture tree clean at close. A dirty tree is a failure even if every
prompt passed.

- [ ] **Step 5: Run the design-engineering routing battery**

`fluid-interfaces` uses a different harness — design-engineering's own cases.

```bash
cd ~/Projects/agent-tools
sed -n '/Gestures, physics, materials, type/,/^$/p' \
  plugins/design-engineering/skills/design-engineering/evals/routing.md
```

Run each listed query against a session with the design-engineering plugin
loaded, and confirm `fluid-interfaces` is what fires:

```bash
claude --plugin-dir plugins/design-engineering -p "<query>" --max-turns 2 </dev/null
```

Expected: `fluid-interfaces` wins every case that `apple-design` used to win.
Record the queries and outcomes in the task report.

- [ ] **Step 6: Commit**

```bash
cd ~/Projects/agent-tools
git add -A
git commit -m "Phase 8 Task 3: separate the three Apple skills by platform

apple-animations, fluid-interfaces, and apple-design all answer to 'make
this feel Apple'. The discriminator is platform, not topic, so each
description now names the sibling that owns the other platform.

Descriptions only; no body changed. This is the one edit in the phase
that moves routing, which is why apple-studio ships at 0.9.0 rather than
carrying 0.8.0 across unchanged.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Move the authoring tools into the catalog

Brings the pipeline, the specs and plans, and the conventions across, and gives
the catalog the root memory file that puts the Apple rules in scope while the
skills are edited.

**Repo:** the catalog. Source is the authoring repo.

**Files:**
- Create: `authoring/apple-studio/pipeline/` (copied, 25 files)
- Create: `authoring/apple-studio/docs/` (copied, 15 files)
- Create: `authoring/apple-studio/CONVENTIONS.md` (copied, 5 lines repointed)
- Create: `authoring/apple-studio/records/.gitkeep`
- Create: `CLAUDE.md` (the catalog's first)
- Modify: `README.md:39-40` and `README.md:59-63`
- Modify: `plugins/apple-studio/skills/apple-frameworks/references/framework-catalog.md:4`

**Interfaces:**
- Consumes: `plugins/apple-studio/` from Task 2 — `CONVENTIONS.md`'s repointed
  paths must name a directory that exists.
- Produces: `authoring/apple-studio/`, which Task 5 deletes the source of.

- [ ] **Step 1: Copy the three trees**

```bash
cd ~/Projects/agent-tools
mkdir -p authoring/apple-studio
rsync -a --exclude='.DS_Store' --exclude='tmp/' \
  ~/Projects/apple-studio/pipeline authoring/apple-studio/
rsync -a --exclude='.DS_Store' \
  ~/Projects/apple-studio/docs authoring/apple-studio/
cp ~/Projects/apple-studio/CONVENTIONS.md authoring/apple-studio/
mkdir -p authoring/apple-studio/records && touch authoring/apple-studio/records/.gitkeep
```

Note the source paths have **no** trailing slash here, unlike Task 2 step 2 —
these copy the directory itself into the destination.

- [ ] **Step 2: Verify the copy**

```bash
cd ~/Projects/agent-tools
find authoring/apple-studio/pipeline -type f | wc -l
find authoring/apple-studio/docs -type f | wc -l
```

Expected: `25` and `15` — the second is 7 specs, 7 plans, and `deferred.md`.

- [ ] **Step 3: Repoint the five paths in `CONVENTIONS.md`**

Lines 32, 43, 135, 144, and 158 each name `plugin/…`, which no longer exists.

```bash
cd ~/Projects/agent-tools/authoring/apple-studio
sed -i '' \
  -e 's|`plugin/skills/|`plugins/apple-studio/skills/|g' \
  -e 's|`plugin/agents/|`plugins/apple-studio/agents/|g' \
  -e 's|`plugin/hooks/|`plugins/apple-studio/hooks/|g' \
  -e 's|`plugin/\.claude-plugin/plugin\.json`|`plugins/apple-studio/.claude-plugin/plugin.json`|g' \
  CONVENTIONS.md
grep -n 'plugin/' CONVENTIONS.md
```

Expected: every remaining hit reads `plugins/apple-studio/…`. A bare `plugin/`
left over means a form the sed did not cover — fix it by hand.

- [ ] **Step 4: Add the naming exception to `CONVENTIONS.md`**

`CONVENTIONS.md:33-34` states the skill naming rule. The catalog names skills
with gerunds; apple-studio's eleven stay as they are, so the rule needs to say
that it is a deliberate local exception. After the existing naming bullet, add:

```markdown
- The catalog's other plugins name skills with gerunds (`animating-interfaces`,
  `configuring-zed`). These eleven keep topic nouns: the `swift-` and `apple-`
  prefixes group code-level against platform-level work at a glance, and the
  catalog already carries eleven noun-named skills. Widening that exception was
  decided in Phase 8; see `docs/specs/2026-09-12-phase8-catalog-migration-design.md`.
```

- [ ] **Step 5: Repoint the generated-file header**

`plugins/apple-studio/skills/apple-frameworks/references/framework-catalog.md:4`
reads:

```markdown
> regenerate: pipeline/generate_catalog.sh (rerun each phase and after WWDC)
```

Change to:

```markdown
> regenerate: authoring/apple-studio/pipeline/generate_catalog.sh (rerun each phase and after WWDC)
```

- [ ] **Step 6: Write the catalog's first `CLAUDE.md`**

The Apple authoring rules have to be in scope while `plugins/apple-studio/skills/`
is edited, and a nested `CLAUDE.md` under `authoring/` would not load in that
subtree. Root memory always loads.

Create `~/Projects/agent-tools/CLAUDE.md`:

```markdown
# agent-tools

A Claude Code plugin marketplace. Eleven plugins under `plugins/`, published
through `.claude-plugin/marketplace.json`.

## Layout

- `plugins/<name>/` — what installs. Nothing an installer does not need goes
  here; the directory is the install unit.
- `authoring/<plugin>/` — dev-time tooling for one plugin. Never installed.
- `tests/` — the pinned contract. `bun test`.

## Verify

Both must pass before any commit that touches `plugins/`:

- `bun test` — registration both ways, name against directory, skill-name
  uniqueness across the catalog, the README skills column, the security eval
  roster.
- `bun run audit` — the vendored validators over every skill, plugin, agent,
  and hook. Exits non-zero on errors only.

`bun run audit:strict` also fails on warnings. It does not currently pass and
is not a gate — run it to compare warning counts, not to gate a commit.
`claude plugin validate .` is the authoritative marketplace check.

## Versions

Version lives in `plugins/<name>/.claude-plugin/plugin.json` and nowhere else.
Marketplace entries carry no version field. An unbumped plugin ships nothing:
`/plugin update` reports "already at the latest version" and users keep the old
copy indefinitely. `bun run audit --since <ref>` names plugins that changed
without a bump.

`name` is install-breaking — users carry it in `enabledPlugins` and every
install command. To change a label, set `displayName`. To change a `name`, add
a `renames` entry mapping old to new. Skill names live in no user setting, so
renaming a skill breaks nothing.

## apple-studio

The one plugin with its own authoring pipeline. Its conventions bind any change
to `plugins/apple-studio/`: read `authoring/apple-studio/CONVENTIONS.md` before
editing a skill or reference there.

Three things from it that are easy to get wrong:

- **Live docs win over memory.** Apple's APIs churn every WWDC. Fetch the
  current page with `authoring/apple-studio/pipeline/docc.py` — developer.apple.com
  serves a JavaScript shell, so a plain fetch returns navigation and no content.
- **A 200 on a doc page is not evidence a symbol exists.** Compilation is the
  ship gate for any API-specific claim:
  `python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/<skill>/references/*.md`
- **Run trigger evals through `authoring/apple-studio/pipeline/run_evals.py`**,
  not a fresh loop. `--allowedTools` does not stop an eval session writing to
  the fixture app; the driver checks the fixture's git status before, during,
  and after, attributes writes to the prompt that made them, and restores the
  tree.

Work happens in numbered phases — see `authoring/apple-studio/CONVENTIONS.md`
and `authoring/apple-studio/docs/`. Phase records go to
`authoring/apple-studio/records/<date>-phaseN-<slug>/`. Tags are namespaced:
`apple-studio-v0.9.0`, never a bare version.
```

- [ ] **Step 7: Correct the two stale README paragraphs**

`README.md:39-40` claims `bun test` pins "version agreement between
`plugin.json` and the marketplace entry". There is no version in a marketplace
entry. Change that clause to read `version presence in each `plugin.json``.

`README.md:59-63` opens the Releasing section with "A version has to move in
**both** places that record it". Replace that paragraph with:

```markdown
A version lives in `plugins/<plugin>/.claude-plugin/plugin.json` and nowhere
else — marketplace entries carry no version field. An unbumped plugin ships
nothing: `/plugin update` reports "already at the latest version" and users keep
the old copy indefinitely. `bun run audit --since <ref>` reports a plugin
directory that changed without a bump.
```

- [ ] **Step 8: Confirm the pipeline still runs from its new home**

```bash
cd ~/Projects/agent-tools
python3 authoring/apple-studio/pipeline/typecheck_snippets.py \
  plugins/apple-studio/skills/swift-concurrency/references/strict-concurrency.md
echo "typecheck exit=$?"
bash authoring/apple-studio/pipeline/test_run_evals.sh && echo "eval driver self-test ok"
```

Expected: `typecheck exit=0` and the self-test passing. The self-test runs
offline. If `typecheck_snippets.py` needs a toolchain that is unavailable, note
that and move on — it is a tool check, not a gate on this task.

- [ ] **Step 9: Run the full gate**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
bun run audit >/dev/null 2>&1; echo "audit exit=$?"
```

Expected: `0 fail`, `audit exit=0`. `authoring/` sits outside `plugins/`, so no
check walks it — this confirms it did not accidentally register as a plugin.

- [ ] **Step 10: Commit**

```bash
cd ~/Projects/agent-tools
git add -A
git commit -m "Phase 8 Task 4: move the apple-studio authoring tools in

pipeline/, docs/, and CONVENTIONS.md land under authoring/apple-studio/,
outside plugins/ so none of it reaches an installer. Five paths in
CONVENTIONS.md repoint, and the naming rule gains the exception Phase 8
decided: these eleven skills keep topic nouns where the catalog uses
gerunds.

Adds the catalog's first CLAUDE.md. The Apple rules have to be in scope
while plugins/apple-studio/skills/ is edited, and a nested memory file
under authoring/ would not load in that subtree.

Corrects two README paragraphs describing version machinery that does
not exist: marketplace entries carry no version field, and bun test
cannot compare one against plugin.json.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Strip and archive the authoring repo

Leaves the authoring repo holding only its verification record.

**Repo:** the authoring repo, `~/Projects/apple-studio`.

**Files:**
- Delete: `plugin/`, `pipeline/`, `docs/`, `CONVENTIONS.md`, `.claude-plugin/marketplace.json`
- Rewrite: `README.md`
- Delete: `CLAUDE.md`
- Keep: `.superpowers/`, `.gitignore`, `.claude/`

**Interfaces:**
- Consumes: Tasks 2 and 4 — everything deleted here must already be committed
  in the catalog.

- [ ] **Step 1: Prove the catalog has everything before deleting anything**

```bash
cd ~/Projects/agent-tools
git status --porcelain | head
diff -r --exclude='.DS_Store' ~/Projects/apple-studio/pipeline authoring/apple-studio/pipeline && echo "pipeline ok"
diff -r --exclude='.DS_Store' ~/Projects/apple-studio/docs authoring/apple-studio/docs && echo "docs ok"
```

Expected: a clean catalog working tree and both `ok` lines. If `git status`
shows anything uncommitted, stop — Task 4 is not finished, and deleting the
source now would lose it. `plugin/` is deliberately not compared: Task 2 edited
five files in the copy.

- [ ] **Step 2: Confirm the record survives and the tags still resolve**

```bash
cd ~/Projects/apple-studio
git tag | tail -3
git show v0.8.0:plugin/skills/apple-design/SKILL.md | head -3
find .superpowers -type f | wc -l
```

Expected: tags listed, the old `SKILL.md` printing from `v0.8.0`, and 391 files
under `.superpowers/`. This is what makes the deletion safe — the tags hold the
tree regardless of what `HEAD` looks like afterwards.

- [ ] **Step 3: Delete what moved**

```bash
cd ~/Projects/apple-studio
git rm -r -q plugin pipeline docs CONVENTIONS.md CLAUDE.md .claude-plugin
```

- [ ] **Step 4: Rewrite the README as a pointer**

Create `~/Projects/apple-studio/README.md`:

```markdown
# apple-studio (archived)

The `apple-studio` plugin now lives in the **agent-tools** catalog:
<https://github.com/frenchfulton94/agent-tools>

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install apple-studio@agent-tools --scope project

The plugin is at `plugins/apple-studio/`. Its distillation pipeline, design
specs, implementation plans, and authoring conventions are at
`authoring/apple-studio/`.

## What is left here

`.superpowers/sdd/` — the verification record for Phases 0 through 7. Task
briefs, task reports, and captured logs, 391 files. Every `verified:` header and
spec verification table in the plugin that cites a log cites one of these, so
they stay reachable at this URL.

Tags `v0.2.0` through `v0.8.0` hold the plugin tree as it stood at each phase.
`git show v0.8.0:plugin/skills/<name>/SKILL.md` still works. The 0.8.0 tree is
also reachable directly at commit `32797c9`, whether or not the tag survives.

Phase 8 moved everything else. Its design spec is at
`authoring/apple-studio/docs/specs/2026-09-12-phase8-catalog-migration-design.md`
in the catalog.
```

- [ ] **Step 5: Commit and push**

```bash
cd ~/Projects/apple-studio
git add -A
git commit -m "Phase 8 Task 5: strip the repo to its verification record

The plugin and its authoring tools now live in agent-tools. What stays
is .superpowers/sdd/ — the captured logs every verified: header cites —
plus the tags that hold each phase's plugin tree.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git push origin phase-8
```

- [ ] **Step 6: Stop here and hand back**

Archiving the GitHub repository and removing the local marketplace are
outward-facing and not reversible by the same command that did them. Report
what is ready and let the user run:

```bash
claude plugin marketplace remove apple-studio
claude plugin marketplace add frenchfulton94/agent-tools --scope project
claude plugin install apple-studio@agent-tools --scope project
```

and archive `frenchfulton94/apple-studio` through GitHub's settings once the
catalog pull request has merged.

---

### Task 6: Release

**Repo:** both.

- [ ] **Step 1: Final gate on the catalog**

```bash
cd ~/Projects/agent-tools
bun test 2>&1 | tail -4
bun run audit >/dev/null 2>&1; echo "audit exit=$?"
claude plugin validate . && echo "ok"
git status --porcelain | head
```

Expected: `0 fail`, `audit exit=0`, `ok`, and a clean tree.

- [ ] **Step 2: Confirm every version that should have moved, did**

```bash
cd ~/Projects/agent-tools
bun run audit --since main 2>&1 | grep -iE "still at|version" | head
```

The branch was cut from `main` at `cb24f86` and not rebased, so `--since main`
compares against the real base.

Expected: no plugin reported as changed without a bump. Four plugins changed in
this phase — `design-engineering`, `workflows`, `security` in Task 1, and
`apple-studio` arriving at `0.9.0`.

- [ ] **Step 3: Open the pull request**

```bash
cd ~/Projects/agent-tools
git push -u origin phase-8-apple-studio
gh pr create --title "Add the apple-studio plugin and rename design-engineering's apple-design to fluid-interfaces" --body "$(cat <<'BODY'
Moves the apple-studio plugin into this catalog, where it now ships from
alone. Eleven skills and two hooks covering native Apple app development —
architecture, strict concurrency, Swift Testing, HIG conformance, SwiftUI
motion, macOS, the framework map, on-device generative AI, performance
diagnosis, App Store release, and the build loop.

design-engineering's `apple-design` becomes `fluid-interfaces`. The catalog
forbids two skills sharing a name, and that skill translates Apple's
fluid-interface principles to the web and Svelte — the literal name belongs to
the plugin doing native Apple work. Skill names live in no user setting, so no
install breaks.

The plugin's authoring pipeline, design specs, and conventions land under
`authoring/apple-studio/`, outside `plugins/` so none of it reaches an
installer. The catalog gains its first `CLAUDE.md` and first `.gitignore`.

Two README paragraphs described version machinery that does not exist —
marketplace entries carry no version field — and are corrected here.

Verified: `bun test` green, `bun run audit` exit 0, `claude plugin validate .`
clean, all eleven skills load under `--plugin-dir`, and the trigger evals rerun
for the two skills whose descriptions changed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```

- [ ] **Step 4: Tag after the merge**

```bash
cd ~/Projects/agent-tools
git checkout main && git pull
git tag apple-studio-v0.9.0
git push origin apple-studio-v0.9.0
```

Namespaced, not a bare `v0.9.0` — the catalog holds eleven plugins on
independent versions and a bare tag would claim the repository for one of them.

- [ ] **Step 5: Confirm the install actually serves 0.9.0**

A version that did not move ships nothing, silently. Confirm delivery rather
than assuming it:

```bash
claude plugin marketplace add frenchfulton94/agent-tools --scope project
claude plugin install apple-studio@agent-tools --scope project
claude plugin list | grep apple-studio
```

Expected: `apple-studio` at `0.9.0`.

- [ ] **Step 6: Record the phase in `docs/deferred.md`**

Two items earned a deferred entry during this phase. Append both to
`authoring/apple-studio/docs/deferred.md`, each with an explicit trigger:

```markdown
## 70 validator warnings in the apple-studio skills

`bun run audit:strict` gained roughly 70 warnings when the plugin arrived: 16
reference files not linked from their `SKILL.md`, 16 nested a level deeper than
the validator expects (all `apple-frameworks` primers), and around 38 reference
files over 100 lines with no table of contents in the first 30. None are errors
and `bun run audit` is unaffected.

**Trigger:** revisit if `audit:strict` is ever made a commit gate, or if a
reader reports trouble navigating a long reference.

## `~/Projects/StudioFixture` cited in a shipped reference

`xcode-loop/references/headless-commands.md:6-7` names the fixture app by a
path on one machine. It is a provenance citation in a verified-against header,
not an instruction, so it ships as it stands.

**Trigger:** rewrite it the next time that reference is revised for any other
reason.
```

Commit with `Phase 8 Task 6: release apple-studio 0.9.0 from the catalog`.

---

## Self-Review

**Spec coverage.** Every spec section maps to a task: the rename to Task 1;
`plugins/apple-studio/`, the manifest, the plugin README, the citation fixes,
the marketplace entry, the README row, and the security roster to Task 2;
routing to Task 3; `authoring/apple-studio/`, the root `CLAUDE.md`, the
`.gitignore`, and the README corrections to Task 4; the archive to Task 5;
tagging, install confirmation, and the two deferred items to Task 6.

**Naming consistency.** `fluid-interfaces` is the skill name throughout;
`apple-studio` names both the plugin and the archived repository, disambiguated
by "the catalog" and "the authoring repo" per the Global Constraints. Version
`0.9.0` and tag `apple-studio-v0.9.0` agree everywhere they appear.

**Known soft spots, flagged rather than hidden.**

- Task 3 steps 4-5 depend on `run_evals.py`'s argument shape and on
  design-engineering's routing battery being runnable by hand. Both steps say to
  check `--help` and read the file rather than assume. If either harness turns
  out to need work, that is a finding to report, not a step to skip — these are
  the only checks covering the phase's one routing change.
- Task 2 step 15 names `validate_hooks.ts` by the path the audit resolves it
  from. The step says how to find it if the name differs.
- Task 6 step 2's `--since main` assumes the branch has not been rebased onto a
  moved `main`. If it has, use the merge-base commit instead.
