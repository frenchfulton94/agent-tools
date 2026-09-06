# Prompt Pattern Library

Positive patterns for the rewrite step. Each: when to use, plus a template or worked example. Apply patterns the diagnosis calls for — not all of them.

Contents:
- [Explicit ask](#explicit-ask)
- [Motivation with constraint](#motivation-with-constraint)
- [Example blocks](#example-blocks)
- [Role line](#role-line)
- [XML content boundaries](#xml-content-boundaries)
- [Long-context layout](#long-context-layout)
- [Quote grounding](#quote-grounding)
- [Output contract](#output-contract)
- [Uncertainty grant](#uncertainty-grant)
- [Scope fence](#scope-fence)
- [Self-check closer](#self-check-closer)
- [Chaining](#chaining)

## Explicit ask

**When:** output is generic, shallow, or minimal.
Name the depth and features wanted; models calibrate effort to the ask.

> Weak: "Create an analytics dashboard."
> Strong: "Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to a fully-featured implementation."

## Motivation with constraint

**When:** a constraint looks arbitrary and gets violated in edge cases.
Attach the reason; reasons generalize to cases you didn't enumerate.

> Weak: "NEVER use ellipses."
> Strong: "The output is read aloud by a text-to-speech engine, so never use ellipses — the engine can't pronounce them."

## Example blocks

**When:** format, tone, or judgment is easier to show than describe; or instructions alone produce inconsistent output.
Use 1–5 examples: relevant to the real task, diverse enough to cover an edge case, and *exactly* what you want — models copy example details, including accidental ones (length, tone, structure). Wrap in tags when the prompt is complex:

```
<examples>
<example>
Input: Refund request, order #4412, outside 30-day window
Output: DENY — outside window. Offer store credit per policy 4.2.
</example>
<example>
Input: Refund request, damaged item, day 2
Output: APPROVE — damage claim within window. No escalation needed.
</example>
</examples>
```

Start with one example; add more only if output still varies.

## Role line

**When:** tone or domain focus drifts; building a persona-driven application.
One professional line in the system prompt: "You are a senior data engineer reviewing pipeline code." Skip theatrics ("world-renowned genius...") — over-constrained roles reduce helpfulness and add nothing.

## XML content boundaries

**When:** the prompt mixes instructions, context, data, and examples, and the model confuses them.
Tag the content types; use consistent, descriptive names; refer to tags in the instructions.

```
<instructions>Summarize the findings for an executive audience.</instructions>
<report>{{REPORT_TEXT}}</report>
```

Skip tags in simple prompts — headings and clear language carry small prompts fine.

## Long-context layout

**When:** prompt includes 20k+ tokens of documents or data.
Order: data first, instructions and question last (up to ~30% quality difference). Wrap multiple documents:

```
<documents>
  <document index="1">
    <source>q3_report.pdf</source>
    <document_content>...</document_content>
  </document>
</documents>

[instructions]
[question]
```

## Quote grounding

**When:** answers over long documents drift from the source or fabricate.

> "First, extract the quotes from the report most relevant to the question, word for word, into a quotes list. If none are relevant, write 'No relevant quotes found.' Then answer using only those quotes, citing them."

## Output contract

**When:** output shape varies or downstream code parses the response.
State the exact shape positively; show, don't prohibit. For machine-read output, give the schema and forbid extras in one line:

> "Return only a JSON object with keys `revenue` (string with units), `margin` (percentage string), `growth` (percentage string). Use null for metrics not stated in the report. No preamble, no markdown fences."

Match the prompt's own formatting to the desired output: prose prompts beget prose; markdown-heavy prompts beget markdown.

## Uncertainty grant

**When:** the model fabricates facts, citations, or numbers.

> "Analyze this data and identify trends. If the data is insufficient to support a conclusion, say so rather than speculating."

Pairs with: "Only use the provided documents; do not draw on outside knowledge" when source-boundedness matters.

## Scope fence

**When:** the model does too much (refactors while fixing, rewrites while editing) or too little (first item only).

> Too little: "Apply this formatting to every section, not just the first."
> Too much: "Fix the failing test. Don't refactor surrounding code, add features, or change public APIs beyond what the fix requires."

## Self-check closer

**When:** multi-step or high-stakes tasks where errors are costly.

> "Before finishing, verify: every requirement above is addressed, the code compiles, and each cited figure appears in the source. Fix anything that fails before responding."

One check, concretely stated. Don't stack multiple vague "double-check your work" lines.

## Chaining

**When:** a single prompt handles multiple stages badly (analysis then rewrite then verification), or intermediate output needs inspection.
Split into sequential prompts, each doing one thing; pass outputs forward. The most valuable link is a review stage — draft → critique → revise:

> Prompt 1: "Summarize this paper covering methodology, findings, and limitations."
> Prompt 2: "Review the summary above against the paper for accuracy and completeness; list specific problems."
> Prompt 3: "Revise the summary to fix exactly the problems listed."

Costs latency; buys accuracy and debuggability. Use when a single prompt is demonstrably inconsistent, not by default.
