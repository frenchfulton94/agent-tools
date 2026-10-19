#!/usr/bin/env python3
"""Extract every ```swift block from a markdown reference and typecheck it.

Written in Phase 6 (2026-09). The highest-yield verification in that phase.

WHY THIS EXISTS: a reference can cite a live doc page for every claim and still
ship API that does not exist. Compiling the snippets is what catches it. Phase 6
found, by compiling and not by reading:
  - the docs spell a method resolved(in:) that the SDK calls resolve(in:)
  - SystemLanguageModel.variant is documented ("macOS 27.0 BETA") and absent
  - two of Apple's own documentation samples do not compile at all

USAGE (from the catalog root)
    python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/<skill>/references/*.md

Exit code 0 only if every snippet compiles.

TARGET DIRECTIVE (iOS added Phase 9; macOS and multi-target added Phase 10):
a reference declares its compile target in its header block, before the first
```swift fence:

    > typecheck: ios 27.0
    > typecheck: macos 26.0
    > typecheck: macos 26.0, ios 26.0

Each target is `macos <major>.<minor>` or `ios <major>.<minor>`. A `macos`
target compiles against the installed macOS SDK with `-target
arm64-apple-macos<version>`; an `ios` target against the iPhoneOS SDK with
`-target arm64-apple-ios<version>`. The version is the DEPLOYMENT target, so
an API newer than it fails with an availability error instead of passing
because the SDK is newer. That is the point of `macos 26.0`: Metal 4 begins at
macOS 26.0 / iOS 26.0, and at the SDK default (27.x) a use below the floor
would pass unseen.

With several targets, a snippet passes if it compiles on AT LEAST ONE of them,
and its PASS line names the target. The exception is a block whose source
contains `#if os(`: each target compiles only its own branch, so such a block
must compile on EVERY listed target, and it prints one PASS line per target
(ruling P50, Phase 10 Task 13). Blocks that stand alone become context for
later blocks per target, so an NSView block never leaks into an iOS compile.
Without any directive a file compiles for the macOS SDK default, which is
correct for cross-platform SwiftUI and wrong for UIKit or iOS-only SwiftUI (the
Duo / adaptive-layout APIs include iOS-only symbols that fail to typecheck on
macOS). Exit codes: 0 all snippets in all files typecheck clean; 1 a snippet
failed to typecheck; 2 a directive is malformed, or names a version newer than
the installed SDK for its platform — this exits rather than silently falling
back to the default.

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

AppIntentsTesting is not on the default framework search path; the macOS -F
derived from `xcrun --show-sdk-platform-path` in run() handles it.

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
    # Added Phase 9 for the iOS directive. UIKit snippets only make sense in a
    # file that declares `> typecheck: ios <version>`; on macOS UIKit does not
    # exist and every one of them fails.
    ("UIKit",           r"\b(UIViewController|UIView\b|UIBarButtonItem|UINavigationItem|UITraitCollection|UISheetPresentationController|UIArrangementViewController)"),
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

# Added Phase 10 (games on Metal). These apply ONLY to a file that declares a
# `> typecheck:` target, so a file with no directive imports exactly what it did
# before the directive grew (the whole-catalog TOTAL is the check). Each pattern
# is a symbol PREFIX the docs use, so a snippet that names the type gets the
# import without writing it. Entries for a module the list above already covers
# (SwiftUI, UIKit, CoreGraphics, os) add patterns; the import is emitted once.
DIRECTIVE_HINTS = [
    ("Metal",           r"\bMTL"),
    ("MetalKit",        r"\bMTK[A-Z]"),
    ("QuartzCore",      r"\b(CAMetal|CADisplayLink|CALayer|CATransaction|CAAnimation|CABasicAnimation)"),
    ("MetalFX",         r"\bMTLFX"),
    ("GameController",  r"\bGC[A-Z]"),
    ("GameKit",         r"\bGK[A-Z]"),
    ("AVFAudio",        r"\bAVAudio"),
    ("PHASE",           r"\bPHASE[A-Z]"),
    ("CoreHaptics",     r"\bCHHaptic"),
    ("ModelIO",         r"\bMDL[A-Z]"),
    ("UniformTypeIdentifiers", r"\bUTType"),
    ("AppKit",          r"\b(NSView|NSWindow|NSEvent|NSApplication|NSScreen|NSCursor)"),
    ("Network",         r"\bNW[A-Z]"),
    ("MetalPerformanceShaders",      r"\bMPS[A-Z]"),
    ("MetalPerformanceShadersGraph", r"\bMPSGraph"),
    ("simd",            r"\b(simd_\w+|float[234]x[234]|double[234]x[234]|float[234]\b|half[234]\b|quat[fd]\b|matrix_float\w+)"),
    ("CoreVideo",       r"\bCV[A-Z]"),
    ("IOSurface",       r"\bIOSurface"),
    ("CoreImage",       r"\bCI(Image|Context|Filter|Kernel|Color)\b"),
    ("CoreMotion",      r"\bCM(MotionManager|DeviceMotion|Attitude)"),
    ("Dispatch",        r"\b(DispatchQueue|DispatchSemaphore|DispatchTime|DispatchGroup|DispatchData|DispatchWorkItem)"),
    ("Synchronization", r"\b(Mutex[<(]|Atomic<)"),
    ("Accelerate",      r"\b(vDSP|vImage|BNNS|cblas)"),
    # More symbols for modules the base list covers.
    ("SwiftUI",         r"\b(NS|UI)(View|ViewController)Representable"),
    ("UIKit",           r"\b(UIApplication|UIScreen|UIWindowScene|UITouch|UIEvent|UIPress|UIDevice|UIResponder)"),
    ("CoreGraphics",    r"\b(CGColorSpace|CGImage|CGContext)"),
    # os_workgroup is MTLDevice's workgroup hand-off; both it and the unfair lock live in `os`.
    ("os",              r"\b(os_workgroup\w*|OSAllocatedUnfairLock|os_unfair_lock)"),
]

# Frameworks that exist on one platform family only. A snippet that names both
# an AppKit type and a UIKit type is cross-platform (`#if os(macOS)` branches),
# and an unconditional `import AppKit` fails on every iOS target. Imports for
# these two are therefore emitted under `#if canImport(...)` — in a directive
# file only; a file with no directive keeps the plain import it always had.
PLATFORM_ONLY = {"AppKit", "UIKit"}

def import_line(mod, conditional=False):
    if conditional and mod in PLATFORM_ONLY:
        return f"#if canImport({mod})\nimport {mod}\n#endif\n"
    return f"import {mod}\n"

def imports_for(code, extended=False):
    """Modules a snippet needs. `extended` adds the Phase 10 hints (directive files only)."""
    out = []
    for mod, pat in FRAMEWORK_HINTS:
        if re.search(pat, code):
            out.append(mod)
    if extended:
        for mod, pat in DIRECTIVE_HINTS:
            if mod not in out and re.search(pat, code):
                out.append(mod)
    if "FoundationModels" in out and "Foundation" not in out:
        out.append("Foundation")
    return out

DIRECTIVE = re.compile(r"^> typecheck:\s*(.*?)\s*$", re.M)
SDK_NAMES = {"macos": "macosx", "ios": "iphoneos"}
SDK_LABELS = {"macos": "MacOSX", "ios": "iPhoneOS"}

class DirectiveError(Exception):
    pass

def parse_targets(text):
    """Return the targets a reference declares, as [(platform, version), ...].

    An empty list means no directive: compile for the macOS SDK default, exactly
    as before the directive existed. Raises DirectiveError for a malformed
    directive or a version newer than the installed SDK for its platform.
    """
    m = DIRECTIVE.search(text)
    if not m:
        return []
    raw = m.group(1)
    targets = []
    for part in raw.split(","):
        v = re.fullmatch(r"(macos|ios) (\d+\.\d+)", part.strip())
        if not v:
            raise DirectiveError(f"bad directive {raw!r}: expected '<macos|ios> <major>.<minor>', "
                                 "comma-separated for several targets")
        targets.append((v.group(1), v.group(2)))
    as_tuple = lambda s: tuple(int(x) for x in s.split("."))
    for plat, want in targets:
        have = subprocess.run(["xcrun", "--sdk", SDK_NAMES[plat], "--show-sdk-version"],
                              capture_output=True, text=True).stdout.strip()
        if not have or as_tuple(have) < as_tuple(want):
            raise DirectiveError(f"installed {SDK_LABELS[plat]} SDK {have or '(none)'} is older than "
                                 f"the directive {plat} {want}")
    return targets

def target_name(target):
    return f"{target[0]} {target[1]}" if target else "macOS (default)"

def run(src, extra, target=None):
    """Typecheck one source. `target` is (platform, version) or None for the macOS default."""
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False) as f:
        f.write(src); p = f.name
    try:
        if target:
            plat_name, version = target
            sdk_name = SDK_NAMES[plat_name]
            sdk = subprocess.run(["xcrun", "--sdk", sdk_name, "--show-sdk-path"],
                                 capture_output=True, text=True).stdout.strip()
            plat = subprocess.run(["xcrun", "--sdk", sdk_name, "--show-sdk-platform-path"],
                                  capture_output=True, text=True).stdout.strip()
            triple = f"arm64-apple-ios{version}" if plat_name == "ios" else f"arm64-apple-macos{version}"
            fw = ["-sdk", sdk, "-target", triple,
                  "-F", f"{plat}/Developer/Library/Frameworks"]
        else:
            # Phase 9, Ruling 7: the hardcoded Xcode-beta.app path this used to
            # carry stopped existing when the beta installed as a differently
            # named app and replaced it, silently dropping the AppIntentsTesting
            # framework path. Derive the macOS platform's Frameworks dir instead
            # of hardcoding one Xcode install's name.
            plat = subprocess.run(["xcrun", "--sdk", "macosx", "--show-sdk-platform-path"],
                                  capture_output=True, text=True).stdout.strip()
            SDK_F = f"{plat}/Developer/Library/Frameworks"
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
        ("proxy",        "GeometryProxy",        "SwiftUI"),
        # Phase 10: a Metal fragment says `device.makeX(...)` without showing
        # where the device came from.
        ("device",       "any MTLDevice",        "Metal"),
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

def check(code, prior="", target=None, standalone_only=False):
    pre, pre_mods = preamble_for(code)
    mods = imports_for(code, extended=target is not None)
    for m in pre_mods:
        if m not in mods:
            mods.append(m)
    hdr = "".join(import_line(m, conditional=target is not None) for m in mods)
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
    if standalone_only:
        # The block already passed on another target. Here we only learn whether
        # it stands alone, so it can serve as context for later blocks on this
        # target; a failure on this target is expected and is not reported.
        attempts = attempts[:2]
    diags = []
    for name, src, extra in attempts:
        rc, err = run(src, extra, target)
        if rc == 0:
            return True, name, ""
        diags.append(f"--- mode: {name} ---\n{err.strip()}")
    return False, None, "\n".join(diags)

def main():
    total = ok = 0
    directive_error = False
    for path in sys.argv[1:]:
        text = pathlib.Path(path).read_text()
        # A file may declare its compile targets via the header directive
        # `> typecheck: <macos|ios> <major>.<minor>[, ...]` (iOS: Phase 9;
        # macOS and several targets: Phase 10). A malformed directive, or one
        # newer than the installed SDK, is a hard stop for this file — it never
        # silently falls back to compiling for the macOS default.
        try:
            targets = parse_targets(text)
        except DirectiveError as e:
            print(f"\n{'='*78}\nFILE: {path}  DIRECTIVE ERROR: {e}")
            directive_error = True
            continue
        blocks = re.findall(r"```swift\n(.*?)```", text, re.S)
        tries = targets or [None]
        multi = len(tries) > 1
        label = ", ".join(target_name(t) for t in tries)
        print(f"\n{'='*78}\nFILE: {path}   ({len(blocks)} swift blocks)   target: {label}")
        # One running context per target: a block that stands alone as
        # declarations is context for the blocks after it, but only on the
        # target it compiled for (an NSView block must not poison an iOS compile).
        prior = {t: "" for t in tries}
        for i, code in enumerate(blocks, 1):
            total += 1
            first = next((l for l in code.strip().splitlines() if l.strip()), "")[:72]
            if multi and "#if os(" in code:
                # A platform-conditional block (ruling P50, Phase 10 Task 13). Each
                # target compiles only its own branch, so a pass on one target says
                # nothing about the other branch. Compile on every target and pass
                # only if each one passes; print one line per target.
                results = []
                for t in tries:
                    p, mode, diag = check(code, prior[t], t)
                    if p and mode in ("parse-as-library", "with-prior"):
                        prior[t] += code + "\n"
                    results.append((t, p, mode, diag))
                if all(p for _, p, _, _ in results):
                    ok += 1
                    for t, _, mode, _ in results:
                        print(f"  [PASS:{mode:16s} @ {target_name(t)}] #{i}  {first}")
                else:
                    for t, p, mode, _ in results:
                        if p:
                            print(f"  [pass:{mode:16s} @ {target_name(t)}] #{i}  {first}")
                    print(f"  [FAIL] #{i}  {first}   (#if os(...) block: must pass on every target)")
                    print("      imports tried: " + (", ".join(imports_for(code, extended=True)) or "(none)"))
                    for t, p, _, diag in results:
                        if not p:
                            print(f"      === target: {target_name(t)} ===")
                            for line in diag.splitlines():
                                print("      " + line)
                continue
            passed = False
            diags = []
            for t in tries:
                p, mode, diag = check(code, prior[t], t, standalone_only=passed)
                # A snippet that stands alone as declarations becomes context for the
                # snippets after it — reference examples build on each other, and a
                # type defined in block 1 is legitimately used in block 3.
                if p and mode in ("parse-as-library", "with-prior"):
                    prior[t] += code + "\n"
                if p and not passed:
                    passed, passed_mode, passed_target = True, mode, t
                elif not p and not passed:
                    diags.append((t, diag))
            first = next((l for l in code.strip().splitlines() if l.strip()), "")[:72]
            if passed:
                ok += 1
                at = f" @ {target_name(passed_target)}" if multi else ""
                print(f"  [PASS:{passed_mode:16s}{at}] #{i}  {first}")
            else:
                print(f"  [FAIL] #{i}  {first}")
                print("      imports tried: " + (", ".join(imports_for(code, extended=bool(targets))) or "(none)"))
                for t, diag in diags:
                    if multi:
                        print(f"      === target: {target_name(t)} ===")
                    for line in diag.splitlines():
                        print("      " + line)
    print(f"\nTOTAL: {ok}/{total} snippets typecheck clean")
    if directive_error:
        sys.exit(2)
    sys.exit(0 if ok == total else 1)

main()
