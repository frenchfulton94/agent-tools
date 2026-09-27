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

`_strip_comments()` runs first, on the raw command text, before shlex ever
sees it (fix round 4, CRITICAL 2 -- see its docstring: shlex's own default
comment rule is wrong for this guard's purpose and was a complete, silent
bypass; it also tracks backtick and `$(...)` state so a '#' lexically
inside either is never mistaken for a top-level comment -- fix round 5's
CRITICAL 1 for the backtick case, fix round 6's IMPORTANT 2 for `$(...)`,
which was left open the first time and reproduced with the identical
lexical shape). `shlex` in POSIX mode with a custom `punctuation_chars`
(the library default plus a backtick -- the default omits it, which let a
backtick-wrapped move glue onto the following word) then splits `;`, `&`,
`&&`, `||`, `|`, `(`, `)`, `` ` `` out as their own tokens while leaving
quoted content alone and stripping matching quotes; `commenters` is
disabled so it never reapplies its own cruder comment rule to text
`_strip_comments()` already handled correctly. `tokenize()` drives the
lexer one token at a time instead of consuming it in one `list(...)` call,
specifically so a parse failure partway through (one unmatched quote)
still yields every token successfully read before that point -- an early
statement that denies correctly on its own must not be discarded because a
LATER, unrelated fragment has a typo in it. `_merge_backtick_spans()` and
`_merge_paren_spans()` then each collapse their matched span (a backtick
pair, or a `$(...)` -- properly depth-tracked, since `$(...)` nests where
backticks do not) back into a single opaque token (fix round 4, CRITICAL 1
for backticks, fix round 6 IMPORTANT 2 for `$(...)` -- an earlier round
treated the backtick as a hard statement boundary, which split a real move
into fragments too small for `positional_args` to read as one argument,
silently ALLOWing a genuinely unpaired move; `$(...)` was left with the
exact same exposure until this round).

Known, accepted limits (documented rather than silently wrong):
  - Command substitution (`$(...)` and `` `...` ``) is not evaluated -- a
    filename either one computes cannot be reasoned about statically
    either way. Each is merged into a single OPAQUE token instead (see
    `_is_opaque`), which keeps it as one argument for pairing purposes and
    routes the statement to the coarse ASK backstop rather than silently
    treating the unknowable value as "no extension, safe".
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
# The backtick is NOT a statement boundary (fix round 4, CRITICAL 1): a
# backtick-delimited span is command substitution, an ordinary part of ONE
# argument, not a separator between commands. It is still listed in
# PUNCTUATION_CHARS above so shlex tokenizes each backtick as its own
# token instead of gluing it onto an adjacent word (round 2's fix), and
# `tokenize()` then merges each matched backtick PAIR back into a single
# opaque token before statements are split -- see `_merge_backtick_spans`.
# Treating the backtick as a boundary (as an earlier round did) split a
# real move into fragments too small for `positional_args` to read as one
# argument, which silently ALLOWed a genuinely unpaired
# `mv a.gd \`echo b/a.gd\``.
STATEMENT_BOUNDARY_TOKENS = frozenset({";", "&", "&&", "||", "|", "(", ")", "\n"})
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


def _strip_comments(command):
    """Strip a bash-accurate '#' comment -- one that begins at the start
    of a WORD (the start of the command, or immediately after unquoted
    whitespace), is itself unquoted, AND is not lexically inside an open
    backtick span or an open `$(...)` substitution -- to end of line,
    leaving everything else, including a '#' anywhere else, untouched.

    This exists because shlex's own default (`commenters='#'`) is wrong
    for this guard's purpose: it treats '#' as a comment start ANYWHERE,
    including mid-word, with no quote- or backtick-awareness. An
    entirely ordinary filename broke this catastrophically (fix round 4,
    CRITICAL 2, a pre-existing bug never caught before that round):
    'touch weird#file.gd && mv scripts/player.gd entities/player.gd'
    tokenized under the old default to just ['touch', 'weird'] -- the
    '&& mv ...' was silently discarded, `tokenize()` reported
    `failed=False` (nothing actually failed, as far as shlex was
    concerned), so even the raw-text backstop never engaged either. A
    complete, silent bypass of the only mechanism enforcing this plugin's
    safety claim, trivially triggered by a filename containing '#'.

    Round 4's own fix had a gap in the same class (fix round 5,
    CRITICAL 1): it tracked single- and double-quote state but not
    backtick state, so an UNQUOTED '#' lexically inside an open backtick
    span (`` `echo Building #42` `` -- an ordinary build/issue-number
    idiom, not a contrivance) was still read as a top-level comment
    start, and the strip ran to end-of-string -- eating the closing
    backtick, everything after it, and a real unpaired move along with
    it. A '#' that IS quoted inside the span
    (`` `echo "Deploying build #42"` ``) was already handled correctly,
    since double-quote tracking alone was sufficient there; the gap was
    specifically the unquoted case. `in_backtick` below closes it: a '#'
    is never a comment start while an unmatched backtick has been seen
    an odd number of times since the last one outside any quote.

    Round 5's own fix had ANOTHER bug in the same class (fix round 6,
    CRITICAL 1): the double-quote branch was collapsed to a bare
    `in_double = not in_double` that fell through to the SAME
    per-character dispatch used for unquoted text -- so a literal
    apostrophe INSIDE an already-open double-quoted string (bash gives it
    no special meaning there at all) was still read as opening a SINGLE
    quote, permanently desyncing the tracker for the rest of the command
    on an odd apostrophe count. A later genuine word-start '#' then fell
    into the (phantom) single-quote branch and was never evaluated as a
    comment at all -- narrating an action with a contraction
    (`echo "building player's script"`) and then leaving a trailing
    comment naming a real file is ordinary agent behavior, not a
    contrivance. Fixed by giving `in_double` its own unconditional
    consume-literally branch, structured exactly like `in_single`'s: while
    inside double quotes, nothing is dispatched character-by-character at
    all, and only a literal '"' closes it. This intentionally means
    double-quoted content is now just as fully opaque to this function as
    single-quoted content is -- a backtick or `$(` occurring INSIDE a
    double-quoted string is not tracked either, a known, accepted
    narrowing in exchange for the desync being impossible; nothing inside
    a double-quoted string can produce an UNQUOTED, word-start '#' in the
    first place, so this narrowing costs nothing for THIS function's
    actual job.

    `paren_depth` (fix round 6, IMPORTANT 2) is the `$(...)` analogue of
    `in_backtick`: unlike a backtick pair, `$(...)` nests properly in
    real bash (`$(echo $(date))`), so this tracks a DEPTH, incremented by
    a literal '$' immediately followed by '(', and by every further '('
    seen before it returns to 0, decremented by every ')' -- closing only
    when depth reaches 0. A '#' is never a comment start while any
    `$(...)` opened here has not yet closed. Confirmed empirically not
    new to this round: `$(echo Building #42) && mv scripts/player.gd
    entities/player.gd` reproduces against the version of this file that
    only closed the backtick case, using the exact same lexical shape --
    ruled in anyway because leaving `$(...)` open while `` `...` `` was
    closed made "the '#' bypass is closed" true only for the spelling
    people write less often.

    A backslash escapes the very next character outright (skipped as an
    inseparable two-character unit) UNLESS already inside single quotes,
    which POSIX gives no escape mechanism at all, or already inside
    double quotes, which are now fully opaque to this function (see
    above) -- this rule now only ever fires for an UNQUOTED backslash,
    which still gives a properly backslash-escaped NESTED backtick span
    the correct behavior for free: the escaped inner backtick never
    toggles `in_backtick`, so the outer span stays open across it,
    matching real bash. An unmatched trailing backtick, or a `$(...)`
    that never closes, just leaves the tracker open for the remainder of
    the string, which only suppresses comment detection from that point
    on -- analysing MORE text, never less, the direction this guard
    always fails toward.

    Deliberately NOT handled (ruled out, fix round 5, reconfirmed still
    accurate in fix round 6): a '#' immediately after a control operator
    with no space (`mv a b;#comment`) is, in real bash, still a
    word-start comment; this function's simpler rule
    (whitespace-or-start-of-string only) does not strip it. Confirmed
    empirically this only ever means MORE text gets analyzed (the literal
    '#comment...' survives as ordinary tokens feeding the rest of the
    pipeline), never less -- worst case a spurious `ask`, never a missed
    `deny`. Extending the rule to cover it was judged out of proportion
    to the risk it would close.

    `tokenize()` calls this BEFORE handing the command to shlex, and
    disables shlex's own `commenters` entirely afterward, so a '#'
    surviving this pass (because it wasn't a real comment start) is never
    reinterpreted as one by the cruder default rule downstream."""
    out = []
    in_single = False
    in_double = False
    in_backtick = False
    paren_depth = 0
    at_word_start = True
    i, n = 0, len(command)
    while i < n:
        ch = command[i]
        if in_single:
            out.append(ch)
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            out.append(ch)
            if ch == '"':
                in_double = False
            i += 1
            continue
        # Not inside any quotes from here on.
        if ch == "\\" and i + 1 < n:
            out.append(ch)
            out.append(command[i + 1])
            at_word_start = False
            i += 2
            continue
        if ch == "'":
            in_single = True
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == "`":
            in_backtick = not in_backtick
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == "$" and i + 1 < n and command[i + 1] == "(":
            paren_depth += 1
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == "(" and paren_depth > 0:
            paren_depth += 1
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == ")" and paren_depth > 0:
            paren_depth -= 1
            at_word_start = False
            out.append(ch)
            i += 1
            continue
        if ch == "#" and at_word_start and not in_backtick and paren_depth == 0:
            while i < n and command[i] != "\n":
                i += 1
            continue  # do not consume/emit the newline itself here
        at_word_start = ch in (" ", "\t", "\n")
        out.append(ch)
        i += 1
    return "".join(out)


def _merge_backtick_spans(tokens):
    """Merge each backtick-delimited span in a flat token stream into a
    single opaque token that still contains its two backticks (so
    `_is_opaque` recognizes it). A matched `` `...` `` pair is genuine
    shell command substitution -- an ordinary part of the ONE argument it
    sits inside, not a separator between statements. An earlier round
    tokenized the backtick as a hard statement boundary, which split a
    real move into fragments too small for `positional_args` to read as a
    single argument -- `mv a.gd \\`echo b/a.gd\\`` became the three
    "statements" `['mv', 'a.gd']`, `['echo', 'b/a.gd']`, `[]`, and the
    degenerate first fragment was then judged fully "resolved" (nothing
    left to check) instead of "truncated" -- a genuinely unpaired move
    silently ALLOWed (fix round 4, CRITICAL 1).

    An unmatched trailing backtick (no closing pair before the token
    stream ends) is left as a lone token, same as before -- it cannot
    attach to a real command word either way, so it does not spuriously
    reclassify anything."""
    out = []
    i, n = 0, len(tokens)
    while i < n:
        if tokens[i] == "`":
            j = i + 1
            while j < n and tokens[j] != "`":
                j += 1
            if j < n:
                out.append(" ".join(tokens[i : j + 1]))
                i = j + 1
                continue
        out.append(tokens[i])
        i += 1
    return out


def _merge_paren_spans(tokens):
    """Merge each `$(...)` command-substitution span in a flat token
    stream into a single opaque token (still containing its '$', so
    `_is_opaque` recognizes it, exactly like `_merge_backtick_spans`) --
    the `$(...)` analogue of that function, given the same treatment for
    the same reason (fix round 6, IMPORTANT 2): `_strip_comments` and
    `_merge_backtick_spans` closed the '#'-swallowing and
    statement-fragmenting bugs for `` `...` ``, but left BOTH open for
    the `$(...)` spelling of the exact same syntax -- the one people
    write more often.

    Unlike a backtick pair, `$(...)` nests properly in real bash
    (`$(echo $(date))`), so this tracks a DEPTH rather than toggling a
    flag, closing only when it returns to 0 after the opening '$('. The
    matching close is found by DEPTH, not by token boundary: shlex's
    `punctuation_chars` mode glues any run of consecutive punctuation
    characters into ONE token -- `$((1+2))` tokenizes with a literal
    '))' token, and `$(echo $(date))` closes BOTH nesting levels inside
    a single '))' token -- so the true close can land in the MIDDLE of a
    token, not just at its edge. Handled by scanning each candidate
    token character-by-character rather than assuming one paren per
    token.

    An unmatched `$(` (depth never returns to 0 before the stream ends)
    is left alone -- the lone `$` token and whatever follows fall through
    to ordinary tokenization/statement-splitting, which is MORE analysis
    of that text, not less, the direction this guard always fails
    toward."""
    out = []
    i, n = 0, len(tokens)
    while i < n:
        if tokens[i] == "$" and i + 1 < n and tokens[i + 1][:1] == "(":
            depth = 0
            collected = [tokens[i]]
            j = i + 1
            closed = False
            leftover = ""
            while j < n:
                tok = tokens[j]
                close_at = None
                d = depth
                for k, c in enumerate(tok):
                    if c == "(":
                        d += 1
                    elif c == ")":
                        d -= 1
                        if d == 0:
                            close_at = k
                            break
                if close_at is not None:
                    collected.append(tok[: close_at + 1])
                    leftover = tok[close_at + 1 :]
                    closed = True
                    j += 1
                    break
                collected.append(tok)
                depth = d
                j += 1
            if closed:
                out.append(" ".join(collected))
                if leftover:
                    out.append(leftover)
                i = j
                continue
        out.append(tokens[i])
        i += 1
    return out


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
    command = _strip_comments(command)
    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION_CHARS)
    lexer.whitespace_split = True
    lexer.commenters = ""  # comments already handled, accurately, above
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
    tokens = [t for t in tokens if t != ""]
    return _merge_paren_spans(_merge_backtick_spans(tokens)), failed


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


def _backtick_inner(tok):
    """The text a merged backtick-span token (see `_merge_backtick_spans`)
    wraps, or None if `tok` isn't one. Real backtick command substitution
    genuinely EXECUTES its inner text as a subprocess regardless of what
    the captured output is later used for -- even a command line that is
    NOTHING BUT a bare backtick span (`` `mv a.gd b/a.gd` `` on its own)
    still runs the inner `mv` as a real side effect. So its inner text is
    recursed into by `flatten()` exactly like `eval "..."` / `sh -c
    "..."`, in ADDITION to (not instead of) the outer statement treating
    the whole merged token as one opaque argument for its own pairing
    analysis -- both are true at once in a real shell."""
    if len(tok) >= 2 and tok[0] == "`" and tok[-1] == "`":
        return tok[1:-1]
    return None


def _paren_inner(tok):
    """The text a merged `$(...)` span token (see `_merge_paren_spans`)
    wraps, or None if `tok` isn't one -- the `$(...)` analogue of
    `_backtick_inner`, for the same reason (fix round 6, IMPORTANT 2):
    `$(...)` genuinely executes its inner text as a subprocess exactly
    like a backtick span does, so it needs the same recursion into
    `flatten()`, in ADDITION to the outer statement treating the whole
    merged token as one opaque argument. `_merge_paren_spans` always
    joins its collected pieces with a single space, so a real span
    always has the exact shape '$ (' at its start; the closing ')' may
    have trailing characters from a glued punctuation run stripped onto
    a following token already (see that function), so `tok` itself
    always ends in ')' when it is one of these."""
    if tok.startswith("$ (") and tok.endswith(")"):
        return tok[3:-1].strip()
    return None


def _substitution_inner(tok):
    """The inner text of `tok` if it is a merged backtick span OR a
    merged `$(...)` span (see `_backtick_inner` / `_paren_inner`), else
    None. The single entry point `flatten()` uses to decide whether to
    recurse into a token as a nested command substitution, so both
    spellings of the same syntax get identical treatment at every scan
    site (fix round 6, IMPORTANT 2 -- the two spellings must not drift
    apart again the way `$(...)` was left behind the first time)."""
    inner = _backtick_inner(tok)
    if inner is not None:
        return inner
    return _paren_inner(tok)


def flatten(command, depth=0, max_depth=6, context=0, _counter=None):
    """Flatten a command into ({"tokens": [...], "exts": frozenset(),
    "context": <id>} entries, any_parse_failure). Covers the command's
    own top-level statements, plus -- recursively, to a bounded depth --
    the inner command of every `sh -c` / `bash -c` / `zsh -c` / `eval`
    statement, every backtick- or `$(...)`-delimited command substitution
    (see `_substitution_inner`), and the exec'd sub-command of every
    `find -exec`/`-execdir` block. This lets every later pass treat a
    nested shell's contents exactly like top-level statements, instead of
    special-casing recursion order at each check site. any_parse_failure
    is True if this command OR any nested command it recursed into
    failed to fully tokenize.

    `context` identifies WHICH execution context an entry came from
    (fix round 5, IMPORTANT 2). Context 0 is the command's own top
    level; every recursion into a genuinely separate execution --
    `sh -c`/`eval`'s inner command, or a backtick/`$(...)` span's inner
    text -- gets its OWN fresh id via `_counter` (a one-element mutable
    box threaded through the whole recursion tree, so every nested call
    shares one counter and no two contexts collide). A `find -exec`
    sub-statement stays in its ENCLOSING statement's context: unlike
    `sh -c`/`eval`/a substitution span, it is not a separate subshell
    whose output could be laundered back into the parent -- it is the
    same top-level command actually naming that sub-command's arguments
    directly.

    This exists because sidecar-pairing (`_collect_moved_args_by_context` /
    `_collect_removed_paths_by_context`, called from `analyze()`) must not credit a
    pairing move found in one context against an unpaired move in
    another: `` `false && mv a.gd.uid b/a.gd.uid` && mv a.gd b/a.gd ``
    names the sidecar move only inside a backtick span that is provably
    unreachable (`false &&` never lets it run), and crediting it anyway
    laundered a genuinely unpaired top-level move into a silent allow.
    The same crediting was possible across `eval`/`sh -c` recursion since
    round 1. Scoping the credit to the context it was actually found in
    closes this without building a real control-flow/reachability model
    (ruled out of proportion -- this is the cheap, correct fix: pairs at
    the top level pair with each other, pairs inside one recursed span
    pair within that span, and nothing crosses a context boundary either
    direction). Accepted trade-off: `sh -c "mv a.gd b/" && mv a.gd.uid
    b/` now denies where it used to allow -- an odd way to write a paired
    move, and the failure direction is safe."""
    entries = []
    if depth > max_depth:
        return entries, False
    if _counter is None:
        _counter = [0]  # context 0 is reserved for the top level
    tokens, failed = tokenize(command)
    any_failed = failed
    for stmt in split_statements(tokens):
        eff = strip_wrappers(stmt)
        fw = first_word(eff)
        top_tokens = _strip_exec_spans(stmt) if fw == "find" else stmt
        entries.append({"tokens": top_tokens, "exts": frozenset(), "context": context})
        if fw in SHELL_C_KEYWORDS and len(eff) >= 3 and eff[1] == "-c":
            _counter[0] += 1
            sub_entries, sub_failed = flatten(
                eff[2], depth + 1, max_depth, _counter[0], _counter
            )
            entries.extend(sub_entries)
            any_failed = any_failed or sub_failed
        elif fw == "eval" and len(eff) >= 2:
            _counter[0] += 1
            sub_entries, sub_failed = flatten(
                " ".join(eff[1:]), depth + 1, max_depth, _counter[0], _counter
            )
            entries.extend(sub_entries)
            any_failed = any_failed or sub_failed
        if fw == "find":
            for exts, sub in find_exec_substatements(stmt):
                entries.append({"tokens": sub, "exts": exts, "context": context})
                for tok in sub:
                    inner = _substitution_inner(tok)
                    if inner is not None:
                        _counter[0] += 1
                        sub_entries, sub_failed = flatten(
                            inner, depth + 1, max_depth, _counter[0], _counter
                        )
                        entries.extend(sub_entries)
                        any_failed = any_failed or sub_failed
        for tok in stmt:
            inner = _substitution_inner(tok)
            if inner is not None:
                _counter[0] += 1
                sub_entries, sub_failed = flatten(
                    inner, depth + 1, max_depth, _counter[0], _counter
                )
                entries.extend(sub_entries)
                any_failed = any_failed or sub_failed
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
    `$SRC`, `${f}`, `$(...)`), or a backtick-delimited command
    substitution span merged into one token by `_merge_backtick_spans`
    (fix round 4, CRITICAL 1 -- it still carries its two backticks, which
    is what this checks for). Its real value, and therefore its real
    extension, is unknowable from text alone; treating it as "no
    extension, no sidecar needed" (what `ext_of` would otherwise silently
    conclude) would be inferring safety from ignorance, the same mistake
    CRITICAL 1 (fix round 2) closed for the disk check. `{}` (find's own
    per-match placeholder, whose possible extensions are already tracked
    precisely via `predicate_exts`) is deliberately not opaque -- callers
    exclude it before this ever matters."""
    return "$" in tok or "`" in tok


def _entry_is_resolved(stmt):
    """True when precise analysis had enough information to reach a
    reliable verdict for this statement -- it was classified as a known
    command, its positional arguments are COMPLETE for that command's
    shape, and none of them are opaque (fix round 3, CRITICAL 2
    over-triggering; the completeness check is fix round 4, CRITICAL 1's
    root-cause fix). An unclassified statement (kind is None -- a bare
    `find` shell, an `xargs` line, a `for`/`while` header) is never
    "resolved": there was no precise verdict for it to begin with, so it
    must still be visible to the coarse backstop below.

    The completeness check exists because `not any(...)` over an EMPTY
    argument list is vacuously True -- "resolved" not because anything
    was actually checked, but because there was nothing left TO check.
    A statement can end up with too few positional arguments for its own
    command form -- `positional_args` reads a bare `['mv', 'x']` as
    (sources=[], dest='x'), zero sources -- and a truncated fragment like
    that must be judged UNRESOLVED by definition, not vacuously cleared,
    whatever caused the truncation. (A prior version of the backtick fix
    surfaced exactly this: splitting on the backtick left a degenerate
    `['mv', 'a.gd']` fragment that this function waved through because it
    had no opaque tokens to find -- not because it had been checked.)

    A CLASSIFIED, COMPLETE statement whose source is a shell variable or
    a merged backtick span (`mv "$f" entities/`, `` mv `echo x.gd` y/ ``)
    is deliberately ALSO treated as unresolved: `command_kind` says "mv",
    but the sidecar check silently answered "no extension, nothing to
    pair" only because the real filename is unknowable, not because it
    truly has none. That is exactly the "looks like a move, could not be
    pinned down precisely" case ASK exists for, so it stays visible to
    the backstop too, despite being classified. A resolved entry was
    fully and correctly handled by the deny/ask loops above (whichever
    way that came out) and must not be re-litigated here -- that was
    CRITICAL 2's fix round 3 regression: a blanket text scan re-flagged
    every already-cleared paired mv, tscn move, and bare cp, because a
    real, safe move by definition contains both a move word and a Godot
    extension."""
    kind = command_kind(stmt)
    if kind is None:
        return False
    if kind in ("rm", "git-rm"):
        targets, _dest = positional_args(stmt)
        if not targets:
            return False  # truncated/degenerate -- nothing was actually checked
        check_toks = targets
    else:
        sources, dest = positional_args(stmt)
        if not sources or dest is None:
            return False  # truncated/degenerate -- same vacuous-truth risk
        check_toks = list(sources) + [dest]
    return not any(_is_opaque(t) for t in check_toks if t != "{}")


def _coarse_token_backstop(entries):
    """Catch a move/removal-ish command whose real arguments were hidden
    from precise classification by something this module does not
    specially unwrap -- chiefly `xargs`, whose own arguments are templated
    from stdin and can never be literal tokens here -- or that WAS
    classified but left opaque (see `_entry_is_resolved`). Deliberately
    exact TOKEN equality for the move/removal WORD, not a raw substring
    search, so it does NOT re-flag `grep "mv foo.gd"` or
    `echo "mv a.gd b/"`: shlex keeps a quoted phrase as ONE token, so it
    is never equal to the bare word "mv". The EXTENSION check is looser
    on purpose (`ext_of` for an ordinary token, plus a raw substring
    search for one merged from a backtick or `$(...)` span): a merged
    span like `` `echo scripts/player.gd` `` or `$(echo
    scripts/player.gd)` is opaque as a whole -- `ext_of` on it finds no
    clean trailing extension -- but the raw text inside it still names
    one, and that's exactly the kind of "looks relevant, could not be
    pinned down" signal this backstop exists to catch (fix round 4,
    CRITICAL 1; extended to `$(...)` in fix round 6, IMPORTANT 2 -- a
    merged `$(...)` token always starts with '$', already the exact
    marker `_is_opaque` looks for). Entries precise analysis already
    fully resolved (classified, complete, non-opaque) are excluded before
    either word or extension is looked for in them, so an
    already-cleared, correctly-paired command can never re-trigger this
    on its own text."""
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
            elif ("`" in tok or tok.startswith("$")) and _RAW_EXT_RE.search(tok):
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


def _collect_moved_args_by_context(entries):
    """Every argument (source or destination) named by any move- or
    copy-class entry, grouped by the execution CONTEXT it came from (fix
    round 5, IMPORTANT 2) -- not one global set. Within one context,
    still deliberately whole-context rather than per-statement:
    'mv a.gd b/ && mv a.gd.uid b/' at the top level -- the sidecar moved
    in a separate, later statement of the SAME context -- must still be
    allowed. But a pairing move named in a DIFFERENT context (a
    `sh -c`/`eval`'s inner command, or a backtick span's inner text) must
    NOT credit a move in this one: that cross-context crediting is
    exactly what let `` `false && mv a.gd.uid b/a.gd.uid` && mv a.gd
    b/a.gd `` launder a provably-unreachable decoy sidecar move (inside a
    backtick span gated by `false &&`) into excusing a real, unpaired
    top-level move. See `flatten()` for how context ids are assigned."""
    moved_by_ctx = {}
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt) or is_copy_statement(stmt):
            srcs, dest = positional_args(stmt)
            s = moved_by_ctx.setdefault(e["context"], set())
            s.update(srcs)
            if dest is not None:
                s.add(dest)
    return moved_by_ctx


def _collect_removed_paths_by_context(entries):
    """As `_collect_moved_args_by_context`, but for `rm`/`git rm` targets."""
    removed_by_ctx = {}
    for e in entries:
        if is_remove_statement(e["tokens"]):
            targets, _ = positional_args(e["tokens"])
            s = removed_by_ctx.setdefault(e["context"], set())
            s.update(targets)
    return removed_by_ctx


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

    moved_by_ctx = _collect_moved_args_by_context(entries)
    moved_norm_by_ctx = {ctx: {_key(a) for a in s} for ctx, s in moved_by_ctx.items()}
    removed_by_ctx = _collect_removed_paths_by_context(entries)
    removed_norm_by_ctx = {ctx: {_key(p) for p in s} for ctx, s in removed_by_ctx.items()}

    # deny: mv / git mv / rsync --remove-source-files / find -exec mv, with
    # a sidecar-bearing source whose sidecar is not named anywhere else in
    # the SAME EXECUTION CONTEXT (fix round 5, IMPORTANT 2 -- a pairing
    # move named only in a different context, e.g. inside a backtick span,
    # must not excuse this one) and is not confirmed absent on disk.
    for e in entries:
        stmt = e["tokens"]
        if is_move_statement(stmt):
            sources, _dest = positional_args(stmt)
            moved_norm = moved_norm_by_ctx.get(e["context"], set())
            if _any_unpaired_source(sources, e["exts"], moved_norm, cwd):
                return ("deny", DENY_MOVE_MSG)

    # deny: cp / install of a sidecar-bearing source that is ALSO removed
    # elsewhere in the SAME CONTEXT, with no sidecar carried to the new
    # path -- a move spelled as two commands.
    for e in entries:
        stmt = e["tokens"]
        if not is_copy_statement(stmt):
            continue
        srcs, _dest = positional_args(stmt)
        moved_norm = moved_norm_by_ctx.get(e["context"], set())
        removed_norm = removed_norm_by_ctx.get(e["context"], set())
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
