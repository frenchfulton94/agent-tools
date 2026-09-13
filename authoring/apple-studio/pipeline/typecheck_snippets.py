#!/usr/bin/env python3
"""Extract every ```swift block from a markdown reference and typecheck it.

Written in Phase 6 (2026-09). The highest-yield verification in that phase.

WHY THIS EXISTS: a reference can cite a live doc page for every claim and still
ship API that does not exist. Compiling the snippets is what catches it. Phase 6
found, by compiling and not by reading:
  - the docs spell a method resolved(in:) that the SDK calls resolve(in:)
  - SystemLanguageModel.variant is documented ("macOS 27.0 BETA") and absent
  - two of Apple's own documentation samples do not compile at all

USAGE
    python3 pipeline/typecheck_snippets.py plugin/skills/<skill>/references/*.md

Exit code 0 only if every snippet compiles.

DESIGN NOTE: reference snippets are illustrative fragments, not programs. The
goal is to catch INVENTED API, not to punish elided context, so each snippet is
tried in several framings (declaration, top-level, wrapped in a function, with a
context preamble, with earlier snippets in the same file as context, and with
common return types). A hallucinated symbol still fails every framing — no
preamble rescues "cannot find type X in scope".

The preamble types must stay ACCURATE. Typing `image` as ImageReference once
made a correct `Attachment(image)` snippet fail, because Attachment takes a
CGImage/CIImage/CVPixelBuffer/URL. A wrong preamble type produces a bogus
failure that reads exactly like a reference defect.

AppIntentsTesting is not on the default framework search path; the -F below
handles it.

Phase 6 Tasks 2/3/6/7. Stricter than prior phases because the APIs are
post-training-data and cannot be sanity-checked from memory.

Strategy per snippet, first success wins:
  1. as written, with inferred imports, -parse-as-library
  2. as written, with inferred imports, top-level (script mode)
  3. body wrapped in `func __probe() async throws { ... }` (for fragments that
     are statements, not declarations)
Anything still failing is reported with the compiler's own diagnostics.
"""
import re, sys, subprocess, tempfile, pathlib, os

FRAMEWORK_HINTS = [
    ("FoundationModels", r"\b(SystemLanguageModel|LanguageModelSession|Generable|GenerationOptions|ContextOptions|Instructions\b|Prompt\(|Transcript|LanguageModelError|GenerationSchema|GeneratedContent|Guide\(|Tool\b|Attachment|ImageReference|PrivateCloudComputeLanguageModel|DynamicGenerationSchema|@Generable|@Guide)"),
    ("AppIntents",      r"\b(AppIntent|AppEntity|AppEnum|EntityQuery|AppShortcut|IntentParameter|AppIntentError|@Parameter|ParameterSummary|EntityPropertyQuery|IntentDescription|IntentDefinitions|IntentResult|LocalizedStringResource)"),
    ("SwiftUI",         r"\b(View\b|@State|@Binding|@Environment|VStack|HStack|Text\(|List\b|ScrollView|NavigationStack|@Observable|Button\(|\.task\b|some View|DragGesture|@GestureState|withAnimation|Animation\.|Spring\(|ButtonStyle|ScrollTargetBehavior|sensoryFeedback|scaleEffect|\.gesture\()"),
    # CoreGraphics-only snippets (a gesture-math helper taking CGFloat and no
    # SwiftUI type) matched no hint and failed with "cannot find type 'CGFloat'",
    # which reads exactly like an invented symbol. Added Phase 7, 2026-09-12.
    ("CoreGraphics",    r"\b(CGFloat|CGSize|CGPoint|CGRect|CGVector|CGAffineTransform)"),
    ("Observation",     r"@Observable"),
    ("Vision",          r"\b(OCRTool|BarcodeReaderTool|ImageProcessingRequest|DetectBarcodesRequest)"),
    ("os",              r"\b(OSSignposter|Logger\(|OSLog|signpost)"),
    ("MetricKit",       r"\bMX[A-Z]"),
    ("Foundation",      r"\b(URL\(|Data\(|Date\(|UUID\(|JSONDecoder|JSONEncoder|Locale)"),
    ("Testing",         r"@Test\b|#expect|#require"),
    ("AppIntentsTesting", r"\b(TestableIntent|withDependencies|AppIntentsTesting|IntentDefinitions)"),
]

def imports_for(code):
    out = []
    for mod, pat in FRAMEWORK_HINTS:
        if re.search(pat, code):
            out.append(mod)
    if "FoundationModels" in out and "Foundation" not in out:
        out.append("Foundation")
    return out

def run(src, extra):
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False) as f:
        f.write(src); p = f.name
    try:
        SDK_F = "/Applications/Xcode-beta.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Frameworks"
        fw = ["-F", SDK_F] if os.path.isdir(SDK_F) else []
        r = subprocess.run(["swiftc", "-typecheck", *fw, *extra, p],
                           capture_output=True, text=True, timeout=240)
        return r.returncode, (r.stderr or "").replace(p, "<snippet>")
    finally:
        os.unlink(p)

# Conventional bindings a fragment may reference without declaring. The point of
# this harness is to catch INVENTED API (wrong symbol, wrong signature), not to
# punish a reference for writing `session.respond(...)` without first showing the
# `let session = ...` line. Anything hallucinated still fails: an unknown member
# or type is not rescued by a preamble.
def preamble_for(code):
    """Declare the conventional bindings a fragment may reference without showing.

    The types here must be ACCURATE — a wrong type produces a bogus failure that
    looks like a reference defect. Learned the hard way: typing `image` as
    ImageReference made a correct `Attachment(image)` snippet fail, because
    Attachment takes a CGImage/CIImage/CVPixelBuffer/URL, not an ImageReference.
    """
    BINDINGS = [
        ("session",      "LanguageModelSession", "FoundationModels"),
        ("model",        "SystemLanguageModel",  "FoundationModels"),
        ("options",      "GenerationOptions",    "FoundationModels"),
        ("transcript",   "Transcript",           "FoundationModels"),
        ("image",        "CGImage",              "FoundationModels"),
        ("prompt",       "String",               None),
        ("instructions", "String",               None),
        ("response",     "String",               None),
        ("ticketBody",   "String",               None),
        ("userText",     "String",               None),
        ("text",         "String",               None),
        ("view",         "__View",               None),
        ("untrustedTextFromTheUser", "String", None),
    ]
    used = [(n, t, m) for n, t, m in BINDINGS if re.search(r"\b" + re.escape(n) + r"\b", code)]
    if not used:
        return "", []
    out = ""
    if any(n == "view" for n, _, _ in used):
        out += "final class __View { var text: String = \"\" }\n"
    decl = "var %s: %s { get { fatalError() } set { } }\n"
    out += "".join(decl % (n, t) for n, t, _ in used)
    mods = {m for _, _, m in used if m}
    if any(t == "CGImage" for _, t, _ in used):
        mods.add("CoreGraphics")
    return out, sorted(mods)

def check(code, prior=""):
    pre, pre_mods = preamble_for(code)
    mods = imports_for(code)
    for m in pre_mods:
        if m not in mods:
            mods.append(m)
    hdr = "".join(f"import {m}\n" for m in mods)
    attempts = [
        ("parse-as-library", hdr + code, ["-parse-as-library"]),
        ("with-prior",       hdr + prior + code, ["-parse-as-library"]),
        ("with-prior+ctx",   hdr + prior + pre + "func __probe() async throws {\n" + code + "\n}\n", ["-parse-as-library"]),
        ("top-level",        hdr + code, []),
        ("wrapped-in-func",  hdr + "func __probe() async throws {\n" + code + "\n}\n", ["-parse-as-library"]),
    ]
    if pre:
        attempts.append(("with-context",
                         hdr + pre + "func __probe() async throws {\n" + code + "\n}\n",
                         ["-parse-as-library"]))
        attempts.append(("with-context-decl",
                         hdr + pre + code, ["-parse-as-library"]))
        # A snippet that is a function BODY may contain `return`. Wrapping it in a
        # Void function turns a correct snippet into a bogus failure, so try the
        # common return types too.
        for rt in ("String?", "String", "Bool", "Int"):
            attempts.append((f"with-context->{rt}",
                             hdr + pre + f"func __probe() async throws -> {rt} {{\n" + code + "\n}\n",
                             ["-parse-as-library"]))
    diags = []
    for name, src, extra in attempts:
        rc, err = run(src, extra)
        if rc == 0:
            return True, name, ""
        diags.append(f"--- mode: {name} ---\n{err.strip()}")
    return False, None, "\n".join(diags)

def main():
    total = ok = 0
    for path in sys.argv[1:]:
        text = pathlib.Path(path).read_text()
        blocks = re.findall(r"```swift\n(.*?)```", text, re.S)
        print(f"\n{'='*78}\nFILE: {path}   ({len(blocks)} swift blocks)")
        prior = ""
        for i, code in enumerate(blocks, 1):
            total += 1
            passed, mode, diag = check(code, prior)
            # A snippet that stands alone as declarations becomes context for the
            # snippets after it — reference examples build on each other, and a
            # type defined in block 1 is legitimately used in block 3.
            if passed and mode in ("parse-as-library", "with-prior"):
                prior += code + "\n"
            first = next((l for l in code.strip().splitlines() if l.strip()), "")[:72]
            if passed:
                ok += 1
                print(f"  [PASS:{mode:16s}] #{i}  {first}")
            else:
                print(f"  [FAIL] #{i}  {first}")
                print("      imports tried: " + (", ".join(imports_for(code)) or "(none)"))
                for line in diag.splitlines():
                    print("      " + line)
    print(f"\nTOTAL: {ok}/{total} snippets typecheck clean")
    sys.exit(0 if ok == total else 1)

main()
