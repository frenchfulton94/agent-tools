# apple-intelligence trigger evals

Phrasing rule carried forward from Phase 3: no "build X" wording — it gets
preempted by the superpowers brainstorming skill before this skill can fire.

## Should fire
- "Summarize a note with the on-device model and stream the result into the view"
- "My Generable struct comes back with half the fields nil — what's wrong?"
- "The model never calls my Tool, it just answers from the prompt"
- "Handle the case where Apple Intelligence is turned off on the device"
- "This session throws contextSizeExceeded partway through a long conversation"
- "Expose 'start a workout' to Siri and Spotlight from my app"
- "My AppEntity query never gets called when I search in Spotlight"
- "Catch a guardrail refusal and show something sensible instead of an error"
- "Send the prompt to Private Cloud Compute instead of the on-device model"
- "Attach a photo to the prompt and ask the model what's in it"

## Should NOT fire
- "Should this feature use on-device AI or just a rule?"          (apple-frameworks primer — adoption judgment)
- "What does Foundation Models cost us versus calling an API?"    (apple-frameworks primer — adoption judgment)
- "Wire up the Anthropic API and stream the response"             (cloud LLM — ordinary networking, out of scope)
- "Detect barcodes in this image with Vision"                     (classical ML — deferred, Phase 7 candidate)
- "Transcribe this audio file"                                    (Speech — deferred)
- "Where should this view model's state live?"                    (swift-architecture)
- "Write tests for this view model"                               (swift-testing)
- "Fix this Sendable warning"                                     (swift-concurrency)
- "Run the mac target and screenshot it"                          (xcode-loop)
- "Why is my Foundation Models feature so slow?"                  (apple-performance — profiling, not implementation)
- "Add a Live Activity for the running timer"                     (activitykit primer — deferred slice)
