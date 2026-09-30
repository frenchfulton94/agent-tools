# apple-studio Phase 9: Adaptive Layout and iPhone Duo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`, one concept-named reference that teaches layout surviving any size, shape, or pose, with iPhone Duo as its most demanding case; fix the two pipeline gaps the survey found; verify every API claim by compiling against the iOS 27.1 SDK and four behavioral claims on the Duo simulator. Version bump to 0.10.0.

**Architecture:** One new reference in the existing `apple-design` skill; no new skill, no agent. Two pipeline scripts gain what this phase needs: `docc.py` stops dropping defined terms and learns HIG pages; `typecheck_snippets.py` learns a per-file iOS target. The eval fixture gains one real screen so `apple-design`'s trigger evals mean something, and the description changes only if that baseline shows a gap.

**Tech Stack:** Python 3 standard library (pipeline scripts), bash (self-tests), SwiftUI / Swift 6, `swiftc -typecheck`, `xcodebuild`, `xcrun simctl`, Xcode 27.1 beta with `iPhoneOS27.1.sdk`, `claude` CLI (trigger evals), `bun` (catalog gates), Vale (prose check).

**Spec:** `authoring/apple-studio/docs/specs/2026-09-30-phase9-adaptive-layout-design.md`

## Global Constraints

- Repo: `~/Projects/agent-tools`, branch `phase9-adaptive-layout`, spec committed at `ea4995c`. Paths are relative to the repo root unless absolute. `AS=authoring/apple-studio` below.
- Phase record: `$AS/records/2026-09-30-phase9-adaptive-layout/`. Every task writes its logs to `task-N-<slug>/` there. Never under `.superpowers/` (CONVENTIONS.md § Verification records).
- **Never commit Apple's text verbatim.** Rendered doc pages stay in the session scratchpad. References are distilled guidance in our own words (CONVENTIONS.md § Reference files).
- **Compilation is the ship gate for every API-specific claim.** A 200 on a doc page is not evidence a symbol exists.
- **27.1 SDK dependency.** Tasks 7 and 8 need Xcode 27.1 beta installed at `/Applications/Xcode-beta.app` with `xcode-select` pointing at it. The user installs it; no task automates it. Tasks 0–6 and 9 do not need it.
- Every commit that touches `plugins/` runs, and must pass: `bun test`, `bun run audit`, `claude plugin validate . --strict`.
- Version lives only in `plugins/apple-studio/.claude-plugin/plugin.json`. Bump to 0.10.0 in Task 9 only. Tag `apple-studio-v0.10.0`, never a bare version.
- Eval harness rules (`.claude/rules/eval-harness.md`), binding: run sweeps through `$AS/pipeline/run_evals.py`; no "build X" phrasing in prompts; a failure is a harness defect until proven otherwise.
- `~/Projects/StudioFixture` MUST have an empty `git status --porcelain` at the close of every task. Only Task 6 commits to it.
- **Leave no simulator booted.** `xcrun simctl list devices booted` prints no device at every task close.
- Out of scope, from the spec: a camera primer; iPad and visionOS rewrites; the 17 deferred-item-7 failures outside `apple-design`; any device-named skill or reference.
- Typecheck baseline measured 2026-09-30: `apple-design` 2/4 (`$AS/records/2026-09-30-phase9-adaptive-layout/survey/typecheck-apple-design-baseline.log:337`). A red file this phase does not touch is not this phase's problem.
- **Deviation from the spec, decided in planning.** The spec asks for preamble bindings for `GeometryProxy` and `UIView` fragments. Only `proxy: GeometryProxy` is added: the name `view` is already bound to a stub class that existing snippets depend on, and rebinding it would break them. UIKit names are verified by header search instead (Task 7, Step 4), and the reference ships no UIKit snippets. Task 9's spec append records this.
- Prose added to specs, `deferred.md`, and references: Controlled Engineering English (spec register for specs and deferred items, R1-E for references); run `vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini <file>`. The "amend" warning is waived (spec § Waiver). This plan itself follows the writing-plans template instead; its `Modify:` labels and long step sentences are not in scope for the check.

## Review Focus

1. **A reference with no `typecheck:` directive** — must compile exactly as today (macOS target). A regression here silently changes every other skill's gate. Pinned in Task 2, Step 7 (whole-catalog TOTAL before and after).
2. **A malformed directive, or a directive newer than the installed SDK** — must stop with exit 2 and a message naming the problem, never fall back to macOS or report 40 "cannot find" errors. Pinned in Task 2, Steps 1–2 (`bad-directive.md`, `too-new.md`).
3. **Nested inline markup and deprecated symbols in DocC JSON** — emphasis inside a list item, a reference inside emphasis, a symbol with `deprecatedAt` — must keep every word and print the deprecation. Pinned in Task 1, Step 1.
4. **Right-to-left layouts** — vertical bars stay on the hardware side in RTL, and reserved-region frames are in a fixed coordinate space. The reference must state both. Pinned in Task 4, Step 9 (grep check).
5. **The fixture screen on its other platforms** — StudioFixture also targets macOS and visionOS, and the new screen must still build there. Pinned in Task 6, Step 3 (macOS build).

---

### Task 0: Opening sweep and charter amendment

**Files:**
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`
- Modify: `$AS/docs/deferred.md` (item 1: append the Phase 9 measurement)
- Modify: `$AS/docs/specs/2026-08-03-apple-studio-design.md:193` (insert the amendment after the Phase 7 block)

**Interfaces:**
- Consumes: `deferred.md` item 1's scan method (Phase 6 and Phase 7 paragraphs).
- Produces: the measurement Task 9's spec append cites; the charter text Task 9 does not repeat.

- [ ] **Step 1: Confirm the branch.** Run `git branch --show-current` → expect `phase9-adaptive-layout`. Run `git merge-base --is-ancestor ea4995c HEAD; echo $?` → expect `0`.

- [ ] **Step 2: Write the scan script.** Create `task-0-sweep/killswitch_scan.py`:

```python
#!/usr/bin/env python3
"""Phase 9 kill-switch scan: apple-studio:* Skill invocations since a date.

Method unchanged from deferred.md item 1 (Phase 6, Phase 7): JSON-parse every
Skill tool_use block and read input.skill. Fixture and authoring sessions are
excluded; they are the plugin's own verification, not real use.
"""
import json
import pathlib
import sys
from collections import Counter

since = sys.argv[1]  # e.g. "2026-09-12"
root = pathlib.Path.home() / ".claude" / "projects"
EXCLUDE = ("-scratchpad-", "-private-tmp-", "StudioFixture", "agent-tools", "apple-studio")

genuine = set()
excluded = Counter()
files = 0
for f in root.rglob("*.jsonl"):
    files += 1
    project = f.relative_to(root).parts[0]
    for line in f.open(errors="ignore"):
        if '"Skill"' not in line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        ts = rec.get("timestamp", "")
        if ts[:10] < since:
            continue
        content = (rec.get("message") or {}).get("content") or []
        for block in content if isinstance(content, list) else []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill"):
                continue
            skill = (block.get("input") or {}).get("skill", "")
            if not skill.startswith("apple-studio:"):
                continue
            if any(x in project for x in EXCLUDE):
                excluded[project] += 1
            else:
                genuine.add((f.stem, skill, ts[:10], project))

print(f"transcripts scanned: {files}")
print(f"excluded invocations by project: {dict(excluded)}")
print(f"genuine non-fixture invocations since {since}: {len(genuine)}")
for g in sorted(genuine):
    print("  ", g)
```

- [ ] **Step 3: Run it.** `python3 $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py 2026-09-12 | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`. Expected: a `genuine non-fixture invocations` line with a count.

- [ ] **Step 4: Apply the pre-taken decision rule; do not improvise.** Item 1 says the skill gate fires only "at the opening sweep of the first phase following a shipped real feature". No real feature has shipped through this plugin, so no skill is cut whatever the count. Append to item 1 a paragraph headed `**Phase 9 measurement (2026-09-30).**` stating: the scan window (since 2026-09-12), transcripts scanned, the genuine count, the excluded counts by project, and the evidence path `records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`. If the genuine count is non-zero, list each hit and state it is the first evidence of real use, not a trigger.

- [ ] **Step 5: Amend the charter.** Insert after line 193 of `$AS/docs/specs/2026-08-03-apple-studio-design.md` (the last line of the Phase 7 block, `> rationale stands.`), keeping one `>` blank line before it:

```markdown
>
> **Amended 2026-09-30 (Phase 9).** Phase 8 shipped the catalog migration,
> not ML, and did not amend the line above. ML remains the one outstanding
> long-tail item. Phase 9 is on-demand work: adaptive layout and iPhone Duo —
> see docs/specs/2026-09-30-phase9-adaptive-layout-design.md.
```

- [ ] **Step 6: Record the `verified:` headers of the two existing files this phase edits.** Run `head -1 plugins/apple-studio/skills/apple-design/references/platform-idioms.md plugins/apple-studio/skills/apple-design/references/hig-patterns.md | tee -a $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/headers.log`. Expected: `2026-08` and `2026-09` respectively. They are re-stamped in Task 4 only because Task 4 edits them.

- [ ] **Step 7: Check prose and commit.** Run Vale on `deferred.md` and the charter; fix any non-"amend" warning in the lines you added.

```bash
git add $AS/docs/deferred.md $AS/docs/specs/2026-08-03-apple-studio-design.md $AS/records/2026-09-30-phase9-adaptive-layout/task-0-sweep
git commit -m "Phase 9 Task 0: kill-switch sweep and charter amendment

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

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

### Task 2: `typecheck_snippets.py` gains a per-file iOS target

**Files:**
- Modify: `$AS/pipeline/typecheck_snippets.py` (`run`, `check`, `main`, `FRAMEWORK_HINTS`, `preamble_for`)
- Create: `$AS/pipeline/fixtures/typecheck/{ios-only.md,macos-default.md,invented.md,bad-directive.md,too-new.md,uikit.md}`
- Create: `$AS/pipeline/test_typecheck_snippets.sh`
- Modify: `$AS/CONVENTIONS.md` (§ Pipeline tooling, the `typecheck_snippets.py` bullet)

**Interfaces:**
- Produces: header directive `> typecheck: ios <major>.<minor>`; exit codes 0 (all clean), 1 (a snippet failed), 2 (directive malformed or SDK older than directive). `check(code, prior, ios=None)`, `run(src, extra, ios=None)`, `ios_target(text) -> str | None`. Tasks 4 and 7 rely on the directive.

- [ ] **Step 1: Write the fixtures.** Each is a tiny markdown file. The fixtures use 27.0 APIs, so this task runs on the installed 27.0 SDK.

`ios-only.md`, `invented.md`, and `macos-default.md` share one snippet, with one character changed in `invented.md` (`ToolbarOverflowMenuu`) and the directive line removed in `macos-default.md`:

````markdown
> typecheck: ios 27.0

```swift
struct OverflowProbe: View {
    var body: some View {
        Text("Body")
            .toolbar {
                ToolbarOverflowMenu {
                    Button("Print", systemImage: "printer") {}
                }
            }
    }
}
```
````

`bad-directive.md`: the same snippet with the header `> typecheck: iOS27`.
`too-new.md`: the same snippet with the header `> typecheck: ios 99.0`.
`uikit.md`:

````markdown
> typecheck: ios 27.0

```swift
final class ProbeViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
    }
}
```
````

- [ ] **Step 2: Write the failing test.** Create `$AS/pipeline/test_typecheck_snippets.sh`:

```bash
#!/bin/bash
# Self-test for typecheck_snippets.py's iOS directive. Needs an installed
# iPhoneOS SDK >= 27.0; compiles for real, so allow ~1 minute.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
F="$HERE/fixtures/typecheck"
fail=0
expect() { # expect <exit-code> <fixture> [grep-pattern]
  out="$(python3 "$HERE/typecheck_snippets.py" "$F/$2" 2>&1)"; rc=$?
  if [ "$rc" != "$1" ]; then echo "FAIL $2: exit $rc, want $1"; echo "$out" | tail -5; fail=1; return; fi
  if [ -n "${3:-}" ] && ! grep -q "$3" <<<"$out"; then echo "FAIL $2: no '$3' in output"; fail=1; return; fi
  echo "ok   $2 -> $rc"
}
expect 0 ios-only.md                        # iOS-only API passes under the directive
expect 1 macos-default.md "unavailable in macOS"   # same code, no directive: macOS, fails
expect 1 invented.md "cannot find"          # invented symbol still fails under iOS
expect 2 bad-directive.md "expected 'ios <major>.<minor>'"
expect 2 too-new.md "older than the directive"
expect 0 uikit.md                           # UIKit hint imports UIKit
exit $fail
```

- [ ] **Step 3: Run it to verify it fails.** `bash $AS/pipeline/test_typecheck_snippets.sh`. Expected: `ios-only.md` fails with exit 1 (no directive support, compiles for macOS), `bad-directive.md` and `too-new.md` exit 1 not 2, `uikit.md` exits 1. Save output to `task-2-typecheck/red.log`.

- [ ] **Step 4: Record the whole-catalog baseline before changing the script.**

```bash
python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/*/references/*.md plugins/apple-studio/skills/*/references/primers/*.md > $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/catalog-before.log 2>&1; tail -1 $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/catalog-before.log
```

Expected: a `TOTAL: <ok>/<n>` line. Record it; Step 7 compares against it.

- [ ] **Step 5: Implement.** In `$AS/pipeline/typecheck_snippets.py`:

  1. Add to `FRAMEWORK_HINTS`, after the SwiftUI entry:

```python
    # Added Phase 9 for the iOS directive. UIKit snippets only make sense in a
    # file that declares `> typecheck: ios <version>`; on macOS UIKit does not
    # exist and every one of them fails.
    ("UIKit",           r"\b(UIViewController|UIView\b|UIBarButtonItem|UINavigationItem|UITraitCollection|UISheetPresentationController|UIArrangementViewController)"),
```

  2. Add to `preamble_for`'s `BINDINGS`: `("proxy", "GeometryProxy", "SwiftUI"),`. Do **not** rebind `view`; existing snippets depend on `view: __View`. UIKit snippets in references are written as full declarations instead (see Task 4).

  3. Add, above `run`:

```python
DIRECTIVE = re.compile(r"^> typecheck:\s*(.*?)\s*$", re.M)

class DirectiveError(Exception):
    pass

def ios_target(text):
    """Return the iOS version a reference declares, or None for the macOS default."""
    m = DIRECTIVE.search(text)
    if not m:
        return None
    v = re.fullmatch(r"ios (\d+\.\d+)", m.group(1))
    if not v:
        raise DirectiveError(f"bad directive {m.group(1)!r}: expected 'ios <major>.<minor>'")
    want = v.group(1)
    have = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-version"],
                          capture_output=True, text=True).stdout.strip()
    as_tuple = lambda s: tuple(int(x) for x in s.split("."))
    if not have or as_tuple(have) < as_tuple(want):
        raise DirectiveError(f"installed iPhoneOS SDK {have or '(none)'} is older than the directive ios {want}")
    return want
```

  4. Change `run(src, extra)` to `run(src, extra, ios=None)`. When `ios` is set, replace the macOS `-F` framework path with the iOS SDK and target:

```python
        if ios:
            sdk = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-path"],
                                 capture_output=True, text=True).stdout.strip()
            plat = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-platform-path"],
                                  capture_output=True, text=True).stdout.strip()
            fw = ["-sdk", sdk, "-target", f"arm64-apple-ios{ios}",
                  "-F", f"{plat}/Developer/Library/Frameworks"]
        else:
            SDK_F = "/Applications/Xcode-beta.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Frameworks"
            fw = ["-F", SDK_F] if os.path.isdir(SDK_F) else []
```

  5. Change `check(code, prior="")` to `check(code, prior="", ios=None)` and pass `ios` to every `run(src, extra, ios)` call.

  6. In `main`, per file: call `ios = ios_target(text)` inside `try`; on `DirectiveError as e`, print `FILE: <path>  DIRECTIVE ERROR: <e>` and remember to exit 2. Print `target: ios <v>` or `target: macOS (default)` on the FILE line. Pass `ios` to `check`. At the end, exit 2 if any directive error occurred, else 0/1 as today.

  7. Add to the module docstring, after USAGE: a paragraph stating the directive, its format, the exit codes, and that it was added in Phase 9 because the Duo APIs include iOS-only symbols that fail on the macOS default.

- [ ] **Step 6: Run the test to verify it passes.** `bash $AS/pipeline/test_typecheck_snippets.sh | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/green.log`. Expected: six `ok` lines, exit 0.

- [ ] **Step 7: Prove no regression on files without the directive.** Re-run Step 4's command into `catalog-after.log`. Expected: the identical `TOTAL:` line, and `diff <(grep -E 'PASS|FAIL' catalog-before.log) <(grep -E 'PASS|FAIL' catalog-after.log)` prints nothing.

- [ ] **Step 8: Document the directive.** In `$AS/CONVENTIONS.md`, append to the `pipeline/typecheck_snippets.py` bullet (after "…is the ship gate for any API-specific claim."):

```markdown
  A reference whose APIs are iOS-only declares `> typecheck: ios <major>.<minor>`
  in its header block; the script then compiles that file against the iPhoneOS
  SDK. Without the directive a file compiles for macOS, which is correct for
  cross-platform SwiftUI and wrong for UIKit or iOS-only SwiftUI. A malformed
  directive, or one newer than the installed SDK, exits 2 rather than falling
  back. (Amended 2026-09-30, Phase 9.)
```

- [ ] **Step 9: Commit.**

```bash
git add $AS/pipeline/typecheck_snippets.py $AS/pipeline/test_typecheck_snippets.sh $AS/pipeline/fixtures/typecheck $AS/CONVENTIONS.md $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck
git commit -m "Phase 9 Task 2: per-file iOS target for the snippet ship gate

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Triage the two `accessibility.md` failures (deferred item 7)

**Files:**
- Modify: `plugins/apple-studio/skills/apple-design/references/accessibility.md:29-37` and `:63-69`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md`

**Interfaces:**
- Consumes: `typecheck_snippets.py` from Task 2 (macOS default is correct here; do not add a directive).
- Produces: `apple-design` at 4/4 before Task 4 adds blocks.

- [ ] **Step 1: Classify before editing.** Write `triage.md` with one row per failure: snippet, compiler error (quote from `survey/typecheck-apple-design-baseline.log`), classification, reason.
  - `#1 Slider(value: $guess.red)`: **framing artifact** — `$guess` is never declared and the expressions sit at top level. **Plus a reference defect** — `accentColor(_:)` is deprecated from iOS 27.2 in favour of `tint(_:)` (`task-1-docc/live-check.log`).
  - `#2 @Environment(\.accessibilityReduceMotion)`: **framing artifact** — a property wrapper at top level. **Plus a reference defect** — `AnyView` in a ternary erases view identity; an `if`/`else` in a `@ViewBuilder` body is the SwiftUI form.

- [ ] **Step 2: Replace block #1** (lines 29–37) with:

```swift
struct ColorGuessRow: View {
    @State private var red = 0.5

    var body: some View {
        VStack {
            Slider(value: $red)
                .tint(.red)
                .accessibilityValue("red \(Int(red * 255))")

            Image("decorative-background")
                .resizable()
                .accessibilityHidden(true)
        }
    }
}
```

- [ ] **Step 3: Replace block #2** (lines 63–69) with:

```swift
struct StatusGlyph: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        if reduceMotion {
            Image(systemName: "circle.fill")
        } else {
            Image(systemName: "circle.fill")
                .symbolEffect(.pulse)
        }
    }
}
```

- [ ] **Step 4: Update the prose around both blocks.** The sentence before block #1 names no API that changed. The sentence before block #2 says "gate custom animations on the environment value" — keep it. Update the file's `verified:` line to add `re-checked 2026-09 (Phase 9: snippets reframed, accentColor → tint)`.

- [ ] **Step 5: Run the gate.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y/typecheck.log | tail -1`. Expected: `TOTAL: 4/4 snippets typecheck clean`.

- [ ] **Step 6: Run the catalog gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design/references/accessibility.md $AS/records/2026-09-30-phase9-adaptive-layout/task-3-a11y
git commit -m "Phase 9 Task 3: triage and fix apple-design's two snippet failures

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Distillation map, `adaptive-layout.md`, and `apple-design` routing

**Files:**
- Create: `$AS/pipeline/maps/apple-design-duo-live.md`
- Create: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`
- Modify: `plugins/apple-studio/skills/apple-design/SKILL.md:15` (routing line)
- Modify: `plugins/apple-studio/skills/apple-design/references/platform-idioms.md:1-7,49,83-93`
- Modify: `plugins/apple-studio/skills/apple-design/references/hig-patterns.md:1,31`
- Modify: `$AS/CONVENTIONS.md:48-49` (file-count rule)

**Interfaces:**
- Consumes: `docc.py --hig` (Task 1); the `> typecheck: ios 27.1` directive (Task 2).
- Produces: `adaptive-layout.md` with section anchors `## What layout reads`, `## System containers first`, `## Reserved regions`, `## Arrangement views`, `## Bars that adapt to space`, `## Games`, `## Checking a layout on iPhone Duo`, `## Maintaining older code: UIKit equivalents`. Task 7 compiles it; Task 8 fills its runtime citations; Task 5 and Task 8 link to its sections by these names.

- [ ] **Step 1: Write the distillation map.** Create `$AS/pipeline/maps/apple-design-duo-live.md` listing, one per line, the seed pages with the `docc.py` invocation for each:
  - `--hig designing-for-iphone-duo`, `--hig layout`, `--hig toolbars`, `--hig split-views`
  - `technologyoverviews/preparing-your-app-for-iphone-duo`
  - SwiftUI: `swiftui/reservedregion`, `swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:)`, `swiftui/arrangementview`, `swiftui/view/arrangementviewstyle(_:)`, `swiftui/environmentvalues/toolbarverticaledge`, `swiftui/view/toolbarverticalbehavior(_:)`, `swiftui/view/toolbarverticalcompressionbehavior(_:)`, `swiftui/toolbarcontent/axisbehavior(_:)`, `swiftui/toolbarcontent/visibilitypriority(_:)`, `swiftui/toolbaroverflowmenu`, `swiftui/toolbaritemplacement/topbarpinnedtrailing`, `swiftui/view/presentationplacement(_:)`, `swiftui/view/backgroundextensioneffect()`
  - UIKit: `uikit/uiarrangementviewcontroller`, `uikit/uiview/reservedregion`, `uikit/uiview/reservedregions(kind:options:)`, `uikit/uitraitcollection/verticalbaredge`, `uikit/uiviewcontroller/preferredverticalbarbehavior`, `uikit/uinavigationitem/pinnedtrailinggroup`, `uikit/uinavigationitem/additionaloverflowitems`, `uikit/uibarbuttonitem/axisbehavior-swift.property`, `uikit/uibarbuttonitem/visibilitypriority`, `uikit/uisheetpresentationcontroller/preferredplacement`, `uikit/uibackgroundextensionview`, `uikit/uiverticalbarcompressionbehavior`
  - `xcode/device-hub`, `avkit/choosing-a-camera-by-the-direction-it-faces`, `avfoundation/registering-a-camera-capture-accessory-on-iphone-duo`
  - App Store Connect screenshot specifications (WebFetch; see `survey/screenshot-specifications.txt`)

  Run each through `docc.py` (the ones with `(` need quoting), writing output to the session scratchpad, **not** the repo. Any that fail: add a `MISSING: <path> — <error>` line to the map.

- [ ] **Step 2: Amend the file-count rule.** In `$AS/CONVENTIONS.md`, replace lines 48–49:

```markdown
- Location: `plugins/apple-studio/skills/<skill>/references/<topic>.md`, one file per
  decision area, a few hundred lines each. Most skills need 3–6. A reference file MUST NOT
  be named for a device; name it for the decision it serves. (Amended 2026-09-30,
  Phase 9: iPhone Duo guidance lives in `apple-design/references/adaptive-layout.md`,
  because its APIs are documented for every platform.) Not book summaries —
  decision-grade guidance only.
```

- [ ] **Step 3: Write the header and sections 1–2 of `adaptive-layout.md`.** Header (fill the month and SDK build when Task 7 compiles):

```markdown
> verified: 2026-09 against https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo, https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo, <every other URL fetched in Step 1 that this file cites>; compiled against iPhoneOS 27.1 SDK (<build>)
> sources: live HIG and developer documentation (DocC JSON)
> typecheck: ios 27.1
> note: iPhone Duo APIs are iOS 27.1 beta as of 2026-09. Re-verify at 27.1 GA (docs/deferred.md). Behavioral claims R1–R4 cite runtime evidence in records/2026-09-30-phase9-adaptive-layout/task-8-probe/.
```

Then `# Adaptive Layout`, a two-sentence opening (this file owns layout that survives any size, shape, or pose; iPhone Duo is the hardest case, iPad windowing and iPhone Mirroring the familiar ones), and:

  - `## What layout reads` — must state, in our own words: layout decisions read size classes and the scene's or container's bounds; never `userInterfaceIdiom`, interface orientation, or screen dimensions (developer page); size views relative to their container. Move in, rewritten to fit, the content of `platform-idioms.md:85-93` (containers adapt; `horizontalSizeClass` over `#if os`). State the fluid-layout rule generally (arbitrary widths, not breakpoints) and note iPad windowing and Duo poses as two sources of it. Duo specifics: outer display is compact width, inner display regular width; together they cover every pose (HIG § Device poses). Don't redesign on resize — let the existing layout expand.
  - `## System containers first` — `NavigationSplitView` collapses on the outer display and expands on the inner, as between compact and regular elsewhere; split views adjust column width and margins to the fold; alerts, context menus, and sheets move off the fold on their own. Mail as the "one more level of hierarchy on the larger display" example (HIG § Best practices). Keep functionality and state identical across displays and poses.

- [ ] **Step 4: Write section 3, `## Reserved regions`.** Must state: two kinds, `occlusion` (hardware covers content) and `division` (the fold splits a view); a region is active or inactive and the query returns intersecting regions; `includeInactive` exists to also see inactive ones; Duo's three regions (outer camera always, inner camera only while the camera runs, fold only when partly open); iPad window controls as the familiar precedent; frames are in a fixed coordinate space, so a manual layout MUST account for right-to-left (`layoutDirectionBehavior`), while a custom `Layout` mirrors for you; prefer even column counts; favor small moves over rearrangement. Ship this snippet:

```swift
struct LiveBadgeOverlay: View {
    var body: some View {
        GeometryReader { proxy in
            let cameraRegions = proxy.reservedRegions(kind: .occlusion)
            let topTrailingBlocked = cameraRegions.contains { region in
                region.frame.minY < 80 && region.frame.maxX > proxy.size.width - 160
            }
            Text("Live")
                .padding(8)
                .background(.thinMaterial, in: .capsule)
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity,
                       alignment: topTrailingBlocked ? .bottomTrailing : .topTrailing)
        }
    }
}
```

   Prose after it: this is the manual fallback; system components already avoid regions, so reach for this only in a custom view.

- [ ] **Step 5: Write section 4, `## Arrangement views`.** Must state: primary plus secondary view; `split` puts them side by side when wider than tall and stacked when taller, adjusting around the fold; `overlay` layers primary over secondary when no division is active, and moves them to either side of the fold when partly open; the default style resolves to split; constrain axes with `axes(_:)`; `HStack`/`VStack` layouts map to split, `ZStack` to overlay; navigation containers go around an arrangement view, never inside; never put one inside a `List`, `ScrollView`, or `NavigationSplitView`. Ship:

```swift
struct TrackDetail: View {
    var body: some View {
        ArrangementView {
            Text("Now playing")
        } secondary: {
            Text("Lyrics")
        }
        .arrangementViewStyle(.split.axes(.horizontal))
    }
}
```

   One sentence: with `.axes(.horizontal)`, a tall container shows only the primary view.

- [ ] **Step 6: Write section 5, `## Bars that adapt to space`.** Must state:
  - Where bars go vertical: the outer display in every orientation; the inner display in landscape; not the inner display in portrait (HIG § Vertical controls). They stay on the hardware side in right-to-left languages. In Split View multitasking each app puts its bar on its outer edge.
  - Context rules (developer page): inspectors horizontal; in a multi-column split view, sidebar and content bars horizontal and detail bar vertical; sheets on the outer display vertical by default; sheets on the inner display horizontal for centered or leading placement and vertical for trailing.
  - Getting it for free: attach `toolbar(content:)` to a `NavigationStack` or `NavigationSplitView`; a custom bar view gets none of this.
  - Order: primary navigation (Back, Close) at the top, then prominent actions (Done), then the remaining groups in their original grouping.
  - Every item gets a title and a symbol: vertical uses the symbol, horizontal prefers the symbol, overflow uses both; a title-only item or a custom-view item never goes vertical. Keep text buttons rare.
  - Overflow: items overflow bottom-to-top by default; set `visibilityPriority(_:)` on groups first, then items; keep frequent actions and badged items visible longest; move any home-made overflow menu into `ToolbarOverflowMenu`; reserve the ellipsis symbol for overflow.
  - Compression: navigation-focused views keep the tab bar and overflow toolbar items (default); task-focused views keep toolbar items with `.prefersToolbarItems`.
  - Opting out: `toolbarVerticalBehavior(.disabled)` only for full-screen media or non-scrolling layouts like a calculator; don't override placement otherwise. `presentationPlacement(_:)` picks a sheet's side. `axisBehavior(_:)` restricts one item.
  - Custom views read `toolbarVerticalEdge` (nil where no vertical bar is ever used) and extend hero images under the bar with `backgroundExtensionEffect()`.
  - Full-width layouts for non-scrolling immersive screens, clear of the Dynamic Island and status bar (Calculator example). Keep controls near the content they affect (Mail's list controls stay over the list).

   Ship these two snippets:

```swift
struct MessageDetail: View {
    var body: some View {
        NavigationStack {
            Text("Message body")
                .navigationTitle("Message")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close", systemImage: "xmark") {}
                    }
                    ToolbarItem(placement: .topBarPinnedTrailing) {
                        Button("Done", systemImage: "checkmark") {}
                    }
                    ToolbarItem(placement: .secondaryAction) {
                        Button("Reply", systemImage: "arrowshape.turn.up.left") {}
                    }
                    .visibilityPriority(.high)
                    ToolbarItem(placement: .secondaryAction) {
                        Button("Flag", systemImage: "flag") {}
                    }
                    .visibilityPriority(.low)
                    ToolbarOverflowMenu {
                        Button("Print", systemImage: "printer") {}
                    }
                }
                .toolbarVerticalCompressionBehavior(.prefersToolbarItems)
        }
    }
}
```

```swift
struct FloatingPaletteHost: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        Image(systemName: "paintpalette")
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity,
                   alignment: barEdge == .leading ? .bottomTrailing : .bottomLeading)
    }
}
```

   Prose after the second: place custom floating controls on the edge opposite the vertical bar.

- [ ] **Step 7: Write sections 6–8.**
  - `## Games` — lock orientation if needed but fill the screen in every pose; keep text and control sizes steady; change the aspect ratio rather than letterbox; if letterboxing is unavoidable, fill the padding with artwork. Link the HIG games page.
  - `## Checking a layout on iPhone Duo` — a checklist: both displays; closed, open, partly folded; rotate each pose; every view, sheet, and popover; bars on the side; nothing important in the fold. Build with the current Xcode: apps built with Xcode 26 or earlier do not extend under the status bar and camera. Preview poses in Xcode's Device Hub; capture them per `xcode-loop` (Task 8 adds that section). Camera apps: one sentence pointing to Apple's "Choosing a camera by the direction it faces" and "Registering a camera capture accessory on iPhone Duo", noting a camera may face the other way after the device opens or closes.
  - `## Maintaining older code: UIKit equivalents` — a two-column table mapping each SwiftUI API named above to its UIKit counterpart: `ArrangementView`→`UIArrangementViewController`; `reservedRegions(kind:options:layoutDirectionBehavior:)`→`UIView.reservedRegions(kind:options:)`; `toolbarVerticalEdge`→`UITraitCollection.verticalBarEdge`; `toolbarVerticalBehavior(_:)`→`UIViewController.preferredVerticalBarBehavior`; `toolbarVerticalCompressionBehavior(_:)`→`UIVerticalBarCompressionBehavior`; `topBarPinnedTrailing`→`UINavigationItem.pinnedTrailingGroup`; `cancellationAction`→`UINavigationItem.leadingItemGroups`; `axisBehavior(_:)`→`UIBarButtonItem.axisBehavior`; `visibilityPriority(_:)`→`UIBarButtonItem.visibilityPriority`; `ToolbarOverflowMenu`→`UINavigationItem.additionalOverflowItems`; `presentationPlacement(_:)`→`UISheetPresentationController.preferredPlacement`; `backgroundExtensionEffect()`→`UIBackgroundExtensionView`. Plus two rules in prose: set items on a view controller inside a navigation controller rather than building a `UIToolbar`/`UINavigationBar`/`UITabBar` yourself; use automatic trait tracking and Auto Layout. No UIKit snippets; Task 7 verifies every UIKit name by header search.

- [ ] **Step 8: Rewire `apple-design`.**
  - `SKILL.md`: insert after the line `- iPhone vs iPad vs Mac in one codebase → \`references/platform-idioms.md\``:
    `- Layout across sizes, poses, and foldables (iPhone Duo), reserved regions, bars that move to the side → \`references/adaptive-layout.md\``
  - `platform-idioms.md`: replace lines 85–93 (from "SwiftUI's structural containers already handle…" through the `horizontalSizeClass` paragraph) with: `Layout shape — containers that adapt, size classes over platform checks, fluid widths — lives in \`adaptive-layout.md\` § What layout reads. What follows is the other half: the capabilities that genuinely differ by platform.` Keep the "Genuine reasons to branch" list and the closing paragraph. In line 49, change "build fluid layout, not fixed breakpoints" to end with "(see `adaptive-layout.md` § What layout reads)". In the file's opening paragraph (line 7), change "see the "When to branch" section for the boundary…" to point at `adaptive-layout.md` for layout shape. Add `re-checked 2026-09 (Phase 9: layout-shape content moved to adaptive-layout.md)` to its `verified:` line.
  - `hig-patterns.md`: after line 31 `(HIG: Tab Bars)`, add a paragraph: `Where bars move to a vertical edge — iPhone Duo's outer display and landscape inner display — item order, overflow, and toolbar-versus-tab-bar compression are in \`adaptive-layout.md\` § Bars that adapt to space.` Add `re-checked 2026-09 (Phase 9: pointer to adaptive-layout.md)` to its `verified:` line.

- [ ] **Step 9: Check the content requirements.** Run and save to `task-4-reference/checks.log`:

```bash
R=plugins/apple-studio/skills/apple-design/references/adaptive-layout.md
wc -l $R                                           # expect 200-300
grep -ci "right-to-left" $R                        # expect >= 2 (reserved regions, bars)
grep -c '^## ' $R                                  # expect 8
grep -n "userInterfaceIdiom" $R                    # expect a "never" rule
grep -rn "When to branch" plugins/apple-studio/skills/apple-design/   # no stale "see When to branch" pointers
vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini $R
```

   Reference prose is R1-E register: fix Vale warnings except where a warning conflicts with an API name.

- [ ] **Step 10: Typecheck what the 27.0 SDK can check.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md`. Expected on the 27.0 SDK: exit 2 with `installed iPhoneOS SDK 27.0 is older than the directive ios 27.1` for `adaptive-layout.md` and 4/4 for the rest. That exit is correct, not a failure of this task: Task 7 owns the 27.1 compile. Save the output to `task-4-reference/typecheck-27.0.log`.

- [ ] **Step 11: Run the catalog gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add $AS/pipeline/maps/apple-design-duo-live.md $AS/CONVENTIONS.md plugins/apple-studio/skills/apple-design $AS/records/2026-09-30-phase9-adaptive-layout/task-4-reference
git commit -m "Phase 9 Task 4: adaptive-layout reference and apple-design routing

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: iPhone Duo screenshot sizes in `app-release`

**Files:**
- Modify: `plugins/apple-studio/skills/app-release/references/app-store-submission.md:1,101`

**Interfaces:**
- Consumes: `survey/screenshot-specifications.txt`.

- [ ] **Step 1: Re-check the source.** WebFetch `https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications` with the prompt "Quote the iPhone Duo screenshot sizes and any note about upload availability." Expected: outer 1398 × 2034 / 2034 × 1398, inner 2007 × 2853 / 2853 × 2007, and a note that uploads come later. If anything differs, use the fetched values and record the difference in `task-5-screenshots/fetch.txt`.

- [ ] **Step 2: Edit.** After the bullet at line 101 (`- **Screenshots per required device class.** …`), append to that bullet: ` iPhone Duo adds two size classes, one per display: outer 1398 × 2034 px (portrait) and inner 2007 × 2853 px (portrait), with their landscape equivalents. As of 2026-09 App Store Connect cannot yet accept Duo uploads, so check the specification page before planning a Duo screenshot set (https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications). Capture each display in the poses \`apple-design\`'s \`adaptive-layout.md\` § Checking a layout on iPhone Duo lists.`

   Append to the file's `verified:` line: `; re-checked 2026-09 against https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications (Phase 9: iPhone Duo sizes)`.

- [ ] **Step 3: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/app-release/references/app-store-submission.md $AS/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots
git commit -m "Phase 9 Task 5: iPhone Duo screenshot sizes

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Fixture screen, eval baseline, and the conditional description edit (deferred item 13)

**Files:**
- Create: `~/Projects/StudioFixture/StudioFixture/MailboxScreen.swift` (committed in the fixture's own repository)
- Modify: `~/Projects/StudioFixture/StudioFixture/ContentView.swift`
- Modify: `plugins/apple-studio/skills/apple-design/evals/triggers.md`
- Modify (conditional, Step 8): `plugins/apple-studio/skills/apple-design/SKILL.md:3`
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/prompts.tsv`, `baseline/`, `after-edit/` (only if Step 8 runs)

**Interfaces:**
- Consumes: the routing line from Task 4; `run_evals.py` (runs each session with `cwd` set to the fixture, `run_evals.py:181`).
- Produces: a fixture with real UI that Task 8's probe copy also contains.

- [ ] **Step 1: Add the screen.** Create `~/Projects/StudioFixture/StudioFixture/MailboxScreen.swift` (the project uses folder-synchronized groups, so no project-file edit is needed). It uses only 27.0 APIs and must build for iOS, macOS, and visionOS:

```swift
import SwiftUI

struct MailboxScreen: View {
    @State private var selection: String?
    private let messages = ["Quarterly report", "Team lunch", "Build failed", "Design review"]

    var body: some View {
        TabView {
            Tab("Inbox", systemImage: "tray") {
                NavigationSplitView {
                    List(messages, id: \.self, selection: $selection) { message in
                        Text(message)
                    }
                    .navigationTitle("Inbox")
                    .toolbar {
                        ToolbarItem(placement: .primaryAction) {
                            Button("Compose", systemImage: "square.and.pencil") {}
                        }
                    }
                } detail: {
                    if let selection {
                        Text(selection)
                            .navigationTitle(selection)
                            .toolbar {
                                ToolbarItem { Button("Archive", systemImage: "archivebox") {} }
                                ToolbarItem { Button("Reply", systemImage: "arrowshape.turn.up.left") {} }
                                ToolbarItem { Button("Flag", systemImage: "flag") {} }
                            }
                    } else {
                        ContentUnavailableView("No Message Selected", systemImage: "envelope")
                    }
                }
            }
            Tab("Settings", systemImage: "gear") {
                Form {
                    Toggle("Notifications", isOn: .constant(true))
                }
            }
        }
    }
}

#Preview {
    MailboxScreen()
}
```

   In `ContentView.swift`, replace the body's `VStack { … }.padding()` with `MailboxScreen()`.

- [ ] **Step 2: Build for iOS.** `xcodebuild -project ~/Projects/StudioFixture/StudioFixture.xcodeproj -scheme StudioFixture -destination 'generic/platform=iOS Simulator' -derivedDataPath $TMPDIR/sf-dd build 2>&1 | tail -3`. Expected: `** BUILD SUCCEEDED **`.

- [ ] **Step 3: Build for macOS.** Same command with `-destination 'platform=macOS'`. Expected: `** BUILD SUCCEEDED **`. (Review Focus 5.) Save both tails to `task-6-evals/fixture-build.log`.

- [ ] **Step 4: Commit in the fixture repository.**

```bash
git -C ~/Projects/StudioFixture add StudioFixture/MailboxScreen.swift StudioFixture/ContentView.swift
git -C ~/Projects/StudioFixture commit -m "Add a mailbox screen with toolbars, tabs, and a split view for apple-design evals"
git -C ~/Projects/StudioFixture status --porcelain   # expect empty
rm -rf $TMPDIR/sf-dd
```

- [ ] **Step 5: Add the eval rows.** In `plugins/apple-studio/skills/apple-design/evals/triggers.md`, append under `## Should fire`:

```markdown
- "Make my app work on iPhone Duo"
- "My toolbar buttons disappear when the phone is closed"
- "Content gets cut off at the fold"
- "Should I use an arrangement view here?"
```

   and under `## Should NOT fire`:

```markdown
- "Screenshot the app on the iPhone Duo simulator"   (xcode-loop)
- "What screenshot sizes does the App Store need for iPhone Duo?"  (app-release)
```

- [ ] **Step 6: Write the sweep file.** Create `task-6-evals/prompts.tsv` with every row of `triggers.md` (existing 10 plus the 6 new), tab-separated as `id<TAB>apple-design<TAB>FIRE|NOFIRE<TAB>prompt`. IDs: `fire-1`…`fire-10`, `nofire-1`…`nofire-6`, in file order. Prompts copied exactly, without quotes or the trailing parenthetical.

- [ ] **Step 7: Run the baseline sweep with the description unchanged.**

```bash
python3 $AS/pipeline/run_evals.py $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/prompts.tsv $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals/baseline
```

   Expected: a results table and `results.tsv` in `baseline/`; the fixture guard reports no writes (exit 1 with a `wrote` column otherwise — if so, the driver has already restored the tree; record which prompt wrote and continue). Record the pass rate, split into should-fire and should-NOT.

- [ ] **Step 8: Decide the description edit from the baseline, not from intuition.** For each failed row, read its session log and classify it per `.claude/rules/eval-harness.md`: `max_turns`, fixture-dependent (the prompt's referent is absent from the fixture), or routing miss (the session saw the skill list and chose another route). Write the classification to `task-6-evals/classification.md`.
  - If **no Duo should-fire row** (`fire-7`…`fire-10`) is a routing miss: do not edit the description. Record "description unchanged: baseline showed no Duo routing gap" and skip to Step 10.
  - If one or more is a routing miss: change `SKILL.md` line 3 `description:` to:

```
description: Apple Human Interface Guidelines conformance for iOS/iPadOS/macOS apps - layout and adaptive layout across sizes, poses, and foldables such as iPhone Duo, typography and Dynamic Type, color and materials, navigation and modality patterns, platform idioms, accessibility, and animation judgment. Use when designing or building UI, adapting a screen to a new size, pose, or fold, choosing a navigation or presentation pattern, styling views, making an app feel native, or fixing accessibility, Dynamic Type, or contrast issues. Not for brand identity or custom visual styling.
```

- [ ] **Step 9 (only if Step 8 edited the description): Sweep again.** Same command, output to `task-6-evals/after-edit`. Compare per row with `baseline/results.tsv`. A row that passed in the baseline and fails after the edit is a regression: revert the edit and record why.

- [ ] **Step 10: Update deferred item 13.** Append a `**Phase 9 (2026-09-30).**` paragraph: the fixture now has a real screen (commit hash from Step 4), the baseline and (if run) post-edit pass rates split by direction, the classification summary, and whether the description changed. State whether item 13 is resolved: resolved if every should-fire row (`fire-1`…`fire-10`) passes or is classified as non-routing and the should-NOT row "Design our brand color palette" passes; otherwise open, with the remaining rows named.

- [ ] **Step 11: Close checks, gates, and commit.**

```bash
git -C ~/Projects/StudioFixture status --porcelain   # expect empty
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design $AS/docs/deferred.md $AS/records/2026-09-30-phase9-adaptive-layout/task-6-evals
git commit -m "Phase 9 Task 6: fixture with real UI, apple-design eval baseline

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Compile gate against the iOS 27.1 SDK (needs Xcode 27.1 beta)

**Files:**
- Modify: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md` (fix any failing snippet or wrong name; fill the header's SDK build)
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/{sdk.log,typecheck.log,names.log}`

**Interfaces:**
- Consumes: the directive (Task 2); the reference (Task 4).
- Produces: a clean `apple-design` gate that Task 9 re-runs.

- [ ] **Step 1: Confirm the SDK, and stop if it is missing.**

```bash
{ xcode-select -p; xcodebuild -version; xcrun --sdk iphoneos --show-sdk-version; } | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/sdk.log
```

   Expected: SDK version `27.1` or later. If it prints `27.0`, stop this task and tell the user the 27.1 beta is not installed or not selected; do not work around it.

- [ ] **Step 2: Run the gate.** `python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/typecheck.log | tail -1`. Expected: `TOTAL: 8/8 snippets typecheck clean` (4 existing plus 4 new).

- [ ] **Step 3: Fix failures from the SDK, not from memory.** For each failure, find the real declaration in the shipped interface:

```bash
I="$(xcrun --sdk iphoneos --show-sdk-path)/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface"
grep -n "<the symbol from the diagnostic>" "$I" | head
```

   Correct the snippet to match the declaration. If a symbol the docs name is absent from the interface, remove the claim and record it in `typecheck.log` as documented-but-absent (the Phase 6 pattern). Re-run Step 2 until clean.

- [ ] **Step 4: Verify every name in prose, not only in snippets.** Snippets cover SwiftUI; the UIKit table and prose names are unchecked until this step.

```bash
SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
SW="$SDK/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface"
UK="$SDK/System/Library/Frameworks/UIKit.framework"
grep -o '`[A-Za-z][A-Za-z0-9_.]*' plugins/apple-studio/skills/apple-design/references/adaptive-layout.md \
  | tr -d '`' | awk -F. '{print $NF}' | sort -u | while read -r name; do
    if grep -qw "$name" "$SW" || grep -rqw "$name" "$UK/Headers" "$UK/Modules" 2>/dev/null; then
      echo "ok      $name"
    else
      echo "MISSING $name"
    fi
  done | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile/names.log | grep MISSING
```

   Expected: only non-symbol words (file names like `adaptive-layout`, `xcode-loop`) listed as MISSING. For each real symbol listed, check its Objective-C spelling in the headers (for example `UIArrangementViewController` may appear under an `NS_SWIFT_NAME`), then correct or remove it. Record each resolution in `names.log`.

- [ ] **Step 5: Fill the header.** Replace `<build>` in the `verified:` line with the build from `sdk.log`, and replace `<every other URL…>` with the actual list of URLs cited.

- [ ] **Step 6: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/apple-design/references/adaptive-layout.md $AS/records/2026-09-30-phase9-adaptive-layout/task-7-compile
git commit -m "Phase 9 Task 7: adaptive-layout compiles against the iOS 27.1 SDK

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Runtime probe R1–R4 and the `xcode-loop` pose section (needs Xcode 27.1 beta)

**Files:**
- Create: `$AS/pipeline/fixtures/duo-probe/DuoProbeView.swift`
- Create: `$AS/pipeline/fixtures/duo-probe/run.sh`
- Modify: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md` (cite R1–R4)
- Modify: `plugins/apple-studio/skills/xcode-loop/references/headless-commands.md:1,6-7` and append a section
- Create: `$AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe/` (discovery log, screenshots, unified-log extracts, `results.md`)

**Interfaces:**
- Consumes: Task 7's clean reference; the fixture (Task 6).
- Produces: runtime evidence for R1–R4; the `xcode-loop` pose instructions `adaptive-layout.md` § Checking a layout on iPhone Duo points to.

- [ ] **Step 1: Discover what the simulator offers.** Run and save everything to `task-8-probe/discovery.log`:

```bash
xcrun simctl list devicetypes | grep -i -E "duo|fold"
xcrun simctl list runtimes | grep -i ios
xcrun simctl help 2>&1 | grep -i -E "pose|posture|fold|hinge|display"
xcrun simctl help io 2>&1 | grep -i -E "pose|posture|fold|display"
```

   Classify the result as exactly one of: **A** — a Duo device type exists and `simctl` sets poses; **B** — a Duo device type exists, poses only through Device Hub or the Simulator GUI; **C** — no Duo device type. Write the classification and the exact command or menu path for poses to `discovery.log`. If **C**: skip to Step 7 and mark R1–R4 "documented, not runtime-checked".

- [ ] **Step 2: Create the device.** `xcrun simctl create "Duo Probe" "<device type identifier from Step 1>" "<iOS 27.1 runtime identifier>"`. Record the UDID.

- [ ] **Step 3: Write the probe view.** Create `$AS/pipeline/fixtures/duo-probe/DuoProbeView.swift`:

```swift
import SwiftUI
import os

private let probeLog = Logger(subsystem: "dev.frenchfultonjr.duoprobe", category: "probe")

/// Phase 9 runtime probe. Each label names the claim it checks; the unified
/// log carries the same values so a pose change is recorded even without a
/// screenshot.
struct DuoProbeView: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge
    @Environment(\.horizontalSizeClass) private var widthClass
    @State private var showSheet = false

    var body: some View {
        NavigationStack {
            GeometryReader { proxy in
                let divisions = proxy.reservedRegions(kind: .division, options: .includeInactive)
                let active = divisions.map(\.isActive)
                VStack(alignment: .leading, spacing: 12) {
                    Text("R1 toolbarVerticalEdge: \(String(describing: barEdge))")
                    Text("width class: \(String(describing: widthClass))  size: \(Int(proxy.size.width))×\(Int(proxy.size.height))")
                    Text("R3 divisions: \(divisions.count)  active: \(active.description)")
                    Button("R4 open sheet") { showSheet = true }
                }
                .padding()
                .onChange(of: active, initial: true) { _, value in
                    probeLog.log("R3 active=\(value.description, privacy: .public) count=\(divisions.count)")
                }
                .onChange(of: String(describing: barEdge), initial: true) { _, value in
                    probeLog.log("R1 edge=\(value, privacy: .public) size=\(Int(proxy.size.width))x\(Int(proxy.size.height))")
                }
            }
            .navigationTitle("Duo probe")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Share", systemImage: "square.and.arrow.up") {}
                }
                ToolbarItem(placement: .secondaryAction) {
                    Button("R2 TitleOnly") {}
                }
                ToolbarItem(placement: .secondaryAction) {
                    Button("R2 WithIcon", systemImage: "star") {}
                }
            }
        }
        .sheet(isPresented: $showSheet) { SheetProbe() }
    }
}

private struct SheetProbe: View {
    @State private var disableVertical = false
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        NavigationStack {
            Form {
                Text("R4 sheet toolbarVerticalEdge: \(String(describing: barEdge))")
                Toggle("toolbarVerticalBehavior(.disabled)", isOn: $disableVertical)
            }
            .navigationTitle("Sheet")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", systemImage: "checkmark") {}
                }
            }
            .toolbarVerticalBehavior(disableVertical ? .disabled : .automatic)
        }
    }
}
```

   If it fails to compile, fix it from the shipped interface as in Task 7 Step 3, not from memory.

- [ ] **Step 4: Write the run script.** Create `$AS/pipeline/fixtures/duo-probe/run.sh`:

```bash
#!/bin/bash
# Phase 9 Duo probe. Builds a scratch copy of StudioFixture with DuoProbeView
# as its root and installs it on the named simulator. Never touches
# ~/Projects/StudioFixture itself.
# Usage: run.sh <simulator-udid> <out-dir>
set -euo pipefail
UDID="$1"; OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
mkdir -p "$OUT"
cp -R "$HOME/Projects/StudioFixture" "$WORK/"
rm -rf "$WORK/StudioFixture/.git"
cp "$HERE/DuoProbeView.swift" "$WORK/StudioFixture/StudioFixture/"
sed -i '' 's/ContentView()/DuoProbeView()/' "$WORK/StudioFixture/StudioFixture/StudioFixtureApp.swift"
sed -i '' 's/IPHONEOS_DEPLOYMENT_TARGET = 27.0;/IPHONEOS_DEPLOYMENT_TARGET = 27.1;/' \
  "$WORK/StudioFixture/StudioFixture.xcodeproj/project.pbxproj"
xcodebuild -project "$WORK/StudioFixture/StudioFixture.xcodeproj" -scheme StudioFixture \
  -destination "id=$UDID" -derivedDataPath "$WORK/dd" build > "$OUT/build.log" 2>&1
APP="$WORK/dd/Build/Products/Debug-iphonesimulator/StudioFixture.app"
xcrun simctl boot "$UDID" 2>/dev/null || true   # "already booted" is fine; bootstatus is the real check
xcrun simctl bootstatus "$UDID"
xcrun simctl install "$UDID" "$APP"
BID="$(plutil -extract CFBundleIdentifier raw "$APP/Info.plist")"
xcrun simctl launch "$UDID" "$BID"
echo "$WORK" > "$OUT/workdir.txt"
echo "$BID" > "$OUT/bundle-id.txt"
```

   `chmod +x` it. Run: `$AS/pipeline/fixtures/duo-probe/run.sh <UDID> $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe`. Expected: `** BUILD SUCCEEDED **` in `build.log` and a `<bundle-id>: <pid>` line.

- [ ] **Step 5: Walk the poses.** For each state in this table, set it (by the Step 1 command or GUI path), wait two seconds, then capture `xcrun simctl io <UDID> screenshot task-8-probe/<state>.png`:

| State | Display | Pose |
|---|---|---|
| `outer-portrait` | outer | closed, portrait |
| `outer-landscape` | outer | closed, landscape |
| `inner-portrait` | inner | fully open, portrait |
| `inner-landscape` | inner | fully open, landscape |
| `inner-partial` | inner | partly folded |
| `outer-sheet` | outer | closed, portrait, sheet open |
| `outer-sheet-disabled` | outer | as above, toggle on |

   After the walk: `xcrun simctl spawn <UDID> log show --last 15m --predicate 'subsystem == "dev.frenchfultonjr.duoprobe"' > task-8-probe/unified.log`.

- [ ] **Step 6: Judge each claim against its evidence.** Write `task-8-probe/results.md`, one row per claim, verdict `CONFIRMED`, `CONTRADICTED`, or `NOT CHECKED`, with the screenshot or `unified.log` line that decides it:
  - **R1:** `edge` non-nil in `outer-portrait`, `outer-landscape`, `inner-landscape`; nil in `inner-portrait`.
  - **R2:** in a state with a vertical bar, "R2 WithIcon" appears in the vertical bar or its overflow, and "R2 TitleOnly" does not appear in the vertical bar.
  - **R3:** `active=[true]` only in `inner-partial`; `[false]` (or no active division) in fully open and closed states.
  - **R4:** `outer-sheet` shows the sheet's bar vertical and a non-nil sheet edge; `outer-sheet-disabled` shows it horizontal.
   A `CONTRADICTED` claim means the reference is wrong: correct `adaptive-layout.md` to match the runtime, and quote the evidence line in the correction.

- [ ] **Step 7: Cite the evidence in the reference.** In `adaptive-layout.md`, after each of the four claims, add `(runtime-checked 2026-09, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md)` or, for `NOT CHECKED` / discovery class C, `(documented, not runtime-checked)`. Re-run Task 7 Step 2; expect the same clean TOTAL.

- [ ] **Step 8: Add the `xcode-loop` pose section (deferred item 12 fires here).**
  - Replace `headless-commands.md` lines 6–7 (`Verified against a Multiplatform SwiftUI app fixture (\`~/Projects/StudioFixture\`, scheme\n\`StudioFixture\`, one target for iOS + macOS, Swift Testing unit tests).`) with `Verified against a multiplatform SwiftUI fixture app (one target for iOS + macOS, Swift Testing unit tests).`
  - Append `## 9. iPhone Duo — displays and poses` containing only what Step 1 and Step 5 verified: for class A, the exact `simctl` pose commands with their observed output; for class B, the Device Hub or Simulator menu path, stated plainly as not scriptable, followed by the screenshot command from § 7; for class C, one sentence that the Xcode 27.1 beta simulator had no iPhone Duo device type as of 2026-09. Commands not run do not go in this file (the file's own rule).
  - Append to its `verified:` line: `; § 9 verified 2026-09 against Xcode 27.1 beta (<build>), by execution`.

- [ ] **Step 9: Clean up.** `xcrun simctl shutdown <UDID>; xcrun simctl delete <UDID>; rm -rf "$(cat $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe/workdir.txt)"`. Then `xcrun simctl list devices booted` → expect no device, and `git -C ~/Projects/StudioFixture status --porcelain` → expect empty. Delete `workdir.txt` from the record (it names a temp path).

- [ ] **Step 10: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add $AS/pipeline/fixtures/duo-probe plugins/apple-studio/skills/apple-design/references/adaptive-layout.md plugins/apple-studio/skills/xcode-loop/references/headless-commands.md $AS/records/2026-09-30-phase9-adaptive-layout/task-8-probe
git commit -m "Phase 9 Task 8: runtime probe of four vertical-bar and fold claims; Duo poses in xcode-loop

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Deferred items, version bump, final gates, spec append

**Files:**
- Modify: `$AS/docs/deferred.md` (items 7 and 12; new items 14–17)
- Modify: `plugins/apple-studio/.claude-plugin/plugin.json` (version, description)
- Modify: `.claude-plugin/marketplace.json:78` (apple-studio description, which mirrors plugin.json)
- Modify: `$AS/docs/specs/2026-09-30-phase9-adaptive-layout-design.md` (append verification results)

**Interfaces:**
- Consumes: every task's record.

- [ ] **Step 1: Update item 7.** Append `**Phase 9 (2026-09-30).**`: its trigger ("the phase after Phase 7") passed in Phase 8 unaddressed; Phase 9 triaged the two `apple-design` failures (both framing artifacts, each with a reference defect: deprecated `accentColor`, `AnyView` in a ternary) and fixed them — evidence `records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md`. 17 remain, none in `apple-design`. The trigger stands: triage them in the next phase.

- [ ] **Step 2: Update item 12.** Append: resolved 2026-09-30 in Phase 9 Task 8, which edited `headless-commands.md` for the Duo pose section and rewrote the citation.

- [ ] **Step 3: Add new items.** After item 13:
  - **14. Re-verify every iOS 27.1 claim at GA.** `adaptive-layout.md` was compiled against a 27.1 beta SDK (build from `task-7-compile/sdk.log`). Beta APIs can be renamed. **Trigger: the first Xcode release whose iPhoneOS SDK is 27.1 non-beta** — re-run the gate and Task 8's probe.
  - **15. A camera primer for direction-aware capture.** Apple's "Choosing a camera by the direction it faces" and the iPhone Duo camera-accessory article are cited once in `adaptive-layout.md`; no AVFoundation primer exists. **Trigger: the first real app that captures photos or video on iPhone Duo.**
  - **16. App Store Connect upload support for Duo screenshots.** `app-store-submission.md` states uploads are not yet accepted. **Trigger: Apple's screenshot specification page drops that note** — then remove the caveat.
  - **17. R1–R4 runtime status.** Include this item only if any claim is `NOT CHECKED` or discovery was class B/C; name each unchecked claim and the reason. **Trigger: the first simulator or device that exposes the missing pose control.**

- [ ] **Step 4: Bump the version and descriptions.** In `plugin.json`: `"version": "0.10.0"`. In both `plugin.json` and `marketplace.json`, change `Human Interface Guidelines conformance and accessibility,` to `Human Interface Guidelines conformance and accessibility, adaptive layout across sizes, poses, and foldables,`.

- [ ] **Step 5: Run every gate and save the output to `task-9-release/gates.log`.**

```bash
python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md | tail -1   # TOTAL: n/n clean
python3 $AS/pipeline/test_docc.py                                                                           # PASS
bash $AS/pipeline/test_typecheck_snippets.sh                                                                # six ok, exit 0
bash $AS/pipeline/test_run_evals.sh                                                                         # passes
bun test
bun run audit
bun run audit --since main                                                                                  # no unbumped plugin
claude plugin validate . --strict
claude --plugin-dir plugins/apple-studio -p "List the apple-design skill's reference files" --allowedTools "Skill Read" --max-turns 6 < /dev/null   # names adaptive-layout.md
git -C ~/Projects/StudioFixture status --porcelain                                                          # empty
xcrun simctl list devices booted                                                                            # no device
```

   Every line must meet its expectation. If Task 7 or 8 could not run for lack of the SDK, the first line exits 2: stop and report the phase as blocked on the SDK rather than shipping.

- [ ] **Step 6: Append verification results to the spec.** Under a new `## Verification results (appended <date>, Phase 9 Task 9)` heading, one subsection per item in the spec's § Verification, each with **PASS**, **PARTIAL**, or **FAIL** and `<file>:<line-range>` evidence pointers into the phase record. Where the phase found one of the spec's own claims wrong, record the correction beside the claim (Phase 7 precedent). Include the kill-switch count, the eval pass rates, and R1–R4 verdicts.

- [ ] **Step 7: Prose check and commit.** Run Vale over `deferred.md` and the spec; fix any non-"amend" warning in the lines you added.

```bash
git add $AS/docs plugins/apple-studio/.claude-plugin/plugin.json .claude-plugin/marketplace.json $AS/records/2026-09-30-phase9-adaptive-layout/task-9-release
git commit -m "Phase 9 Task 9: apple-studio 0.10.0 — adaptive layout and iPhone Duo

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 8: Hand off.** Do not push, open a PR, or tag without the user's go-ahead. Report the branch, the commit list, and the gate log, then use superpowers:finishing-a-development-branch. The tag `apple-studio-v0.10.0` goes on the merge commit on `main`, after merge. Remind the user that Xcode imports a copy of the plugin and needs a re-import after merge (`deferred.md` item 3).
