#!/usr/bin/env python3
"""Flag Tailwind v3-era syntax that behaves differently (or not at all) in v4.

Scans markup, component, and CSS files for constructs that changed in v4. Most
findings are SILENT failures: the class still compiles, but renders differently
than the author intended. Those are the ones worth catching mechanically,
because nothing in the build output points at them.

Deliberately a trap detector, not a class validator: projects define arbitrary
theme colors and custom utilities, so checking every token against a fixed
inventory produces noise. Every rule here is unambiguous regardless of theme.

Usage:
    python3 check_tailwind_v4.py FILE [FILE ...]
    python3 check_tailwind_v4.py --json src/components/Card.tsx
    cat page.html | python3 check_tailwind_v4.py -

Exit codes: 0 clean, 1 findings, 2 usage error. Data on stdout, errors on stderr.
"""

import argparse
import json
import re
import sys

# (regex, severity, message). SILENT = compiles but renders differently.
# BROKEN = the class no longer generates any CSS at all.
RULES = [
    # --- Renamed scales: still valid classes, different size. Silent. ---
    (r"(?<![\w/-])shadow-sm(?![\w-])", "SILENT",
     "v3 shadow-sm is v4 shadow-xs. In v4, shadow-sm is the old bare `shadow`."),
    (r"(?<![\w/-])shadow(?![\w-])", "SILENT",
     "Bare `shadow` is v3; v4 spells that size shadow-sm."),
    (r"(?<![\w/-])drop-shadow-sm(?![\w-])", "SILENT",
     "v3 drop-shadow-sm is v4 drop-shadow-xs."),
    (r"(?<![\w/-])drop-shadow(?![\w-])", "SILENT",
     "Bare `drop-shadow` is v3; v4 spells that size drop-shadow-sm."),
    (r"(?<![\w/-])blur-sm(?![\w-])", "SILENT",
     "v3 blur-sm is v4 blur-xs."),
    (r"(?<![\w/-])blur(?![\w-])", "SILENT",
     "Bare `blur` is v3; v4 spells that size blur-sm."),
    (r"(?<![\w/-])backdrop-blur-sm(?![\w-])", "SILENT",
     "v3 backdrop-blur-sm is v4 backdrop-blur-xs."),
    (r"(?<![\w/-])backdrop-blur(?![\w-])", "SILENT",
     "Bare `backdrop-blur` is v3; v4 spells that size backdrop-blur-sm."),
    (r"(?<![\w/-])rounded-sm(?![\w-])", "SILENT",
     "v3 rounded-sm is v4 rounded-xs."),
    (r"(?<![\w/-])rounded(?![\w-])", "SILENT",
     "Bare `rounded` is v3; v4 spells that radius rounded-sm."),
    (r"(?<![\w/-])ring(?![\w-])", "SILENT",
     "v4 `ring` is 1px currentColor, not 3px blue-500. Use ring-3 plus an explicit ring color."),

    # --- Removed utilities: generate nothing. Broken. ---
    (r"(?<![\w/-])(bg|text|border|divide|ring|placeholder)-opacity-\d+", "BROKEN",
     "Opacity utilities were removed. Use a color opacity modifier, e.g. bg-black/50."),
    (r"(?<![\w/-])flex-shrink(?:-\d+)?(?![\w-])", "BROKEN",
     "flex-shrink-* was removed. Use shrink-*."),
    (r"(?<![\w/-])flex-grow(?:-\d+)?(?![\w-])", "BROKEN",
     "flex-grow-* was removed. Use grow-*."),
    (r"(?<![\w/-])overflow-ellipsis(?![\w-])", "BROKEN",
     "overflow-ellipsis was removed. Use text-ellipsis."),
    (r"(?<![\w/-])decoration-(slice|clone)(?![\w-])", "BROKEN",
     "decoration-slice/clone were removed. Use box-decoration-slice/clone."),
    (r"(?<![\w/-])bg-gradient-to-(t|tr|r|br|b|bl|l|tl)(?![\w-])", "BROKEN",
     "bg-gradient-to-* is now bg-linear-to-*."),

    # --- Changed syntax ---
    (r"(?<![\w/-])(start|end)-(\d+|px|full|auto)(?![\w-])", "SILENT",
     "start-*/end-* are deprecated in favor of the logical inset utilities "
     "inset-s-*/inset-e-*. (col-start-*/row-start-* are unaffected.)"),
    (r"(?<![\w/-])outline-none(?![\w-])", "SILENT",
     "v4 outline-none really sets outline-style:none. For the v3 accessible "
     "invisible outline, use outline-hidden."),
    (r'class(?:Name)?="[^"]*(?<![\w-])!(?=[a-z])[a-z][\w:/-]*', "SILENT",
     "Leading `!` for important is deprecated. Put it at the end: bg-red-500!"),
    (r"(?<![\w/-])(bg|text|border|fill|stroke|shadow|ring|outline|accent|caret)-\[--[\w-]+\]",
     "BROKEN",
     "CSS variable shorthand changed from [--var] to (--var), e.g. bg-(--brand)."),
    (r"(?<![\w/-])(grid-cols|grid-rows|object)-\[[^\]\s]*,", "BROKEN",
     "Commas are no longer treated as spaces in grid/object arbitrary values. "
     "Use underscores: grid-cols-[max-content_auto]."),
    (r"(?<![\w/-])transform-none(?![\w-])", "SILENT",
     "transform-none no longer resets rotate/scale/translate (they are individual "
     "properties now). Reset the specific one, e.g. scale-none."),
    (r"transition-\[[^\]]*\btransform\b[^\]]*\]", "SILENT",
     "transition-[...transform...] no longer covers rotate/scale/translate. "
     "List the individual properties, e.g. transition-[opacity,scale]."),
    (r"^\s*@tailwind\s+(base|components|utilities|screens|variants)\s*;", "BROKEN",
     'The @tailwind directives were removed. Use @import "tailwindcss";'),
    (r"@layer\s+utilities\s*\{", "SILENT",
     "@layer utilities no longer registers a real utility. Use @utility name { ... }."),
    (r"theme\(\s*(colors|spacing|screens|fontSize|borderRadius)\.", "SILENT",
     "theme() dot notation is deprecated. Use the CSS variable, e.g. var(--color-red-500), "
     "or theme(--breakpoint-xl) inside media queries."),
    (r"\bresolveConfig\b", "BROKEN",
     "resolveConfig was removed in v4. Read the generated CSS variables instead."),
    (r"\bcorePlugins\b", "BROKEN",
     "The corePlugins option is not supported in v4."),
    (r"^\s*(safelist|separator)\s*:", "BROKEN",
     'safelist/separator are unsupported in v4. Safelist via @source inline("...").'),
    (r'["\']?(tailwindcss)["\']?\s*:\s*\{\}', "BROKEN",
     "The PostCSS plugin moved to its own package: @tailwindcss/postcss."),
    (r"\b(autoprefixer|postcss-import)\b", "SILENT",
     "v4 handles imports and vendor prefixing itself; these can be removed."),
]

# Behavioral changes with no syntactic tell. Reported once per file when the
# triggering class appears, since the class itself is still correct.
CONTEXT_RULES = [
    (r"(?<![\w/-])(border|divide)(?:-[xytrblse]|-[bi][se])?(?![\w-])(?![^\"']*\b(?:border|divide)-(?:[a-z]+-\d{2,3}|white|black|transparent|current|inherit))",
     "Default border/divide color is currentColor in v4, not gray-200. Set a color explicitly."),
]

CSS_EXT = (".css", ".scss", ".pcss", ".sass", ".less", ".styl")

# Tokens that look like utility classes, for the bundle audit. Deliberately
# loose: the point is to flag files worth excluding, not to resolve every class.
CLASSY = re.compile(
    r"\b(?:(?:hover|focus|focus-visible|active|disabled|dark|group-hover|peer-checked|"
    r"sm|md|lg|xl|2xl|first|last|odd|even|print|motion-safe|motion-reduce):)*"
    r"(?:bg|text|border|divide|ring|outline|shadow|rounded|p|px|py|pt|pr|pb|pl|ps|pe|"
    r"m|mx|my|mt|mr|mb|ml|w|h|size|min-w|max-w|min-h|max-h|flex|grid|gap|space-x|space-y|"
    r"items|justify|self|place|inset|top|right|bottom|left|z|opacity|blur|scale|rotate|"
    r"translate|transition|duration|ease|delay|animate|font|tracking|leading|indent|"
    r"align|whitespace|break|cursor|select|resize|overflow|object|aspect|columns|order|"
    r"col|row|fill|stroke|accent|caret|decoration|underline|uppercase|lowercase|capitalize|"
    r"truncate|line-clamp|backdrop-blur|inline|block|table|contents|hidden|sr-only)"
    r"(?:-[a-z0-9./\[\]()%#-]+)?\b"
)


def audit_docs(text, filename):
    """Count utility-looking tokens in a file that Tailwind would scan."""
    tokens = {m.group(0) for m in CLASSY.finditer(text)}
    return sorted(tokens)


def scan(text, filename):
    findings = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(("//", "*", "<!--")) and "@tailwind" not in stripped:
            continue
        for pattern, severity, message in RULES:
            flags = re.M
            for m in re.finditer(pattern, line, flags):
                findings.append({
                    "file": filename,
                    "line": lineno,
                    "column": m.start() + 1,
                    "severity": severity,
                    "match": m.group(0)[:60],
                    "message": message,
                })
    seen_context = set()
    for lineno, line in enumerate(lines, 1):
        for pattern, message in CONTEXT_RULES:
            if message in seen_context:
                continue
            m = re.search(pattern, line)
            if m:
                seen_context.add(message)
                findings.append({
                    "file": filename,
                    "line": lineno,
                    "column": m.start() + 1,
                    "severity": "CHECK",
                    "match": m.group(0)[:60],
                    "message": message,
                })
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Flag Tailwind v3-era syntax that misbehaves in v4.")
    parser.add_argument("files", nargs="+",
                        help="files to scan; use - for stdin")
    parser.add_argument("--json", action="store_true",
                        help="emit findings as JSON on stdout")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress the clean-run message")
    parser.add_argument("--docs-audit", action="store_true",
                        help="report utility-looking tokens per file; use to find "
                             "documentation that is inflating the CSS bundle")
    args = parser.parse_args()

    if args.docs_audit:
        rows = []
        for path in args.files:
            try:
                if path == "-":
                    text, name = sys.stdin.read(), "<stdin>"
                else:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        text, name = fh.read(), path
            except (OSError, IOError) as exc:
                print(f"could not read {path}: {exc}", file=sys.stderr)
                continue
            rows.append((name, audit_docs(text, name)))
        if not rows:
            print("scanned 0 files; nothing was checked.", file=sys.stderr)
            return 2
        if args.json:
            json.dump({"files": [{"file": n, "count": len(t), "tokens": t}
                                 for n, t in rows]}, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return 0
        every = set()
        for name, toks in sorted(rows, key=lambda r: -len(r[1])):
            every |= set(toks)
            print(f"{len(toks):5}  {name}")
        print(f"{len(every):5}  DISTINCT ACROSS ALL FILES")
        if every:
            print("\nTailwind generates CSS for tokens like these wherever they "
                  "appear, including\nmarkdown tables and code fences. If these "
                  "files are not application source,\nexclude them from the "
                  'stylesheet:\n\n    @source not "../path/to/docs";')
        return 0

    all_findings = []
    scanned = 0
    unreadable = []
    for path in args.files:
        try:
            if path == "-":
                text, name = sys.stdin.read(), "<stdin>"
            else:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text, name = fh.read(), path
        except (OSError, IOError) as exc:
            unreadable.append(path)
            print(f"could not read {path}: {exc}. Expected a readable text file; "
                  f"check the path and try again.", file=sys.stderr)
            continue
        scanned += 1
        all_findings.extend(scan(text, name))

    # A file that was never opened must not be reported as clean.
    if scanned == 0:
        print("scanned 0 files; nothing was checked.", file=sys.stderr)
        return 2

    if args.json:
        json.dump({"findings": all_findings, "count": len(all_findings)},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        order = {"BROKEN": 0, "SILENT": 1, "CHECK": 2}
        for f in sorted(all_findings,
                        key=lambda x: (order.get(x["severity"], 3), x["file"], x["line"])):
            print(f'{f["file"]}:{f["line"]}:{f["column"]}: '
                  f'{f["severity"]} [{f["match"]}] {f["message"]}')
        if not all_findings and not args.quiet:
            note = f" ({len(unreadable)} file(s) unreadable)" if unreadable else ""
            print(f"No v3-era Tailwind constructs found in {scanned} file(s){note}.")

    return 1 if all_findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
