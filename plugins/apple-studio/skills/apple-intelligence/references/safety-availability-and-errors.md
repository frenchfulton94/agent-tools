> verified: 2026-09 against https://developer.apple.com/documentation/FoundationModels/improving-the-safety-of-generative-model-output, https://developer.apple.com/documentation/FoundationModels/LanguageModelError, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/ContextSizeExceeded, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/RateLimited, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/Refusal, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/Refusal/explanation, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/Timeout, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/GuardrailViolation, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/UnsupportedCapability, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/UnsupportedTranscriptContent, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/UnsupportedGenerationGuide, https://developer.apple.com/documentation/FoundationModels/LanguageModelError/UnsupportedLanguageOrLocale, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Error, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Error/AssetsUnavailable, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Guardrails, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Guardrails/default, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Guardrails/permissiveContentTransformations, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Availability-swift.enum, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Availability-swift.enum/UnavailableReason, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Availability-swift.enum/UnavailableReason/appleIntelligenceNotEnabled, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Availability-swift.enum/UnavailableReason/deviceNotEligible, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/Availability-swift.enum/UnavailableReason/modelNotReady, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/availability-swift.property, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/isAvailable, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/UseCase, https://developer.apple.com/documentation/FoundationModels/SystemLanguageModel/contextSize, https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/tokencount(for:), https://developer.apple.com/documentation/FoundationModels/adding-server-side-intelligence-with-private-cloud-compute, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Availability-swift.enum, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Availability-swift.enum/UnavailableReason, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Availability-swift.enum/UnavailableReason/deviceNotEligible, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Availability-swift.enum/UnavailableReason/systemNotReady, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Error, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Error/QuotaLimitReached, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Error/NetworkFailure, https://developer.apple.com/documentation/FoundationModels/PrivateCloudComputeLanguageModel/Error/ServiceUnavailable, https://developer.apple.com/documentation/BundleResources/Entitlements/com.apple.developer.private-cloud-compute, https://developer.apple.com/documentation/FoundationModels/managing-the-context-window, https://developer.apple.com/documentation/foundationmodels/languagemodelsession/logfeedbackattachment(sentiment:issues:desiredoutput:), https://developer.apple.com/documentation/FoundationModels/LanguageModelSession/GenerationError, https://developer.apple.com/documentation/foundationmodels/languagemodelsession/generationerror/refusal(_:_:), https://developer.apple.com/documentation/FoundationModels/LanguageModelSession/GenerationError/Context, https://developer.apple.com/documentation/FoundationModels/LanguageModelSession/Error, https://developer.apple.com/documentation/FoundationModels/LanguageModelSession/ToolCallError
> sources: live Apple docs (no book input — the corpus predates these frameworks)

# Safety, availability, and errors

## The error surface has two eras — match yours to your deployment target

Foundation Models redrew its error types between OS 26 (currently shipping)
and OS 27 (beta as of this writing). On 26, every generation-time failure —
safety, capability, session misuse, asset problems — arrived as one enum,
`LanguageModelSession.GenerationError` (9 cases, `introducedAt: 26.0`,
`deprecatedAt: 27.0` per its own DocC metadata). It still compiles —
deprecation warns, it doesn't remove the type — but isn't where new code
should point. At 27, Apple split it into three purpose-built types, each
documented `27.0 BETA`: `LanguageModelError` (top-level, backend-independent
generation failures: context, rate limit, refusal, timeout, guardrail, three
"unsupported" cases), `SystemLanguageModel.Error` (on-device-only, currently
just `assetsUnavailable(_:)`), and `LanguageModelSession.Error` (session
*misuse*, not model behavior: `concurrentRequests`,
`transcriptMutationWhileResponding`).

Renames if you're migrating: `.assetsUnavailable(_:)` and
`.concurrentRequests(_:)` moved out to the two new types above;
`.exceededContextWindowSize(_:)` became `contextSizeExceeded(_:)`;
`.unsupportedGuide(_:)` became `unsupportedGenerationGuide(_:)`; old
`.decodingFailure(_:)` has no documented 27-era equivalent. **A bare
`GenerationError` at the `FoundationModels` top level never existed** — that
name only ever lived nested under `LanguageModelSession`, only through OS
26. Match your deployment target: 27+ gets the three types below; a 26-only
target still catches `LanguageModelSession.GenerationError` — every UI
judgment here applies identically, only the catch clause's spelling
changes.

## Guardrails: what they decide, and for whom

`SystemLanguageModel.Guardrails` (stable since 26.0, unlike the error types
above) is a safety system tied to a specific model instance, checking both
the input prompt and the model's output. `.default` runs every guardrail and
throws `LanguageModelError.guardrailViolation(_:)` on a hit.
`.permissiveContentTransformations` lets the on-device model reason about
sensitive source material — summarizing a news article, tagging profanity in
a chat log — by skipping the check, but **only for calls that generate a
plain `String`**; guided generation runs the default guardrails regardless
of the mode you set. Reach for permissive mode only when the feature
*transforms* sensitive material a person already possesses, not when it's
exposed to open-ended input from strangers. PCC has its own guardrails with
different, non-configurable policies — no `.permissiveContentTransformations`
there.

Settle three things per feature before shipping, not from a bug report:
does the guardrail system apply and is it configurable; where might it be
too permissive for your audience (close that gap with app-level layers, not
Apple's); and where might it be too restrictive (adjust your prompt or
instructions, don't fight the guardrail).

## Handling a guardrail violation

```swift
do {
    let response = try await session.respond(to: prompt)
} catch LanguageModelError.guardrailViolation(let violation) {
    // Safety check failed on the prompt or the response.
}
```

This is a **framework-level block** — the reply never got produced at all.
Give people a specific, non-apologetic message ("this feature isn't
designed to handle that kind of input") and a path to try different input;
don't imply the app crashed. If a *built-in* prompt trips this, that's a bug
in your prompt — experiment with rephrasing to find the trigger phrase
before shipping, since your own users can't fix your app's prompts.

## Handling a model refusal

A refusal is different in kind: the model declined, the framework didn't
block it. Plain-string generation has no error at all for this — the
refusal is ordinary response text (something like a "Sorry, I can't help
with that" opener), and Apple's own guidance is blunt that **you may not be
able to tell it apart from a normal answer programmatically**. Design the UI
to present both cases the same way.

Guided/structured generation is the reliable path: with no typed
placeholder for "polite no," it throws `LanguageModelError.refusal(_:)`.

```swift
do {
    let response = try await session.respond(to: prompt, generating: [String].self)
} catch LanguageModelError.refusal(let refusal) {
    do {
        let explanation = try await refusal.explanation.content   // async, can be slow
    } catch {
        let explanation = refusal.debugDescription                // fallback
    }
}
```

`explanation` is itself a model call — don't block a UI transition on it;
show the fallback text immediately and upgrade when it arrives, or skip it
and just offer a rephrase affordance.

## `LanguageModelError`, case by case — with the UI move per case

`LanguageModelError`'s own abstract is "a failure ... when using any
language model," so every case below applies whether the session is on the
on-device `SystemLanguageModel` or `PrivateCloudComputeLanguageModel`;
PCC's own additional error cases are separate (see below).

- **`contextSizeExceeded(_:)`** — the window is full; the session cannot
  process another request, period. *Don't retry the same session* — start a
  new one (`init(model:tools:transcript:)`, seeded from a condensed old
  transcript if continuity matters) and tell the person their conversation
  was summarized/reset. To catch this proactively, surface a "getting full"
  indicator from `SystemLanguageModel.contextSize`/`tokenCount(for:)` —
  never a hardcoded number.
- **`rateLimited(_:)`** (carries `resetDate`) — transient, self-clearing.
  Disable input, show "try again in a moment"; don't force a new session.
- **`refusal(_:)`** — covered above: a model decision, not a bug. Offer
  rephrasing, not an apology-for-the-app tone.
- **`timeout(_:)`** — took too long. Standard retry; if it correlates with
  large prompts/attachments, suggest trimming input.
- **`guardrailViolation(_:)`** — covered above: a framework-level block, not
  the model's voice. Message the block, not a generic error.
- **`unsupportedCapability(_:)`** (carries `capability`) — the session asked
  its backend for something it doesn't support. A code/config bug, not user
  behavior — fix by gating the feature's entry point on a capability check
  before calling the model, not with end-user copy.
- **`unsupportedTranscriptContent(_:)`** (carries `unsupportedContent`) —
  thrown reseeding/continuing a session from a transcript whose content the
  *current* model can't consume: a PCC transcript reseeded on-device,
  multimodal content replayed into a text-only path, or any on-device/PCC
  crossing. Strip or summarize unsupported entries before reseeding across a
  model swap.
- **`unsupportedGenerationGuide(_:)`** (carries `schemaName`) — a `@Guide`/
  schema constraint the model can't honor. Developer/test-time bug against
  your own `Generable` types; shouldn't reach production.
- **`unsupportedLanguageOrLocale(_:)`** (carries `languageCode`) — outside
  the model's supported set. Check `supportedLanguages` before *offering*
  the feature in a locale, rather than discovering this at request time.

## `SystemLanguageModel.Error` and `LanguageModelSession.Error`

`SystemLanguageModel.Error.assetsUnavailable(_:)` means the on-device
model's assets (weights for the base model or a specialized `UseCase`)
aren't in place for this request — the same bucket as `Availability`'s
`.modelNotReady` below, just discovered at call time instead of through the
proactive check. Hitting it in production is a sign you skipped that check
somewhere, not a new UI state to design.

`LanguageModelSession.Error`'s two cases (`concurrentRequests`,
`transcriptMutationWhileResponding`) both mean "you didn't respect
`isResponding`" — races in your own code, not model behavior (mechanics in
`foundation-models-sessions.md`). Fix the race in development; a real user
never causes either on their own, so there's no good end-user copy to write.

## Designing the unavailable state as three different situations

`SystemLanguageModel` exposes both a `Bool` (`isAvailable`) and an enum
(`availability` → `.available` / `.unavailable(UnavailableReason)`). The
`Bool` is a trap if it's the *only* thing your UI branches on — it can't
distinguish "come back later" from "this device will never run this" from
"go flip a setting." `UnavailableReason` has exactly three cases, confirmed
on its own page:

- **`.deviceNotEligible`** — a hardware/software ceiling, permanent for this
  device. Don't leave a grayed-out button; remove the feature's entry point
  entirely. A disabled control implies "not yet," which is false here, and
  reads as a bug the next time the person checks.
- **`.appleIntelligenceNotEnabled`** — a system setting the person controls.
  The *one* case that deserves a call-to-action: point at Settings and say
  what turning it on unlocks. **Do not promise a one-tap jump:** no
  Apple-Intelligence-specific Settings deep link is documented on any
  FoundationModels page (checked 2026-09-02). Write the copy as instructions
  to a location, not as a button that teleports there.
- **`.modelNotReady`** — governed by network status, battery level, and
  system load per its own page, not by anything your app or the user can
  force. Show "try again shortly"; don't send them to Settings (nothing
  there fixes this) and don't remove the feature (it isn't permanent).

Always keep a `case .unavailable(let other)` catch-all, matching Apple's own
sample code — treat any future reason as transient, not a verdict on the
device.

`PrivateCloudComputeLanguageModel` does **not** share this enum — it has its
own `.Availability`/`.UnavailableReason` with only two cases:
`.deviceNotEligible` and `.systemNotReady` ("the system is not yet ready to
serve PCC requests," a server-readiness state, not a local model download).
No PCC equivalent of `.appleIntelligenceNotEnabled` is documented. Check
`PrivateCloudComputeLanguageModel().availability` directly for a PCC-backed
feature; don't infer its state from the on-device model's `availability` or
assume the trees line up case-for-case.

## Untrusted input: the one boundary that matters

Session mechanics for `Instructions` vs `Prompt` live in
`foundation-models-sessions.md`; the judgment this file owns is what that
boundary means for content you don't control. Instructions outrank prompts,
which makes `instructions` a privileged channel — anything unverified there
(raw user text, scraped webpage content, any external source) is a
prompt-injection vector, full stop. Unverified content only ever goes in the
`Prompt`, wrapped in your own template text rather than interpolated raw:

```swift
let userInput = untrustedTextFromTheUser        // never goes in `Instructions`
let prompt = "Generate a wholesome journal prompt reflecting on their day. They said: \(userInput)"
```

The wrapping text is the trusted preamble deciding the task; the untrusted
suffix only supplies content, never instructions. When that isn't
confidence-inspiring enough, drop open text entirely: constrain *input* to a
fixed `@Generable enum` of choices, or constrain *output* the same way, so
the model is structurally incapable of emitting outside the safe set — a
stronger guarantee than any amount of prompt wording. A deny list is a
cheap second gate on top of guardrails, checked both directions (before
sending, before displaying); host it remotely to update faster than app
review cycles. Multimodal prompts need both inputs checked individually
*and* jointly — an acceptable image plus an acceptable caption can still be
unsafe as a pair.

## Private Cloud Compute

PCC requires the managed `com.apple.developer.private-cloud-compute`
entitlement — **a managed entitlement, not one you can simply add to a
target.** The entitlement page is explicit that eligibility is gated and
access is requested: "To develop with PCC you must meet certain eligibility
requirements. To learn more and request access to the managed entitlement,
see Accessing Private Cloud Compute"
(https://developer.apple.com/apple-intelligence/private-cloud-compute/). Treat
the request as lead time in the schedule, not a build-settings checkbox; the
approval process itself is not documented in the framework reference. Swapping backends is one line,
`LanguageModelSession(model: PrivateCloudComputeLanguageModel())`, and every
downstream call, tool, and instruction carries over unchanged.
Three things genuinely differ from the on-device path: **offline** —
`SystemLanguageModel` works without a network, PCC needs one, so treat a PCC
network failure as a signal to retry on-device rather than a dead end;
**usage limits** — on-device is unlimited, PCC carries a per-day quota
raisable via iCloud+, and quota state belongs as ambient UI sourced from
`quotaUsage.status`/`isApproachingLimit` *before* someone hits the wall, not
a dismissible alert after; and **context size** — don't restate the
on-device figure (see the primer's resolution of that ambiguity), but PCC's
**32K** is stable across every page checked this phase and safe to hardcode
in comparisons.

PCC layers three more errors on top of `LanguageModelError`, all about the
round trip itself:

- **`.quotaLimitReached(_:)`** — the day's budget is gone. Unlike
  `rateLimited`, waiting *seconds* doesn't help: either wait for
  `resetDate` or route to the upgrade sheet via
  `quotaUsage.limitIncreaseSuggestion?.show()`.
- **`.networkFailure(_:)`** — no connection. Fall back to
  `SystemLanguageModel` for the same request rather than failing outright.
- **`.serviceUnavailable(_:)`** — PCC itself is down, not the network. Same
  fallback judgment, framed as "using the on-device assistant for now," not
  a bare error.

Xcode's Scheme editor can simulate both quota states (Run > Options >
"Simulated Apple Foundation Models Availability") — exercise the UI for
each before ever hitting a real quota.

## Safety as an ongoing practice, not a checklist

Run a risk assessment per AI feature, not once for the app: for each
feature, write down what could go wrong, how bad it would be, and what
mitigates it (instructions, a deny list, a fixed-choice input) — cheap
before launch, expensive to reconstruct after a gap ships. Test beyond
happy-path prompts — nonsense input, sensitive topics, ambiguous phrasing —
and log enough (timestamp, prompt, response, which mitigation fired) to spot
regressions, since Apple ships new on-device models in routine OS updates
and a prompt that behaved yesterday can refuse or comply differently
tomorrow. Give people an in-app reporting path: when something gets past
both Apple's guardrails and your own layer,
`session.logFeedbackAttachment(sentiment:issues:desiredOutput:)` packages it
for Feedback Assistant — the one channel that can actually move Apple's
guardrail tuning, which a local log can't.

## Classic pitfalls

- **Catching bare `error` and showing one generic message.** Four distinct
  types can come out of a session — `LanguageModelError`,
  `SystemLanguageModel.Error`, `LanguageModelSession.Error`, and PCC's own
  `.Error` — with opposite recoveries (rephrase vs. new session vs. wait for
  quota). Pattern-match the case, not just `catch {}`.
- **Treating `isAvailable` as the whole story.** It's yes/no; it can't tell
  you which of three unrelated recoveries applies.
- **Assuming PCC shares `SystemLanguageModel`'s `Availability` type.** It
  doesn't — a separate enum, two cases instead of three, no
  `.appleIntelligenceNotEnabled` equivalent.
- **Writing `LanguageModelSession.GenerationError` catches against 27+-only
  docs, or `LanguageModelError` catches with a 26-only deployment target.**
  The two eras don't interoperate; match the catch clause to your minimum
  OS.
- **Retrying the same session after `contextSizeExceeded`.** That session
  is finished; only a new one (fresh or transcript-seeded) recovers.
- **Putting user or fetched-webpage text in `instructions`** because it
  feels like the more powerful channel. That's the injection vector by
  design — instructions outrank prompts.
- **Assuming every refusal is catchable.** Only guided/structured
  generation reliably throws `.refusal(_:)`; a plain-string response can
  *be* a refusal with no error raised at all.

## Cross-references

- Session lifecycle, `Instructions`/`Prompt` mechanics, the availability
  check's plumbing, streaming, transcripts: `foundation-models-sessions.md`.
- `Generable`/`Tool` mechanics, `ToolCallError`, schema validation errors:
  `guided-generation-and-tools.md`.
- Whether a feature should use AI at all, the on-device context-window
  number's ambiguity, platform floors: `apple-frameworks/references/primers/foundation-models.md`.
- Token-usage and session profiling via the Foundation Models instrument:
  `apple-performance`.
