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

Exit 0 when the manifest is written, 1 when any seed returns non-200.
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
LINK_STARTS = ("](/documentation/", "](/design/")


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


def extract_links(md: str) -> list:
    """Return documentation and design link targets in order, without duplicates.

    A target runs from the "(" after "](" to the ")" that closes it, tracking
    nested parentheses so `makeBuffer(length:options:)` stays whole. A target
    also ends at whitespace, which a path never contains. Fragments are dropped.
    """
    links = []
    seen = set()
    i = 0
    n = len(md)
    while i < n:
        hits = [j for j in (md.find(s, i) for s in LINK_STARTS) if j != -1]
        if not hits:
            break
        start = min(hits) + 2  # first character of the path
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
        target = md[start:j].split("#", 1)[0]
        if target and target not in seen:
            seen.add(target)
            links.append(target)
        i = max(j, start)
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
    collectionGroup is left out. A page reached by several seeds gets one row,
    attributed to the shallowest, then earliest, seed; a seed always keeps its
    own row. Paths compare case-insensitively and keep the first spelling seen.
    """
    rows = {}
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
                rows.setdefault(path.lower(), Row(path, seed.path, seed.bound, depth,
                                                  "", "", 0, code or 404, seed.dest))
                continue
            meta = page_meta(text)
            dtype = str(meta.get("documentType", ""))
            role = str(meta.get("role", ""))
            expandable = dtype == "article" or role == "collectionGroup"
            if depth == 0 or expandable:
                rows.setdefault(path.lower(), Row(path, seed.path, seed.bound, depth,
                                                  dtype, role, page_words(text), 200,
                                                  seed.dest))
            if not (depth == 0 or expandable):
                continue
            if seed.bound == "page" or (seed.bound == "depth1" and depth >= 1):
                continue
            scope = _scope(seed.path)
            for link in extract_links(text):
                if seed.bound == "recursive" and _scope(link) != scope:
                    continue
                nxt.append((link, depth + 1, idx))
        frontier = nxt
    return sorted(rows.values(), key=lambda r: r.path)


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


def main(argv=None) -> int:
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
    fetcher = Fetcher(args.cache, args.offline)
    rows = crawl(seeds, fetcher, fetcher.status, fetcher.prefetch)
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
