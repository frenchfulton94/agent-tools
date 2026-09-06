# Locale Detection and i18n Routing

Contents:

- [Built-in strategies](#built-in-strategies)
- [Choosing a strategy array](#choosing-a-strategy-array)
- [How urlPatterns work](#how-urlpatterns-work)
- [Pattern cookbook](#pattern-cookbook)
- [Ordering rules](#ordering-rules)
- [routeStrategies](#routestrategies)
- [Client-side redirects](#client-side-redirects)
- [Multi-tenancy](#multi-tenancy)
- [Troubleshooting](#troubleshooting)

## Built-in strategies

| Strategy            | Reads from                                | Availability                                                                                 |
| ------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------- |
| `url`               | Pathname/domain via `urlPatterns`         | Both. Server-side, only for document requests (`Sec-Fetch-Dest: document`)                   |
| `cookie`            | `PARAGLIDE_LOCALE` cookie                 | Both — the only persistent option the server sees on the first request                       |
| `localStorage`      | `PARAGLIDE_LOCALE` key                    | Browser only; skipped on the server                                                          |
| `preferredLanguage` | `navigator.languages` / `Accept-Language` | Both. Tries exact match (`en-US`) then base language (`en`)                                  |
| `globalVariable`    | In-memory global                          | Testing, and SSG where `setLocale()` stores the build-time locale. Unsafe for concurrent SSR |
| `baseLocale`        | `settings.json`                           | Always resolves — terminal fallback                                                          |
| `custom-*`          | Whatever you define                       | See api.md                                                                                   |

## Choosing a strategy array

Evaluated left to right; first non-`undefined` wins.

```js
[
	'url',
	'baseLocale'
] // URL is the source of truth (SEO sites)
[
	('localStorage', 'cookie', 'url', 'baseLocale')
] // returning visitors keep their choice
[
	('localStorage', 'cookie', 'preferredLanguage', 'url', 'baseLocale')
] // auto-detect, override sticks
[('cookie', 'baseLocale')]; // app with no localized URLs
```

Two rules decide most of these:

- Anything after a wildcard `url` entry never runs, because the default pattern matches every path.
- In SSR, the server sees `cookie` and `preferredLanguage` on the first request but never `localStorage`. A `localStorage`-only override therefore loses the initial render, and the server may redirect to a different locale than the client would pick. Pair it with `cookie`.

## How urlPatterns work

Each entry maps one canonical route to one localized form per locale:

```js
{
  pattern: "/about",            // canonical route your app actually serves
  localized: [
    ["de", "/ueber-uns"],       // [locale, localized path]
    ["en", "/about"],
  ],
}
```

Incoming `/ueber-uns` resolves to locale `de` and de-localizes to `/about`. Outgoing `localizeHref("/about", { locale: "de" })` returns `/ueber-uns`. Syntax is the web-standard [URLPattern](https://urlpattern.com) — test patterns there before shipping them.

Omitting `urlPatterns` entirely gives locale prefixes for non-base locales (`/about`, `/de/about`), which is the common case and needs no config.

## Pattern cookbook

Prefix non-base locales only:

```js
{ pattern: "/:path(.*)?", localized: [["de", "/de/:path(.*)?"], ["en", "/:path(.*)?"]] }
```

Prefix every locale (SvelteKit/Next `[locale]` route segments, and SSG generally). The dedicated `/` entry is what prevents a homepage redirect loop:

```js
urlPatterns: [
	{
		pattern: '/',
		localized: [
			['en', '/en'],
			['fr', '/fr']
		]
	},
	{
		pattern: '/:path(.*)?',
		localized: [
			['en', '/en/:path(.*)?'],
			['fr', '/fr/:path(.*)?']
		]
	}
];
```

Translated pathnames, with a wildcard fallback for untranslated routes:

```js
urlPatterns: [
	{
		pattern: '/about',
		localized: [
			['en', '/about'],
			['de', '/ueber-uns']
		]
	},
	{
		pattern: '/products/:id',
		localized: [
			['en', '/products/:id'],
			['de', '/produkte/:id']
		]
	},
	{
		pattern: '/:path(.*)?',
		localized: [
			['en', '/:path(.*)?'],
			['de', '/:path(.*)?']
		]
	}
];
```

When a path is identical across locales (that last entry), the URL cannot identify the locale — fallback strategies decide it.

Unprefixed section inside an otherwise prefixed site:

```js
{ pattern: "/dashboard/:path(.*)?",
  localized: [["en", "/dashboard/:path(.*)?"], ["de", "/dashboard/:path(.*)?"]] }
```

Subdomains — the localhost entry is mandatory or local dev never localizes:

```js
urlPatterns: [
	{
		pattern: 'http://localhost::port?/:path(.*)?',
		localized: [
			['en', 'http://localhost::port?/en/:path(.*)?'],
			['de', 'http://localhost::port?/de/:path(.*)?']
		]
	},
	{
		pattern: 'https://example.com/:path(.*)?',
		localized: [
			['en', 'https://example.com/:path(.*)?'],
			['de', 'https://de.example.com/:path(.*)?']
		]
	}
];
```

Base path, using URLPattern's optional-group syntax `{shop/}?` so the pattern matches with and without the prefix:

```js
{ pattern: "/{shop/}?:path(.*)?",
  localized: [["en", "/{shop/}?en/:path(.*)?"], ["de", "/{shop/}?de/:path(.*)?"]] }
```

Route unavailable in one locale — point it at the 404:

```js
{ pattern: "/specific-path", localized: [["en", "/specific-path"], ["de", "/de/404"]] }
```

## Ordering rules

Both levels of the array are first-match-wins.

- **Across patterns:** specific before wildcard. A leading `/:path(.*)?` makes every later entry unreachable.
- **Within one `localized` array:** prefixed before unprefixed. Listing `["en", "/:path(.*)?"]` first makes it swallow `/de/about` during de-localization, so the German URL never maps back to `/about`.

## routeStrategies

URLPattern has no negative lookahead, so you cannot exclude `/api/*` inside `urlPatterns`. Use `routeStrategies`, matched in declaration order, first match wins:

```ts
routeStrategies: [
	{ match: '/dashboard/:path(.*)?', strategy: ['cookie', 'baseLocale'] },
	{ match: '/rpc/:path(.*)?', strategy: ['cookie', 'baseLocale'] },
	{ match: '/api/:path(.*)?', exclude: true } // no locale redirect, no de-localization
];
```

`strategy` and `exclude` are mutually exclusive on one rule.

## Client-side redirects

`paraglideMiddleware` canonicalizes document requests server-side. `shouldRedirect()` exposes the same decision for SPAs and for post-hydration navigations:

```ts
const decision = await shouldRedirect({ url: window.location.href });
if (decision.shouldRedirect) window.location.href = decision.redirectUrl.href;
```

TanStack Router — in a `beforeLoad` hook, `throw redirect({ to: decision.redirectUrl.href })`. SvelteKit — call it from the root `+layout.svelte` in `onMount` and `afterNavigate`.

Perform locale-changing redirects as full document navigations (`window.location.href`), including same-origin ones. SvelteKit's `goto()` and `setLocale(..., { reload: false })` both leave a stale document shell whose `<html lang>` and server-rendered data belong to the old locale.

This is a supplement to server-side detection, not a replacement: it runs too late to fix the first document request.

## Multi-tenancy

One config can serve different defaults per domain — give each tenant its own pattern:

```js
urlPatterns: [
	{
		pattern: 'http://localhost::port?/:path(.*)?',
		localized: [
			['fr', 'http://localhost::port?/fr/:path(.*)?'],
			['en', 'http://localhost::port?/:path(.*)?']
		]
	},
	{
		pattern: 'https://customer1.fr/:path(.*)?',
		localized: [
			// French default
			['fr', 'https://customer1.fr/:path(.*)?'],
			['en', 'https://customer1.fr/en/:path(.*)?']
		]
	},
	{
		pattern: 'https://customer2.com/:path(.*)?',
		localized: [
			// English default
			['en', 'https://customer2.com/:path(.*)?'],
			['fr', 'https://customer2.com/fr/:path(.*)?']
		]
	}
];
```

Restrict locales per tenant by mapping the unsupported ones to `/404`, and filter the tenant's locale switcher to the supported set so users never click through to it.

## Troubleshooting

| Symptom                                  | Cause                                                                                                                                                                      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "No locale found"                        | Empty `strategy`; overrides not called at the entrypoint; messages called outside a request context; or `strategy: ["url"]` alone on an API request                        |
| Redirect loop                            | Middleware and framework both de-localizing (pass the original request), or a missing dedicated `/` pattern when all locales are prefixed, or trailing-slash normalization |
| Switcher changes URL, text unchanged     | Client-side navigation with no reload — use `setLocale()` or a reloading link                                                                                              |
| Locale bleeds between requests           | `disableAsyncLocalStorage: true` in a concurrent server                                                                                                                    |
| `getLocale()` returns the wrong locale   | Called outside the `paraglideMiddleware` callback                                                                                                                          |
| Stored preference ignored on first paint | `localStorage` is invisible to the server; add `cookie`                                                                                                                    |
| Pattern silently ignored                 | An earlier wildcard matched first                                                                                                                                          |

To debug, log inside the middleware callback (`request.url` → `locale`) and check `localizeHref("/about", { locale: "de" })` against expectations.
