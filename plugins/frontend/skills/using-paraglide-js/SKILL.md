---
name: using-paraglide-js
description: Writes, configures, and debugs internationalization with Paraglide JS (@inlang/paraglide-js) and inlang message files. Use when the user mentions Paraglide, inlang, project.inlang, paraglideVitePlugin, paraglideMiddleware, or a generated paraglide/ directory; when they want to add or fix translated messages, pluralization, locale detection, locale switching, or localized URLs in a Vite, SvelteKit, TanStack Start or Router, React Router, Next.js, Astro, or Node server app that uses Paraglide; and when they are adopting it alongside or in place of i18next or react-intl. Also use on symptoms without the library named - "no locale found", locale bleeding between concurrent SSR requests, redirect loops on locale-prefixed URLs, hydration mismatches on language, or a language switcher that changes the URL but leaves the text unchanged.
license: MIT
---

# Using Paraglide JS

Paraglide compiles inlang message files into typed, tree-shakable ESM functions. Your app imports and calls those functions directly. There is no provider, no context, no hook, no `t()`, and no async loading of translation bundles; a design that needs one of those has been imported from a runtime i18n library and does not belong here.

This skill targets `@inlang/paraglide-js` **v2**, which renamed most of the v1 API and deleted its framework adapter packages. v1-era code does not compile against v2 and v1-era snippets are still widespread, so confirm the installed version before writing anything.

## Before writing code, read the project

Paraglide's behavior is decided almost entirely by config the agent cannot guess. Read these four things first; skipping them produces code that contradicts the project's own setup.

1. `package.json` — the `@inlang/paraglide-js` major version.
2. `project.inlang/settings.json` — `baseLocale`, `locales`, and `modules` (the `modules` entry determines message file syntax — see [Message syntax follows the plugin](#message-syntax-follows-the-plugin)).
3. The compiler config — `paraglideVitePlugin({...})` in the bundler config, or a `paraglide-js compile` script, or a `compile()` call. Note `outdir`, `strategy`, and `urlPatterns`.
4. `<outdir>/README.md` — the compiler emits this file describing the exact generated API for _this_ project. It is the authoritative reference when it exists.

For a project with none of this yet, `npx @inlang/paraglide-js@latest init` scaffolds it.

## The API surface

Three generated entry points, and nothing else:

```ts
import { m } from './paraglide/messages.js'; // message functions
import { getLocale, setLocale, locales, localizeHref } from './paraglide/runtime.js'; // locale + URL helpers
import { paraglideMiddleware } from './paraglide/server.js'; // SSR only

m.hello_world(); // "Hello World!"
m.greeting({ name: 'Ada' }); // parameters are one object argument
m.greeting({ name: 'Ada' }, { locale: 'de' }); // render in a specific locale
```

`import * as m from "./paraglide/messages.js"` also works. Message functions return `LocalizedString`, a branded string type you can require in props to keep untranslated literals out of the UI.

These names appear constantly in pre-v2 code and in model memory. They do not exist in v2:

| Do not write                                                                               | Write instead                                                               |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| `languageTag()`                                                                            | `getLocale()`                                                               |
| `setLanguageTag()`                                                                         | `setLocale()`                                                               |
| `onSetLanguageTag(cb)`                                                                     | `overwriteSetLocale(fn)`                                                    |
| `availableLanguageTags`                                                                    | `locales`                                                                   |
| `sourceLanguageTag` (settings)                                                             | `baseLocale`                                                                |
| `m.greeting({...}, { languageTag })`                                                       | `m.greeting({...}, { locale })`                                             |
| `import { paraglide } from "@inlang/paraglide-vite"`                                       | `import { paraglideVitePlugin } from "@inlang/paraglide-js"`                |
| `@inlang/paraglide-sveltekit`, `@inlang/paraglide-astro`, `@inlang/paraglide-js-adapter-*` | Nothing — the core package covers every framework                           |
| `<ParaglideJS>` wrapper, `i18n.route()`                                                    | Nothing — use `paraglideMiddleware` server-side and `localizeHref` in links |

`@inlang/paraglide-js-react` (and the `-svelte`, `-vue`, `-solid` siblings) do exist and are current, but they only render rich-text markup via `<ParaglideMessage>`. They are not providers and supply no hooks. See `references/message-format.md`.

## Switching locale is a document navigation

`setLocale()` updates the configured strategies and then performs a full document navigation — to the localized URL when URL routing is on, otherwise a reload. This is the design, not a limitation: the new document renders the app, `<html lang>`, `dir`, and server-rendered data together.

```ts
import { setLocale } from "./paraglide/runtime.js";

<button onClick={() => setLocale("de")}>Deutsch</button>  // ✅
```

Two failure modes to avoid:

- **A plain link is not a locale switcher.** `<a href={localizeHref("/page", { locale: "de" })}>` changes the URL, but under client-side routing the framework navigates without reloading and the text stays in the old locale. Either call `setLocale()`, or force a document navigation on the link (SvelteKit: `data-sveltekit-reload`).
- **`setLocale(locale, { reload: false })` is not "the nicer way to avoid a flash."** It updates strategies and nothing else — no re-render, no URL change, no `<html lang>` update. It is for a fully client-rendered surface that owns its whole reactive shell and must preserve unsaved in-memory work, such as an embedded widget or extension options page. Never use it on a route whose strategy includes `url`, or with `experimentalPerLocaleBuild`; `getLocale()` will keep returning the old locale.

To preview another locale without switching, pass `{ locale }` to the message call instead.

## Strategy order is a fallthrough chain

`strategy` is evaluated left to right and the first entry that returns a locale wins. Default: `["cookie", "globalVariable", "baseLocale"]`.

The trap: with the default `urlPatterns`, `url` matches every path via a `/:path(.*)?` wildcard, so it _always_ resolves. Anything after `url` is dead code.

```js
strategy: ['url', 'localStorage', 'cookie']; // ❌ last two never run
strategy: ['localStorage', 'cookie', 'url', 'baseLocale']; // ✅ preference wins, url is the fallback
```

End the array with `baseLocale` so a locale always resolves. Add `cookie` whenever an SSR app needs a stored preference to affect the first document request — the server cannot read `localStorage`, so a `localStorage`-only override silently loses the initial render and causes hydration mismatches.

Use `routeStrategies` for per-route exceptions (unprefixed `/dashboard` reading from cookie, `/api` excluded from i18n entirely). URLPattern has no negative lookahead, so excluding paths inside `urlPatterns` is not possible — `routeStrategies` is the mechanism.

## Server rendering

Wrap the request in `paraglideMiddleware`. It detects the locale, redirects document requests to the canonical localized URL, de-localizes the URL for your app, and scopes the locale to the request with `AsyncLocalStorage`.

```ts
export function handle(request: Request) {
	return paraglideMiddleware(request, async ({ request, locale }) => {
		return renderApp(request);
	});
}
```

- Call messages **inside** the callback. `m.hello()` at module scope on the server has no request context and throws "no locale found".
- Keep `AsyncLocalStorage` enabled. Disabling it in a concurrent server leaks one request's locale into another. It is a compatibility fallback for runtimes lacking `node:async_hooks`, not a performance knob.
- If the framework already rewrites localized URLs (TanStack Router's `rewrite.input`/`output`), pass the **original** request to your handler, not the callback's — both de-localizing produces an infinite redirect loop.
- Behind a proxy or TLS terminator, pass `effectiveRequestUrl` so redirects target the browser-facing URL.
- The middleware does not set the locale cookie. `setLocale()` on the client does, or set `Set-Cookie` yourself.

SSG has no request, so there is no middleware: set the locale per page with `setLocale()` for sequential builds, or `overwriteGetLocale()` for concurrent rendering (React). See `references/frameworks.md`.

## Message syntax follows the plugin

Message files are plain data whose syntax is set by the plugin in `project.inlang/settings.json` — the default inlang message format, i18next, JSON, or ICU MessageFormat 1. Writing ICU `{count, plural, one {# item} other {# items}}` into a project using the default inlang format produces a literal string, not a plural. Check `modules` before authoring, and match the syntax already present in the existing message files.

Two rules that hold across plugins:

- **Keep keys resolvable at build time.** `m[someRuntimeString]()` defeats tree-shaking and type safety. Build an explicit map instead: `const nav = { home: m.calm_green_otter, about: m.bright_coral_fox }`.
- **Prefer flat, stable, meaningless keys** (`calm_green_otter`) for new messages — renaming a semantic key breaks translation history and every call site at once. Never rename established keys just to adopt this style, and give independently-evolving messages separate keys even when today's text is identical.

## Gotchas

- Locale-prefixed URLs need a dedicated `pattern: "/"` entry before the wildcard when the base locale is also prefixed, or the homepage redirect-loops.
- Within one pattern's `localized` array, list the prefixed locale before the unprefixed one — a generic entry first swallows every URL during de-localization.
- With `strategy: ["url"]` alone, API requests get no locale: URL extraction only applies to document requests (`Sec-Fetch-Dest: document`). Add `cookie` or `baseLocale`.
- Domain-based routing needs a separate `http://localhost::port?/...` pattern or local dev never localizes.
- Custom strategy names must start with `custom-`. Client-side `getLocale` must be synchronous; server-side may be async.
- `emitTsDeclarations: true` needs TypeScript 5.6+ and keeps the language server in sync when keys change; without it, set `allowJs: true` in `tsconfig.json`.
- URLPattern treats `/about` and `/about/` as different paths.

## Verify before reporting done

- [ ] Every runtime import resolves against the generated `runtime.js` — no `languageTag`/`availableLanguageTags`/adapter packages
- [ ] Locale switching goes through `setLocale()` or a reloading link, not a client-routed `<a>`
- [ ] Nothing after a wildcard `url` entry in `strategy`; array ends in `baseLocale`
- [ ] Server-side message calls sit inside the `paraglideMiddleware` callback
- [ ] New message syntax matches the plugin already configured in `project.inlang/settings.json`
- [ ] Message keys are static; any dynamic lookup goes through an explicit map

## Where to look

- `references/api.md` — full `runtime.js`/`server.js` export list and compiler options, when you need a signature, a default value, or a helper you have not used before.
- `references/routing.md` — when the task involves `urlPatterns`, translated pathnames, domain or multi-tenant routing, `routeStrategies`, or client-side redirects.
- `references/message-format.md` — when authoring or editing message files: parameters, plurals and variants, number/date/relative-time formatting, rich-text markup, arrays.
- `references/frameworks.md` — when wiring a specific framework (SvelteKit, TanStack, React Router, Astro, Next.js, Hono/Express/Fastify/Elysia), SSG, or a monorepo.
- `references/migration.md` — when upgrading from Paraglide 1.x, or adopting Paraglide alongside i18next or another existing i18n library.
