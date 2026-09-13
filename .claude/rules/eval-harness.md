---
paths:
  - "plugins/apple-studio/skills/*/evals/**"
---

# Trigger-eval harness

One headless session per prompt, from the catalog root:

```
claude --plugin-dir plugins/apple-studio -p "<prompt>" \
  --allowedTools "Skill Read" --max-turns 6 \
  --output-format stream-json --verbose < /dev/null
```

- **`< /dev/null` is required.** Driving the sweep from a `while read` loop over
  a prompt file lets the backgrounded `claude` inherit the loop's stdin and
  swallow the rest of the file into its prompt. Phase 6 lost a verdict this way
  and the identical prompt passed once redirected.
- **`--max-turns 2` is too low.** Denied `Bash` attempts still consume turns, so
  a skill can run out before it fires. Use 6, and re-run the whole sweep at one
  setting rather than patching a single row. Phase 8 re-learned this the hard
  way: `--max-turns 2` produced `error_max_turns` with no `Skill` call at all,
  which reads exactly like a routing miss and is not one.
- **From-scratch and consume-test prompts run from the fixture cwd**
  (`~/Projects/StudioFixture`), not the catalog root, with `--max-turns` ≥ 25.
- **A routing query run with cwd inside a repo that contains its own eval file
  can answer analytically instead of invoking the skill.** Phase 8 saw this
  directly: a prompt run with cwd inside `agent-tools` read the very eval file
  under test and reasoned about the answer instead of calling `Skill`. Run
  eval sweeps from a cwd that has no visibility into the evals being scored —
  the fixture for consume-tests, a neutral directory otherwise — never from
  inside the catalog or authoring tree.
- **No "build X" phrasing** in eval prompts — the superpowers brainstorming
  skill preempts the skill under test.
- **`--allowedTools` does not prevent writes.** The Phase 6 sweep left nine
  source files, a `build/` directory, and two modified files in the fixture.
  Check `git -C ~/Projects/StudioFixture status --porcelain` in the *closing*
  verification pass, not only after the task that touches the fixture; restore
  with `git clean -fd` + `git restore .`. A dirty fixture does not invalidate
  trigger verdicts (they depend on which skill fires) but contaminates any
  prompt that reads the project.

A failure is a harness defect until proven otherwise. Broadening a skill
description to catch a prompt that was never properly delivered is how a real
routing bug gets buried — Phase 6 traced both apparent misfires to this file's
first two rules and changed no description.

Run the sweep through `authoring/apple-studio/pipeline/run_evals.py` rather
than a fresh loop; it implements the guard above and self-tests offline via
`authoring/apple-studio/pipeline/test_run_evals.sh` (paths as they stand in
the catalog; consult that script directly if this line drifts).
