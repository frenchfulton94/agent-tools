"""Parse Godot .tscn and .tres files.

The grammar is documented in godot-docs/file_formats/tscn.rst, vendored beside
this plugin. Parsing is deliberately strict: an unrecognised construct raises
rather than being skipped, because a partial scene tree presented as complete
is how an agent deletes a node it never saw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"^\[([A-Za-z_][A-Za-z0-9_]*)(\s.*)?\]\s*$")
_ATTR_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
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


def _scan_value(text: str, start: int) -> int:
    """Return the index just past the balanced value beginning at `start`.

    A plain token ends at the first depth-0 whitespace. Brackets, braces,
    parens, and quoted strings (with backslash escapes) keep the value open
    across internal spaces, the same depth-and-quote tracking `_incomplete`
    uses to decide whether a *property* value continues on the next line —
    applied here within a single heading line instead. Real Godot 4.7.2
    output puts array- and constructor-valued attributes on node and
    connection headings (`groups=["a", "b"]`,
    `node_paths=PackedStringArray("a", "b")`), and a flat non-quote
    alternation stops at the first internal space or `]`, silently
    truncating the value instead of raising.
    """
    i = start
    n = len(text)
    depth = 0
    in_string = False
    escaped = False
    while i < n:
        ch = text[i]
        if escaped:
            escaped = False
        elif in_string:
            if ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth <= 0 and ch.isspace():
            break
        i += 1
    return i


def _parse_attrs(text: str, line_no: int) -> dict:
    out = {}
    text = text or ""
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        m = _ATTR_KEY.match(text, i)
        if not m:
            raise TscnParseError(
                line_no, f"expected attribute name near {text[i:i + 20]!r}", text
            )
        key = m.group(0)
        i = m.end()
        while i < n and text[i].isspace():
            i += 1
        if i >= n or text[i] != "=":
            raise TscnParseError(line_no, f"expected '=' after attribute {key!r}", text)
        i += 1
        # Godot's own writer sometimes emits a space between '=' and the
        # value (observed on `connection` headings' `binds=` attribute); skip
        # it rather than treating it as significant.
        while i < n and text[i].isspace():
            i += 1
        start = i
        i = _scan_value(text, start)
        value = text[start:i]
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
                attrs=_parse_attrs(heading.group(2), i),
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
