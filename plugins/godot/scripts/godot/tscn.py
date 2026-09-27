"""Parse Godot .tscn and .tres files.

The grammar is documented in godot-docs/file_formats/tscn.rst, vendored beside
this plugin. Parsing is deliberately strict: an unrecognised construct raises
rather than being skipped, because a partial scene tree presented as complete
is how an agent deletes a node it never saw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"^\[([A-Za-z_][A-Za-z0-9_]*)(\s[^\]]*)?\]\s*$")
_ATTR = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=("(?:[^"\\]|\\.)*"|[^\s\]]+)')
_PROP = re.compile(r'^([A-Za-z_][A-Za-z0-9_/.]*(?:\[[^\]]*\])?)\s*=\s*(.*)$')


class TscnParseError(Exception):
    def __init__(self, line_no: int, reason: str, line: str = ""):
        super().__init__(f"line {line_no}: {reason}: {line.strip()}".rstrip(": "))
        self.line_no = line_no
        self.reason = reason
        self.line = line


@dataclass
class Block:
    kind: str
    attrs: dict
    props: dict
    line_no: int


@dataclass
class Node:
    name: str
    type: str | None = None
    parent: str | None = None
    instance: str | None = None
    props: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    path: str = ""


def _parse_attrs(text: str) -> dict:
    out = {}
    for key, value in _ATTR.findall(text or ""):
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        out[key] = value
    return out


def _incomplete(value: str) -> bool:
    """True when a property value continues on the next line."""
    depth = 0
    in_string = False
    escaped = False
    for ch in value:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_string:
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
    return depth > 0 or in_string


def parse(text: str) -> list:
    blocks: list = []
    current = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.strip()
        if not stripped or stripped.startswith(";"):
            continue

        heading = _HEADING.match(stripped)
        if heading:
            current = Block(
                kind=heading.group(1),
                attrs=_parse_attrs(heading.group(2)),
                props={},
                line_no=i,
            )
            blocks.append(current)
            continue

        prop = _PROP.match(stripped)
        if prop:
            if current is None:
                raise TscnParseError(i, "property before any heading", raw)
            key, value = prop.group(1), prop.group(2)
            while _incomplete(value) and i < len(lines):
                value += "\n" + lines[i]
                i += 1
            current.props[key] = value.strip()
            continue

        raise TscnParseError(i, "not a heading, property, or comment", raw)
    return blocks


def ext_resources(blocks: list) -> list:
    return [
        {
            "type": b.attrs.get("type"),
            "path": b.attrs.get("path"),
            "uid": b.attrs.get("uid"),
            "id": b.attrs.get("id"),
        }
        for b in blocks
        if b.kind == "ext_resource"
    ]


def scene_tree(blocks: list):
    nodes = []
    by_path = {}
    root = None

    for b in blocks:
        if b.kind != "node":
            continue
        name = b.attrs.get("name")
        if not name:
            raise TscnParseError(b.line_no, "node heading has no name")
        node = Node(
            name=name,
            type=b.attrs.get("type"),
            parent=b.attrs.get("parent"),
            instance=b.attrs.get("instance"),
            props=dict(b.props),
        )
        if node.parent is None:
            node.path = "."
            root = node
        elif node.parent == ".":
            node.path = name
        else:
            node.path = f"{node.parent}/{name}"
        if node.path in by_path:
            raise TscnParseError(b.line_no, f"duplicate node path {node.path!r}")
        by_path[node.path] = node
        nodes.append(node)

    for node in nodes:
        if node.parent is None:
            continue
        parent = by_path.get(node.parent)
        if parent is None:
            raise TscnParseError(
                0, f"node {node.path!r} names unknown parent {node.parent!r}"
            )
        parent.children.append(node)

    return root
