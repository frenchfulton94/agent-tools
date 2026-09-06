#!/usr/bin/env python3
"""Fail if any YAML frontmatter in the package does not parse.

A SKILL.md whose frontmatter is invalid is skipped silently by the harness:
no error, no skill. This catches that before install.
"""
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("skip: PyYAML not installed"); sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent.parent
bad = []
targets = [ROOT / "SKILL.md"] + sorted(ROOT.glob("assets/*.md"))
for path in targets:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        continue
    block = text.split("---", 2)[1]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        bad.append(f"{path.name}: frontmatter does not parse — {exc}")
        continue
    if not isinstance(data, dict) or "name" not in data:
        bad.append(f"{path.name}: frontmatter has no name")
        continue
    print(f"  pass  {path.name}: frontmatter parses ({len(data)} keys)")

if bad:
    for line in bad:
        print(f"  FAIL  {line}")
    sys.exit(1)
print("all frontmatter parses")
