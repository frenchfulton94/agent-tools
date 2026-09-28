import json
import shutil
import tempfile
import os
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import refs, tscn

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_healthy_project_has_no_broken_references(self):
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"], [])

    def test_uid_index_maps_sidecar_uid_to_its_script(self):
        g = refs.graph(str(self.root))
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "scripts/player.gd")

    def test_move_without_sidecar_is_reported_broken(self):
        # Spec 3.4: the script moves, the .uid does not. Unrepairable by --import.
        (self.root / "entities").mkdir()
        shutil.move(str(self.root / "scripts" / "player.gd"),
                    str(self.root / "entities" / "player.gd"))
        (self.root / "scripts" / "player.gd.uid").unlink()
        g = refs.graph(str(self.root))
        self.assertEqual(len(g["broken"]), 1)
        self.assertEqual(g["broken"][0]["uid"], "uid://cnnyipgx21jca")
        self.assertEqual(g["broken"][0]["reason"], "uid-not-found")

    def test_move_with_sidecar_resolves_through_the_uid(self):
        # Spec 3.4: identity survives, so this is NOT reported broken even though
        # the .tscn still names the old path.
        (self.root / "entities").mkdir()
        shutil.move(str(self.root / "scripts" / "player.gd"),
                    str(self.root / "entities" / "player.gd"))
        shutil.move(str(self.root / "scripts" / "player.gd.uid"),
                    str(self.root / "entities" / "player.gd.uid"))
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"], [])
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "entities/player.gd")

    def test_deleted_target_with_no_uid_anywhere_is_missing_path(self):
        (self.root / "scripts" / "player.gd").unlink()
        (self.root / "scripts" / "player.gd.uid").unlink()
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"][0]["reason"], "uid-not-found")

    def test_orphan_detection(self):
        (self.root / "unused.gd").write_text("extends Node\n")
        g = refs.graph(str(self.root))
        self.assertIn("unused.gd", g["orphans"])
        # Autoload scripts are referenced from project.godot's [autoload]
        # section, not from any scene's ext_resource entries. A version of
        # this graph that never reads project.godot reports both as orphans
        # on every project that has autoloads -- a false positive that gets
        # a tool like this switched off. assertIn above cannot catch that
        # regression (it would still pass with a list full of false
        # positives); only assertNotIn on the known-referenced paths can.
        self.assertNotIn("scripts/game_state.gd", g["orphans"])
        self.assertNotIn("scripts/audio.gd", g["orphans"])
        # The main scene (run/main_scene) is likewise referenced by nothing
        # inside any scene file. It happens to be excluded from orphan
        # candidates today because orphan detection only considers
        # .gd/.gdshader files, but the assertion documents the invariant
        # refs.py maintains regardless of that filter's current scope.
        self.assertNotIn("main.tscn", g["orphans"])

    def test_duplicate_uids_are_reported(self):
        (self.root / "copy.gd").write_text("extends Node\n")
        (self.root / "copy.gd.uid").write_text("uid://cnnyipgx21jca")
        g = refs.graph(str(self.root))
        self.assertEqual(len(g["duplicate_uids"]), 1)
        self.assertEqual(g["duplicate_uids"][0]["uid"], "uid://cnnyipgx21jca")

    def test_unparsable_and_unreadable_scenes_are_each_reported_once(self):
        # main.tscn is the only scene that references scripts/player.gd via
        # its ext_resource entry. Corrupt it and graph() can no longer see
        # that reference -- it must say so via parse_errors rather than
        # quietly presenting an orphan list as if nothing were skipped.
        # This is the exact anti-pattern tscn.py's own docstring warns
        # against, one layer up: a partial result presented as complete is
        # how a user deletes something they never saw.
        #
        # Alongside it, corrupt a second .tscn and a .tres with syntax
        # errors, and add one more .tscn that can't even be *opened* -- a
        # dangling symlink, which survives a git checkout and is an
        # ordinary failure mode, not a hypothetical one. All four must be
        # named in parse_errors exactly once each: not zero (the bug this
        # fix round exists to close) and not twice (a regression to
        # re-parsing / double-reporting the same file, the failure mode a
        # naive two-call-site fix would produce).
        with open(self.root / "main.tscn", "a") as f:
            f.write("this is not a heading, property, or comment\n")
        (self.root / "broken_scene.tscn").write_text("also not one\n")
        (self.root / "broken_resource.tres").write_text("nor this\n")
        (self.root / "dangling.tscn").symlink_to(self.root / "does_not_exist.tscn")

        with mock.patch("godot.tscn.parse", wraps=tscn.parse) as spy:
            g = refs.graph(str(self.root))

        error_paths = [e["path"] for e in g["parse_errors"]]

        # Every corrupt/unreadable file is named, exactly once.
        for expected in (
            "main.tscn",
            "broken_scene.tscn",
            "broken_resource.tres",
            "dangling.tscn",
        ):
            self.assertEqual(
                error_paths.count(expected), 1,
                f"expected exactly one parse_errors entry for {expected!r}, "
                f"got {error_paths.count(expected)}",
            )
        self.assertEqual(len(g["parse_errors"]), 4)

        # tscn.parse() is only ever reachable for the three files that can
        # be opened at all -- dangling.tscn fails at the open() step and
        # never reaches it. Pinning the call count directly (rather than by
        # proxy through parse_errors' length) is what would catch a
        # regression to a second parse site being reintroduced elsewhere:
        # main.tscn (the only scene that also parses successfully
        # elsewhere in this suite) would then be parsed twice, and this
        # count would rise to 4 without parse_errors necessarily changing.
        self.assertEqual(spy.call_count, 3)

        # The unreadable file's entry says so distinctly from a syntax
        # error -- a caller (or a human) needs to know whether the fix is
        # "edit the scene" or "check the filesystem".
        by_path = {e["path"]: e["error"] for e in g["parse_errors"]}
        self.assertIn("unreadable", by_path["dangling.tscn"].lower())
        self.assertNotIn("unreadable", by_path["main.tscn"].lower())

        # The .uid sidecar is a separate code path from the scene parse, so
        # the uid is still known even though the scene that names it isn't.
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "scripts/player.gd")

        # scripts/player.gd was referenced only from inside main.tscn, which
        # can no longer be read -- the graph genuinely cannot confirm it is
        # still used, so it is reported as an orphan. That is legitimate
        # *only* because parse_errors names the specific file responsible;
        # asserting both together (rather than "orphans contains X" alone,
        # or "parse_errors is non-empty" alone -- either one in isolation
        # can't tell a caller *why* the orphan call is uncertain) is what
        # makes this assertion capable of failing on its own, rather than
        # being implied for free by the count assertion above.
        self.assertIn("scripts/player.gd", g["orphans"])
        self.assertIn("main.tscn", error_paths)


class TestUnreadableSidecarsAreReportedNotRaised(unittest.TestCase):
    """Final whole-branch review, IMPORTANT 2.

    Task 4 hardened the .tscn read path in _parse_scenes so an unreadable file
    became a parse_errors entry rather than an exception, on the reasoning that
    "broken symlinks survive a checkout, so this is ordinary, not exotic." The
    sidecar reads twenty lines below never got the same treatment -- and a
    project has one .uid per script, far more of them than .tscn files.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="godot-sidecar-")
        shutil.copytree(SAMPLE, self.root, dirs_exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _graph(self):
        return refs.graph(self.root)

    def test_dangling_uid_symlink_is_reported(self):
        link = os.path.join(self.root, "dangling.gd.uid")
        os.symlink(os.path.join(self.root, "nowhere-at-all"), link)
        result = self._graph()  # must not raise FileNotFoundError
        paths = [e["path"] for e in result["parse_errors"]]
        self.assertIn("dangling.gd.uid", paths)

    def test_unreadable_import_sidecar_is_reported(self):
        bad = os.path.join(self.root, "art.png.import")
        with open(bad, "w") as f:
            f.write('uid="uid://abc"\n')
        os.chmod(bad, 0o000)
        try:
            if os.access(bad, os.R_OK):
                self.skipTest("running as a user that ignores the mode bits")
            result = self._graph()  # must not raise PermissionError
        finally:
            # Restore before tearDown, not via addCleanup: cleanups run AFTER
            # tearDown, by which point the whole tree is already gone.
            os.chmod(bad, 0o644)
        paths = [e["path"] for e in result["parse_errors"]]
        self.assertIn("art.png.import", paths)

    def test_non_utf8_uid_is_reported_not_silently_mangled(self):
        # Re-review IMPORTANT A. errors="replace" would decode this to
        # "uid://b\ufffd\ufffd123" and record it in the index: the scene's real
        # uid:// then resolves to nothing, so the script lands in BOTH `broken`
        # and `orphans` while parse_errors: [] claims the report is complete.
        # A crash is bad ergonomics; this would be a confident wrong answer
        # about the exact case the module exists to diagnose.
        bad = os.path.join(self.root, "scripts", "player.gd.uid")
        os.makedirs(os.path.dirname(bad), exist_ok=True)
        with open(bad, "wb") as f:
            f.write(b"uid://b\xff\xfe123")
        result = self._graph()
        paths = [e["path"] for e in result["parse_errors"]]
        self.assertIn("scripts/player.gd.uid", paths)
        blob = json.dumps(result)
        self.assertNotIn("\ufffd", blob)

    def test_a_healthy_project_still_reports_no_parse_errors(self):
        # Over-blocking direction: the hardening must not manufacture errors.
        self.assertEqual(self._graph()["parse_errors"], [])


if __name__ == "__main__":
    unittest.main()
