#!/usr/bin/env python3
"""Compile every ```metal, ```cpp, and ```rust block in a markdown reference.

Written in Phase 10 (2026-10), the sibling of typecheck_snippets.py. That script
owns ```swift blocks; this one owns the other three languages a Metal reference
carries, and it refuses to let any other code fence ship unchecked.

WHY THIS EXISTS: the same reason as the Swift gate. A reference can cite a live
doc page for every claim and still ship API that does not exist, and in MSL,
metal-cpp, and objc2-metal the invented symbol is just as easy to write.
Compilation is the ship gate.

USAGE (from the catalog root)
    python3 authoring/apple-studio/pipeline/typecheck_native.py FILE... [--cache DIR]

`--cache` defaults to authoring/apple-studio/pipeline/tmp (gitignored). It holds
the metal-cpp headers and the scratch cargo crates.

Exit code 0 only if every gated block compiles. 1: a snippet failed to compile.
2: a setup or directive problem, so the gate could not give an honest answer. 2
wins over 1. Nothing below may pass silently or produce a bogus "cannot find".

DIRECTIVES, in the file's header block (like `> typecheck:` for Swift):

    > typecheck-metal: metal4.0
        xcrun -sdk macosx metal -std=metal4.0 -c <f> -o /dev/null
        Needs the Metal Toolchain: `xcodebuild -downloadComponent MetalToolchain`
        (Xcode 27 ships the shader compiler as a separate download). A version
        the compiler rejects, such as metal9.9, exits 2.

    > typecheck-cpp: metal-cpp 26.4
        clang++ -std=c++20 -fsyntax-only -I <cache>/metal-cpp/26.4 <f>
        The headers come from `fetch_metal_cpp.sh 26.4`. A missing directory
        exits 2 (not in cache), because every symbol would otherwise fail with
        a "file not found" that reads like a reference defect.

    > typecheck-rust: objc2 = "=0.6.5", objc2-metal = "=0.3.2"
        The comma-separated TOML dependency items are written verbatim under
        [dependencies] of a scratch crate at <cache>/rust-gate/<sha256 of the
        directive>/ (edition 2024), then `cargo check --message-format short`.
        The first run needs the network to fetch crates. A dependency that does
        not resolve exits 2: a crate that never resolved says nothing about the
        snippet. objc2-metal gates its classes and protocols behind cargo
        features, but its default features enable all of them.

A file with blocks in one of these languages and no matching directive exits 2.
Any other fence language exits 2 (`ungated fence language: objc`), except text,
bash, sh, console, tsv, and the config and data fences xml, json, toml, plist,
yaml, cmake, makefile (Phase 10 ruling P3: they are configuration, not code in a
gated language). ```swift blocks are skipped here; typecheck_snippets.py
compiles them.

Fence strictness (Phase 10 fix round 1). typecheck_snippets.py finds its blocks
with the literal text "```swift\n", so a ```Swift, ~~~swift, or "```swift title"
fence reaches no compiler. Every fence in a file must therefore be exactly
"```<lowercase language>": three backticks, no tildes, nothing after the
language. Anything else exits 2, naming the opener. A swift-like opener the
Swift gate cannot parse says `swift fence the Swift gate cannot parse`. A bare
fence exits 2 (`unlabelled fence`): label it text, or a gated language.

Strategy per snippet, first success wins:
  metal  1. the snippet after `#include <metal_stdlib>` and `using namespace metal;`
         2. the same with earlier passing blocks prepended
         3. the body wrapped in `kernel void __probe(uint __tid [[thread_position_in_grid]]) { ... }`
  cpp    1. the snippet after <Foundation/Foundation.hpp>, <Metal/Metal.hpp>,
            <QuartzCore/QuartzCore.hpp>, and <MetalFX/MetalFX.hpp> when cached
         2. the same with earlier passing blocks prepended
         3. the body wrapped in `void __probe() { ... }`
  rust   1. the snippet as src/lib.rs
         2. the same with earlier passing blocks prepended
         3. the body wrapped in `pub fn __probe() { ... }`, `use` lines hoisted above it
         4. the whole snippet wrapped in `pub fn __probe() { ... }`, where its
            `use` lines shadow earlier blocks' instead of colliding with them
An invented symbol fails every framing. A block that stands alone becomes
context for the blocks after it.
"""
import argparse
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATED = ("metal", "cpp", "rust")
# Fences that need no compile gate. Swift is gated, by the other script.
UNGATED_TEXT = {"text", "bash", "sh", "console", "tsv"}
UNGATED_CONFIG = {"xml", "json", "toml", "plist", "yaml", "cmake", "makefile"}
SKIPPED = {"swift"}

class SetupError(Exception):
    """The gate cannot give an honest answer. Exit 2."""


class DirectiveError(SetupError):
    pass


FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,}|~{3,})")
# The only opener a gated or ungated block may use. typecheck_snippets.py finds
# its blocks with the literal text "```swift\n", so an opener it would not match
# must never reach a reader as a block that "passed".
EXACT_OPENER = re.compile(r"```([a-z0-9_+-]+)")
SWIFT_LIKE = re.compile(r"[`~]{3,}\s*swift(?![a-z0-9_+-])", re.I)


def extract_blocks(text):
    """Return [(opener, code, line_number)] for every fenced block, in order.

    `opener` is the fence line without its indent, exactly as written. Fences made
    of backticks or tildes, of any length, are recognised so that no code block
    escapes classification; classify_opener() decides which ones are acceptable.
    """
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        indent, ticks = m.group("indent"), m.group("ticks")
        opener = lines[i][len(indent):]
        start = i + 1
        body = []
        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped and set(stripped) == {ticks[0]} and len(stripped) >= len(ticks):
                break
            line = lines[i]
            body.append(line[len(indent):] if line.startswith(indent) else line.lstrip())
            i += 1
        blocks.append((opener, "\n".join(body) + "\n", start))
        i += 1
    return blocks


def classify_opener(opener, line):
    """Return the fence language for an acceptable opener, or raise SetupError."""
    if opener == "```":
        raise SetupError(f"unlabelled fence: label it text, or a gated language (line {line})")
    m = EXACT_OPENER.fullmatch(opener)
    if m:
        return m.group(1)
    if SWIFT_LIKE.match(opener):
        raise SetupError(f"swift fence the Swift gate cannot parse: {opener} (line {line}); "
                         "write exactly ```swift, in lowercase, with nothing after it")
    raise SetupError(f"fence not in the exact form ```<lowercase language> (line {line}): {opener}; "
                     "no tildes, no uppercase, nothing after the language")


def directive(text, kind):
    """Return the value of `> typecheck-<kind>: ...`, or None. Two of them is an error."""
    found = re.findall(rf"^> typecheck-{kind}:[ \t]*(.*?)[ \t]*$", text, re.M)
    if len(found) > 1:
        raise DirectiveError(f"more than one '> typecheck-{kind}:' directive")
    return found[0] if found else None


def run_cmd(cmd, cwd=None, env=None, timeout=240):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env)
    except FileNotFoundError as e:
        raise SetupError(f"cannot run {cmd[0]}: {e}")
    return r.returncode, (r.stderr or "") + (r.stdout or "")


class Gate:
    def close(self):
        pass

    def accumulate(self, prior, code, mode):
        """The text a passing block adds to the context for later blocks."""
        return code + "\n"


def with_prior_and_probe(prelude, prior, code, wrap):
    """The three framings shared by all three languages."""
    return [
        ("as-written", prelude + code),
        ("with-prior", prelude + prior + code),
        ("wrapped-in-fn", prelude + prior + wrap(code)),
    ]


# ---------------------------------------------------------------- metal

MSL_PRELUDE = "#include <metal_stdlib>\nusing namespace metal;\n"


class MetalGate(Gate):
    name = "metal"

    def __init__(self, value, cache):
        m = re.fullmatch(r"metal(\d+\.\d+)", value)
        if not m:
            raise DirectiveError(f"bad directive {value!r}: expected 'metal<major>.<minor>'")
        self.std = f"metal{m.group(1)}"
        # A version the compiler does not know would turn every block into a bogus
        # failure, so ask it once with an empty kernel file.
        rc, out = self.compile(MSL_PRELUDE)
        if rc != 0:
            if "missing Metal Toolchain" in out:
                raise SetupError("missing Metal Toolchain; run: xcodebuild -downloadComponent MetalToolchain")
            first = next((l for l in out.splitlines() if l.strip()), "")
            raise DirectiveError(f"-std={self.std} rejected by xcrun metal: {first}")

    def label(self):
        return f"-std={self.std}"

    def compile(self, src):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "snippet.metal")
            pathlib.Path(f).write_text(src)
            rc, out = run_cmd(["xcrun", "-sdk", "macosx", "metal", f"-std={self.std}", "-c", f, "-o", "/dev/null"])
            return rc, out.replace(f, "<snippet>")

    def framings(self, code, prior):
        wrap = lambda c: "kernel void __probe(uint __tid [[thread_position_in_grid]]) {\n" + c + "\n}\n"
        return with_prior_and_probe(MSL_PRELUDE, prior, code, wrap)


# ---------------------------------------------------------------- cpp

class CppGate(Gate):
    name = "cpp"

    def __init__(self, value, cache):
        m = re.fullmatch(r"metal-cpp (\d+(?:\.\d+)*)", value)
        if not m:
            raise DirectiveError(f"bad directive {value!r}: expected 'metal-cpp <version>'")
        self.version = m.group(1)
        self.root = pathlib.Path(cache) / "metal-cpp" / self.version
        if not (self.root / "Metal" / "Metal.hpp").is_file():
            raise SetupError(f"metal-cpp {self.version} not in cache; run fetch_metal_cpp.sh {self.version}")
        includes = ["Foundation/Foundation.hpp", "Metal/Metal.hpp", "QuartzCore/QuartzCore.hpp"]
        if (self.root / "MetalFX" / "MetalFX.hpp").is_file():
            includes.append("MetalFX/MetalFX.hpp")
        self.prelude = "".join(f"#include <{h}>\n" for h in includes)
        # The headers themselves must compile, or every block fails for a reason
        # that is not the block's.
        rc, out = self.compile(self.prelude)
        if rc != 0:
            raise SetupError(f"metal-cpp {self.version} headers do not compile: {out.strip()[:400]}")

    def label(self):
        return f"metal-cpp {self.version}, -std=c++20"

    def compile(self, src):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "snippet.cpp")
            pathlib.Path(f).write_text(src)
            rc, out = run_cmd(["clang++", "-std=c++20", "-fsyntax-only", "-I", str(self.root), f])
            return rc, out.replace(f, "<snippet>")

    def framings(self, code, prior):
        wrap = lambda c: "void __probe() {\n" + c + "\n}\n"
        return with_prior_and_probe(self.prelude, prior, code, wrap)


# ---------------------------------------------------------------- rust

RESOLVE_FAILURE = re.compile(
    r"failed to select a version|no matching package|failed to get `|failed to download|"
    r"failed to load source|failed to parse manifest|Unable to update|could not find `[^`]+` in registry|"
    r"network|Could not resolve host|spurious")
COMPILE_FAILURE = re.compile(r"could not compile|error\[E\d+\]|error: aborting")
USE_START = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?use\b")


def split_toml_items(value):
    """Split on commas that are outside quotes, brackets, and braces."""
    items, depth, quote, cur = [], 0, None, []
    for ch in value:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    items.append("".join(cur).strip())
    return [i for i in items if i]


def hoist_uses(code):
    """Return (use statements, remaining code). A statement runs to its `;`."""
    uses, rest, i = [], [], 0
    lines = code.splitlines()
    while i < len(lines):
        if USE_START.match(lines[i]):
            stmt = [lines[i]]
            while not stmt[-1].rstrip().endswith(";") and i + 1 < len(lines):
                i += 1
                stmt.append(lines[i])
            uses.append("\n".join(stmt))
        else:
            rest.append(lines[i])
        i += 1
    return uses, "\n".join(rest) + "\n"


def drop_repeated_uses(prior, code):
    """Remove from `code` any use statement already present in `prior`.

    A reference repeats its imports block after block, and the same `use` twice
    in one module is an error that has nothing to do with the snippet.
    """
    have = {" ".join(u.split()) for u in hoist_uses(prior)[0]}
    uses, rest = hoist_uses(code)
    kept = [u for u in uses if " ".join(u.split()) not in have]
    # Keep line order stable enough to read in a diagnostic: uses first.
    return "\n".join(kept + [rest]) if kept else rest


class RustGate(Gate):
    name = "rust"

    def __init__(self, value, cache):
        if not value:
            raise DirectiveError("'> typecheck-rust:' names no dependencies; expected TOML items such as objc2-metal = \"=0.3.2\"")
        self.value = value
        self.items = split_toml_items(value)
        key = hashlib.sha256(value.encode()).hexdigest()
        base = pathlib.Path(cache) / "rust-gate"
        self.keydir = base / key
        self.keydir.mkdir(parents=True, exist_ok=True)
        # Every invocation gets its OWN crate directory. Two runs that share a
        # directive (parallel writers do) must not share a src/lib.rs: cargo takes
        # its build lock after the source is written, so one run's snippet would be
        # compiled as the other's, and an invented symbol could pass. The shared
        # target directory keeps builds cached; the lock file is seeded from the
        # last run so a warm run does not re-resolve.
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=self.keydir))
        self.env = dict(os.environ, CARGO_TARGET_DIR=str(base / "target"), CARGO_TERM_COLOR="never")
        # The crate name is unique per run too. Cargo hashes a workspace member by its
        # path RELATIVE to the workspace root, so two runs with the same crate name
        # share fingerprints in the shared target directory: the later run sees an
        # up-to-date stamp from the other run's build and reports success without
        # compiling its own source. Measured: an invented symbol passed 3 rounds of 4.
        self.crate = "probe_" + re.sub(r"[^a-z0-9]", "_", self.dir.name.lower())
        (self.dir / "src").mkdir()
        seed = self.keydir / "Cargo.lock"
        if seed.is_file():
            (self.dir / "Cargo.lock").write_text(seed.read_text())
        manifest = (
            f'[package]\nname = "{self.crate}"\nversion = "0.0.0"\nedition = "2024"\n\n'
            "[workspace]\n\n[dependencies]\n" + "\n".join(self.items) + "\n"
        )
        (self.dir / "Cargo.toml").write_text(manifest)
        try:
            self.preflight(value)
        except BaseException:
            self.close()
            raise

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def accumulate(self, prior, code, mode):
        # with-prior compiled the block with its repeated `use` lines removed;
        # adding the raw block would put the duplicates into every later framing.
        return (drop_repeated_uses(prior, code) if mode == "with-prior" else code) + "\n"

    def preflight(self, value):
        rc, out = self.cargo_check("")
        if rc == 0 and (self.dir / "Cargo.lock").is_file():
            tmp = self.keydir / f"Cargo.lock.{os.getpid()}"
            tmp.write_text((self.dir / "Cargo.lock").read_text())
            os.replace(tmp, self.keydir / "Cargo.lock")
        if rc != 0 and RESOLVE_FAILURE.search(out) and not COMPILE_FAILURE.search(out):
            lines = [l for l in out.splitlines() if l.strip()][:3]
            raise SetupError("rust dependency resolution failed for "
                             f"{value!r}; the crates never resolved, so no block was compiled:\n  " + "\n  ".join(lines))
        if rc != 0:
            raise SetupError(f"cargo check failed on an empty crate for {value!r}:\n  " + out.strip()[:400])

    def label(self):
        return "cargo check, " + self.value

    def cargo_check(self, src):
        (self.dir / "src" / "lib.rs").write_text(src)
        rc, out = run_cmd(["cargo", "check", "--message-format", "short"], cwd=self.dir, env=self.env, timeout=900)
        keep = [l for l in out.splitlines()
                if l.strip() and not re.match(r"\s*(Compiling|Checking|Locking|Downloading|Downloaded|Finished|Updating|Adding)\b", l)
                and "warning" not in l]
        return rc, "\n".join(keep) if rc != 0 else out

    def compile(self, src):
        return self.cargo_check(src)

    def framings(self, code, prior):
        def wrap(c):
            uses, rest = hoist_uses(drop_repeated_uses(prior, c))
            return "\n".join(uses) + "\npub fn __probe() {\n" + rest + "\n}\n"
        return [
            ("as-written", code),
            ("with-prior", prior + drop_repeated_uses(prior, code)),
            ("wrapped-in-fn", prior + wrap(code)),
            # Overlapping but unequal `use` statements ("use a::{X}" after "use a::{X, Y}")
            # collide at module level. Inside a function body they shadow instead.
            ("wrapped-whole", prior + "pub fn __probe() {\n" + code + "\n}\n"),
        ]


GATES = {"metal": MetalGate, "cpp": CppGate, "rust": RustGate}


# ---------------------------------------------------------------- driver

def check_block(gate, code, prior):
    diags = []
    for name, src in gate.framings(code, prior):
        rc, out = gate.compile(src)
        if rc == 0:
            return True, name, ""
        diags.append(f"--- framing: {name} ---\n{out.strip()}")
    return False, None, "\n".join(diags)


def check_file(path, cache):
    """Return (ok_count, total, error_or_None). Prints the report for the file."""
    text = pathlib.Path(path).read_text()
    # Refuse before compiling anything: an unchecked fence is the thing this gate exists to stop.
    blocks = []
    for opener, code, line in extract_blocks(text):
        lang = classify_opener(opener, line)
        if not (lang in GATED or lang in SKIPPED or lang in UNGATED_TEXT or lang in UNGATED_CONFIG):
            raise SetupError(f"ungated fence language: {lang} (line {line}); add a compile gate for it, "
                             "or use a text, bash, sh, console, or tsv fence")
        blocks.append((lang, code, line))
    by_lang = {lang: [b for b in blocks if b[0] == lang] for lang in GATED}
    gates = {}
    opened = []
    for lang in GATED:
        if not by_lang[lang]:
            continue
        try:
            value = directive(text, lang)
            if value is None:
                raise SetupError(f"{len(by_lang[lang])} ```{lang} block(s) but no '> typecheck-{lang}:' directive")
            gates[lang] = GATES[lang](value, cache)
        except SetupError:
            for g in gates.values():
                g.close()
            raise
        opened.append(gates[lang])
    try:
        n = sum(len(v) for v in by_lang.values())
        label = "; ".join(g.label() for g in gates.values()) or "(no gated blocks)"
        print(f"\n{'=' * 78}\nFILE: {path}   ({n} gated blocks)   target: {label}")
        ok = 0
        for lang, gate in gates.items():
            prior = ""
            for _, code, line in by_lang[lang]:
                passed, mode, diag = check_block(gate, code, prior)
                if passed and mode in ("as-written", "with-prior"):
                    prior += gate.accumulate(prior, code, mode)
                first = next((l for l in code.strip().splitlines() if l.strip()), "")[:72]
                if passed:
                    ok += 1
                    print(f"  [PASS:{lang}:{mode:13s}] line {line}  {first}")
                else:
                    print(f"  [FAIL:{lang}] line {line}  {first}")
                    for l in diag.splitlines():
                        print("      " + l)
    finally:
        for g in opened:
            g.close()
    return ok, n


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compile ```metal, ```cpp, and ```rust blocks in markdown references.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--cache", default=str(HERE / "tmp"),
                    help="directory holding metal-cpp/ and rust-gate/ (default: pipeline/tmp)")
    args = ap.parse_args(argv)
    total = ok = 0
    setup_error = False
    for path in args.files:
        try:
            o, n = check_file(path, args.cache)
        except SetupError as e:
            print(f"\n{'=' * 78}\nFILE: {path}  SETUP ERROR: {e}")
            setup_error = True
            continue
        ok += o
        total += n
    print(f"\nTOTAL: {ok}/{total} snippets compile clean")
    if setup_error:
        return 2
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
