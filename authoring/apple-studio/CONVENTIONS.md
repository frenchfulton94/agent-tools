# apple-studio authoring conventions

Standards for every component in this repo, across all phases. Written in Phase 0 so
later phases can't drift from earlier ones. Amend deliberately, never silently.

## Stack baseline (the default voice of all guidance)

- SwiftUI-first, Swift 6 strict concurrency, async/await, SPM, Swift Testing.
- UIKit, Combine, XCTest, and other legacy material appears only under a heading that
  marks it as such: `## Maintaining older code: <topic>`.
- Current Apple docs win over book material on any conflict:
  - https://docs.swift.org/swift-book/
  - https://developer.apple.com/documentation/
  - https://developer.apple.com/design/human-interface-guidelines

## Live-docs-first rule

When working with any Apple framework or API, fetch and consult the current
developer.apple.com documentation — never rely on memory alone. Framework APIs
churn every WWDC; memory of them is presumed stale. The framework-catalog
reference answers "what exists?"; live docs answer "how does it work today?".

## Scope boundary

This plugin covers **native correctness**: architecture, concurrency, testing, HIG
conformance, accessibility, release engineering. Custom visual design and branding are
out of scope — other tooling owns "does it look distinctively ours"; this plugin owns
"is it correctly Apple".

## Skills

- Directory: `plugins/apple-studio/skills/<name>/` with a lean `SKILL.md` and knowledge in
  `references/*.md`, loaded on demand (progressive disclosure).
- Naming: kebab-case. Code-level skills use a `swift-` prefix (`swift-architecture`);
  platform/tooling skills use plain names (`xcode-loop`, `apple-design`, `app-release`).
- The catalog's other plugins name skills with gerunds (`animating-interfaces`,
  `configuring-zed`). These eleven keep topic nouns: the `swift-` and `apple-`
  prefixes group code-level against platform-level work at a glance, and the
  catalog already carries eleven noun-named skills. Widening that exception was
  decided in Phase 8; see `docs/specs/2026-09-12-phase8-catalog-migration-design.md`.
- SKILL.md carries process and judgment triggers; references carry depth. If SKILL.md
  exceeds ~150 lines, move content into references.
- Every skill ships trigger evals (fires when it should, silent when it shouldn't) per
  the authoring-skills skill.

## Reference files (distilled knowledge)

- Location: `plugins/apple-studio/skills/<skill>/references/<topic>.md`, one file per
  decision area, a few hundred lines each. Most skills need 3–6. A reference file MUST NOT
  be named for a device; name it for the decision it serves. (Amended 2026-09-30,
  Phase 9: iPhone Duo guidance lives in `apple-design/references/adaptive-layout.md`,
  because its APIs are documented for every platform.) Not book summaries —
  decision-grade guidance only.
- Every reference file starts with this header:

  ```
  > verified: <YYYY-MM> against <doc URLs checked>
  > sources: <book short-names distilled from>
  ```

- Distillation rules:
  - **Currency:** API-specific claims are checked against live Apple docs; docs win.
  - **Baseline:** modern stack is the default voice (see above).
  - **Worth-it:** skip anything Claude reliably knows already; capture judgment,
    trade-offs, and Apple-specific depth only.
- Never commit raw book text. `corpus/` is gitignored; committed references are
  distilled guidance in our own words.
- Generated reference files (e.g. `framework-catalog.md`) use a `> generated: <date>` /
  `> regenerate: <script>` header instead of the `verified:` block; the generator script is
  their verification.

## Pipeline tooling

`pipeline/` holds the scripts distillation depends on. Three are worth knowing
about before starting any live-docs work, and a fourth move — reading the SDK's
own shipped interface — is named alongside them:

- **`pipeline/docc.py`** — fetches and renders an Apple DocC JSON page.
  developer.apple.com serves a JavaScript shell, so fetching a human doc URL
  returns navigation and no content; the content is the DocC JSON behind it.
  `--children` walks topicSections, `--tutorial` handles the tutorials prefix
  (tutorials are not under `/documentation/`).
- **`pipeline/typecheck_snippets.py`** — compiles every ```swift block in a
  reference. **A 200 on a doc page is not evidence a symbol exists.** Phase 6
  found the live docs simultaneously behind the shipped OS and ahead of the
  shipped SDK, and found two non-compiling samples in Apple's own
  documentation. Compilation, not fetch success, is the ship gate for any
  API-specific claim.
  A reference whose APIs are iOS-only declares `> typecheck: ios <major>.<minor>`
  in its header block; the script then compiles that file against the iPhoneOS
  SDK. Without the directive a file compiles for macOS, which is correct for
  cross-platform SwiftUI and wrong for UIKit or iOS-only SwiftUI. A malformed
  directive, or one newer than the installed SDK, exits 2 rather than falling
  back. (Amended 2026-09-30, Phase 9.)
- **`pipeline/run_evals.py`** — runs the trigger-eval sweep against the fixture
  app. **`--allowedTools` does not stop an eval session from writing to the
  fixture.** Phase 6 left nine source files and a build directory in
  StudioFixture on that assumption. The driver therefore checks the fixture's
  git status before the sweep, after every prompt, and at close; it attributes
  writes to the prompt that made them, restores the tree, and exits non-zero.
  It also launches every session with stdin at `/dev/null` and defaults to
  `--max-turns 6`, because a stdin leak and turn exhaustion each produced a
  failure in Phase 6 that read like a skill misfire and would have been
  "fixed" by editing a skill description. Run the sweep through this script
  rather than a fresh loop; `pipeline/test_run_evals.sh` self-tests it offline.
- **The shipped `.swiftinterface`** — the SDK's own textual module interface, at
  `$(xcrun --sdk iphoneos --show-sdk-path)/System/Library/Frameworks/<Framework>.framework/Modules/<Framework>.swiftmodule/<arch>-apple-ios.swiftinterface`.
  Not a script and not under `pipeline/`; named here because it is the only one of
  these moves that answers **how** an API behaves rather than whether it exists.
  Some declarations ship their body. Phase 7 read `DragGesture.Value.velocity` as
  `4.0 * (predicted.x - location.x)`, inverted it to
  `predictedEndLocation == location + velocity * 0.25`, and so established that
  SwiftUI projects a flat 0.25 s of momentum — a fact the documentation does not
  state anywhere, so `docc.py` could not reach it, and a fact about behavior rather
  than existence, so `typecheck_snippets.py` could not reach it either. The same
  phase used it a second way, negatively: grepping the whole interface for `rubber`,
  `resistance`, and `overscroll` is evidence that no public rubber-banding API
  exists, because the interface is complete in a way the documentation is not.
  **Third strongest, still below runtime measurement — and that ranking was earned,
  not assumed.** Bodies are partial: `velocity` ships one, `predictedEndLocation`
  ships `get` with nothing in it, so the 0.25 s figure was an inference from an
  identity until 48 measured flicks put it at 0.250000 s every time. Worse, a
  reading that goes past the literal body can be flatly wrong — Phase 7 read the
  interface as implying that a `@GestureState` reset and a `withAnimation` on a
  separately committed offset hand off inside one graph update, and the running
  framework disagreed on 12 of 12 flicks. The interface states what a body computes;
  it says nothing about when the view graph schedules it. So the four moves rank in
  increasing strength — documented, exists in the shipped SDK, computes this, does
  this at runtime — and where two disagree, the later one wins. Treat a shipped body
  as an implementation detail rather than contract: re-read it per SDK instead of
  trusting a remembered line number, and cite it in a `verified:` header as
  "the shipped `<Symbol>` body in `<SDK>` `<Framework>.swiftinterface` (`<arch>`)",
  never as a machine-specific absolute path.

## Distillation maps

**Maps are seed lists, not exhaustive registries.** A distillation map enumerates the
dispatch-time starting points. Distillers may follow narrower pages under an enumerated
parent when the fetch actually succeeds (DocC JSON 200) — the reference file's header
citations, not the map, are the citation record. Expected-but-missing pages are still
recorded in the map as `MISSING:`. (Codified Phase 5 from the Phase 4 Task 3 controller
ruling.)

## Verification records

- Spec verification tables point at evidence as `<file>:<line-range>`, not bare filenames.
- A phase working in the catalog writes its task briefs, reports, and captured
  logs to `authoring/apple-studio/records/<date>-phaseN-<slug>/` — not to
  `.superpowers/`. The catalog's `.superpowers/sdd/.gitignore` is a single `*`
  inherited from this repository's own tooling; anything committed under
  `.superpowers/` here is silently dropped. (Phase 8's own record predates
  this rule and lives in the archived `apple-studio` repository instead, at
  `.superpowers/sdd/2026-09-12-phase8-catalog-migration/`.)
- Raw headless-session transcripts MUST NOT be committed: eval-sweep and probe
  session logs carry the recording machine's environment. A Phase 9 eval
  session ran `wrangler whoami` unprompted, and its output reached a public
  branch. Keep transcripts compressed under the record's `raw/` directory,
  which `.gitignore` excludes, and commit the summaries that cite them:
  results tables, tallies, classifications, reports. A citation into a
  transcript names the local archive. (Amended 2026-10-01, Phase 9.)
- Commit only what the record needs. A task brief that is a verbatim section of
  the committed plan is not copied. Keep a build log's result line and drop the
  rest. Keep one copy of byte-identical screenshots, and record the others'
  names in the record's README. (Amended 2026-10-01, Phase 9.)

## Subagents

- Directory: `plugins/apple-studio/agents/<name>.md`. Reviewer agents read the same reference files
  as the authoring skills, so review standards and authoring standards cannot drift.
  (No agents currently ship — cut Phase 5 per the kill-switch; see docs/deferred.md
  item 1 for the restore pointer.)
- Do not set `hooks`, `mcpServers`, or `permissionMode` in plugin agents (ignored when
  loaded from a plugin).

## Hooks

- Directory: `plugins/apple-studio/hooks/hooks.json` + `plugins/apple-studio/hooks/scripts/`.
- Scripts are referenced via `${CLAUDE_PLUGIN_ROOT}`; writable state goes to
  `${CLAUDE_PLUGIN_DATA}`.
- Every hook **fails open**: on script error, log a warning and allow the action.
  A broken hook must never block real work.
- Validate with the authoring-hooks validation script before committing.

## Formatting and linting

Deliberately not a hook. When a project contains `.swiftformat` or `.swiftlint.yml`,
run the corresponding tool after edits. This is a convention line, not machinery.

## Versioning and releases

- Version lives in `plugins/apple-studio/.claude-plugin/plugin.json` only (never duplicated in the
  marketplace entry). Bump per phase: 0.1.0 = Phase 0 scaffold, 0.2.0 = Phase 1, etc.
- Before any version bump: `claude plugin validate . --strict` passes from the repo
  root, and each new component demonstrably loads under `--plugin-dir`.

## The kill-switch rule

Any component that hasn't earned its context cost by the following phase — references
that never get loaded, skills that never fire, machinery nobody missed — gets cut or
merged. Deletion is a feature.
