import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "hooks" / "scripts" / "godot-guard.sh"

CASES = [
    # (command, expected decision)
    # --- deny: unrepairable -------------------------------------------------
    ("mv scripts/player.gd entities/player.gd", "deny"),
    ("git mv src/enemy.gd actors/enemy.gd", "deny"),
    ("mv water.gdshader shaders/water.gdshader", "deny"),
    ("godot --headless --path . --convert-3to4", "deny"),
    # --- allow: the sidecar travels too ------------------------------------
    ("mv scripts/player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid", "allow"),
    ("mv scripts/ entities/", "allow"),
    ("git mv scripts entities", "allow"),
    # --- allow: uid lives inside the file -----------------------------------
    ("mv main.tscn scenes/main.tscn", "allow"),
    ("mv theme.tres ui/theme.tres", "allow"),
    # --- allow: regenerable -------------------------------------------------
    ("rm -rf .godot", "allow"),
    ("rm -rf .godot/imported", "allow"),
    # Spec 3.8: deleting a sidecar in place leaves the file's path unchanged,
    # so a scene naming its path= still resolves either way (only .uid
    # reliably regenerates the identical UID on reimport; .import does not,
    # but the asset itself is never lost). Denying these would be noise.
    ("rm scripts/player.gd.uid", "allow"),
    ("rm -f assets/hero.png.import", "allow"),
    ("rm assets/hero.png.import && godot --headless --import", "allow"),
    # --- ask: recoverable from git -----------------------------------------
    ("rm scripts/player.gd", "ask"),
    ("rm main.tscn", "ask"),
    ("rm project.godot", "ask"),
    ("rm export_presets.cfg", "ask"),
    # --- allow: ordinary work ----------------------------------------------
    ("godot --headless --path . --check-only --script main.gd", "allow"),
    ("ls scripts/", "allow"),
    ("cat scripts/player.gd", "allow"),
    ("grep -rn 'uid://' .", "allow"),
    ("godot --headless --path . --export-release macOS builds/game.dmg", "allow"),
    ("git status", "allow"),
]

# Fix round 1 of 5: an independent review ran the actual script (not just the
# regexes) and found seven confirmed bypasses beyond the `\b` bug fixed in
# round 1's first commit. Each block below is one finding, named to match the
# review. See godot_guard.py's module docstring for why these forced a move
# from whole-command regex matching to real tokenization.
REGRESSION_CASES = [
    # CRITICAL 1 -- [[ =~ ]] is case-sensitive; nothing folded case, so
    # MV/RM/GIT MV matched no rule at all (and on macOS's case-insensitive
    # filesystem, MV genuinely renames the file -- this is not academic).
    ("MV scripts/player.gd entities/player.gd", "deny"),
    ("Git Mv src/enemy.gd actors/enemy.gd", "deny"),
    ("GIT MV src/enemy.gd actors/enemy.gd", "deny"),
    ("RM scripts/player.gd", "ask"),
    ("Rm project.godot", "ask"),
    # CRITICAL 2 -- the ask tier's boundary regex required whitespace or
    # end-of-string right after the extension, so a closing quote, `;`, or
    # `)` defeated it. Quoting a path is the ordinary way to write a shell
    # command, so this was the common case, not an edge case.
    ('rm "scripts/player.gd"', "ask"),
    ("rm 'scripts/player.gd'", "ask"),
    ("rm scripts/player.gd;echo done", "ask"),
    ('rm "project.godot"', "ask"),
    ("rm project.godot;echo done", "ask"),
    ("rm scripts/player.gd)", "ask"),
    # CRITICAL 3 -- rsync --remove-source-files and install-then-rm are real
    # unrepairable moves that contain neither `mv` nor `rm` as their own
    # command, so the old whole-command approach never saw them. A directory
    # rsync (sidecars travel inside it, same as a directory mv) must still
    # allow.
    ("rsync --remove-source-files scripts/player.gd entities/player.gd", "deny"),
    ("rsync -a --remove-source-files scripts/ entities/", "allow"),
    ("install scripts/player.gd entities/player.gd && rm scripts/player.gd", "deny"),
    # CRITICAL 4 -- the sidecar check asked "does .uid appear ANYWHERE in the
    # command", not "did THIS source's sidecar get named in a move/copy
    # statement". A batch mv with one paired and one unpaired source, a
    # comment mentioning the sidecar, and an unrelated later command that
    # merely contains the substring ".uid" all defeated the old check.
    ("mv scripts/a.gd scripts/a.gd.uid scripts/b.gd entities/", "deny"),
    ("mv scripts/player.gd entities/player.gd  # remember to move player.gd.uid too", "deny"),
    ("mv scripts/player.gd entities/player.gd; echo done.uid", "deny"),
    # IMPORTANT 5 -- over-blocking on text that merely mentions a move. This
    # is the failure mode that gets a guard disabled, taking the real rule
    # down with it. Proper tokenization means `mv`/`rm` must be the first
    # word of a shell statement, not merely "not preceded by a letter" --
    # a quoted argument to grep/echo is one token, never classified as a
    # command at all.
    ('grep "mv foo.gd" notes.md', "allow"),
    ('echo "mv a.gd b/"', "allow"),
    ('grep "rm project.godot" notes.md', "allow"),
    # IMPORTANT 6 -- cp-then-rm of the same sidecar-bearing source is a move
    # spelled as two commands; it needs the move's deny message, not a
    # generic ask. A bare `cp` with no later `rm` is genuine duplication,
    # not a move, and stays allowed.
    ("cp scripts/player.gd entities/player.gd && rm scripts/player.gd", "deny"),
    ("cp scripts/player.gd entities/player.gd", "allow"),
    # find -exec mv is a real per-match unrepairable move when the -name
    # predicate matches a sidecar-bearing extension (every match loses its
    # sidecar with no way for a single -exec invocation to carry it along);
    # it is NOT dangerous when the predicate matches .tscn/.tres, whose
    # uid:// is inline and travels with the file regardless.
    ("find . -name '*.gd' -exec mv {} /tmp/ \\;", "deny"),
    ("find . -name '*.tscn' -exec mv {} archive/ \\;", "allow"),
    # Confirmed correct, do not break (verified against this file's own
    # history, not just re-asserted):
    ('mv "scripts/my player.gd" "entities/my player.gd"', "deny"),  # quoted paths inside an mv deny correctly
    ("mv scripts/player.gd \\\n   entities/player.gd", "deny"),  # backslash-continued multi-line mv denies
    ('sh -c "mv scripts/player.gd entities/player.gd"', "deny"),  # sh -c "mv ..." denies
    (
        "mv scripts/player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),  # sidecar moved in an earlier separate command allows
    ("godot --headless --path . --validate-conversion-3to4", "allow"),  # does not collide with --convert-3to4
    ("rm -rf .godot", "allow"),
]

# Fix round 2 of 5 (the coordinator's own numbering; not to be confused with
# REGRESSION_CASES above, which is round 1's independent review): four more
# problems surfaced by running the round-1 tokenizer against reality, not
# just reading it.
ROUND3_CASES = [
    # CRITICAL 2 -- the tokenized rewrite is precise, and precise was
    # narrower than the old whole-command regex it replaced: a real,
    # well-defined process wrapper in front of `mv` bypassed classification
    # entirely (the first token of the statement was never literally "mv").
    # Each of these is a genuinely unpaired move and must still deny.
    ("sudo mv scripts/player.gd entities/player.gd", "deny"),
    ("env mv scripts/player.gd entities/player.gd", "deny"),
    ("command mv scripts/player.gd entities/player.gd", "deny"),
    ("nice mv scripts/player.gd entities/player.gd", "deny"),
    ("/bin/mv scripts/player.gd entities/player.gd", "deny"),
    ("/usr/bin/mv scripts/player.gd entities/player.gd", "deny"),
    ('eval "mv scripts/player.gd entities/player.gd"', "deny"),
    ("`mv scripts/player.gd entities/player.gd`", "deny"),  # backtick now a punctuation/boundary char
    # The same wrapper shapes, paired, must still allow -- restoring
    # precision means the wrapped command gets the SAME full analysis as
    # an unwrapped mv, not an automatic deny just for being wrapped.
    (
        "sudo mv scripts/player.gd entities/player.gd && sudo mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    (
        "/bin/mv scripts/player.gd entities/player.gd && /bin/mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    # Forms that evade precise classification entirely (the real argument is
    # templated from stdin, or the command word is not the statement's own
    # first token in any way this module specially unwraps) fall to the
    # coarse ASK backstop -- restoring the old regex's reach without its
    # false denies. Never DENY for these: precise analysis could not confirm
    # anything, so ask is the honest tier, not a block.
    ("echo scripts/player.gd | xargs mv -t entities/", "ask"),
    ("for f in scripts/*.gd; do mv \"$f\" entities/; done", "ask"),
    ("bash <<'HEREDOC'\nmv scripts/player.gd entities/player.gd\nHEREDOC", "ask"),
    # IMPORTANT 3 -- one unmatched quote used to blind analysis of the WHOLE
    # command, discarding even an earlier, well-formed, fully-parsed
    # statement. A well-formed deny must survive a later typo.
    ("mv scripts/player.gd entities/player.gd; echo 'oops", "deny"),
    # The malformed fragment itself still can't be tokenized, so it falls to
    # the raw-text backstop -- ask, not silent allow, not deny.
    ("echo 'oops; mv scripts/player.gd entities/player.gd", "ask"),
    # IMPORTANT 4 -- `mv -t DIR src` inverts the pairing check when the
    # flag's value is misread as a source and the real source is excluded
    # as "the destination". Both the separate-value and `=` forms of the
    # flag must deny when genuinely unpaired, and allow when paired.
    ("mv -t entities/ scripts/player.gd", "deny"),
    ("mv --target-directory=entities/ scripts/player.gd", "deny"),
    (
        "mv -t entities/ scripts/player.gd && mv -t entities/ scripts/player.gd.uid",
        "allow",
    ),
    (
        "mv --target-directory=entities/ scripts/player.gd "
        "&& mv --target-directory=entities/ scripts/player.gd.uid",
        "allow",
    ),
    # rsync's -t means preserve-times, a boolean, NOT the target-directory
    # flag -- must not be misread as consuming the next token as a target.
    ("rsync -t -a --remove-source-files scripts/player.gd entities/player.gd", "deny"),
    # MINOR 5 -- pairing must survive a harmless path spelling difference
    # between the source's mv and the sidecar's mv (a leading './', a
    # doubled separator) rather than failing safe on a cosmetic mismatch.
    (
        "mv ./scripts/player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    (
        "mv scripts//player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
]

# Fix round 4 of 5 (coordinator numbering): two Criticals the round-3 pass
# left open -- one it introduced, one open since round 1 and never caught.
ROUND4_CASES = [
    # CRITICAL 1 -- treating the backtick as a statement boundary (round
    # 2's fix for backtick-gluing) split a real move into fragments too
    # small for positional_args to read as one argument, so the degenerate
    # leftover was judged "resolved" vacuously (nothing left to check, not
    # because anything WAS checked). Measured against round 1 as
    # regressions: all three denied under round 1, silently allowed (or
    # downgraded from deny to ask) once the backtick became a boundary.
    ("mv scripts/player.gd `echo entities/player.gd`", "deny"),
    ("git mv scripts/player.gd `echo entities/player.gd`", "deny"),
    ("cp scripts/player.gd `echo x` && rm scripts/player.gd", "deny"),
    # The general fix, both directions: an opaque DESTINATION doesn't
    # change a concrete, unpaired SOURCE's verdict (still deny -- the
    # backtick's unknowable value doesn't rescue an already-bad source).
    # An opaque SOURCE genuinely can't be pinned down -- ask, not deny,
    # and not a silent allow either.
    ("mv `echo scripts/player.gd` entities/", "ask"),
    # A bare command line that is NOTHING BUT a backtick span still runs
    # its inner text as a real subprocess in an actual shell (that's what
    # command substitution means) -- recursing into it must catch this
    # exactly like `eval "..."` / `sh -c "..."` are already recursed into.
    ("`mv scripts/player.gd entities/player.gd`", "deny"),
    # CRITICAL 2 -- shlex's default commenters='#' treats '#' as a comment
    # start ANYWHERE, including mid-word, with no quote-awareness. An
    # entirely ordinary filename silently discarded everything after it,
    # and tokenize() reported no failure at all, so even the raw-text
    # backstop never engaged -- a complete, silent bypass, pre-existing
    # since round 1 and never caught until this round.
    ("touch weird#file.gd && mv scripts/player.gd entities/player.gd", "deny"),
    # A genuine trailing comment (preceded by whitespace) must still be
    # stripped -- this command's comment TEXT itself names a real rm
    # target; if the fix stopped stripping comments altogether instead of
    # applying the correct, narrower rule, this would wrongly ask (the
    # comment's "rm scripts/player.gd" would be read as swept into the
    # same rm statement's own target list) instead of allow.
    ("rm -rf .godot  # rm scripts/player.gd", "allow"),
    # A line that is entirely a comment (from a leading '#' at the very
    # start) executes nothing in a real shell.
    ("# note: mv scripts/player.gd entities/player.gd", "allow"),
]

# Fix round 5 of 5 (coordinator numbering): finding 1 (the completeness
# check) verdicted ADDRESSED and load-bearing beyond its own trigger.
# Finding 2 (the '#'/backtick fix) was NOT addressed -- narrowed, not
# closed -- plus a new IMPORTANT finding: cross-execution-context pairing
# credit laundered a decoy sidecar move.
ROUND5_CASES = [
    # CRITICAL 1 -- round 4's _strip_comments tracked quote state but not
    # backtick depth, so an UNQUOTED '#' lexically inside an open backtick
    # span (an ordinary build/issue-number idiom, not a contrivance) was
    # still read as a top-level comment start, and the strip ran to
    # end-of-string -- eating the closing backtick, the '&&', and a real
    # unpaired move along with it.
    ("`echo Building #42` && mv scripts/player.gd entities/player.gd", "deny"),
    # The same '#' QUOTED inside the span was already handled correctly
    # (double-quote tracking alone sufficed there) -- confirms the fix
    # didn't regress the case that was never broken.
    (
        '`echo "Deploying build #42"` && mv scripts/player.gd entities/player.gd',
        "deny",
    ),
    # Paired, to confirm the backtick-nested '#' doesn't itself cause a
    # false deny/ask when the move is genuinely safe.
    (
        "`echo Building #42` && mv scripts/player.gd entities/player.gd "
        "&& mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    # A genuine trailing comment (no backtick involved) must still strip.
    ("mv scripts/player.gd entities/player.gd  # a real trailing comment", "deny"),
    # IMPORTANT 2 -- a sidecar-pairing move named only inside a provably
    # unreachable backtick span (`false &&` never lets it run) must not
    # credit a real, unpaired top-level move.
    (
        "`false && mv scripts/player.gd.uid entities/player.gd.uid` "
        "&& mv scripts/player.gd entities/player.gd",
        "deny",
    ),
    # Ordinary same-context pairing must still allow: both at the top
    # level...
    (
        "mv scripts/player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    # ...and both inside the SAME sh -c (one recursed context, shared).
    (
        'sh -c "mv scripts/player.gd entities/player.gd '
        '&& mv scripts/player.gd.uid entities/player.gd.uid"',
        "allow",
    ),
    # Accepted trade-off: split across a context boundary (one half inside
    # sh -c, the other at top level) now denies, where it used to allow --
    # an odd way to write a paired move, and the failure direction is safe.
    (
        'sh -c "mv scripts/player.gd entities/player.gd" '
        "&& mv scripts/player.gd.uid entities/player.gd.uid",
        "deny",
    ),
    # The reviewer's independently-discovered trigger for fix round 4's
    # completeness check: an mv with NO destination at all must not be
    # judged vacuously "resolved" just because there was nothing left to
    # check.
    ("touch foo.gd && mv scripts/player.gd", "ask"),
]

# Fix round 6 (the coordinator's final round for this task): one Critical
# fix round 5 itself introduced, plus an asymmetry that fix round 5's own
# work exposed (closing the '#'-swallowing/statement-fragmenting bug class
# for backticks but not for the more common `$(...)` spelling of the same
# syntax).
ROUND6_CASES = [
    # CRITICAL 1 -- round 5 collapsed the double-quote branch to a bare
    # `in_double = not in_double` that fell through to the SAME
    # per-character dispatch as unquoted text, so a literal apostrophe
    # INSIDE an already-open double-quoted string (no special meaning in
    # real bash) was misread as opening a SINGLE quote, permanently
    # desyncing the tracker on an odd apostrophe count. A later genuine
    # word-start '#' then fell into the phantom single-quote branch and
    # was never stripped -- its words (here, naming the very sidecar
    # paths the pairing check looks for) became extra, unintended
    # positional arguments of the mv statement immediately before it.
    (
        "echo \"building player's script\" && mv scripts/player.gd "
        "entities/player.gd  # note scripts/player.gd.uid "
        "entities/player.gd.uid unaffected",
        "deny",
    ),
    # An EVEN apostrophe count self-heals (confirms the parity mechanism
    # itself, not just this one fix) -- must also deny, same reason.
    (
        "echo \"it's the dev's script\" && mv scripts/player.gd "
        "entities/player.gd  # note scripts/player.gd.uid "
        "entities/player.gd.uid unaffected",
        "deny",
    ),
    # The same apostrophe-in-double-quotes shape with NO trailing comment
    # at all must still behave correctly (deny, genuinely unpaired) --
    # confirms the fix isn't somehow coupled to the comment's presence.
    ("echo \"building player's script\" && mv scripts/player.gd entities/player.gd", "deny"),
    # Paired, with the apostrophe-bearing comment still present -- must
    # allow, confirming the fix doesn't itself introduce a false deny/ask.
    (
        "echo \"building player's script\" && mv scripts/player.gd "
        "entities/player.gd && mv scripts/player.gd.uid "
        "entities/player.gd.uid  # done",
        "allow",
    ),
    # IMPORTANT 2 -- `$(...)` gets none of the protection given to
    # backticks: the same '#'-swallowing bug, mirrored exactly.
    ("$(echo Building #42) && mv scripts/player.gd entities/player.gd", "deny"),
    # The same '#' QUOTED inside the substitution was already safe
    # (double-quote tracking alone sufficed) -- confirms no regression.
    (
        '$(echo "Deploying build #42") && mv scripts/player.gd entities/player.gd',
        "deny",
    ),
    # Paired, to confirm the $(...)-nested '#' doesn't itself cause a
    # false deny/ask when the move is genuinely safe.
    (
        "$(echo Building #42) && mv scripts/player.gd entities/player.gd "
        "&& mv scripts/player.gd.uid entities/player.gd.uid",
        "allow",
    ),
    # The same statement-fragmenting bug backticks had, mirrored for
    # `$(...)`: an opaque DEST doesn't rescue a concrete, unpaired SOURCE.
    ("mv scripts/player.gd $(echo entities/player.gd)", "deny"),
    ("git mv scripts/player.gd $(echo entities/player.gd)", "deny"),
    ("cp scripts/player.gd $(echo x) && rm scripts/player.gd", "deny"),
    # An opaque SOURCE genuinely can't be pinned down -- ask, not deny,
    # not a silent allow either.
    ("mv $(echo scripts/player.gd) entities/", "ask"),
    # A bare command line that is NOTHING BUT a `$(...)` span still runs
    # its inner text as a real subprocess (same as the bare-backtick
    # case) -- recursion must catch this.
    ("$(mv scripts/player.gd entities/player.gd)", "deny"),
    # `$(...)` nests properly (unlike backticks) -- a doubly-nested
    # substitution must still recurse correctly into the real move.
    ("mv scripts/player.gd $(echo $(echo entities/player.gd))", "deny"),
    # The IMPORTANT-2 (fix round 5) cross-context laundering fix, mirrored
    # for `$(...)`: a sidecar-pairing move named only inside a provably
    # unreachable `$(...)` span must not credit a real, unpaired top-level
    # move.
    (
        "$(false && mv scripts/player.gd.uid entities/player.gd.uid) "
        "&& mv scripts/player.gd entities/player.gd",
        "deny",
    ),
]

# Round 7 (final whole-branch review, IMPORTANT 3): five rounds of adversarial
# review all targeted the TOKENIZER -- how arguments are found. Nobody audited
# the VOCABULARY those arguments are matched against, and ASSET_EXTS was
# missing mainstream game-asset types, so `mv hero.tga art/` sailed through the
# hardened tokenizer and was then simply not recognised as an asset.
#
# Both directions, because this guard has failed both ways during the plan:
# the unpaired move must deny, and the paired move must still allow.
ROUND7_CASES = [
    # Measured on 4.7.2: each of these writes a .import carrying a uid=.
    ("mv hero.tga art/", "deny"),
    ("mv hero.bmp art/", "deny"),
    ("mv sky.hdr art/", "deny"),
    ("mv sky.exr art/", "deny"),
    ("mv rig.dae models/", "deny"),
    ("mv table.csv data/", "deny"),
    ("mv level.escn scenes/", "deny"),
    ("mv body.woff fonts/", "deny"),
    ("mv body.woff2 fonts/", "deny"),
    # Over-blocking direction: pairing the sidecar must still allow, for every
    # newly covered type. A vocabulary fix that broke pairing would be a
    # regression traded for a fix.
    ("mv hero.tga hero.tga.import art/", "allow"),
    ("mv hero.bmp hero.bmp.import art/", "allow"),
    ("mv sky.hdr sky.hdr.import art/", "allow"),
    ("mv sky.exr sky.exr.import art/", "allow"),
    ("mv rig.dae rig.dae.import models/", "allow"),
    ("mv table.csv table.csv.import data/", "allow"),
    ("mv level.escn level.escn.import scenes/", "allow"),
    ("mv body.woff body.woff.import fonts/", "allow"),
    ("mv body.woff2 body.woff2.import fonts/", "allow"),
    # Measured ABSENT: dds and ktx load directly at runtime and flac produces
    # no sidecar even for a genuine file, so there is no uid to orphan and a
    # deny here would be pure over-blocking.
    ("mv tex.dds art/", "allow"),
    ("mv tex.ktx art/", "allow"),
    ("mv music.flac audio/", "allow"),
]


def decide(command, cwd=None):
    tool_input = {"command": command}
    payload = {"tool_name": "Bash", "tool_input": tool_input}
    if cwd is not None:
        payload["cwd"] = cwd
    proc = subprocess.run(
        ["bash", str(GUARD)], input=json.dumps(payload), capture_output=True, text=True, timeout=10
    )
    out = proc.stdout.strip()
    if not out:
        return "allow"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


class TestGuard(unittest.TestCase):
    def test_decision_table(self):
        failures = []
        for command, expected in CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_regression_decision_table(self):
        failures = []
        for command, expected in REGRESSION_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_round3_decision_table(self):
        failures = []
        for command, expected in ROUND3_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_round4_decision_table(self):
        failures = []
        for command, expected in ROUND4_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_round5_decision_table(self):
        failures = []
        for command, expected in ROUND5_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_round6_decision_table(self):
        failures = []
        for command, expected in ROUND6_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_round7_decision_table(self):
        failures = []
        for command, expected in ROUND7_CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_cwd_pointing_at_unrelated_directory_still_denies(self):
        # CRITICAL 1 (fix round 2): the disk check must not treat "this path
        # doesn't resolve under cwd" as proof of "never imported". A real
        # scripts/player.gd and its .uid sit in directory A; the payload's
        # cwd names an unrelated, empty directory B (exactly what a
        # compound `cd subdir && mv ...` produces when cwd disagrees with
        # reality). Absence of proof under the WRONG directory is not proof
        # of safety, so this must still deny.
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            os.makedirs(os.path.join(a, "scripts"))
            os.makedirs(os.path.join(a, "entities"))
            with open(os.path.join(a, "scripts", "player.gd"), "w") as f:
                f.write("extends Node\n")
            with open(os.path.join(a, "scripts", "player.gd.uid"), "w") as f:
                f.write("uid://abc123\n")
            self.assertEqual(
                decide("mv scripts/player.gd entities/player.gd", cwd=b),
                "deny",
            )

    def test_cwd_pointing_at_nonexistent_directory_still_denies(self):
        # Same failure mode, the other common shape: cwd names a path that
        # does not exist on disk at all (not just "the wrong, but real,
        # directory").
        self.assertEqual(
            decide(
                "mv scripts/player.gd entities/player.gd",
                cwd="/nonexistent-dir-for-this-test/also-nonexistent",
            ),
            "deny",
        )

    def test_permits_godot_cache_removal(self):
        # A guard that fires on harmless operations gets disabled, and then it
        # protects nothing. .godot/ is regenerated by --import.
        self.assertEqual(decide("rm -rf .godot"), "allow")

    def test_deny_message_explains_the_fix(self):
        payload = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "mv a.gd b/a.gd"}}
        )
        proc = subprocess.run(
            ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
        )
        reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn(".uid", reason)

    def test_non_bash_tools_are_ignored(self):
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "a.gd"}})
        proc = subprocess.run(
            ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
        )
        self.assertEqual(proc.stdout.strip(), "")

    def test_copy_then_remove_with_sidecar_carried_over_still_asks(self):
        # IMPORTANT 6's fix distinguishes cp-then-rm WITHOUT a carried sidecar
        # (a move in disguise -> deny) from a bare cp with no later rm (real
        # duplication -> allow). This is the third shape: the sidecar IS
        # carried over via its own cp, so nothing is unrepairable -- but the
        # command still literally deletes scripts/player.gd and its sidecar
        # from their original path, which is exactly what the ask tier
        # exists to flag. This is deliberately "ask", not "allow": the guard
        # has no way to confirm, from text alone, that the two rm's targets
        # were the exact files just safely re-homed by the two cp's, so
        # treating the rm's at face value is the conservative, correct
        # choice, not a false positive.
        command = (
            "cp scripts/player.gd entities/player.gd && "
            "cp scripts/player.gd.uid entities/player.gd.uid && "
            "rm scripts/player.gd && rm scripts/player.gd.uid"
        )
        self.assertEqual(decide(command), "ask")

    def test_brand_new_file_with_no_sidecar_on_disk_is_allowed(self):
        # IMPORTANT 7: a file that was never imported has no .uid to lose.
        # The hook payload's `cwd` field (documented as a common PreToolUse
        # input) lets the guard stat for the sidecar instead of assuming.
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "scripts"))
            os.makedirs(os.path.join(d, "entities"))
            with open(os.path.join(d, "scripts", "new_feature.gd"), "w") as f:
                f.write("extends Node\n")
            self.assertEqual(
                decide("mv scripts/new_feature.gd entities/new_feature.gd", cwd=d),
                "allow",
            )

    def test_real_imported_file_with_sidecar_on_disk_still_denies(self):
        # The other half of IMPORTANT 7: the disk check must not become a
        # blanket escape hatch. A file whose sidecar genuinely exists next
        # to it is exactly the case this guard exists to catch.
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "scripts"))
            os.makedirs(os.path.join(d, "entities"))
            with open(os.path.join(d, "scripts", "player.gd"), "w") as f:
                f.write("extends Node\n")
            with open(os.path.join(d, "scripts", "player.gd.uid"), "w") as f:
                f.write("uid://abc123\n")
            self.assertEqual(
                decide("mv scripts/player.gd entities/player.gd", cwd=d),
                "deny",
            )

    def test_no_cwd_in_payload_still_denies_conservatively(self):
        # When the payload carries no cwd, the disk check cannot run at all.
        # The guard must not treat "cannot verify" as "assume safe" -- it
        # falls back to the same default as before IMPORTANT 7 existed.
        self.assertEqual(
            decide("mv scripts/new_feature.gd entities/new_feature.gd", cwd=None),
            "deny",
        )

    def test_fails_open_on_empty_stdin(self):
        proc = subprocess.run(
            ["bash", str(GUARD)], input="", capture_output=True, text=True, timeout=10
        )
        self.assertEqual(proc.stdout.strip(), "")
        self.assertEqual(proc.returncode, 0)

    def test_fails_open_on_malformed_json(self):
        proc = subprocess.run(
            ["bash", str(GUARD)], input="{not valid json", capture_output=True, text=True, timeout=10
        )
        self.assertEqual(proc.stdout.strip(), "")
        self.assertEqual(proc.returncode, 0)

    def test_fails_open_on_missing_command_key(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {}})
        proc = subprocess.run(
            ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
        )
        self.assertEqual(proc.stdout.strip(), "")
        self.assertEqual(proc.returncode, 0)

    def test_fails_open_when_python3_is_unreachable(self):
        # This guard depends on python3, not jq (see godot-guard.sh and
        # godot_guard.py for why). The same fail-open contract the original
        # bash-only version gave for a missing jq must hold for python3.
        payload = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "mv a.gd b/a.gd"}}
        )
        env = {"PATH": "/nonexistent-bin-dir"}
        proc = subprocess.run(
            ["/bin/bash", str(GUARD)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        self.assertEqual(proc.stdout.strip(), "")
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
