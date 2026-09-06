# Verifying a Prompt Rewrite

Contents:
- [Tier 1: cold read](#tier-1-cold-read)
- [Tier 2: A/B testing](#tier-2-ab-testing)
- [Writing assertions](#writing-assertions)
- [Reading the results](#reading-the-results)
- [Without any tooling](#without-any-tooling)

## Tier 1: cold read

Always do this; it needs no tooling.

1. Re-read the rewritten prompt as the model will receive it — alone, with no conversation context. Anywhere a context-free reader would ask a question, the model will guess.
2. Check the ledger both ways: every diagnosed failure has a change addressing it; every change traces to a diagnosed failure. Changes without diagnoses are decoration — cut them.
3. Simulate 2–3 realistic inputs mentally, including one edge case, against the new wording. Look for instructions that collide, scopes that overlap, and examples that contradict a rule.
4. Confirm no Step 4 anti-pattern survived (prefill, thinking scaffolds, reasoning-echo, caps, sampling params). If code execution is available, `scripts/lint_prompt.ts` does this mechanically.

## Tier 2: A/B testing

When you can run clean-context agents (subagents, fresh sessions, or an eval harness):

1. Fix 2–3 realistic test inputs before testing — varied phrasing/formality, at least one edge case (ambiguous request, malformed data, out-of-scope ask).
2. For each input, run the **old** prompt and the **new** prompt in separate, clean contexts. 2–3 repetitions each when affordable — single runs can't separate prompt effect from luck.
3. Grade every run against written assertions (below), PASS/FAIL with quoted evidence from the output. No benefit of the doubt.
4. For subjective quality, add a blind comparison: show both outputs to a fresh judge without labels; ask which better satisfies the user's goal and why.

Clean context is the point — a session that has seen the old prompt, the diagnosis, or the other output is contaminated as a judge and as a test subject.

## Writing assertions

Derive assertions from the diagnosis: each diagnosed failure becomes at least one assertion that would have FAILED on the old prompt.

- Observable and specific: "response contains valid JSON parseable by `json.loads`", "every section heading is followed by ≥2 sentences", "response declines to invent figures for the missing quarter".
- Not vague ("output is better"), not brittle ("uses exactly the phrase 'Total Revenue'").
- Keep a couple of regression assertions for things the old prompt did *well*, so the rewrite doesn't trade one failure for another.

## Reading the results

- New passes where old failed → the rewrite's demonstrated value.
- Both pass → assertion doesn't measure the change; replace it.
- Both fail → the problem isn't wording, or the assertion is broken.
- **Intermittent** (same prompt, same input, different reps disagree) → remaining ambiguity. Fix with one example or one scope clause; adding rules on top of ambiguity increases variance.
- New prompt wins but is much longer → try a shorter variant; on current models leaner frequently matches or beats longer. Keep the shortest version that holds the wins.

## Without any tooling

In a plain chat with no subagents:

- Run the strongest available comparison: paste the new prompt into a fresh conversation with one test input; compare against a saved output of the old prompt on the same input, graded with the same written assertions.
- Blind yourself as far as possible: write the assertion verdicts for both outputs before deciding which you prefer overall.
- State honestly in your report which tier was used — "verified by cold read only" is a legitimate, labeled result, not a failure.
