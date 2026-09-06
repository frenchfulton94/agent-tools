---
name: authoring-hooks
description: Creates, audits, and debugs Claude Code hooks — event selection, matcher syntax, handler configuration in settings.json or a plugin hooks.json, and the exit-code and JSON output contracts. Use when the user wants something to happen automatically at a point in the agent loop, wants to enforce a rule that plain instructions keep failing to enforce, wants to block or rewrite a tool call, wants to inject context at session start, wants to review or tighten hooks they already have, or has a hook that silently never fires, fires too often, or fires but does not block. Also use when the user says Claude keeps doing something despite being told not to, even if they never say "hook".
license: MIT
---

# Authoring Hooks

A hook is a handler Claude Code runs at a fixed point in the agent loop. Skills and memory files are advisory — a model can reason around them. A hook is executed by the harness, so it happens whether or not the model cooperates. That is the whole reason to reach for one.

Most broken hooks are not broken scripts. They are configured against the wrong event, matched with a pattern that never matches, or written to signal a decision in a way the harness ignores.

## Is a hook the right tool?

| The user wants... | Use... |
|---|---|
| A rule that holds every time, with no chance of being reasoned around | A hook |
| A hard allow/deny on tools or paths | The permission system — `permissions.deny` in settings, not a hook |
| Repeated multi-step know-how applied with judgment | A skill |
| A project fact the agent should always know | The project memory file |

Hooks and permissions overlap but are not interchangeable. A `PreToolUse` hook that denies is a policy check that can be written in code; `permissions.deny` is a static rule the harness enforces without running anything. Prefer permissions when the rule is expressible as a pattern, and a hook when the decision needs to look at the file, the repository, or the command.

## Four decisions

Every hook is: **event → matcher → handler type → output contract.** Get these in order.

**1. Event.** The most-used ones:

| Event | Fires | Can block? |
|---|---|---|
| `PreToolUse` | Before a tool runs, in every permission mode | Yes — blocks the call |
| `PostToolUse` | After a tool succeeds | No — the tool already ran |
| `PostToolUseFailure` | After a tool fails | No |
| `UserPromptSubmit` | When the user submits a prompt | Yes — blocks and erases the prompt |
| `SessionStart` | At session start, resume, clear, compact, or fork | No — context injection only |
| `Stop` | When Claude is about to finish its turn | Yes — forces the turn to continue |
| `SubagentStop` | When a subagent finishes | Yes |
| `SessionEnd` | On session teardown | No, and the budget is 1.5 s |
| `Notification` | On permission prompts, idle prompts, and similar | No |
| `PreCompact` | Before context compaction | Yes |

Read `references/events.md` for the full catalog — every event, what its matcher matches, whether exit 2 blocks it, and its input and output fields.

**2. Matcher.** See the matcher section below.

**3. Handler type.** `command` is the default and the only one that covers every event. `http`, `mcp_tool`, `prompt`, and `agent` exist for cases a script cannot serve. Read `references/handlers.md` when choosing, or when a command hook misbehaves on quoting or timeouts.

**4. Output contract.** Exit codes and JSON, below.

## Configuration shape

Three levels: event → matcher group → handler.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "node", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/format.js"], "timeout": 30 }
        ]
      }
    ]
  }
}
```

The same object goes in `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, a plugin's `hooks/hooks.json` (wrapped in an outer object that may add a `description`), or skill and agent frontmatter. Hooks from every source merge; they never replace each other. All matching hooks run in parallel, so a `deny` from one does not suppress another's side effects.

## Exit codes

| Exit | Meaning |
|---|---|
| `0` | Success. Stdout is parsed as JSON if it starts with `{` |
| `2` | Blocking error. Stdout and any JSON are ignored; stderr is fed back to Claude |
| anything else | Non-blocking error. Execution continues; the transcript shows a hook-error line |

Exit `1` does not block. This is the single most common hook bug: the script uses the conventional Unix failure code, the tool runs anyway, and nothing looks wrong. Use `exit 2` to enforce policy. (`WorktreeCreate` is the exception — any non-zero exit aborts creation there.)

Do not mix the two channels. Either exit with a code and write a message to stderr, or exit 0 and print a JSON object as the entire contents of stdout. JSON printed alongside exit 2 is discarded.

## JSON output

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "This file is generated. Edit src/schema.ts and run `bun generate` instead."
  }
}
```

`additionalContext` must be nested inside `hookSpecificOutput`. Placed at the top level it is silently ignored — no error, no warning, and the hook looks like it ran fine.

Decision fields differ by event family:

- Most blocking events take a top-level `decision: "block"` with a `reason`. The value is only ever `"block"`; to allow, omit the field or exit 0 with no output.
- `PreToolUse` uses `hookSpecificOutput.permissionDecision` (`allow`, `deny`, `ask`, `defer`) with `permissionDecisionReason`. Across hooks, precedence is deny > defer > ask > allow. A hook can tighten permissions but never loosen them — `allow` does not override a deny rule.
- `PermissionRequest` uses `hookSpecificOutput.decision.behavior`.

Universal fields: `continue: false` stops Claude entirely and takes precedence over any decision field, with `stopReason` shown to the user (not to Claude); `systemMessage` surfaces a warning to the user; `suppressOutput` hides stdout from the transcript. Every output string is capped at 10,000 characters — longer content is written to a file and replaced with a preview and path.

## Matchers

A matcher is compared one of two ways, and which one it gets depends on the characters in it:

- Only letters, digits, `_`, `-`, spaces, `,`, or `|` → **exact string**, or a `|`- or `,`-separated list of exact strings. `Bash`, `Edit|Write`.
- Any other character → **unanchored JavaScript regex**. `^Notebook`, `mcp__memory__.*`.

Consequences worth internalizing:

- `Edit.*` is a regex and matches `NotebookEdit` too. Write `^Edit$` when you mean only `Edit`.
- `mcp__memory` contains only exact-match characters, so it is compared as a literal string and matches nothing. MCP matchers need the regex form: `mcp__memory__.*`.
- Matchers are case-sensitive, and so are event names. `postToolUse` registers nothing.
- A matcher set on an event that does not support one is silently ignored — it does not narrow anything.
- Omitting the matcher, or using `"*"` or `""`, matches everything.

Different events match different things: tool events match the tool name, `SessionStart` matches the start reason, `SubagentStart` and `SubagentStop` match the agent type, `FileChanged` matches literal filenames to watch. The full mapping is in `references/events.md`.

## Injected context

Write `additionalContext` as factual statements about the project, not as instructions addressed to the agent. Text framed as an out-of-band system command can trip prompt-injection defenses, which surfaces it to the user instead of using it as context. "The deploy script requires `AWS_PROFILE=prod`" works; "SYSTEM: you must always set AWS_PROFILE" does not.

One resume caveat: injected text is stored in the transcript and replayed on `--continue` and `--resume` rather than regenerated, so timestamps, branch names, and commit SHAs go stale. `SessionStart` hooks do re-run on resume, with `source` set to `resume` or `fork`.

## Security

Command hooks run with full user permissions and can touch anything the user can. Quote every shell variable, reject `..` in paths taken from hook input, prefer exec form with `args` when the input is untrusted, and skip `.env`, `.git/`, and key material. Hooks run without a controlling terminal, so `/dev/tty` is unavailable — use `systemMessage` for user-facing output.

## Debugging a hook that misbehaves

| Symptom | Look at |
|---|---|
| Never fires | Event name casing; matcher class (exact vs. regex); `if` set on a non-tool event, where the hook never runs; the plugin not reloaded after an edit; `/hooks` to confirm it registered at all |
| Fires but does not block | `exit 1` instead of `exit 2`; an event that cannot block regardless of exit code |
| Runs, but its output is ignored | JSON printed alongside exit 2; `additionalContext` not nested in `hookSpecificOutput`; anything other than the JSON object on stdout, including shell-profile banners |
| Fires far too often | An unanchored regex matcher — `Edit.*` catching `NotebookEdit`, or a bare `.*` |
| Blocks forever | A `Stop` hook without a `stop_hook_active` guard; the harness overrides it after 8 consecutive blocks |
| Reported as "command not found" | A relative path — use an absolute one, `${CLAUDE_PROJECT_DIR}`, or `${CLAUDE_PLUGIN_ROOT}` in a plugin; also check `chmod +x` |

Test the handler directly before blaming the configuration:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh; echo "exit=$?"
```

Then run `bun scripts/validate_hooks.ts <config> --strict` for the configuration faults above, and `--simulate <Event>` to drive each handler with a synthetic payload and see what Claude Code would do with the result. `claude --debug` logs matcher evaluation and handler output; `/hooks` shows what actually registered, grouped by event and labeled by source.

## Auditing existing hooks

- [ ] Every event name is spelled and cased exactly as documented
- [ ] Every matcher is in the class its author intended, and anchored if it names a tool
- [ ] Handler types are supported by their events (`SessionStart` and `Setup` accept only `command` and `mcp_tool`)
- [ ] `if` appears only on tool events, where it is evaluated
- [ ] Scripts signal blocking with exit 2, and never print JSON alongside it
- [ ] `additionalContext` is nested inside `hookSpecificOutput`
- [ ] Paths are absolute or go through `${CLAUDE_PROJECT_DIR}` / `${CLAUDE_PLUGIN_ROOT}`, and shell-form commands quote them
- [ ] `Stop` and `SubagentStop` hooks check `stop_hook_active` before blocking
- [ ] No two `PreToolUse` hooks write `updatedInput` for the same tool — they run in parallel and the last to finish wins
- [ ] Deletion pass, last: hooks that no longer fire on anything, and hooks whose rule is now covered by a permission rule

Silent no-ops deserve their own line in the report. A hook that never fires reads exactly like a hook that is working.

## Verify

Before reporting done: the configuration validates, the handler was run against a real payload and returned the exit code and JSON you expect, and the hook was observed firing (`/hooks` for registration, `claude --debug` for evaluation). For a blocking hook, confirm it actually blocked — not that it ran.

## Output contract

- **Creating:** the configuration block and any script, plus one line stating what fires it, what it does, and what it blocks.
- **Auditing:** findings per hook keyed to the debugging table above, then the diffs. Call out silent no-ops explicitly. If the configuration is sound, say so and stop.

`references/patterns.md` has complete worked recipes — format-on-write, blocking a dangerous command, session-start context injection, a test gate on `Stop`, and a plugin-bundled hook. Start from one when the task resembles it.

## Related skills

- `authoring-plugins` — for bundling hooks into a distributable plugin. This skill is self-contained without it.
- `authoring-skills` — for the advisory counterpart, when a rule does not need enforcing. Self-contained without it.
- `authoring-subagents` — for hooks scoped to a single subagent. Self-contained without it.
