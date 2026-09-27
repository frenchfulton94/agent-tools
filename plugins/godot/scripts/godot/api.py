"""Serve Godot's class reference from the user's own engine binary.

`--dump-extension-api-with-docs` emits every class with its brief description,
full description, methods, properties and signals — about 12 MB for 4.7.2. It
is generated from whatever engine the user actually has, so answers stay
correct across versions without vendoring 29 MB of class reference that would
go stale (spec decision 7).

The dump is written to the cache directory and reused until the engine version
changes. Generating it costs about two seconds.
"""

from __future__ import annotations

import json
import os

from . import engine

_CACHE: dict = {}


def _default_cache_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    path = os.path.join(base, "claude-godot-plugin")
    os.makedirs(path, exist_ok=True)
    return path


def engine_version() -> str:
    result = engine.run(["--version"], timeout=15)
    return (result.stdout or result.stderr).strip().splitlines()[0].strip()


def load_dump(cache_dir: str | None = None) -> dict:
    cache_dir = cache_dir or _default_cache_dir()
    if cache_dir in _CACHE:
        return _CACHE[cache_dir]

    dump_path = os.path.join(cache_dir, "extension_api.json")
    version_path = os.path.join(cache_dir, "VERSION")

    current = None
    if os.path.isfile(dump_path) and os.path.isfile(version_path):
        cached_version = open(version_path).read().strip()
        try:
            current = engine_version()
        except engine.MissingBinary:
            current = cached_version  # Serve the cache when the binary is gone.
        if cached_version != current:
            os.remove(dump_path)

    if not os.path.isfile(dump_path):
        os.makedirs(cache_dir, exist_ok=True)
        engine.run(
            ["--headless", "--dump-extension-api-with-docs"],
            cwd=cache_dir,
            timeout=120,
        )
        if not os.path.isfile(dump_path):
            raise RuntimeError("Godot did not produce extension_api.json")
        open(version_path, "w").write(current or engine_version())

    dump = json.load(open(dump_path))
    _CACHE[cache_dir] = dump
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


def search_classes(query: str, limit: int = 25, cache_dir: str | None = None) -> list:
    dump = load_dump(cache_dir)
    needle = (query or "").lower()
    scored = []
    for entry in dump.get("classes", []):
        name = entry.get("name", "")
        brief = entry.get("brief_description") or ""
        if needle in name.lower():
            score = 0 if name.lower() == needle else 1
        elif needle in brief.lower():
            score = 2
        else:
            continue
        scored.append((score, name, {
            "name": name,
            "inherits": entry.get("inherits"),
            "brief_description": brief,
        }))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]
