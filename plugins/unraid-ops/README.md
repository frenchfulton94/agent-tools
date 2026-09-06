# unraid-ops

Unraid server administration for Claude Code: the know-how as a skill, a guard against the documented data-loss command patterns as a hook, and a triage command that captures evidence before it is lost.

Built from the official documentation at [docs.unraid.net](https://docs.unraid.net) (223 pages), current through Unraid 7.3.2 with 7.4.0-beta.1 in the tree.

## Components

| Component | Shape | Why this shape |
|---|---|---|
| `skills/managing-unraid-servers` | Skill | Repeated multi-step know-how applied in the main conversation, loaded on demand across seven domain references |
| `hooks/hooks.json` + `scripts/guard_destructive_storage.py` | Hook | Two of the gates must hold even when an agent is being reasoned at by a user mid-outage. Instructions are advisory; a `PreToolUse` deny is not |
| `commands/unraid-triage.md` | Command | A named entry point for "something is wrong", enforcing capture-before-reboot ordering |

## Install

    claude plugin marketplace add YOUR-GITHUB-OWNER/agent-tools --scope project
    claude plugin install unraid-ops@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/unraid-ops
claude plugin validate plugins/unraid-ops --strict
```

Verify components registered with `claude --plugin-dir plugins/unraid-ops --debug`, then `/hooks` for the guard and the skill list for the skill.

## The guard

Fires on every `Bash` call, judges each shell segment independently, and returns a permission decision. `deny` is reserved for patterns that are never correct on an Unraid server; `ask` is used where the same command is legitimate on a pool or unassigned device but catastrophic on an array member — the hook cannot tell which a given `/dev/sdX` is, and pretending otherwise would be worse than asking.

| Pattern | Decision | Reason |
|---|---|---|
| `/mnt/user` and `/mnt/diskN` in one segment | deny | Two views of the same files; documented corruption path |
| Repair tool against a whole disk (`xfs_repair /dev/sdb`) | deny | Array disks repair via `/dev/mdXp1` in Maintenance Mode |
| `dd of=/dev/sdX` or `of=/dev/nvmeX` | deny | The documented zeroing procedure targets `/dev/mdXp1` so parity stays valid |
| `mkfs*` | ask | Formatting an array disk erases it *and* updates parity |
| Repair tool against a raw partition (`/dev/sdb1`) | ask | Correct for pools and unassigned devices; invalidates parity on an array member |
| `btrfs check --repair` | ask | Can worsen damage; scrub and read-only check come first |
| `zpool destroy` / `labelclear` | ask | Destroys a pool |
| `wipefs /dev/*` | ask | Removes filesystem signatures |

Commands led by a read-only tool (`grep`, `ls`, `cat`, `find`, …) skip the cross-view rule, so searching across both views is not blocked.

**Known limits.** The guard is a pattern matcher, not a model of your server. It cannot tell an array member from a pool device, cannot see which disk is parity, and will not catch a destructive action taken through the WebGUI or a script it never sees. It reduces one class of mistake; it is not a safety system. Test any change to it against `scripts/` payloads before relying on it.

## Testing the guard

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cp /mnt/disk2/x /mnt/user/x"}}' \
  | python3 scripts/guard_destructive_storage.py
```

Empty output means allow. A JSON body carries the decision. The script always exits 0 — the decision travels in the body, per the `PreToolUse` contract.

## Skill evals

`skills/managing-unraid-servers/evals/` holds a 20-query trigger battery and 5 behavior cases with PASS/FAIL assertions, for A/B runs against a baseline. They are never loaded automatically.
