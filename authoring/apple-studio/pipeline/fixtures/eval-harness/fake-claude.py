#!/usr/bin/env python3
"""Stub `claude` for testing pipeline/run_evals.py without real sessions.

Behavior is chosen by the prompt text:
  contains "WRITE"     -> writes a file into cwd (the fixture-write defect)
  contains "SILENT"    -> invokes no skill
  contains "EXHAUST"   -> ends in error_max_turns
  otherwise            -> invokes the skill named after "USE "
Also fails loudly if anything arrives on stdin, which is the stdin-leak test.
"""
import json
import os
import select
import sys

argv = sys.argv[1:]
prompt = ""
for i, a in enumerate(argv):
    if a == "-p" and i + 1 < len(argv):
        prompt = argv[i + 1]

# stdin must be empty; a leak shows up as readable data on fd 0
leaked = ""
if select.select([sys.stdin], [], [], 0)[0]:
    leaked = sys.stdin.read()
if leaked.strip():
    print(json.dumps({"type": "result", "subtype": "error", "is_error": True,
                      "stdin_leak": leaked[:200]}))
    sys.exit(0)

def emit(obj):
    print(json.dumps(obj), flush=True)

emit({"type": "system", "subtype": "init", "cwd": os.getcwd()})

if "WRITE" in prompt:
    with open(os.path.join(os.getcwd(), "LeakedByEval.swift"), "w") as f:
        f.write("// written by the stub, standing in for the real defect\n")

skill = None
if "USE " in prompt:
    skill = prompt.split("USE ", 1)[1].split()[0]
if "SILENT" in prompt:
    skill = None

if skill:
    emit({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "invoking"},
        {"type": "tool_use", "name": "Skill", "input": {"skill": f"apple-studio:{skill}"}},
    ]}})

if "EXHAUST" in prompt:
    emit({"type": "result", "subtype": "error_max_turns", "is_error": True, "num_turns": 6})
else:
    emit({"type": "result", "subtype": "success", "is_error": False, "num_turns": 2})
