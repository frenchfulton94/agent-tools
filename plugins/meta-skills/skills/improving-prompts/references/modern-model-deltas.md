# Modern Model Deltas

What changed in current-generation Claude models (Claude 4.5+, Sonnet 4.6/5, Opus 4.6–4.8, Fable/Mythos 5) versus the models most prompt-engineering advice was written for — and how to migrate prompts.

Contents:
- [Removed: assistant prefill](#removed-assistant-prefill)
- [Removed: manual thinking budgets](#removed-manual-thinking-budgets)
- [Removed: sampling parameters](#removed-sampling-parameters)
- [New refusal: reasoning extraction](#new-refusal-reasoning-extraction)
- [Behavior shift: emphasis inflation backfires](#behavior-shift-emphasis-inflation-backfires)
- [Behavior shift: literal instruction following](#behavior-shift-literal-instruction-following)
- [Behavior shift: over-prescription degrades output](#behavior-shift-over-prescription-degrades-output)
- [Effort and adaptive thinking](#effort-and-adaptive-thinking)
- [Tokenizer and budget notes](#tokenizer-and-budget-notes)
- [What did not change](#what-did-not-change)

## Removed: assistant prefill

**What changed:** Prefilling the assistant's response (seeding the turn with `{` or "Here is the JSON:") is no longer supported — requests with a prefilled final assistant turn return an error on Claude 4.6+ and Fable/Mythos 5.

**Detect:** API code adding a trailing `assistant` message; prompt docs saying "begin your response with...".

**Migrate:**
- Structured output needs → the API's structured outputs / JSON schema feature, or strict tool definitions.
- Skip-the-preamble needs → a direct instruction: "Respond with only the JSON object, no preamble, no markdown fences."
- Continuation needs → move the partial text into the user turn.

Before: `messages=[..., {"role": "assistant", "content": "{"}]`
After: instruction "Return only valid JSON matching this schema: ..." (or `output_config` with a JSON schema).

## Removed: manual thinking budgets

**What changed:** Manual extended-thinking budgets (`budget_tokens`) are deprecated on 4.6-era models and rejected on Opus 4.7+, Sonnet 5, and Fable 5. Adaptive thinking plus the `effort` parameter replaced them, and reliably performs better. On Fable 5, adaptive thinking is always on; on Sonnet 5 it defaults on.

**Detect:** `thinking: {type: "enabled", budget_tokens: N}`; elaborate `<thinking>`/`<answer>` scaffolds in prompts.

**Migrate:** `thinking: {type: "adaptive"}` and choose `effort` (see [Effort](#effort-and-adaptive-thinking)). In prose, replace manual chain-of-thought scaffolds with at most a brief targeted nudge ("Consider the donor's history before drafting"). Manual CoT remains acceptable only where platform thinking is unavailable.

## Removed: sampling parameters

**What changed:** Non-default `temperature`, `top_p`, or `top_k` return an error on Sonnet 5 (and this direction is spreading). Steer variety and tone with instructions instead.

**Migrate:** delete the parameters; for creative variety, ask for it ("Propose 4 distinct directions before committing to one").

## New refusal: reasoning extraction

**What changed:** On Fable 5, instructions telling the model to echo, transcribe, or explain its internal reasoning as response text can trigger a `reasoning_extraction` refusal (and fallbacks to other models in some deployments).

**Detect:** "show your thinking", "explain your chain of thought", "walk me through your internal reasoning", "output your thought process".

**Migrate:** ask for the result plus a *stated* rationale: "Give your answer, then briefly justify it with the key evidence." Read structured thinking blocks via the API if you need reasoning visibility. Audit skills and system prompts for show-your-thinking scaffolds when migrating to Fable 5.

## Behavior shift: emphasis inflation backfires

**What changed:** Older models under-triggered, so prompts accumulated "CRITICAL: You MUST use this tool whenever...". Current models take that emphasis literally and **over**-trigger — the tool fires when it shouldn't, the rule applies where it shouldn't.

**Migrate:** normal phrasing. "Use this tool when it would enhance your understanding" replaces "Default to using this tool". "Use X when Y" replaces "CRITICAL: ALWAYS use X". Positive examples of desired behavior beat negative instructions. If a prompt reads like it's shouting, that's a redesign signal, not a style choice.

## Behavior shift: literal instruction following

**What changed:** Current models follow instructions more literally and generalize less silently. An instruction demonstrated on one section will be applied to that section only, unless scope is stated.

**Migrate:** state scope explicitly ("Rename the variable everywhere it appears, not only in this file"). State when rules apply and when they don't. This also means one clear sentence now does the work that a page of repetition did before — repetition is no longer insurance, it's noise.

## Behavior shift: over-prescription degrades output

**What changed:** Prompts and skills tuned for older models are often too prescriptive for current ones and measurably degrade output quality. Default model behavior is frequently better than the micro-managed behavior the old prompt enforces.

**Migrate:** when improving an old prompt, test *removal*: strip instructions that enforce things the model now does well by default (formatting hygiene, effort, step ordering) and compare. Keep only instructions that fix a failure you can still observe. Scope-limiting additions are still useful against over-engineering ("Fix the bug; don't refactor surrounding code or add features beyond the task").

## Effort and adaptive thinking

For prompts that ship with an API configuration:

- **Effort is the main quality lever.** Opus 4.8: start at `xhigh` for coding/agentic work, minimum `high` for intelligence-sensitive work; `max` can overthink. Fable 5: `high` default, `xhigh` for the hardest work; lower tiers still perform well. Sonnet 5: `high` default.
- With high effort, allow a large output budget (start ~64k tokens for agentic coding).
- Models at low effort or with thinking disabled reach for tools less — add an explicit nudge if tool use matters.
- When thinking is off, some models are sensitive to the word "think" — prefer "consider", "evaluate", "reason through" in prose.

## Tokenizer and budget notes

- Sonnet 5 uses a new tokenizer producing ~30% more tokens for the same text — revisit `max_tokens` limits copied from older configs (risk: truncation at `stop_reason: max_tokens`).
- Long-context behavior is much improved, but placement still matters: longform data at the top, query at the end (up to ~30% quality difference on long-context tasks); quote-extraction grounding still helps above ~20k tokens.

## What did not change

The durable core that survives every model generation: explicit beats implied; motivation ("why") generalizes better than bare rules; relevant, diverse examples steer format- and judgment-sensitive tasks; XML tags cleanly bound content types in complex prompts; a one-line role in the system prompt helps tone and domain focus; direct action verbs get action ("Change this function", not "Can you suggest changes?"); permission to say "I don't know" reduces fabrication; a closing self-check catches errors; and chaining separates stages that need separate attention.
