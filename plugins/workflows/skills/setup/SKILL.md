---
name: setup
description: Sets up or reconciles this project's OpenSpec workflow — the seven -flow schemas, their router and design subagent, a rewritten openspec/config.yaml that carries forward what the project already had, and guarded installation of the three plugins the flows call (mattpocock-skills, agent-skills, impeccable). Use when the user runs /workflows:setup, asks to configure, adopt, update, or repair this repo's OpenSpec workflow, or wants to know how far the repo has drifted from what setup installed. Re-running is safe and is how a project takes updates; --check reports drift without writing.
disable-model-invocation: true
license: MIT
---

# Set up the OpenSpec workflow

`$ARGUMENTS` may carry `--check` (report only, writes nothing) or `--dry-run` (writes only
the plan JSON). There is one workflow and no level to choose. If `$ARGUMENTS` names
`standard` or `advanced`, say that those levels were removed in 0.10.0 and that setup now
installs the one workflow, then carry on.

Setup installs OpenSpec's project files, the workflow, and the three plugins its flows
call. It installs nothing else: no general-purpose plugins, no stack-specific layers.

**Nothing is written before the user approves the plan.** No schemas, no agents, no
config, no settings, no scratch files in the repo. This command replaces a file the user
wrote, in a repository you are a guest in, so that gate is the whole safety model.

Two things stay off the table for the whole run:

- **Do not run `openspec config profile`.** It is machine-global: it changes the profile
  for every project on that machine, not just this one. Where the plan warns that the
  machine profile lacks a workflow the flows use, report the warning with the command
  the user would run, and leave the decision to them.
- **Do not pass `payloadRoot`** to `buildPlan`. It is a test-only seam. A wrong path
  throws rather than degrading to an empty but plausible plan, but nothing in a real run
  has any business planning against a payload other than this plugin's own.

## 1. Detect

```bash
REPO="$(git rev-parse --show-toplevel)"
node "${CLAUDE_PLUGIN_ROOT}/scripts/detect.mjs" "$REPO"
```

Read the JSON and use it as given — which schemas and agents already exist, which plugins
the settings file has already decided, the machine's OpenSpec profile, whether a previous
run happened and at what level. Do not re-derive any of it by hand, and do not ask the
user about anything already in it.

Capture the two tree hashes now, while nothing has touched them; step 8 needs this
before-picture to prove setup left the user's specs and changes alone:

```bash
node -e 'const {join}=require("node:path"),{pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({hashTree})=>console.log(JSON.stringify({specs:hashTree(join(process.argv[2],"openspec","specs")),changes:hashTree(join(process.argv[2],"openspec","changes"))})))' \
  "${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs" "$REPO"
```

## 2. Build and present the plan

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/detect.mjs" "$REPO" \
  | node "${CLAUDE_PLUGIN_ROOT}/scripts/plan.mjs"
```

`plan.mjs` takes no argument. A non-zero exit with empty stdout is a failure: show its
message and stop rather than proceeding on a guess.

Render the plan for a human — not as raw JSON. Cover the mode (`fresh` or `reconcile`),
every file that would be created or replaced, the `config.yaml`
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
- `retire` — names this plugin used to ship and no longer does, from `retired.json`: the
  old bridge schema, and every schema and agent of the `standard` and `advanced` levels
  removed in 0.10.0. `retire.*.retire` lists the ones safe to delete: recorded as ours,
  unedited, and used by no open change. `retire.*.keep` lists the rest, each with its
  reason. Name both. A repository that was set up at a removed level also gets a warning
  saying so; lead the retire section with it, and make clear that declining every
  deletion is a complete answer — those schemas keep working, they just stop updating.

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

## 3. Apply, in this order

Every `openspec` command below carries `OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1`, and none of
them may be run without both. Every subcommand runs a preAction hook that writes
`~/.config/openspec/config.json` on first use and POSTs to a third-party endpoint on every
use; the plugin's scripts already set these on every spawn they make, and the README tells
the user that **every** invocation this plugin makes sets them. Two of them are yours.

1. **`openspec init`, only if `openspec/` is absent.** Never over an existing directory:
   `init` has a legacy-cleanup path, and `--force` approves it non-interactively. The
   plan's `openspecInit` already answers this — follow it.

   ```bash
   OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec init --scope project --tools claude
   ```

   Neither flag is optional. `--scope project` puts OpenSpec's skills in this repository
   (`.agents/skills/`, linked from `.claude/skills/`), where they are committed and
   travel with it. Without it, OpenSpec 2.x installs them into `~/.agents/skills` and
   `~/.claude/skills` for every project on the machine — a machine-wide write from a
   project command, which is the thing this skill does not do. `--tools claude`: on a
   repo with no `.claude/` directory yet, bare `openspec init` exits with
   `No tools detected and no --tools flag provided` — and this is the first write of the
   run on the fresh-repo path.

   `init` also writes a default `openspec/config.yaml`. The plan was built before it
   existed, so it says `create`; treat step 4 as a replace and back that file up like any
   other.
2. **Schemas.** Copy `${CLAUDE_PLUGIN_ROOT}/payload/openspec/schemas/` into
   `openspec/schemas/` with `copyAdditive` from
   `${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs`. `overwrite` is `plan.schemas.update` —
   the ones a previous run of this plugin installed and nobody has edited since, which is
   how a re-run takes updates — plus any name from `plan.schemas.collide` the user
   approved individually. Never a name they did not approve.

   ```bash
   node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({copyAdditive})=>{require("node:fs").mkdirSync(process.argv[3],{recursive:true});console.log(JSON.stringify(copyAdditive(process.argv[2],process.argv[3],{overwrite:JSON.parse(process.argv[4])}),null,2))})' \
     "${CLAUDE_PLUGIN_ROOT}/scripts/lib/tree.mjs" \
     "${CLAUDE_PLUGIN_ROOT}/payload/openspec/schemas" "$REPO/openspec/schemas" "$OVERWRITE_SCHEMAS"
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
     "${CLAUDE_PLUGIN_ROOT}/payload/agents" "$REPO/.claude/agents" "$OVERWRITE_AGENTS"
   ```

   **Then retired names, schemas first.** Leave every `plan.retire.*.keep` entry alone and
   report its reason. Ask about each name in `plan.retire.schemas.retire` individually,
   and delete only the ones the user approves:

   ```bash
   rm -r "$REPO/openspec/schemas/${NAME:?}"     # an approved retired schema
   ```

   Then the agents. If any retired schema stays, whether the user declined it or it is in
   `plan.retire.schemas.keep`, do not offer the retired agents: the old schemas dispatch
   them. Keep every retired agent and tell the user why. Otherwise ask about each name in
   `plan.retire.agents.retire` individually, and delete only the ones the user approves:

   ```bash
   rm "$REPO/.claude/agents/${NAME:?}"          # an approved retired agent file
   ```

   Step 7 drops the deleted names from the record by itself.
4. **`openspec/config.yaml`.** See section 4 — it is the one destructive step.
5. **Router and CLAUDE.md.** Install the router at `openspec/ROUTING.md`: copy
   `${CLAUDE_PLUGIN_ROOT}/payload/openspec/ROUTING.md` when the file is absent; when it
   exists and differs, show the diff and replace it only if the user approves. Then make
   sure memory loads the router: when `CLAUDE.md` (or `AGENTS.md`, if that is what the
   repository uses) has no line naming `openspec/ROUTING.md`, show the user this one line
   and add it only if they approve, creating the file when there is none:

   ```
   Before creating an OpenSpec change, read openspec/ROUTING.md and name the schema it picks.
   ```

   Add nothing else to that file. The router only works from somewhere memory reliably
   loads it.
6. **Plugins.**

   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/install-plugins.mjs" < "$PLAN"
   ```

   This installs at project scope and records anything a managed marketplace blocks
   instead of failing the run — read its `installed` / `blocked` / `skipped` output and
   carry it into the report.
7. **Record the run.** This writes `.claude/workflows.json`: this plugin's
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

   The record merges into whatever is already there rather than replacing it, so the
   files a removed level installed stay recorded as ours. That record is what lets a
   later run offer them for retirement instead of mistaking them for the user's own.

   Retired names step 3 deleted leave the record; a retired name the user kept is still
   on disk, so it stays recorded as ours.

   This runs **before** verification, deliberately. Verification exits non-zero on a
   failed check, and a legitimately blocked plugin is one — so with the order reversed, a
   managed-marketplace repo would apply the whole payload and then never record it, and
   every file this run wrote would come back next time as the user's. The record states
   what we wrote; that is true whether or not the config reaches the model.
8. **Verify**, with the hashes from step 1 — file presence proves nothing here, because
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

## 4. Rewriting `openspec/config.yaml`

This is the one file replaced rather than merged. The user's existing file is **input**,
not the base — `${CLAUDE_PLUGIN_ROOT}/payload/openspec/config.yaml.example` is the base,
and the old file supplies what is project-specific.

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
exact failure I4 forbids. On success, `ids` is the union across every schema installed in
this repository plus the built-in `spec-driven` ids (`proposal`, `specs`, `design`,
`tasks`). A schema from a removed level that is still on disk still counts, so its rules
carry.

- **Back up** the existing file to the plan's `config.backupTo` path first. If that field
  is unexpectedly absent even though the file exists, get a fresh, collision-safe
  destination from `backupPath(configPath)` rather than inventing a filename by hand:

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({backupPath})=>console.log(backupPath(process.argv[2])))' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$OLD_CONFIG_PATH"
  ```

- **Every other top-level key** — `skillsScope`, `store`, `references`, and anything else
  the old file carries besides `schema`, `context`, `rules`, and `operations` — goes
  into the new file verbatim. The example has none of them, and dropping one changes
  where OpenSpec looks for skills or specs without a word.
- `schema:` — the example wins: `feature-flow`. On a repository coming from a removed
  level this changes the default for new changes; say so in the diff.
- `context:` — start from the example, then fold in the project-specific facts from the
  old file. Prefer pointers over copies: an inline list of commands or stack facts is a
  second copy of the repository's manifests that nothing keeps in sync. `context` is injected into every artifact prompt
  and is capped at 50KB — before finalizing the text, check the real byte count rather
  than eyeballing it, since OpenSpec drops the entire field, silently, one byte past the
  cap:

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({contextSize})=>console.log(JSON.stringify(contextSize(process.argv[2]))))' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$CONTEXT_TEXT"
  ```

  Treat `capBytes` as a ceiling to stay far below, not a budget to spend. On a reconcile,
  regenerate the generic half from the example and preserve the project-specific slots.
- **Text the previous release shipped** — parse the old file's `rules:` map and its
  `operations.*.guidance` lists yourself (there is no YAML dependency in this plugin;
  reading and structuring them is judgment work). A file an earlier run wrote still holds
  that release's example text, which reads as the user's own unless it is split out first:
  carried forward, an old rule fires in flows it was never written for. Split both maps
  against `retired.json` before the two steps below touch them:

  ```bash
  node -e 'const fs=require("node:fs"),{pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({splitRetiredConfig})=>{const p=process.argv[2],retired=fs.existsSync(p)?JSON.parse(fs.readFileSync(p,"utf8")).config:null;console.log(JSON.stringify(splitRetiredConfig({rules:JSON.parse(process.argv[3]),guidance:JSON.parse(process.argv[4])},retired),null,2))})' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "${CLAUDE_PLUGIN_ROOT}/payload/retired.json" "$OLD_RULES_JSON" "$OLD_GUIDANCE_JSON"
  ```

  `$OLD_RULES_JSON` is the old `rules:` map as JSON; `$OLD_GUIDANCE_JSON` maps each
  operation to its `guidance` list, as in `{"apply":["…"]}`, or is `{}`. A line is dropped
  only on an exact match with text a previous release's example shipped. Only the two
  `kept` maps go on. Name every `dropped` line, verbatim, in the diff below and in the
  report as "dropped: shipped by a previous release"; if the user asks to keep one, move
  it back into `kept`.
- `rules:` — classify `rules.kept` from the split above against the ids from the
  artifact-id step — never against "exists in the default schema":

  ```bash
  node -e 'const {pathToFileURL}=require("node:url");import(pathToFileURL(process.argv[1]).href).then(({classifyRules,commentBlock})=>{const {carried,unmatched}=classifyRules(JSON.parse(process.argv[2]),JSON.parse(process.argv[3]));console.log(JSON.stringify({carried,unmatched,commentBlock:commentBlock(unmatched)}))})' \
    "${CLAUDE_PLUGIN_ROOT}/scripts/config-facts.mjs" "$USER_RULES_JSON" "$KNOWN_IDS_JSON"
  ```

  `$USER_RULES_JSON` is `rules.kept`, as JSON; `$KNOWN_IDS_JSON` is the
  artifact-id step's `ids` array, verbatim. This is a union across the installed set: a rule
  keyed to `diagnose` is valid because `bugfix-flow` defines it, even though the default
  schema is `feature-flow` — `classifyRules` carries it either way, because membership is
  checked against the whole union, not the default schema.
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

- `operations.*.guidance` — append `guidance.kept` after the example's entries, unless
  they contradict each other; say so when they do rather than silently picking one.

**Write the `context:` and `rules:` text you author here as prompts, not config values.**
`context` is injected into every artifact request for the life of this project, and each
rule into every matching one. State each thing once, plainly, as an instruction; wording
that is merely acceptable costs tokens on every turn and misfires quietly.

Show the diff — carried over, dropped with the reason, unmatched — and get agreement
before writing the file.

## 5. Report

State plainly:

- what was created, updated, replaced, backed up, and retired, with paths — and which
  schemas and agents were left alone because they are the user's, naming each;
- each `config.yaml` line dropped as "dropped: shipped by a previous release", verbatim;
- on a repository that was set up at a removed level: which of its schemas and agents
  were retired, which were kept and why, and that the plugins it enabled were left alone;
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
  - `/impeccable init` on a project with a user interface — an interview that writes
    `PRODUCT.md`. The flows send all surface work through impeccable, and it asks for
    this first. A project with no user interface skips it.
  - `/reload-plugins` to activate newly installed plugins in this session.
- the teammate line: "Anyone else cloning this repo should install the `workflows` plugin
  and run `/workflows:setup` — a committed `.claude/settings.json` does not install
  plugins for them."

Never report a step as succeeded without the command output that shows it.
