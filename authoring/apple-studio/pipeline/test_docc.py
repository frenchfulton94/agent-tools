#!/usr/bin/env python3
"""Offline test for docc.py rendering. Standard library only.

Phase 9 found docc.py dropped the text of emphasis, strong, and new-term nodes,
so a defined term rendered as a gap ("represent an , which is"). This pins it.
"""
import importlib.util
import io
import json
import pathlib
import contextlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("docc", HERE / "docc.py")
docc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docc)  # must not run main() on import

page = json.loads((HERE / "fixtures/docc/inline-markup.json").read_text())
out = io.StringIO()
with contextlib.redirect_stdout(out):
    docc.print_page(page, "fixture://inline-markup")
text = out.getvalue()

failures = []
for needle in ["arrangement view", "The fold.", "Present when partly open.",
               "TargetSymbol", "Aside body text.", "DEPRECATED:", "27.2",
               "Use the replacement instead."]:
    if needle not in text:
        failures.append(f"missing {needle!r}")
if "an , which" in text or "an  holds" in text:
    failures.append("defined term rendered as a gap")
if docc.url_for("designing-for-iphone-duo", "hig") != \
        "https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-iphone-duo.json":
    failures.append("hig url wrong")

if failures:
    print("FAIL\n  " + "\n  ".join(failures) + "\n--- rendered ---\n" + text)
    sys.exit(1)
print("PASS test_docc.py")
