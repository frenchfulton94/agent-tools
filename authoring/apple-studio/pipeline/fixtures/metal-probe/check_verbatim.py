#!/usr/bin/env python3
"""Check that the probe's pasted snippets still match the apple-metal references.

Each file below holds exactly one fenced block from a reference, plus lines the
probe adds. A probe line ends with the marker `// probe` (Swift, C++, Rust) or
`# probe` (TOML, sh). The check removes every probe line and compares what is
left, byte for byte, with the block whose first line is given. Blank lines left
at the top of the file, after probe-only imports, are dropped first.

Exit 0 when every file matches, 1 when one drifts, 2 when a block is missing.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REFS = HERE.parents[4] / "plugins/apple-studio/skills/apple-metal/references"

# (probe file, reference file, start of one of the block's first three lines)
MAP = [
    ("Sources/MetalProbe/Reference/FlatColorPipeline.swift", "command-model.md",
     "/// The MSL the frame's pipeline compiles. It is the same source as the"),
    ("Sources/MetalProbe/Reference/FrameLoop.swift", "command-model.md",
     "/// How many frames the CPU may encode ahead of the GPU."),
    ("Sources/MetalProbe/Reference/RenderOffscreen.swift", "command-model.md",
     "func renderOffscreen(device: any MTLDevice, target: any MTLTexture, frames: Int) throws {"),
    ("Sources/MetalProbe/Reference/LabelledFrame.swift", "gpu-debugging-and-profiling.md",
     "func encodeLabelledFrame(queue: any MTL4CommandQueue,"),
    ("Sources/MetalProbe/Reference/StartTrace.swift", "gpu-debugging-and-profiling.md",
     "enum TraceError: Error { case captureLayerMissing }"),
    ("Sources/MetalProbe/Reference/FrameCapture.swift", "gpu-debugging-and-profiling.md",
     "final class FrameCapture {"),
    ("cpp/main.cpp", "cpp-and-rust.md",
     "// main.cpp: the one translation unit that defines the private implementation."),
    ("cpp/capture.cpp", "cpp-and-rust.md",
     "// Call before the frame's beginCommandBuffer; after the frame-done wait,"),
    ("rust/Cargo.toml", "cpp-and-rust.md", "[package]"),
    ("rust/src/main.rs", "cpp-and-rust.md", "use core::ptr::NonNull;"),
    ("rust/src/capture.rs", "cpp-and-rust.md", "use objc2::rc::Retained;"),
    ("rust/xcode-cargo.sh", "cpp-and-rust.md", "#!/bin/sh"),
]

PROBE_LINE = re.compile(r"(//|#) probe\b")


def blocks(path):
    lines = path.read_text().split("\n")
    found, i = [], 0
    while i < len(lines):
        if re.fullmatch(r"```\w+", lines[i]):
            j = i + 1
            while lines[j] != "```":
                j += 1
            found.append(lines[i + 1:j])
            i = j
        i += 1
    return found


def find_block(ref, first):
    """The one block in `ref` with a line starting `first` among its first three, or None.

    `ref` names a reference file, or is a path to a copy of one (run.sh reads
    earlier versions of a reference out of git that way)."""
    path = pathlib.Path(ref) if pathlib.Path(ref).is_file() else REFS / ref
    candidates = [b for b in blocks(path) if any(l.startswith(first) for l in b[:3])]
    return candidates[0] if len(candidates) == 1 else None


def main():
    if sys.argv[1:2] == ["--block"]:
        # check_verbatim.py --block <reference.md or path> <start of one of its first lines>
        # prints that block, so run.sh can execute documented commands verbatim.
        block = find_block(sys.argv[2], sys.argv[3])
        if block is None:
            print(f"no single block in {sys.argv[2]} starts with {sys.argv[3]!r}", file=sys.stderr)
            return 2
        print("\n".join(block))
        return 0
    bad = 0
    for probe_file, ref, first in MAP:
        # A block is found by any of its first three lines, so a leading
        # `import Metal` or `@MainActor` does not make the key ambiguous.
        want = find_block(ref, first)
        if want is None:
            print(f"MISSING {probe_file}: no single block in {ref} starts with {first!r}")
            return 2
        have = [l for l in (HERE / probe_file).read_text().rstrip("\n").split("\n")
                if not PROBE_LINE.search(l)]
        while have and have[0] == "":   # the blank line after probe-only imports
            have.pop(0)
        if have == want:
            print(f"ok      {probe_file} == {ref}")
        else:
            bad += 1
            print(f"DRIFT   {probe_file} != {ref}")
            for n, (a, b) in enumerate(zip(have, want)):
                if a != b:
                    print(f"  first difference at block line {n + 1}:\n    probe: {a!r}\n    ref:   {b!r}")
                    break
            else:
                print(f"  lengths differ: probe {len(have)} lines, reference {len(want)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
