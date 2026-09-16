---
name: maintaining-para-systems
description: Maintains a PARA tree that already exists — sweeping 0-Inbox, archiving completed projects, detecting drift between the project list and the folders on disk, and declaring digital bankruptcy when a tree is past repair. Use when a PARA root already exists and the user asks for a weekly review, an inbox sweep, an archive pass, or says their system has gone stale, messy, or out of sync with what they are actually working on. For a directory that has not been organized yet, prefer organizing-files-with-para.
license: MIT
---

# Maintaining PARA systems

An organized tree drifts. Projects finish without being archived, `0-Inbox`
fills, and `PARA.md` stops describing what the user is actually working on.

This skill assumes a root that already has `PARA.md` and the `0`–`4` skeleton.
If it does not, use `organizing-files-with-para` instead.

## The upkeep pass

1. **Reconcile `PARA.md` against reality.** Ask which projects have finished.
   A finished project moves to `4-Archives` whole — folder and all.
2. **Sweep `0-Inbox`.** Everything there was previously undecidable, and the
   project list may have grown since. **Never treat `0-Inbox` as a root of its
   own** — `apply.py` would build a nested `0-Inbox/{0-Inbox,1-Projects,…}`
   skeleton inside it, register a second root with the guard hook, and then
   reject every destination reaching back up into the real tree as escaping.
   Instead:

   - List `0-Inbox`'s contents directly (`ls`, or `find <root>/0-Inbox`).
     `scan.py` will not show them: it skips the whole skeleton when scanning
     the real root.
   - Build one plan **rooted at the real root**, whose `files` entries are
     `0-Inbox/<name>` and whose destinations are the ordinary
     `1-Projects/<name>`, `2-Areas/<name>`, `3-Resources/<name>`, or
     `4-Archives/<year>`. Relative paths reaching down into `0-Inbox` validate
     and apply normally; a file that still has no home stays where it is.
3. **Report drift, do not fix it silently.** A folder under `1-Projects` with
   no `PARA.md` entry, or an entry with no folder, is a question for the user.
4. **Mine before archiving.** Ask whether anything in a finishing project is
   reusable elsewhere before it goes cold.

Every move still goes through an approved plan and `apply.py`. Maintenance is
not a licence to skip the gate.

## When the tree is past repair

Digital bankruptcy is a supported outcome, not a failure: move everything into
`4-Archives/<today>` and re-run the setup. Nothing is deleted and everything
stays searchable. Offer it when the inbox has grown faster than the sweep for
several passes running.

See `references/upkeep.md` and `references/starting-over.md`.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
