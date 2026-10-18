# apple-games trigger evals

Phrasing rule carried forward from Phase 3: no "build X" wording — it gets
preempted by the superpowers brainstorming skill before this skill can fire.
Every row is a how-to question, per the Phase 10 eval-fixture decision
(Task 12).

## Should fire
- "How do I keep my game's physics at the same speed on 60 Hz and 120 Hz displays?"
- "How do I set up a render thread for CAMetalDisplayLink in my Mac game?"
- "How do I read a game controller's thumbsticks once per simulation step?"
- "How do I add on-screen touch controls to my Metal game on iPhone?"
- "How do I play positional sound effects that walls muffle with PHASE?"
- "How do I make my Mac game turn on Game Mode?"
- "How do I sync game saves between a player's iPhone and Mac?"
- "How do I download level packs after install with Background Assets?"

## Should NOT fire
- "How do I find which render pass takes the most GPU time in my frame?"     (apple-metal — GPU frame time)
- "How do I find out why my app takes three seconds to launch?"              (apple-performance — launch time)
- "How do I add particle effects to a SpriteKit scene?"                      (SpriteKit — out of scope)
- "How do I read a gamepad button press in a Godot GDScript _input handler?" (gdscript — Godot, out of scope)
- "How do I lay out a settings screen that adapts from iPhone to iPad?"      (apple-design — general HIG layout)
- "How do I notarize my Mac app for distribution outside the App Store?"     (app-release — notarization)
