---
name: apple-intelligence
description: Implementing on-device generative AI and system intent exposure on Apple platforms - Foundation Models sessions, Instructions vs Prompt, streaming, transcripts, multimodal attachments, guided generation with Generable and Guide, generation schemas, tool calling, guardrails and refusals, the LanguageModelError surface, unavailable-state handling, Private Cloud Compute, and App Intents for Siri, Spotlight and Apple Intelligence. Use when writing or debugging code against FoundationModels or AppIntents - structured output that comes back wrong, a tool that never gets called, a context-window overflow, an intent that never appears in Spotlight or Siri. Not for whether a feature should use AI at all or what it costs (apple-frameworks primers), cloud LLM API integration, Vision/Speech/Core ML (deferred), widgets or Live Activities (apple-frameworks primers), or profiling a model's runtime cost (apple-performance).
---

# On-device intelligence (implementation)

Scope: how the code is written. **Whether** to use on-device AI at all, what it
costs, and on-device-vs-cloud are adoption judgment and belong to
apple-frameworks (its `foundation-models` and `app-intents` primers).
Classical ML — Vision, Speech, Core ML —
is out of scope this phase; widgets, Controls and Live Activities keep their
`widgetkit`/`activitykit` primers.

Read the reference for the decision at hand:
- Sessions, Instructions vs Prompt, streaming, context window, transcripts, attachments, availability mechanics → `references/foundation-models-sessions.md`
- Generable/Guide, generation schemas, GeneratedContent, partial values, the Tool protocol and call loop → `references/guided-generation-and-tools.md`
- Guardrails, refusals, the error surface case by case, unavailable-state UX, untrusted input, Private Cloud Compute → `references/safety-availability-and-errors.md`
- AppIntent, AppEntity, queries, App Shortcuts, Spotlight/Siri, the extension target, testing → `references/app-intents-implementation.md`

Rules that always apply:
- **This API is post-training-data. Do not write a symbol you have not
  verified.** Fetch the current page, then compile it. Both failure directions
  are live and confirmed on this toolchain: the docs spell a method
  `resolved(in:)` that the SDK calls `resolve(in:)`, and document
  `SystemLanguageModel.variant`, which the SDK does not have at all. A 200 on a
  doc page is not evidence a symbol exists.
- **`GenerationError` does not exist** as a bare type — the name is a magnet
  for invention. Current code catches `LanguageModelError`; the deprecated
  `LanguageModelSession.GenerationError` is what macOS 26 targets still use.
- **Never hardcode the on-device context window.** Apple's prose says 4096,
  this host measures 8192, and both were checked the same day. Read
  `SystemLanguageModel.contextSize` and `tokenCount(for:)`. PCC's 32K is the
  one figure safe to state.
- **Check availability before anything else, and branch on every case.**
  Ineligible device, Apple Intelligence off, and model-not-ready are different
  situations with different user recourse; collapsing them to one boolean
  throws away the only actionable one.
- **`Instructions` is trusted, `Prompt` is not.** The model is trained to obey
  instructions over prompt content, which makes the split an injection-safety
  boundary. User and remote content goes in the prompt — never interpolated
  into instructions.
- **Prefer guided generation to parsing prose.** A `Generable` type is both the
  parse and the contract; string-matching a response for a refusal is the
  pattern this framework exists to replace.
- **Apple's own samples do not always compile.** Two were found non-conforming
  while writing these references. Compile a sample before trusting it, however
  official the source.
- Profiling a Foundation Models app's runtime cost → apple-performance
  (apple-performance's `profiling-workflow` reference); Xcode ships a
  Foundation Models
  instrument with a token-usage timeline.
