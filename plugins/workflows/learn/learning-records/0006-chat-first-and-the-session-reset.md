# The chain is chat-first, and the gap before apply is a taught step

Two related corrections to how the running lessons (06–12) present the loop, made 2026-08-28.

**`/opsx:new <a sentence>` is the primary way to start a change; the CLI is the option.**
The lessons opened every chain with `openspec new change <slug>`, which is a terminal command
that makes the learner invent a slug and returns no first-artifact template. The shipped
command template is explicit that this is not the intended entry point: "The argument after
`/opsx:new` is the change name (kebab-case), OR a description of what the user wants to
build" — a sentence is a first-class input, and the command derives the slug, scaffolds,
shows status, prints the first template, and stops. Naming a schema in the same sentence is
how a learner exercises row 1 of the routing precedence table, so lesson 06's routing example
is now a sentence rather than a flag. `openspec new change` stays in every lesson as the
terminal form, labelled as such, because it is the right tool in a script.

**The gap between the last planning artifact and the first line of code was untaught.** No
lesson mentioned `/clear` at all, and lesson 12 said only "switch at artifact boundaries"
without naming a command. Three facts make that gap the highest-value moment in the chain,
and they compose into one ritual now taught in lesson 08, deepened in lesson 12, and carded
on `command-card.html`:

1. OpenSpec's own guidance is to clear context before implementation, and the plugin's
   `using-openspec.md` already carried that line — unconnected to any lesson step.
2. A model or effort switch made inside a full window still drags that window into every
   following turn, so `/clear` has to come *first*, not after. `/model` sets both knobs —
   model with up/down, its effort with left/right — and `/effort` covers the common
   depth-only case.
3. `apply` and `continue` infer the change from the conversation when the name is omitted.
   Clearing is precisely what removes the thing they infer from. So taking clearing
   seriously is what makes `/opsx:apply <change>` non-optional, and every command in the
   lessons now carries the change name.

**Why clearing is free, and this is the part that makes it teachable:** artifact status is
pure filesystem existence — a fact lesson 09 already taught for a different reason. Nothing a
chain depends on lives in a session, so `/clear` costs the change nothing and returns the
whole window to the implementation loop. `/opsx:continue <change>` is therefore also the
resume command for a brand-new session, which no lesson had said.

**Implication for future sessions:** the ritual is one unit — clear, re-pick, name the change
— and it should be stated once with reasoning (lesson 08) and referenced, not restated, in
09, 10, and 11. Lesson 11's hotfix section is the one place it runs *upward* in depth, since
the postmortem follows apply and wants the top tier.
