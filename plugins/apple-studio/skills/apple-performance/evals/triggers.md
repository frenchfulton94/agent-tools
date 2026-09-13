# apple-performance trigger evals

Phrasing rule carried forward from Phase 3: no "build X" wording — it gets
preempted by the superpowers brainstorming skill before this skill can fire.

## Should fire
- "Scrolling this list stutters on a real device but feels fine in the Simulator"
- "The app freezes for about a second when I tap Save"
- "Which Instruments template should I use for a UI that feels sluggish?"
- "Our launch time got noticeably worse this release — where do I look?"
- "Memory climbs the longer the app runs but Leaks reports nothing"
- "This screen redraws constantly even when nothing visible changed"
- "The Organizer shows a spike in terminations — what's causing them?"
- "Battery drain complaints since the last update; how do I measure it?"
- "How do I add my own signposts so my work shows up in the timeline?"
- "The app binary has grown 40 MB and I need to know what's in it"

## Should NOT fire
- "Run the mac target and screenshot it"                     (xcode-loop)
- "The build fails with a linker error"                      (xcode-loop)
- "Write a test for this view model"                         (swift-testing)
- "How do I write a performance test with a baseline?"       (swift-testing — test authoring)
- "Make this card flip with a spring animation"              (apple-animations — implementation, not cost)
- "Where should this view's state live?"                     (swift-architecture)
- "Fix this Sendable warning"                                (swift-concurrency)
- "Stream a summary from the on-device model"                (apple-intelligence — implementation)
- "Does this screen follow the HIG?"                         (apple-design)
- "Set up TestFlight for the beta"                           (app-release)
