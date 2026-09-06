# Baseline review

For a whole repository or a directory. Broad, and necessarily shallower per file than a diff
review — the goal is to find where the risk concentrates, not to read every line.

Dispatch this to the `security-auditor` subagent for anything beyond a few dozen files. It reads
these same references in its own context and returns only the findings.

## Stage 1: Map the application

Produce this before reading any application code — it decides what is worth reading.

    rg --files -g '!node_modules' -g '!.git' | head -200
    cat package.json requirements.txt go.mod pom.xml Gemfile 2>/dev/null

Record: languages and frameworks, entry points (HTTP routes, queues, cron, CLI), data stores,
authentication mechanism, external integrations, and where secrets are configured.

## Stage 2: Select sheets

Grep `references/index.md` once per stack tag and once per architectural feature found in Stage 1.
Choose 5–10 sheets for the whole audit. Reading more than that is how a baseline review runs out of
context before it reaches the code.

Always include for a web application: input validation, authentication, session management, access
control. Add by evidence, not by habit — a sheet for a technology the repository does not use costs
context and finds nothing.

## Stage 3: Sweep by control, not by file

For each selected sheet, grep the repository for the patterns it warns about, then read only the
matches. Control-first ordering means one loaded sheet is applied everywhere it is relevant, rather
than reloading sheets file by file.

Concrete starting greps:

    rg -n "execute|query|raw|prepare" --type-add 'src:*.{ts,js,py,rb,go,java,php,cs}' -t src
    rg -n "innerHTML|dangerouslySetInnerHTML|v-html|\|safe" -t src
    rg -n "process\.env|os\.environ|getenv" -t src
    rg -n "eval|exec|spawn|system|Runtime\.getRuntime" -t src

## Stage 4: Verify before reporting

Read the surrounding code for every candidate. Framework defaults invalidate a large share of
pattern matches — an ORM call that looks like concatenation is often parameterised underneath, and
reporting it burns the reader's trust. Confirm the sink is real and the input is untrusted.

## Write the report

A baseline audit dispatched to the `security-auditor` agent produces a file, not just a chat
message. Write it to `docs/security-reviews/YYYY-MM-DD-<scope>.md` in the repository being
audited, where `<scope>` is the audited path in kebab-case, or `repo` for a whole-repository
sweep — `src/api` becomes `2026-07-28-src-api.md`, a full sweep becomes `2026-07-28-repo.md`.
Re-auditing the same scope on the same day overwrites; git carries the history.

Then verify it and include the result:

    bun <skill>/scripts/verify-citations.ts docs/security-reviews/<name>.md

Report the checker's summary line at the end of the report. If it reports any `FAIL`, fix the
citation before finishing — a failed citation means the sheet does not say what the finding claims,
which is worse than having no finding.

Diff reviews and single-concern answers do not write files. Neither does the small-scope inline
case — `/security:audit <path>` on a handful of files follows the review method above but stays in
chat, because the artifact is worth its cost for a vendor integration or an inherited system and is
pure friction for a three-file check. The file is produced when the audit is dispatched to the
agent, which is the same boundary the command's routing table already draws.

Where the artifact does apply, it is the point: a dated, sourced report that outlives whoever ran
it.

## Coverage statement

The report says what was examined and what was not: directories skipped, file types not read, and
anything deferred for size. A baseline review that implies total coverage it did not achieve is
the most damaging way this can fail — it converts an unknown into a false assurance.
