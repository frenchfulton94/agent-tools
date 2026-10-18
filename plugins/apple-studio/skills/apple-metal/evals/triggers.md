# apple-metal trigger evals

Phrasing rule carried forward from Phase 3: no "build X" wording — it gets
preempted by the superpowers brainstorming skill before this skill can fire.
Every row is a how-to question, per the Phase 10 eval-fixture decision
(Task 12).

## Should fire
- "How do I set up three frames in flight with Metal 4 command allocators?"
- "How do I fix textures that render pink after I moved to residency sets?"
- "How do I stop the first pipeline compile for an effect from hitching a frame?"
- "How do I choose load and store actions so my G-buffer stays in tile memory?"
- "How do I add MetalFX temporal upscaling to my Metal renderer?"
- "How do I find which render pass costs the most GPU time from the terminal?"
- "How do I drive a Metal 4 command queue from my Rust engine with objc2-metal?"
- "How do I choose between MSL 4.0 and 4.1 when the game still supports macOS 26?"

## Should NOT fire
- "How do I add a ripple with colorEffect to a SwiftUI image?"              (apple-animations — SwiftUI shader modifier)
- "How do I find why scrolling my settings list stutters?"                  (apple-performance — app-level slowness)
- "How do I add particle effects to a SpriteKit scene?"                     (SpriteKit — out of scope)
- "How do I check a Godot .gdshader for errors before I run the game?"      (godot-testing-and-debugging)
- "How does a Cook-Torrance BRDF trade energy between diffuse and specular?" (general rendering theory — out of scope)
- "How do I read the thumbsticks of a game controller?"                     (apple-games — input)
