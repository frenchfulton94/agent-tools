# Change procedures

Contents:
- [Add a skill to an existing plugin](#add-a-skill-to-an-existing-plugin)
- [Add a plugin](#add-a-plugin)
- [Move a skill between plugins](#move-a-skill-between-plugins)
- [Rename a plugin](#rename-a-plugin)
- [Retire a plugin](#retire-a-plugin)
- [Cut a release](#cut-a-release)

Every procedure below ends the same way: run the suite and the sweep, and bump the version if
behavior changed. That last clause is the one people skip, and it is the one that decides whether
anyone receives the change.

## Add a skill to an existing plugin

Choose the plugin before writing anything — `references/curation.md` covers the call. Then:

- Create `plugins/<plugin>/skills/<skill>/SKILL.md`, frontmatter `name` matching the directory.
- Confirm the name is unique across every plugin. Two plugins shipping one skill name leaves which
  copy wins undefined, and the loser goes on being edited by someone who believes it is live.
- Add the skill to the plugin's skills cell in the marketplace README.
- Bump the plugin's version in `plugin.json`, the marketplace entry, and the README cell if it
  quotes one. A new skill is new behavior.
- Run the suite. In a repository whose evals record a competitor lineup, adding a skill can fail a
  lineup assertion by design — read the failure, which names the two valid answers, rather than
  editing the assertion.

## Add a plugin

- Create `plugins/<name>/` with `.claude-plugin/plugin.json`. That directory holds the manifest and
  nothing else; component directories (`skills/`, `agents/`, `hooks/`, `commands/`) sit at the
  plugin root. Components placed inside `.claude-plugin/` produce the most common failure report
  there is: the plugin installs, appears in `/plugin`, and none of its components exist.
- Register it in `marketplace.json` with a `source` of `./plugins/<name>`, a `category`, a
  `description`, and a `version` matching the manifest.
- Add a README row: link, skills, and the same description text used in the other two files.
- Reload and confirm it appears — `/plugin marketplace update` for a local marketplace, then check
  the plugin lists at the version you set.

## Move a skill between plugins

A move is a delete and an add, and it changes which install a user needs to get that skill. Treat it
as user-visible.

- Move the directory, then update both plugins' README cells.
- Bump both plugins: the source lost behavior, the destination gained it.
- Say so in the release note. A user who installed the source plugin for that one skill will lose it
  on their next update with no other signal.

There is no redirect mechanism for skills the way `renames` covers plugins. If the move would strand
a meaningful number of users, keeping the skill where it is and fixing the description is often the
better call.

## Rename a plugin

`name` is the identifier users carry in `enabledPlugins`, `pluginConfigs`, and every install command.
Changing it breaks all of them.

- If the goal is only a nicer label, set `displayName` and stop. `name` stays.
- Otherwise: change `name` in `plugin.json` and the marketplace entry, rename the directory, update
  `source`, and update the README row and links.
- Add a `renames` entry at the top level of `marketplace.json` mapping the old name to the new one.
  Without it, existing users see `plugin-not-found`.
- Update that plugin's own README — its title, its install command, its `--plugin-dir` path. Nothing
  loads this file, so nothing will tell you it is now wrong.

```json
{
  "renames": { "formatter": "code-formatter", "legacy-linter": null }
}
```

`renames` is append-only history. Keep entries after everyone has migrated; a later rename adds a
second entry rather than editing the first, and Claude Code follows the chain. A remote-sourced
plugin reports `plugin-cache-miss` after a rename and needs one `/plugin install` to refetch.

## Retire a plugin

- Remove the entry from `plugins`, and the directory if it is not being kept for history.
- Map the old name to `null` in `renames`. Users then see that it was removed instead of an error.
- Remove its README row.
- Say in the release note what replaces it, if anything.

## Cut a release

- Every plugin whose behavior changed has a new version in `plugin.json`, the marketplace entry, and
  its README cell. `bun scripts/audit_marketplace.ts . --since <last-release-ref>` names the ones
  that were missed.
- The suite and the sweep both pass.
- Descriptions still describe what each plugin now contains — a plugin that gained a component
  usually needs its blurb rewritten in all three places at once.
- Confirm delivery rather than assuming it: update the marketplace and check the new version is what
  installs. A version that did not move ships nothing, silently.
