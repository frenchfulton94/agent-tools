import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import api, engine

HAS_GODOT = engine.find_binary() is not None

FAKE_DUMP = {
    "header": {"version_full_name": "Godot Engine v4.7.2.stable.official"},
    "classes": [
        {"name": "Object", "inherits": None, "brief_description": "Base class.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "Node", "inherits": "Object", "brief_description": "Base class for scene objects.",
         "description": "", "methods": [{"name": "add_child", "description": "Adds a child."}],
         "properties": [], "signals": [{"name": "ready", "description": "Emitted when ready."}]},
        {"name": "Node2D", "inherits": "Node", "brief_description": "A 2D game object.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "CharacterBody2D", "inherits": "PhysicsBody2D",
         "brief_description": "A 2D physics body specialized for characters moved by script.",
         "description": "", "methods": [], "properties": [], "signals": []},
        # brief_description says nothing about gravity -- only description
        # does. Exists to pin IMPORTANT 8: search_classes must also scan
        # description, not just name/brief_description, or a concept search
        # like "gravity" returns nothing despite this being exactly the node
        # such a search exists to find.
        {"name": "RigidBody2D", "inherits": "PhysicsBody2D",
         "brief_description": "A 2D physics body that is moved by a physics simulation.",
         "description": ("This node simulates realistic physics, reacting to forces and "
                          "gravity from the physics engine, unlike a CharacterBody2D."),
         "methods": [], "properties": [], "signals": []},
    ],
}


class TestLookupAndSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        (Path(self.tmp) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
        # NOTE: this must match what engine_version() actually returns, or
        # load_dump() sees a version mismatch against the live engine, deletes
        # this fixture, and regenerates from the real ~1,036-class dump --
        # silently making every assertion below exercise the real engine
        # instead of FAKE_DUMP. `godot --version` prints a bare
        # "4.7.2.stable.official.ed1daf0bf" (no "Godot Engine v" prefix, plus
        # a build hash), not the brief's original literal.
        #
        # Gated on catching MissingBinary, not on engine.find_binary()
        # truthiness: find_binary() returns a GODOT_BIN override without
        # checking it actually exists, so a stale/bad GODOT_BIN would make
        # the truthiness check pass and then engine_version() raise
        # MissingBinary anyway, crashing every test in this class instead of
        # falling back to "test". Catching the exception handles both a
        # genuine absence and a claimed-but-not-runnable binary the same way.
        try:
            version = api.engine_version()
        except engine.MissingBinary:
            version = "test"
        (Path(self.tmp) / "VERSION").write_text(version)

    def test_lookup_returns_inheritance_chain(self):
        found = api.lookup_class("Node2D", cache_dir=self.tmp)
        self.assertEqual(found["inheritance_chain"], ["Node", "Object"])

    def test_lookup_is_case_insensitive(self):
        self.assertIsNotNone(api.lookup_class("node2d", cache_dir=self.tmp))

    def test_lookup_unknown_class_returns_none(self):
        self.assertIsNone(api.lookup_class("NoSuchClass", cache_dir=self.tmp))

    def test_lookup_single_member(self):
        found = api.lookup_class("Node", member="add_child", cache_dir=self.tmp)
        self.assertEqual(found["member"]["name"], "add_child")

    def test_search_matches_brief_description(self):
        hits = api.search_classes("characters moved by script", cache_dir=self.tmp)
        self.assertEqual(hits[0]["name"], "CharacterBody2D")

    def test_search_matches_name(self):
        names = [h["name"] for h in api.search_classes("node2d", cache_dir=self.tmp)]
        self.assertIn("Node2D", names)

    def test_search_matches_full_description_not_just_brief(self):
        # IMPORTANT 8: "gravity" appears nowhere in any class's name or
        # brief_description in this fixture -- only in RigidBody2D's
        # description. A search that only scans name/brief_description
        # returns zero hits here, which is the concept-search feature not
        # working, not a lesser version of it.
        names = [h["name"] for h in api.search_classes("gravity", cache_dir=self.tmp)]
        self.assertIn("RigidBody2D", names)


class TestEngineVersionRobustness(unittest.TestCase):
    """engine_version() must not crash on blank output and must not trust
    the first line blindly -- IMPORTANT 2 and IMPORTANT 3."""

    def test_empty_stdout_falls_back_to_stderr_instead_of_indexerror(self):
        # `result.stdout or result.stderr` treats whitespace-only stdout as
        # truthy, so it never falls through to stderr even when stderr holds
        # the real version -- and ''.splitlines()[0] then raises a bare
        # IndexError instead of finding it there.
        fake = engine.Result("   \n", "4.7.2.stable.official.ed1daf0bf\n", 0, False)
        with mock.patch.object(engine, "run", return_value=fake):
            self.assertEqual(api.engine_version(), "4.7.2.stable.official.ed1daf0bf")

    def test_banner_line_before_version_is_skipped(self):
        # stdout.splitlines()[0] would return the banner line here, not the
        # version on the line beneath it.
        fake = engine.Result(
            "Some Vulkan banner line\n4.7.2.stable.official.ed1daf0bf\n", "", 0, False
        )
        with mock.patch.object(engine, "run", return_value=fake):
            self.assertEqual(api.engine_version(), "4.7.2.stable.official.ed1daf0bf")

    def test_no_version_shaped_line_anywhere_raises_clear_error(self):
        fake = engine.Result("   \n", "   \n", 0, False)
        with mock.patch.object(engine, "run", return_value=fake):
            with self.assertRaises(RuntimeError):
                api.engine_version()


class TestMissingVersionFile(unittest.TestCase):
    """A dump present with VERSION missing (a process killed between writing
    the dump and writing VERSION) must force one regeneration, not serve the
    stale dump forever -- IMPORTANT 4."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()

    def test_dump_present_but_version_missing_forces_one_regeneration(self):
        (Path(self.tmp) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
        # Deliberately no VERSION file.

        regenerated = {
            "header": {},
            "classes": [{"name": "Regenerated", "inherits": None, "brief_description": "",
                         "description": "", "methods": [], "properties": [], "signals": []}],
        }

        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result("5.5.5.stable.official.f00dcafe\n", "", 0, False)
            (Path(cwd) / "extension_api.json").write_text(json.dumps(regenerated))
            return engine.Result("", "", 0, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            dump = api.load_dump(cache_dir=self.tmp)

        self.assertEqual([c["name"] for c in dump["classes"]], ["Regenerated"])
        self.assertEqual(
            (Path(self.tmp) / "VERSION").read_text(), "5.5.5.stable.official.f00dcafe"
        )


class TestWarmCacheRevalidation(unittest.TestCase):
    """A warm in-memory cache hit must still notice a live engine version
    change -- IMPORTANT 5. Otherwise an engine upgrade in this long-lived MCP
    server stays invisible until the process restarts."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()

    def test_warm_cache_notices_a_live_version_change(self):
        dumps = {
            "1.0.0.stable.official.aaaaaaaa": {
                "header": {}, "classes": [{"name": "Old", "inherits": None, "brief_description": "",
                                            "description": "", "methods": [], "properties": [], "signals": []}],
            },
            "2.0.0.stable.official.bbbbbbbb": {
                "header": {}, "classes": [{"name": "New", "inherits": None, "brief_description": "",
                                            "description": "", "methods": [], "properties": [], "signals": []}],
            },
        }
        state = {"version": "1.0.0.stable.official.aaaaaaaa"}

        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result(state["version"] + "\n", "", 0, False)
            (Path(cwd) / "extension_api.json").write_text(json.dumps(dumps[state["version"]]))
            return engine.Result("", "", 0, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            first = api.load_dump(cache_dir=self.tmp)
            self.assertEqual([c["name"] for c in first["classes"]], ["Old"])

            # Simulate an engine upgrade happening under a long-lived process:
            # _CACHE still holds the old dump in memory; nothing on disk was
            # touched by us directly.
            state["version"] = "2.0.0.stable.official.bbbbbbbb"

            second = api.load_dump(cache_dir=self.tmp)
        self.assertEqual([c["name"] for c in second["classes"]], ["New"])


class TestCorruptCacheSelfHeals(unittest.TestCase):
    """CRITICAL 1, self-heal half: a corrupt extension_api.json must not
    wedge every future call on the same JSONDecodeError forever."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()

    def test_corrupt_dump_is_deleted_and_regenerated_once(self):
        (Path(self.tmp) / "VERSION").write_text("9.9.9.stable.official.deadbeef")
        (Path(self.tmp) / "extension_api.json").write_text("{not valid json at all")

        healed = {
            "header": {},
            "classes": [{"name": "Healed", "inherits": None, "brief_description": "",
                         "description": "", "methods": [], "properties": [], "signals": []}],
        }

        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result("9.9.9.stable.official.deadbeef\n", "", 0, False)
            (Path(cwd) / "extension_api.json").write_text(json.dumps(healed))
            return engine.Result("", "", 0, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            dump = api.load_dump(cache_dir=self.tmp)

        self.assertEqual([c["name"] for c in dump["classes"]], ["Healed"])
        # The file on disk is genuinely fixed, not just the in-memory copy.
        on_disk = json.loads((Path(self.tmp) / "extension_api.json").read_text())
        self.assertEqual([c["name"] for c in on_disk["classes"]], ["Healed"])


class TestAtomicGeneration(unittest.TestCase):
    """CRITICAL 1, race half. A reliable *timing-dependent* concurrency test
    (N real threads racing a shared clock) is inherently a little
    probabilistic, so this class does both: a direct test of the
    atomic-replace helper's failure behavior (fully deterministic), and a
    concurrency test built so its correctness does not depend on timing --
    every writer's slow/chunked work happens in its own private scratch
    directory no matter how threads interleave, and the only operation that
    ever touches the shared path is a single os.replace(). See the class
    docstring on the concurrency test for how this was verified to actually
    catch the bug it's guarding, not just always pass by construction.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()

    def test_failed_regeneration_leaves_no_partial_file_and_no_scratch_dir(self):
        # An existing (stale) dump is present; the mocked engine "crashes"
        # during regeneration (produces no extension_api.json at all). The
        # old dump must be gone (it really is stale) but nothing partial or
        # corrupt takes its place, and no scratch directory leaks.
        (Path(self.tmp) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
        (Path(self.tmp) / "VERSION").write_text("stale-marker")

        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result("1.2.3.stable.official.cafecafe\n", "", 0, False)
            return engine.Result("", "simulated crash, no output written", 1, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            with self.assertRaises(RuntimeError):
                api.load_dump(cache_dir=self.tmp)

        remaining = os.listdir(self.tmp)
        self.assertNotIn("extension_api.json", remaining)  # removed, not corrupted
        # No leaked tempfile.mkdtemp() scratch directory left behind.
        self.assertEqual([n for n in remaining if n != "VERSION"], [])

    def test_successful_generation_leaves_no_scratch_directory_behind(self):
        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result("1.2.3.stable.official.cafecafe\n", "", 0, False)
            (Path(cwd) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
            return engine.Result("", "", 0, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            api.load_dump(cache_dir=self.tmp)

        self.assertEqual(sorted(os.listdir(self.tmp)), ["VERSION", "extension_api.json"])

    def test_two_concurrent_cold_cache_writers_never_produce_a_torn_file(self):
        """Deterministic concurrency proof -- not a timing race.

        Reproduces the coordinator's own scenario directly: "N overlapping
        cold-cache callers each shell out their own regeneration into the
        same path." Two threads both discover a missing dump_path at once
        and race to create it, exactly as the coordinator measured against
        the real engine (found 4/253 unparseable samples under 8 concurrent
        writers pre-fix, sampling the file every 2ms).

        A first attempt at this test used that same technique -- a sampler
        thread polling dump_path on a tight interval while N writer threads
        raced. It turned out unreliable as a regression test: reverting
        `_generate_dump` to skip the scratch directory (writing straight at
        `dump_path`, reproducing pre-fix behavior) produced real,
        observable corruption -- confirmed by eye via background-thread
        tracebacks (FileNotFoundError / JSONDecodeError racing on
        os.remove/open) -- but the sampler-based test still reported "OK"
        in 5 out of 5 runs against that broken code, because Python's GIL
        and the small fixture payload made truly overlapping torn writes
        too rare to depend on for a pass/fail assertion. A test a real bug
        cannot reliably fail is worse than no test, so it was replaced with
        this one, which uses `threading.Event` to force the interleaving
        deterministically instead of hoping the scheduler produces it:

        1. Two writers (A, B) both start against a totally empty cache_dir
           (no dump_path, no VERSION -- a genuine cold-cache race, not a
           version-driven regeneration, which deletes the old file
           up front and so never has two writers targeting the same
           existing path at once).
        2. Both write a complete, valid payload into their OWN private
           scratch directory, then deliberately park -- before either can
           reach `_generate_dump`'s `os.replace()` -- until released.
        3. While both are parked, dump_path must not exist at all: neither
           writer has published, and under the fix, nothing but the final
           `os.replace()` ever touches it -- so there is no window where a
           reader can observe a torn or partial file.
        4. A is released and publishes; dump_path must now be exactly A's
           complete content.
        5. B is released and publishes; dump_path must now be exactly B's
           complete content -- a clean swap, not a merge with A's.

        Confirmed this catches the regression: reverting `_generate_dump`
        to write directly into `cache_dir` (no scratch directory) makes
        step 3's `assertFalse(dump_path.exists())` fail immediately and
        deterministically, every time -- because under that code, each
        writer's very first `write_text()` call lands straight on the
        shared `dump_path`, visible well before either thread parks. See
        the fix-round-1 report for that transcript.
        """
        dump_a = {"header": {}, "classes": [
            {"name": "A", "inherits": None, "brief_description": "",
             "description": "", "methods": [], "properties": [], "signals": []},
        ]}
        dump_b = {"header": {}, "classes": [
            {"name": "B", "inherits": None, "brief_description": "",
             "description": "", "methods": [], "properties": [], "signals": []},
        ]}
        payload_by_thread = {"writer-A": dump_a, "writer-B": dump_b}
        parked = {"writer-A": threading.Event(), "writer-B": threading.Event()}
        release = {"writer-A": threading.Event(), "writer-B": threading.Event()}

        def fake_run(args, cwd=None, timeout=None):
            if args[:1] == ["--version"]:
                return engine.Result("1.0.0.stable.official.aaaaaaaa\n", "", 0, False)
            name = threading.current_thread().name
            target = Path(cwd) / "extension_api.json"
            target.write_text(json.dumps(payload_by_thread[name]))
            parked[name].set()
            release[name].wait(timeout=5)
            return engine.Result("", "", 0, False)

        dump_path = Path(self.tmp) / "extension_api.json"
        with mock.patch.object(engine, "run", side_effect=fake_run):
            api._CACHE.clear()
            t_a = threading.Thread(
                target=api.load_dump, kwargs={"cache_dir": self.tmp}, name="writer-A"
            )
            t_b = threading.Thread(
                target=api.load_dump, kwargs={"cache_dir": self.tmp}, name="writer-B"
            )
            t_a.start()
            t_b.start()
            try:
                self.assertTrue(parked["writer-A"].wait(timeout=5), "writer A never parked")
                self.assertTrue(parked["writer-B"].wait(timeout=5), "writer B never parked")

                # Both writers hold complete, valid payloads in their own
                # scratch directories; neither has published. dump_path
                # must not exist at all -- never a torn/partial file.
                self.assertFalse(dump_path.exists())

                release["writer-A"].set()
                t_a.join(timeout=5)
                after_a = json.loads(dump_path.read_text())
                self.assertEqual([c["name"] for c in after_a["classes"]], ["A"])

                release["writer-B"].set()
                t_b.join(timeout=5)
                after_b = json.loads(dump_path.read_text())
                self.assertEqual([c["name"] for c in after_b["classes"]], ["B"])
            finally:
                release["writer-A"].set()
                release["writer-B"].set()
                t_a.join(timeout=5)
                t_b.join(timeout=5)


@unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores permission bits")
class TestUnwritableCacheDir(unittest.TestCase):
    """IMPORTANT 7: an unwritable cache directory must name the real cause,
    not surface as a generic 'Godot did not produce extension_api.json'."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        os.chmod(self.tmp, 0o500)

    def tearDown(self):
        os.chmod(self.tmp, 0o700)

    def test_names_the_real_cause(self):
        def fake_run(args, cwd=None, timeout=None):
            return engine.Result("1.0.0.stable.official.aaaaaaaa\n", "", 0, False)

        with mock.patch.object(engine, "run", side_effect=fake_run):
            with self.assertRaises(RuntimeError) as ctx:
                api.load_dump(cache_dir=self.tmp)

        message = str(ctx.exception)
        self.assertIn("not writable", message)
        self.assertIn(self.tmp, message)


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestAgainstRealEngine(unittest.TestCase):
    def test_dump_is_generated_and_cached_by_version(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        dump = api.load_dump(cache_dir=tmp)
        self.assertGreater(len(dump["classes"]), 500)
        self.assertTrue((Path(tmp) / "extension_api.json").is_file())

    def test_real_class_carries_documentation(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        found = api.lookup_class("CharacterBody2D", cache_dir=tmp)
        self.assertIn("character", (found["brief_description"] or "").lower())


if __name__ == "__main__":
    unittest.main()
