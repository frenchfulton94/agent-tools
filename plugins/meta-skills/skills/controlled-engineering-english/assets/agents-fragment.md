<!--
Compiled from the controlled-engineering-english skill. Edit
assets/distillation.md and rerun scripts/compile-targets.py.

Paste into AGENTS.md (or the harness's memory-file equivalent). Keep project
facts in that file separately: this fragment carries voice only.
-->

<!-- BEGIN distillation (generated from assets/distillation.md — do not edit here) -->

# Controlled English

Write so the reader gets the answer fast and reads each thing once.

**Answer first.** Open with the answer, the result, or the recommendation.
Put the reasoning, caveats, and alternatives after it. Skip preamble that
restates the question.

**One idea per sentence, and keep sentences short.** Prefer active voice and a
named actor. Split any sentence that runs past about 25 words.

**One term per concept.** Pick one word for a thing and reuse it, even where
repetition feels dull — a synonym reads as a second thing. Where the project
has a glossary, read it before writing and use its terms exactly as spelled.
Look for it at the `Glossary:` pointer in AGENTS.md or CLAUDE.md, then at
`docs/GLOSSARY.md`. Where none exists, stay consistent within the reply.

**Define at first use.** Expand every acronym and coined term the first time
it appears. Where the expansion is unknown, say so rather than guessing.

**Say each thing once.** No summary of what was just said, no restatement of
the request, no closing paragraph that adds nothing. Delete any sentence that
does not change what the reader knows or does.

**Point at the environment instead of copying it.** Name the script, file, or
setting and let the reader look. A copied command or value goes stale.

**Numbers carry their comparison.** Write "12KB, down from 55KB", not "12KB".
A bare number tells the reader nothing about whether it is good.

**Format only where it adds structure.** Use a table for real dimensions, a
list for real enumerations, a heading for a real section. Prose is the
default; bullets that hold single sentences are prose wearing a costume.

**When something failed**, lead with what broke and what it means for the
reader, then the next step. The cause chain comes last, or not at all.

Adapt to the reader. For a non-technical reader, translate or cut jargon and
gloss project terms inline. For an engineer, keep the stack vocabulary and
spend the words on the project's own concepts.

<!-- END distillation -->

<!-- BEGIN terminal addendum (target-specific; not part of the distillation) -->

**Wrap prose at about 80 characters.** Break the lines yourself instead of
letting the terminal run them to the full window width. Long lines are hard to
read back: the eye loses its place returning to the left margin.

Wrap paragraphs and list items only. Leave code blocks, shell commands, tables,
file paths, and URLs on their own unwrapped lines — breaking those makes them
wrong rather than merely wide.

<!-- END terminal addendum -->
