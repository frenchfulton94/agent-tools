# TOOLS.md

Canonical map of this project's stack, commands, and agent capabilities. Every entry
cites the file it came from. Read this before changing dependencies, scripts, build
config, test setup, or deployment.

Last verified: [YYYY-MM-DD] against [commit sha, or "working tree"]

<!-- TEMPLATE: replace every [bracketed] placeholder with a fact you read in a file,
     delete rows the repo has no evidence for, and delete these comments before saving.
     Do not keep a row you could not source. -->

## How to use this file

- Prefer what is listed here over ecosystem defaults, even when something else is more common elsewhere.
- Run every command with the package manager named below.
- If a capability is already covered by a dependency listed here, use it. Propose additions before installing anything new.
- Where a local wrapper module is listed for a dependency, import the wrapper rather than the dependency directly.
- Check Agent capabilities before starting a task. Prefer a listed skill, MCP server, or subagent over improvising the same work by hand.
- If this file disagrees with the manifest, lockfile, or config, the repo wins: verify against those files, then correct this one as part of your change.
- Anything under Unknowns is genuinely unresolved. Check the repo or ask; do not fill it with a default.

## Package manager

- **Manager:** [name and version] — evidence: [lockfile, `packageManager` field]
- **Install:** `[command]`
- **Add a dependency:** `[command]`
- **Run a script:** `[command]`
- **Do not use:** [the other managers for this ecosystem] — the committed lockfile is [lockfile]

## Runtime

- **[Language] version:** [x.y] — evidence: [.nvmrc, engines, go.mod, .python-version]
- [Other runtime facts the config establishes: container base image, target platform.]

## Layout and conventions

- **Framework:** [name and version] — evidence: [manifest entry and config file]
- **Entry points / routing:** [the convention actually in use] — evidence: [directories that exist]
- **New code goes in:** [paths]
- **Do not create:** [the sibling convention this project does not use]

## Key dependencies

<!-- One subsection per capability the project actually has: UI, data and auth, state,
     validation, background jobs. Delete the ones that do not apply. -->

### [Capability]

- **Package:** `[name]` `[version]` — evidence: [manifest, and the version the lockfile resolved]
- **Local wrapper:** [path and what it exports, or "none"]
- [One line of usage policy, only where the repo establishes one.]

## Commands

<!-- Only commands that exist in the manifest scripts, Makefile, or task file. -->

| Task | Command | Source |
|---|---|---|
| [Dev server] | `[command]` | [package.json scripts.dev] |
| [Build] | `[command]` | [source] |
| [Lint] | `[command]` | [source] |
| [Test] | `[command]` | [source] |

## Testing

- **Runner(s):** [name] — evidence: [dependency and config file]
- **Smallest useful check:** `[command]`
- [Where tests live and how they are named, as the repo does it.]

## Deployment

- **Target:** [platform] — evidence: [config file or CI workflow]
- **Constraints:** [runtime limits, env handling, edge or serverless notes the config establishes]
- Secrets stay in environment variables. Never commit `.env` values, tokens, or keys.

## Agent capabilities

<!-- Capabilities an agent can invoke here. The middle column says where the thing is
     committed, which is what decides whether every reader of this file has it. The
     third column is this project's policy on when to reach for it, not a copy of the
     capability's own description. -->

| Capability | Committed in | Reach for it when |
|---|---|---|
| [skill name] | [.claude/skills/name] | [task situation] |
| [MCP server name] | [.mcp.json] | [task situation] |
| [subagent name] | [.claude/agents/name.md] | [task situation] |
| [capability] | not committed; available only if installed | [task situation] |

<!-- Rules and memory files that govern work here. -->

| File | Governs |
|---|---|
| [CLAUDE.md] | [what it covers] |

## Unknowns

<!-- Keep this section even when empty: an empty Unknowns means "checked and resolved",
     a missing one means "never checked". -->

- [Fact] — checked [files], found [nothing / conflicting evidence]. Ask before assuming.

## Keeping this file current

Update the affected lines in the same change that causes any of these:

- Package manager or lockfile changes
- A dependency is added, removed, replaced, or upgraded across a major version
- A script is added, renamed, or removed
- Framework, router, or directory convention migrates
- Deploy target or platform config changes
- A skill, MCP server, subagent, or rules file is added, removed, or renamed
- A local wrapper module moves or changes what it exports

Scope the edit to what changed and refresh `Last verified`. Do not regenerate the whole
file: a rewrite churns unrelated lines and hides the real change in review.
