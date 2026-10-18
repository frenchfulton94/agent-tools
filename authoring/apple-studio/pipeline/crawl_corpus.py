#!/usr/bin/env python3
"""Crawl Apple documentation seeds into a deterministic corpus manifest.

Standard library only. Usage:

    crawl_corpus.py MAP... --out MANIFEST --cache DIR [--offline]

Each MAP lists seeds under a "## Seeds" heading, one per line:

    - <bound> <dest> <url>

`bound` is `recursive`, `depth1`, or `page`. The crawler fetches each page as
Markdown (`<url>.md`), keeps the raw text in the cache, and writes one manifest
row per page: path, seed, bound, depth, documentType, role, words, http, dest.
Every later reader and the ledger checker key off that manifest, so link
extraction and de-duplication are exact: a link is taken whole up to its closing
parenthesis, and paths are compared case-insensitively.

Exit 0 when the manifest is written and no seed is non-200. Exit 1 when a seed
returns non-200 (the manifest is still written). Exit 2, with no manifest, when any
fetch fails for a reason other than a real 404 or 410: a transport error, a 403,
429, or 5xx, or an `--offline` cache miss.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, NamedTuple, Optional

HOST = "https://developer.apple.com"
BOUNDS = ("recursive", "depth1", "page")
DESTS = ("apple-metal", "apple-games", "apple-performance", "app-release")
HEADER = ("path", "seed", "bound", "depth", "documentType", "role", "words", "http", "dest")
THREADS = 8
GONE = (404, 410)
LINK_STARTS = ("](/documentation/", "](/design/", "](doc://", "<doc://")


class Seed(NamedTuple):
    path: str
    bound: str
    dest: str


class Row(NamedTuple):
    path: str
    seed: str
    bound: str
    depth: int
    documentType: str
    role: str
    words: int
    http: int
    dest: str


def key(path: str) -> str:
    """Cache key: no leading slash, lowercase, "/" as "__", odd characters as "_"."""
    k = path.lstrip("/").lower().replace("/", "__")
    return re.sub(r"[^a-z0-9_.()'-]", "_", k)


_DOC_HOST = re.compile(r"\Adoc://[^/\s]+")
_HIG = re.compile(r"\A/design/human-interface-guidelines(?=/|\Z)", re.I)


def _doc_path(target: str):
    """Map a link target to a /documentation/... or /design/... path, or None.

    Accepts site-relative paths and `doc://<bundle>/...` URLs, whatever the
    bundle (`com.apple.documentation`, `com.apple.metal`, `com.apple.HIG`).
    Human Interface Guidelines links are spelled `/design/Human-Interface-
    Guidelines/...` in the `doc://` form; they map to the lowercase spelling
    the site paths use.
    """
    m = _DOC_HOST.match(target)
    if m:
        target = target[m.end():]
    target = target.split("#", 1)[0]
    if not (target.startswith("/documentation/") or target.startswith("/design/")):
        return None
    return _HIG.sub("/design/human-interface-guidelines", target, count=1)


def extract_links(md: str) -> list:
    """Return documentation and design link targets in order, without duplicates.

    Three forms are followed: `[t](/documentation/p)`, `[t](doc://bundle/documentation/p)`,
    and the autolink `<doc://bundle/documentation/p>`. A `](` target runs to the
    `)` that closes it, tracking nested parentheses so `makeBuffer(length:options:)`
    stays whole. An autolink runs to `>`. Either also ends at whitespace, which a
    path never contains. Fragments are dropped, and `doc://` targets map to the
    `/documentation/` or `/design/` path.
    """
    links = []
    seen = set()
    i = 0
    n = len(md)
    while i < n:
        hits = [(j, s) for s in LINK_STARTS for j in [md.find(s, i)] if j != -1]
        if not hits:
            break
        pos, starter = min(hits)
        if starter == "<doc://":
            start = pos + 1
            j = start
            while j < n and md[j] != ">" and not md[j].isspace():
                j += 1
        else:
            start = pos + 2
            depth = 1
            j = start
            while j < n:
                c = md[j]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif c.isspace():
                    break
                j += 1
        target = _doc_path(md[start:j])
        if target and target not in seen:
            seen.add(target)
            links.append(target)
        i = max(j, pos + 1)
    return links


_COMMENT = re.compile(r"\A\s*<!--(.*?)-->", re.S)


def page_meta(text: str) -> dict:
    m = _COMMENT.match(text)
    if not m:
        return {}
    try:
        meta = json.loads(m.group(1))
    except ValueError:
        return {}
    return meta if isinstance(meta, dict) else {}


def page_words(text: str) -> int:
    """Whitespace-separated tokens after the leading <!-- ... --> comment."""
    return len(_COMMENT.sub("", text, count=1).split())


def _scope(path: str) -> str:
    """First two path segments, lowercased: /documentation/metal."""
    return "/" + "/".join(path.lower().strip("/").split("/")[:2])


def _is_signature(path: str) -> bool:
    """True for a callable-signature path such as `.../expm1(_:)-mfq5`.

    Such a path names a function, method, or initializer symbol. Across the
    13,859 pages of the first full crawl, all 445 pages with "(" in the last
    segment were symbols and none was a collectionGroup, so the crawler does not
    fetch them. This also avoids Apple's edge, which answers 403 for some of them
    (the `expm1` family in Accelerate). A seed is never skipped.
    """
    return "(" in path.rsplit("/", 1)[-1]


def _attribute(lk: str, reach: dict, seeds: list):
    """Pick the seed a page's row belongs to. Returns (seed index, depth).

    `reach` maps each seed that reached the page to the shallowest depth.
    1. A seed keeps its own row (depth 0, earliest identical seed).
    2. A `recursive` seed that reached the page and whose scope (first two path
       segments) contains it, ordered by depth then map order. A recursive seed
       that merely covers the scope without reaching the page does not count:
       `os/workgroups` covers all of `/documentation/os`, which would otherwise
       claim the logging pages that only `os/logging` reaches.
    3. The shallowest reaching seed; at equal depth, one whose own scope is the
       page's scope; then the earliest.
    """
    own = [i for i, s in enumerate(seeds) if s.path.lower() == lk]
    if own:
        return own[0], 0
    scope = _scope(lk)
    covering = [i for i in reach
                if seeds[i].bound == "recursive" and _scope(seeds[i].path) == scope]
    pool = covering or list(reach)
    idx = min(pool, key=lambda i: (reach[i], _scope(seeds[i].path) != scope, i))
    return idx, reach[idx]


def crawl(seeds: list, fetch: Callable, status: Optional[Callable] = None,
          prefetch: Optional[Callable] = None) -> list:
    """Breadth-first crawl. Each seed is crawled under its own bound.

    `fetch(path)` returns the page text, or None when the page is not 200.
    `status(path)` returns the HTTP status for a None fetch (default 404).
    `prefetch(paths)` is called with each level's unique paths before they are
    processed, so a caller can fetch them in parallel.

    A page is expanded when it is a seed, or an article, or a collectionGroup,
    and its seed's bound allows it. A `recursive` seed follows only links that
    share its first two path segments. A non-seed symbol that is not a
    collectionGroup is left out. Paths compare case-insensitively and keep the
    first spelling seen.

    A page reached by several seeds gets one row, attributed (see `_attribute`)
    so that `dest` is topical: a seed keeps its own row; otherwise a `recursive`
    seed whose scope contains the page wins, shallowest then earliest; otherwise
    the shallowest seed, preferring at equal depth a seed that shares the page's
    first two path segments, then the earliest.
    """
    found = {}  # lowercased path -> [spelling, (documentType, role, words, http), {seed: depth}]
    visited = set()
    frontier = [(s.path, 0, i) for i, s in enumerate(seeds)]
    while frontier:
        if prefetch:
            uniq = []
            seen_here = set()
            for path, _, idx in frontier:
                lk = path.lower()
                if lk not in seen_here and (lk, idx) not in visited:
                    seen_here.add(lk)
                    uniq.append(path)
            prefetch(uniq)
        nxt = []
        for path, depth, idx in frontier:
            pair = (path.lower(), idx)
            if pair in visited:
                continue
            visited.add(pair)
            seed = seeds[idx]
            text = fetch(path)
            if text is None:
                code = status(path) if status else 404
                ob = found.setdefault(path.lower(), [path, ("", "", 0, code), {}])
                ob[2][idx] = min(depth, ob[2].get(idx, depth))
                continue
            meta = page_meta(text)
            dtype = str(meta.get("documentType", ""))
            role = str(meta.get("role", ""))
            expandable = dtype == "article" or role == "collectionGroup"
            if depth == 0 or expandable:
                ob = found.setdefault(path.lower(),
                                      [path, (dtype, role, page_words(text), 200), {}])
                ob[2][idx] = min(depth, ob[2].get(idx, depth))
            if not (depth == 0 or expandable):
                continue
            if seed.bound == "page" or (seed.bound == "depth1" and depth >= 1):
                continue
            scope = _scope(seed.path)
            for link in extract_links(text):
                if _is_signature(link):
                    continue
                if seed.bound == "recursive" and _scope(link) != scope:
                    continue
                nxt.append((link, depth + 1, idx))
        frontier = nxt
    rows = []
    for lk, (spelling, info, reach) in found.items():
        idx, depth = _attribute(lk, reach, seeds)
        seed = seeds[idx]
        rows.append(Row(spelling, seed.path, seed.bound, depth, *info[:3], info[3], seed.dest))
    return sorted(rows, key=lambda r: r.path)


def parse_map(text: str) -> list:
    """Read seed lines from the "## Seeds" section of a map file."""
    seeds = []
    in_seeds = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_seeds = line[3:].strip().lower() == "seeds"
            continue
        if not in_seeds or not line.startswith("- "):
            continue
        parts = line[2:].split()
        if not parts or parts[0] not in BOUNDS:
            continue  # prose bullet such as "- MISSING: ..."
        if len(parts) != 3 or parts[1] not in DESTS or not parts[2].startswith(HOST + "/"):
            raise ValueError("malformed seed line: " + line)
        path = parts[2][len(HOST):].split("#", 1)[0]
        if path.endswith(".md"):
            path = path[:-3]
        seeds.append(Seed(path, parts[0], parts[1]))
    return seeds


class Fetcher:
    """Cache-first page fetcher, safe to call from several threads."""

    def __init__(self, cache_dir: str, offline: bool = False):
        self.cache_dir = cache_dir
        self.offline = offline
        self.statuses = {}
        self.texts = {}
        self.lock = threading.Lock()
        os.makedirs(cache_dir, exist_ok=True)

    def _file(self, path: str) -> str:
        return os.path.join(self.cache_dir, key(path) + ".md")

    def _download(self, path: str):
        url = HOST + urllib.parse.quote(path, safe="/()'-._~:") + ".md"
        code = 0
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                code = e.code
                if code < 500 and code != 429:
                    return code, None
            except Exception:
                code = 0
            time.sleep(1 + attempt * 2)
        return code, None

    def __call__(self, path: str):
        lk = path.lower()
        with self.lock:
            if lk in self.texts:
                return self.texts[lk]
        f = self._file(path)
        text = None
        code = 200
        if os.path.exists(f):
            with open(f, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        elif os.path.exists(f + ".gone"):
            with open(f + ".gone", encoding="utf-8") as fh:
                code = int(fh.read().strip())
        elif self.offline:
            code = 0
        else:
            code, body = self._download(path)
            if code == 200 and body is not None:
                tmp = f + ".part-%d" % threading.get_ident()
                with open(tmp, "wb") as fh:
                    fh.write(body)
                os.replace(tmp, f)
                text = body.decode("utf-8", errors="replace")
            elif code in GONE:
                # Remember a real 404 or 410, so a re-run (and --offline) sees the same row.
                with open(f + ".gone", "w", encoding="utf-8") as fh:
                    fh.write("%d\n" % code)
        with self.lock:
            self.texts[lk] = text
            self.statuses[lk] = 200 if text is not None else code
        return text

    def status(self, path: str) -> int:
        return self.statuses.get(path.lower(), 0)

    def prefetch(self, paths: list):
        with cf.ThreadPoolExecutor(THREADS) as ex:
            list(ex.map(self, paths))


def write_manifest(rows: list, out: str):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\t".join(HEADER) + "\n")
        for r in rows:
            fh.write("\t".join(str(v) for v in r) + "\n")


def main(argv=None, fetcher_factory=Fetcher) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("maps", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--offline", action="store_true",
                    help="read the cache only; make no network request")
    args = ap.parse_args(argv)

    seeds = []
    for m in args.maps:
        with open(m, encoding="utf-8") as fh:
            seeds.extend(parse_map(fh.read()))
    fetcher = fetcher_factory(args.cache, args.offline)
    rows = crawl(seeds, fetcher, fetcher.status, fetcher.prefetch)

    # Only a real 404 or 410 from the server is a legitimate non-200 row. Any
    # other code (0 for a transport failure or an offline cache miss, 403, 429,
    # 5xx) means a page's subtree is missing, so the run fails and writes nothing.
    failed = [r for r in rows if r.http != 200 and r.http not in GONE]
    for r in failed:
        print("fetch failed: %s -> %s" % (r.path, r.http or "no response"), file=sys.stderr)
    if failed:
        print("manifest not written: %d fetch failure(s)" % len(failed), file=sys.stderr)
        return 2
    write_manifest(rows, args.out)

    seed_keys = {s.path.lower() for s in seeds}
    bad = [r for r in rows if r.path.lower() in seed_keys and r.http != 200]
    words = sum(r.words for r in rows)
    print("%d seeds, %d rows, %d words, %d rows not 200" %
          (len(seeds), len(rows), words, sum(1 for r in rows if r.http != 200)))
    for r in bad:
        print("seed not 200: %s -> %s" % (r.path, r.http), file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
