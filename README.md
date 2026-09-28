# agent-tools

Claude Code plugins for this catalog — agent tooling, the
TypeScript and SvelteKit stacks, interface craft and motion, containers, OWASP-grounded security
review, and OpenSpec workflow setup.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install <plugin>@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugins travel with the repo instead of living on one workstation.

## What ships

| Plugin | Skills | For |
|---|---|---|
| [meta-skills](plugins/meta-skills) | `authoring-hooks` `authoring-plugins` `authoring-skills` `authoring-subagents` `controlled-engineering-english` `improving-prompts` `maintaining-plugin-marketplaces` `managing-project-memory` `mapping-project-tooling` | Building and maintaining Claude Code's own extension surfaces, plus prompts, project memory, and documentation. Ships the `controlled-english` output style |
| [typescript](plugins/typescript) | `bun` `configuring-biome` `debugging-type-errors` `drizzle-development` `refactoring-typescript` `vite` `vitest-testing` `writing-typescript` | The TypeScript toolchain — compiler settings, strictness migrations, tests, bundling, formatting, typed data access |
| [frontend](plugins/frontend) | `bem-css` `bits-ui` `feature-sliced-design` `internationalized-date-time` `layerchart` `sanitizing-untrusted-html` `styling-with-tailwind` `using-paraglide-js` | The SvelteKit-leaning web application stack — components, charts, styling, layout, i18n, sanitization |
| [design-engineering](plugins/design-engineering) | `animating-interfaces` `animation-vocabulary` `design-engineering` `finding-animation-opportunities` `fluid-interfaces` `improving-animations` `reviewing-animations` | Interface craft and motion on the Svelte stack — building, reviewing, auditing, and finding animation, plus the judgement and the Apple fluid-interface principles underneath it |
| [docker-workbench](plugins/docker-workbench) | `configuring-dev-containers` `containerizing-apps` `managing-container-runtimes` `securing-container-supply-chain` | Docker and containers, from Dockerfiles to supply chain. Ships a `container-debugger` agent and a volume-loss guard hook |
| [security](plugins/security) | `reviewing-code-security` | OWASP-grounded review with verifiable citations. Ships `/security:audit`, a `security-auditor` agent, and a credential-format hook |
| [workflows](plugins/workflows) | `choosing-a-workflow` `configuring-openspec` `setup` | Setting up and routing OpenSpec workflows. Ships `/workflows:setup` and a self-paced learning package |
| [unraid-ops](plugins/unraid-ops) | `managing-unraid-servers` | Unraid server administration — array, pools, shares, Docker, VMs, remote access, recovery. Ships `/unraid-ops:triage`, a data-loss guard hook, and a read-only MCP server over the Unraid GraphQL API |
| [dokploy](plugins/dokploy) | `automating-dokploy` `configuring-dokploy-enterprise` `deploying-apps-to-dokploy` `hardening-dokploy` `operating-dokploy-servers` | Self-hosted Dokploy PaaS — deploying apps, operating the host, scripting the CLI/API, hardening against a compliance-mapped checklist, and configuring the licensed SSO/SCIM tier. Ships a guard hook against irreversible project, database, and volume removal |
| [zed](plugins/zed) | `configuring-zed` | Configuring the Zed editor |
| [apple-studio](plugins/apple-studio) | `app-release` `apple-animations` `apple-design` `apple-frameworks` `apple-intelligence` `apple-macos` `apple-performance` `swift-architecture` `swift-concurrency` `swift-testing` `xcode-loop` | Native Apple app development — architecture, strict concurrency, testing, HIG conformance, motion, macOS, frameworks, on-device AI, performance, release. Ships a PostToolUse edit tracker and a Stop build gate |
| [para](plugins/para) | `maintaining-para-systems` `organizing-files-with-para` | Organizing a directory into PARA — Projects, Areas, Resources, Archives — with an approve-before-move plan. Ships `/para:organize`, an undo trail, and a guard hook against deletion and unplanned moves |
| [godot](plugins/godot) | `gdscript` `godot-scene-files` | Game development with Godot 4 — GDScript with static typing, the style guide, and the warning system |

Each plugin's own README covers its components, its limits, and how to run it locally.

## Development

    bun test                # the pinned contract
    bun run audit           # the sweep: validators plus what no test covers
    bun run audit:strict    # the same, failing on warnings too
    claude plugin validate  # authoritative marketplace check

`bun test` pins registration in both directions, `name` matching directory, a semver version in
each `plugin.json`, the same description in `plugin.json` and the marketplace entry, `SKILL.md`
presence and frontmatter match, skill-name uniqueness across the catalog, the README links above,
and the vendored `.agents/skills/` copies against their sources under `plugins/`. `bun run audit`
runs the four vendored validators over every skill, plugin, agent, and hook, then checks the
plugin-level READMEs, this README's skills column, and the marketplace-level schema. The two are
deliberately disjoint — a second implementation of one invariant disagrees with the first the next
time either changes.

`bun run audit` exits non-zero on errors only. The validator warnings it prints — body length, a
reference file with no table of contents — are judgement calls an author may have made
deliberately, so `bun test` gates on the sweep's catalog findings and prints the rest as advisory.
`bun run audit:strict` fails on them too, for a maintainer working through the backlog.

To validate one plugin, or to load it without installing:

    claude plugin validate plugins/<plugin> --strict
    claude --plugin-dir plugins/<plugin>

## Releasing

A version lives in `plugins/<plugin>/.claude-plugin/plugin.json` and nowhere
else — marketplace entries carry no version field. An unbumped plugin ships
nothing: `/plugin update` reports "already at the latest version" and users keep
the old copy indefinitely. `bun run audit --since <ref>` reports a plugin
directory that changed without a bump.

`name` is an install-breaking identifier — users carry it in `enabledPlugins` and every install
command. To change only the label, set `displayName` and leave `name` alone. When a `name` genuinely
has to change, add it to `renames` in `marketplace.json`, mapping old to new, or to `null` when the
plugin is retired. `renames` is append-only history: existing entries stay put even after everyone
has migrated.

## License

MIT for the plugin sources. `plugins/security/skills/reviewing-code-security/owasp/` is the OWASP
Cheat Sheet Series, vendored verbatim under CC-BY-SA-4.0 — see `owasp/NOTICE.md`.
