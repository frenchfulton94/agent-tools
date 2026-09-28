"""One place that decides whether engine-invoking tests run.

The suite splits in two. `bun test` — the catalog's fast gate — runs the
parsers, the guard, the server's wiring and the hook's logic, plus a single
real engine invocation as a smoke check. Everything that actually drives Godot
runs separately, via `bun run test:engine`.

**The split is by marker, not by file.** `test_server.py` holds 47 tests of
which 8 need the engine, and `test_api.py` holds 25 of which one does. Moving
whole files would either drop real coverage from the fast gate or leave it
slow, so each test declares its own requirement and the gate below decides.

**Why an environment variable and not "is Godot installed".** Each of the five
suites used to compute its own `HAS_GODOT = engine.find_binary() is not None`,
which looks like an off-switch and is not one: `find_binary()` falls back to
`/Applications/Godot.app/Contents/MacOS/Godot`, so on a normal macOS dev
machine it is true even with `godot` off `PATH`. Measured — the full 203 ran
with a stripped `PATH`, nothing skipped. A deliberate flag is the only honest
way to ask for the fast subset.

The default is engine tests ON. Running `python3 -m unittest discover` by hand
gets the whole suite, and only the caller that explicitly wants speed opts out,
so forgetting the flag costs time rather than coverage.
"""

import os
import sys
import unittest
from pathlib import Path

# Self-sufficient rather than relying on whichever test module imported this
# one having already done it: discovery order is not something this module
# should depend on.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from godot import engine, render  # noqa: E402


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


SKIP_ENGINE = _flag("GODOT_SKIP_ENGINE_TESTS")

# A binary exists at all. Not an off-switch (see the module docstring) — this
# only distinguishes a machine with no Godot from one that has it.
HAS_BINARY = engine.find_binary() is not None

ENGINE_TESTS_ENABLED = HAS_BINARY and not SKIP_ENGINE

# `and` short-circuits deliberately: render.has_display() shells out to
# launchctl, and the fast gate must not pay for a probe whose answer it will
# not use.
DISPLAY_TESTS_ENABLED = ENGINE_TESTS_ENABLED and render.has_display()

_WHY = (
    "engine tests are off: no Godot binary"
    if not HAS_BINARY
    else "engine tests are off: GODOT_SKIP_ENGINE_TESTS is set "
    "(run `bun run test:engine` for these)"
)

#: Needs to drive the Godot binary. Skipped in the fast gate.
requires_engine = unittest.skipUnless(ENGINE_TESTS_ENABLED, _WHY)

#: Needs the binary AND a real rendering device (headless renders nothing —
#: spec 3.2), so it cannot run on a headless CI box at all.
requires_display = unittest.skipUnless(
    DISPLAY_TESTS_ENABLED,
    _WHY if not ENGINE_TESTS_ENABLED else "needs a display; headless renders nothing",
)

#: The exception: runs whenever a binary exists, INCLUDING in the fast gate.
#: Reserved for the one smoke invocation that proves the engine path is still
#: wired up, so `bun test` cannot go green on a server that can no longer talk
#: to Godot at all. Keep this to a single fast invocation.
engine_smoke = unittest.skipUnless(HAS_BINARY, "no Godot binary")
