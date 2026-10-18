#!/usr/bin/env python3
"""Names the heaviest symbol inside one signpost interval, from an xctrace export.

    heaviest_under_interval.py <trace> --subsystem <id> --interval <name>
        [--work-dir <dir>] [--top <n>]

Task 9, claim R4. The script knows only the signpost: a subsystem and an
interval name. It does not know which function the probe slowed down, and it
never searches for a function name. It does these steps:

1. `xctrace export --toc` lists the tables in run 1.
2. It exports the signpost-interval table. The rows whose name and subsystem
   match give the time ranges, each on its own thread.
3. It exports each CPU table that the trace holds: the `processor-trace-*`
   tables, and `time-profile` or `cpu-profile` when they are present. For each
   table it prints the columns, so the log shows what the export contains.
4. It charges CPU cost to symbols inside the time ranges, on the same thread:
   - Sample rows, which have a backtrace: the weight of the row (its cycles,
     else its weight, else 1) goes to the leaf function. That is self weight.
     xctrace lists code inlined into a function as extra frames at the same
     address; those frames count as the function that holds them.
   - Interval rows, which have a start, a duration and a symbol: the time of
     each range goes to the innermost interval that is open, and cycles are
     shared out in proportion to time. That is self time.
5. It prints the symbols for each table, heaviest first. For sample rows it
   also prints the raw leaf frame, with inlined frames not grouped, and the
   first backtrace that it charged to the heaviest symbol. Then one line:
   `heaviest symbol under '<interval>': <symbol> (<table>, <share>%)`.

Exit status: 0 when a table gave a verdict, 1 when no CPU table had rows
inside the intervals, and 2 when an export failed.
"""
import argparse
import bisect
import collections
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

CPU_SCHEMA = re.compile(r"^(processor-trace-.*|time-profile|cpu-profile)$")
SIGNPOST_SCHEMAS = ("OSSignpostIntervals", "os-signpost-interval")


def export(trace, out, xpath=None):
    cmd = ["xcrun", "xctrace", "export", "--input", trace, "--output", out]
    cmd += ["--xpath", xpath] if xpath else ["--toc"]
    shown = " ".join(c if " " not in c and "[" not in c else "'%s'" % c for c in cmd)
    print("$ " + shown.replace(os.path.dirname(out) + "/", "$WORK/"))
    done = subprocess.run(cmd, capture_output=True, text=True)
    print("exit: %d" % done.returncode)
    if done.returncode != 0:
        print((done.stdout + done.stderr).strip())
        sys.exit(2)


def table_xpath(schema):
    return '/trace-toc/run[@number="1"]/data/table[@schema="%s"]' % schema


class Value:
    """One cell: its text, its fmt, a frame name, and child cells by tag."""

    __slots__ = ("tag", "text", "fmt", "name", "addr", "inlined", "leaf", "frames", "children")

    def __init__(self, el, leaf, frames, children):
        self.tag, self.text, self.fmt = el.tag, (el.text or "").strip() or None, el.get("fmt")
        self.name, self.addr, self.inlined = el.get("name"), el.get("addr"), el.get("inlined")
        self.leaf, self.frames, self.children = leaf, frames, children

    def number(self):
        try:
            return int(self.text)
        except (TypeError, ValueError):
            return None

    def label(self):
        return self.name or self.fmt or self.text


def leaf_function(frames):
    """The function that was executing, from a leaf-first list of frames.

    Frames that share the leaf's address are one machine frame: code inlined
    into a function, which xctrace lists as frames of their own. The cost
    belongs to the function in the binary, the outermost frame of that group.
    """
    if not frames:
        return None
    k = 0
    while k + 1 < len(frames) and frames[0].addr and frames[k + 1].addr == frames[0].addr:
        k += 1
    return frames[k].label()


def read_tables(path):
    """Yields (schema, columns, rows) per <node>, with refs resolved.

    columns is a list of (mnemonic, engineering-type); each row is a list of
    Value or None, one per column. xctrace writes a repeated cell once with an
    id and later as <tag ref="id"/>, so every id is kept.
    """
    by_id = {}

    def value(el):
        ref = el.get("ref")
        if ref is not None:
            return by_id.get(ref)
        if el.tag == "sentinel":
            return None
        kids = [value(k) for k in el]
        children = {}
        for k in kids:
            if k is not None:
                children.setdefault(k.tag, k)
        frames = [k for k in kids if k is not None and k.tag == "frame"]
        leaf = leaf_function(frames)
        v = Value(el, leaf, frames, children)
        if el.get("id") is not None:
            by_id[el.get("id")] = v
        return v

    schema, columns = None, []
    read_tables.columns = {}
    for event, el in ET.iterparse(path, events=("start", "end")):
        if event == "start" and el.tag == "node":
            schema, columns = None, []
        elif event == "end" and el.tag == "schema":
            schema = el.get("name")
            columns = [(c.findtext("mnemonic"), c.findtext("engineering-type")) for c in el.findall("col")]
            read_tables.columns[schema] = columns
        elif event == "end" and el.tag == "row":
            yield schema, columns, [value(k) for k in el]
            el.clear()


def thread_id(v):
    if v is None:
        return None
    tid = v.children.get("tid")
    return tid.text if tid is not None else v.label()


def column(columns, *wanted):
    """Index of the first column whose mnemonic or engineering type matches."""
    for want in wanted:
        for i, (mnemonic, etype) in enumerate(columns):
            if re.fullmatch(want, mnemonic or "") or re.fullmatch(want, etype or ""):
                return i
    return None


def signpost_ranges(path, subsystem, name):
    ranges = collections.defaultdict(list)   # thread -> [(start, end)]
    for schema, cols, row in read_tables(path):
        i_start, i_dur = column(cols, "start"), column(cols, "duration")
        i_name, i_sub = column(cols, "name"), column(cols, "subsystem")
        i_thread = column(cols, "start-thread", "thread")
        cell = lambda i: row[i] if i is not None and i < len(row) else None
        n, s = cell(i_name), cell(i_sub)
        if n is None or s is None or n.label() != name or s.label() != subsystem:
            continue
        start, dur = cell(i_start), cell(i_dur)
        if start is None or dur is None or start.number() is None or dur.number() is None:
            continue
        if not ranges:
            print("first matching row: start %s (fmt %s), duration %s (fmt %s), thread %s"
                  % (start.text, start.fmt, dur.text, dur.fmt, cell(i_thread).label() if cell(i_thread) else None))
        ranges[thread_id(cell(i_thread))].append((start.number(), start.number() + dur.number()))
    for spans in ranges.values():
        spans.sort()
    return ranges


def overlap(spans, starts, a, b):
    """Total time that [a, b) shares with the sorted, disjoint spans."""
    total = 0
    k = max(bisect.bisect_right(starts, a) - 1, 0)
    while k < len(spans) and spans[k][0] < b:
        lo, hi = max(a, spans[k][0]), min(b, spans[k][1])
        if hi > lo:
            total += hi - lo
        k += 1
    return total


def charge(path, ranges):
    """Returns {schema: (mode, columns, rows seen, Counter symbol -> cost, unit,
    {symbol: the frames of its first backtrace}, Counter raw leaf frame -> cost)}."""
    starts = {t: [s for s, _ in spans] for t, spans in ranges.items()}
    any_thread = sorted(s for spans in ranges.values() for s in spans)
    any_starts = [s for s, _ in any_thread]
    result = {}
    open_calls = collections.defaultdict(list)   # (schema, thread) -> [(start, end, symbol, cycles)]
    for schema, cols, row in read_tables(path):
        cell = lambda i: row[i] if i is not None and i < len(row) else None
        i_bt = column(cols, r".*backtrace.*", "stack", "callstack")
        i_time = column(cols, "time", "sample-time", "start", "start-time", "timestamp")
        i_dur = column(cols, "duration")
        i_thread = column(cols, "thread")
        i_cycles = column(cols, r".*cycles.*")
        i_weight = column(cols, "weight")
        i_sym = column(cols, r".*symbol.*", r".*function.*", "frame", "name")
        entry = result.setdefault(schema, [None, cols, 0, collections.Counter(), "", {}, collections.Counter()])
        entry[2] += 1
        thread = thread_id(cell(i_thread))
        spans = ranges.get(thread) if thread is not None else any_thread
        span_starts = starts.get(thread) if thread is not None else any_starts
        t = cell(i_time)
        if not spans or t is None or t.number() is None:
            continue
        t0 = t.number()
        if i_bt is not None and i_dur is None:
            entry[0] = "samples: cost goes to the leaf function (self weight)"
            if overlap(spans, span_starts, t0, t0 + 1) == 0:
                continue
            bt = cell(i_bt)
            if bt is None or bt.leaf is None:
                continue
            for i, unit in ((i_cycles, "cycles"), (i_weight, "weight"), (None, "samples")):
                if i is None:
                    continue
                w = cell(i).number() if cell(i) is not None else None
                if w is not None:
                    break
            else:
                w, unit = 1, "samples"
            entry[3][bt.leaf] += w
            entry[4] = unit
            entry[5].setdefault(bt.leaf, bt.frames)
            entry[6][bt.frames[0].label()] += w
        elif i_dur is not None and (i_sym is not None or i_bt is not None):
            entry[0] = "intervals: time goes to the innermost open call (self time)"
            d = cell(i_dur)
            sym = cell(i_bt).leaf if i_bt is not None and cell(i_bt) is not None else None
            sym = sym or (cell(i_sym).label() if i_sym is not None and cell(i_sym) is not None else None)
            if d is None or d.number() is None or sym is None:
                continue
            cyc = cell(i_cycles).number() if i_cycles is not None and cell(i_cycles) is not None else None
            open_calls[(schema, thread)].append((t0, t0 + d.number(), sym, cyc))
    for (schema, thread), calls in open_calls.items():
        spans = ranges.get(thread) if thread is not None else any_thread
        span_starts = starts.get(thread) if thread is not None else any_starts
        entry = result[schema]
        entry[4] = "ns of self time"
        # Sweep the call boundaries: between two boundaries, the innermost
        # open call runs. Calls on one thread nest, so the innermost is the
        # top of a stack ordered by start, outer call first.
        calls.sort(key=lambda c: (c[0], -c[1]))
        stack, points = [], sorted({p for c in calls for p in c[:2]})
        k = 0
        for a, b in zip(points, points[1:]):
            while k < len(calls) and calls[k][0] <= a:
                stack.append(calls[k])
                k += 1
            while stack and stack[-1][1] <= a:
                stack.pop()
            if stack:
                entry[3][stack[-1][2]] += overlap(spans, span_starts, a, b)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--subsystem", required=True)
    ap.add_argument("--interval", required=True)
    ap.add_argument("--work-dir")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    trace = os.path.abspath(args.trace)
    work = os.path.abspath(args.work_dir or os.path.splitext(trace)[0] + "-export")
    os.makedirs(work, exist_ok=True)

    toc = os.path.join(work, "toc.xml")
    export(trace, toc)
    schemas = sorted({t.get("schema") for t in ET.parse(toc).iter("table") if t.get("schema")})
    print("tables in run 1: %d schemas" % len(schemas))
    print("  " + " ".join(schemas))
    for p in ET.parse(toc).iter("process"):
        if p.get("type") == "launched":
            print("launched process: " + " ".join('%s="%s"' % kv for kv in p.attrib.items()))

    signpost_schema = next((s for s in SIGNPOST_SCHEMAS if s in schemas), None)
    if signpost_schema is None:
        print("no signpost-interval table (looked for %s)" % ", ".join(SIGNPOST_SCHEMAS))
        return 1
    sp = os.path.join(work, signpost_schema + ".xml")
    export(trace, sp, table_xpath(signpost_schema))
    ranges = signpost_ranges(sp, args.subsystem, args.interval)
    for cols in read_tables.columns.values():
        print("columns: " + ", ".join("%s:%s" % c for c in cols))
    count = sum(len(v) for v in ranges.values())
    total = sum(b - a for v in ranges.values() for a, b in v)
    print("'%s' intervals in %s: %d, on %d thread(s), %.3f s in all"
          % (args.interval, args.subsystem, count, len(ranges), total / 1e9))
    if not count:
        return 1

    verdicts = []
    for schema in [s for s in schemas if CPU_SCHEMA.match(s)]:
        out = os.path.join(work, schema + ".xml")
        print()
        print("## %s" % schema)
        export(trace, out, table_xpath(schema))
        for name, (mode, cols, rows, cost, unit, examples, raw) in charge(out, ranges).items():
            print("columns: " + ", ".join("%s:%s" % c for c in cols))
            print("rows: %d" % rows)
            print("mode: %s" % (mode or "none: no backtrace, or no duration and symbol"))
            whole = sum(cost.values())
            if not whole:
                print("nothing charged inside the intervals")
                continue
            print("cost inside '%s' intervals: %d %s" % (args.interval, whole, unit))
            for sym, c in cost.most_common(args.top):
                print("  %6.2f%%  %s" % (100.0 * c / whole, sym))
            top, c = cost.most_common(1)[0]
            verdicts.append((name, top, 100.0 * c / whole))
            if raw:
                print("for comparison, the raw leaf frame, with inlined frames not grouped:")
                for sym, c in raw.most_common(3):
                    print("  %6.2f%%  %s" % (100.0 * c / whole, sym))
            if examples.get(top):
                print("first backtrace charged to %s, leaf first:" % top)
                for f in examples[top][:4]:
                    print("  addr %s  %s%s" % (f.addr, f.label(), "  (inlined=%s)" % f.inlined if f.inlined else ""))
    print()
    if not verdicts:
        print("no CPU table had rows inside the '%s' intervals" % args.interval)
        return 1
    # Processor Trace tables first: they are the claim; a sampler is a cross-check.
    verdicts.sort(key=lambda v: not v[0].startswith("processor-trace"))
    for name, top, share in verdicts:
        print("heaviest symbol under '%s': %s (%s, %.2f%%)" % (args.interval, top, name, share))
    return 0


if __name__ == "__main__":
    sys.exit(main())
