"""Serve Godot's class reference from the user's own engine binary.

`--dump-extension-api-with-docs` emits every class with its brief description,
full description, methods, properties and signals — about 12 MB for 4.7.2. It
is generated from whatever engine the user actually has, so answers stay
correct across versions without vendoring 29 MB of class reference that would
go stale (spec decision 7).

The dump is written to the cache directory and reused until the engine version
changes. Generating it costs about two seconds.

Two things make the caching less obvious than it looks.

First, the MCP server this module serves is long-lived and can field
overlapping calls. Two callers racing a cold cache must never both write
`extension_api.json` in place: each generates into its own private scratch
directory and only ever publishes with a single atomic `os.replace()`, so a
concurrent reader can only ever see one complete generation or another, never
a torn mix of both.

Second, a dump on disk can go bad by routes this module doesn't control — a
process killed mid-write, a full disk — and a `json.JSONDecodeError` on every
future call, forever, is worse than the cost of one extra regeneration. A bad
dump is deleted and regenerated once rather than wedging the cache
permanently; the user has no way to know `~/.cache/claude-godot-plugin`
exists to delete it by hand.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time

from . import engine

# cache_dir -> {"version": str, "dump": dict, "checked_at": float}
# "checked_at" is a time.monotonic() reading from the last time this entry's
# version was SUCCESSFULLY confirmed against the live engine -- see
# _REVALIDATE_INTERVAL_SECONDS and load_dump's warm-hit branch.
_CACHE: dict = {}

# Revalidating a warm cache entry costs one `godot --version` subprocess
# spawn -- measured at ~17.5ms, all of it process-spawn overhead. An agent
# session can call lookup_class/search_classes dozens of times, and paying
# that cost on every single call is pure waste when the engine practically
# never changes underfoot. Revalidate at most this often per cache_dir
# instead: still catches an engine upgrade in a long-lived MCP server (the
# property Finding 5 bought), just not on every call.
_REVALIDATE_INTERVAL_SECONDS = 60

# Every real Godot version string starts with a dotted numeric build
# (4, 4.7 or 4.7.2) followed by a dotted word segment (.stable, .dev, ...).
# Real installs always carry a build-hash suffix after that
# (".official.ed1daf0bf"), but this pattern only needs to anchor the front:
# it exists to reject banner/driver lines that can precede the version line
# on some builds, not to validate the whole string.
_VERSION_LINE = re.compile(r"^\d+\.\d+(\.\d+)?\.\w+")

# Stashed directly on a loaded dump dict (not keyed through _CACHE) so that
# building/reading the search index never needs a second, separate lookup
# into _CACHE after load_dump has already returned that dump object -- see
# _search_index.
_SEARCH_INDEX_KEY = "__api_search_index__"


def _default_cache_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    path = os.path.join(base, "claude-godot-plugin")
    os.makedirs(path, exist_ok=True)
    return path


def _resolve_cache_dir(cache_dir: str | None) -> str:
    return cache_dir or _default_cache_dir()


def engine_version() -> str:
    """Return the running engine's version, e.g.
    "4.7.2.stable.official.ed1daf0bf" -- every real install's --version
    output carries a build-hash suffix; a literal without one (as in an
    earlier draft of this module's own tests) does not match any real
    install.

    Scans every line of stdout, then every line of stderr, for the first one
    that looks like a version, rather than trusting stdout.splitlines()[0]:
    some builds print a banner line ahead of the version, blank/whitespace-only
    stdout must fall through to stderr rather than being treated as present,
    and empty output must raise a clear error instead of a bare IndexError.
    """
    result = engine.run(["--version"], timeout=15)
    for stream in (result.stdout, result.stderr):
        for line in (stream or "").splitlines():
            candidate = line.strip()
            if candidate and _VERSION_LINE.match(candidate):
                return candidate
    # A timeout reaches here too, because run() SIGKILLs the child and a killed
    # engine prints nothing -- indistinguishable from a build with unparseable
    # version output unless we say which one happened.
    if result.timed_out:
        raise RuntimeError(
            "Godot did not print a version within 15s; the process was killed. "
            "Check that GODOT_BIN (or the `godot` on PATH) is a real engine "
            "binary and not a wrapper that waits on input."
        )
    raise RuntimeError(
        "Godot's --version output did not contain a recognizable version "
        f"string. stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _read_dump(dump_path: str) -> dict:
    with open(dump_path) as f:
        return json.load(f)


def _generate_dump(cache_dir: str, dump_path: str) -> None:
    """Run Godot's dump into a private scratch directory, then publish it
    onto `dump_path` with a single atomic `os.replace()`.

    This is the fix for the concurrency half of the caching race: writing
    the engine's own output straight at `dump_path` lets two overlapping
    cold-cache callers interleave their writes into one corrupt file. A
    private `tempfile.mkdtemp(dir=cache_dir)` per call means each writer's
    output is only ever a complete file before it's ever visible at
    `dump_path`, and `os.replace()` on the same filesystem is atomic, so a
    racing reader can only ever observe one complete generation or another.
    """
    if not os.access(cache_dir, os.W_OK):
        raise RuntimeError(
            f"Cache directory {cache_dir!r} is not writable by this "
            "process; cannot generate extension_api.json. Check its "
            "permissions."
        )
    scratch = tempfile.mkdtemp(dir=cache_dir)
    try:
        result = engine.run(
            ["--headless", "--dump-extension-api-with-docs"],
            cwd=scratch,
            timeout=120,
        )
        scratch_dump = os.path.join(scratch, "extension_api.json")
        if not os.path.isfile(scratch_dump):
            # Both a timeout and a genuine failure land here with no file, so
            # name which one rather than reporting the symptom for both.
            if result.timed_out:
                raise RuntimeError(
                    "Godot did not finish dumping the class reference within "
                    "120s; the process was killed and no cache was written. "
                    "The dump is a one-time cost per engine version -- retry, "
                    "and it will be served from cache afterwards."
                )
            raise RuntimeError(
                f"Godot did not produce extension_api.json in {scratch!r} "
                f"(cache dir {cache_dir!r})."
            )
        os.replace(scratch_dump, dump_path)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _regenerate(cache_dir: str, dump_path: str, version_path: str, current: str | None) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    _generate_dump(cache_dir, dump_path)
    version = current or engine_version()
    with open(version_path, "w") as f:
        f.write(version)
    return version


def load_dump(cache_dir: str | None = None) -> dict:
    cache_dir = _resolve_cache_dir(cache_dir)
    now = time.monotonic()

    entry = _CACHE.get(cache_dir)
    if entry is not None:
        if now - entry["checked_at"] < _REVALIDATE_INTERVAL_SECONDS:
            # Revalidated recently enough -- serve without spawning
            # anything. This is what makes the check below cheap in
            # practice: it only runs at most once per cache_dir per
            # _REVALIDATE_INTERVAL_SECONDS, not on every call.
            return entry["dump"]
        # A warm hit outside the window still has to check the live engine
        # version: without this, a Godot upgrade in this long-lived MCP
        # server stays invisible until the process restarts, and every
        # answer keeps coming from the old engine's API for the rest of its
        # life. But a failed CHECK is not evidence the cached dump itself is
        # stale -- a flaky subprocess spawn, or engine_version() itself
        # raising because --version transiently printed nothing
        # recognizable, says nothing about whether the dump we already have
        # is wrong. Serve it rather than fail a request that would
        # otherwise have succeeded; do not advance checked_at on failure, so
        # the next call retries instead of waiting out the window.
        try:
            live = engine_version()
        except Exception:
            return entry["dump"]
        entry["checked_at"] = now
        if live == entry["version"]:
            return entry["dump"]
        _CACHE.pop(cache_dir, None)  # Stale -- fall through and re-derive.

    dump_path = os.path.join(cache_dir, "extension_api.json")
    version_path = os.path.join(cache_dir, "VERSION")

    current = None
    checked_ok = False
    if os.path.isfile(dump_path):
        # A missing VERSION file (not just a missing dump) must still be
        # treated as "no cached version on record" rather than skipping the
        # check entirely -- a process killed between writing the dump and
        # writing VERSION leaves exactly dump-present/VERSION-missing, and
        # skipping the check here would serve that dump forever without ever
        # calling engine_version() again to notice and repair it.
        cached_version = None
        if os.path.isfile(version_path):
            with open(version_path) as f:
                cached_version = f.read().strip()
        try:
            current = engine_version()
            checked_ok = True
        except engine.MissingBinary:
            current = cached_version  # Serve the cache when the binary is gone.
        if cached_version != current:
            os.remove(dump_path)

    if not os.path.isfile(dump_path):
        # _regenerate resolves and writes a live version (calling
        # engine_version() itself if `current` isn't already known), and a
        # failure here is a genuine "cannot produce a dump at all" -- unlike
        # the warm path above, this is not caught broadly.
        current = _regenerate(cache_dir, dump_path, version_path, current)
        checked_ok = True

    try:
        dump = _read_dump(dump_path)
    except (json.JSONDecodeError, OSError):
        # Corrupt on disk -- self-heal by regenerating once instead of
        # raising the same JSONDecodeError on every future call forever.
        os.remove(dump_path)
        current = _regenerate(cache_dir, dump_path, version_path, current)
        checked_ok = True
        dump = _read_dump(dump_path)

    _CACHE[cache_dir] = {
        "version": current,
        "dump": dump,
        "checked_at": now if checked_ok else float("-inf"),
    }
    return dump


def _by_name(dump: dict) -> dict:
    return {c["name"].lower(): c for c in dump.get("classes", [])}


def lookup_class(name: str, member: str | None = None, cache_dir: str | None = None):
    dump = load_dump(cache_dir)
    index = _by_name(dump)
    found = index.get((name or "").lower())
    if not found:
        return None

    chain = []
    parent = found.get("inherits")
    while parent:
        chain.append(parent)
        parent = (index.get(parent.lower()) or {}).get("inherits")

    out = {
        "name": found["name"],
        "inherits": found.get("inherits"),
        "inheritance_chain": chain,
        "brief_description": found.get("brief_description"),
        "description": found.get("description"),
        "methods": found.get("methods", []),
        "properties": found.get("properties", []),
        "signals": found.get("signals", []),
    }

    if member:
        needle = member.lower()
        for group in ("methods", "properties", "signals"):
            for entry in out[group]:
                if entry.get("name", "").lower() == needle:
                    out["member"] = entry
                    out["member_kind"] = group
                    return out
        out["member"] = None
    return out


def _search_index(dump: dict) -> list:
    """The lowercased search corpus for this dump object, built once and
    reused across calls to `search_classes`.

    Descriptions are the bulk of the ~12 MB dump, so lowercasing all of them
    on every query (rather than once per dump) would repeat that scan on
    every call. The index is cached directly on the dump object itself
    (under `_SEARCH_INDEX_KEY`) rather than through a second, separate
    `_CACHE[cache_dir]` lookup: `load_dump(cache_dir)` and re-indexing
    `_CACHE[cache_dir]` afterwards are two operations, not one, and a
    concurrent warm-hit revalidation on another thread can pop that entry in
    the gap between them (load_dump's own revalidation does exactly this on
    a version mismatch) -- which raised a bare KeyError out of the public
    search_classes. Operating on the dump object load_dump already handed
    back removes the gap entirely: there is no second _CACHE read to race.
    A version change replaces the whole entry with a brand new dump object
    (see `load_dump`), so this can never point at stale content either.
    """
    cached = dump.get(_SEARCH_INDEX_KEY)
    if cached is not None:
        return cached
    index = [
        (
            c.get("name", ""),
            c.get("name", "").lower(),
            c.get("brief_description") or "",
            (c.get("brief_description") or "").lower(),
            (c.get("description") or "").lower(),
            c.get("inherits"),
        )
        for c in dump.get("classes", [])
    ]
    dump[_SEARCH_INDEX_KEY] = index
    return index


def search_classes(query: str, limit: int = 25, cache_dir: str | None = None) -> list:
    dump = load_dump(cache_dir)
    index = _search_index(dump)
    needle = (query or "").lower()
    scored = []
    for name, name_lower, brief, brief_lower, desc_lower, inherits in index:
        if name_lower == needle:
            score = 0
        elif needle in name_lower:
            score = 1
        elif needle in brief_lower:
            score = 2
        elif needle in desc_lower:
            # Matching only name/brief_description misses classes that only
            # discuss a concept in their full description -- e.g. "gravity"
            # matches nothing in RigidBody2D's brief_description, but its
            # description covers gravity at length. Ranked below name/brief
            # hits so a precise match still sorts first.
            score = 3
        else:
            continue
        scored.append((score, name, {
            "name": name,
            "inherits": inherits,
            "brief_description": brief,
        }))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]
