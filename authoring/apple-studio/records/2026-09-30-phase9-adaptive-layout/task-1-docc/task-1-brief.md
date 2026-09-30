### Task 1: `docc.py` renders inline markup, deprecation, and HIG pages

**Files:**
- Modify: `$AS/pipeline/docc.py` (render, fetch, main; add `__main__` guard)
- Create: `$AS/pipeline/fixtures/docc/inline-markup.json`
- Create: `$AS/pipeline/test_docc.py`

**Interfaces:**
- Produces: `fetch(path, kind="doc")` with `kind` in `{"doc", "tutorial", "hig"}`; `render(o, acc, refs)` unchanged in signature; CLI flag `--hig <slug>`; a `DEPRECATED:` output line. Tasks 4 and 8 use `--hig designing-for-iphone-duo`.

- [ ] **Step 1: Write the fixture.** Our own words, not Apple's. Create `$AS/pipeline/fixtures/docc/inline-markup.json`:

```json
{
  "metadata": {"title": "Fixture page", "platforms": [{"name": "iOS", "introducedAt": "13.0", "deprecatedAt": "27.2", "deprecated": false}]},
  "deprecationSummary": [{"type": "paragraph", "inlineContent": [{"type": "text", "text": "Use the replacement instead."}]}],
  "abstract": [{"type": "text", "text": "A fixture."}],
  "references": {"doc://x/Target": {"title": "TargetSymbol", "url": "/documentation/x/target"}},
  "primaryContentSections": [{"kind": "content", "content": [
    {"type": "paragraph", "inlineContent": [
      {"type": "text", "text": "A container called an "},
      {"type": "newTerm", "inlineContent": [{"type": "text", "text": "arrangement view"}]},
      {"type": "text", "text": " holds two views."}
    ]},
    {"type": "unorderedList", "items": [
      {"content": [{"type": "paragraph", "inlineContent": [
        {"type": "emphasis", "inlineContent": [{"type": "text", "text": "The fold."}]},
        {"type": "text", "text": " Present when partly open."}
      ]}]}
    ]},
    {"type": "paragraph", "inlineContent": [
      {"type": "strong", "inlineContent": [
        {"type": "text", "text": "See "},
        {"type": "reference", "identifier": "doc://x/Target"}
      ]}
    ]},
    {"type": "aside", "style": "note", "name": "Note", "content": [
      {"type": "paragraph", "inlineContent": [{"type": "text", "text": "Aside body text."}]}
    ]}
  ]}]
}
```

- [ ] **Step 2: Write the failing test.** Create `$AS/pipeline/test_docc.py`:

```python
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
```

- [ ] **Step 3: Run it to verify it fails.** `python3 $AS/pipeline/test_docc.py`. Expected: it runs `main()` on import (argv empty, prints nothing), then fails with `AttributeError: module 'docc' has no attribute 'print_page'`.

- [ ] **Step 4: Implement.** In `$AS/pipeline/docc.py`:

  1. Replace the two base constants and `fetch` with:

```python
BASES = {
    "doc": "https://developer.apple.com/tutorials/data/documentation/",
    "tutorial": "https://developer.apple.com/tutorials/data/tutorials/",
    # Added Phase 9: HIG pages are DocC JSON too, under design/, which the
    # documentation/ and tutorials/ prefixes cannot reach.
    "hig": "https://developer.apple.com/tutorials/data/design/human-interface-guidelines/",
}

def url_for(path, kind="doc"):
    return BASES[kind] + path + ".json"

def fetch(path, kind="doc"):
    url = url_for(path, kind)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r), url
```

  2. In `render`, add these branches before the `elif t == "paragraph":` branch:

```python
        elif t in ("emphasis", "strong", "newTerm"):
            # Phase 9: these carry inlineContent, which the generic walk below
            # skips. Dropping it turned every defined term into a gap.
            mark = "**" if t == "strong" else "*"
            acc.append(mark); render(o.get("inlineContent", []), acc, refs); acc.append(mark)
            return
        elif t == "aside":
            acc.append("\n> **" + (o.get("name") or o.get("style", "note")) + ":** ")
            render(o.get("content", []), acc, refs)
            return
        elif t == "table":
            for row in o.get("rows", []):
                acc.append("\n| ")
                for cell in row:
                    render(cell, acc, refs); acc.append(" | ")
            acc.append("\n")
            return
```

  3. Split the per-page printing out of `main` into `print_page(d, url, children=False)`. It prints exactly what `main` prints today (title, SOURCE, PLATFORMS, ABSTRACT, body, topic sections when `children`), plus, after PLATFORMS:

```python
        dep = [f"{p.get('name')} {p['deprecatedAt']}" for p in pl if p.get("deprecatedAt")]
        if dep:
            summary = []
            render(d.get("deprecationSummary", []), summary, d.get("references", {}))
            print("DEPRECATED: " + ", ".join(dep) + " — " + "".join(summary).strip())
```

  4. `main` parses `--children`, `--tutorial`, and `--hig`, picks `kind` (`"hig"` if `--hig`, `"tutorial"` if `--tutorial`, else `"doc"`), calls `fetch(path, kind)`, then `print_page(d, url, children)`.
  5. Replace the bare `main()` at the end of the file with `if __name__ == "__main__":\n    main()`.
  6. Add `--hig <slug>` to the module docstring's Usage block.

- [ ] **Step 5: Run the test to verify it passes.** `python3 $AS/pipeline/test_docc.py`. Expected: `PASS test_docc.py`.

- [ ] **Step 6: Check the live pages.** Run:

```bash
python3 $AS/pipeline/docc.py --hig designing-for-iphone-duo | grep -c "reserved regions"
python3 $AS/pipeline/docc.py technologyoverviews/preparing-your-app-for-iphone-duo | grep -o "represent an [^,]*,"
python3 $AS/pipeline/docc.py "swiftui/view/accentcolor(_:)" | grep DEPRECATED
```

Expected: a count ≥ 1; `represent an *arrangement view*,`; a line starting `DEPRECATED: iOS 27.2`. Save the three outputs to `task-1-docc/live-check.log`.

- [ ] **Step 7: Commit.**

```bash
git add $AS/pipeline/docc.py $AS/pipeline/test_docc.py $AS/pipeline/fixtures/docc $AS/records/2026-09-30-phase9-adaptive-layout/task-1-docc
git commit -m "Phase 9 Task 1: docc.py keeps defined terms, prints deprecation, reaches the HIG

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

