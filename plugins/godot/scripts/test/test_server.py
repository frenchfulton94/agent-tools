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
    """

    @unittest.skipUnless(HAS_GODOT, "needs a Godot binary to generate the dump")
    def test_lookup_class_does_not_leak_the_search_index(self):
        response = call("lookup_class", {"name": "Node"})
        text = response["result"]["content"][0]["text"]
        self.assertNotIn("__api_search_index__", text)

    @unittest.skipUnless(HAS_GODOT, "needs a Godot binary to generate the dump")
    def test_search_classes_does_not_leak_the_search_index(self):
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
        # not see it): a timeout must come back as isError, and its text
        # must not be the "compiled with no errors" message.
        with mock.patch.object(
            server.render, "check_shader",
            side_effect=render.ShaderCheckTimedOut("check_shader timed out after 1s"),
        ):
            result = server.dispatch_tool_call("check_shader", {
                "project_path": str(SAMPLE), "shader_path": "res://good.gdshader",
            })
        self.assertTrue(result.get("isError"))
        text = result["content"][0]["text"]
        self.assertIn("timed out", text)
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


if __name__ == "__main__":
    unittest.main()
