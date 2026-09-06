# Install

## Read this first if the skill lives inside a Tailwind project

Tailwind scans **every** file in a project for class names, skipping only
`.gitignore`d paths, `node_modules`, binaries, CSS files, and lock files.
Markdown is not skipped, and Tailwind does not care that a class name sits in a
documentation table or a fenced code block — it reads all source as plain text.

This skill's reference files are dense with real class names by design. Dropped
into a Tailwind repo unexcluded, every one of them becomes a generated rule in
the production bundle: on the order of 150+ utilities and tens of kilobytes of
CSS that no page actually uses.

Add one line to the CSS entry file, pointing at wherever the skill is installed:

```css
@import 'tailwindcss';

@source not '../.claude';
```

The path is relative to the stylesheet, and excluding the directory covers this
file too. Adjust it to match the install location — `../.agents`, `../docs`, or
whatever the project uses.

Verify with `@source not` in place: rebuild, then grep the output CSS for a class
that appears in the skill's docs but nowhere in the application. `block-lh` and
`inline-md` are good canaries — both are real stock utilities present in these
references, and neither is plausible in application code. Pick a canary that is a
genuine stock utility; something like `tab-github` only exists once you define
`--tab-size-github`, so its absence proves nothing.

Two alternatives, if excluding by path is awkward:

- Install the skill outside the project directory entirely.
- Add it to `.gitignore`, which Tailwind already honors.

The same trap applies to anything else in the repo that documents class names:
component library READMEs, Storybook MDX, design-system notes, changelogs.

## Layout

```
styling-with-tailwind/
├── SKILL.md                          entry point
├── references/
│   ├── v3-to-v4-migration.md         rename, removal, behavioral-change tables
│   ├── variants.md                   all built-in variants and state patterns
│   └── theme-and-utilities.md        theme namespaces, scales, custom utilities
├── scripts/
│   └── check_tailwind_v4.py          v3-era syntax detector (stdlib only)
└── evals/                            trigger battery and A/B cases (maintainers)
```

## Checking your own work

```
python3 scripts/check_tailwind_v4.py src/**/*.tsx src/app.css
```

Severities: `BROKEN` generates no CSS, `SILENT` compiles at a different size or
color than intended, `CHECK` is a changed default worth confirming.

To find documentation files that are inflating a bundle:

```
python3 scripts/check_tailwind_v4.py --docs-audit README.md docs/*.md
```
