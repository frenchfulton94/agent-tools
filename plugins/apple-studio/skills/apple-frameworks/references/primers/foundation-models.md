> verified: 2026-09 against https://developer.apple.com/documentation/foundationmodels.md, https://developer.apple.com/tutorials/data/documentation/foundationmodels.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel/availability-swift.enum.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel/availability-swift.enum/unavailablereason.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/expanding-generation-with-tool-calling.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/improving-the-safety-of-generative-model-output.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/adding-intelligent-app-features-with-generative-models.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models.json, https://developer.apple.com/tutorials/data/documentation/foundationmodels/managing-the-context-window.json
> sources: live docs

# Foundation Models

> **This primer answers "should we, and what does it cost".** For *how to write
> the code* — sessions, guided generation, tool calling, the error surface,
> Private Cloud Compute — see the **`apple-intelligence`** skill. Nothing below
> is an implementation guide, deliberately.

## What it is / when to reach for it

Foundation Models gives apps API access to the large language models behind
Apple Intelligence: an on-device model (`SystemLanguageModel`) and, per the
docs, a server-side "Private Cloud Compute" (PCC) model with a larger context
window for tasks the on-device model can't handle well. The framework's own
abstract frames its scope narrowly: "perform tasks with models that specialize
in language understanding, structured output, and tool calling." The docs
list supported tasks explicitly — summarize, extract entities, understand
text, refine/edit text, classify/judge text, compose creative writing,
generate tags, generate game dialog — and just as explicitly list tasks to
avoid: basic math, code generation, and logical reasoning. That's a real
scope constraint, not boilerplate hedging — treat it as a hard boundary when
deciding whether this framework fits a feature.

Reach for it over a cloud LLM API (OpenAI/Anthropic/etc.) when the task fits
the supported-task list above, you want on-device privacy (no API key
management, requests preserve privacy on both the on-device and PCC paths per
the docs), you want zero per-request cost, and the on-device context window
(32K on PCC) is enough — read the on-device figure at runtime from
`SystemLanguageModel.contextSize`, do not plan against a hardcoded number;
see "Context window" below for why. Prefer a cloud LLM API instead when the task
needs code generation, multi-step logical reasoning, arbitrary math, a context
window larger than PCC's 32K, or availability outside Apple Intelligence
eligibility. Skip AI entirely when a deterministic rule, lookup, or fixed UI
flow solves the problem — the safety docs recommend a fixed set of
prompts/choices as the highest-safety design, itself a signal generative UI
should be the fallback, not the default.

## Architecture integration

A `LanguageModelSession` is the unit of work — the docs describe two usage
shapes: a new session per single-turn interaction, or one session reused
across turns for multi-turn/conversational interactions. A session "can only
handle one request at a time" per the docs; check `isResponding` before
issuing a new request rather than firing concurrent requests at the same
session. `SystemLanguageModel.default` is the on-device model handle apps
query for availability and pass into a session; `PrivateCloudComputeLanguageModel`
is the equivalent handle for the PCC path (iOS 27+). Sessions can be
initialized with `tools:` and `instructions:` — instructions are documented
as taking priority over prompts and are the place for steering behavior, not
unverified user input (see Classic pitfalls). For structured work, response
types conform to `Generable` via a macro, returning typed values instead of
raw strings to parse. Streaming responses (`streamResponse`) exist for
incremental UI updates, with a `PartiallyGenerated` optional-everything
variant auto-generated alongside `@Generable` types for that purpose.

The docs recommend starting with the on-device model and evaluating it with
what they call "the Evaluations framework" before migrating a feature to PCC
— treat PCC as an escalation path for reasoning/context-size needs, not the
default. Xcode ships a "Foundation Models" instrument (Product > Profile) for
inspecting token usage and session request/response/tool-call breakdowns —
the documented path to understanding cost/latency during development.

## Privacy, entitlements, review

- The docs state both the on-device path and PCC "preserve privacy," and that
  PCC requires no API key management from the developer.
- PCC specifically requires requesting access to a managed entitlement,
  documented as `com.apple.developer.private-cloud-compute`; the docs point
  developers to Apple's separate Private Cloud Compute developer page for
  eligibility/access details rather than stating the process inline.
- PCC has daily per-user request quotas (distinct from rate limiting) that
  the docs say can be raised via an iCloud+ upgrade path (`model.quotaUsage`,
  a `quotaLimitReached` error, a `limitIncreaseSuggestion` API).
- The safety-guidance page dedicates significant space to App-Review-adjacent
  design obligations, without naming App Review directly: build additional
  app-specific safety layers beyond the framework's built-in guardrails, run
  a documented risk-assessment exercise per AI feature (harm → severity →
  mitigation), test with adversarial/nonsensical input, and give users a way
  to report harmful output (`LanguageModelFeedback` plus Feedback Assistant
  for escalating guardrail gaps to Apple).
- **Not documented on any page fetched for this primer:** no Info.plist
  usage-description key was mentioned anywhere for the on-device
  `SystemLanguageModel` path (unlike, e.g., Photos or Location) — treat as
  unconfirmed, not as "none required," and verify before shipping. No
  specific App Review guideline numbers were stated either.

## Availability

Platform floor per the framework's own topic page: iOS 26.0+, iPadOS 26.0+,
macOS 26.0+, Mac Catalyst 26.0+, visionOS 26.0+, and watchOS 27.0+ (beta).
`PrivateCloudComputeLanguageModel` carries its own higher floor — the docs
guard it with `#available(iOS 27.0, macOS 27.0, watchOS 27.0, visionOS 27.0,
*)` in example code, so PCC is not available everywhere the base framework
is.

Beyond the OS floor, the on-device model has a separate, runtime-checked
eligibility gate tied to Apple Intelligence: `SystemLanguageModel.default
.availability` returns `.available` or `.unavailable(reason)`, and must be
checked before use — the documented pattern in every example, not optional
boilerplate. `SystemLanguageModel.Availability.UnavailableReason` (confirmed directly
against its own DocC reference page) has exactly three cases:
`.deviceNotEligible` (device/region doesn't support Apple Intelligence),
`.appleIntelligenceNotEnabled` (eligible device, but the user hasn't turned
Apple Intelligence on in Settings), and `.modelNotReady` (still downloading,
or unavailable for another system reason). Never assume the model is available just
because the OS-version check passed — device eligibility, region, Apple
Intelligence enablement, and model-download state are all separate,
runtime-only gates, modeled as a switch with alternative UI per case, not a
single "AI on/off" flag.

**Context window — query it, never hardcode it.** The window is a hard
per-session budget covering instructions, prompts, tool definitions/schemas,
and responses combined; exceeding it throws
`LanguageModelError.contextSizeExceeded(_:)` and stops the session responding.
PCC is 32K, stated consistently across the PCC page's prose and its capability
table.

The **on-device** number is where planning goes wrong. Apple's prose says 4096
("Apple's on-device foundation model has a context window of 4096 tokens per
session", *Managing the context window*; "Context size 4K" in the PCC
comparison table), but `SystemLanguageModel.default.contextSize` measured
**8192** on macOS 27.0 (build 26A5416b, Swift 6.4) on 2026-09-02. Both were
checked the same day. They describe the same quantity — `contextSize` is "the
maximum context size in tokens that the model supports" and the article's
window is "the total number of tokens that can be used in a single session,
including both input prompts and generated responses" — so this is not two
different measurements.

The reading: **the documented figure lags the shipped OS**, and the window is
version-dependent. That makes any hardcoded constant a latent bug in both
directions — budgeting to 4096 wastes half the window on this OS, and
budgeting to 8192 breaks on a device where the doc's figure is the real one.
Call `SystemLanguageModel.contextSize` and `tokenCount(for:)` and budget
against what the device reports. Evidence: `task-0-contextwindow.md` in the
`2026-09-02-phase6-intelligence-performance` record, in the archived authoring
repository (`apple-studio`, not this catalog) at
`.superpowers/sdd/2026-09-02-phase6-intelligence-performance/task-0-contextwindow.md`.

## What's on the surface now (refreshed 2026-09)

This primer was written against an earlier cut of the framework. Four areas
have appeared or grown since, and each changes an adoption estimate — kept at
planning grade, with implementation in `apple-intelligence`.

- **Multimodal prompting is real.** `Attachment` carries an image alongside
  text (`CGImage`, `CIImage`, `CVPixelBuffer`, or a URL), so "understand this
  screenshot/photo" is now in scope for the on-device model. If a feature was
  costed as text-only-therefore-not-viable, re-cost it.
- **Dynamic profiles.** `DynamicInstructions` and session profiles let
  instructions vary per session without rebuilding the prompt by hand. Relevant
  to estimates only as a "this is supported, don't budget for a homegrown
  templating layer" signal.
- **A custom language-model-provider path exists.** `LanguageModel`,
  `LanguageModelExecutor` and KV-cache tuning allow running your own Core AI
  model inside a Foundation Models session. This is the escape hatch when the
  system model's task list genuinely does not fit — worth knowing before
  concluding "Foundation Models can't do this, so we need a cloud API."
- **There is an evaluation surface.** Apple documents evaluating prompts to
  measure performance and improve responses. Budget for prompt evaluation as a
  real activity rather than assuming prompts are written once.

Scope constraint unchanged and still the deciding factor: the supported-task
list is narrow and the avoid-list (math, code generation, multi-step logical
reasoning) is a hard boundary, not hedging.

## Classic pitfalls

- **Not branching on every `Availability` case.** The docs model this as a
  switch with distinct UI for `.available`, device-ineligible, and
  not-ready — collapsing to a single boolean throws away "try again later"
  (downloading) vs. "this device can't do this" (ineligible).
- **Blowing the on-device context window.** The docs'
  token-management guidance is specific and repeated: keep prompts to no
  more than three paragraphs, keep `@Guide`/tool descriptions short, limit
  sessions to 3-5 tools, and split long tasks across multiple sessions
  rather than one giant context.
- **Putting unverified user or external input directly into
  `instructions`.** The safety docs call this out explicitly as a
  prompt-injection vector, since instructions are prioritized over
  prompts — user input belongs in the prompt, not the trusted instructions
  string.
- **Treating a string response as reliably parseable for refusal
  detection.** The docs state a refusal can come back as an ordinary string
  starting with "Sorry, I can't help with," and that you may not be able to
  programmatically distinguish it from a normal response without extra
  classification — guided generation surfaces refusals as a typed error
  instead, which is the reliable path. **The type name matters and is a
  known trap:** there is no bare `GenerationError` — it does not exist in the
  SDK (`error: cannot find 'GenerationError' in scope`, verified 2026-09-02).
  On macOS 27 the case is `LanguageModelError.refusal`; the 26.0-era
  `LanguageModelSession.GenerationError.refusal` still compiles but is
  deprecated as of macOS 27.0. See `apple-intelligence` /
  `safety-availability-and-errors.md` for the full surface.
- **Using `.required` tool-calling mode without an explicit exit
  condition.** The docs warn that without one, "the model will continue
  calling the tool indefinitely."
- **Assuming the on-device model can do math, code, or multi-step logical
  reasoning because "it's an LLM."** The framework's own task list
  explicitly excludes these — pick PCC, a cloud API, or a non-AI solution
  instead of fighting the on-device model.

## Current docs

- https://developer.apple.com/documentation/foundationmodels.md
- https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models.md
- https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel.md
- https://developer.apple.com/documentation/foundationmodels/managing-the-context-window.md
- https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation.md
- https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling.md
- https://developer.apple.com/documentation/foundationmodels/improving-the-safety-of-generative-model-output.md
- https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute.md
- https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions.md
