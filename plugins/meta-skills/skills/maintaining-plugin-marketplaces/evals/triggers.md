# Trigger battery: maintaining-plugin-marketplaces

## Should trigger (10)

1. "Add a skill for writing release notes to this marketplace — which plugin should it go in?"
2. "Is this marketplace healthy? Check whether anything has drifted."
3. "I renamed a plugin and now people are getting plugin-not-found."
4. "We're cutting a release. What needs to move before I tag it?"
5. "Clean up the plugins in this repo — I think some of it is dead."
6. "I bumped the plugin but `/plugin update` says everyone's already on the latest version."
7. "Do any of our skills overlap? I think two of them fight over the same requests."
8. "Should the brand-linting skill live in `marketing` or `web-development`?"
9. "I want to retire the security plugin without breaking anyone who installed it."
10. "the readme says we ship five skills but i only count four, whats going on"

## Should not trigger (10) — near-misses

1. "Write me a skill that reviews SQL migrations." (authoring one skill → `authoring-skills`)
2. "My skill never fires — Claude ignores it." (one description's trigger problem → `authoring-skills`)
3. "This plugin installs but none of its skills show up." (one plugin's layout → `authoring-plugins`)
4. "What fields can go in plugin.json?" (manifest schema → `authoring-plugins`)
5. "Add a PostToolUse hook that runs our formatter." (hook authoring → `authoring-hooks`)
6. "How do I install a plugin from someone else's marketplace?" (consuming, not maintaining)
7. "Run the tests and tell me why they're failing." (plain test run; no catalog judgment involved)
8. "Trim this SKILL.md down, it's 900 lines." (one skill's size → `authoring-skills`)
9. "Set up a GitHub Actions workflow for this repo." (CI authoring, not catalog maintenance)
10. "What's the difference between a plugin and a marketplace?" (docs question, no artifact to change)

## Notes on the boundary

Cases 1–4 and 8 are the ones worth measuring. They sit one layer below this skill and share most of its vocabulary — "plugin", "skill", "marketplace" — so a description that fires on them is over-broad, and the closing clause routing single-artifact work to the sibling skills is what has to carry the separation.

Should-trigger 8 and should-not 1 are deliberately adjacent: one asks *where a skill goes* and one asks *for a skill to be written*. A run where both fire the same skill means the description is not distinguishing placement from authoring.
