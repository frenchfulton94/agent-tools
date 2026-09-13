# Live endpoint map: apple-intelligence

Targets (Tasks 2–3): `foundation-models-sessions.md`, `guided-generation-and-tools.md`,
`safety-availability-and-errors.md`, `app-intents-implementation.md`.

**No books map, and there will not be one.** The corpus is spent — every book
distilled in Phases 1–5 predates Foundation Models entirely, and `pipeline/convert.sh`
is dormant until new books arrive. This skill is 100% live-docs. A future phase
should not go looking for `apple-intelligence-books.md`.

This map is a **seed list, not an exhaustive registry**, per the CONVENTIONS.md
"Distillation maps" rule: it enumerates dispatch-time starting points, distillers may
follow narrower pages under an enumerated parent when the fetch actually succeeds
(DocC JSON 200), and the reference files' own header citations — not this map — are
the citation record. Expected-but-missing pages are recorded below as `MISSING:`.

## Endpoint pattern

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

where `<path>` mirrors the human URL path under `developer.apple.com/documentation/`.

Two shapes of trap live in this pattern and both were hit while building this map:

- **Overloaded names get a DocC disambiguation suffix.** `X` may 404 while
  `X-swift.property` / `X-swift.enum` / `X-pt7n` is the real page. Every seed below
  is recorded in the exact form that returned 200.
- **Case is not the signal it looks like.** Apple's own indexes emit lowercase paths
  and mixed-case paths interchangeably; both resolve. Do not "correct" one to match
  the other.

## Probe status

94 seeds probed at spec time (2026-09-02) — **all 200, zero MISSING** —
and **re-probed at Task 1 execution time: all 94 unchanged, still 200.**
The 15 additional child endpoints named by the plan were probed at Task 1:
14 × 200, 1 × 404 (see the trap note below).
Evidence: `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/spec-endpoint-probe.tsv`.

---

## ⚠️ BINDING CONSTRAINTS FOR DISTILLERS

Read these before writing a line. They come from Task 0's findings and are not
style preferences.

1. **No symbol name, type name, or signature ships from model memory.** Foundation
   Models is entirely post-training-data. If it is not in a page you fetched, it
   does not go in the reference.

2. **A 200 on a doc page is NOT sufficient grounds to ship a symbol.** Task 0 found
   the live docs simultaneously *behind* the shipped OS and *ahead* of the shipped
   SDK. `SystemLanguageModel/variant-swift.property` returns 200 and is documented
   "macOS 27.0 BETA", but does not exist in the Xcode 27.0 (27A5228h) SDK on this
   host:

       error: value of type 'SystemLanguageModel' has no member 'variant'

   `swiftc -typecheck` is the ship gate, not the fetch. Seeded pages that do not
   compile get documented as documented-but-unavailable, or dropped.

3. **The on-device context window is 4096 in the docs and 8192 on this host.** No
   reference may state either number as *the* value. Cite either only as what a
   named source said on a named date, and route readers to
   `SystemLanguageModel.contextSize` / `tokenCount(for:)` at runtime. PCC's **32K
   is safe to state** — consistent across both doc pages, nothing contradicts it.
   Full resolution: `task-0-contextwindow.md`.

4. **`GenerationError` does not exist.** It is the plausible-sounding name the model
   will reach for; the real type is `LanguageModelError`.
   `MISSING: FoundationModels/GenerationError` → 404, confirmed at Task 1.
   This trap was predicted by the spec and re-confirmed on execution.

5. **Implementation only.** Adoption judgment ("should this feature use AI at all",
   what it costs) belongs to `apple-frameworks/references/primers/foundation-models.md`
   and stays there. Cross-ref it; do not restate it.

---

## `foundation-models-sessions.md`

Apple's *Essentials*, *Sessions and prompts*, *Session transcripts*, and
*Prompt attachments* sections, plus the language/locale and model-introspection surface.

### Essentials
- `FoundationModels/generating-content-and-performing-tasks-with-foundation-models`
- `FoundationModels/adding-intelligent-app-features-with-generative-models`
- `Updates/FoundationModels`

### Sessions and prompts
- `FoundationModels/prompting-an-on-device-foundation-model`
- `FoundationModels/managing-the-context-window` — see BINDING CONSTRAINT 3
- `FoundationModels/updating-prompts-for-new-model-versions`
- `FoundationModels/LanguageModelSession`
- `FoundationModels/LanguageModelSession/isResponding`
- `FoundationModels/LanguageModelSession/respond(to:options:)`
- `FoundationModels/LanguageModelSession/streamResponse(to:options:)`
- `FoundationModels/Instructions`
- `FoundationModels/Prompt`
- `FoundationModels/GenerationOptions`
- `FoundationModels/ContextOptions`

### Session transcripts
- `FoundationModels/transcripts`
- `FoundationModels/Transcript`
- `FoundationModels/LanguageModelSession/Transcript`

### Prompt attachments (multimodal)
- `FoundationModels/analyzing-images-with-multimodal-prompting`
- `FoundationModels/Attachment`
- `FoundationModels/ImageAttachmentContent`
- `FoundationModels/ImageReference`

### System language model — the availability entry point every integration needs
- `FoundationModels/SystemLanguageModel`
- `FoundationModels/SystemLanguageModel/availability-swift.property`
- `FoundationModels/SystemLanguageModel/Availability-swift.enum`
- `FoundationModels/SystemLanguageModel/contextSize`
- `FoundationModels/SystemLanguageModel/tokenCount(for:)`
- `FoundationModels/SystemLanguageModel/supportedLanguages`
- `FoundationModels/SystemLanguageModel/UseCase`
- `FoundationModels/SystemLanguageModel/variant-swift.property` — **documented, NOT in the shipped SDK.** See BINDING CONSTRAINT 2.
- `FoundationModels/supporting-languages-and-locales-with-foundation-models`

**Required content:** session lifecycle and reuse (single-turn vs multi-turn),
`Instructions` vs `Prompt` and why the distinction is an injection-safety boundary
rather than a naming convention, the one-request-at-a-time constraint and
`isResponding`, streaming responses, `GenerationOptions`/`ContextOptions`,
context-window management and overflow behaviour, transcripts, multimodal
attachments, locale support, and prompt updates across model versions. Open with
the availability check — it is the entry point every integration needs.

---

## `guided-generation-and-tools.md`

Apple's *Structured output* (all 9) and *Tools* (all 3), plus the first-party Vision
tool conformances.

### Structured output
- `FoundationModels/generating-swift-data-structures-with-guided-generation`
- `FoundationModels/Generable`
- `FoundationModels/Generable(description:)`
- `FoundationModels/Guide(description:)`
- `FoundationModels/GenerationSchema`
- `FoundationModels/DynamicGenerationSchema`
- `FoundationModels/GeneratedContent`
- `FoundationModels/ConvertibleToGeneratedContent`
- `FoundationModels/ConvertibleFromGeneratedContent`

### Tools
- `FoundationModels/expanding-generation-with-tool-calling`
- `FoundationModels/generate-dynamic-game-content-with-guided-generation-and-tools`
- `FoundationModels/Tool`

### First-party `Tool` conformances (Vision) — in scope, per the spec's 2026-09-02 correction
- `Vision/OCRTool`
- `Vision/BarcodeReaderTool`

These are Vision types conforming to the Foundation Models `Tool` protocol. They sit
inside this phase's tool-calling scope, not outside it with the rest of Vision. The
judgment to carry: **check for a supplied tool before writing one.**

`OUT OF SCOPE (Phase 6): Vision/CoreMLRequest` — custom Core ML models through
Vision. Probed and confirmed 200; deferred with the classical-ML surface.

**Required content:** why typed generation beats parsing free text, `Generable`/
`Guide`, static vs `DynamicGenerationSchema`, `GeneratedContent` and its conversion
protocols, partial/streaming generated values, the `Tool` protocol and the call loop,
error handling inside a tool, and the two Vision tools with the check-first judgment.

---

## `safety-availability-and-errors.md`

Apple's *Safety* and *Private Cloud Compute* sections plus the error surface.

- `FoundationModels/improving-the-safety-of-generative-model-output`
- `FoundationModels/LanguageModelError` — **the real error type; see BINDING CONSTRAINT 4**
- `FoundationModels/SystemLanguageModel/Error`
- `FoundationModels/SystemLanguageModel/Guardrails`
- `FoundationModels/SystemLanguageModel/Availability-swift.enum` — the unavailable cases
- `FoundationModels/adding-server-side-intelligence-with-private-cloud-compute`
- `FoundationModels/PrivateCloudComputeLanguageModel`
- `BundleResources/Entitlements/com.apple.developer.private-cloud-compute`

**Required content:** the safety page's design advice, `Guardrails`, guardrail-violation
handling, the `LanguageModelError` / `SystemLanguageModel.Error` surface and what each
case means *for UI*, designing the unavailable state (device ineligible, Apple
Intelligence off, model not downloaded) as a first-class path rather than an
afterthought, untrusted-input handling when app or user content reaches a prompt, and
the PCC path with its entitlement.

---

## `app-intents-implementation.md`

Scoped to the Siri / Spotlight / Apple Intelligence path only.

### Essentials + App-specific content
- `AppIntents/getting-started-with-the-app-intents-framework`
- `AppIntents/app-intents`
- `AppIntents/app-entities`
- `AppIntents/app-enums`
- `AppIntents/common-data-types`
- `AppIntents/app-extension`
- `Updates/AppIntents`

### Feature + system integration (in-scope subset)
- `AppIntents/adopting-app-intents-to-support-system-experiences`
- `AppIntents/apple-intelligence-and-siri-ai`
- `AppIntents/spotlight`
- `AppIntents/app-shortcuts`
- `AppIntents/donations-and-discovery`
- `AppIntents/visual-presentation`

### Testing
- `AppIntents/verifying-your-app-intents-implementation`
- `AppIntentsTesting`
- `AppIntentsTesting/testing-your-app-intents-code`

### Errors
- `AppIntents/AppIntentError`
- `AppIntents/CustomAppIntentErrorConvertible`

**Required content:** `AppIntent`, `AppEntity`, `AppEnum`, common data types, queries,
`AppShortcutsProvider`, parameter summaries and visual presentation, donations and
discovery, the App Intents extension target, `AppIntentError`, and testing via
AppIntentsTesting. Route widgets/Controls/Live Activities to the deferred slice with
a one-line pointer — do not cover them.

---

## OUT OF SCOPE (Phase 6)

Recorded so a future phase finds them listed rather than having to rediscover them.
All are live and return 200; none is cut for being stale or broken.

### Foundation Models sections cut — advanced, well past first adoption
`OUT OF SCOPE (Phase 6): Dynamic profiles`
- `FoundationModels/composing-dynamic-sessions-with-instructions-and-profiles`
- `FoundationModels/origami-crafting-a-dynamic-tutorial-for-apple-intelligence`
- `FoundationModels/DynamicInstructions`, `DynamicInstructionsForEach`
- `FoundationModels/LanguageModelSession/DynamicProfile`, `/DynamicProfileModifier`, `/Profile`

`OUT OF SCOPE (Phase 6): Custom language model provider`
- `FoundationModels/running-a-core-ai-model-in-a-foundation-models-session`
- `FoundationModels/optimizing-key-value-caching-in-language-model-sessions`
- `FoundationModels/LanguageModel`, `LanguageModelCapabilities`, `LanguageModelExecutor`,
  `LanguageModelExecutorGenerationChannel`, `LanguageModelExecutorGenerationRequest`

`OUT OF SCOPE (Phase 6): Custom session properties`
- `FoundationModels/LanguageModelSession/SessionProperty`
- `FoundationModels/SessionPropertyKey`, `SessionPropertyValues`, `SessionPropertyEntry()`

Each is a clean later addition to an existing skill, not a new phase.

### App Intents children deferred with the widget slice
`OUT OF SCOPE (Phase 6):`
- `AppIntents/widgets-live-activities-and-controls` — a coherent future phase; the
  `widgetkit` and `activitykit` primers hold the ground meanwhile. The seam is
  Apple's own child boundary, not one we invented.
- `AppIntents/app-schema-domains`
- `AppIntents/visual-intelligence`
- `AppIntents/hardware-interactions`
- `AppIntents/focus`

### Classical ML — cut for capacity, not for value
`OUT OF SCOPE (Phase 6): Vision / Speech / Core ML / Create ML.`
The spec withdrew the original "these are old and stable so model priors are
reliable" rationale as **false** on 2026-09-02: Vision is now a Swift-native request
API (`DetectBarcodesRequest`, `ClassifyImageRequest`, `ImageProcessingRequest`) and
Speech is module-based (`SpeechAnalyzer`, `SpeechTranscriber`, `AssetInventory`),
with the `VN`-prefixed and `SFSpeechRecognizer`-era types that dominate priors filed
under the framework's own **"Legacy API"** heading. That is the *same* stale-priors
condition that justifies a Foundation Models reference. The honest label is **cut for
capacity** — this phase is already double any prior one. Strongest Phase 7 candidate;
**do not re-argue it on "the model already knows it" grounds.**
Cached indexes for the eventual phase:
`index-vision.json`, `index-speech.json`.

---

## CROSS-REF (not distilled here)

- `FoundationModels/analyzing-the-runtime-performance-of-your-foundation-models-app`
  → **`apple-performance`** (`profiling-workflow.md`). Note for that distiller:
  Xcode ships a **Foundation Models instrument** with a token-usage timeline, named
  in `managing-the-context-window`.
- `FoundationModels/evaluating-prompts-to-measure-performance-and-improve-model-responses`
  and `Evaluations/evaluating-language-model-responses` → prompt-evaluation surface.
  Not distilled this phase; recorded because it postdates the primer and belongs with
  whichever future phase takes evaluation seriously.
