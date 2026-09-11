# security

Security review grounded in the OWASP Cheat Sheet Series. Every finding cites a specific
cheatsheet and section, from a corpus vendored into this plugin and pinned to an upstream commit —
so a review runs offline and produces the same result twice.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install security@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/security
claude plugin validate plugins/security --strict
```

## Usage

    /security:audit                 # review the diff against main
    /security:audit --baseline      # sweep the whole repository
    /security:audit src/api         # scope to a subtree

The `reviewing-code-security` skill also fires on requests like "check this for security problems"
without the command.

A `--baseline` audit, or a bare-path audit large enough that `/security:audit` dispatches the
`security-auditor` agent, writes a dated report to `docs/security-reviews/` and verifies every
citation in it against the corpus before finishing. Diff reviews, single questions, and small-scope
path audits that stay inline do not write a file.

    bun skills/reviewing-code-security/scripts/verify-citations.ts <report.md>

re-checks a report at any time: it confirms each cited sheet exists, each `§` section is a real
heading in it, and each quote appears verbatim. `bun test` runs it over every committed report.

## Components

| Component | What it does |
|---|---|
| `reviewing-code-security` skill | Routes diff vs baseline, retrieves cheatsheets, formats findings |
| `security-auditor` agent | Runs baseline sweeps in its own context, writes a verified report to `docs/security-reviews/`, and returns only findings |
| `/security:audit` command | Explicit entry point |
| `PostToolUse` hook | Flags high-confidence credential patterns in written files (advisory) |

## The hook is advisory, on purpose

It warns; it does not block. It matches only six near-certain patterns — PEM private-key headers,
`AKIA`-prefixed AWS key IDs, GitHub personal-access and fine-grained tokens, Anthropic API keys,
and Slack bot tokens. A blocking hook that false-positives gets switched off within a week, which
is worse than an advisory one that survives. Each pattern carries a precision test asserting that a
prose mention of its prefix does not match.

**It needs `jq`**, which stock macOS and minimal Linux images do not ship. Without it the hook
cannot read the tool payload, so it announces that once per session — "the credential-format scan
is not running in this session: jq is not installed" — rather than exiting silently, which would be
indistinguishable from a clean scan. Install it with `brew install jq` on macOS or
`apt-get install jq` on Debian and Ubuntu, and the scan turns itself back on.

**It also speaks up when the scan itself cannot run**, for the same reason it speaks up about
`jq`: a scan that produces no output is indistinguishable from a clean file, and silence there is
worse than knowing the scan never happened. If `grep` cannot read the file — permissions set to
`000`, or an I/O error from the underlying device — the hook says "the file at path
`<path>`…`</path>` could not be read, so the credential-format scan did not run on it." If the path
names nothing at all by the time the scan runs — the file was written and then removed before
`PostToolUse` fired — it says "the credential-format scan did not run: no regular file was present at path
`<path>`…`</path>` when the scan ran." Both are advisory, exit 0 either way, and both wrap the path
the same way the match advisory does.

Notebooks are not scanned. The matcher is anchored to `Write` and `Edit`, and `NotebookEdit`
carries a different payload shape.

## Known limitation: the agent has Bash and Write

`security-auditor` needs `Bash` for `git diff` and `rg`, and `Write` to produce its report at
`docs/security-reviews/`. Plugin-shipped agents silently drop `permissionMode`, so neither is
enforced structurally — the agent body constrains `Bash` to read-only commands and `Write` to that
one report path, which is advisory either way. If your threat model needs that enforced, copy the
agent to `.claude/agents/` and set `permissionMode` there, accepting the loss of plugin
distribution.

The same is true of citation verification: the inline `rg -F` check in `SKILL.md`'s Verify
checklist and the agent's own `verify-citations.ts` run before it reports done are both instructed,
not enforced — nothing stops a model from skipping either. The check that does not depend on the
model is the `bun test` sweep over every committed report in `docs/security-reviews/`, which is
what CI actually gates on.

## Corpus provenance

`skills/reviewing-code-security/owasp/` is the OWASP Cheat Sheet Series, verbatim and
unmodified, under CC-BY-SA-4.0. See `owasp/NOTICE.md` for attribution and
`owasp/SOURCE.json` for the pinned upstream commit and sync date. Maintainers refresh it
with `bun skills/reviewing-code-security/scripts/sync-owasp.ts`; it is never fetched at review time.
Follow it with `bun skills/reviewing-code-security/scripts/build-index.ts` to regenerate
`references/index.md` — the two must run together, or the index drifts from the corpus it describes.
