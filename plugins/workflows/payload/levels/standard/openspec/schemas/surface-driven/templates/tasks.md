## 1. <!-- Behavior task example -->

**Files:**
- Create: `exact/path/to/file`
- Test: `tests/exact/path`

**Interfaces:**
- Produces: <!-- exact names/signatures later tasks rely on -->

**Tooling:** <!-- named skills/MCP tools/commands with exact invocation + fallback; fresh subagent executors only get what is named here -->

**Brief/Specs:** <!-- brief section + Requirement/Scenario served -->

```text
(actual failing-test code for step 1.1)
```

- [ ] 1.1 Write the failing test above at `tests/...`
- [ ] 1.2 Run `<exact test command>` and confirm it fails with `<expected failure>`
- [ ] 1.3 Write the minimal implementation to pass it
- [ ] 1.4 Run `<exact test command>` and confirm the suite is green
- [ ] 1.5 Commit

## 2. <!-- Surface task example -->

**Files:**
- Modify: `exact/path/to/component`

**Tooling:** <!-- e.g. "browser tool for 2.2's inspection round when available, otherwise manual review"; detector invocation for 2.3 -->

**Brief/Specs:** <!-- brief section + states covered -->

- [ ] 2.1 Build the surface fully against the committed world (all states from the brief)
- [ ] 2.2 One batched inspection round at desktop + mobile; list every defect found
- [ ] 2.3 Fix the whole batch; run the detector on edited files and fix findings
- [ ] 2.4 One confirming round; then stop polishing and commit
