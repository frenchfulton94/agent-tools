# bugfix-flow

An OpenSpec schema for defect fixes. Companion to `mattpocock-bridge`.

`diagnose → specs → tasks → apply`

A defect needs no case made for fixing it, so this schema drops the interview and the
proposal. What it adds is a gate: nothing can be written until the root cause is, which is
the one discipline defect fixes actually lack.

## Use it

```
/opsx:new fix the export timezone offset, using bugfix-flow
```

Or in a terminal, when the slug is already decided:

```bash
openspec new change fix-export-timezone --schema bugfix-flow
```

Per-change, so it sits alongside `mattpocock-bridge` without replacing it. Copy the folder
to `openspec/schemas/bugfix-flow/` and leave `schema: mattpocock-bridge` as the project
default.

## Config

Both schemas share one `openspec/config.yaml`. Rules keyed to `specs` and `tasks` fire in
both, since those artifact ids exist in each; `diagnose` fires only here. `context:` reaches
every artifact of both.

## Artifacts

| Artifact | Skills | What it carries |
|---|---|---|
| `diagnose` | `diagnosing-bugs`, `domain-modeling` | Reproduction, root cause, fix layer (symptom or cause, with reasoning), and the seam the regression test sits at |
| `specs` | — | The case the spec was silent about, as an ADDED requirement whose scenario is the reproduction made permanent |
| `tasks` | — | Failing test first, then the fix |
| `apply` | `tdd`, `code-review` | Test at the agreed seam, smallest fix at the agreed layer, full suite, review |

## Escape hatch

Where the spec already covered the case and the code simply disagreed, no delta is owed:
set `skip_specs: true` in the change's `.openspec.yaml`. The regression test holds the line.

## When to use the other schema instead

A fault whose fix is a redesign is a change, not a bugfix — `diagnose` says to stop and
reopen under `mattpocock-bridge`. The signal is the fix altering behaviour the product
cares about, rather than restoring behaviour it already promised.
