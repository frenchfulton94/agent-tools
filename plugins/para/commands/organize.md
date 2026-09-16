---
description: Organize a directory into the PARA structure, with an approve-before-move plan
argument-hint: [directory, e.g. ~/Downloads]
---

Organize this directory into PARA: **$ARGUMENTS**

Use the `organizing-files-with-para` skill and follow its seven-step run. The
ordering matters: steps 1 and 2 are read-only, and step 6 is the only one that
moves anything.

Do not move a single file before the user has approved the rendered plan. If
the user asks you to "just do it", still render the plan first — it is the
artifact the approval is about, and producing it costs one scan.

If no directory was given, ask for one. Never default to the home directory:
`$HOME` is refused by design.
