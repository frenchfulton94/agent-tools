# `workflows` plugin resources

Ordered by trust. The plugin source outranks every document below it, including this
repository's own design records and the upstream docs: schemas and scripts are what
actually run.

## Knowledge — primary (this repository)

- [`plugins/workflows/skills/setup/SKILL.md`](../skills/setup/SKILL.md)
  The setup procedure itself: detect → one question → plan → approve → apply in nine
  ordered steps, plus the `config.yaml` rewrite rules. Use for: anything about what
  `/workflows:setup` does, in what order, and what it refuses to do.
- [`plugins/workflows/README.md`](../README.md)
  The user-facing contract: install, levels table, the five "will not do" guarantees, the
  human steps, and an unusually honest verification-and-limits section. Use for: the
  short answer, and for what is *not* proven end to end.
- [`plugins/workflows/payload/levels/*/openspec/schemas/*/schema.yaml`](../payload/levels)
  All twelve workflows. Each artifact's `id`, `generates`, `description`, `template`,
  `instruction`, and `requires`. Use for: what an artifact actually asks of you — the
  `instruction` field is the real prompt, and no summary replaces reading it.
- [`plugins/workflows/payload/levels/advanced/openspec/ROUTING.md`](../payload/levels/advanced/openspec/ROUTING.md)
  The eight-branch decision tree, the prompt-signal table, and the escalation guardrails.
  Use for: routing, and for the exact wording to quote when a route is contested.
- [`plugins/workflows/payload/levels/*/agents/*.md`](../payload/levels)
  The eight subagents, each pinning `model:` and `effort:` in frontmatter. Use for:
  model and effort decisions — these are the only model recommendations in this plugin
  that execute rather than advise.
- [`plugins/workflows/payload/levels/*/openspec/config.yaml.example`](../payload/levels)
  The `context:` and per-artifact `rules:` each level ships. Use for: what reaches the
  model on every request versus only on one artifact.
- [`plugins/workflows/skills/configuring-openspec/`](../skills/configuring-openspec)
  Five reference files on OpenSpec's configuration surfaces, verified against v1.9.0
  source rather than only its docs. Use for: `config.yaml` fields and limits, schema
  authoring, the CLI, the day-to-day loop, and symptom-first troubleshooting.

## Knowledge — this repository's design record

Corroborating, not authoritative. Read for *why*, never for *what*.

- [`docs/ideas/workflows-plugin.md`](../../../docs/ideas/workflows-plugin.md)
  The problem statement and the one distinction the design turns on: not code vs. prose,
  but *when the guidance has to fire*. Use for: explaining to a teammate why schemas are
  copied into the repo while reference prose stays in the plugin.
- [`docs/superpowers/specs/2026-08-27-workflows-plugin-design.md`](../../../docs/superpowers/specs/2026-08-27-workflows-plugin-design.md)
  The design spec, including the numbered invariants (I1–I6) the README cites. Use for:
  what each invariant claims and which test proves it.
- [`docs/superpowers/notes/2026-08-27-workflows-plugin-research.md`](../../../docs/superpowers/notes/2026-08-27-workflows-plugin-research.md)
  Research notes behind the design. Use for: alternatives considered and rejected.

## Knowledge — upstream

- [OpenSpec docs](https://github.com/Fission-AI/OpenSpec/tree/main/docs)
  The CLI and `/opsx` command set this plugin configures. Highest-value pages:
  [`opsx.md`](https://github.com/Fission-AI/OpenSpec/blob/main/docs/opsx.md) (the command
  table and the update-vs-start-fresh heuristics),
  [`customization.md`](https://github.com/Fission-AI/OpenSpec/blob/main/docs/customization.md)
  (schemas and templates),
  [`commands.md`](https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md)
  (core vs. expanded command sets),
  [`concepts.md`](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md).
  Use for: anything about OpenSpec itself rather than this plugin's opinions about it.
- [`skills/openspec-onboard/SKILL.md`](https://github.com/Fission-AI/OpenSpec/tree/main/skills/openspec-onboard)
  Upstream's own guided first-cycle walkthrough, phase-structured with a preflight and
  graceful-exit handling. Use for: the shape a teaching skill should take, and as a
  second opinion on the day-one loop.
- [mattpocock/skills](https://github.com/mattpocock/skills)
  The pack `minimal` depends on. Authoritative for skill *names* — the published summary
  page paraphrases several of them incorrectly. Its
  [`ask-matt`](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md)
  is the model for a router that recommends and stops.
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
  The pack `advanced` installs. Use for: confirming a skill the schemas call by name
  (`code-simplification`, `debugging-and-error-recovery`, `performance-optimization`,
  `source-driven-development`, `deprecation-and-migration`) still exists.
- [obra/superpowers](https://github.com/obra/superpowers)
  The pack `standard` installs — brainstorming, TDD, written plans, subagent execution,
  code review, evidence-first verification. Use for: what `craft-driven` hands off to.
- [Impeccable](https://impeccable.style/llms.txt)
  The design skill both UI-touching schemas call. Writes `PRODUCT.md` and `DESIGN.md`;
  `/impeccable init` is one of the human steps setup cannot do. Use for: what
  `design-brief` and `surface` are reaching for.
- [taste-skill](https://www.tasteskill.dev/llms.txt)
  Installed on web projects at `advanced`. Anti-generic-UI rules with three dials. Use
  for: what `taste-preflight` is checking against.

## Knowledge — attached usage guides

Three, supplied as usage guides for the workflows, all treated as secondary. Read the
caveats: one of them does not apply to this harness at all.

- **`mattpocock-superpowers-schema-model-effort.md`** — model and effort per artifact for
  `craft-driven`, `surface-driven`, `mattpocock-bridge`, and `bugfix-flow`, in Claude
  model names. Agrees with the subagent frontmatter in source almost line for line. Use
  for: the `minimal` and `standard` levels' model decisions.
- **`compass_artifact_wf-292569d9…md`** — a 16-row routing table over the `advanced`
  level's eight schemas × two phases. **Its model column is DeepSeek V4 under OpenCode, not
  Claude under Claude Code.** Superseded for model choice by the subscription-tier guide
  below. Use only for the depth-follows-artifact reasoning and the phase split; do not
  carry its model IDs, effort names, prices, or its `reasoning_content` bug into a Claude
  Code session.
- **`compass_artifact_wf-45f4a136…md`** — per-schema, per-phase model and effort for the
  `advanced` eight in Claude model names, across Pro / Max 5x / Max 20x, plus the
  burn-control primitives (`opusplan`, `/usage`, effort defaults, `ANTHROPIC_API_KEY`) and
  the resolution-order and Fable caveats. **This is the guide that closes the model gap for
  the `advanced` level.** Its routing content agrees with the shipped agent pins. Its usage
  limits, prices and promotional windows are dated and unverified here — treat them as
  directional and check `/usage` and Anthropic's own pages instead. One of its
  recommendations, `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5`, must **not** be followed in
  a repository this plugin configured — see
  [[0005-tier-guide-closes-the-model-gap]].

## Wisdom (communities)

- [OpenSpec Discussions](https://github.com/Fission-AI/OpenSpec/discussions) and
  [Issues](https://github.com/Fission-AI/OpenSpec/issues)
  Where schema, archive, and CLI behaviour gets settled by the maintainers. Use for:
  confirming a CLI behaviour before treating it as fixed, and for reporting a schema
  contract that archives without merging.
- [mattpocock/skills issues](https://github.com/mattpocock/skills/issues)
  Active, and the pack changes fast. Use for: whether a skill was renamed before blaming
  a schema that calls it by the old name.
- [Anthropic Discord](https://discord.gg/anthropic) — Claude Code channels
  Use for: model and effort behaviour questions, and subagent frontmatter surprises.
- Internal: whoever maintains these repos
  The highest-value community for this mission, because it is the one that will actually
  run these repos. Use for: contested routes, and for whether a level is right for a
  given project. Record settled disputes as a learning record.

## Gaps

- ~~**No Claude-model recommendation exists for the `advanced` level's eight schemas.**~~
  **Closed 2026-08-28** by the subscription-tier guide, which supplies all eight schemas ×
  two phases in Claude model names plus a per-tier adaptation. Lesson 12 and the model card
  now carry the real table; what still needs judgement is the four premium cells and the
  tier deltas.
- **No absolute usage figures exist.** Anthropic publishes relative multipliers only, so
  every hours-per-week or tokens-per-window number in the tier guide is dated or
  third-party estimation. Nothing in this package budgets against them, and neither should
  a reader.
- **Fable's weekly weight is community math, not a published formula.** The "roughly twice
  an Opus session" figure shapes the Max-tier advice and cannot be verified from here.
- **No end-to-end proof of the setup skill's own orchestration.** The README says so
  plainly: `claude -p --plugin-dir` cannot drive it, and the prose has been reviewed, not
  executed. There is no recording or transcript of a real run to learn from.
- **No Windows evidence.** The `%APPDATA%` config path is reasoned from the CLI source and
  has never been run on Windows.
- **No worked example of the `config.yaml` rewrite** — the one destructive step — with a
  real before/after and a real unmatched-rules comment block. Lesson 03 builds one from
  the functions in `config-facts.mjs` rather than citing a source that does not exist.
