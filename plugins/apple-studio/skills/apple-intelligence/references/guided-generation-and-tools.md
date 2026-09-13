> verified: 2026-09 against https://developer.apple.com/documentation/FoundationModels/generating-swift-data-structures-with-guided-generation, https://developer.apple.com/documentation/FoundationModels/Generable, https://developer.apple.com/documentation/foundationmodels/generable(description:), https://developer.apple.com/documentation/foundationmodels/guide(description:), https://developer.apple.com/documentation/foundationmodels/guide(description:_:), https://developer.apple.com/documentation/FoundationModels/GenerationGuide, https://developer.apple.com/documentation/FoundationModels/Generable/PartiallyGenerated, https://developer.apple.com/documentation/foundationmodels/generable/aspartiallygenerated(), https://developer.apple.com/documentation/FoundationModels/Generable/generationSchema, https://developer.apple.com/documentation/FoundationModels/GenerationSchema, https://developer.apple.com/documentation/FoundationModels/DynamicGenerationSchema, https://developer.apple.com/documentation/FoundationModels/GeneratedContent, https://developer.apple.com/documentation/FoundationModels/GeneratedContent/isComplete, https://developer.apple.com/documentation/foundationmodels/generatedcontent/value(_:forproperty:), https://developer.apple.com/documentation/FoundationModels/GeneratedContent/Kind-swift.enum, https://developer.apple.com/documentation/FoundationModels/ConvertibleToGeneratedContent, https://developer.apple.com/documentation/FoundationModels/ConvertibleFromGeneratedContent, https://developer.apple.com/documentation/FoundationModels/PromptRepresentable, https://developer.apple.com/documentation/FoundationModels/expanding-generation-with-tool-calling, https://developer.apple.com/documentation/FoundationModels/generate-dynamic-game-content-with-guided-generation-and-tools, https://developer.apple.com/documentation/FoundationModels/Tool, https://developer.apple.com/documentation/FoundationModels/GenerationOptions, https://developer.apple.com/documentation/FoundationModels/GenerationOptions/toolCallingMode-swift.property, https://developer.apple.com/documentation/FoundationModels/GenerationOptions/ToolCallingMode-swift.struct, https://developer.apple.com/documentation/FoundationModels/LanguageModelSession/ToolCallError, https://developer.apple.com/documentation/FoundationModels/LanguageModelError, https://developer.apple.com/documentation/FoundationModels/LanguageModelSession, https://developer.apple.com/documentation/Vision/OCRTool, https://developer.apple.com/documentation/Vision/BarcodeReaderTool
> sources: live Apple docs (no book input — the corpus predates these frameworks)

# Guided generation and tools

## Why typed generation beats parsing free text

Without guided generation, `respond(to:)` gives you a `String`, and every
downstream consumer becomes a parser: regex, JSON-mode prompting-and-praying,
or a retry loop when the model's "JSON" has a trailing comma. Guided
generation flips the failure mode. Describe a Swift type with `@Generable`,
and the framework converts it to a JSON schema, hands that to the model, and
constrains sampling so the model is structurally incapable of emitting a
token sequence outside the grammar. There is no parse step to fail — the
value either arrives as your type or the call throws, so error handling
moves from "is this valid JSON" to "did the framework have context room for
this schema" and "is the content semantically right" — the failure modes
actually worth designing for.

The cost is context, not correctness: every `Generable` type, `@Guide`
description, and `Tool` you attach is serialized into the model's context
on each request — real budget, not free documentation. Neither Apple's
docs (4096) nor a runtime measurement on the currently shipping OS is *the*
number to design against; read `SystemLanguageModel.contextSize` /
`tokenCount(for:)` at runtime. Session-level context accounting and
overflow (`LanguageModelError`) live in `foundation-models-sessions.md`.

## Generable and Guide

`@Generable` attaches to a `struct`, `actor`, or `enum` (including enums
with associated values) to make it a valid response or tool-output type.
`@Guide(description:)` goes on stored properties to explain their semantics
in natural language, and — critically — to attach programmatic constraints
via `GenerationGuide` static members: `.range(_:)`, `.count(_:)`,
`.minimumCount(_:)`, `.maximumCount(_:)`, `.constant(_:)`, `.anyOf(_:)`,
`.pattern(_:)`, `.element(_:)`, `.minimum(_:)`, `.maximum(_:)`. Properties
generate in declaration order.

```swift
@Generable(description: "Basic profile information about a cat")
struct CatProfile {
    var name: String                                    // no guide needed
    @Guide(description: "The age of the cat", .range(0...20))
    var age: Int
}
```

`Generable` types nest freely inside other `Generable` types — a nested
type must itself be `Generable`. Only add a `Guide` description when it
changes behavior; a clearly-named property (`age: Int`) often needs
nothing, and a long description is pure context tax for no quality gain.
`@Generable` also synthesizes `PromptRepresentable` conformance — the
protocol a value needs to be interpolated into a prompt or returned as a
`Tool.Output`. Don't hand-override `promptRepresentation` on a `Generable`
type: the docs call overriding it a performance/correctness risk; write
your own conformance only for non-`Generable` types.

## Static schemas vs `DynamicGenerationSchema` — reach for dynamic rarely

`GenerationSchema` is the compiled, static description of a type's shape.
`@Generable` generates one for you (`YourType.generationSchema`); you
essentially never construct one by hand for a type you can write at
compile time.

Go to `DynamicGenerationSchema` only when the *shape* isn't known until
runtime — a restaurant's menu fetched from a server, a plugin-defined field
set, a user-configured form. That's the entire justification. Even then
you needn't go fully dynamic: `DynamicGenerationSchema(type:guides:)`
wraps an existing static `Generable` type as one branch of a dynamic tree,
and `(referenceTo:)` lets schemas reference each other by name — a typical
case is one variable leaf stitched onto static structure. Assemble named
`DynamicGenerationSchema.Property` values (e.g. an `anyOf:` leaf
enumerating a menu's daily soups), compile with `GenerationSchema
(root:dependencies:)`, pass the result to `session.respond(to:schema:)`,
and pull values back off the returned `GeneratedContent` with
`value(_:forProperty:)`. Compiling is throwing: conflicting property
names, undefined references, or duplicate types surface as
`GenerationSchema.SchemaError` — a config bug to validate once at startup,
not a per-request one, since a compile-time type could never be internally
inconsistent this way.

## `GeneratedContent` and the conversion protocols

`GeneratedContent` is the framework's untyped currency for structured
output — "a single value, an array, or key-value pairs with unique keys."
It's what a dynamic-schema request returns instead of a concrete type, and
what a `Tool` can return directly when its output doesn't map cleanly onto
a `Generable` struct. Pull typed values out with `value(_:)` /
`value(_:forProperty:)`; `kind` (`GeneratedContent.Kind`) exposes which
JSON-shaped case it holds; `jsonString`/`debugDescription` are for logging.
Two protocols bridge it to your own types: `ConvertibleToGeneratedContent`
(implement `generatedContent`) and `ConvertibleFromGeneratedContent`
(implement `init(_:) throws`). `@Generable` synthesizes both; write them
by hand only for a type you want in guided generation without a full
`Generable` schema — e.g. a `Tag` wrapper whose `generatedContent` is
`GeneratedContent(properties: ["raw": raw])` and whose `init(_:) throws`
reads back `content.value(String.self, forProperty: "raw")` — for a type
you don't own and can't attach `@Generable` to directly.

## Partial and streaming generated values

`streamResponse(to:generating:...)` yields partial values as generation
proceeds instead of one final struct. Every `Generable` type gets a
synthesized `PartiallyGenerated` associated type (`asPartiallyGenerated()`
returns it); on a struct, every stored property turns `Optional` — a field
reads `nil` until generated, and stays set once it is.

```swift
let stream = session.streamResponse(to: "Generate a cute rescue cat", generating: CatProfile.self)
for try await partial in stream {
    partial.content.name   // String? — filled in once the model emits it
}
```

Design UI around "fields appear in declaration order," not "redraw a
diff." A list bound to a `[SubType]` property grows one element at a time;
a text field should skeleton-load until its property is non-`nil`, not
wait for the whole object. At the raw `GeneratedContent` level,
`isComplete` tells you whether that piece is finished — useful when
consuming `GeneratedContent` directly (dynamic-schema path) rather than a
typed `PartiallyGenerated`. Session streaming plumbing (`ResponseStream`,
cancellation): `foundation-models-sessions.md`.

## The `Tool` protocol and the call loop

A `Tool` is how the model reaches into your app: query a database, call an
existing framework (`Contacts`, `HealthKit`), or perform a side effect.
Conform a `Sendable` type — the framework runs tools concurrently,
including the same tool called multiple times in parallel (e.g. weather
for three cities in one turn) — with `name`/`description` (injected into
context so the model knows when to call it; keep it as tight as the
`Guide` rule above, since it's paid for every turn the tool is attached), a
nested `Arguments` type (normally `@Generable`, so call arguments arrive
through the same guided-generation machinery as any other output), and
`func call(arguments: Arguments) async throws -> Output`, where `Output`
must conform to `PromptRepresentable` — in practice `String`, any
`Generable` type, or `GeneratedContent`.

```swift
struct BreadDatabaseTool: Tool {
    let name = "searchBreadDatabase"
    let description = "Searches a local database for bread recipes."

    @Generable
    struct Arguments {
        @Guide(description: "The type of bread to search for")
        var searchTerm: String
        @Guide(description: "The number of recipes to get", .range(1...6))
        var limit: Int
    }
    @Generable
    struct Recipe { var name: String; var description: String; var link: String }

    func call(arguments: Arguments) async throws -> [Recipe] { [] }
}
// Attach it: LanguageModelSession(tools: [BreadDatabaseTool()])
```

The loop: tools attach at session creation; on each `respond`/
`streamResponse` call, the framework puts every attached tool's name,
description, and argument schema into context. The model decides per turn
whether it needs a tool. If so, it generates `Arguments` through the same
constrained sampling as any other guided generation, the framework decodes
them and invokes `call(arguments:)`, and your `Output` goes back into the
model's context as the tool's result — the model can then answer directly
or chain into another call ("back-to-back tool calls" when one tool's
output feeds the next). You own the tool instance's lifetime and any state
it holds across calls; the framework only owns call sequencing.

`GenerationOptions(toolCallingMode:)` — `.required` / `.allowed` /
`.disallowed` — forces or forbids tool use for one request: `.required`
when you hold UI-state context the model doesn't and must ground the
answer in a tool, `.disallowed` when the session already has what it needs
and a call would just add latency. **There is no fourth "automatic" case to
look for:** `toolCallingMode` is `Optional` and its default is literally `nil`
— verified by printing `GenerationOptions().toolCallingMode` on macOS 27.0,
which yields `nil`, against `Optional(...Kind.required)` when set. Unset means
unset; the model decides. Forcing `.required` needs an
exit: a tool throws, or a later request drops back to `.allowed`. This
type is documented "iOS/macOS 27.0 BETA" alongside `LanguageModelError`;
both typechecked cleanly against Xcode 27.0 (27A5228h) here, unlike
`SystemLanguageModel.variant` — re-verify against your own toolchain.

## Error handling inside a tool

Throw from `call(arguments:)` for anything that should abort the model's
use of that tool — missing permissions, a timing-out dependency, a state
your tool can't service. The session wraps your error in
`LanguageModelSession.ToolCallError`, carrying `.tool` (which tool failed)
and `.underlyingError` (your thrown error, downcastable to your own type):

```swift
enum MyToolError: Error { case databaseIsEmpty }

do {
    _ = try await session.respond(to: "Find a recipe for tomato soup.")
} catch let error as LanguageModelSession.ToolCallError {
    print(error.tool.name)
    if case .databaseIsEmpty = error.underlyingError as? MyToolError { /* handle */ }
} catch {
    // any other session error — see safety-availability-and-errors.md
}
```

When a tool throws, the framework rolls the session's transcript back to
the last known-good state rather than leaving a half-formed tool call in
history — full transcript/retry-policy semantics live in
`foundation-models-sessions.md`. The alternative to throwing is returning a
short explanatory string as `Output` ("Cannot access the database") and
letting the model react in natural language instead of unwinding the call
— prefer that when the model can reasonably talk around the failure; throw
when it can't.

## Vision's first-party tools: check before you build

Before writing a `Tool` for something perceptual, check whether Apple
already shipped one. Two `Vision` types conform to `Tool` directly, usable
by adding an instance to a session's `tools:` array with no `Arguments`/
`call` implementation of your own:

- `OCRTool` — recognizes text in an image, returns it as a string.
- `BarcodeReaderTool` — scans machine-readable codes, returns an array of
  `Barcode` results (decoded content plus symbology).

Both accept `init(name:description:)` overrides for a task-specific
name/description, and both are documented unavailable in Simulator —
testing needs a real device. These are the only Vision surface in scope
here; the rest, including running your own Core ML model through it, is
deferred — don't reach past these two conformances.

## Classic pitfalls

- **`Tool.Output` must be `PromptRepresentable`, not merely `Encodable`.**
  Apple's own tool-calling guide states the rule correctly ("a string, a
  `GeneratedContent` object, or any `@Generable` type"), then shows a
  `WeatherTool` returning a plain `Encodable` `Forecast` as `Output` —
  that sample does not typecheck (confirmed with `swiftc -typecheck`
  against Xcode 27.0: `error: type 'WeatherTool' does not conform to
  protocol 'Tool'`). `Codable` conformance does not satisfy `Output`.
- **Don't hand-write `promptRepresentation` on a `@Generable` type.** The
  synthesized conformance is the one the framework is tuned against.
- **`.required` tool-calling mode with no exit condition loops forever.**
  Arrange for a tool to throw or the mode to drop back to `.allowed`.
- **`OCRTool`/`BarcodeReaderTool` don't run in Simulator.** A feature only
  ever tested in Simulator looks fine until the first device run.

## Cross-references

- Session lifecycle, `Instructions`/`Prompt`, streaming plumbing,
  transcripts, attachments, availability: `foundation-models-sessions.md`.
- `LanguageModelError`/`SystemLanguageModel.Error`, guardrails, the
  unavailable state, PCC: `safety-availability-and-errors.md`.
- Whether a feature should use guided generation/tools at all, and what it
  costs: `apple-frameworks/references/primers/foundation-models.md`.
- `Sendable`/concurrency rules for tools: `swift-concurrency`; token-usage
  profiling via the Foundation Models Instrument: `apple-performance`.
