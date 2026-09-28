"""Structural invariants of the godot package.

These assert properties the rest of the suite relies on but never checks,
because each one holds by the ABSENCE of something -- an import that isn't
there, a file handle that isn't left open. A property enforced only by absence
regresses silently: nothing fails when someone adds the thing back.
"""

import ast
import os
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "godot"
SERVER = Path(__file__).resolve().parents[1] / "godot_mcp_server.py"

# Spec decision 16: "project_overview, scene_tree, and reference_graph are pure
# parsers requiring no Godot binary. This is a tested property, not an
# accident." It was NOT tested before this file existed -- the three suites
# simply never called the binary, which is a different thing. Godot is on PATH
# on every machine that develops this plugin, so adding an engine call to
# overview() would have kept every test green and broken only for the users
# decision 16 exists to protect: the ones with no engine installed.
PURE_MODULES = ["project.py", "refs.py", "tscn.py"]
ENGINE_MODULES = {"engine", "api", "render"}


def _imported_names(path: Path) -> set:
    """Every segment of every imported name.

    Collecting only `split(".")[0]` was a real hole: for `from . import engine`
    the head IS "engine" and the check worked, but for the absolute spellings
    `import godot.engine` and `from godot.engine import run` the head is
    "godot", so the engine module was reachable with the test still green.
    Recording every segment covers relative and absolute spellings alike.
    """
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.update(node.module.split("."))
            for alias in node.names:
                names.update(alias.name.split("."))
    return names


class TestPureParsersNeverReachTheEngine(unittest.TestCase):
    def test_no_pure_module_imports_an_engine_module(self):
        offenders = []
        for name in PURE_MODULES:
            reached = _imported_names(PKG / name) & ENGINE_MODULES
            if reached:
                offenders.append(f"{name} imports {sorted(reached)}")
        self.assertEqual(
            offenders,
            [],
            "A pure parser reached an engine module. project_overview, "
            "scene_tree and reference_graph must work with no Godot binary "
            "installed (spec decision 16).",
        )

    def test_no_pure_module_can_spawn_a_process_at_all(self):
        """Decision 16's actual words are "requiring no Godot binary", which is
        a stronger claim than "imports no engine module". A direct
        `subprocess.run(["godot", "--version"])` inside overview() violates the
        property while importing nothing the closure test looks for, so the
        spawning primitives are banned outright from the pure parsers.
        """
        banned = {"subprocess", "multiprocessing", "popen2", "commands"}
        offenders = []
        for name in PURE_MODULES:
            source = (PKG / name).read_text()
            reached = _imported_names(PKG / name) & banned
            if reached:
                offenders.append(f"{name} imports {sorted(reached)}")
            for call in ("os.system(", "os.popen(", "os.spawn", "os.exec"):
                if call in source:
                    offenders.append(f"{name} calls {call}")
        self.assertEqual(
            offenders,
            [],
            "A pure parser can spawn a process. Decision 16 promises these "
            "three tools need no Godot binary, which bans spawning it "
            "directly, not merely importing the module that would.",
        )

    def test_the_transitive_closure_is_clean_too(self):
        # refs imports project and tscn; a violation one level down is just as
        # fatal to the property and just as invisible on a machine with Godot.
        seen, stack, offenders = set(), list(PURE_MODULES), []
        while stack:
            name = stack.pop()
            if name in seen:
                continue
            seen.add(name)
            reached = _imported_names(PKG / name)
            if reached & ENGINE_MODULES:
                offenders.append(f"{name} -> {sorted(reached & ENGINE_MODULES)}")
            for dep in reached:
                if (PKG / f"{dep}.py").exists():
                    stack.append(f"{dep}.py")
        self.assertEqual(offenders, [])


class TestNoLeakedFileHandles(unittest.TestCase):
    """Every read goes through a context manager.

    Deferred three times across Tasks 3 and 4 as trivial in isolation, which it
    was each time; the suite printed ResourceWarning on every run regardless.
    Harmless under CPython refcounting and not harmless under anything else.
    """

    def test_every_open_is_bound_by_a_with(self):
        """Assert on the `open` CALL, not on one spelling of its use.

        Matching `open(...).read()` as a single chained expression pinned one
        spelling and missed the property. All of these leak the identical
        handle and kept that version green:

            _f = open(p); parse_cfg(_f.read())     # measurably ResourceWarns
            list(open(p))
            io.open(p).read()
            open(p).readline()

        Every legitimate read in this package is `with open(...) as f`, so the
        rule is simply: an `open` call must be a `with` item's context
        expression. Nothing here needs an exception.
        """
        offenders = []
        targets = [PKG / n for n in os.listdir(PKG) if n.endswith(".py")]
        targets.append(SERVER)
        hooks = SERVER.parents[2] / "hooks" / "scripts"
        if hooks.is_dir():
            targets += [hooks / n for n in os.listdir(hooks) if n.endswith(".py")]

        def is_open(call):
            func = call.func
            if isinstance(func, ast.Name):
                return func.id == "open"
            return isinstance(func, ast.Attribute) and func.attr == "open"

        for path in targets:
            tree = ast.parse(path.read_text())
            managed = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.With, ast.AsyncWith)):
                    for item in node.items:
                        managed.add(id(item.context_expr))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and is_open(node) and id(node) not in managed:
                    offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(
            offenders,
            [],
            "An open() outside a `with` leaks the handle under any "
            "implementation that does not refcount. Use `with open(...) as f`.",
        )


if __name__ == "__main__":
    unittest.main()
