# Behavior test cases: authoring-hooks

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Create a blocking hook (must-pass set)

**Prompt:** "Block Claude from editing anything under `src/generated/` — those files come from our codegen step. It should be told to edit `schema.prisma` and re-run `bun generate` instead."

**Assertions:**
1. Uses `PreToolUse`, not `PostToolUse`. (A `PostToolUse` hook cannot prevent the edit; the file is already written.)
2. The event name is spelled and cased exactly as documented.
3. Blocking is signalled with `exit 2`, or with exit 0 plus `permissionDecision: "deny"` — never `exit 1`. (Baselines reliably fail this: `exit 1` is the conventional failure code and produces a hook that runs, reports nothing, and blocks nothing.)
4. If JSON is returned, it is the sole contents of stdout and is not printed alongside a non-zero exit.
5. Any `additionalContext` or `permissionDecisionReason` states what to do instead, not only that the edit is forbidden.
6. The matcher is anchored or exact — `Edit|Write`, not `Edit.*`, which would also catch `NotebookEdit`.
7. The script path is absolute or goes through `${CLAUDE_PROJECT_DIR}`, not a bare relative path.
8. The response says how to verify the hook actually blocks, and the verification is more than "restart Claude Code" — piping a sample payload into the script, or checking `/hooks`.
9. The hook was actually tested or validated before delivery, not merely proposed with testing left to the user.

## Case 2 — Audit a broken hook configuration

**Prompt:** "None of these hooks seem to do anything. Can you work out what's wrong with each one?"
(Working directory: the skill root; the configuration is `evals/fixtures/broken-hooks.json`.)

**Assertions:**
1. Identifies that `guard.sh` exits 1 where it intends to block, and states that exit 1 is non-blocking.
2. Identifies that `context.sh` places `additionalContext` at the top level rather than inside `hookSpecificOutput`, and that this is silently ignored.
3. Identifies the miscased `postCompact` event.
4. Identifies at least two of: the `prompt` handler on `SessionStart` (which accepts only `command` and `mcp_tool`), the `if` condition on a non-tool event (where the handler never runs), the literal `mcp__memory` matcher (which matches nothing), the unanchored `Edit.*` matcher, and the relative `./notify.sh` command path.
5. Reports findings before proposing edits.
6. Does not claim a fault the fixture does not contain.

## Case 3 — Edge: wrong mechanism

**Prompt:** "Write me a hook that makes sure Claude follows our TypeScript style guide — no `any`, prefer `const`, that kind of thing."

**Assertions:**
1. Response distinguishes the mechanical parts (which a hook can check by running a linter) from the judgment parts (which it cannot), rather than producing a hook that pattern-matches style rules.
2. Recommends a skill, a linter invoked from a hook, or both — and does not present a regex-based style hook as sufficient.
3. Response stays proportionate and does not scaffold a large hook script for rules an existing linter already enforces.
