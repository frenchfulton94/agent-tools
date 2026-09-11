# frontend

The web application stack this team builds on. The set leans SvelteKit — three of the skills are
Svelte-specific and the rest are the layers around them.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install frontend@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/frontend
claude plugin validate plugins/frontend --strict
```

## Components

| Component | Shape | Layer |
|---|---|---|
| `bits-ui` | Skill | Headless Svelte 5 components — building, styling, and wrapping them accessibly |
| `layerchart` | Skill | Charts and data visualization in Svelte/SvelteKit (LayerChart v2) |
| `styling-with-tailwind` | Skill | Tailwind CSS v4 — utilities, variants, container queries, `@theme` tokens |
| `bem-css` | Skill | BEM class naming for the CSS Tailwind does not cover |
| `feature-sliced-design` | Skill | Where code belongs — FSD layers under `src/lib`, thin `src/routes` |
| `using-paraglide-js` | Skill | Internationalization with Paraglide JS and inlang message files |
| `internationalized-date-time` | Skill | Dates, times, zones, and calendars with `@internationalized/date` |
| `sanitizing-untrusted-html` | Skill | DOMPurify, including server-side on jsdom |

## Two boundaries worth knowing

**Against `typescript`.** That plugin is what the type system reaches — the compiler, the test
runner, the bundler, and Drizzle. This one is what renders. `tsconfig`, Vitest, and database
schema questions go there.

**Against `security`.** `sanitizing-untrusted-html` is here rather than in `security` because it
is a library-wiring task in application code — which DOMPurify config, which hooks, verified
against known bypasses. `security` reviews a diff or a repository against OWASP and cites it; it
does not write the sanitizer call.

## License

MIT.
