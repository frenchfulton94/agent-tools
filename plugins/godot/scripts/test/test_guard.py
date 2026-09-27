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
    # Spec 3.8: UIDs are path-derived, so deleting a sidecar in place
    # regenerates the identical UID. Denying these would be noise.
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
