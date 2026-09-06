# Evaluating Skills

Contents:
- [What to test and when](#what-to-test-and-when)
- [Building behavior test cases](#building-behavior-test-cases)
- [The A/B protocol](#the-ab-protocol)
- [Grading](#grading)
- [The trigger battery](#the-trigger-battery)
- [Description optimization loop](#description-optimization-loop)
- [Iteration rules](#iteration-rules)
- [Manual fallbacks without subagents](#manual-fallbacks-without-subagents)

## What to test and when

Two independent questions, tested separately:

1. **Does it fire?** (trigger accuracy — tests the description)
2. **Does it help?** (behavior change vs. baseline — tests the body)

A skill can pass one and fail the other. Test triggering with the [trigger battery](#the-trigger-battery); test behavior with the [A/B protocol](#the-ab-protocol). For a new skill, run behavior tests first — there is no point tuning the description of a skill that doesn't help.

## Building behavior test cases

Start with 2–3 cases; don't over-invest before first results.

- **Vary phrasing and formality.** One casual ("hey can you clean up this csv"), one precise (full paths, exact steps).
- **Include at least one edge case:** malformed input, ambiguous instructions, or a request the skill should decline or route elsewhere.
- **Use realistic context:** real file paths, real column names, a plausible backstory. "Process this data" is too vague to test anything.

Each case has: a prompt, any input files, and a short list of **assertions** — written before running, refined after the first run. Good assertions are observable and specific: "output is valid JSON", "chart has labeled axes", "includes at least 3 recommendations". Weak: "output is good" (vague), "uses exactly the phrase X" (brittle). Not everything needs an assertion — style and "feels right" go to human review instead.

## The A/B protocol

Run each case twice per repetition: once **with** the skill available, once **without** (baseline). When improving an existing skill, the baseline is the old version.

- **Clean context per run.** Each run starts fresh — a subagent or a new session — with no memory of other runs. Contaminated context invalidates the comparison.
- Per run provide: the skill (or nothing for baseline), the test prompt, input files, an output location.
- **2–3 repetitions per configuration** when feasible; a single rep can't distinguish skill effect from luck.
- Record what's observable: assertions passed, wall time, output size or token counts if your environment reports them.

Interpretation:
- Assertions that pass in **both** configurations measure nothing about the skill — replace them.
- Assertions that fail in both indicate a broken assertion or a too-hard case — fix the test.
- Assertions that pass with the skill and fail baseline are the skill's demonstrated value — protect them from regressions in later edits.
- Weigh costs: +50 points pass rate for +13 seconds is worth it; +2 points for double the tokens usually isn't.

## Grading

- Grade each assertion PASS/FAIL **with quoted evidence from the output**. No benefit of the doubt: a "Summary" heading followed by one vague sentence is a FAIL on "includes a summary".
- Use verification scripts for mechanical checks (valid JSON, row counts, file exists) — more reliable than judgment.
- For subjective qualities, use a **blind comparison**: present both outputs to a fresh judge (subagent or fresh session) without saying which had the skill; ask which is better organized, more usable, more polished, and why. Blindness removes the bias toward the version that "should" win.
- Also grade the assertions themselves each round: too easy, too brittle, unverifiable? Fix the test suite as you fix the skill.

## The trigger battery

Build ~20 queries: 8–10 that **should** trigger the skill, 8–10 that should **not**.

- Strong positives are queries where the skill helps but the connection isn't obvious — symptom phrasings, no domain keywords, realistic noise (file paths, "my manager asked me to...", typos).
- Strong negatives are **near-misses**: same keywords, different need (for a CSV-analysis skill: "update the formulas in my Excel budget"). Distant negatives ("write a fibonacci function") test nothing.
- If sibling skills exist in the same environment, include queries that belong to the siblings — misrouting to or from a neighbor is the most common real-world trigger failure.

To run: give a clean-context agent the skill *descriptions only* (target plus several distractors), one query, and ask which skill applies or "none". Repeat per query, ideally 3 reps. Score should-trigger and should-not accuracy separately. A note on realism: agents consult skills mainly for tasks beyond their easy reach — a trivial one-step query may not trigger even a perfectly matching description, so don't use trivial queries as positives.

## Description optimization loop

When trigger accuracy is low:

1. Split the battery ~60% train / 40% validation, keeping the positive/negative mix in both. Freeze the split.
2. Revise the description using **train failures only**. Generalize from failures to broader intent categories — do not paste failed queries' keywords into the description; that's overfitting.
3. Re-run the full battery. Track validation accuracy per iteration.
4. Stop after ~5 iterations; keep the iteration with the **best validation score** (often not the last).
5. Sanity-check the winner on 5–10 fresh queries never used during tuning.

Keep the description within limits (≤1024 chars) — it grows during optimization; re-check every round.

## Iteration rules

- Revise the description only from trigger evidence; revise the body only from A/B evidence. Don't cross the streams.
- **Generalize from failures** — fix the underlying issue, not the specific test case.
- **Intermittent failures mean ambiguity.** If a case passes some reps and fails others, the instructions permit multiple readings: add one example or one scope clause, not more rules.
- **Plateau means over-constraint.** If pass rates stall while the skill grows, delete instructions and re-test; leaner frequently wins on current models.
- If every run reinvents the same helper code, move that code into `scripts/` — reliability plus token savings.
- Stop when assertions pass consistently, human feedback comes back empty, or an iteration produces no measurable change.

## Manual fallbacks without subagents

Every step above has a no-tooling equivalent, weaker but real:

- **Baseline:** recall or reproduce one real failed attempt at the task; write down what went wrong before drafting.
- **Trigger battery:** read the description alone (cover the body); for each of your 20 queries, honestly judge "would this description fire?" Misses still count — revise and re-judge.
- **A/B:** apply the skill to one test case yourself in a fresh conversation, then compare against a prior no-skill attempt using the same written assertions and the same no-benefit-of-the-doubt grading.
- **Blind comparison:** put both outputs side by side, hide their labels, and grade against the assertion list before revealing which is which.
