---
name: setup
description: Sets up or reconciles this project's OpenSpec workflow — schemas and subagents for a chosen complexity level, a rewritten openspec/config.yaml that carries forward what the project already had, and guarded plugin installation. Use when the user runs /workflows:setup, asks to configure, adopt, update, or repair this repo's OpenSpec workflow, or wants to know how far the repo has drifted from the level it was set up at. Re-running is safe and is how a project takes updates; --check reports drift without writing.
disable-model-invocation: true
license: MIT
---

# Set up the OpenSpec workflow

`$ARGUMENTS` may carry a level — `minimal`, `standard`, or `advanced` — and one of
`--check` (report only, writes nothing) or `--dry-run` (writes only the plan JSON).

**Nothing is written before the user approves the plan.** No schemas, no agents, no
config, no settings, no scratch files in the repo. This command replaces a file the user
wrote, in a repository you are a guest in, so that gate is the whole safety model.

Two things stay off the table for the whole run, at every level:

- **Do not run `openspec config profile`.** It is machine-global: it changes the profile
  for every project on that machine, not just this one. Where the plan warns that the
  machine profile lacks a workflow this level uses, report the warning with the command
  the user would run, and leave the decision to them.
- **Do not pass `payloadRoot`** to `plan.mjs` or `buildPlan`. It is a test-only seam for
  pinning manifest composition order. A wrong path now throws rather than degrading to an
  empty but plausible plan, but nothing in a real run has any business planning against a
  payload other than this plugin's own.

## 1. Detect

```bash
REPO="$(git rev-parse --show-toplevel)"
node "${CLAUDE_PLUGIN_ROOT}/scripts/detect.mjs" "$REPO"
```

Read the JSON and use it as given — whether this repo is a web project, which schemas
already exist, which plugins the settings file has already decided, whether a previous
run happened. Do not re-derive any of it by hand, and do not ask the user about anything
already in it.

Capture the two tree hashes now, while nothing has touched them; step 9 needs this
before-picture to prove setup left the user's specs and changes alone:

```bash
node -e 'const {join}=require("node:path"),{pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({hashTree})=>console.log(JSON.stringify({specs:hashTree(join(process.argv[2],"openspec","specs")),changes:hashTree(join(process.argv[2],"openspec","changes"))})))' \
  "${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs" "$REPO"
```

## 2. Choose the level

If `$ARGUMENTS` named a level, use it and skip this section.

Otherwise: **form a recommendation from the repository first, then ask once.** This is the
only question setup asks, and a level is not something a newcomer can pick from counts of
schemas and artifacts — those numbers describe the levels without distinguishing them.

### 2a. Read the repository

Ask one question about the repository, not about the user. Sample the recent work:

```bash
git -C "$REPO" log --no-merges -n 40 --format='%s'
```

Sort those subjects into **kinds** — new capability, defect, structural cleanup, trivial
change, dependency bump, incident, open question, bootstrap — and count the kinds, not the
commits. Fold in what step 1 already detected: whether this is a web project, and whether
`openspec/` and its schemas are already here.

- **Two or three kinds, mostly features and defects** → `minimal` or `standard`.
- **Five or more kinds, especially dependency bumps or incidents** → `advanced`. Those two
  are the ones that get mangled when a repository only knows how to do features and bugs.
- **Between `minimal` and `standard`** — does work here usually start from an unclear idea
  that needs interviewing, or from a surface someone can already picture? Interview →
  `minimal`. Surface → `standard`. A repo detected as web leans `standard`, but the history
  outranks the detection: a web repo whose commits are mostly backend still interviews.
- **Too little history to count** — a fresh or near-empty repo — recommend `minimal` and
  say plainly that it is a default rather than a reading of their work.

### 2b. Ask, with the recommendation and the reason

One AskUserQuestion, three options. Each option is the level **name and what it is for** —
no schema counts, no artifact counts, no router column. Put the recommended level first and
mark it `(Recommended)`, and give the evidence in one clause: which kinds of work you
counted, and in how many commits.

| Level | What to say it is |
|---|---|
| `minimal` | `mattpocock-bridge` and `bugfix-flow`. Features and defects, where a piece of work usually starts as an unclear idea and an interview is what turns it into a plan |
| `standard` | `craft-driven` and `surface-driven`. The same two kinds of work, but it usually starts from a surface someone can already picture, so design leads and behaviour follows |
| `advanced` | Eight schemas and a router that picks between them — features, defects, cleanups, dependency bumps, incidents, spikes, bootstraps. For repositories where the work comes in too many kinds for one chain to fit |

Recommend; do not decide. If they pick another level, use it without arguing — **choosing
wrong is cheap.** Setup deletes nothing, so a later run at a different level adds that
level's schemas beside the first set and merges the run record rather than orphaning
anything.

For the numbers behind these — schemas, longest chain, router, plugin counts — see
`plugins/workflows/README.md`. They belong in the plan you present at step 3, not in the
question.

## 3. Build and present the plan

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/detect.mjs" "$REPO" \
  | node "${CLAUDE_PLUGIN_ROOT}/scripts/plan.mjs" "$LEVEL"
```

An unknown level exits non-zero with empty stdout: show its message and stop rather than
proceeding on a guess.

Render the plan for a human — not as raw JSON. Cover the mode (`fresh` or `reconcile`),
the detected web answer, every file that would be created or replaced, the `config.yaml`
backup path, which plugins install and which are skipped **with the reason**, the status
line decision, the probe change verification will create and remove, the human steps that
will remain, and every warning.

Schemas and agents each come in three groups, and the difference is the whole safety
story — say which is which, by name:

- `copy` — not there yet.
- `update` — a previous run of this plugin installed it and nobody has edited it since
  (`.claude/workflows.json` records the hash we wrote). Refreshing these is how a re-run
  takes updates.
- `collide` — the user's own file, or one of ours they have since changed. Never replaced
  unless they approve that specific name. Ask about each one individually; "approve all"
  is not an answer to this question.

A warning that `.claude/settings.json` could not be read invalidates the plugin and
status-line sections of the plan you are showing. Lead with it, and say plainly that the
choices in that file cannot be honoured until they fix it.

Then branch on the flags:

- `--check` — print the report and stop.
- `--dry-run` — write the plan JSON to `.claude/workflows-plan.json`, report where it
  went, and stop. That file is the only thing `--dry-run` writes.
- otherwise — ask the user to approve. Anything short of approval stops the run.

Save the approved plan JSON outside the repo (`"${TMPDIR:-/tmp}/workflows-plan.json"`)
and apply that exact plan. Re-running `plan.mjs` partway through apply replans against a
half-applied repo and would hand the user something they never approved.

## 4. Apply, in this order

Every `openspec` command below carries `OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1`, and none of
them may be run without both. Every subcommand runs a preAction hook that writes
`~/.config/openspec/config.json` on first use and POSTs to a third-party endpoint on every
use; the plugin's scripts already set these on every spawn they make, and the README tells
the user that **every** invocation this plugin makes sets them. Two of them are yours.

1. **`openspec init`, only if `openspec/` is absent.** Never over an existing directory:
   `init` has a legacy-cleanup path, and `--force` approves it non-interactively. The
   plan's `openspecInit` already answers this — follow it.

   ```bash
   OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec init --tools claude
   ```

   `--tools claude` is not optional: on a repo with no `.claude/` directory yet, bare
   `openspec init` exits with `No tools detected and no --tools flag provided` — and this
   is the first write of the run on the fresh-repo path.
2. **Schemas.** Copy `${CLAUDE_PLUGIN_ROOT}/payload/levels/$LEVEL/openspec/schemas/` into
   `openspec/schemas/` with `copyAdditive` from
   `${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs`. `overwrite` is `plan.schemas.update` —
   the ones a previous run of this plugin installed and nobody has edited since, which is
   how a re-run takes updates — plus any name from `plan.schemas.collide` the user
   approved individually. Never a name they did not approve.

   ```bash
   node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({copyAdditive})=>{require("node:fs").mkdirSync(process.argv[3],{recursive:true});console.log(JSON.stringify(copyAdditive(process.argv[2],process.argv[3],{overwrite:JSON.parse(process.argv[4])}),null,2))})' \
     "${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs" \
     "${CLAUDE_PLUGIN_ROOT}/payload/levels/$LEVEL/openspec/schemas" "$REPO/openspec/schemas" "$OVERWRITE_SCHEMAS"
   ```

   Then validate each schema copied or updated, and report each result:

   ```bash
   OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec schema validate "$NAME"
   ```
3. **Agents.** Same copy, same rule — `copyAdditive`, never `cp -R`. A subagent the user
   has customised is theirs: `plan.agents.collide` is reported, not replaced, and
   `overwrite` is `plan.agents.update` plus anything they approved by name.

   ```bash
   node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({copyAdditive})=>{require("node:fs").mkdirSync(process.argv[3],{recursive:true});console.log(JSON.stringify(copyAdditive(process.argv[2],process.argv[3],{overwrite:JSON.parse(process.argv[4])}),null,2))})' \
     "${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs" \
     "${CLAUDE_PLUGIN_ROOT}/payload/levels/$LEVEL/agents" "$REPO/.claude/agents" "$OVERWRITE_AGENTS"
   ```
4. **TOOLS.md.** Invoke `mapping-project-tooling`. Do this before the config, because the
   config text points at TOOLS.md and is worth less if it points at nothing.
5. **`openspec/config.yaml`.** See section 5 — it is the one destructive step.
6. **CLAUDE.md.** Invoke `managing-project-memory`. On `advanced`, let it decide where
   `ROUTING.md` belongs; the router only works from somewhere memory reliably loads it.
7. **Plugins.**

   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/install-plugins.mjs" < "$PLAN"
   ```

   This installs at project scope and records anything a managed marketplace blocks
   instead of failing the run — read its `installed` / `blocked` / `skipped` output and
   carry it into the report.
8. **Record the run.** This writes `.claude/workflows.json`: the level, this plugin's
   version, the date, and the hash of every schema and agent **this run owns**. It reads
   the approved plan on stdin and derives that set itself — `copy` plus `update`, for
   schemas and agents alike — so a mistyped list cannot make a file ours that the plan
   never said was:

   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/record.mjs" "$REPO" $APPROVED_COLLISIONS < "$PLAN"
   ```

   `$APPROVED_COLLISIONS` is optional and unquoted: zero or more plain, space-separated
   names the user approved replacing at the gate — the only thing here the plan cannot
   tell us, because approval happens after it is built. Each is honoured only if it
   actually appears in `plan.schemas.collide` or `plan.agents.collide`; anything else is
   reported as `ignored` and recorded for nothing. Pass no names when the user approved
   none. Never pass a name they declined: that would make their file ours, and the next
   run would replace it with no gate and no mention.

   The record merges into whatever is already there rather than replacing it, so a level
   switch does not orphan the files the previous level installed — they are still on disk
   and still ours, and returning to that level updates them instead of reporting a
   collision that never happened.

   This runs **before** verification, deliberately. Verification exits non-zero on a
   failed check, and a legitimately blocked plugin is one — so with the order reversed, a
   managed-marketplace repo would apply the whole payload and then never record it, and
   every file this run wrote would come back next time as the user's. The record states
   what we wrote; that is true whether or not the config reaches the model.
9. **Verify**, with the hashes from step 1 — file presence proves nothing here, because
   OpenSpec drops fields that fail validation and warns only to stderr:

   ```bash
   node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({verify})=>{const r=verify(process.argv[2],{before:JSON.parse(process.argv[3]),expectRules:JSON.parse(process.argv[4]),expectPlugins:JSON.parse(process.argv[5])});console.log(JSON.stringify(r,null,2));process.exit(r.ok?0:1)})' \
     "${CLAUDE_PLUGIN_ROOT}/scripts/verify.mjs" "$REPO" "$BEFORE_HASHES" "$EXPECT_RULES" "$EXPECT_PLUGINS"
   ```

   `$BEFORE_HASHES` is step 1's JSON verbatim, `$EXPECT_RULES` a JSON array of rule
   strings you actually wrote into `config.yaml`, and `$EXPECT_PLUGINS` the plan's
   `plugins.install` array — what the plan said would be installed, **not** what
   `install-plugins.mjs` reported installing. Feeding it the report would make the check
   assert that what install said it installed is installed, which cannot fail for the case
   it exists to catch: a plugin a managed marketplace blocked never enters that list. A
   blocked plugin failing this check is the correct outcome, and a failing check is a
   result to report, not an obstacle to route around.

## 5. Rewriting `openspec/config.yaml`

This is the one file replaced rather than merged. The user's existing file is **input**,
not the base — the level's `config.yaml.example` is the base, and the old file supplies
what is project-specific.

This step splits in two: `config-facts.mjs` supplies the facts below, and you supply the
judgment (what `context:` prose survives, what to fold in, what to prune, how to phrase a
rule). Never derive a fact yourself where a function exists for it — the point of pulling
these out of prose is that a wrong-by-hand union or a colliding backup path is exactly how
a user's own rule or config gets silently discarded (I4).

**Artifact ids.** Get the authoritative union from `artifactIds()` before classifying
anything. Never guess it, and never read it out of schema YAML — the CLI is the only
authority:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$REPO"
```

This prints `{ "ok", "ids", "error" }` and exits non-zero on failure. **If `ok` is
`false`, stop — do not classify a single rule, and report `error` to the user instead.**
A CLI failure never degrades to an empty or partial union: classifying against one would
silently mark every rule the user wrote as unmatched, discarding it from `rules:` — the
exact failure I4 forbids. On success, `ids` is the union across any schema this level
installs plus the built-in `spec-driven` ids (`proposal`, `specs`, `design`, `tasks`).

- **Back up** the existing file to the plan's `config.backupTo` path first. If that field
  is unexpectedly absent even though the file exists, get a fresh, collision-safe
  destination from `backupPath(configPath)` rather than inventing a filename by hand:

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({backupPath})=>console.log(backupPath(process.argv[2])))' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$OLD_CONFIG_PATH"
  ```

- `schema:` — the level's example wins. Choosing a level is choosing this.
- `context:` — start from the example, then fold in the project-specific facts from the
  old file. Prefer pointers over copies: an inline stack list is a second copy of
  TOOLS.md that nothing keeps in sync. `context` is injected into every artifact prompt
  and is capped at 50KB — before finalizing the text, check the real byte count rather
  than eyeballing it, since OpenSpec drops the entire field, silently, one byte past the
  cap:

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({contextSize})=>console.log(JSON.stringify(contextSize(process.argv[2]))))' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$CONTEXT_TEXT"
  ```

  Treat `capBytes` as a ceiling to stay far below, not a budget to spend. On a reconcile,
  regenerate the generic half from the example and preserve the project-specific slots.
- `rules:` — parse the old file's `rules:` map yourself (there is no YAML dependency in
  this plugin; reading and structuring it is judgment work), then classify it against the
  ids from the step above — never against "exists in the default schema":

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({classifyRules,commentBlock})=>{const {carried,unmatched}=classifyRules(JSON.parse(process.argv[2]),JSON.parse(process.argv[3]));console.log(JSON.stringify({carried,unmatched,commentBlock:commentBlock(unmatched)}))})' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$USER_RULES_JSON" "$KNOWN_IDS_JSON"
  ```

  `$USER_RULES_JSON` is the `rules:` map you parsed, as JSON; `$KNOWN_IDS_JSON` is the
  prior step's `ids` array, verbatim. This is a union across the installed set: a rule
  keyed to `diagnose` is valid at `minimal` because `bugfix-flow` defines it, even though
  that level's default schema is `mattpocock-bridge` — `classifyRules` carries it either
  way, because membership is checked against the whole union, not the default schema.
- **Unmatched ids** — never drop them, and never leave them under `rules:`, where OpenSpec
  warns about them on every command. The call above already rendered the trailing comment
  block via `commentBlock`; write its `commentBlock` string verbatim rather than
  hand-formatting the same shape yourself:

  ```yaml
  # Unmatched rules carried over from your previous config.yaml.
  # No installed schema defines these artifact ids, so they are kept here
  # rather than under `rules:`, where they would warn on every command.
  #   old-artifact-id:
  #     - "…the user's original text, verbatim…"
  ```

- `operations.*.guidance` — append the user's entries after the example's, unless they
  contradict each other; say so when they do rather than silently picking one.

**Invoke `improving-prompts` for the `context:` and `rules:` text you author here.** These
are not config values, they are prompts: `context` is injected into every artifact request
for the life of this project, and each rule into every matching one. Wording that is
merely acceptable costs tokens on every turn and misfires quietly.

Show the diff — carried over, dropped with the reason, unmatched — and get agreement
before writing the file.

## 6. Report

State plainly:

- what was created, updated, replaced, and backed up, with paths — and which schemas and
  agents were left alone because they are the user's, naming each;
- which plugins installed, which were skipped and why, and which were blocked and why —
  `install-plugins.mjs` reports the CLI's own stderr as the reason, not a guess, so pass it
  through verbatim rather than paraphrasing it into "blocked by managed settings";
  - A blocked reason containing `Permission denied (publickey)` or `git@github.com` is an
    SSH auth failure, not a managed-settings block, even though a marketplace add already
    prefers the plugin's own HTTPS URL to avoid exactly this. It still means the machine
    has no usable GitHub SSH key and something downstream (the `install` step itself, or a
    marketplace source this repo didn't define with a `github` source) fell back to SSH.
    Tell the user, in order:
    1. Add an SSH key to GitHub — <https://docs.github.com/authentication/connecting-to-github-with-ssh>.
    2. Or make git rewrite every SSH GitHub URL to HTTPS for this machine's subprocess
       clones: `git config --global url."https://github.com/".insteadOf git@github.com:`.
    3. If failures persist, install and authenticate the GitHub CLI
       (<https://cli.github.com>) — `gh auth login` — which git and `claude` can use as a
       credential helper for HTTPS clones.
    Then re-run `/workflows:setup` to retry the blocked plugin.
- every verification check and its result;
- the human steps that remain, which are the ones no agent can do:
  - `/mattpocock-skills:setup-matt-pocock-skills` — an interview only the user can
    answer; it writes `docs/agents/issue-tracker.md`. Re-running `/workflows:setup`
    afterwards folds that into `context:`.
  - `/impeccable init` on a web project — writes `PRODUCT.md` and `DESIGN.md`.
  - `/reload-plugins` to activate newly installed plugins in this session.
  - **Switch the output style**, after that reload: select `controlled-english` under
    `/config`. It ships with the `meta-skills` plugin, so it does not appear in the list
    until that plugin is active — which is why this step comes second, not first. Selecting
    a style is a user act; nothing here can do it, and it changes the register of every
    reply in the repository.
- the teammate line: "Anyone else cloning this repo should install the `workflows` plugin
  and run `/workflows:setup` — a committed `.claude/settings.json` does not install
  plugins for them."

Never report a step as succeeded without the command output that shows it.
