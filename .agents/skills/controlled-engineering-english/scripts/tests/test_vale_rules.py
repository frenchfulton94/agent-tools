#!/usr/bin/env python3
"""Check that the Vale rule files flag the planted fixture violations.

Usage:
    python3 scripts/tests/test_vale_rules.py

This is a test harness, not a second backend. It reads the same YAML rule
files Vale reads, so the rules stay single-sourced: a rule deleted from
styles/CEE stops being checked here too.

Requires PyYAML. Where PyYAML is missing, this test skips and says so; the
skill itself needs neither PyYAML nor Vale.

Exit code 0 = every planted violation was flagged.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("skip: PyYAML not installed; run `vale` directly instead")
    sys.exit(0)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
STYLES = ROOT / "scripts" / "vale" / "styles" / "CEE"
FIXTURES = ROOT / "evals" / "fixtures"

FAILURES = []


def load(name):
    return yaml.safe_load((STYLES / name).read_text(encoding="utf-8"))


def body_of(path):
    """Strip the fixture's HTML comment header — it is not under test."""
    text = path.read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def sentences(text):
    prose = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("#", "|", "-"))
    )
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose) if s.strip()]


def find_substitutions(text, rule):
    """Vale treats substitution keys as regular expressions; so does this."""
    hits = set()
    for banned in rule["swap"]:
        if re.search(rf"\b(?:{banned})\b", text, flags=re.IGNORECASE):
            hits.add(banned)
    return hits


def find_existence(text, rule):
    hits = set()
    for token in rule["tokens"]:
        if re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE):
            hits.add(token)
    return hits


def find_long_sentences(text, rule):
    return [s for s in sentences(text) if len(re.findall(r"\b\w+\b", s)) > rule["max"]]


def check(name, condition, detail=""):
    if condition:
        print(f"  pass  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        FAILURES.append(name)


def assert_re2_safe():
    """Vale's regex engine (RE2) has no lookaround. A pattern using one fails
    in Vale while passing here, so the harness would lie. Catch it instead."""
    banned = ("(?=", "(?!", "(?<=", "(?<!")
    for path in sorted(STYLES.glob("*.yml")):
        rule = yaml.safe_load(path.read_text(encoding="utf-8"))
        patterns = list(rule.get("swap", {})) + list(rule.get("tokens", []))
        patterns += [rule["token"]] if "token" in rule else []
        bad = [
            (pattern, construct)
            for pattern in patterns
            for construct in banned
            if construct in pattern
        ]
        check(
            f"{path.name}: {len(patterns)} patterns are RE2-safe",
            not bad,
            f"lookaround in {bad}",
        )


print("RE2 safety")
assert_re2_safe()

core = load("CoreWords.yml")
cased = load("CoreWordsCased.yml")
hedging = load("Hedging.yml")
length = load("SentenceLength.yml")

print("spec-tool keywords survive")
DELTA_KEYWORDS = [
    "ADDED Requirements",
    "MODIFIED Requirements",
    "REMOVED Requirements",
    "RENAMED Requirements",
]
for keyword in DELTA_KEYWORDS:
    hit = find_substitutions(keyword, core) | {
        k for k in cased["swap"] if re.search(rf"\b{re.escape(k)}\b", keyword)
    }
    check(f"{keyword!r} untouched", not hit, f"flagged by {sorted(hit)}")

for prose, word in (("modify the config", "modify"), ("removed the row", "removed")):
    hit = {k for k in cased["swap"] if re.search(rf"\b{re.escape(k)}\b", prose)}
    check(f"{prose!r} still flagged", bool(hit), "case-sensitive rule missed it")

print("readme-bad.md")
readme = body_of(FIXTURES / "readme-bad.md")
core_hits = find_substitutions(readme, core)
check("core-list violations flagged", len(core_hits) >= 3, f"found {sorted(core_hits)}")
for planted, pattern in (
    ("utilized", "utiliz(?:e|es|ed|ing)"),
    ("prior to", "prior to"),
    ("commencing", "commenc(?:e|es|ed|ing)"),
):
    check(f"flags '{planted}'", pattern in core_hits)
check("hedging flagged", bool(find_existence(readme, hedging)))
check("over-25-word sentence flagged", bool(find_long_sentences(readme, length)))

print("release-note-bad.md")
note = body_of(FIXTURES / "release-note-bad.md")
check("over-25-word sentence flagged", bool(find_long_sentences(note, length)))
check("hedging flagged", bool(find_existence(note, hedging)), "expected 'may wish to'")

print("spec-bad.md")
spec = body_of(FIXTURES / "spec-bad.md")
check("over-25-word sentence flagged", bool(find_long_sentences(spec, length)))

print("glossary rules")
generated = HERE / "golden-glossary.yml"
glossary = yaml.safe_load(generated.read_text(encoding="utf-8"))
banned_in_readme = find_substitutions(readme, glossary)
check(
    "generated glossary rules catch the synonym cluster",
    len(banned_in_readme) >= 3,
    f"found {sorted(banned_in_readme)}",
)

print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("all checks passed")
