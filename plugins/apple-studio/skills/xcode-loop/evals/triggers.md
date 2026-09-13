# xcode-loop trigger evals
## Should fire
- "Build the app and make sure it compiles"
- "Run the test suite for this project and show me the failures"
- "Boot an iPhone simulator and screenshot the onboarding screen"
- "Did my change break anything? Verify it runs"
- "Install the app on a simulator and launch it"
## Should NOT fire
- "Explain actor isolation in Swift 6"          (swift-concurrency)
- "Review this diff for architecture problems"  (swift-architecture)
- "What's the best way to store user settings?" (swift-architecture)
- "Write a test for the parser"                 (swift-testing — writing, not running)
