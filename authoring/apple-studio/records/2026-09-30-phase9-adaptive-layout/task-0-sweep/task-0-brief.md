### Task 0: Opening sweep and charter amendment

**Files:**
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`
- Modify: `$AS/docs/deferred.md` (item 1: append the Phase 9 measurement)
- Modify: `$AS/docs/specs/2026-08-03-apple-studio-design.md:193` (insert the amendment after the Phase 7 block)

**Interfaces:**
- Consumes: `deferred.md` item 1's scan method (Phase 6 and Phase 7 paragraphs).
- Produces: the measurement Task 9's spec append cites; the charter text Task 9 does not repeat.

- [ ] **Step 1: Confirm the branch.** Run `git branch --show-current` → expect `phase9-adaptive-layout`. Run `git merge-base --is-ancestor ea4995c HEAD; echo $?` → expect `0`.

- [ ] **Step 2: Write the scan script.** Create `task-0-sweep/killswitch_scan.py`:

```python
#!/usr/bin/env python3
"""Phase 9 kill-switch scan: apple-studio:* Skill invocations since a date.

Method unchanged from deferred.md item 1 (Phase 6, Phase 7): JSON-parse every
Skill tool_use block and read input.skill. Fixture and authoring sessions are
excluded; they are the plugin's own verification, not real use.
"""
import json
import pathlib
import sys
from collections import Counter

since = sys.argv[1]  # e.g. "2026-09-12"
root = pathlib.Path.home() / ".claude" / "projects"
EXCLUDE = ("-scratchpad-", "-private-tmp-", "StudioFixture", "agent-tools", "apple-studio")

genuine = set()
excluded = Counter()
files = 0
for f in root.rglob("*.jsonl"):
    files += 1
    project = f.relative_to(root).parts[0]
    for line in f.open(errors="ignore"):
        if '"Skill"' not in line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        ts = rec.get("timestamp", "")
        if ts[:10] < since:
            continue
        content = (rec.get("message") or {}).get("content") or []
        for block in content if isinstance(content, list) else []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill"):
                continue
            skill = (block.get("input") or {}).get("skill", "")
            if not skill.startswith("apple-studio:"):
                continue
            if any(x in project for x in EXCLUDE):
                excluded[project] += 1
            else:
                genuine.add((f.stem, skill, ts[:10], project))

print(f"transcripts scanned: {files}")
print(f"excluded invocations by project: {dict(excluded)}")
print(f"genuine non-fixture invocations since {since}: {len(genuine)}")
for g in sorted(genuine):
    print("  ", g)
```

- [ ] **Step 3: Run it.** `python3 $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py 2026-09-12 | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`. Expected: a `genuine non-fixture invocations` line with a count.

- [ ] **Step 4: Apply the pre-taken decision rule; do not improvise.** Item 1 says the skill gate fires only "at the opening sweep of the first phase following a shipped real feature". No real feature has shipped through this plugin, so no skill is cut whatever the count. Append to item 1 a paragraph headed `**Phase 9 measurement (2026-09-30).**` stating: the scan window (since 2026-09-12), transcripts scanned, the genuine count, the excluded counts by project, and the evidence path `records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`. If the genuine count is non-zero, list each hit and state it is the first evidence of real use, not a trigger.

- [ ] **Step 5: Amend the charter.** Insert after line 193 of `$AS/docs/specs/2026-08-03-apple-studio-design.md` (the last line of the Phase 7 block, `> rationale stands.`), keeping one `>` blank line before it:

```markdown
>
> **Amended 2026-09-30 (Phase 9).** Phase 8 shipped the catalog migration,
> not ML, and did not amend the line above. ML remains the one outstanding
> long-tail item. Phase 9 is on-demand work: adaptive layout and iPhone Duo —
> see docs/specs/2026-09-30-phase9-adaptive-layout-design.md.
```

- [ ] **Step 6: Record the `verified:` headers of the two existing files this phase edits.** Run `head -1 plugins/apple-studio/skills/apple-design/references/platform-idioms.md plugins/apple-studio/skills/apple-design/references/hig-patterns.md | tee -a $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/headers.log`. Expected: `2026-08` and `2026-09` respectively. They are re-stamped in Task 4 only because Task 4 edits them.

- [ ] **Step 7: Check prose and commit.** Run Vale on `deferred.md` and the charter; fix any non-"amend" warning in the lines you added.

```bash
git add $AS/docs/deferred.md $AS/docs/specs/2026-08-03-apple-studio-design.md $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep
git commit -m "Phase 9 Task 0: kill-switch sweep and charter amendment

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

