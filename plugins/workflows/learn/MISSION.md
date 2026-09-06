# Mission: the `workflows` plugin

## Why

A colleague picking this up cold should be able to clone a repo,
run one command, and be doing spec-driven work correctly the same afternoon — without
DMing the plugin's author. The plugin already makes the setup correct-by-construction;
what is missing is a learner who can pick the right level, read the plan gate, route a
task to the right schema, and drive that schema to an archive without supervision.

## Success looks like

- A teammate who has never seen OpenSpec runs `/workflows:setup` start to finish with no
  help, and can say afterwards which files it wrote and which it refused to touch.
- Given ten one-line work requests, the learner routes each to the right schema in one
  pass and names the `ROUTING.md` rule that decided it.
- The learner drives at least one change end to end — proposal through archive — in each
  level they have installed.
- The learner picks a model and effort per artifact from the depth-follows-artifact rule
  rather than leaving one setting on for the whole session.
- The learner can prove `context:` and `rules:` reached the model, instead of assuming
  a silent config is a working one.
- Asked "which of our repos have fallen behind?", the learner answers with
  `--check` output rather than a guess.

## Constraints

- Self-paced and asynchronous. No scheduled sessions; lessons must stand alone and be
  finishable in one sitting.
- Written for a newcomer first, with author-level detail kept to clearly marked
  appendices — one package serves both onboarding and the author's own cross-repo practice.
- The plugin source is the source of truth. Where a usage guide or an upstream doc
  disagrees with the code, the code wins and the difference is named.
- Nothing here may recommend a workflow behaviour that is not in the plugin source.

## Out of scope

- Authoring new OpenSpec schemas from scratch. The plugin ships twelve; learning to write
  a thirteenth is a different mission. `configuring-openspec` already covers it.
- The internals of the packs the schemas call into (superpowers, mattpocock, impeccable,
  agent-skills). Lessons teach where a schema hands off, not what happens on the far side.
- Building or maintaining the plugin itself. That is `authoring-plugins` territory.
