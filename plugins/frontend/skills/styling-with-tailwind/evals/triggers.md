# Trigger Battery

Twenty queries for testing whether the description fires correctly. Run by giving
a clean-context agent the skill _descriptions only_ — this skill plus distractors —
one query at a time, asking which applies or "none". Score positives and negatives
separately.

Sibling skills in this environment that make good distractors: `frontend-design`
(visual direction, typography, aesthetic choices), `authoring-skills`, and
`writing-typescript`.

## Should trigger (10)

Several deliberately avoid the words "Tailwind" or "v4" — the skill has to fire
on the symptom, since that is how these arrive in practice.

| #   | Query                                                                                    |
| --- | ---------------------------------------------------------------------------------------- |
| P1  | "Build me a responsive pricing card with a gradient header and dark mode support."       |
| P2  | "My shadows look way smaller than they did before the upgrade and I can't work out why." |
| P3  | "Migrate this project from Tailwind 3 to 4."                                             |
| P4  | "The focus ring on my buttons disappeared after I bumped dependencies."                  |
| P5  | "Why is `bg-${color}-500` not producing any CSS in my React component?"                  |
| P6  | "My borders are showing up black instead of light gray everywhere."                      |
| P7  | "How do I add a custom brand color so I can use `bg-brand` in my markup?"                |
| P8  | "`@apply` throws an error inside my Vue component's style block."                        |
| P9  | "Set up a class-based dark mode toggle instead of following the OS setting."             |
| P10 | "Style this list so each row highlights when the checkbox inside it is checked."         |

## Should not trigger (10)

Near-misses. Each shares vocabulary or surface with the positives but wants
something else.

| #   | Query                                                                | Belongs to                    |
| --- | -------------------------------------------------------------------- | ----------------------------- |
| N1  | "What font pairing would suit a fintech dashboard?"                  | frontend-design               |
| N2  | "Make this landing page feel less generic and more editorial."       | frontend-design               |
| N3  | "Pick a colour system and type scale for our marketing site."        | frontend-design               |
| N4  | "Write a skill that captures our code review checklist."             | authoring-skills              |
| N5  | "Convert this Bootstrap 4 navbar to Bootstrap 5."                    | neither — different framework |
| N6  | "My CSS grid rows collapse when a child overflows. Why?"             | plain CSS debugging           |
| N7  | "Set up PostCSS with cssnano for this project."                      | build tooling, no Tailwind    |
| N8  | "Explain how CSS cascade layers work."                               | CSS concepts                  |
| N9  | "Refactor this React component to use a reducer."                    | React, styling irrelevant     |
| N10 | "Our design system needs documented spacing tokens — write the doc." | documentation                 |

N5 and N7 are the sharpest tests: both sit in the same neighborhood (utility CSS
framework migration; PostCSS configuration) without being about Tailwind.

## Scoring

Record should-trigger and should-not accuracy separately across ~3 repetitions.
A trivial one-step query may not fire even a well-written description, so do not
read a single miss on a simple positive as a description failure.

If accuracy is low, revise using train-split failures only, generalize to intent
categories rather than pasting query keywords into the description, and keep the
iteration with the best validation score.
