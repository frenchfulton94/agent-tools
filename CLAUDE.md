# agent-tools

A Claude Code plugin marketplace. Ten plugins under `plugins/`, published
through `.claude-plugin/marketplace.json`.

## Layout

- `plugins/<name>/` — what installs. Nothing an installer does not need goes
  here; the directory is the install unit.
- `authoring/<plugin>/` — dev-time tooling for one plugin. Never installed.
- `tests/` — the pinned contract. `bun test`.
- `.agents/skills/` — copies of skills whose source is `plugins/*/skills/`
  (`skills-lock.json` records which); `.claude/skills/*` symlinks into them.
  **Edit the `plugins/` copy.** An edit under `.claude/skills/` or
  `.agents/skills/` ships nothing, and only `bun test` catches it.

## Verify

Both must pass before any commit that touches `plugins/`:

- `bun test` — registration both ways, name against directory, skill-name
  uniqueness across the catalog, that every plugin has a README row linking to
  a real directory, the security eval roster, `.agents/skills/` against its
  sources.
- `bun run audit` — the vendored validators over every skill, plugin, agent,
  and hook, plus the README's skills column (that each plugin's shipped skills
  are all listed in its row — `bun test` checks the row exists and links
  correctly, not its contents). Exits non-zero on errors only.

**A third command is required for commits touching `plugins/godot/`:**
`bun run test:engine` (~23s). The godot plugin's Python suite is split — the
tests that drive the real engine are gated behind `GODOT_SKIP_ENGINE_TESTS`,
which `bun test` sets, because unsplit they were ~38s of a ~40s gate. `bun test`
still makes one real `--check-only` as a smoke check, and fails if the gate
stops skipping, but it does not run the 33 engine-gated tests. Skipping
`test:engine` on a godot change means shipping untested engine behaviour.

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

The one plugin with its own authoring pipeline. Read
`authoring/apple-studio/CONVENTIONS.md` before editing a skill or reference
under `plugins/apple-studio/`; `.claude/rules/apple-studio.md` carries the
pipeline rules and loads with those files.

Two that fire at phase end, after a path-scoped rule may have been compacted
away:

- A phase writes its record to
  `authoring/apple-studio/records/<date>-phaseN-<slug>/`.
- Tags are namespaced: `apple-studio-v0.9.0`, never a bare version.
