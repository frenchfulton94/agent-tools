# Background

Nothing here is normative. Every sentence in this file explains why a rule
exists; no sentence adds a rule. If moving a sentence to `rules.md` would
change what an agent does, it is misfiled and belongs there instead.

Contents:
- [Where the two-part architecture comes from](#where-the-two-part-architecture-comes-from)
- [Why enforcement is the whole problem](#why-enforcement-is-the-whole-problem)
- [Why there are registers](#why-there-are-registers)
- [Why the glossary is a separate file the project owns](#why-the-glossary-is-a-separate-file-the-project-owns)
- [Why Vale is optional](#why-vale-is-optional)
- [Standing caveats](#standing-caveats)

## Where the two-part architecture comes from

Simplified Technical English (ASD-STE100) was written for aerospace
maintenance documentation, where a misread instruction is a safety event. Its architecture is the part worth copying. STE pairs a set of writing rules
with a dictionary. The dictionary fixes one word to one meaning and one part
of speech, and bans the synonyms. It leaves an escape hatch for the project's
own technical names.

CEE copies the architecture and not the dictionary. STE's word list is
copyrighted, aerospace-specific, and wrong for software. The core list in
`dictionary.md` is written from drift observed in engineering prose.

The prose rules come from a different lineage. It runs through the Google and
Microsoft style guides, ISO 24495-1 on plain language, and Nielsen Norman's
research on how people read documentation. That lineage supplies active voice, the sentence ceiling, and one idea per
sentence. It also supplies defining acronyms at first use, and the
problem-then-next-step shape for incident messaging.

## Why enforcement is the whole problem

Caterpillar Fundamental English is the cautionary case. It was a real
controlled language with a real dictionary, and it decayed once nobody owned
it. A controlled language is a coordination device: it works while everyone
uses it and delivers nothing while half do.

Two consequences run through the design. First, deterministic checks wherever
a rule can be machine-checked, because a rule enforced by memory is a rule
enforced sometimes. Second, waivers with reasons and dates (G-X1), because a
standard with no legitimate exit gets abandoned wholesale the first time it is
wrong.

## Why there are registers

The two audiences differ in exactly one way: what they may be assumed to
know. An engineer knows the stack but not this project. A stakeholder knows
neither. Every difference between R1-E and R1-S falls out of that one difference. That
is why the two registers share every G rule and the whole dictionary.

Spec prose is not a third audience. It is R1-E writing for a reader who will
implement it. So it adds only the two rules that matter to an implementer:
fixed normative keywords (G-N1) and the behavior-implementation split (E-4).

## Why the glossary is a separate file the project owns

Vocabulary is the project's, not the standard's. A skill that shipped its own
domain words would be wrong in every repo but one.

Keeping it in the repo also makes it shared infrastructure. One file settles a
term for a release note, a spec, and a README at once. That stops the three
describing one thing in three different words, which is the drift this
standard exists to prevent.

The gloss column exists because the same concept was being explained to
stakeholders differently in every document. Writing the explanation once, in
the glossary, makes S-1 a lookup rather than an improvisation.

## Why Vale is optional

Vale is a Go binary. Sandboxed environments, restricted CI, and plain chat sessions do not always
have it. A standard that requires a binary stops working in the environments
where documents are most often written.

Every rule in CEE is applicable by review alone. Vale is one deterministic
backend that sharpens enforcement where it is present. The glossary format is
plain markdown for the same reason. The compiler emits Vale rules today;
another tool's rules could be added without touching the glossary.

## Standing caveats

- Do not copy STE's dictionary. Its word list is copyrighted; its architecture
  is not.
- Enforcement plus a named owner, or the language dies. Every documented
  controlled language that failed, failed this way.
- The published benefit numbers for controlled languages come from aerospace
  and manufacturing documentation. They are suggestive for software
  documentation and not evidence about it.
