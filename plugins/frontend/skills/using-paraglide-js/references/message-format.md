# Authoring Message Files

Syntax here is `@inlang/plugin-message-format` (the inlang default). Check `modules` in `project.inlang/settings.json` first — with the i18next, JSON, or ICU plugin the file syntax differs and this page does not apply.

Contents:

- [File format plugins](#file-format-plugins)
- [Parameters](#parameters)
- [Message keys](#message-keys)
- [Variants and pluralization](#variants-and-pluralization)
- [Formatters](#formatters)
- [Markup and rich text](#markup-and-rich-text)
- [Arrays and objects](#arrays-and-objects)

## File format plugins

| Plugin                | File pattern             | Use for                                         |
| --------------------- | ------------------------ | ----------------------------------------------- |
| Inlang Message Format | `messages/{locale}.json` | New projects; full variant and markup support   |
| i18next               | `locales/{locale}.json`  | Keeping existing i18next files while migrating  |
| JSON                  | `{locale}.json`          | Plain key–value strings                         |
| ICU MessageFormat 1   | plugin-defined           | Teams that already write `{count, plural, ...}` |

Plugins are declared as URLs in `modules`, and several can be combined during a migration:

```json
{
	"baseLocale": "en",
	"locales": ["en", "de"],
	"modules": ["https://cdn.jsdelivr.net/npm/@inlang/plugin-message-format@4.4.0/dist/index.js"]
}
```

Locales live in `settings.json`; adding one there is what makes it compile.

## Parameters

```json
{ "greeting": "Hello {name}!" }
```

```ts
m.greeting({ name: 'Samuel' });
```

Inputs are one object argument. The generated types make a missing or misspelled input a compile error.

## Message keys

Prefer flat, stable, meaningless keys for new messages — `calm_green_otter`, not `login_button_label`. Semantic keys invite renames when copy or placement changes, and a rename looks to translation tooling like one deletion plus one new message, discarding history, comments, and screenshots. Sherlock (the VS Code extension) generates these keys on extraction and shows the message text inline so readability is not lost.

Do not rename established keys to adopt this convention; stability is the point. Do give independently-evolving messages separate keys even when their current text is identical — two buttons both reading "OK" today will diverge tomorrow.

Nested objects are supported via bracket notation, but flat keys compile to direct function names with go-to-definition and auto-import:

```json
{ "nav.home": "Home" }
```

```ts
m['nav.home']();
```

Dynamic access must go through an explicit map, or tree-shaking and type safety are both lost:

```ts
const navMessages = { home: m.calm_green_otter, about: m.bright_coral_fox } as const;
navMessages[item.key]();
```

## Variants and pluralization

A variant message is an array of one object with `declarations`, `selectors`, and `match`.

```json
{
	"some_happy_cat": [
		{
			"declarations": ["input count", "local countPlural = count: plural"],
			"selectors": ["countPlural"],
			"match": {
				"countPlural=one": "There is one cat.",
				"countPlural=other": "There are many cats."
			}
		}
	]
}
```

Read `local countPlural = count: plural` as "define `countPlural` as `plural(count)`". Categories come from `Intl.PluralRules` for the active locale, so locales with `few`/`many` need those arms.

Ordinals pass `type=ordinal`:

```json
{
	"finished_readout": [
		{
			"declarations": [
				"input placeNumber",
				"local ordinalCategory = placeNumber: plural type=ordinal"
			],
			"selectors": ["ordinalCategory"],
			"match": {
				"ordinalCategory=one": "You finished in {placeNumber}st place",
				"ordinalCategory=two": "You finished in {placeNumber}nd place",
				"ordinalCategory=few": "You finished in {placeNumber}rd place",
				"ordinalCategory=*": "You finished in {placeNumber}th place"
			}
		}
	]
}
```

Any inputs can be matched, not just plurals — gender, platform, A/B bucket. Use `*` for the catch-all arm and provide one for every selector combination:

```json
{
	"jojo_mountain_day": [
		{
			"match": {
				"platform=android, userGender=male": "{username} has to download the app on his phone.",
				"platform=*, userGender=*": "The person has to download the app."
			}
		}
	]
}
```

## Formatters

Exactly four names: `plural`, `number`, `datetime`, `relativetime`. `numberFormat`, `dateFormat`, and `relativeTimeFormat` are common inventions and do not exist.

```json
{
	"price_in_usd": [
		{
			"declarations": [
				"input amount",
				"local formattedAmount = amount: number style=currency currency=USD"
			],
			"match": { "amount=*": "Price: {formattedAmount}" }
		}
	],
	"purchase_date": [
		{
			"declarations": [
				"input date",
				"local formattedDate = date: datetime dateStyle=long timeStyle=short timeZone=UTC"
			],
			"match": { "date=*": "Purchase date: {formattedDate}." }
		}
	]
}
```

`number` and `datetime` forward their options to `Intl.NumberFormat` and `Intl.DateTimeFormat`. Set an explicit `timeZone` when output must be stable across environments.

`relativetime` additionally **requires** `unit`, because `Intl.RelativeTimeFormat` takes the unit as a separate argument rather than an option. Use a literal (`unit=day`) or a dynamic input (`unit=$unit`). Supported: `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`, `second`. Negative values are past, positive future; `numeric=auto` yields "yesterday"/"today"/"tomorrow".

```json
{
	"relative_update": [
		{
			"declarations": [
				"input duration",
				"input unit",
				"local formattedDuration = duration: relativetime unit=$unit style=short"
			],
			"match": { "duration=*,unit=*": "Updated {formattedDuration}." }
		}
	]
}
```

Paraglide formats the `(value, unit)` pair you hand it and never picks a unit itself — do threshold selection in app code, then call the message.

Pass raw values (`number`, `Date`, parseable date string), never pre-formatted strings, or per-locale formatting is lost.

Formatting runs at call time in the current document's locale. For a preview in another locale, pass `{ locale }` to the call rather than switching the app's locale.

## Markup and rich text

Markup lets translators place links and emphasis while the app decides how they render. Tag names are arbitrary identifiers — `{#b}` does **not** become `<b>` on its own; you always supply the renderer.

```json
{
	"cta": "{#link to=|/docs| @track}Read docs{/link}",
	"welcome": "{#b}Hi {name}{/b}{#icon/}"
}
```

- `{#tag}...{/tag}` wrapping tag; `{#tag/}` standalone.
- `name=|literal|` or `name=$variable` → `options.name`.
- `@flag` → `attributes.flag === true`; `@variant=|hero|` → `attributes.variant === "hero"`.

Calling the message plainly strips the wrappers and returns text. To render, use the framework adapter — `@inlang/paraglide-js-react`, `-svelte`, `-vue`, `-solid`:

```tsx
<ParaglideMessage
	message={m.cta}
	inputs={{}}
	markup={{
		link: ({ children, options, attributes }) => (
			<a href={options.to} data-track={attributes.track === true}>
				{children}
			</a>
		)
	}}
/>
```

Svelte uses `{#snippet link({ children, options })}` children instead of a `markup` prop. Renderer keys are type-checked against the tag names in the message: required for markup messages, rejected for plain ones. A missing wrapping-tag renderer still renders children; a missing standalone renderer renders nothing.

For custom rendering, `m.cta.parts({})` returns framework-neutral `text` / `markup-start` / `markup-end` / `markup-standalone` entries.

## Arrays and objects

There is no `returnObjects`. Store JSON as a string and parse it:

```json
{ "features": "[\"Fast\", \"Secure\", \"Easy to use\"]" }
```

```ts
const features: string[] = JSON.parse(m.features());
```

Objects need `{`/`}` escaped as `\{`/`\}` (double-escaped in JSON), so entry arrays plus `Object.fromEntries` are usually easier for translators. Interpolation does not work inside a JSON blob — when list items need parameters, use one message key per item instead.
