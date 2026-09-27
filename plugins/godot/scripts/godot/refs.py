"""Build the uid:// reference graph for a project and report what is broken.

Identity in Godot is carried three different ways, measured in spec 3.7:

  .gd, .gdshader      a .uid sidecar file beside the source
  imported assets     a .import sidecar carrying uid=
  .tscn, .tres        inline, in the [gd_scene]/[gd_resource] heading

A reference resolves if either the path still exists or the uid is still owned
by some file. A move that carries the sidecar keeps the uid and stays healthy
even though the .tscn still names the old path; a move that leaves the sidecar
behind mints a new uid and breaks the reference unrepairably (spec 3.4).

A scene or resource file is not the only thing that references a script.
project.godot's [autoload] section and its run/main_scene key name scripts
and scenes that no .tscn/.tres ext_resource entry ever points at -- nothing
in a scene references the main scene, and nothing references an autoload
except the engine reading project.godot at boot. Skipping that file would
report every autoload script as an orphan on every real project, which is
exactly the kind of false positive that gets a tool like this switched off.
So graph() treats project.overview(root)["autoloads"] and ["main_scene"] as
references too, alongside what it finds by walking scenes.

Walking a real project will meet .tscn/.tres files tscn.parse() cannot
parse -- a merge conflict left in a scene, a half-written save, a hand
edit gone wrong. graph() skips a file it cannot parse rather than raising
out of the whole call: one corrupt scene should not stop the tool from
reporting on the rest of the project. The cost is a false negative narrower
than it sounds -- a script referenced *only* from inside the unparsable
scene can be misreported as an orphan -- but that is preferable to refusing
to analyse the project at all over one bad file elsewhere in the tree.
"""

from __future__ import annotations

import os
import re

from . import project
from . import tscn

SCENE_EXT = (".tscn", ".tres")
SIDECAR_SOURCE_EXT = (".gd", ".gdshader")
SKIP_DIRS = {".godot", ".git", "addons"}
_UID_IN_IMPORT = re.compile(r'^uid="(uid://[^"]+)"', re.MULTILINE)


def _strip_res(path: str) -> str:
    return path[len("res://"):] if path.startswith("res://") else path


def _walk(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            yield full, os.path.relpath(full, root).replace(os.sep, "/")


def _uid_index(root: str):
    index: dict = {}
    duplicates: dict = {}

    def record(uid, rel):
        if not uid:
            return
        if uid in index and index[uid] != rel:
            duplicates.setdefault(uid, [index[uid]]).append(rel)
        else:
            index[uid] = rel

    for full, rel in _walk(root):
        if rel.endswith(".uid"):
            source = rel[: -len(".uid")]
            record(open(full).read().strip(), source)
        elif rel.endswith(".import"):
            match = _UID_IN_IMPORT.search(open(full, errors="replace").read())
            if match:
                record(match.group(1), rel[: -len(".import")])
        elif rel.endswith(SCENE_EXT):
            try:
                blocks = tscn.parse(open(full, errors="replace").read())
            except tscn.TscnParseError:
                continue
            if blocks and blocks[0].kind in ("gd_scene", "gd_resource"):
                record(blocks[0].attrs.get("uid"), rel)

    return index, [{"uid": u, "paths": p} for u, p in duplicates.items()]


def _project_references(root: str) -> set:
    """Paths named by project.godot itself: autoloads and the main scene.

    Neither is named from inside any .tscn/.tres ext_resource entry, so
    without this they would be reported as orphaned on every project.
    """
    if not os.path.isfile(os.path.join(root, "project.godot")):
        return set()

    overview = project.overview(root)
    referenced = set()
    for path in overview.get("autoloads", {}).values():
        target = _strip_res(path or "")
        if target:
            referenced.add(target)

    main_scene = _strip_res(overview.get("main_scene") or "")
    if main_scene:
        referenced.add(main_scene)

    return referenced


def graph(root: str) -> dict:
    index, duplicates = _uid_index(root)
    broken = []
    referenced = _project_references(root)

    for full, rel in _walk(root):
        if not rel.endswith(SCENE_EXT):
            continue
        try:
            blocks = tscn.parse(open(full, errors="replace").read())
        except tscn.TscnParseError:
            continue
        for res in tscn.ext_resources(blocks):
            path = (res.get("path") or "")
            uid = res.get("uid")
            target = _strip_res(path)
            path_exists = bool(target) and os.path.isfile(os.path.join(root, target))
            uid_target = index.get(uid) if uid else None

            if path_exists:
                referenced.add(target)
            elif uid_target:
                referenced.add(uid_target)
            else:
                broken.append(
                    {
                        "scene": rel,
                        "path": path,
                        "uid": uid,
                        "reason": "uid-not-found" if uid else "missing-path",
                    }
                )

    orphans = []
    for _, rel in _walk(root):
        if rel.endswith((".uid", ".import")) or rel.endswith(SCENE_EXT):
            continue
        if not rel.endswith(SIDECAR_SOURCE_EXT):
            continue
        if rel not in referenced:
            orphans.append(rel)

    return {
        "uid_index": index,
        "broken": broken,
        "orphans": sorted(orphans),
        "duplicate_uids": duplicates,
    }
