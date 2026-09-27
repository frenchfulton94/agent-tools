#!/usr/bin/env python3
"""godot_guard.py -- analysis core for the godot plugin's PreToolUse guard.

godot-guard.sh (the hook's actual entry point) does no analysis itself; it
reads stdin, checks that python3 exists, and hands stdin to this module
untouched. Everything below is pure text analysis. It never executes,
`eval`s, or shells out to any part of the command it is examining -- it
only reads it.

## Why this is not a regex-over-the-whole-command guard

The first version of this guard (task 9, round 1) tested the *whole
command string* against a handful of patterns. It shipped with two
confirmed bugs: `\\b` as a word-boundary assertion silently matches
nothing under stock macOS bash, and a whole-command substring test cannot
express "did THIS file's sidecar get named too" once more than one file,
one statement, or one comment is on the line. That forced a rewrite onto
real tokenization (round 1's second commit): split the command into
statements with `shlex`, split statements into arguments, reason per
argument.

## Round 2: precision earns narrowness, narrowness can regress coverage

Moving classification to "is the first word of a statement literally
mv/rm/cp/..." is precise, but precision has a cost the first rewrite did
not account for: the OLD whole-command regex matched `mv` flanked by any
non-letter, ANYWHERE in the text -- so it accidentally caught `sudo mv`,
`env mv`, `xargs mv`, a backtick-wrapped move, and a few other shapes it
had no business being precise about, just because a substring test does
not know what "precise" means. The tokenized rewrite is architecturally
correct and IS narrower, and narrower here meant a real regression: those
same wrapped forms produced silent ALLOW instead of the old (accidental,
but real) coverage.

The fix is two-layered, not a bigger regex:

  1. Restore precision for the wrapper shapes that have a well-defined
     "real command follows" structure: `sudo`, `env`, `command`, `nice`,
     `time`, a leading absolute path (`/bin/mv`), `eval "..."`, and the
     shell keywords (`do`/`then`/`else`) that precede a command inside a
     `for`/`while`/`if` body when a loop is written on one line. These are
     stripped (see `strip_wrappers`) so the REAL command and its REAL
     arguments reach the exact same precise DENY/ASK analysis as an
     unwrapped `mv`.
  2. For everything that still evades precise classification --
     `xargs`-templated arguments (the real filename is supplied via stdin,
     never a literal token), an unmatched quote (an ordinary typo, not
     malice, and must not blind analysis of an earlier well-formed
     fragment), a heredoc body, or any other shape this file does not
     specifically understand -- a coarse, token-based backstop (see
     `_coarse_token_backstop` / `_coarse_raw_backstop`) returns ASK, never
     DENY, whenever the command merely *looks* move/removal-shaped next to
     a Godot-relevant extension. ASK is cheap, does not train anyone to
     switch the guard off, and restores the coverage the old regex had
     without the old regex's false denies.

## Tokenizing

`shlex` in POSIX mode with a custom `punctuation_chars` (the library
default plus a backtick -- the default omits it, which let a
backtick-wrapped move glue onto the following word) splits `;`, `&`,
`&&`, `||`, `|`, `(`, `)`, `` ` `` out as their own tokens while leaving
quoted content alone, strips matching quotes, and drops `# ...`-to-end-
of-line comments. `tokenize()` drives the lexer one token at a time
instead of consuming it in one `list(...)` call, specifically so a parse
failure partway through (one unmatched quote) still yields every token
successfully read before that point -- an early statement that denies
correctly on its own must not be discarded because a LATER, unrelated
fragment has a typo in it.

Known, accepted limits (documented rather than silently wrong):
  - Command substitution (`$(...)`) is not evaluated -- a filename it
    computes cannot be reasoned about statically either way. Backticks are
    now tokenized as their own boundary (see above), which is a
    conservative treatment (the pair splits into a statement of its own),
    not a full evaluation.
  - `xargs`'s own templated arguments are fundamentally opaque to static
    analysis (the real filename lives in whatever was piped to it, never
    a literal token in the xargs statement itself) -- this is why `xargs`
    is handled by the coarse backstop, not promoted to precise analysis.
  - Depends on python3, not jq. This plugin already requires python3 for
    its MCP server, so this trades one already-required dependency for
    another rather than adding a new one; jq is no longer used anywhere in
    this guard. Fails open (silent allow) exactly the same way if python3
    itself is somehow unreachable -- see godot-guard.sh.
"""
import json
import os
import re
import shlex
import sys

# --- file-identity vocabulary (measured, spec 3.7 / 3.8) --------------------

SIDECAR_EXTS = frozenset({"gd", "gdshader"})  # .uid sidecar beside the file
ASSET_EXTS = frozenset({
    "png", "jpg", "jpeg", "webp", "svg", "wav", "ogg", "mp3",
    "glb", "gltf", "fbx", "obj", "ttf", "otf",
})  # .import sidecar beside the file
INLINE_UID_EXTS = frozenset({"tscn", "tres"})  # uid:// lives inside the file
GODOT_RELEVANT_EXTS = SIDECAR_EXTS | ASSET_EXTS | INLINE_UID_EXTS
SIDECAR_SUFFIX = ".uid"
ASSET_SUFFIX = ".import"

# Real, well-defined process wrappers (their remaining arguments are passed
# to a literal following command unchanged) plus the shell keywords that
# can precede a command inside a one-line for/while/if body. Stripped
# before classification so the REAL command reaches precise analysis.
WRAPPER_KEYWORDS = frozenset({"sudo", "env", "command", "nice", "time", "do", "then", "else"})

MOVE_LIKE_KINDS = frozenset({"mv", "git-mv", "cp", "install", "rsync"})
TARGET_FLAG_KINDS = frozenset({"mv", "cp", "install"})  # NOT rsync: its -t means preserve-times
SHELL_C_KEYWORDS = frozenset({"sh", "bash", "zsh"})
# shlex's default punctuation_chars=True set is '();<>|&' -- it omits the
# backtick, which let a backtick-wrapped move glue onto the following word
# (measured, fix round 2). Compute the default once and add it, rather than
# hardcoding a guessed string, so this stays correct if the default set ever
# changes upstream.
PUNCTUATION_CHARS = shlex.shlex("", posix=True, punctuation_chars=True).punctuation_chars + "`"
STATEMENT_BOUNDARY_TOKENS = frozenset({";", "&", "&&", "||", "|", "(", ")", "`", "\n"})
PROJECT_CONFIG_BASENAMES = frozenset({"project.godot", "export_presets.cfg"})

# Coarse backstop vocabulary (see module docstring, point 2).
_COARSE_MOVE_WORDS = frozenset({"mv", "rm", "cp", "install", "rsync"})


def _ci(s):
    """Fold for comparison only -- macOS's default filesystem is
    case-insensitive, so 'Scripts/Player.GD' and 'scripts/player.gd.uid'
    can name the same two files. Never used for anything sent to disk."""
    return s.casefold()


def _norm_path(s):
    """Collapse a leading './' and doubled separators, for EQUALITY
    comparisons only (sidecar-pairing set membership) -- 'mv ./a.gd b/'
    paired with 'mv a.gd.uid b/' must still recognize the same file.
    Never used for extension detection (which needs to see a real
    trailing slash on a directory-like token) and never needed for disk
    resolution (the OS already treats './x' and 'x' identically there)."""
    if not s:
        return s
    normalized = os.path.normpath(s)
    if s.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    return normalized


def _key(s):
    """The normalized, case-folded form used for all set-membership
    pairing checks (moved/removed path sets, computed sidecar names)."""
    return _ci(_norm_path(s))


def _basename_lower(tok):
    return tok.rsplit("/", 1)[-1].lower()


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
    variables. Returns (tokens, failed): `failed` is True when the lexer
    hit an unrecoverable parse error (e.g. an unmatched quote) -- but
    `tokens` still holds every token successfully read BEFORE that point,
    because the lexer is driven one token at a time rather than consumed
    via a single `list(...)` call. A syntax error confined to a later
    fragment of the command must not discard analysis of an earlier,
    well-formed one (fix round 2, IMPORTANT 3)."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION_CHARS)
    lexer.whitespace_split = True
    raw = []
    failed = False
    while True:
        try:
            tok = lexer.get_token()
        except ValueError:
            failed = True
            break
        if tok is None:
            break
        raw.append(tok)
    # A backslash-newline line continuation survives shlex as a literal
    # newline character, either as its own token or glued to the front of
    # the next word (measured). Stripping leading/trailing whitespace from
    # every token, and dropping any that go empty, recovers the intended
    # tokens in both shapes without affecting normal quoted arguments.
    tokens = [t.strip() for t in raw]
    return [t for t in tokens if t != ""], failed


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
    """The command word of a statement, by basename and lowercased -- so
    an absolute path (`/bin/mv`) is recognized exactly like a bare `mv`."""
    return _basename_lower(statement[0]) if statement else ""


def strip_wrappers(statement):
    """Peel off leading process wrappers/shell keywords (see
    WRAPPER_KEYWORDS) and their immediate flag-shaped tokens, exposing the
    real command and its real arguments to every check below. A leading
    `git mv`/`git rm` is left intact (as a 2-token unit) rather than
    stripped, since callers special-case it.

    Known, accepted limit: a wrapper flag that takes a separate value
    (`sudo -u user`, `nice -n 10`) is not recognized as consuming that
    value, so the value can be misread as the next candidate command word
    and precise classification is skipped in favor of the coarse ASK
    backstop. Only the flag SHAPES the coordinator's review actually
    listed (bare `sudo mv`, `env mv`, `command mv`, `nice mv`, `/bin/mv`)
    are guaranteed full precision; anything fancier degrades gracefully
    rather than silently, same as `mv -t DIR src` degraded before IMPORTANT
    4 gave it real handling."""
    i = 0
    n = len(statement)
    steps = 0
    while i < n and steps < 8:
        steps += 1
        word = _basename_lower(statement[i])
        if word == "git" and i + 1 < n and statement[i + 1].lower() in ("mv", "rm"):
            return statement[i:]
        if word not in WRAPPER_KEYWORDS:
            return statement[i:]
        i += 1
        while i < n and statement[i].startswith("-") and statement[i] != "-":
            i += 1
    return statement[i:]


def _eff_is_git(eff, sub):
    return len(eff) > 1 and first_word(eff) == "git" and eff[1].lower() == sub


def command_kind(statement):
    """One of "mv"/"git-mv"/"cp"/"install"/"rsync"/"rm"/"git-rm", or None,
    after stripping known wrappers. The single source of truth every other
    classification function in this module is built from."""
    eff = strip_wrappers(statement)
    fw = first_word(eff)
    if fw == "mv":
        return "mv"
    if _eff_is_git(eff, "mv"):
        return "git-mv"
    if fw == "cp":
        return "cp"
    if fw == "install":
        return "install"
    if fw == "rsync":
        return "rsync"
    if fw == "rm":
        return "rm"
    if _eff_is_git(eff, "rm"):
        return "git-rm"
    return None


def positional_args(statement):
    """Returns (sources, dest) for a move/copy-like command (mv, git mv,
    cp, install, rsync) -- dest is the -t/--target-directory value when
    given (mv/cp/install only; rsync's -t means preserve-times, a boolean,
    and must NOT be read as taking a value -- IMPORTANT 4), else the
    conventional last positional argument. Returns (targets, None) for
    rm/git rm and anything else, since those have no destination-argument
    convention -- treating the last named path as a "dest" would wrongly
    exempt it from being checked."""
    eff = strip_wrappers(statement)
    kind = command_kind(statement)
    skip = 2 if kind in ("git-mv", "git-rm") else 1
    supports_target_flag = kind in TARGET_FLAG_KINDS
    has_dest_convention = kind in MOVE_LIKE_KINDS

    plain = []
    target_dir = None
    i = skip
    n = len(eff)
    while i < n:
        tok = eff[i]
        if supports_target_flag and tok in ("-t", "--target-directory"):
            if i + 1 < n:
                target_dir = eff[i + 1]
                i += 2
            else:
                i += 1
            continue
        if supports_target_flag and tok.startswith("--target-directory="):
            target_dir = tok.split("=", 1)[1]
            i += 1
            continue
        if tok.startswith("-") and tok != "-":
            i += 1
            continue
        plain.append(tok)
        i += 1

    if not has_dest_convention:
        return plain, None
    if target_dir is not None:
        return plain, target_dir
    if plain:
        return plain[:-1], plain[-1]
    return [], None


def is_move_statement(statement):
    kind = command_kind(statement)
    if kind in ("mv", "git-mv"):
        return True
    if kind == "rsync":
        eff = strip_wrappers(statement)
        return any(t.lower() == "--remove-source-files" for t in eff[1:])
    return False


def is_copy_statement(statement):
    return command_kind(statement) in ("cp", "install")


def is_remove_statement(statement):
    return command_kind(statement) in ("rm", "git-rm")


def find_exec_substatements(statement):
    """Yield (predicate_exts, sub_statement_tokens) for every -exec/-execdir
    block inside a `find` statement. predicate_exts is the set of
    extensions implied by whichever -name/-iname pattern appeared earlier
    in the SAME find statement -- best-effort, not a full evaluation of
    find's boolean expression grammar."""
    eff = strip_wrappers(statement)
    if first_word(eff) != "find":
        return
    seen_exts = set()
    i = 0
    n = len(eff)
    while i < n:
        tok = eff[i]
        low = tok.lower()
        if low in ("-name", "-iname") and i + 1 < n:
            e = ext_of(eff[i + 1])
            if e:
                seen_exts.add(e)
            i += 2
            continue
        if low in ("-exec", "-execdir") and i + 1 < n:
            j = i + 1
            sub = []
            while j < n and eff[j] not in (";", "+"):
                sub.append(eff[j])
                j += 1
            if sub:
                yield (frozenset(seen_exts), sub)
            i = j + 1
            continue
        i += 1


def _strip_exec_spans(statement):
    """Return `statement`'s tokens with every -exec/-execdir ... (;|+) span
    removed, keeping -name/-iname patterns and everything else intact.
    Used ONLY for the top-level `find` entry the coarse backstop scans
    (fix round 3, over-triggering): each -exec clause already gets its own,
    separately and precisely classified entry from
    `find_exec_substatements`, so leaving its command word (e.g. `mv`) in
    the top-level entry TOO would double-count the same real command --
    once as a precisely resolved, already-cleared sub-entry, and again as
    an unresolved substring in the raw top-level tokens, which is exactly
    what made 'find -name *.tscn -exec mv ...' (inline UID, genuinely
    safe) false-trigger the backstop."""
    out = []
    i, n = 0, len(statement)
    while i < n:
        tok = statement[i]
        if tok.lower() in ("-exec", "-execdir"):
            j = i + 1
            while j < n and statement[j] not in (";", "+"):
                j += 1
            i = j + 1  # skip the terminator too
            continue
        out.append(tok)
        i += 1
    return out


def flatten(command, depth=0, max_depth=6):
    """Flatten a command into ({"tokens": [...], "exts": frozenset()}
    entries, any_parse_failure). Covers the command's own top-level
    statements, plus -- recursively, to a bounded depth -- the inner
    command of every `sh -c` / `bash -c` / `zsh -c` / `eval` statement, and
    the exec'd sub-command of every `find -exec`/`-execdir` block. This
    lets every later pass treat a nested shell's contents exactly like
    top-level statements, instead of special-casing recursion order at
    each check site. any_parse_failure is True if this command OR any
    nested command it recursed into failed to fully tokenize."""
    entries = []
    if depth > max_depth:
        return entries, False
    tokens, failed = tokenize(command)
    any_failed = failed
    for stmt in split_statements(tokens):
        eff = strip_wrappers(stmt)
        fw = first_word(eff)
        top_tokens = _strip_exec_spans(stmt) if fw == "find" else stmt
        entries.append({"tokens": top_tokens, "exts": frozenset()})
        if fw in SHELL_C_KEYWORDS and len(eff) >= 3 and eff[1] == "-c":
            sub_entries, sub_failed = flatten(eff[2], depth + 1, max_depth)
            entries.extend(sub_entries)
            any_failed = any_failed or sub_failed
        elif fw == "eval" and len(eff) >= 2:
            sub_entries, sub_failed = flatten(" ".join(eff[1:]), depth + 1, max_depth)
            entries.extend(sub_entries)
            any_failed = any_failed or sub_failed
        if fw == "find":
            for exts, sub in find_exec_substatements(stmt):
                entries.append({"tokens": sub, "exts": exts})
    return entries, any_failed


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
    lose: the SOURCE PATH ITSELF must resolve to a file that exists, AND
    its sidecar must not. "Neither exists" is NOT evidence of anything --
    it is exactly what a wrong or stale `cwd` looks like (a compound
    `cd sub && mv ...` in one Bash call, where the payload's cwd still
    names the pre-cd directory, is an entirely ordinary way for this field
    to disagree with reality -- CRITICAL 1, fix round 2). False means
    "cannot tell", and the caller must treat that as "assume it matters",
    not as permission to skip the check."""
    sidecar = sidecar_name_for(token)
    if sidecar is None:
        return False
    resolved = _resolve(cwd, token)
    resolved_sidecar = _resolve(cwd, sidecar)
    if resolved is None or resolved_sidecar is None:
        return False
    try:
        source_exists = os.path.lexists(resolved)
    except OSError:
        return False
    if not source_exists:
        # The source itself doesn't resolve under cwd -- we cannot verify
        # ANYTHING from this, least of all "safe". Fall through to deny.
        return False
    try:
        return not os.path.lexists(resolved_sidecar)
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

ASK_BACKSTOP_MSG = (
    "This command contains text that looks like a file move or removal "
    "(mv/rm/cp/install/rsync/xargs) alongside a Godot-relevant extension "
    "(.gd, .gdshader, .tscn, .tres, or an imported asset type), but this "
    "guard's precise analysis could not fully account for it -- often "
    "because of something that hides the real arguments from static text "
    "analysis: a wrapper this guard does not specially handle, an "
    "xargs-templated argument supplied via a pipe, or an unparsed quote "
    "elsewhere in the command. It may be entirely safe. Before running it, "
    "confirm that any .uid or .import sidecar travels with the file it "
    "belongs to; prefer a plain mv/git mv when possible, since those get "
    "this guard's full, precise check instead of this general caution."
)


# --- coarse backstop (fix round 2, CRITICAL 2 / IMPORTANT 3) ----------------


def _is_opaque(tok):
    """True when a positional argument cannot be read as a literal filename
    at all -- a shell variable or command-substitution reference (`$f`,
    `$SRC`, `${f}`, `$(...)`). Its real value, and therefore its real
    extension, is unknowable from text alone; treating it as "no
    extension, no sidecar needed" (what `ext_of` would otherwise silently
    conclude) would be inferring safety from ignorance, the same mistake
    CRITICAL 1 closed for the disk check. `{}` (find's own per-match
    placeholder, whose possible extensions are already tracked precisely
    via `predicate_exts`) is deliberately not opaque -- callers exclude it
    before this ever matters."""
    return "$" in tok


def _entry_is_resolved(stmt):
    """True when precise analysis had enough information to reach a
    reliable verdict for this statement -- it was classified as a known
    command AND none of its source/destination positional arguments are
    opaque (fix round 3, CRITICAL 2 over-triggering). An unclassified
    statement (kind is None -- a bare `find` shell, an `xargs` line, a
    `for`/`while` header) is never "resolved": there was no precise
    verdict for it to begin with, so it must still be visible to the
    coarse backstop below. A CLASSIFIED statement whose source is a shell
    variable (`mv "$f" entities/`) is deliberately treated the same way --
    `command_kind` says "mv", but the sidecar check silently answered
    "no extension, nothing to pair" only because the real filename is
    unknowable, not because it truly has none. That is exactly the
    "looks like a move, could not be pinned down precisely" case ASK
    exists for, so it stays visible to the backstop too, despite being
    classified. A resolved entry was fully and correctly handled by the
    deny/ask loops above (whichever way that came out) and must not be
    re-litigated here -- that was CRITICAL 2's fix round 3 regression:
    a blanket text scan re-flagged every already-cleared paired mv, tscn
    move, and bare cp, because a real, safe move by definition contains
    both a move word and a Godot extension."""
    kind = command_kind(stmt)
    if kind is None:
        return False
    if kind in ("rm", "git-rm"):
        check_toks = positional_args(stmt)[0]
    else:
        sources, dest = positional_args(stmt)
        check_toks = list(sources) + ([dest] if dest is not None else [])
    return not any(_is_opaque(t) for t in check_toks if t != "{}")


def _coarse_token_backstop(entries):
    """Catch a move/removal-ish command whose real arguments were hidden
    from precise classification by something this module does not
    specially unwrap -- chiefly `xargs`, whose own arguments are templated
    from stdin and can never be literal tokens here -- or that WAS
    classified but left opaque (see `_entry_is_resolved`). Deliberately
    exact TOKEN equality, not a raw substring search, so it does NOT
    re-flag `grep "mv foo.gd"` or `echo "mv a.gd b/"`: shlex keeps a
    quoted phrase as ONE token, so it is never equal to the bare word
    "mv". Entries precise analysis already fully resolved (classified,
    non-opaque) are excluded before either word or extension is looked
    for in them, so an already-cleared, correctly-paired command can
    never re-trigger this on its own text."""
    has_word = False
    has_ext = False
    for e in entries:
        if _entry_is_resolved(e["tokens"]):
            continue
        toks = e["tokens"]
        for i, tok in enumerate(toks):
            low = tok.lower()
            if low in _COARSE_MOVE_WORDS:
                has_word = True
            elif low == "xargs":
                j = i + 1
                while j < len(toks) and toks[j].startswith("-"):
                    j += 1
                if j < len(toks) and toks[j].lower() in _COARSE_MOVE_WORDS:
                    has_word = True
            if ext_of(tok) in GODOT_RELEVANT_EXTS:
                has_ext = True
    return has_word and has_ext


_RAW_MOVE_WORD_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:mv|rm|cp|install|rsync|xargs)(?![A-Za-z0-9_])", re.IGNORECASE
)
_RAW_EXT_RE = re.compile(
    r"\.(?:" + "|".join(sorted(GODOT_RELEVANT_EXTS)) + r")(?![A-Za-z0-9_])", re.IGNORECASE
)


def _coarse_raw_backstop(command):
    """Last-resort RAW TEXT scan, used only when some fragment of the
    command could not be tokenized at all (fix round 2, IMPORTANT 3: an
    unmatched quote is an ordinary typo, not an adversarial construction,
    and must not blind analysis of an earlier well-formed fragment -- but
    the broken fragment itself cannot be reasoned about with tokens, so
    this falls back to substring matching for JUST that situation)."""
    return bool(_RAW_MOVE_WORD_RE.search(command)) and bool(_RAW_EXT_RE.search(command))


# --- analysis ------------------------------------------------------------


def _collect_moved_args(entries):
    """Every argument (source or destination) named by any move- or
    copy-class entry anywhere in the (flattened) command. Deliberately
    whole-command, not per-statement: 'mv a.gd b/ && mv a.gd.uid b/' --
    the sidecar moved in a separate, later statement of the SAME command
    -- must still be allowed, so pairing is checked against this global
    set."""
    moved = set()
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt) or is_copy_statement(stmt):
            srcs, dest = positional_args(stmt)
            moved.update(srcs)
            if dest is not None:
                moved.add(dest)
    return moved


def _collect_removed_paths(entries):
    removed = set()
    for e in entries:
        if is_remove_statement(e["tokens"]):
            targets, _ = positional_args(e["tokens"])
            removed.update(targets)
    return removed


def _any_unpaired_source(sources, predicate_exts, moved_norm, cwd):
    moveable = SIDECAR_EXTS | ASSET_EXTS
    for tok in sources:
        if tok == "{}":
            if predicate_exts and (predicate_exts & moveable):
                return True
            continue
        sc = sidecar_name_for(tok)
        if sc is None:
            continue
        if _key(sc) in moved_norm:
            continue
        if sidecar_confirmed_absent(cwd, tok):
            continue
        return True
    return False


def analyze(command, cwd):
    """Return (decision, reason) or None (allow, silently)."""
    entries, any_failed = flatten(command)
    if not entries and not any_failed:
        return None

    # --convert-3to4: irreversible, whole-project rewrite. Token-based
    # (not a raw substring test) so it is anchored to an actual argument,
    # not text that merely contains the string.
    for e in entries:
        if any(t.lower() == "--convert-3to4" for t in e["tokens"]):
            return ("deny", DENY_CONVERT_MSG)

    moved_args = _collect_moved_args(entries)
    moved_norm = {_key(a) for a in moved_args}
    removed_paths = _collect_removed_paths(entries)
    removed_norm = {_key(p) for p in removed_paths}

    # deny: mv / git mv / rsync --remove-source-files / find -exec mv, with
    # a sidecar-bearing source whose sidecar is not named anywhere else in
    # the command and is not confirmed absent on disk.
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt):
            sources, _dest = positional_args(stmt)
            if _any_unpaired_source(sources, e["exts"], moved_norm, cwd):
                return ("deny", DENY_MOVE_MSG)

    # deny: cp / install of a sidecar-bearing source that is ALSO removed
    # elsewhere in the command, with no sidecar carried to the new path --
    # a move spelled as two commands.
    for e in entries:
        stmt = e["tokens"]
        if not is_copy_statement(stmt):
            continue
        srcs, _dest = positional_args(stmt)
        for src in srcs:
            if _key(src) not in removed_norm:
                continue
            sc = sidecar_name_for(src)
            if sc is None:
                continue
            if _key(sc) in moved_norm:
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
        targets, _dest = positional_args(stmt)
        for tok in targets:
            ext = ext_of(tok)
            if ext in SIDECAR_EXTS or ext in INLINE_UID_EXTS:
                return ("ask", ASK_REF_MSG)
            if os.path.basename(tok).lower() in PROJECT_CONFIG_BASENAMES:
                return ("ask", ASK_CONFIG_MSG)

    # coarse backstop: precise analysis found nothing. Two independent
    # triggers -- a recognizably move/removal-shaped token pair that
    # precise classification did not account for (xargs), or a parse
    # failure somewhere in the command (an unmatched quote), which leaves
    # a stretch of text no tokenizer-based check can see into at all.
    if _coarse_token_backstop(entries):
        return ("ask", ASK_BACKSTOP_MSG)
    if any_failed and _coarse_raw_backstop(command):
        return ("ask", ASK_BACKSTOP_MSG)

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
