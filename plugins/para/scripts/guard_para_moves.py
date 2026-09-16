#!/usr/bin/env python3
"""PreToolUse guard for a PARA-managed root.

Reads a PreToolUse payload on stdin and returns a permission decision. Exit 0
always; the decision travels in the JSON body, matching
plugins/unraid-ops/scripts/guard_destructive_storage.py.

Scope is deliberate. The guard only has an opinion inside a root that apply.py
has registered, which means it fails open elsewhere. The alternative — judging
every rm anywhere — fires on ordinary work, and a hook that annoys gets
disabled, which fails open permanently and everywhere. Narrow and durable beats
broad and switched off.

No imports from the other para modules: the guard must never fail to load
because a sibling module has a problem.

Accepted limitations: this is a lexical guard over the literal command text.
It cannot see through backticks or $(...) command substitution, $HOME/~
expansion, an interpreter one-liner like `python3 -c "shutil.rmtree(...)"`,
a bare `cd` with no argument, `cd -`, or a bare relative path with no
preceding cd/pushd. Those are out of scope for a PreToolUse text match.
"""

import json
import os
import pathlib
import posixpath
import re
import shlex
import sys

DESTRUCTIVE = ("rm", "rmdir", "unlink", "shred", "trash")
RELOCATING = ("mv", "rename")
WRAPPERS = {"sudo", "doas", "env", "nohup", "time", "command", "exec", "builtin", "xargs"}
VALUE_FLAGS = {"-u", "-g", "-p", "-C", "-h", "--user", "--group", "--prompt"}
CWD_CHANGING = {"cd", "pushd"}

# Commands that only read. A destructive-looking token inside one of these
# (a grep pattern, a filename, an echoed string) is not an action — deletion
# is judged by finding the verb ANYWHERE in the token list once the leading
# word clears this exemption, so a read-only leader keeps that scan from
# ever firing. Deliberately NOT here: `find`, which both deletes (`-delete`)
# and runs arbitrary commands (`-exec rm {} \;`), so it must stay subject to
# the token scan. What made `find <root> -name rm` a false positive was the
# PREDICATE VALUE being read as a command name, and _scannable_tokens fixes
# exactly that without exempting find from the scan.
READ_ONLY = {
    "echo", "grep", "egrep", "fgrep", "rg", "cat", "less", "more", "head",
    "tail", "ls", "stat", "du", "df", "file", "wc", "test", "[", "printf",
    "diff", "cmp", "shasum", "md5sum", "sha256sum", "tree", "open", "bat",
    "awk", "sed", "wc", "sort", "uniq", "cut",
}

# find predicates whose next token is a VALUE (a name, a path, a user, a
# type), never a command. `-exec` and `-execdir` are pointedly absent: the
# token after those two IS a command, and must stay visible to the scan.
FIND_VALUE_PREDICATES = {
    "-name", "-iname", "-path", "-ipath", "-wholename", "-iwholename",
    "-lname", "-ilname", "-regex", "-iregex", "-user", "-group",
    "-newer", "-samefile", "-type", "-perm", "-size", "-inum", "-links",
}


def registry_path():
    override = os.environ.get("PARA_ROOTS_FILE")
    if override:
        return pathlib.Path(override)
    return pathlib.Path.home() / ".config" / "para" / "roots"


def registered_roots(path=None):
    target = pathlib.Path(path) if path else registry_path()
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [line.strip() for line in lines if line.strip()]


def segments(command):
    return [s for s in re.split(r"&&|\|\||[;|&\n]", command) if s.strip()]


def leading_word(segment):
    stripped = segment.strip().lstrip("({ \t")
    while stripped:
        while re.match(r"^\w+=\S*\s+", stripped):
            stripped = re.sub(r"^\w+=\S*\s+", "", stripped)
        match = re.match(r"^([\w./-]+)", stripped)
        if not match:
            return ""
        word = match.group(1).split("/")[-1]
        if word not in WRAPPERS:
            return word
        stripped = stripped[match.end():].strip()
        while stripped.startswith("-"):
            flag_match = re.match(r"^(\S+)", stripped)
            if not flag_match:
                break
            flag = flag_match.group(1)
            stripped = re.sub(r"^\S+\s*", "", stripped)
            if flag in VALUE_FLAGS and stripped and not stripped.startswith("-"):
                stripped = re.sub(r"^\S+\s*", "", stripped)
    return ""


def _tokens_of(segment):
    """Shell-aware tokens, so quoting is interpreted the way bash would.

    shlex understands that "/a/Documents'/x" is a path containing an
    apostrophe, while /a/"Documents"/x is just /a/Documents/x. Blanket
    quote-stripping got the first case wrong. Unbalanced quotes raise, so
    fall back to a crude split rather than having no opinion at all.
    """
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return [t.strip("'\"") for t in re.findall(r"'[^']*'|\"[^\"]*\"|[^\s;|&]+", segment)]


def touches_root(segment, roots):
    """Return the root a segment's path tokens actually fall inside."""
    for token in _tokens_of(segment):
        for root in roots:
            base = root.rstrip("/")
            if token == base or token.startswith(base + "/"):
                return root
    return None


def _cd_argument(segment):
    """First non-flag argument to a cd/pushd, or '' if there is none."""
    for part in _tokens_of(segment)[1:]:
        if not part.startswith("-"):
            return part
    return ""


def _deletes_by_flag(segment, lead):
    """Deletion that does not lead with a destructive verb."""
    if lead == "find" and re.search(r"(?:^|\s)-delete(?:\s|$)", segment):
        return True
    if lead == "rsync" and "--remove-source-files" in segment:
        return True
    if lead == "git" and re.search(r"^\s*git\s+clean\b", segment):
        # -n / --dry-run only previews. Denying a read-only command is how a
        # hook earns being switched off.
        if re.search(r"(?:^|\s)--dry-run(?:\s|$)|(?:^|\s)-[a-zA-Z]*n[a-zA-Z]*(?:\s|$)", segment):
            return False
        return True
    return False


def _scannable_tokens(tokens, lead):
    """Tokens that could name a command, with predicate VALUES removed.

    `find <root> -name rm` names a file to look for, not a command to run,
    while `find <root> -exec rm {} \\;` does name one. Dropping only the token
    after a value-taking predicate keeps the second visible while silencing
    the first — a blanket READ_ONLY exemption for `find` hid both.
    """
    if lead != "find":
        return tokens
    kept, skip = [], False
    for token in tokens:
        if skip:
            skip = False
            continue
        if token in FIND_VALUE_PREDICATES:
            skip = True
            continue
        kept.append(token)
    return kept


def _resolve_cd(cwd, argument):
    """Apply a cd/pushd argument lexically. None means 'no longer knowable'.

    Tracking the PATH rather than which-root-we-are-in is what lets `cd ..`
    from <root>/sub resolve back to <root>, while `cd ..` from <root> leaves.
    """
    if not argument or argument.startswith("-") or argument.startswith("~"):
        return None
    if argument.startswith("/"):
        return posixpath.normpath(argument)
    if cwd is None:
        return None
    return posixpath.normpath(posixpath.join(cwd, argument))


def _root_of(path, roots):
    """The registered root containing an absolute path, if any."""
    if not path:
        return None
    for root in roots:
        base = root.rstrip("/")
        if path == base or path.startswith(base + "/"):
            return root
    return None


def evaluate(command, roots):
    """Return (decision, reason), or None when the guard has no opinion."""
    if not roots:
        return None

    cwd = None
    for segment in segments(command):
        lead = leading_word(segment)

        # `cd <root> && rm -rf x` is an ordinary shape: after the cd, a bare
        # relative path is still inside the managed root. Track where we are,
        # not which root we are in, so `cd ..` resolves rather than guesses.
        if lead in CWD_CHANGING:
            cwd = _resolve_cd(cwd, _cd_argument(segment))
            continue

        root = touches_root(segment, roots) or _root_of(cwd, roots)
        if not root:
            continue

        # The verb's position does not matter: a wrapper flag we failed to
        # recognize as value-taking must not hide it. Scan every token once
        # the leading word clears the read-only exemption.
        tokens = _tokens_of(segment)
        scannable = _scannable_tokens(tokens, lead)
        deletes = lead in DESTRUCTIVE or (
            lead not in READ_ONLY and any(t in DESTRUCTIVE for t in scannable)
        )
        relocates = lead in RELOCATING or (
            lead not in READ_ONLY and any(t in RELOCATING for t in scannable)
        )

        if _deletes_by_flag(segment, lead) or deletes:
            return (
                "deny",
                f"This deletes inside the PARA root {root}. Deletion is not part of "
                "this plugin's vocabulary — archiving is a move. If something must "
                "go, move it to 4-Archives instead.",
            )
        if relocates:
            return (
                "deny",
                f"This moves files inside the PARA root {root} without going through "
                "apply.py, so no undo manifest would be written. Produce a plan and "
                "apply it, or run the move outside the managed root.",
            )
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Malformed payload: stay out of the way.

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        sys.exit(0)

    verdict = evaluate(command, registered_roots())
    if not verdict:
        sys.exit(0)

    decision, reason = verdict
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": f"[para] {reason}",
            }
        },
        sys.stdout,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
