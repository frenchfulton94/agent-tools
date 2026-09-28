# GUT and gdUnit4

Everything in this file is **distilled from each framework's own
documentation**, not measured against this plugin's engine the way
`verify-loop.md` and SKILL.md's opening sections are — neither framework is
installed in this repository's fixtures, and both are third-party addons
this plugin never assumes present. Verify version-specific command syntax
against the addon actually installed in a given project before relying on
it; both frameworks evolve their CLI runners across versions.

Reach for either only once the zero-install baseline (`check_script` plus
`run_scene`, see SKILL.md) can't answer the question — a missing assertion
framework, a need to run many small isolated cases with setup/teardown, or a
project that already has one installed.

## Contents

- [GUT](#gut)
- [gdUnit4](#gdunit4)
- [Choosing between them](#choosing-between-them)

## GUT

GUT ("Godot Unit Test") is the older, more established of the two, with the
longest track record across both Godot 3 and 4.

**Installing:** via the AssetLib tab in the editor (search "Gut"), or by
cloning `https://github.com/bitwes/Gut` into `addons/gut` directly. Either
way, enable it under **Project Settings → Plugins** afterward.

**Writing a first test:** a test script extends `GutTest` and lives under a
test directory (`test/` or `res://test/` by convention, configurable). Test
methods are named `test_*`:

```gdscript
extends GutTest

func test_addition():
	assert_eq(2 + 2, 4, "sanity check")

func test_signal_was_emitted():
	var obj = SomeNode.new()
	watch_signals(obj)
	obj.do_the_thing()
	assert_signal_emitted(obj, "the_thing_happened")
```

GUT ships `assert_eq`/`assert_ne`/`assert_true`/`assert_false`, signal
assertions (`watch_signals` + `assert_signal_emitted`), and doubling/stubbing
support for isolating a unit from its collaborators.

**Running headless (CI):** the bundled `gut_cmdln.gd` script runs from the
command line without opening the editor:

```
godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit
```

`-gexit` quits and returns a non-zero exit code on any test failure — unlike
`--check-only`, GUT's own runner is designed to have its exit code trusted;
it isn't reusing the trap this skill's opening section warns about, because
it isn't relying on the *engine's* check-only path, it's a script deciding
its own exit code based on which of its own assertions failed.

## gdUnit4

gdUnit4 is the newer of the two, built specifically for Godot 4, with an
editor-integrated test explorer panel, IDE integrations (VS Code, JetBrains
via a plugin), parameterized tests, and fuzzing support.

**Installing:** via AssetLib, or cloning
`https://github.com/MikeSchulze/gdUnit4` into `addons/gdUnit4`, then
enabling it under **Project Settings → Plugins**.

**Writing a first test:** a test suite extends `GdUnitTestSuite`:

```gdscript
extends GdUnitTestSuite

func test_addition():
	assert_int(2 + 2).is_equal(4)

func test_array_contains():
	assert_array([1, 2, 3]).contains([2])
```

Assertions are fluent (`assert_int(...).is_equal(...)`,
`assert_str(...).contains(...)`), typed per value kind rather than one
generic `assert_eq`.

**Running headless (CI):** gdUnit4 ships its own wrapper scripts
(`addons/gdUnit4/runtest.sh` on Linux/macOS, `runtest.cmd` on Windows) that
locate the project's Godot binary and drive a headless run, typically
invoked as:

```
addons/gdUnit4/runtest.sh -a res://test
```

and can emit a JUnit XML report for CI test-result integration — check the
version actually installed for the exact flag, since this has changed
across gdUnit4 releases.

## Choosing between them

Both cover the same core need — isolated test cases with setup/teardown and
an assertion library — and either is a reasonable default if a project has
neither yet. Lean toward:

- **GUT** for the simpler mental model, the longer history (more existing
  examples and Stack Overflow answers to draw on), and projects that might
  still need to run on Godot 3.
- **gdUnit4** for built-in editor tooling (a test explorer panel, inline
  pass/fail markers), parameterized/data-driven tests without writing your
  own loop, and CI pipelines that want a structured report format
  out of the box.

Neither is a prerequisite for the ladder in `verify-loop.md` — both operate
one layer above it, for hand-written assertions about specific behavior,
where `check_script`/`run_scene` only tell you the code parses and doesn't
crash.
