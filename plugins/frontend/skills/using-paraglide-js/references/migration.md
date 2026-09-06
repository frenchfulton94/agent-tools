# Migration

Contents:

- [Paraglide 1.x to 2.x](#paraglide-1x-to-2x)
- [Rebuilding what the SvelteKit adapter did](#rebuilding-what-the-sveltekit-adapter-did)
- [Adopting Paraglide alongside i18next or react-intl](#adopting-paraglide-alongside-i18next-or-react-intl)

## Paraglide 1.x to 2.x

v2 renamed "language tag" to "locale" throughout and deleted the per-framework adapter packages in favour of one core package. The renames are mechanical:

| v1                                                                                         | v2                                                           |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `languageTag()`                                                                            | `getLocale()`                                                |
| `setLanguageTag()`                                                                         | `setLocale()`                                                |
| `onSetLanguageTag(cb)`                                                                     | `overwriteSetLocale(fn)`                                     |
| `availableLanguageTags`                                                                    | `locales`                                                    |
| `sourceLanguageTag` (settings)                                                             | `baseLocale`                                                 |
| `AvailableLanguageTag` (type)                                                              | `Locale`                                                     |
| `m.greeting({...}, { languageTag: x })`                                                    | `m.greeting({...}, { locale: x })`                           |
| `import { paraglide } from "@inlang/paraglide-vite"`                                       | `import { paraglideVitePlugin } from "@inlang/paraglide-js"` |
| `@inlang/paraglide-sveltekit`, `@inlang/paraglide-astro`, `@inlang/paraglide-js-adapter-*` | removed — core package only                                  |

What changed structurally, beyond names:

- **Strategies replaced adapters.** Locale detection is now compiler config (`strategy`, `urlPatterns`, `routeStrategies`) rather than an adapter's behavior.
- **`setLocale()` navigates.** v1's reactive language switching, and stores built on `onSetLanguageTag`, have no v2 equivalent by design — a locale change is a document navigation.
- **Variants arrived.** Pluralization and gendering are now supported natively; see message-format.md.
- **Keys got flexible.** Nested/dotted keys work via `m["a.b"]()`, and arbitrary key names are allowed.

Order of work: bump the dependency, delete the adapter package and its config, apply the renames, add `strategy`/`urlPatterns` to the compiler config, then rebuild locale switching and any framework wiring from `references/frameworks.md`.

## Rebuilding what the SvelteKit adapter did

`<ParaglideJS>` and `i18n.route()` are gone; the same behavior comes from three separate pieces, all covered in frameworks.md: `paraglideMiddleware` in `hooks.server.ts`, a `reroute` hook in `hooks.ts`, and `%lang%`/`%dir%` placeholders in `app.html`. Links that change locale need `data-sveltekit-reload`, which is the most common silent failure in this migration — switching appears to work in dev but the text never updates.

## Adopting Paraglide alongside i18next or react-intl

Paraglide compiles _your existing translation files_ through inlang plugins, so the two libraries can run side by side off one source of truth. No file migration is needed and there is no big-bang cutover.

1. `npx @inlang/paraglide-js@latest init`.
2. Point `project.inlang/settings.json` at your existing format and paths:

```json
{
	"baseLocale": "en",
	"locales": ["en", "de", "fr"],
	"modules": ["https://cdn.jsdelivr.net/npm/@inlang/plugin-i18next@6.0.11/dist/index.js"],
	"plugin.inlang.i18next": { "pathPattern": "./locales/{locale}.json" }
}
```

3. Use Paraglide in new code; leave existing calls alone. Both read the same files:

```ts
i18next.t('greeting', { name: 'World' }); // untouched
m.greeting({ name: 'World' }); // compiled, typed, tree-shaken
```

Convert call sites opportunistically, or keep both indefinitely.

Two things that do not translate directly:

- **`<Trans>` components** → Paraglide's markup adapters (`@inlang/paraglide-js-react` and siblings), with app-supplied renderers per tag name.
- **`returnObjects`** → `JSON.parse(m.key())`, or one message key per item when the items need interpolation.

Paraglide wants keys known at build time — that is what buys type safety and tree-shaking. For CMS-driven or fully dynamic catalogs, map content IDs to message functions explicitly, or have the CMS return already-localized content. If most strings are only known at runtime, a runtime i18n library remains the better fit; say so rather than forcing the compiler model.
