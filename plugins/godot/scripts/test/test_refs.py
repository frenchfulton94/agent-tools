import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import refs

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

    def test_unparsable_scene_is_reported_not_silently_skipped(self):
        # main.tscn is the only scene that references scripts/player.gd via
        # its ext_resource entry. Corrupt it and graph() can no longer see
        # that reference -- it must say so via parse_errors rather than
        # quietly presenting an orphan list as if nothing were skipped.
        # This is the exact anti-pattern tscn.py's own docstring warns
        # against, one layer up: a partial result presented as complete is
        # how a user deletes something they never saw.
        with open(self.root / "main.tscn", "a") as f:
            f.write("this is not a heading, property, or comment\n")

        g = refs.graph(str(self.root))

        # (a) parse_errors names the file that failed.
        main_tscn_errors = [e for e in g["parse_errors"] if e["path"] == "main.tscn"]
        self.assertEqual(len(main_tscn_errors), 1)

        # (b) it appears exactly once -- _uid_index and graph()'s own
        # ext_resource scan must share one parse pass over the file, not
        # each report (or each re-parse) it independently.
        self.assertEqual(len(g["parse_errors"]), 1)

        # The .uid sidecar is a separate code path from the scene parse, so
        # the uid is still known even though the scene that names it isn't.
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "scripts/player.gd")

        # (c) scripts/player.gd was referenced only from inside the now
        # unparsable scene, so the graph legitimately cannot confirm it is
        # still used -- but if it shows up in orphans, parse_errors must be
        # non-empty right alongside it, so a caller can tell the report is
        # partial rather than a clean, confident "unused".
        if "scripts/player.gd" in g["orphans"]:
            self.assertTrue(g["parse_errors"])


if __name__ == "__main__":
    unittest.main()
