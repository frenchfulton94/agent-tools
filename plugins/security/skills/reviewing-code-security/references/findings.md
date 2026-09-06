# Findings report format

## Contents

- [Header](#header)
- [Per finding](#per-finding)
- [The quote](#the-quote)
- [Severity rubric](#severity-rubric)
- [Unverified observations](#unverified-observations)
- [Nothing found](#nothing-found)
- [Citation check](#citation-check)

## Header

Always first. The corpus fields come from `owasp/SOURCE.json` and make the review
reproducible — the same code against the same corpus SHA yields the same findings.

```markdown
# Security review — <scope>

- **Scope:** <branch/PR/directory>, <N> files examined
- **Mode:** diff-based | baseline
- **Corpus:** OWASP Cheat Sheet Series @ <sha[0:7]>, synced <syncedAt date>
- **Findings:** <N> critical, <N> high, <N> medium, <N> low
```

## Per finding

```markdown
### [SEVERITY] <one-line description of the flaw>

**Where:** `path/to/file.ts:123`
**Source:** `Password_Storage_Cheat_Sheet.md` § Argon2id
**Quote:** "These parameters control how computationally expensive it is to compute a password hash."

**What:** What the code does, in one or two sentences.

**Why it matters:** The concrete consequence — who can do what. Not "this is insecure".

**Reachability:** How untrusted input reaches this code, or why it cannot.

**Fix:** What the cited sheet prescribes, applied to this code. Include a patch when it is
under ~10 lines.
```

## The quote

The quote is what makes a citation checkable rather than trusted. `scripts/verify-citations.ts`
searches for it in the cited section, so a quote the checker cannot find there is reported as a
failure — and a review that never opened the section cannot produce one.

Four constraints, each for a reason:

- **At least 5 words.** Shorter than that identifies no passage rather than a specific one — a
  single stopword like "the" would match almost any section. `scripts/verify-citations.ts` rejects
  a shorter quote outright, as its own failure distinct from one it simply couldn't find.
- **Under 15 words.** Long enough to identify the passage, short enough to stay clearly within
  fair quotation of the CC-BY-SA-4.0 corpus.
- **From a single line of the sheet.** A quote spanning a line break will not match, and false
  failures are how a checker ends up switched off.
- **Never the value of a discovered secret.** A finding about a hardcoded credential quotes the
  *cheatsheet*, never the credential. Putting it in the report re-discloses it, and writing the
  report would trip this plugin's own credential hook.

When no single line of the cited section states the point, cite the section without a quote rather
than assembling one from fragments. The checker treats a missing quote as unverified, not as a
failure — an honest gap beats a synthetic quote.

Order: severity descending, then by file path. One heading per finding — never merge two flaws
into one entry, because they get fixed by different changes.

## Severity rubric

| Severity | Test | Example |
|---|---|---|
| Critical | Unauthenticated remote exploit, with data loss or code execution | Unparameterised SQL on a public search endpoint |
| High | Authenticated exploit, or credential/PII disclosure | IDOR letting any user read another's records |
| Medium | Needs unusual conditions, or weakens a control without breaking it | Session cookie missing `SameSite` where CSRF tokens are present |
| Low | Hardening gap with no exploit path established | Missing `X-Content-Type-Options` on a JSON-only API |

When exploitability and blast radius disagree, exploitability decides. A trivially exploitable
information leak outranks a theoretical remote-code-execution path behind three preconditions.

## Unverified observations

Anything you could not ground in a cheatsheet goes here, never among the findings:

```markdown
## Unverified observations

- `path/to/file.ts:45` — <observation>. No cheatsheet in the corpus covers this; treat as a lead,
  not a finding.
```

## Nothing found

Say so plainly, and state coverage:

```markdown
No findings. Examined <N> files across <areas> against <sheets cited>. Not examined: <gaps>.
```

Do not manufacture Low findings to fill a report. A clean review that names its gaps is more useful
than four padded entries, because the reader can act on the gaps.

## Citation check

A baseline report — one dispatched to the `security-auditor` agent, per `references/baseline.md`
— ends with the checker's own summary line, not a paraphrase of it. After writing the report, run

    bun <skill>/scripts/verify-citations.ts docs/security-reviews/<name>.md

and append its last line verbatim under this heading:

````markdown
## Citation check

```
<N> citation(s): <N> verified, <N> unquoted, <N> failed
```
````

If it reports any `FAIL`, fix the citation and re-run before finishing — see
`references/baseline.md`.
