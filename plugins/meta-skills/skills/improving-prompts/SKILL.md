---
name: improving-prompts
description: Reviews and rewrites prompts of any kind — system prompts, user prompts, agent instructions, slash commands, prompt templates — to make them clearer, leaner, and more effective on current Claude models. Use when the user shares a prompt and asks to improve, review, tighten, fix, optimize, or debug it, when a prompt underperforms, over-triggers, or gets ignored, when migrating prompts written for older models, or when drafting a high-stakes prompt from scratch. Also use when the user describes prompt symptoms without saying "prompt" — "my agent keeps doing X", "the model ignores my instructions", "the output is too verbose", "it worked on the old model but not now". Not for Agent Skill packages (SKILL.md) or project memory files (CLAUDE.md) — prefer their dedicated skills for those artifact types.
license: MIT
---

# Improving Prompts

Improve a prompt by diagnosing what actually fails, fixing that with the right technique, and verifying the fix — not by applying every technique to every prompt. The best prompt is the one that achieves the goal reliably with the minimum necessary structure; added structure that doesn't fix an observed problem makes prompts worse on current models.

## Step 1: Classify before touching

Establish three facts. Ask only if they can't be inferred:

1. **Where the prompt runs** — system prompt, user turn, agent/subagent instruction, command or template, skill text. This decides what's available (roles belong in system prompts; data placement matters in user turns) and what's forbidden (API params vs. prose).
2. **Target model and surface** — current Claude models differ materially from pre-2025 models and from other vendors. Migration advice lives in `references/modern-model-deltas.md`.
3. **Degrees of freedom the task needs** — a narrow bridge (one safe path: exact commands, low freedom) or an open field (many valid paths: goals and principles, high freedom). The most common rewrite error is over-constraining an open field or under-constraining a narrow bridge.

## Step 2: Diagnose — match the fix to the failure

Find the failure first; each has a different fix. Applying clarity fixes to a formatting failure (or vice versa) adds length without adding reliability.

| Symptom | Likely cause | Fix |
|---|---|---|
| Output too generic or shallow | Prompt states topic, not expectations | State desired depth/features explicitly ("go beyond the basics; include...") |
| Instruction ignored | Buried, vague, or drowned in noise | Move it up, make it concrete and testable, cut surrounding filler |
| Wrong output shape or style | Prohibitions where a recipe is needed | Positive template: state the shape wanted, show one filled example |
| Inconsistent across runs | Ambiguous wording permits several readings | Add one example or scope clause; tighten wording — not more rules |
| Does part of the task | Implicit scope | Explicit scope: "every section, not just the first" |
| Fabricates facts | No permitted out | Grant it: "If the data is insufficient, say so rather than speculating" |
| Over-eager tool/rule use | Emphasis inflation (CRITICAL/MUST) | Normal phrasing: "Use X when Y" |
| Suggests instead of doing | Polite indirection | Direct action verbs: "Change this function", not "Can you suggest changes?" |
| Worked on old model, broken now | Deprecated technique | Apply the migration table in Step 4 |

## Step 3: Rewrite

Apply only what the diagnosis calls for. The durable core:

1. **Clarity test.** Show the prompt to an imagined colleague with no context — anywhere they'd be confused, the model will be too. State exactly what's wanted; don't rely on inference.
2. **Motivation.** Give the why behind non-obvious constraints ("read aloud by text-to-speech, so no ellipses") — reasons generalize to unlisted cases; bare rules don't.
3. **Examples.** For format- or judgment-sensitive tasks, 1–5 examples beat description. Make them relevant, diverse (cover an edge case), and exactly aligned with what you want — models pattern-match on example details, including unwanted ones.
4. **Structure.** Order matters in long prompts: longform data at the top, instructions and the question at the end. Use XML tags to bound distinct content types in complex prompts (`<context>`, `<input>`); skip them in simple ones. When answers over long contexts (~20k+ tokens) drift from the source or fabricate, have the model extract relevant quotes before answering.
5. **Output contract.** Say what the response contains and in what order. Phrase positively ("flowing prose paragraphs"), match the prompt's own style to the desired output, and for machine-read output specify the exact schema.
6. **Self-check.** For multi-step or high-stakes tasks, end with one verification instruction ("Before finishing, verify the answer against the stated criteria").

Read `references/prompt-patterns.md` when applying a pattern you need the template or worked example for.

## Step 4: Modernize

Prompts written for pre-2025 models often contain now-harmful techniques. Scan for these; details and before/after examples in `references/modern-model-deltas.md`:

| Found in prompt | Do this |
|---|---|
| Prefilled assistant turn (forcing output to start with `{` etc.) | Remove — rejected by current models. Use structured outputs or a direct instruction |
| Manual thinking budgets, "think step by step" scaffolds with `<thinking>` tags | Remove — use the platform's thinking/effort settings; keep at most a brief "consider X before Y" |
| "Show your reasoning / explain your chain of thought in the response" | Remove — can trigger refusals on newest models. Ask for a result plus brief stated rationale |
| ALL-CAPS emphasis, "CRITICAL: You MUST" | Rephrase normally — current models over-trigger on shouting |
| Long enumerations of cases and exceptions | Collapse to one brief instruction plus the genuinely non-obvious exceptions |
| Aggressive anti-laziness scaffolds, forced status updates | Remove and re-test — usually no longer needed |
| Sampling parameters in prose or config (`temperature`, `top_p`) | Remove — rejected on newest models; steer tone via instructions |
| Heavy role theatrics ("world-renowned genius...") | Keep a one-line professional role; cut the theatrics |

Removal is a first-class improvement. If a prompt performs worse after your rewrite than before, prefer the shorter variant and re-diagnose.

## Step 5: Verify

- **Always:** re-read the rewrite cold, as the model would — no conversation context. Check every diagnosed failure has a corresponding change and no change lacks a diagnosis.
- **If you can execute code:** run `bun scripts/lint_prompt.ts <file>` for a mechanical scan of the Step 4 anti-patterns.
- **If you can run clean-context tests** (subagents or fresh sessions): A/B the old and new prompt on 2–3 realistic inputs, grade against written assertions with quoted evidence. Inconsistency across reps means remaining ambiguity — tighten wording, don't add rules. Protocol: `references/verification.md`. (This skill ships its own test material in `evals/` — maintainers rerun it after edits.)

## Output contract

Deliver, in order:

1. **The rewritten prompt** in a fenced block, ready to paste.
2. **Change log** — each change: what changed, which diagnosed failure it fixes, one-clause why.
3. **Deliberately unchanged** — anything that looks unusual but was kept, and why.

If the prompt is already sound, say so and recommend at most 1–2 minor changes. Do not rewrite for the sake of rewriting — length added without a diagnosis is a regression.

## Related skills

- `authoring-skills` — when the "prompt" is an Agent Skill (SKILL.md package). Self-contained without it.
- `managing-project-memory` — when the "prompt" is a CLAUDE.md / project memory file. Self-contained without it.
