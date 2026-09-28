import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine, render  # noqa: E402
import godot_mcp_server as server  # noqa: E402

SERVER = Path(__file__).resolve().parents[1] / "godot_mcp_server.py"
SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"

HAS_GODOT = engine.find_binary() is not None
HAS_DISPLAY = HAS_GODOT and render.has_display()


def _fs_is_case_insensitive():
    """True if a file created under the system temp directory is also
    reachable via an upper-cased name -- i.e. the filesystem folds case
    (APFS's default mode on macOS, but not the only mode a real Mac can be
    running). Checked empirically with a real probe file rather than
    assumed, since the case-insensitive-but-case-preserving bypass this
    guards against only exists on such a filesystem.
    """
    probe_dir = tempfile.mkdtemp(prefix="godot-fscheck-")
    try:
        probe = os.path.join(probe_dir, "CaseProbe")
        with open(probe, "w"):
            pass
        return os.path.exists(os.path.join(probe_dir, "caseprobe"))
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)


FS_IS_CASE_INSENSITIVE = _fs_is_case_insensitive()


def rpc(*messages, timeout=180):
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    proc = subprocess.run(
        ["python3", str(SERVER)], input=payload, capture_output=True, text=True, timeout=timeout
    )
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def call(name, arguments):
    responses = rpc(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": name, "arguments": arguments}},
    )
    return responses[-1]


class TestProtocol(unittest.TestCase):
    def test_initialize_reports_server_info(self):
        responses = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "godot")

    def test_tools_list_exposes_nine_tools(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        names = {t["name"] for t in responses[-1]["result"]["tools"]}
        self.assertEqual(
            names,
            {"project_overview", "scene_tree", "reference_graph", "check_script",
             "run_scene", "check_shader", "screenshot_scene", "lookup_class",
             "search_classes"},
        )

    def test_every_tool_declares_a_description_and_schema(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        for tool in responses[-1]["result"]["tools"]:
            self.assertTrue(tool.get("description"), tool["name"])
            self.assertIn("inputSchema", tool)

    def test_unknown_tool_is_an_error_not_a_crash(self):
        response = call("no_such_tool", {})
        self.assertTrue(response["result"].get("isError"))


class TestParserToolsNeedNoBinary(unittest.TestCase):
    """Spec decision 16: these three answer without a Godot install."""

    def test_project_overview(self):
        response = call("project_overview", {"project_path": str(SAMPLE)})
        text = response["result"]["content"][0]["text"]
        self.assertIn("Sample", text)
        self.assertFalse(response["result"].get("isError"))

    def test_scene_tree(self):
        response = call("scene_tree", {"scene_path": str(SAMPLE / "main.tscn")})
        self.assertIn("Main", response["result"]["content"][0]["text"])

    def test_reference_graph(self):
        response = call("reference_graph", {"project_path": str(SAMPLE)})
        self.assertFalse(response["result"].get("isError"))


class TestReferenceGraphSurfacesParseErrors(unittest.TestCase):
    """Drift item 1: refs.graph() now returns a fifth key, parse_errors, and
    a caller reading `broken: []` while files were skipped is being told a
    partial answer is a complete one. The tool's output must put that where
    it cannot be missed, not at the tail of a JSON blob.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clean_project_has_no_warning_and_empty_parse_errors(self):
        response = call("reference_graph", {"project_path": str(self.root)})
        self.assertFalse(response["result"].get("isError"))
        text = response["result"]["content"][0]["text"]
        self.assertNotIn("WARNING", text)
        body = json.loads(text)
        self.assertEqual(body["parse_errors"], [])
        # parse_errors is the first key, not buried after broken/orphans/etc.
        self.assertEqual(list(body.keys())[0], "parse_errors")

    def test_corrupt_scene_produces_a_prominent_warning(self):
        with open(self.root / "main.tscn", "a") as f:
            f.write("this is not a heading, property, or comment\n")

        response = call("reference_graph", {"project_path": str(self.root)})
        self.assertFalse(response["result"].get("isError"))
        text = response["result"]["content"][0]["text"]

        # The warning appears before the JSON blob, not only inside it.
        json_start = text.index("{")
        self.assertIn("WARNING", text[:json_start])
        self.assertIn("parse_errors", text[:json_start])

        body = json.loads(text[json_start:])
        self.assertEqual(len(body["parse_errors"]), 1)
        self.assertEqual(body["parse_errors"][0]["path"], "main.tscn")


class TestNeverDumpsRawApiLoad(unittest.TestCase):
    """Drift item 2: api.load_dump() stashes an internal
    "__api_search_index__" key on the dict it returns. lookup_class and
    search_classes must never leak it -- they build fresh dicts instead.

    IMPORTANT (fix round 1, found by running the break-a-test drill on all
    four drift-item tests, as recommended): the original version of the
    lookup_class test called only lookup_class, in its own fresh subprocess.
    The leak key is stashed onto the *in-memory* dump object as a side
    effect of api.search_classes() calling api._search_index() -- api.py's
    module-level _CACHE, and therefore that key, is never populated at all
    unless something in the *same process* called search_classes first.
    lookup_class itself never touches _search_index(). So the old test's
    dump never had the key to leak in the first place, regardless of
    whether lookup_class's own guard (using api.lookup_class() rather than
    dumping api.load_dump() raw) was present or removed -- confirmed
    directly: with call_tool()'s lookup_class branch changed to
    `json.dumps(api.load_dump())`, the old single-call test still passed.
    Fixed by calling search_classes first, in the same server subprocess, so
    the key is genuinely present on the cached dump before lookup_class runs
    against it.
    """

    @unittest.skipUnless(HAS_GODOT, "needs a Godot binary to generate the dump")
    def test_lookup_class_does_not_leak_the_search_index_after_search_ran_first(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "search_classes", "arguments": {"query": "body", "limit": 5}}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "lookup_class", "arguments": {"name": "Node"}}},
        )
        # search_classes ran first, in this same process -- its own call to
        # api._search_index() has genuinely stashed the key onto the cached
        # dump object by the time lookup_class runs against that same cache.
        lookup_result = responses[-1]["result"]
        self.assertFalse(lookup_result.get("isError"))
        text = lookup_result["content"][0]["text"]
        self.assertNotIn("__api_search_index__", text)

    @unittest.skipUnless(HAS_GODOT, "needs a Godot binary to generate the dump")
    def test_search_classes_does_not_leak_the_search_index(self):
        # search_classes populates the key itself, on its own first call, so
        # a single isolated call already exercises the real risk (unlike
        # lookup_class above) -- this one was not a false negative.
        response = call("search_classes", {"query": "body", "limit": 5})
        text = response["result"]["content"][0]["text"]
        self.assertNotIn("__api_search_index__", text)


class TestCheckShaderTimeoutIsAnErrorNotACleanCompile(unittest.TestCase):
    """Drift item 3: render.check_shader() raises ShaderCheckTimedOut rather
    than returning [] on a timeout. The server must report that as an error,
    never as "Shader compiled with no errors."

    Runs entirely against a mocked render.check_shader, so it needs neither
    Godot nor a display and always executes -- mirroring
    TestCheckShaderPathAnchoring's own rationale in test_render.py.
    """

    def test_timeout_propagates_out_of_call_tool(self):
        # call_tool() itself must not swallow this -- it is main()'s/
        # dispatch_tool_call()'s job to translate it, not call_tool()'s.
        with mock.patch.object(
            server.render, "check_shader",
            side_effect=render.ShaderCheckTimedOut("check_shader timed out after 1s"),
        ):
            with self.assertRaises(render.ShaderCheckTimedOut) as ctx:
                server.call_tool("check_shader", {
                    "project_path": str(SAMPLE), "shader_path": "res://good.gdshader",
                })
            self.assertIn("timed out", str(ctx.exception))

    def test_timeout_is_reported_as_a_tool_error_not_a_clean_compile(self):
        # End-to-end through dispatch_tool_call() (in-process, so the mock
        # actually takes effect -- rpc() spawns a separate process and would
        # not see it): a timeout must come back as isError, with the
        # exception's own clean message -- not the "compiled with no
        # errors" message, and not a traceback either.
        #
        # IMPORTANT (fix round 1, break-a-test drill): the original version
        # asserted only `assertIn("timed out", text)` and
        # `assertNotIn("compiled with no errors", text)`. Both stay true even
        # with the specific `except render.ShaderCheckTimedOut` clause
        # removed from dispatch_tool_call(): ShaderCheckTimedOut is an
        # Exception subclass, so it falls into the generic `except
        # Exception: traceback.format_exc(limit=3)` branch instead, and that
        # traceback's last line is `godot.render.ShaderCheckTimedOut: check
        # shader timed out after 1s...` -- which contains "timed out" and
        # does not contain "compiled with no errors", so the old assertions
        # passed on a raw traceback. Confirmed directly: removing that one
        # except clause left this test green. Fixed by asserting the text is
        # exactly the exception's own message and contains no "Traceback".
        message = "check_shader timed out after 1s"
        with mock.patch.object(
            server.render, "check_shader",
            side_effect=render.ShaderCheckTimedOut(message),
        ):
            result = server.dispatch_tool_call("check_shader", {
                "project_path": str(SAMPLE), "shader_path": "res://good.gdshader",
            })
        self.assertTrue(result.get("isError"))
        text = result["content"][0]["text"]
        self.assertEqual(text, message)
        self.assertNotIn("Traceback", text)
        self.assertNotIn("compiled with no errors", text)


class TestScreenshotPixelSurfaces(unittest.TestCase):
    """Drift item 4: render.screenshot_scene()'s result dict now carries a
    "pixel" key. The tool must pass it through rather than dropping it.
    """

    @unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
    def test_screenshot_scene_reports_the_centre_pixel(self):
        out_dir = Path(tempfile.mkdtemp(prefix="godot-shot-test-"))
        try:
            response = call("screenshot_scene", {
                "project_path": str(SAMPLE),
                "scene": "res://main.tscn",
                "out_path": str(out_dir / "scene.png"),
                "width": 64,
                "height": 64,
                "frames": 2,
            })
            self.assertFalse(response["result"].get("isError"), response["result"])
            body = json.loads(response["result"]["content"][0]["text"])
            self.assertIn("pixel", body)
            self.assertIsNotNone(body["pixel"])
            self.assertEqual(len(body["pixel"]), 3)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)


class TestScreenshotOutPathIsContainedOutsideTheProject(unittest.TestCase):
    """CRITICAL (fix round 1): out_path reached the renderer with no
    containment check. The reviewer verified empirically that passing
    out_path = <project>/project.godot on a disposable copy SILENTLY
    OVERWROTE it -- 372 bytes of project config replaced by 165 bytes
    starting with the PNG magic number, no warning, no isError, no diff.
    That directly contradicts this server's one load-bearing property
    (read-only w.r.t. project source): a tool call is invisible to the
    Task 9 guard hook, so an unconstrained out_path was a mutation channel
    nothing could observe.

    Uses a temp copy of the fixture, never the shared committed one under
    test/fixtures/ -- these tests are specifically probing whether the
    server can be made to overwrite a project file, so they must never
    risk actually doing that to a file every other test in this suite
    depends on.

    The rejection path runs entirely inside call_tool(), before
    render.screenshot_scene() (and therefore before any display/Godot
    requirement) is ever reached, so the first two tests need neither.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_path_inside_the_project_is_rejected(self):
        target = self.root / "project.godot"
        original = target.read_bytes()

        response = call("screenshot_scene", {
            "project_path": str(self.root),
            "scene": "res://main.tscn",
            "out_path": str(target),
        })
        self.assertTrue(response["result"].get("isError"), response["result"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("out_path", text)
        self.assertIn("project directory", text)

        # Decisive, not just "an error came back": the file itself must be
        # byte-for-byte untouched, not silently replaced by PNG bytes.
        self.assertEqual(target.read_bytes(), original)

    def test_path_inside_a_project_subdirectory_is_rejected(self):
        response = call("screenshot_scene", {
            "project_path": str(self.root),
            "scene": "res://main.tscn",
            "out_path": str(self.root / "scripts" / "sneaky.png"),
        })
        self.assertTrue(response["result"].get("isError"), response["result"])
        self.assertFalse((self.root / "scripts" / "sneaky.png").exists())

    def test_symlink_pointing_back_into_the_project_is_rejected(self):
        # A path that is textually outside the project but resolves, via a
        # symlink, back to a file inside it -- the reason the containment
        # check compares os.path.realpath() on both sides rather than the
        # raw strings.
        outside = Path(tempfile.mkdtemp(prefix="godot-shot-outside-link-"))
        try:
            symlink_path = outside / "sneaky_link.godot"
            symlink_path.symlink_to(self.root / "project.godot")
            original = (self.root / "project.godot").read_bytes()

            response = call("screenshot_scene", {
                "project_path": str(self.root),
                "scene": "res://main.tscn",
                "out_path": str(symlink_path),
            })
            self.assertTrue(response["result"].get("isError"), response["result"])
            self.assertEqual((self.root / "project.godot").read_bytes(), original)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    @unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
    def test_path_outside_the_project_still_works(self):
        out_dir = Path(tempfile.mkdtemp(prefix="godot-shot-outside-"))
        try:
            response = call("screenshot_scene", {
                "project_path": str(self.root),
                "scene": "res://main.tscn",
                "out_path": str(out_dir / "scene.png"),
                "width": 64, "height": 64, "frames": 2,
            })
            self.assertFalse(response["result"].get("isError"), response["result"])
            body = json.loads(response["result"]["content"][0]["text"])
            self.assertTrue(os.path.isfile(body["path"]))
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_resolved_out_path_not_the_raw_one_is_passed_to_the_renderer(self):
        # IMPORTANT 1 (fix round 4): round 3 changed the render.screenshot_scene()
        # call to pass resolved_out rather than the raw out_path (closing a
        # second, independent TOCTOU -- render.py re-resolves whatever
        # string it's given against the CWD live at render time). That
        # single-line change had no regression test: the reviewer reverted
        # it, passing out_path instead, and all existing tests -- including
        # test_path_outside_the_project_still_works above -- still passed,
        # because none of them asserted anything about which exact string
        # reaches the renderer, only that the call succeeds. Mocks the
        # renderer and asserts directly on the third positional argument it
        # actually receives, using a symlinked directory so the raw and
        # resolved strings are guaranteed to differ textually while naming
        # the same file.
        real_dir = Path(tempfile.mkdtemp(prefix="godot-shot-real-"))
        link_dir = real_dir.parent / (real_dir.name + "-link")
        link_dir.symlink_to(real_dir)
        try:
            raw_out_path = str(link_dir / "scene.png")
            resolved_out_path = os.path.realpath(raw_out_path)
            self.assertNotEqual(raw_out_path, resolved_out_path)  # sanity: the symlink really changes the string

            with mock.patch.object(
                server.render, "screenshot_scene",
                return_value={
                    "path": resolved_out_path, "diagnostics": [], "timed_out": False, "pixel": (1, 2, 3),
                },
            ) as mocked:
                result = server.dispatch_tool_call("screenshot_scene", {
                    "project_path": str(self.root),
                    "scene": "res://main.tscn",
                    "out_path": raw_out_path,
                })
            self.assertFalse(result.get("isError"), result)
            passed_out_path = mocked.call_args.args[2]
            self.assertEqual(passed_out_path, resolved_out_path)
            self.assertNotEqual(passed_out_path, raw_out_path)
        finally:
            link_dir.unlink()
            shutil.rmtree(real_dir, ignore_errors=True)

    @unittest.skipUnless(FS_IS_CASE_INSENSITIVE, "needs a case-insensitive filesystem to reproduce")
    def test_case_variant_of_project_directory_is_rejected(self):
        # CRITICAL (fix round 2): the string-only check
        # (resolved_out.startswith(project_root + os.sep)) is defeated for
        # free on APFS (case-insensitive but case-preserving, the macOS
        # default): os.path.realpath() does not canonicalise letter case,
        # so an upper-cased ancestor directory name resolves to the exact
        # same on-disk directory without matching as a string. Nothing on
        # disk changes -- no rename, no new file, no symlink -- only the
        # string the caller happens to type.
        upper_root = self.tmp / "PROJ"
        # Sanity check that this environment's filesystem really does fold
        # case the way the test assumes, so a failure here means the test
        # fixture itself is wrong, not the fix under test.
        self.assertTrue(
            os.path.exists(upper_root),
            "case-insensitive fs expected but the upper-cased path does not exist",
        )
        self.assertTrue(os.path.samefile(upper_root, self.root))

        target = upper_root / "project.godot"
        original = (self.root / "project.godot").read_bytes()

        response = call("screenshot_scene", {
            "project_path": str(self.root),
            "scene": "res://main.tscn",
            "out_path": str(target),
        })
        self.assertTrue(response["result"].get("isError"), response["result"])
        self.assertEqual((self.root / "project.godot").read_bytes(), original)

    def test_hardlink_to_a_project_file_is_rejected(self):
        # CRITICAL 2 (fix round 2): a hardlink from outside the project to
        # a file inside it has no distinct path for ANY containment check
        # to resolve -- it IS the same inode under a second name, not a
        # reference to one. Narrower than the case bypass (it needs a
        # hardlink to already exist), but writing through it corrupts the
        # inside file exactly the same way.
        outside = Path(tempfile.mkdtemp(prefix="godot-shot-hardlink-"))
        try:
            hardlink_path = outside / "looks_external.png"
            os.link(str(self.root / "project.godot"), str(hardlink_path))
            self.assertGreater(os.stat(hardlink_path).st_nlink, 1)
            original = (self.root / "project.godot").read_bytes()

            response = call("screenshot_scene", {
                "project_path": str(self.root),
                "scene": "res://main.tscn",
                "out_path": str(hardlink_path),
            })
            self.assertTrue(response["result"].get("isError"), response["result"])
            text = response["result"]["content"][0]["text"]
            self.assertIn("hard link", text)
            self.assertEqual((self.root / "project.godot").read_bytes(), original)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    @unittest.skipUnless(FS_IS_CASE_INSENSITIVE, "needs a case-insensitive filesystem to reproduce")
    def test_directory_appearing_between_check_and_render_is_rejected(self):
        # IMPORTANT 1 (fix round 3): the round-2 fix's OSError fallback
        # re-admitted the case bypass whenever out_path's IMMEDIATE parent
        # directory didn't exist yet, even though a HIGHER, case-fold
        # ancestor did -- the exact hole CRITICAL 1 existed to close.
        # Reproduced by the reviewer end to end: the missing subdirectory
        # materialising between the check and the render let a real Godot
        # process write a real PNG inside the project.
        #
        # Reproduces that exact sequencing deterministically -- no timing,
        # no threading, so not flaky -- by wrapping the real containment
        # check with a side effect that creates the subdirectory
        # immediately after the check runs (whatever verdict it reaches),
        # simulating precisely what the reviewer's race produced by hand:
        # the directory does not exist WHEN THE CHECK RUNS, and does exist
        # by the time render.screenshot_scene() would be called.
        #
        # An earlier version of this test pre-created the subdirectory
        # before calling at all, which turned out not to exercise the bug:
        # with the directory already present, the (even buggy) per-ancestor
        # walk simply reaches an existing, matching ancestor one level up
        # without ever hitting the vulnerable OSError branch, so that
        # version stayed green whether or not the round-3 fix was applied.
        # Caught by running this drill and confirming it went red for a
        # DIFFERENT case (TestOutPathContainmentHandlesMissingAncestorsSafely,
        # which tests the same missing-ancestor shape directly against the
        # helper and does hit the bug) while this one stayed green.
        upper_root = self.tmp / "PROJ"
        self.assertTrue(os.path.samefile(upper_root, self.root))
        subdir = upper_root / "newsubdir"
        target = subdir / "scene.png"
        self.assertFalse(subdir.exists())
        original = (self.root / "project.godot").read_bytes()

        real_check = server._out_path_is_inside_project

        def _check_then_let_the_race_happen(resolved_out, project_root):
            verdict = real_check(resolved_out, project_root)
            os.makedirs(subdir, exist_ok=True)  # what the reviewer's race produced, right after the check
            return verdict

        try:
            with mock.patch.object(
                server, "_out_path_is_inside_project", side_effect=_check_then_let_the_race_happen,
            ):
                result = server.dispatch_tool_call("screenshot_scene", {
                    "project_path": str(self.root),
                    "scene": "res://main.tscn",
                    "out_path": str(target),
                })
            self.assertTrue(result.get("isError"), result)
            text = result["content"][0]["text"]
            # Specifically the containment message, not e.g. a NoDisplay
            # error that would also set isError but for an unrelated
            # reason and would not prove this check actually caught it.
            self.assertIn("out_path", text)
            self.assertIn("project directory", text)
            self.assertFalse(target.exists())
            self.assertEqual((self.root / "project.godot").read_bytes(), original)
        finally:
            shutil.rmtree(subdir, ignore_errors=True)


class TestOutPathContainmentHandlesMissingAncestorsSafely(unittest.TestCase):
    """IMPORTANT 1 (fix round 3), tested directly against the helper --
    fast, precise, and (for the unresolvable-root case) not practically
    reachable through the full server without contriving an already-broken
    project_path.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _inside(self, out_path, project_path=None):
        project_root = os.path.realpath(str(project_path or self.root))
        resolved_out = os.path.realpath(str(out_path))
        return server._out_path_is_inside_project(resolved_out, project_root)

    @unittest.skipUnless(FS_IS_CASE_INSENSITIVE, "needs a case-insensitive filesystem to reproduce")
    def test_missing_ancestor_does_not_mask_a_higher_case_fold_alias(self):
        # The subdirectory is deliberately left NOT created -- this is the
        # exact shape of the round-2 bug (the immediate parent doesn't
        # exist), checked without needing the "race" at all: the fixed
        # helper must find the case-fold alias by walking past the missing
        # level, not by falling back to a string comparison once it hits it.
        upper_root = self.tmp / "PROJ"
        self.assertTrue(os.path.samefile(upper_root, self.root))
        out_path = upper_root / "does-not-exist-yet" / "scene.png"
        self.assertFalse((upper_root / "does-not-exist-yet").exists())
        self.assertTrue(self._inside(out_path))

    def test_unresolvable_project_root_is_treated_as_unsafe(self):
        # If project_root itself cannot be stat'd at all, identity can
        # never be determined for anything under it -- treated as unsafe
        # (True, i.e. "reject") rather than falling through to a string
        # comparison, which is the failure mode this whole function exists
        # to avoid.
        bogus_root = os.path.realpath(str(self.tmp / "does-not-exist-at-all"))
        out_path = self.tmp / "does-not-exist-at-all" / "somewhere" / "scene.png"
        self.assertTrue(self._inside(out_path, project_path=bogus_root))

    def test_unresolvable_project_path_is_reported_as_a_project_path_problem(self):
        # MINOR 2 (fix round 4): _out_path_is_inside_project() itself
        # correctly treats an unverifiable project_root as unsafe (the test
        # above), but at the call_tool() level that shared a message with a
        # genuine containment match -- "out_path must be outside the
        # project directory" -- even though out_path was never the problem
        # here. This is genuinely new as of round 3 (round 2's string
        # fallback would have let a downstream engine error name the real
        # cause instead), and every other tool in this server names
        # project.godot directly when project_path is bad, so this one
        # should too.
        bogus_project = str(Path(tempfile.mkdtemp()) / "does-not-exist-at-all")
        response = call("screenshot_scene", {
            "project_path": bogus_project,
            "scene": "res://main.tscn",
            "out_path": str(self.tmp / "somewhere" / "scene.png"),
        })
        self.assertTrue(response["result"].get("isError"), response["result"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("project_path", text)
        self.assertNotIn("out_path", text)


class TestOutPathContainmentDoesNotOverReject(unittest.TestCase):
    """The reviewer verified these are all correctly ACCEPTED today and
    must stay accepted: an inode-walk implementation is more likely to
    over-reject than a string-prefix one (mishandling a nonexistent
    directory, a symlinked project root, a relative path, ...), so each
    case is checked explicitly against the actual helper the server calls,
    rather than assumed to still work by virtue of the rejection tests
    passing.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _inside(self, out_path, project_path=None):
        project_root = os.path.realpath(str(project_path or self.root))
        resolved_out = os.path.realpath(str(out_path))
        return server._out_path_is_inside_project(resolved_out, project_root)

    def test_sibling_prefixed_directory_is_not_rejected(self):
        # "/tmp/proj" vs "/tmp/proj-backup/x.png" -- a naive prefix check
        # without the separator would over-reject this; the existing
        # `+ os.sep` string fallback already handled it, and the identity
        # walk must not regress it.
        sibling = self.tmp / "proj-backup" / "x.png"
        self.assertFalse(self._inside(sibling))

    def test_trailing_slash_on_project_path_is_not_rejected(self):
        project_with_slash = str(self.root) + os.sep
        self.assertFalse(self._inside(self.tmp / "outside.png", project_path=project_with_slash))
        self.assertTrue(self._inside(self.root / "project.godot", project_path=project_with_slash))

    def test_project_path_as_dot_is_not_rejected(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.root)
            self.assertTrue(self._inside(self.root / "project.godot", project_path="."))
            self.assertFalse(self._inside(self.tmp / "outside.png", project_path="."))
        finally:
            os.chdir(cwd)

    def test_relative_project_path_is_not_rejected(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp)
            self.assertTrue(self._inside(self.root / "project.godot", project_path="proj"))
        finally:
            os.chdir(cwd)

    def test_symlinked_project_path_is_not_rejected(self):
        link = self.tmp / "proj-link"
        link.symlink_to(self.root)
        self.assertTrue(self._inside(self.root / "project.godot", project_path=str(link)))

    def test_relative_out_path_is_not_rejected(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp)
            self.assertFalse(self._inside("outside.png"))
            self.assertTrue(self._inside("proj/project.godot"))
        finally:
            os.chdir(cwd)

    def test_dotdot_normalised_path_landing_outside_is_not_rejected(self):
        out_path = self.root / ".." / "outside.png"
        self.assertFalse(self._inside(out_path))

    def test_nonexistent_out_path_directory_is_not_rejected(self):
        out_path = self.tmp / "does-not-exist-yet" / "scene.png"
        self.assertFalse(self._inside(out_path))

    def test_sibling_prefixed_directory_end_to_end_is_not_rejected(self):
        # The unit-level check above proves the helper's own logic; this
        # confirms the full call_tool() wiring (both checks, in order)
        # agrees, without needing a real Godot render to prove "accepted".
        sibling_out = self.tmp / "proj-backup" / "x.png"
        os.makedirs(sibling_out.parent, exist_ok=True)
        with mock.patch.object(
            server.render, "screenshot_scene",
            return_value={"path": str(sibling_out), "diagnostics": [], "timed_out": False, "pixel": (1, 2, 3)},
        ):
            result = server.dispatch_tool_call("screenshot_scene", {
                "project_path": str(self.root),
                "scene": "res://main.tscn",
                "out_path": str(sibling_out),
            })
        self.assertFalse(result.get("isError"), result)


class TestMalformedArgumentsIsACleanErrorNotATraceback(unittest.TestCase):
    """IMPORTANT (fix round 1): calling a tool with a non-object
    "arguments" (e.g. a bare string) used to reach call_tool()'s
    `args["project_path"]` indexing, raising a raw
    `TypeError: string indices must be integers` -- caught only by the
    generic `except Exception` branch, surfacing a multi-line traceback
    with absolute paths, unlike the four named exceptions' one-sentence
    errors. dispatch_tool_call() now validates the type before ever
    reaching call_tool().
    """

    def test_string_arguments_is_a_clean_error(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "project_overview", "arguments": "not-an-object"}},
        )
        result = responses[-1]["result"]
        self.assertTrue(result.get("isError"))
        text = result["content"][0]["text"]
        self.assertNotIn("Traceback", text)
        self.assertNotIn("string indices", text)

    def test_list_arguments_is_a_clean_error(self):
        result = server.dispatch_tool_call("project_overview", ["not", "a", "dict"])
        self.assertTrue(result.get("isError"))
        text = result["content"][0]["text"]
        self.assertNotIn("Traceback", text)

    def test_missing_arguments_still_defaults_to_empty_object(self):
        # Confirms the fix didn't change behaviour for the common case: no
        # "arguments" key at all (None) is still treated as {}, not rejected.
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "search_classes"}},
        )
        result = responses[-1]["result"]
        # No "query" key in {} -> KeyError inside call_tool(), which is a
        # different (pre-existing, out of scope here) failure mode -- the
        # point of this test is only that it is *not* rejected for having a
        # non-dict "arguments", i.e. it reaches call_tool() at all.
        self.assertTrue(result.get("isError"))
        self.assertNotIn("expected a JSON object", result["content"][0]["text"])


@unittest.skipUnless(HAS_GODOT, "needs a Godot binary to spawn a real child")
class TestSignalHandlingTearsDownInFlightChildren(unittest.TestCase):
    """The server's children run detached into their own process group
    (engine.run uses start_new_session=True). If this server process is
    killed, nothing reaps them by default -- SIGTERM in particular runs no
    Python code at all unless the server installs its own handler. This
    drives the server through a real, long-running headless run_scene call
    and confirms that SIGTERM to the server also takes down the Godot child,
    rather than leaving it running to its own --quit-after.

    IMPORTANT (found via this plan's break-a-test practice, run against this
    exact test): signalling the moment the child's pid appears is NOT a valid
    test of the fix. A freshly launched Godot process spends its first
    couple hundred ms emitting its own startup diagnostics to stderr, a pipe
    this server holds the read end of; killing the server at that instant
    closes that pipe, and the child's own very next startup-log write gets
    SIGPIPE and dies -- with or without this server's own SIGTERM handler
    installed. Measured directly: with the handler deliberately removed,
    signalling immediately still killed the child in ~0.1s (a false pass),
    while signalling two seconds later -- past that startup burst, well
    into the quiet steady-state frame loop that writes nothing -- correctly
    left the child running for the rest of the 10s window. The delay below
    is what makes this test capable of failing at all.
    """

    # Time for Godot's own startup stderr chatter to quiet down before the
    # child reaches its steady frame loop, which writes nothing. Sending the
    # signal inside that startup window can kill the child via an unrelated
    # SIGPIPE (see the class docstring) regardless of whether this server's
    # own signal handling works, making the test pass for the wrong reason.
    _SETTLE_SECONDS = 2

    def _find_child_pid(self, server_pid, deadline):
        while time.monotonic() < deadline:
            try:
                out = subprocess.run(
                    ["pgrep", "-P", str(server_pid)],
                    capture_output=True, text=True, timeout=5,
                )
            except Exception:
                out = None
            if out and out.returncode == 0:
                pids = [int(p) for p in out.stdout.split() if p.strip()]
                if pids:
                    return pids[0]
            time.sleep(0.1)
        return None

    def _still_alive(self, pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def test_sigterm_kills_the_in_flight_godot_child(self):
        proc = subprocess.Popen(
            ["python3", str(SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        child_pid = None
        try:
            proc.stdin.write(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            ) + "\n")
            proc.stdin.flush()
            proc.stdout.readline()  # initialize response

            # A frame count large enough that the child is still running well
            # after we detect and kill it -- not so large the test is slow.
            proc.stdin.write(json.dumps(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "run_scene",
                            "arguments": {"project_path": str(SAMPLE), "frames": 100000}}}
            ) + "\n")
            proc.stdin.flush()

            child_pid = self._find_child_pid(proc.pid, time.monotonic() + 10)
            self.assertIsNotNone(child_pid, "Godot child never appeared")
            self.assertTrue(self._still_alive(child_pid))

            # See the class docstring: signalling immediately risks a false
            # pass via SIGPIPE from Godot's own startup logging, not this
            # server's signal handling.
            time.sleep(self._SETTLE_SECONDS)
            self.assertTrue(
                self._still_alive(child_pid), "Godot child exited on its own before "
                "the signal was even sent -- the test fixture itself is broken."
            )

            proc.send_signal(signal.SIGTERM)

            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and self._still_alive(child_pid):
                time.sleep(0.1)

            self.assertFalse(
                self._still_alive(child_pid),
                "Godot child survived the server's SIGTERM -- orphaned, still running "
                "toward its own --quit-after.",
            )
        finally:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                if pipe is not None:
                    pipe.close()
            if child_pid is not None and self._still_alive(child_pid):
                try:
                    os.killpg(child_pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass


class TestBadInputPathIsNeverAConfidentAnswer(unittest.TestCase):
    """Final whole-branch review, IMPORTANT 4.

    Nine tools had four conventions for one user error (a typo'd or stale
    path): two raw tracebacks, three confident CLEAN-or-EMPTY answers, one
    correct message. The clean answers are the dangerous ones -- an agent
    asking "does this project have broken references?" about a mistyped path
    was told broken: [], orphans: [], parse_errors: [] with no error flag,
    which is indistinguishable from a healthy project.
    """

    def setUp(self):
        self.missing = os.path.join(
            tempfile.mkdtemp(prefix="godot-nonproject-"), "not-a-project"
        )

    def test_every_project_path_tool_rejects_a_nonexistent_project(self):
        for tool, extra in [
            ("project_overview", {}),
            ("reference_graph", {}),
            ("check_script", {"script_path": "a.gd"}),
            ("run_scene", {}),
            ("check_shader", {"shader_path": "res://a.gdshader"}),
            ("screenshot_scene", {"scene": "res://a.tscn"}),
        ]:
            with self.subTest(tool=tool):
                args = {"project_path": self.missing, **extra}
                with self.assertRaises(server.BadInputPath) as caught:
                    server.call_tool(tool, args)
                self.assertIn("is not a Godot project", str(caught.exception))

    def test_a_real_project_is_not_rejected(self):
        # The over-blocking direction: the pre-check must not reject the
        # fixture project, or it has traded a wrong answer for no answer.
        server._require_project({"project_path": str(SAMPLE)})

    def test_scene_tree_rejects_a_missing_scene_file(self):
        with self.assertRaises(server.BadInputPath) as caught:
            server.call_tool("scene_tree", {"scene_path": self.missing + ".tscn"})
        self.assertIn("does not name a readable file", str(caught.exception))

    def test_dispatch_reports_it_as_an_error_not_a_traceback(self):
        result = server.dispatch_tool_call(
            "reference_graph", {"project_path": self.missing}
        )
        self.assertTrue(result.get("isError"))
        text = result["content"][0]["text"]
        self.assertIn("is not a Godot project", text)
        self.assertNotIn("Traceback", text)


class TestCheckScriptTimeoutIsNotAVerdict(unittest.TestCase):
    """Final whole-branch review, IMPORTANT 1.

    run() SIGKILLs a hung engine, which then prints nothing -- so a timeout
    produced exactly the empty stderr a clean script produces, and the server
    rendered it as "the script parses and type-checks." This is the same
    defect Task 7 fixed for check_shader; the fix was applied to that one call
    site and never generalised to its sibling.
    """

    def test_timed_out_check_raises_rather_than_reporting_clean(self):
        timed_out = engine.Result(stdout="", stderr="", returncode=-9, timed_out=True)
        with mock.patch.object(engine, "run", return_value=timed_out):
            with self.assertRaises(engine.ScriptCheckTimedOut) as caught:
                engine.check_script(str(SAMPLE), "a.gd")
        self.assertIn("not a verdict", str(caught.exception))

    def test_a_clean_result_still_reports_clean(self):
        clean = engine.Result(stdout="", stderr="", returncode=0, timed_out=False)
        with mock.patch.object(engine, "run", return_value=clean):
            self.assertEqual(engine.check_script(str(SAMPLE), "a.gd"), [])

    def test_the_server_surfaces_it_as_an_error(self):
        timed_out = engine.Result(stdout="", stderr="", returncode=-9, timed_out=True)
        with mock.patch.object(engine, "run", return_value=timed_out):
            result = server.dispatch_tool_call(
                "check_script",
                {"project_path": str(SAMPLE), "script_path": "scripts/player.gd"},
            )
        self.assertTrue(result.get("isError"))
        self.assertNotIn("parses and type-checks", result["content"][0]["text"])


class TestLookupClassAlwaysReturnsValidJson(unittest.TestCase):
    """Final whole-branch review, MINOR 3 (raised: 25 of 1,036 classes hit it).

    `json.dumps(found, indent=2)[:60000]` cut mid-token, so the agent received
    text that announces itself as JSON and does not parse. The classes past
    the cut are the ones most worth looking up -- Node, Control, CanvasItem,
    Window, TextEdit, RenderingServer.
    """

    def test_oversized_class_is_trimmed_by_members_and_still_parses(self):
        big = {
            "name": "Huge",
            "methods": [{"name": f"m{i}", "description": "x" * 400} for i in range(400)],
            "properties": [{"name": f"p{i}", "description": "y" * 400} for i in range(400)],
        }
        self.assertGreater(len(json.dumps(big, indent=2)), server.LOOKUP_BUDGET)
        text = json.dumps(server._fit_class(big), indent=2)
        self.assertLessEqual(len(text), server.LOOKUP_BUDGET)
        parsed = json.loads(text)  # the whole point: it must parse
        self.assertEqual(parsed["name"], "Huge")
        marker = parsed["methods"][-1]
        self.assertIsInstance(marker, str)
        self.assertIn("more methods omitted", marker)
        self.assertIn("400 in total", marker)

    def test_a_small_class_is_returned_untouched(self):
        small = {"name": "Tiny", "methods": [{"name": "a"}], "properties": []}
        self.assertEqual(server._fit_class(small), small)


if __name__ == "__main__":
    unittest.main()
