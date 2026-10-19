"""Compare two typecheck_snippets.py catalog logs per (file, snippet number).

usage: python3 -I catalog_diff.py BEFORE AFTER PHASE10_FILES_LIST
Prints PASS->FAIL, FAIL->PASS, snippets new in AFTER, and every FAIL in a
Phase 10 file. Exit 1 when a PASS->FAIL flip or a Phase 10 FAIL exists.
"""
import re
import sys

FILE_RE = re.compile(r"^FILE: (\S+)")
SNIP_RE = re.compile(r"^  \[(PASS|FAIL)[^\]]*\] #(\d+)\s+(.*)$")


def parse(path):
    out = {}
    cur = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = FILE_RE.match(line)
            if m:
                cur = m.group(1)
                out.setdefault(cur, {})
                continue
            m = SNIP_RE.match(line)
            if m and cur:
                out[cur][int(m.group(2))] = (m.group(1), m.group(3).strip())
    return out


def main():
    before, after = parse(sys.argv[1]), parse(sys.argv[2])
    with open(sys.argv[3], encoding="utf-8") as fh:
        p10 = {l.strip() for l in fh if l.strip()}
    flips_bad, flips_good, new, p10_fail = [], [], [], []
    for f, snips in sorted(after.items()):
        for n, (st, first) in sorted(snips.items()):
            prev = before.get(f, {}).get(n)
            if prev is None:
                new.append((f, n, st, first))
            elif prev[0] == "PASS" and st == "FAIL":
                flips_bad.append((f, n, first, prev[1]))
            elif prev[0] == "FAIL" and st == "PASS":
                flips_good.append((f, n, first, prev[1]))
            if f in p10 and st == "FAIL":
                p10_fail.append((f, n, first))
    tot = lambda d: (sum(1 for s in d.values() for v in s.values() if v[0] == "PASS"),
                     sum(len(s) for s in d.values()))
    print("before: %d/%d PASS" % tot(before))
    print("after:  %d/%d PASS" % tot(after))
    print("PASS->FAIL flips: %d" % len(flips_bad))
    for f, n, a, b in flips_bad:
        print("  %s #%d  now: %s  (before: %s)" % (f, n, a, b))
    print("FAIL->PASS flips: %d" % len(flips_good))
    for f, n, a, b in flips_good:
        print("  %s #%d  now: %s  (before: %s)" % (f, n, a, b))
    print("snippets with no before entry (new or renumbered): %d" % len(new))
    by_file = {}
    for f, n, st, first in new:
        by_file.setdefault(f, []).append(st)
    for f, sts in sorted(by_file.items()):
        print("  %s: %d new, %d PASS, %d FAIL%s" % (
            f, len(sts), sts.count("PASS"), sts.count("FAIL"),
            "" if f in p10 else "  (NOT a Phase 10 file)"))
    p10_in_after = sorted(f for f in after if f in p10)
    print("Phase 10 reference files in the run: %d" % len(p10_in_after))
    for f in p10_in_after:
        s = after[f]
        print("  %s: %d/%d PASS" % (f, sum(1 for v in s.values() if v[0] == "PASS"), len(s)))
    print("FAIL in a Phase 10 file: %d" % len(p10_fail))
    for f, n, first in p10_fail:
        print("  %s #%d  %s" % (f, n, first))
    # Same-number snippets whose first line changed: renumbering hint.
    moved = [(f, n) for f, s in after.items() for n, v in s.items()
             if n in before.get(f, {}) and before[f][n][1] != v[1]]
    print("same-number snippets whose first line differs (edited or renumbered): %d" % len(moved))
    for f, n in sorted(moved):
        print("  %s #%d  before: %s | after: %s" % (f, n, before[f][n][1], after[f][n][1]))
    return 1 if flips_bad or p10_fail else 0


if __name__ == "__main__":
    sys.exit(main())
