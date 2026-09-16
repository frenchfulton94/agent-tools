#!/usr/bin/env python3
"""Path safety for the para plugin.

Everything that decides whether a path may be touched lives here, so the
rules have one home and one test file. Nothing in this module deletes.
"""

import fnmatch
import os
import pathlib

# Bundles macOS presents as single items, plus dependency trees that are one
# item by their parent. Descending into any of these would scatter them.
PACKAGE_SUFFIXES = (
    ".app", ".rtfd", ".photoslibrary", ".musiclibrary", ".bundle",
    ".framework", ".pkg", ".xcodeproj", ".xcworkspace", ".playground",
)
PACKAGE_DIRS = (".git", "node_modules", ".venv", "venv", ".tox")

DEFAULT_NEVER_READ = (
    "**/.ssh/**", "**/.gnupg/**", "**/*.pem", "**/*.key", "**/*.kdbx",
    "**/.env*", "**/Keychains/**", "**/*.keychain*",
)

DEFAULT_NEVER_MOVE = (
    "**/*.app",
    "**/node_modules", "**/node_modules/**",
    "**/.git", "**/.git/**",
    "**/Library", "**/Library/**",
)

SKELETON = ("0-Inbox", "1-Projects", "2-Areas", "3-Resources", "4-Archives")


class UnsafeRoot(Exception):
    """The requested root is one this plugin refuses to organize."""


def validate_root(raw):
    """Resolve a user-supplied root, refusing the ones that are never safe."""
    path = pathlib.Path(raw).expanduser().resolve()
    home = pathlib.Path.home().resolve()

    if not path.is_dir():
        raise UnsafeRoot(f"{path} is not a directory.")
    if path == pathlib.Path("/"):
        raise UnsafeRoot("Refusing to organize the filesystem root.")
    if path == home:
        raise UnsafeRoot(
            "Refusing to organize your home directory. Name a subdirectory "
            "such as ~/Documents or ~/Downloads instead."
        )
    if path in home.parents:
        raise UnsafeRoot(f"Refusing to organize {path}: it is above your home directory.")
    return path


def volume_of(path):
    """Device id, for same-volume checks. A cross-volume mv is copy+delete."""
    return os.stat(path).st_dev


def is_package(path):
    """True when the path is one item, not a directory to descend into."""
    if path.name in PACKAGE_DIRS:
        return True
    return path.is_dir() and path.suffix.lower() in PACKAGE_SUFFIXES


def matches_any(path, root, patterns):
    """Glob-match a path against patterns, testing both absolute and relative."""
    absolute = str(path)
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = absolute
    for pattern in patterns:
        expanded = os.path.expanduser(pattern)
        for candidate in (absolute, relative, f"/{relative}"):
            if fnmatch.fnmatch(candidate, expanded):
                return True
    return False


def safe_destination(dest):
    """Return dest, or dest with ' (n)' appended until it is free.

    APFS is case-insensitive by default, so a case-only difference is a
    collision. exists() already reflects that, which is why this is a plain
    loop rather than a directory listing comparison.
    """
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
