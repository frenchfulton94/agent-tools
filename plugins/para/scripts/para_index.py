#!/usr/bin/env python3
"""Parse and render PARA.md — the user's project list.

Parsing is deliberately forgiving: a heading plus a dash list. Text after the
first em-dash is a human description and is never parsed for meaning. An
entry's section IS its P/A/R classification, which is why the user edits
sections rather than a separate field.
"""

import re

SECTIONS = {
    "projects": "1-Projects",
    "areas": "2-Areas",
    "resources": "3-Resources",
}
POLICY = ("never read", "never move")


class Index:
    def __init__(self, projects=None, areas=None, resources=None,
                 never_read=None, never_move=None):
        self.projects = projects or []
        self.areas = areas or []
        self.resources = resources or []
        self.never_read = never_read or []
        self.never_move = never_move or []

    def classify(self, name):
        """Return the destination folder for a name, or None if unlisted."""
        needle = name.strip().casefold()
        for entries, destination in (
            (self.projects, "1-Projects"),
            (self.areas, "2-Areas"),
            (self.resources, "3-Resources"),
        ):
            for entry in entries:
                if entry.casefold() == needle:
                    return destination
        return None

    def all_names(self):
        return list(self.projects) + list(self.areas) + list(self.resources)


def _entry_name(line):
    """'- client-redesign — ship the site — due X' -> 'client-redesign'."""
    body = line.lstrip().lstrip("-").strip()
    return re.split(r"\s+—\s+", body, maxsplit=1)[0].strip()


def parse_index(text):
    buckets = {key: [] for key in list(SECTIONS) + list(POLICY)}
    current = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().casefold()
            continue
        if current in buckets and line.lstrip().startswith("-"):
            name = _entry_name(line)
            if name:
                buckets[current].append(name)
    return Index(
        projects=buckets["projects"],
        areas=buckets["areas"],
        resources=buckets["resources"],
        never_read=buckets["never read"],
        never_move=buckets["never move"],
    )


def render_index(index, root, updated):
    lines = ["# PARA index", "", f"Root: {root}", f"Updated: {updated}", ""]
    for title, entries in (
        ("Projects", index.projects),
        ("Areas", index.areas),
        ("Resources", index.resources),
        ("Never read", index.never_read),
        ("Never move", index.never_move),
    ):
        lines.append(f"## {title}")
        lines.extend(f"- {entry}" for entry in entries)
        lines.append("")
    return "\n".join(lines)
