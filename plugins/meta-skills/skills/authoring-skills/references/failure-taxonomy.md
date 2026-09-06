# Match the Form to the Failure

Contents:
- [Why form matters](#why-form-matters)
- [The taxonomy](#the-taxonomy)
- [Rationalization patterns and counters](#rationalization-patterns-and-counters)
- [Red flags in a draft skill](#red-flags-in-a-draft-skill)
- [Variance is a metric](#variance-is-a-metric)

## Why form matters

Every skill instruction has a form: prohibition, recipe, checklist, example, principle, or gate. Each form fixes one class of failure and can make another class worse. Most bloated, ineffective skills chose the wrong form and then compensated with volume and emphasis. Diagnose the failure class first; the form follows.

## The taxonomy

| Observed failure | Wrong fix (common) | Right fix |
|---|---|---|
| Agent skips a step under pressure ("tests take too long") | Longer explanation of why the step matters | A gate: a short, unambiguous rule placed before the step, plus a counter for the specific excuse observed |
| Output has the wrong shape or style | Prohibitions ("don't use bullets", "never preamble") | A positive recipe or template: state the shape you want; show one filled example. A recipe leaves nothing to negotiate — output matches the stated shape or it doesn't |
| Agent does the task a different way each run | More rules covering each variant seen | One canonical procedure with exact commands (lower the degrees of freedom) |
| Agent over-applies the skill to cases it shouldn't touch | Emphasis ("ONLY when...") | Explicit scope boundaries with one near-miss example of when *not* to apply it |
| Agent misses edge case it couldn't have known | General warnings | A gotchas entry: the specific environment fact that defies reasonable assumption, one line each |
| Agent ignores the instruction entirely | All-caps, repetition | Move it earlier, make it concrete and testable, and cut surrounding noise — buried rules get lost; on current models, shouted rules over-trigger |
| Agent asks the user things the skill already answers | More detail | Rephrase ambiguously-worded lines; ambiguity, not absence, causes the questions |
| Quality plateaus or drops as you add rules | Even more rules | Delete rules. Over-constrained skills suppress the model's judgment; remove and re-test |

Two structural cautions:

- **Nuance clauses reopen negotiation.** Appending "unless it matters" or "except when appropriate" to a working rule turns a settled instruction back into a judgment call and measurably increases variance. If an exception is real, state it as its own concrete rule.
- **Violating the letter is violating the spirit.** If testing shows agents complying technically while defeating the purpose, the fix is a recipe or gate that makes the purpose the only compliant reading — not an appeal to good faith.

## Rationalization patterns and counters

When a baseline run skips your process, capture the excuse verbatim — the excuse tells you exactly what sentence the skill needs. Common patterns:

| Excuse observed | Counter that works |
|---|---|
| "This case is simple, the full process is overkill" | "Simple cases use this process too; deciding a case is simple is part of the process, not a reason to skip it." |
| "I'll do X first, then come back to the process" | Place the gate before any action: "Before doing anything else, ..." |
| "The user seems in a hurry" | "Speed pressure is the situation this skill exists for; the short path is the skill." |
| "I already know what this will say" | "If the outcome is obvious, the process is fast. Run it." |
| "This is close enough to the required output" | A template with the exact required fields, so "close" is visibly incomplete |

Add counters only for excuses you have actually observed. Speculative counters are noise.

## Red flags in a draft skill

Any of these means stop and rediagnose:

- All-caps emphasis walls, or repeated MUST/NEVER/CRITICAL
- The description contains "first... then..." or numbered steps
- More than one prohibition without an adjacent "instead, do X"
- Rules added in response to imagined, never-observed failures
- The same guidance stated at equal depth in both SKILL.md and a reference file (a one-line inline digest pointing to the full reference is fine)
- A growing list of exception clauses on one rule
- Instructions telling the agent to reveal or transcribe its internal reasoning
- You cannot say, for a given line, which observed failure it prevents

## Variance is a metric

Run the same scenario several times (fresh context each time). When guidance lands, runs converge on the same shape. Five different interpretations across five runs means the wording is not binding — the fix is one concrete example or a tighter scope clause, not more rules. Track variance across edits: an edit that improves the average but widens the spread is a regression.
