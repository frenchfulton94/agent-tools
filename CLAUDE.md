# agent-tools

A Claude Code plugin marketplace. Ten plugins under `plugins/`, published
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
