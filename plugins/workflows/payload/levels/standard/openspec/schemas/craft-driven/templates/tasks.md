## 1. <!-- Component name -->

**Files:**
- Create: `exact/path/to/file`
- Modify: `exact/path/to/existing:lines`
- Test: `tests/exact/path`

**Interfaces:**
- Consumes: <!-- exact names/signatures from earlier tasks -->
- Produces: <!-- exact names/signatures later tasks rely on -->

**Specs:** <!-- Requirement / Scenario this task implements -->

**Tooling:** <!-- Named skills / MCP tools / commands for this task, with exact invocation and a fallback: "use <tool> when available, otherwise <fallback>". Executors (possibly fresh subagents) only get what is named here. -->

```text
(actual failing-test code for step 1.1 goes here, in the project's language)
```

- [ ] 1.1 Write the failing test above at `tests/...`
- [ ] 1.2 Run `<exact test command>` and confirm it fails with `<expected failure>`
- [ ] 1.3 Write the minimal implementation in `<file>` to pass it
- [ ] 1.4 Run `<exact test command>` and confirm it passes with the suite green
- [ ] 1.5 Commit: `git add ... && git commit -m "..."`

## 2. <!-- Next component; UI tasks add detector + state-coverage steps -->

- [ ] 2.1 ...
