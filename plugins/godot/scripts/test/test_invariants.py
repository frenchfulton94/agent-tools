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
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
            for alias in node.names:
                names.add(alias.name.split(".")[0])
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

    def test_no_bare_open_read_in_the_package(self):
        offenders = []
        targets = [PKG / n for n in os.listdir(PKG) if n.endswith(".py")]
        targets.append(SERVER)
        for path in targets:
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                # open(...) used as a plain expression -- i.e. not bound by a
                # `with`, whose context expression is a separate node type.
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in ("read", "readlines"):
                    inner = func.value
                    if isinstance(inner, ast.Call) and getattr(inner.func, "id", "") == "open":
                        offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(
            offenders,
            [],
            "open(...).read() leaks the handle; use `with open(...) as f`.",
        )


if __name__ == "__main__":
    unittest.main()
