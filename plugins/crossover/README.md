# crossover

Running Windows applications and games on a Mac with CodeWeavers CrossOver, for Claude Code. It packages the know-how as a skill, debug-log reading as an agent, and a guard against deleting bottles as a hook.

The material comes from the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base): all 47 articles, fetched 2026-10-17. Command-line behaviour was measured on CrossOver 25.1.1, against throwaway bottles created in a scratch folder with `CX_BOTTLE_PATH`.

## Components

| Component | Shape | Why this shape |
|---|---|---|
| `skills/using-crossover-mac` | Skill | Multi-step know-how applied in the main conversation, loaded on demand across five references. The KB's Advanced Settings differ between 23.7–24, 25, and 26, so the skill establishes the version before describing any of them |
| `agents/crossover-log-triage.md` | Subagent | Debug logs run to hundreds of megabytes. Most of each one is noise that appears even when a program succeeds, and only the conclusion is worth keeping in the conversation |
| `hooks/hooks.json` + `scripts/crossover-guard.pl` | Hook | A bottle holds installed applications, licences, and saves, and has no undo except an archive. `cxbottle --delete` skips its own confirmation without a terminal (measured), so an instruction is not enough |

No MCP server: CrossOver's own command-line tools already give Bash everything an MCP server would add, and a second copy would drift from CrossOver releases.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install crossover@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/crossover
claude plugin validate plugins/crossover --strict
```

## The guard

The guard runs on every `Bash` call. A command containing none of `rm`, `unlink`, `find`, `rsync`, `xargs`, `cxbottle`, `cxuninstall`, or `RemovalTool` is allowed after one regex check. A command containing one of them is split into shell statements and words: quotes, `~` and `$HOME`, `cd`, globs, `sudo`/`env`/`nice` wrappers, `bash -c`, and `eval` are all handled. Each target is then checked against every bottle found on disk.

| Pattern | Decision | Why |
|---|---|---|
| `rm -r` of a bottle, a bottle folder or any ancestor of one, a C: drive, or a C: drive's top-level folder | deny | No undo. `cxbottle --delete` is the supported route |
| `rm` / `unlink` of `system.reg`, `user.reg`, `userdef.reg`, or `cxbottle.conf` | deny | With `system.reg` gone the bottle cannot start, and the file is not recreated (measured) |
| `cxbottle --delete` | ask | Legitimate, but its own confirmation does not appear without a terminal |
| `cxuninstall`, launching the Removal Tool | ask | Both can remove every bottle |
| `find … -delete` / `-exec rm`, or `rsync --delete`, into a bottle | ask | Which files go depends on the filters |
| A recursive delete of a target the guard cannot resolve (`$VAR`, `$(…)`, `xargs`), on a command mentioning CrossOver | ask | It cannot be judged without running the shell |

Bottles are found in the default folder, in the published-bottle folder, and wherever `BottleDir` or `ManagedBottleDirs` (in `com.codeweavers.CrossOver` or `…CrossOverGames`), `CX_BOTTLE_PATH`, or `BottlePath` (in any `CrossOver*.app` bundle's or the user's `CrossOver.conf`) point. A folder counts as a bottle if it holds a `cxbottle.conf`. With no bottles, the guard stays silent.

The guard is written in Perl because CrossOver's own tools are Perl scripts, so `/usr/bin/perl` is present wherever CrossOver's command line works. On a Mac without the developer tools, `python3` is a stub that opens an install dialog. Only core modules are used.

**Known limits.** It does not see a delete performed by a script file that a command runs, or by the Finder. It does not guard `mv`, which is reversible, or `cxbottle --removeall` and `--uninstall`, whose menus and associations `cxbottle --install` re-creates. It fails open on a malformed payload or an internal error. Deleting one folder deeper than the C: drive's top level, such as `drive_c/Program Files/Game`, is allowed, because that is how a user removes a single game folder on purpose.

## Testing

```bash
bun test tests/crossover-guard.test.ts    # from the marketplace root
```

The suite builds a fixture home folder with bottles in all four kinds of location and runs the real script against 71 cases: 32 that must be denied, 16 that must ask, and 23 that must be allowed: `echo "rm -rf …"`, removing a symlink to a bottle, `find ~ -name .DS_Store -delete`, unzipping the Removal Tool, and others. Every case also asserts a clean exit and an empty stderr with `CROSSOVER_GUARD_DEBUG=1` set, so an internal error cannot pass as "allow".

The guard also takes a payload directly:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cxbottle --bottle Steam --delete"},"cwd":"/tmp"}' \
  | perl plugins/crossover/scripts/crossover-guard.pl
```

Empty output means allow. Otherwise a JSON body carries the decision. The script always exits 0.

## Skill evals

`skills/using-crossover-mac/evals/` holds a 20-query trigger battery and 5 behavior cases with PASS/FAIL assertions, for A/B runs against a baseline. They are never loaded automatically.
