# Source outranks every document, and the drifts are worth teaching

Three places where a secondary document disagreed with the plugin source, all resolved in
favour of source and all named in a `Drift` aside rather than silently corrected:

1. `payload/levels/minimal/openspec/schemas/mattpocock-bridge/README.md` says to choose
   profile "expanded". No such preset exists — `plan.mjs` and the OpenSpec docs agree the
   presets are `core` and `custom`.
2. The mattpocock guide puts both design gates on the very top tier; the shipped agents
   pin `opus`. Identical on a Pro plan, divergent above it, and raising the pin means
   editing the file — which makes it yours forever.
3. `https://www.aihero.dev/skills.md` returns a paraphrase with several wrong skill names
   (`/domain-model`, `/to-prd`, `/to-issues`, `/review`) against the real repo.

**Why teach the drift rather than just the fact:** the habit of checking source is the
transferable skill. A lesson that silently prefers source teaches the fact and not the
habit.
