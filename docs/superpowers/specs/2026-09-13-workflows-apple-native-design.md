# Apple-native support for the workflows plugin

Date: 2026-09-13
Status: approved design, awaiting implementation plan

## 1. Goal

The `workflows` plugin sets up a repository's OpenSpec workflow. Today it
detects web repositories and installs the web plugin layer. It knows nothing
about Apple-native repositories. This design adds Apple-native detection,
an Apple plugin layer, an `app-release` schema with supporting content, and
a documentation-link sweep in `apple-studio`.

## 2. Decision log

Each row records a decision the user made during design. A later change to
one of these reopens the design; it is not an implementation detail.

| # | Decision |
|---|---|
| 1 | Scope covers detection, plugins, and Apple-specific workflow content — not detection alone. |
| 2 | Content ships: an `app-release` schema, one Apple gate agent, verification via TOOLS.md delegation, and learn material. |
| 3 | Apple workflow content lands in the `advanced` level only. |
| 4 | Detection has two tiers. App signals gate the workflow content. A bare `Package.swift` gates the plugin layer only. |
| 5 | Mixed web + Apple repositories are handled by TOOLS.md delegation, not combined templates, a setup question, or web-wins. |
| 6 | Apple payload content nests inside the advanced level (`payload/levels/advanced/apple/`), not a general stack axis. |
| 7 | The Xcode MCP bridge is surfaced as a human step, not automated `.mcp.json` state. |
| 8 | The link sweep converts page-form `/documentation/` links only. JSON provenance citations stay as they are. |

## 3. Detection

`scripts/detect.mjs` gains `appleSignals(repoRoot)` beside `webSignals`.

Signals, by tier:

- **App signals** (tier 2): a `*.xcodeproj` or `*.xcworkspace` entry at the
  repository root or one directory deep; a root `Project.swift` or a root
  `Tuist/` directory; a root `project.yml`.
- **Swift signals** (tier 1): a root `Package.swift`. App signals imply
  tier 1.

The detection object gains one field:

```js
apple: {
  app: bool,      // any app signal
  swift: bool,    // any Swift signal; true whenever app is true
  signals: []     // e.g. ['app:ios/App.xcodeproj', 'swift:Package.swift']
}
```

Requirements:

- Detection MUST use filesystem checks only. It MUST NOT spawn a process
  for Apple signals.
- A directory that cannot be read MUST degrade to "no signal", never to a
  crash. Reuse the guarded pattern `dirNames` already implements.
- `detect.mjs` MUST also report whether the repository's `.mcp.json`
  configures an `xcode` MCP server. An unparseable `.mcp.json` counts as
  "not configured".

## 4. Plugin layer (tier 1)

New manifest `payload/base/settings.base.apple.json`:

```json
{
  "enabledPlugins": { "apple-studio@agent-tools": true },
  "extraKnownMarketplaces": {
    "agent-tools": {
      "source": { "repo": "frenchfulton94/agent-tools", "source": "github" }
    }
  }
}
```

`buildPlan` MUST push this manifest when `detection.apple.swift` is true,
directly after the web manifest line. Merge order is unchanged otherwise.
The existing I3 rule (a decided plugin id is never overridden) applies
unchanged. A mixed web + Apple repository receives both layers.

The manifest starts with `apple-studio` alone. Adding further plugins later
is a manifest edit, not a design change.

## 5. Advanced Apple content (tier 2)

New subtree, mirroring the level layout:

```
payload/levels/advanced/apple/
  openspec/schemas/app-release/
    schema.yaml
    templates/release-scope.md
    templates/preflight.md
    templates/tasks.md
    templates/post-release.md
  agents/
    apple-design-gate.md
```

### 5.1 The app-release schema

Four artifacts, chained by `requires`, in the house style of the existing
schemas:

1. **release-scope** — what ships and as what number. Version and build
   bump decision, contents since the last release, phased-release intent,
   and the named go/no-go owner. A decision record, not a changelog dump.
2. **preflight** — the pre-submission checklist. It covers:
   - signing and provisioning
   - privacy manifest and nutrition-label answers, checked against actual
     code behavior
   - screenshots and metadata; export compliance
   - review notes: demo account, areas reviewers cannot reach

   Every item MUST name the evidence checked, not a bare checkbox.
3. **tasks** — archive, upload, TestFlight distribution, testing gates,
   submission. Every step MUST name its verification signal (build visible
   in App Store Connect, TestFlight install on device, review state
   transition).
4. **post-release** — completed after release, before archiving: the
   phased-release monitoring plan with pause thresholds, and links to
   follow-up changes.

The schema's `apply.instruction` MUST point at the `apple-studio`
`app-release` skill as the knowledge source. The schema owns the chain and
gates; the skill owns the mechanics. Content MUST NOT be copied from the
skill into the schema.

### 5.2 The gate agent

One agent, `apple-design-gate.md`. It grounds design review in the
`apple-design` skill (HIG, platform idioms) and verifies through the
`xcode-loop` skill. It ships under its own name beside the neutral gates.
`review-gate` and `taste-preflight` stay unchanged.

### 5.3 Routing

`ROUTING.md` stays a single file. It gains one decision-tree entry:

> Shipping a build to TestFlight or the App Store → **app-release**
> (installed only in Apple-native app repositories; if the schema is
> absent, this entry does not apply)

And two guardrails:

- An app-release change that discovers a code defect MUST stop and spawn a
  bugfix change. The release chain never absorbs code fixes.
- An urgent fix already live in the store routes the code work through
  hotfix. The expedited-review submission still goes through app-release,
  referencing the hotfix.

### 5.4 Composition

When `level === 'advanced'` and `detection.apple.app` is true, the shipped
schema and agent lists are the union of the level root and the apple
subtree. `classify` runs on the merged lists unchanged, so ownership,
collisions, and updates (I2, I6) behave exactly as they do today.

## 6. Verification via TOOLS.md

Three template groups are reworded to delegate verification:

- `feature/templates/verification.md`
- `upgrade/templates/verification.md`
- any advanced-schema `tasks.md` whose verification prose names a
  stack-specific command

The new wording: "run the checks for the stack this change touches, as
recorded in TOOLS.md." No per-stack template variants exist.

The setup skill's step 4 writes TOOLS.md via `mapping-project-tooling`. It
gains one sentence: in an Apple-native repository, confirm the build,
test, and simulator commands land in TOOLS.md.

These edits change shipped-template hashes. Prior repositories see them as
`update` (untouched) or `collide` (user-edited) on re-run. That is the
existing I6 behavior; nothing new is built for it.

## 7. buildPlan changes

Complete list:

1. Push `settings.base.apple.json` on tier 1 (section 4).
2. Union composition on advanced + app (section 5.4).
3. The plan gains an `apple: { app, swift }` field, mirroring `web`, so the
   rendered plan states why Apple content appears.
4. Loud-failure guard: if `detection.apple.app` is true, the level is
   `advanced`, and the apple subtree is missing from the payload,
   `buildPlan` MUST throw. It MUST NOT degrade to a plan that omits
   content it claimed to ship. This follows the Ruling 48 precedent.

## 8. Human steps and the Xcode integration

When `detection.apple.app` is true and no `xcode` MCP server is configured,
`buildPlan` MUST append this human step:

> Enable "Allow external agents to use Xcode tools" in Xcode → Settings →
> Intelligence, then run
> `claude mcp add --transport stdio xcode -- xcrun mcpbridge`.
> Verification then drives Xcode directly; without it, xcode-loop falls
> back to headless xcodebuild.

Rationale, recorded so the boundary survives:

- The settings toggle is human-only. No automation can perform it.
- The in-Xcode Claude agent needs no step. Repo-scoped
  `.claude/settings.json` travels with the repository.
  `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig` is
  machine-global; the plugin reports machine-global state and never writes
  it, matching the OpenSpec machine-profile policy.

The `apple-studio` README's Install section gains the Xcode Add-Plug-in
flow as an alternate install path. It also gains a pointer to the
mcpbridge toggle for external-agent use.

## 9. Apple documentation link sweep (apple-studio)

Verified on 2026-09-13 against live URLs:

| Link class | Unique count | `.md` result |
|---|---|---|
| `/documentation/...` (incl. symbol URLs) | 1,045 | 200, `text/markdown` |
| `/tutorials/data/...json` | 93 | JSON API; 92 have `.md` equivalents |
| `/design/human-interface-guidelines/...` | 32 | 404 — no `.md` exists |
| `/help/`, `/app-store/`, `/support/`, misc | 9 | redirects or HTML |

Requirements:

- Every page-form `/documentation/` link under `plugins/apple-studio/`
  MUST end in `.md`. This applies in prose and in `> verified:` headers.
- The `/tutorials/data/...json` links MUST NOT change. They are the
  distillation pipeline's citation record (see
  `authoring/apple-studio/CONVENTIONS.md`); rewriting them would falsify
  provenance.
- HIG, help, app-store, and support links MUST NOT change.
- Implementation MUST verify the full converted set: fetch every rewritten
  URL and fail on any response that is not `text/markdown`. No sampling.
- The sweep carries the standing apple-studio ride-alongs:
  `.agents/skills/` re-sync, version bump, `bun test`, `bun run audit`.

## 10. Learn material

One new lesson ships: `0014-apple-native-repos.html`, in the existing
lesson format. It covers three topics:

- the two detection tiers and what each installs
- the app-release chain end to end
- the mcpbridge setup, including the human-only toggle

Reference cards: `workflow-atlas.html` gains app-release as a ninth entry
marked "Apple app repos, advanced level"; `router-card.html` gains the
routing line.

Constraints the implementation inherits:

- `assets/check-structure.mjs` and `check-answers.mjs` pin lesson structure
  and quiz answers; they update alongside the lesson.
- The build rewrites source citations to blob URLs and fails on 404s. The
  lesson's citations of `payload/levels/advanced/apple/...` paths MUST land
  after the payload exists.
- Merging publishes to the public site. Review the lesson with that in
  mind before merge.

## 11. Skill prose updates

- `skills/setup/SKILL.md`: interview and plan rendering mention the apple
  field; step 4 gains the TOOLS.md sentence; human steps gain mcpbridge.
- `skills/choosing-a-workflow/references/chains.md`: gains the app-release
  chain, qualified "Apple app repos only".
- `skills/choosing-a-workflow/evals/`: gains a routing case for "ship this
  build to TestFlight".
- Plugin README levels table: advanced is 8 schemas, 9 in Apple-native app
  repositories, as a footnote.

## 12. Tests

- **detect**: signal tiers; the one-level-deep xcodeproj scan; a
  permission-locked directory degrades to no signal; the `.mcp.json` read
  (present, absent, unparseable).
- **plan**:
  - apple manifest pushed on tier 1
  - union composition on advanced + app
  - `classify` over merged lists — an existing user `app-release` schema
    collides and is named
  - the loud-failure guard
  - the `apple` plan field
  - the conditional mcpbridge human step
- **link-sweep regression**: a repository test pins that no page-form
  `/documentation/` link without `.md` exists under
  `plugins/apple-studio/`.
- **e2e (opt-in)**: one Apple fixture repository (a stub `.xcodeproj`
  directory suffices) proving the advanced plan ships app-release and
  I2/I6 hold over it. Runs pre-release, not in CI, like the rest of the
  suite.
- `ci-workflows.test.ts` and the audit need no changes.

## 13. Versioning and catalog

- `workflows`: minor bump — new capability.
- `apple-studio`: patch bump — link sweep and README addition.
- `.agents/skills/` re-syncs for the vendored apple-studio skills.
- The marketplace description for `workflows` gains a clause naming
  Apple-native support. The "twelve workflows" phrasing there and in the
  README takes the same footnote treatment as the levels table.
- `bun run audit --since <ref>` confirms nothing else changed unbumped.

## 14. Process requirements

Every implementation task MUST load the skills its surface requires before
editing:

| Work surface | Required skill(s) |
|---|---|
| OpenSpec schema, templates, ROUTING.md, config.yaml.example | `configuring-openspec` |
| Prompt-bearing prose: schema `instruction:` blocks, gate agent, template rewording | `improving-prompts` |
| `apple-design-gate.md` (a subagent definition) | `authoring-subagents` |
| SKILL.md edits | `authoring-skills` |
| Plugin manifests, payload layout, version bumps, plugin READMEs | `authoring-plugins` |
| Marketplace entry, catalog-level README rows | `maintaining-plugin-marketplaces` |

General rule: a task touching any Claude Code extension surface loads its
`authoring-*` skill. This binds future amendments, not only the tasks named
here. Detection and plan script changes are plain code; the repository's
test gates cover them.

## 15. Deferred

Recorded as decisions, not omissions:

1. Automating `claude mcp add` via project-scope `.mcp.json` — a new
   managed-state surface (record, reconcile, collisions) for a one-liner.
2. Generalizing to a stack axis (`payload/stacks/`) if a second stack
   arrives.
3. Apple content for the `standard` level.
4. Converting the JSON provenance citations — declined deliberately
   (section 9).

## 16. Invariants kept

- I1: nothing here touches `openspec/specs/` or `openspec/changes/`.
- I2: an existing `app-release` schema collides and is named in the plan,
  never replaced silently.
- I3: a decided plugin id is skipped; the apple manifest adds ids, never
  overrides.
- I6: template rewording flows through the existing update/collide split.
- Machine-global state (`openspec config profile`,
  `CodingAssistant/ClaudeAgentConfig`) is reported, never written.
- Telemetry opt-outs on every spawn are unaffected; detection adds no
  spawns.
