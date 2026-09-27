#!/usr/bin/env python3
"""godot_guard.py -- analysis core for the godot plugin's PreToolUse guard.

godot-guard.sh (the hook's actual entry point) does no analysis itself; it
reads stdin, checks that python3 exists, and hands stdin to this module
untouched. Everything below is pure text analysis. It never executes,
`eval`s, or shells out to any part of the command it is examining -- it
only reads it.

## Why this is not a regex-over-the-whole-command guard

The first version of this guard (this plan's task 9, round 1) tested the
*whole command string* against a handful of patterns: "does 'mv' appear as
a word", "does '.gd' appear before whitespace or end-of-string", "does
'.uid' appear ANYWHERE in the command". That version shipped with two
confirmed bugs of increasing severity:

  - `\b` as a word-boundary assertion silently matches nothing under stock
    macOS bash (3.2, linked against the platform libc regex, not glibc) --
    caught in round 1, before this file existed.
  - A whole-command substring test cannot express "did THIS file's sidecar
    get named too" once more than one file, one statement, or one comment
    is on the line: `mv scripts/a.gd scripts/a.gd.uid scripts/b.gd
    entities/` has ".uid" in the command, but only a.gd is paired --
    b.gd's sidecar is never named, and the file is none the wiser. Same
    root cause makes `mv scripts/player.gd entities/player.gd; echo
    done.uid` and a `# ... .uid ...` comment both defeat the same check by
    putting ".uid" somewhere harmless. This is what forced the rewrite:
    the question "is this source's sidecar named in a move or copy
    statement anywhere in this command" is a per-argument, per-statement
    question, and answering it from raw text alone is not reliable.

So this module tokenizes with Python's `shlex` in POSIX mode with
`punctuation_chars` enabled, which -- confirmed empirically against every
adversarial input this plan's review produced -- correctly: strips
matching quotes, resolves backslash escapes, drops `# ...`-to-end-of-line
comments, and splits `;`, `&`, `&&`, `||`, `|`, `(`, `)` out as their own
tokens while leaving quoted content alone (so `grep "mv foo.gd"` keeps
"mv foo.gd" as ONE token, not three -- this is what makes `mv`/`rm`
detection based on "first word of a statement" immune to text that merely
*mentions* a move, without any separate command-position regex).

Known, accepted limits (documented rather than silently wrong):
  - Command substitution (`$(...)`, backticks) and pipelines with `(`/`)`
    subshells are treated as hard statement boundaries, not parsed. A
    filename computed via substitution cannot be reasoned about statically
    either way, so this is a limit shared with any static analysis of shell
    text, not a hole opened by this design specifically.
  - `positional_args` does not know which flags consume a following value
    (e.g. `mv -t DIR src`), so a flag's value can be misread as a bare
    positional argument. This is harmless here: an extra non-path token
    never matches a sidecar-bearing extension, so at worst it adds a token
    that is checked and ignored -- it does not suppress a real check.
  - Depends on python3, not jq. This plugin already requires python3 for
    its MCP server, so this trades one already-required dependency for
    another rather than adding a new one; jq is no longer used anywhere in
    this guard. Fails open (silent allow) exactly the same way if python3
    itself is somehow unreachable -- see godot-guard.sh.
"""
import json
import os
import shlex
import sys

# --- file-identity vocabulary (measured, spec 3.7 / 3.8) --------------------

SIDECAR_EXTS = frozenset({"gd", "gdshader"})  # .uid sidecar beside the file
ASSET_EXTS = frozenset({
    "png", "jpg", "jpeg", "webp", "svg", "wav", "ogg", "mp3",
    "glb", "gltf", "fbx", "obj", "ttf", "otf",
})  # .import sidecar beside the file
INLINE_UID_EXTS = frozenset({"tscn", "tres"})  # uid:// lives inside the file
SIDECAR_SUFFIX = ".uid"
ASSET_SUFFIX = ".import"

MOVE_KEYWORDS = frozenset({"mv"})
COPY_KEYWORDS = frozenset({"cp", "install"})
SHELL_C_KEYWORDS = frozenset({"sh", "bash", "zsh"})
STATEMENT_BOUNDARY_TOKENS = frozenset({";", "&", "&&", "||", "|", "(", ")", "`", "\n"})
PROJECT_CONFIG_BASENAMES = frozenset({"project.godot", "export_presets.cfg"})


def _ci(s):
    """Fold for comparison only -- macOS's default filesystem is
    case-insensitive, so 'Scripts/Player.GD' and 'scripts/player.gd.uid'
    can name the same two files. Never used for anything sent to disk."""
    return s.casefold()


def ext_of(token):
    """Lowercased final extension of the token's own basename, without the
    dot; '' for a directory-like token (trailing slash), one with no dot,
    or a dotfile with no further dot (".godot", ".gitignore" have no
    "extension" in the sense this guard cares about). Uses only the final
    path component so a dot in an ancestor directory's name (rare, but
    real: "my.project/entities") can never be mistaken for this token's
    own extension."""
    name = os.path.basename(token.rstrip("/"))
    if name.startswith(".") and name.count(".") == 1:
        return ""
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1].lower()


def is_sidecar_bearing(token):
    return ext_of(token) in SIDECAR_EXTS


def is_asset(token):
    return ext_of(token) in ASSET_EXTS


def sidecar_name_for(token):
    """The sidecar filename this token would need if it is a move/copy
    source, or None if this token's type carries its uid:// inline (or has
    no sidecar concept at all)."""
    if is_sidecar_bearing(token):
        return token + SIDECAR_SUFFIX
    if is_asset(token):
        return token + ASSET_SUFFIX
    return None


# --- tokenizing ---------------------------------------------------------


def tokenize(command):
    """Whole-command shlex tokenization. Never executes anything -- shlex
    only lexes text, it does not evaluate command substitution or expand
    variables. Returns [] on unbalanced quotes rather than raising: a
    guard that cannot parse a command must fail open on it, not crash."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        raw = list(lexer)
    except ValueError:
        return []
    # A backslash-newline line continuation survives shlex as a literal
    # newline character, either as its own token or glued to the front of
    # the next word (measured). Stripping leading/trailing whitespace from
    # every token, and dropping any that go empty, recovers the intended
    # tokens in both shapes without affecting normal quoted arguments.
    tokens = [t.strip() for t in raw]
    return [t for t in tokens if t != ""]


def split_statements(tokens):
    """Split a flat token stream into simple-command statements at shell
    control operators."""
    statements = []
    current = []
    for tok in tokens:
        if tok in STATEMENT_BOUNDARY_TOKENS:
            if current:
                statements.append(current)
                current = []
        else:
            current.append(tok)
    if current:
        statements.append(current)
    return statements


def first_word(statement):
    return statement[0].lower() if statement else ""


def _is_git_prefixed(statement, sub):
    return (
        len(statement) > 1
        and first_word(statement) == "git"
        and statement[1].lower() == sub
    )


def positional_args(statement):
    """Non-flag tokens after the command name(s). See the module docstring
    for the accepted imprecision around flags that consume a value."""
    skip = 1
    if _is_git_prefixed(statement, "mv") or _is_git_prefixed(statement, "rm"):
        skip = 2
    out = []
    for tok in statement[skip:]:
        if tok.startswith("-") and tok != "-":
            continue
        out.append(tok)
    return out


def is_move_statement(statement):
    fw = first_word(statement)
    if fw in MOVE_KEYWORDS:
        return True
    if _is_git_prefixed(statement, "mv"):
        return True
    if fw == "rsync" and any(t.lower() == "--remove-source-files" for t in statement[1:]):
        return True
    return False


def is_copy_statement(statement):
    return first_word(statement) in COPY_KEYWORDS


def is_remove_statement(statement):
    return first_word(statement) == "rm" or _is_git_prefixed(statement, "rm")


def find_exec_substatements(statement):
    """Yield (predicate_exts, sub_statement_tokens) for every -exec/-execdir
    block inside a `find` statement. predicate_exts is the set of
    extensions implied by whichever -name/-iname pattern appeared earlier
    in the SAME find statement -- best-effort, not a full evaluation of
    find's boolean expression grammar."""
    if first_word(statement) != "find":
        return
    seen_exts = set()
    i = 0
    n = len(statement)
    while i < n:
        tok = statement[i]
        low = tok.lower()
        if low in ("-name", "-iname") and i + 1 < n:
            e = ext_of(statement[i + 1])
            if e:
                seen_exts.add(e)
            i += 2
            continue
        if low in ("-exec", "-execdir") and i + 1 < n:
            j = i + 1
            sub = []
            while j < n and statement[j] not in (";", "+"):
                sub.append(statement[j])
                j += 1
            if sub:
                yield (frozenset(seen_exts), sub)
            i = j + 1
            continue
        i += 1


def flatten(command, depth=0, max_depth=6):
    """Flatten a command into {"tokens": [...], "exts": frozenset()}
    entries: its own top-level statements, plus -- recursively, to a
    bounded depth -- the inner command of every `sh -c` / `bash -c` /
    `zsh -c` statement, and the exec'd sub-command of every `find`
    -exec/-execdir block. This lets every later pass (sidecar-pairing,
    ask checks) treat a nested shell's contents exactly like top-level
    statements, instead of special-casing recursion order at each check
    site."""
    entries = []
    if depth > max_depth:
        return entries
    tokens = tokenize(command)
    for stmt in split_statements(tokens):
        entries.append({"tokens": stmt, "exts": frozenset()})
        fw = first_word(stmt)
        if fw in SHELL_C_KEYWORDS and len(stmt) >= 3 and stmt[1] == "-c":
            entries.extend(flatten(stmt[2], depth + 1, max_depth))
        if fw == "find":
            for exts, sub in find_exec_substatements(stmt):
                entries.append({"tokens": sub, "exts": exts})
    return entries


# --- disk-aware sidecar check (spec: cwd is a common PreToolUse field) ------


def _resolve(cwd, path):
    if not path:
        return None
    if os.path.isabs(path):
        return path
    if not cwd:
        return None
    return os.path.join(cwd, path)


def sidecar_confirmed_absent(cwd, token):
    """True only when we have positive, on-disk evidence that this
    sidecar-bearing SOURCE token has no established uid:// identity to
    lose -- either the file does not exist yet, or it exists but its
    sidecar does not (never imported). False means "cannot tell" (no cwd,
    unresolvable path, or a real stat error), and the caller must treat
    that as "assume it matters", not as permission to skip the check --
    absence of proof is not proof of safety."""
    sidecar = sidecar_name_for(token)
    if sidecar is None:
        return False
    resolved = _resolve(cwd, token)
    resolved_sidecar = _resolve(cwd, sidecar)
    if resolved is None or resolved_sidecar is None:
        return False
    try:
        return not os.path.lexists(resolved) or not os.path.lexists(resolved_sidecar)
    except OSError:
        return False


# --- messages ----------------------------------------------------------

DENY_MOVE_MSG = (
    "This moves a .gd, .gdshader, or imported asset without its sidecar "
    "(.uid for a script or shader, .import for an asset). Godot keeps that "
    "file's identity in the sidecar: move the file alone and the next "
    "import mints a new UID, while every scene referencing it still names "
    "the old one. No reimport reconciles that -- the references are "
    "repaired by hand, one at a time. Move both files in the same command "
    "(for example 'mv a.gd b/a.gd && mv a.gd.uid b/a.gd.uid'), or move the "
    "whole containing directory instead (the sidecar travels with it), and "
    "then run 'godot --headless --path . --import' -- or do the move in "
    "the Godot editor, which handles the sidecar for you. If you were only "
    "quoting or searching for this text, run that lookup yourself; this "
    "guard reasons about arguments to mv/cp/install/rsync/find -exec and "
    "cannot tell a mention inside an unrelated command from a real move."
)

DENY_COPY_REMOVE_MSG = (
    "This copies a .gd, .gdshader, or imported asset to a new path and "
    "then removes the original -- which is a move in every way that "
    "matters here, just spelled as two commands. The sidecar (.uid or "
    ".import) was not also copied, so the next import mints a new UID at "
    "the new path while every existing scene reference still names the "
    "old one. Copy the sidecar alongside the file (or move both with "
    "'mv', or move the whole containing directory), then run "
    "'godot --headless --path . --import', or do it in the Godot editor, "
    "which handles the sidecar for you."
)

DENY_CONVERT_MSG = (
    "--convert-3to4 rewrites every file in the project in place, and "
    "there is no undo. Confirm the project is committed to git or "
    "otherwise backed up, then let the user run it themselves. To see "
    "what it would change without changing anything, use "
    "--validate-conversion-3to4, which is read-only."
)

ASK_REF_MSG = (
    "Deleting a scene, resource, or script orphans every uid:// reference "
    "pointing at it. Nothing reports the breakage at deletion time -- it "
    "surfaces later as a scene that will not load. Check what references "
    "it first with the reference_graph MCP tool. The file itself is "
    "recoverable from git if it was committed."
)

ASK_CONFIG_MSG = (
    "This removes a project-level configuration file. project.godot "
    "defines the project itself -- autoloads, input map, rendering "
    "settings -- and export_presets.cfg holds every export configuration "
    "including signing settings. Neither is regenerated, and both are "
    "recoverable only from git."
)


# --- analysis ------------------------------------------------------------


def _collect_moved_args(entries):
    """Every positional argument named by any move- or copy-class entry
    anywhere in the (flattened) command. Deliberately whole-command, not
    per-statement: 'mv a.gd b/ && mv a.gd.uid b/' -- the sidecar moved in
    a separate, later statement of the SAME command -- must still be
    allowed, so pairing is checked against this global set."""
    moved = set()
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt) or is_copy_statement(stmt):
            moved.update(positional_args(stmt))
    return moved


def _collect_removed_paths(entries):
    removed = set()
    for e in entries:
        if is_remove_statement(e["tokens"]):
            removed.update(positional_args(e["tokens"]))
    return removed


def _any_unpaired_source(args, predicate_exts, moved_norm, cwd):
    if len(args) < 2:
        return False  # not a well-formed move/copy; nothing to check
    moveable = SIDECAR_EXTS | ASSET_EXTS
    for tok in args[:-1]:
        if tok == "{}":
            if predicate_exts and (predicate_exts & moveable):
                return True
            continue
        sc = sidecar_name_for(tok)
        if sc is None:
            continue
        if _ci(sc) in moved_norm:
            continue
        if sidecar_confirmed_absent(cwd, tok):
            continue
        return True
    return False


def analyze(command, cwd):
    """Return (decision, reason) or None (allow, silently)."""
    entries = flatten(command)
    if not entries:
        return None

    # --convert-3to4: irreversible, whole-project rewrite. Token-based
    # (not a raw substring test) so it is anchored to an actual argument,
    # not text that merely contains the string.
    for e in entries:
        if any(t.lower() == "--convert-3to4" for t in e["tokens"]):
            return ("deny", DENY_CONVERT_MSG)

    moved_args = _collect_moved_args(entries)
    moved_norm = {_ci(a) for a in moved_args}
    removed_paths = _collect_removed_paths(entries)
    removed_norm = {_ci(p) for p in removed_paths}

    # deny: mv / git mv / rsync --remove-source-files / find -exec mv, with
    # a sidecar-bearing source whose sidecar is not named anywhere else in
    # the command and is not confirmed absent on disk.
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt):
            if _any_unpaired_source(positional_args(stmt), e["exts"], moved_norm, cwd):
                return ("deny", DENY_MOVE_MSG)

    # deny: cp / install of a sidecar-bearing source that is ALSO removed
    # elsewhere in the command, with no sidecar carried to the new path --
    # a move spelled as two commands.
    for e in entries:
        stmt = e["tokens"]
        if not is_copy_statement(stmt):
            continue
        args = positional_args(stmt)
        if len(args) < 2:
            continue
        for src in args[:-1]:
            if _ci(src) not in removed_norm:
                continue
            sc = sidecar_name_for(src)
            if sc is None:
                continue
            if _ci(sc) in moved_norm:
                continue
            if sidecar_confirmed_absent(cwd, src):
                continue
            return ("deny", DENY_COPY_REMOVE_MSG)

    # ask: rm (or git rm) of a reference-bearing file, or of a
    # project-level config file that is recoverable only from git.
    for e in entries:
        stmt = e["tokens"]
        if not is_remove_statement(stmt):
            continue
        for tok in positional_args(stmt):
            ext = ext_of(tok)
            if ext in SIDECAR_EXTS or ext in INLINE_UID_EXTS:
                return ("ask", ASK_REF_MSG)
            if os.path.basename(tok).lower() in PROJECT_CONFIG_BASENAMES:
                return ("ask", ASK_CONFIG_MSG)

    return None


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (ValueError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return 0
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = None

    try:
        result = analyze(command, cwd)
    except Exception:
        # A guard that crashes on a weird command is worse than one that
        # occasionally does not fire -- fail open.
        return 0

    if result is None:
        return 0
    decision, reason = result
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
