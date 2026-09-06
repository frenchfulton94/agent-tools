---
name: authoring-skills
description: Creates, audits, improves, and evaluates Agent Skills — SKILL.md packages with references, scripts, and evals. Use when the user wants to build a new skill, review or fix an existing one, make a skill trigger reliably, shrink a bloated skill, port a repeated workflow or checklist into a skill, or test whether a skill actually changes agent behavior. Also use when a skill misfires — agents ignore it, follow only its description, or over-trigger on it — and when the user says they keep re-explaining the same multi-step process or workflow every session, even if they never use the word "skill". For plain prompts or CLAUDE.md memory files, prefer their dedicated skills.
license: MIT
---

# Authoring Skills

Create, audit, improve, and evaluate Agent Skills. A skill is a directory with a `SKILL.md` (YAML frontmatter + instructions) and optional `references/`, `scripts/`, and `assets/`. The description loads into every session; the body loads only when triggered — so the description determines whether the skill fires, and the body determines whether it works.

## Should this even be a skill?

Route the content before authoring anything. Skills are for repeated, multi-step know-how — other homes fit other content better:

| The content is... | Put it in... |
|---|---|
| A one-line project fact or convention | The project memory file (CLAUDE.md), not a skill |
| A rule that must happen every time, no exceptions | A hook — see `authoring-hooks` (memory and skills are advisory; hooks are enforced) |
| Isolated, verbose work where only the summary matters | A subagent — see `authoring-subagents` |
| A set of the above, packaged for distribution | A plugin — see `authoring-plugins` |
| Guidance tied to specific files or paths | A path-scoped rules file that loads with those files |
| A repeated multi-step procedure, technique, or reference | A skill — continue below |

If the user asks for enforcement ("make Claude always do X"), recommend a hook and explain that instruction files can be ignored under pressure; a hook cannot.

## Spec in brief

Full field tables and the manual checklist are in `references/spec.md`. The hard limits, plus the conventions that break discovery:

- `name`: ≤64 chars, lowercase `a-z0-9-` only, no leading/trailing/double hyphens, must match the directory name, no reserved words ("claude", "anthropic"), no XML tags. Prefer gerund form: `processing-pdfs`, not `pdf-helper`.
- `description`: required, ≤1024 chars, no XML tags. Convention, not a rejection: third person ("Analyzes...", not "I analyze") — mixed point of view hurts discovery.
- Body: keep under 500 lines (~5k tokens); split into `references/` before you approach that.
- `references/`: linked one level deep from SKILL.md only (nested chains get partially read). Files over ~100 lines start with a table of contents. Tell the reader *when* to load each file ("Read `references/<topic>.md` if the API returns non-200"), not just that it exists.
- `scripts/`: executed, not loaded — their tokens are free. State whether to run or read each one ("Run `scripts/<name>.py`" vs "See `scripts/<name>.py` for the algorithm"). Keep scripts dependency-free or pin versions, and never make them prompt interactively.
- Portability: skip experimental or product-specific frontmatter unless the skill targets one product. Phrase tooling as capability-conditional: "If you can execute code, run the script; otherwise apply the checklist manually."

## The description is half the skill

The agent decides whether to load your skill from the description alone. Two failure modes, opposite fixes:

**Never fires** — the description is vague or implementation-focused. Write what the skill does (third person) plus a "Use when..." clause packed with user-intent triggers, including symptom phrasings where the user never names the domain ("even if they don't mention CSV").

**Fires but gets skipped** — the description summarizes the workflow, so the agent follows the summary and never reads the body. This is an observed failure: a description saying "review between tasks" produced one review when the body required two. Describe *when to use*, never *how it works*. If your description contains sequenced steps, rewrite it.

```yaml
# Weak: vague, and leaks workflow
description: Helps with CSVs by first profiling columns, then cleaning, then charting.

# Strong: capability + dense triggers, zero workflow
description: Analyzes CSV and tabular data files — summary statistics, derived
  columns, charts, cleaning. Use when the user has a CSV, TSV, or spreadsheet
  and wants to explore, transform, or visualize it, even if they don't say
  "CSV" or "analysis".
```

## Authoring workflow

Ground the skill in an observed failure, not an imagined one. Skills written from imagination produce generic advice the agent already knows.

1. **Baseline.** Run the target task without the skill (a fresh session or subagent if available; otherwise recall or reproduce a real failed attempt). Capture what actually went wrong — verbatim, including any excuses the agent gave for skipping steps.
2. **Draft minimal.** Write the smallest instruction set that counters the observed failure. Apply the leanness test to every line: "Would the agent get this wrong without it?" If not, cut it — the agent already knows what a PDF is.
3. **Match the form to the failure.** Prohibitions fix skipped steps; they backfire on output-shaping problems, where a positive recipe or template wins. Wrong-form fixes make skills longer and worse. Consult `references/failure-taxonomy.md` before choosing.
4. **Set the degrees of freedom.** Fragile, consistency-critical operations get exact commands ("Run exactly this; do not add flags"). Open-ended tasks get principles and a why. Most bad skills over-constrain the open field and under-constrain the narrow bridge.
5. **Close observed loopholes only.** When testing reveals a rationalization, add its counter. Do not pre-emptively enumerate loopholes — speculative rules are noise that dilutes the real ones.

For starting skeletons (technique, reference, and workflow skills), use `references/templates.md`.

## Writing for current models

Current Claude models follow instructions more literally and need less forcing than the models much existing skill advice was written for. Older-style skills actively degrade their output.

- One brief instruction beats an enumeration of cases; state scope explicitly ("every section, not just the first").
- Drop emphasis inflation. "CRITICAL: You MUST..." causes over-triggering now; "Use X when Y" works. All-caps walls are a signal the skill needs redesign, not louder wording.
- Prefer positive recipes ("Write flowing prose paragraphs") over prohibitions ("Don't use bullets").
- Never instruct an agent to echo, transcribe, or explain its internal reasoning in the response — on newer models this can trigger refusals. Ask for a result plus a brief stated rationale instead.
- Explain why once, briefly. A rule with a reason survives novel situations; a bare rule invites literal-minded workarounds.
- When improving an old skill, treat deletion as a first-class fix. If quality plateaus while you add rules, the skill is over-constrained — remove instructions and re-test.

## Evaluating

Verify at the highest tier your environment supports. Full protocols, grading rules, and the description-optimization loop are in `references/evaluation.md`.

- **Tier 0 — lint.** If you can execute code, run `bun scripts/validate_skill.ts <skill-dir> --strict`. Otherwise apply the manual checklist in `references/spec.md`.
- **Tier 1 — cold read.** Re-read the skill as a stranger with zero conversation context. Read the description alone: would you know when to fire it — and would you wrongly believe you know the whole workflow? Then simulate 2–3 near-miss requests and check they wouldn't trigger it.
- **Tier 2 — measured.** If you can run clean-context agents (subagents or fresh sessions): (a) a trigger battery of ~8–10 should-trigger and 8–10 should-not queries, where the valuable negatives are near-misses from adjacent domains; (b) an A/B run of the task with and without the skill, graded against written assertions with quoted evidence — no benefit of the doubt. Inconsistent results across reps mean ambiguous instructions: add one example or scope clause, not more rules. (This skill ships its own test material in `evals/` — maintainers rerun it after edits.)

## Auditing an existing skill

Work through in order; report findings before editing anything.

- [ ] Frontmatter passes spec lint (name rules, description ≤1024, no XML tags)
- [ ] Description states capability + triggers, and contains no workflow steps
- [ ] Description read alone would fire on the intended requests and not on near-misses
- [ ] Body under 500 lines; anything reference-shaped moved to `references/`
- [ ] No all-caps emphasis walls or MUST/NEVER inflation
- [ ] No instruction to reveal or transcribe internal reasoning
- [ ] Prohibitions checked against the failure taxonomy (recipe needed instead?)
- [ ] Every file in `references/`, `scripts/`, and `assets/` is referenced from SKILL.md with a when-to-load or run condition (`evals/` is exempt — it's for the skill's maintainers, not its users)
- [ ] Reference files over ~100 lines start with a table of contents
- [ ] Deletion pass, always last: for each line, "would the agent get this wrong without it?" Cut what fails.

## Output contract

- **Creating:** deliver the full file tree with every file's content, plus a short rationale for what went inline vs. `references/`, and a trigger battery in `evals/` so the skill ships testable.
- **Auditing:** deliver a findings report keyed to the checklist above first, then the proposed diffs, each with a one-line why. If the skill is already sound, say so and stop — do not invent findings.

## Related skills

- `improving-prompts` — for prompts that aren't skills (system prompts, agent instructions). This skill is self-contained without it.
- `managing-project-memory` — for CLAUDE.md and project memory files. Self-contained without it.
- `authoring-hooks` — for enforced behavior a skill can only advise. Self-contained without it.
- `authoring-subagents` — for work that belongs in its own context window. Self-contained without it.
- `authoring-plugins` — for packaging skills and other components for distribution. Self-contained without it.
