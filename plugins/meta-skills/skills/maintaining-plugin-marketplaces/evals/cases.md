# Behavior test cases: maintaining-plugin-marketplaces

Run each case with the skill and without (baseline), clean context per run, working directory set to a marketplace repository.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Audit the catalog (must-pass set)

**Prompt:** "Is this marketplace healthy? Have a look and tell me what needs fixing."

**Assertions:**
1. The vendored `validate_*.ts` validators were actually run over the corpus, not merely mentioned as available.
2. The stale plugin README is reported by path, with what is wrong in it. (Baselines reliably fail this: `bun test` passes, so a green suite is reported as a healthy catalog. Nothing loads a plugin README, so nothing surfaces it.)
3. The existing test suite was run, and its coverage is credited rather than re-derived by hand as a manual checklist.
4. Findings are reported before any file is edited.
5. Each finding names the consequence — who experiences it and when — not only the rule it breaks.
6. Nothing is reported as a finding that the suite already pins and that currently passes (no invented drift).
7. If the catalog is sound in some dimension, that is stated plainly rather than padded with speculative findings.

## Case 2 — Add a skill

**Prompt:** "I've written a skill that lints our Tailwind class ordering. Add it to this marketplace."

**Assertions:**
1. The placement question is answered explicitly — which plugin, and why that plugin's installers would want this — before anything is created.
2. The answer is a plugin that already exists, or a stated reason why no existing plugin shares that audience. (Baselines reliably fail this: a new plugin is scaffolded by default because it is the locally simpler move.)
3. The skill name is checked for collision against every skill already in the catalog.
4. The plugin's version is bumped, and in every place that records it — `plugin.json`, the marketplace entry, and the README cell if it quotes one.
5. The README's skills column is updated.
6. The suite is run afterward, and any failure it produces is read and explained rather than worked around by editing the assertion.
7. The response does not claim the change is live without having confirmed it — no "users will now get it" absent a version bump.

## Case 3 — The request whose right answer is "don't"

**Prompt:** "Rename the `meta-skills` plugin to `Agent Tooling` — it reads better in the plugin list."

**Assertions:**
1. The response distinguishes the display label from the install identifier rather than treating this as a single change.
2. `displayName` is proposed as the fix, with `name` left alone.
3. The consequence of renaming `name` is stated concretely: existing `enabledPlugins` and `pluginConfigs` entries and every install command break.
4. If a `name` change is pursued anyway at the user's direction, a `renames` entry is added mapping the old name to the new one, and it is described as append-only history.
5. `Agent Tooling` is not silently accepted as a `name` value — it is neither kebab-case nor a legal identifier. (Baselines reliably fail this: the rename is performed as asked, in one place, with no migration and no note that installs will break.)
6. The plugin's own README is included in the list of things a rename touches.
