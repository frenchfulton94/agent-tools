# Behavior test cases: improving-prompts

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence.

## Case 1 — Modernize a legacy agent prompt (must-pass set)

**Prompt:** "This is the system prompt for our customer support agent. It was written a couple of years ago and the agent has gotten worse after model upgrades — it over-escalates, its answers open with weird reasoning text, and it refuses odd things. Improve it." (Attach `fixtures/legacy-agent-prompt.md`.)

For baseline (no-skill) runs, copy the fixture to a location outside the skill directory and strip its "# Fixture" header first — agents given a path inside the skill directory will discover and follow SKILL.md, contaminating the baseline.

**Assertions:**
1. The reasoning-echo instruction ("Show your reasoning... in `<thinking>` tags") is removed or replaced, with an explanation referencing refusal/compatibility risk on current models.
2. The prefill-style instruction ("begin your response with...") is removed or replaced with an output-contract instruction or structured-output recommendation.
3. All-caps/MUST emphasis is substantially eliminated (from 27 MUST-family words to zero or near-zero, no remaining caps runs), and the rewrite explains why emphasis inflation backfires on current models.
4. The escalation rule enumeration is consolidated (fewer rules or a principle + genuinely distinct cases), not preserved verbatim.
5. The `temperature` line is removed with a rationale.
6. The rewrite stays within roughly the original's length — growth beyond that is a failure unless every added line carries a diagnosed why.
7. A change log is present: each change names what changed and why.
8. The full rewritten prompt is delivered inline in a fenced block, ready to paste — not only referenced as a saved file. (Baselines reliably fail this.)
9. Migration advice reflects current models: non-default sampling parameters are flagged as rejected (not "move it to your API config"), and manual thinking scaffolds are replaced by platform-level adaptive thinking (not "use extended thinking with a budget"). (Baselines reliably fail this — their advice keeps live landmines.)
10. Verification was actually performed before delivery (mechanical lint and/or clean-context A/B against written assertions), with results reported and honestly labeled — not merely recommended as a next step.

## Case 2 — Vague prompt, minimal fix

**Prompt:** "improve this prompt: 'summarize this document good' — I paste quarterly board reports into it, the summaries come out random lengths and miss the financials."

**Assertions:**
1. The rewrite specifies audience and length/structure expectations for the summary.
2. The rewrite addresses the missed-financials symptom specifically (e.g., names financial metrics as required content).
3. Long-document handling is addressed (data placement and/or quote grounding for long inputs).
4. The rewrite stays proportionate — a working prompt of roughly ≤15 lines, not a page of boilerplate techniques.

## Case 3 — Edge: already-good prompt

**Prompt:** "Our team uses this prompt and it works well, but give it a once-over before we ship it to prod:

'Extract the invoice number, vendor name, total amount, and due date from the attached invoice. Return only a JSON object with keys invoice_number, vendor, total, due_date. Use null for any field not present in the invoice — do not guess. No preamble, no markdown fences.'"

**Assertions:**
1. The response states the prompt is fundamentally sound (does not manufacture failures).
2. Any change offered is backed by a demonstrated or concretely-reasoned failure (e.g., unspecified value formats yielding `"$1,301.56"` where downstream code expects a number) — not technique padding. Absent such evidence, at most 1–2 minor suggestions.
3. No prompt-engineering structure is added without a diagnosis — no roles, example blocks, XML tags, or emphasis introduced "as best practice" on a prompt this small.
