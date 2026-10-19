"""Extract the dispatch snippets verbatim from the reference and build the driver."""
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
REF = pathlib.Path("/Users/michaelfrenchfultonjr/Projects/agent-tools/.claude/worktrees/apple-studio-phase10-games/plugins/apple-studio/skills/apple-metal/references/compute-and-gpu-driven.md")
text = REF.read_text()
swift = re.findall(r"```swift\n(.*?)```", text, re.S)
metal = re.findall(r"```metal\n(.*?)```", text, re.S)
upload = next(b for b in swift if "func encodeUploadThenFilter" in b)
pipe = next(b for b in swift if "func makeFilterPipeline" in b)
kernel = next(b for b in metal if "filterTile" in b)
(HERE / "snippet.swift").write_text("import Metal\n\n" + upload + "\n" + pipe)
(HERE / "filterTile.metal").write_text(kernel)
r = subprocess.run(["swiftc", "-O", "main.swift", "snippet.swift", "-o", "dispatch"], cwd=HERE,
                   capture_output=True, text=True)
print("build exit", r.returncode, r.stderr[-2000:])
