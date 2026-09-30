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
