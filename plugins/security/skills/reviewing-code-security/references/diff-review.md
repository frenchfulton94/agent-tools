# Diff-based review

For a branch, a pull request, or staged changes. Reviews what changed and what the change reaches —
not the whole repository.

## Establish the diff

    git merge-base HEAD main                       # the fork point
    git diff --stat $(git merge-base HEAD main)    # scope and size
    git diff $(git merge-base HEAD main)           # the change itself

For staged-only review use `git diff --staged`. If the base branch is not `main`, ask rather than
guessing — reviewing against the wrong base silently hides or invents changes.

If the diff exceeds ~2,000 lines, say so and propose either a baseline sweep or a split by
subsystem. A diff review that skims is worse than an honest refusal to skim.

## What to examine

In order, because each step narrows the next:

1. **New entry points.** Routes, handlers, event consumers, CLI arguments, webhooks. Untrusted
   input enters here and every downstream finding traces back to one.
2. **Changed trust boundaries.** New calls across a network, a shell, a parser, a template, or a
   database. Grep the index for the boundary type.
3. **Touched controls.** Anything modifying authentication, authorization, session handling,
   cryptography, or file handling. A change that weakens an existing control outranks a new
   missing one — regressions are what diff review is uniquely able to catch.
4. **Dependencies.** New or bumped entries in a lockfile: check the sheets tagged `supply-chain`.
5. **Configuration.** CI workflows, Dockerfiles, IaC. These change the blast radius of everything
   else.

## Reachability

For each candidate finding, establish whether an untrusted input can actually reach the code. Trace
it with `rg` from the entry point. State the path in the finding, or state that you could not
establish one — an unreachable flaw is Low, and saying so is what makes the Highs credible.

## Scope discipline

Report pre-existing problems in files the diff touches only when the change makes them reachable or
worse. Otherwise note them in one line under "pre-existing, out of scope". A diff review that
expands into a baseline audit stops being reviewable at merge time.
