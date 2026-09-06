# Agent Skill Specification Reference

Contents:
- [Directory layout](#directory-layout)
- [Frontmatter fields](#frontmatter-fields)
- [Name rules](#name-rules)
- [Description rules](#description-rules)
- [Size and structure limits](#size-and-structure-limits)
- [Directory semantics](#directory-semantics)
- [Portability guidance](#portability-guidance)
- [Manual validation checklist](#manual-validation-checklist)

## Directory layout

```
skill-name/
├── SKILL.md      # Required: YAML frontmatter + Markdown instructions
├── references/   # Optional: docs loaded on demand
├── scripts/      # Optional: executable code (runs without loading into context)
├── assets/       # Optional: templates/resources used in output, never loaded
└── evals/        # Optional convention: test cases and trigger queries
```

Only `SKILL.md` is required. Use forward slashes in all paths, relative to the skill root.

## Frontmatter fields

| Field | Required | Constraint |
|---|---|---|
| `name` | Yes | ≤64 chars; see [Name rules](#name-rules) |
| `description` | Yes | ≤1024 chars, non-empty; see [Description rules](#description-rules) |
| `license` | No | License name or path to a bundled license file; keep short |
| `compatibility` | No | 1–500 chars; environment requirements. Most skills don't need it |
| `metadata` | No | Arbitrary string→string map; use unique keys |
| `allowed-tools` | No | Space-separated pre-approved tools. Experimental; support varies by product — omit for portable skills |

Some products add further fields (argument hints, invocation controls, model/effort overrides, forked execution). They are ignored elsewhere; only add them when the skill deliberately targets that product, and keep the skill functional without them.

## Name rules

- Lowercase letters, digits, hyphens only (`a-z`, `0-9`, `-`)
- No leading or trailing hyphen; no consecutive hyphens (`--`)
- Must match the parent directory name exactly
- No XML tags
- No reserved words: `claude`, `anthropic` (some surfaces reject these; keep the brand word in the description instead, where it is allowed)
- Prefer gerund form describing the activity: `processing-pdfs`, `analyzing-spreadsheets`, `writing-documentation`
- Avoid vague names (`helper`, `utils`, `tools`) and bare generic nouns (`documents`, `data`)

Valid: `pdf-processing`, `data-analysis`, `code-review`
Invalid: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing` (double hyphen), `claude-md-fixer` (reserved word)

## Description rules

- ≤1024 chars (re-check after every edit — descriptions grow during optimization)
- Third person ("Analyzes...", not "I analyze..." or "You can use this to...")
- No XML tags
- Formula: *what it does* + *"Use when..."* triggers written as user intent, including symptom triggers where the user never names the domain
- Never include sequenced workflow steps — agents may follow the description instead of reading the body
- Put the most important use case first: some surfaces truncate long descriptions in their skill listing

## Size and structure limits

| Level | What loads | Budget |
|---|---|---|
| Metadata | `name` + `description`, every session | ~100 tokens |
| Body | SKILL.md on trigger | <500 lines / ~5k tokens |
| Resources | `references/` on demand; `scripts/` executed only | Unlimited on disk; pay per read |

Practical notes:
- A loaded skill body stays in context for the rest of the session — every line is a recurring cost.
- Some products truncate re-injected skill bodies after compaction (keeping the start), so put the most important instructions near the top of SKILL.md.

## Directory semantics

**references/** — loaded into context when needed.
- Link each file from SKILL.md with a *condition*: "Read `references/api-errors.md` if the API returns a non-200 status."
- One level deep from SKILL.md only. Agents may preview nested files with a partial read and act on incomplete information.
- Files over ~100 lines start with a table of contents (partial reads then still see the map).
- Split by domain (`references/finance.md`, `references/sales.md`) so only relevant content loads.
- Each fact has one authoritative home. A deliberate brief digest in SKILL.md that points to the authoritative reference is good progressive disclosure; restating reference content at equal depth is duplication.

**scripts/** — executed, not loaded; output enters context, source does not.
- Make execution intent explicit: "Run `bun scripts/x.ts`" vs "See `scripts/x.ts` for the algorithm."
- Never prompt interactively (agents run non-interactive shells; a blocked prompt hangs forever). Take input from flags, env vars, or stdin.
- Document with `--help`; keep its output short (it enters context).
- Error messages state what went wrong, what was expected, what to try.
- Structured output (JSON/CSV) over prose; data on stdout, diagnostics on stderr; bounded output size (harnesses truncate long tool output).
- Handle errors inside the script rather than failing and leaving recovery to the agent.
- No unexplained magic numbers — justify each constant with a comment.
- Don't assume packages are installed: use stdlib, or pin versions and state the install command in SKILL.md.

**assets/** — files used in output (templates, boilerplate, images). Never loaded into context; copied or referenced by the work product.

## Portability guidance

To keep a skill working across Claude Code, Claude.ai, and Cowork:

- Frontmatter: `name`, `description`, optionally `license`. Nothing product-specific.
- Never hard-require code execution or subagents. Phrase as capability-conditional: "If you can execute code, run `scripts/validate.py`; otherwise apply the checklist below."
- Scripts are accelerators, not dependencies: every script check must also exist as a manual checklist in a reference file.
- Network access varies by surface (none on the API, restricted on claude.ai). Skills requiring downloads should say what to do when offline.
- Refer to MCP tools by fully qualified name (`ServerName:tool_name`) and treat their absence as normal.

## Manual validation checklist

The no-code-execution equivalent of `scripts/validate_skill.ts`:

- [ ] SKILL.md exists at the skill root and starts with `---` YAML frontmatter
- [ ] `name` matches directory name; ≤64 chars; only `a-z0-9-`; no edge/double hyphens; no `claude`/`anthropic`; no `<` or `>`
- [ ] `description` present, ≤1024 chars, no `<` or `>`, third person
- [ ] Description contains no sequenced workflow ("first... then...", numbered steps)
- [ ] Body ≤500 lines (flag >200 as worth splitting)
- [ ] Every file in `references/`, `scripts/`, `assets/` is mentioned in SKILL.md
- [ ] References linked from SKILL.md are one level deep
- [ ] Reference files >100 lines begin with a table of contents
- [ ] No interactive prompts in scripts; no unpinned third-party dependencies
