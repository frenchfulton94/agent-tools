# Editor, CI, and Git Hook Integration

Contents:

- [Editors](#editors)
- [CI](#ci)
- [Git hooks](#git-hooks)
- [Useful CLI flags](#useful-cli-flags)

## Editors

First-party extensions exist for VS Code (and Open VSX for VSCodium/Cursor), Zed, and IntelliJ. Community extensions cover Vim, Neovim, and Sublime Text.

### VS Code

```jsonc
// .vscode/settings.json
{
	"editor.defaultFormatter": "biomejs.biome",
	"editor.formatOnSave": true,
	"editor.codeActionsOnSave": {
		"source.fixAll.biome": "explicit",
		"source.organizeImports.biome": "explicit"
	}
}
```

`source.fixAll.biome` applies only safe fixes. To have an unsafe fix applied on save, make that specific rule's fix safe in `biome.json` — there is no blanket "apply unsafe fixes on save" setting.

Commit this to `.vscode/settings.json` rather than leaving it to individual machines; a teammate whose default formatter is still Prettier will produce a reformat war on every save.

Extension settings worth knowing:

| Setting                      | Use                                                                                                                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `biome.enabled`              | Default `true`. Per-folder in multi-root workspaces.                                                                                                                                 |
| `biome.requireConfiguration` | Default `false`. Set `true` so Biome only activates where a `biome.json` exists — the right choice when only some repos use Biome.                                                   |
| `biome.configurationPath`    | Custom config location. v2 only.                                                                                                                                                     |
| `biome.inlineConfig`         | Editor-only config overlay layered over `biome.json`. Good for locally silencing a rule (`noConsole` during debugging) without touching the committed config.                        |
| `biome.lsp.bin`              | Override the binary path; accepts a string or a platform→path map. Point it at `./node_modules/@biomejs/cli-<platform>/biome`, not at `@biomejs/biome/bin`, which is only a wrapper. |
| `biome.lsp.trace.server`     | Set `verbose` when filing a bug; the trace lands in the output panel.                                                                                                                |
| `biome.lsp.watcher.kind`     | `recommended` / `polling` / `none`. Biome 2.4.0+. Try `polling` if folders end up locked.                                                                                            |

Multi-root workspaces get one Biome instance per workspace folder automatically.

If formatting misbehaves right after upgrading the extension from 2.x: close the editor, kill every lingering `biome` process, reopen. Stale daemon connections are the usual cause. Also note `biome.lspBin` → `biome.lsp.bin` (deprecated) and `biome.requireConfigFile` → `biome.requireConfiguration` (removed, must be renamed).

## CI

Use `biome ci`, not `biome check`. The `ci` command has no `--write`, prints GitHub annotations when run there, allows thread-count control, and interprets VCS integration as `--changed` rather than `--staged` (a remote has no staging area).

### GitHub Actions

```yaml
name: Code quality
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v5
        with:
          persist-credentials: false
      - uses: biomejs/setup-biome@v2
        with:
          version: latest
      - run: biome ci .
```

Pin `version` to the same version as the `-E`-pinned devDependency rather than `latest`, or CI and local runs will drift apart on a minor release.

If `biome.json` uses `extends` to reach an npm package, add Node setup and a dependency install before the Biome step — the action installs only the binary:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: 'npm'
- run: npm ci
```

For inline PR comments, the community `mongolyy/reviewdog-action-biome@v1` action posts review comments and commit suggestions; it needs `pull-requests: write`.

### GitLab CI

Run the official image and emit a Code Quality report:

```yaml
stages: [quality]
lint:
  image:
    name: ghcr.io/biomejs/biome:latest
    entrypoint: ['']
  stage: quality
  script:
    - biome ci --reporter=gitlab --colors=off > /tmp/code-quality.json
    - cp /tmp/code-quality.json code-quality.json
  artifacts:
    reports:
      codequality: [code-quality.json]
  rules:
    - if: $CI_COMMIT_BRANCH
    - if: $CI_MERGE_REQUEST_ID
```

The empty `entrypoint` is required for the image to work under GitLab CI.

## Git hooks

Every recipe below wants `--no-errors-on-unmatched` (so a commit touching no Biome-handled file doesn't fail) and usually `--files-ignore-unknown=true` (so file types Biome doesn't handle pass silently). Using `--files-ignore-unknown=true` alone covers file types Biome supports now _and_ later; a `glob` gives tighter control. You don't need both.

### Lefthook

```yaml
# lefthook.yml
pre-commit:
  commands:
    check:
      glob: '*.{js,ts,cjs,mjs,d.cts,d.mts,jsx,tsx,json,jsonc,css}'
      run: npx @biomejs/biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true
```

`stage_fixed: true` re-stages files the hook rewrote. Drop `--write` and `stage_fixed` for a check-only hook, and use `{push_files}` under a `pre-push` key to check on push instead. Run `lefthook install` afterward.

### Husky + lint-staged

`.husky/pre-commit` contains just `lint-staged`. Then in `package.json`:

```json
{
	"lint-staged": {
		"*": ["biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"]
	}
}
```

Add `"prepare": "husky"` to `scripts` so hooks install with the package.

### git-format-staged

Avoids `git stash` internally, so conflicts between staged and unstaged changes don't need manual intervention:

```sh
git-format-staged --formatter 'biome check --write --files-ignore-unknown=true --no-errors-on-unmatched --stdin-file-path="{}"' '*'
```

### pre-commit

```yaml
repos:
  - repo: https://github.com/biomejs/pre-commit
    rev: 'v2.0.6'
    hooks:
      - id: biome-check
        additional_dependencies: ['@biomejs/biome@2.1.1']
```

Hook ids: `biome-ci`, `biome-check`, `biome-format`, `biome-lint`. The version must be pinned in `additional_dependencies` because pre-commit installs its own copy — meaning two places to bump on upgrade. Avoid that with a local hook against the project's own install:

```yaml
repos:
  - repo: local
    hooks:
      - id: local-biome-check
        name: biome check
        entry: npx @biomejs/biome check --write --files-ignore-unknown=true --no-errors-on-unmatched
        language: system
        types: [text]
```

### Plain shell hook

Works, but cross-platform breakage is on you:

```sh
#!/bin/sh
set -eu
if git status --short | grep --quiet '^MM'; then
  printf '%s\n' "ERROR: Some staged files have unstaged changes" >&2
  exit 1
fi
npx @biomejs/biome check --write --staged --files-ignore-unknown=true --no-errors-on-unmatched
git update-index --again
```

The `MM` guard fails the commit when a staged file also has unstaged changes, which `--write` would otherwise mangle.

## Useful CLI flags

| Flag                          | Effect                                                                      |
| ----------------------------- | --------------------------------------------------------------------------- |
| `--write`                     | Apply safe fixes and formatting (v1's `--apply`)                            |
| `--write --unsafe`            | Also apply unsafe fixes (v1's `--apply-unsafe`)                             |
| `--staged`                    | Only files staged in git; needs VCS integration enabled                     |
| `--changed`                   | Only files changed vs `vcs.defaultBranch`; the CI-appropriate form          |
| `--no-errors-on-unmatched`    | Exit 0 when nothing matched                                                 |
| `--files-ignore-unknown=true` | Skip unsupported file types quietly                                         |
| `--reporter=`                 | Alternate output format, e.g. `gitlab`, for CI report artifacts             |
| `--config-path`               | Point at a specific config; needed when running above multiple root configs |
| `--colors=off`                | Suppress ANSI codes for tools that render them literally                    |
