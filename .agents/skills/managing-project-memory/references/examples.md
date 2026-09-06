# Worked Examples

Before/after cuts and routing decisions with the reasoning spelled out.

Contents:
- [Cutting a bloated section](#cutting-a-bloated-section)
- [Vague to actionable](#vague-to-actionable)
- [Routing a procedure to a skill](#routing-a-procedure-to-a-skill)
- [Routing area guidance to a path-scoped rule](#routing-area-guidance-to-a-path-scoped-rule)
- [Routing enforcement to a hook](#routing-enforcement-to-a-hook)
- [The "what not to add" gallery](#the-what-not-to-add-gallery)

## Cutting a bloated section

Before (11 lines, ~1 fact):

```markdown
## Authentication
Our application uses JSON Web Tokens (JWT) for authentication. JWT is an
open standard (RFC 7519) that defines a compact and self-contained way for
securely transmitting information between parties as a JSON object. When a
user logs in, the server generates a token signed with our secret key using
the HS256 algorithm. The client should store this token and include it in
subsequent requests. The token is passed in the Authorization header using
the Bearer scheme. Tokens expire after 24 hours, at which point the client
must re-authenticate. We chose JWT because it is stateless and scales
horizontally without shared session storage. See auth.md for more details
about our authentication flow and how to debug common issues.
```

After (2 lines, all the facts an agent needs):

```markdown
## Auth
- JWT HS256, `Authorization: Bearer <token>`, 24h expiry; helpers in `src/auth/`
```

Why: the RFC explanation is model knowledge; the design rationale is not actionable; the surviving line holds the project-specific parameters. Per-line test: removing "HS256" could cause a wrong-algorithm bug — it stays. Removing "JWT is an open standard..." causes nothing — it goes.

## Vague to actionable

| Before | After | Why |
|---|---|---|
| "Test your changes before committing" | "Run `pnpm test:unit` before committing; full `pnpm test` needs Docker" | The agent knows testing is good; it can't know the command split |
| "Be careful with database migrations" | "Migrations run on the pooled port 6543; against 5432 they hang silently" | "Careful" isn't an action; the port number is |
| "Follow our code style" | *(delete; linter config already enforces it)* | Never send an agent to do a linter's job |
| "Keep components organized" | "One component per file; shared ones in `src/components/ui/`" | Testable placement rule vs. sentiment |

## Routing a procedure to a skill

Found in a CLAUDE.md (28 lines): a step-by-step release procedure — version bump, changelog generation, tag format, artifact upload, announcement template.

Decision: a release happens in a small fraction of sessions, but its 28 lines are paid in every session. Move the procedure to a skill (loads only when a release is asked for). Leave one pointer in memory only if the team wants discoverability:

```markdown
- Releases follow the release skill; never tag manually
```

## Routing area guidance to a path-scoped rule

Found in a root CLAUDE.md: "When editing anything in `src/api/`, validate all input with zod before touching the DB, and never return raw DB errors to clients."

Decision: costs every session, applies only to API work. Move to `.claude/rules/api.md`:

```yaml
---
paths:
  - "src/api/**"
---
- Validate all input with zod before DB access
- Map DB errors to `ApiError`; never return raw driver errors to clients
```

Caveat: path-scoped rules don't survive compaction until re-triggered — keep a rule in the root instead if violating it even once is catastrophic.

## Routing enforcement to a hook

User asks: "Add a line so the agent never pushes directly to main."

A memory line ("Never push directly to main") is advice — usually followed, not guaranteed. The correct home is a pre-tool-use hook that blocks the push command, which executes regardless of what the agent decides. Deliver the hook; optionally keep the memory line as documentation of the policy, stated once, without emphasis inflation.

## The "what not to add" gallery

Real candidates that fail the governing test, with the reason:

- "This project uses React 18 with TypeScript" — visible in package.json in one read
- "The `utils/` folder contains utility functions" — derivable and content-free
- "Always write meaningful commit messages" — sentiment, not instruction; the commit format rule (if nonstandard) is the actionable part
- "Our API returns JSON" — the model's default assumption
- A 40-line description of the sprint process — not needed by the agent to edit code; route to team docs
- "IMPORTANT: read the whole codebase before making changes" — anti-actionable; burns the instruction budget and slows every task
