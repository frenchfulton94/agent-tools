# API Reference

Contents:

- [messages.js](#messagesjs)
- [runtime.js: locale state](#runtimejs-locale-state)
- [runtime.js: URL helpers](#runtimejs-url-helpers)
- [runtime.js: locale extraction](#runtimejs-locale-extraction)
- [runtime.js: validation and constants](#runtimejs-validation-and-constants)
- [runtime.js: overrides and custom strategies](#runtimejs-overrides-and-custom-strategies)
- [server.js](#serverjs)
- [Compiler options](#compiler-options)
- [Generated output layout](#generated-output-layout)
- [Invoking the compiler](#invoking-the-compiler)

## messages.js

```ts
import { m } from './paraglide/messages.js'; // or: import * as m from ...

m.key(); // no inputs
m.key({ name: 'Ada' }); // inputs object
m.key({ name: 'Ada' }, { locale: 'de' }); // per-call locale override
m['nav.home'](); // dotted keys via bracket notation
m.key.parts({ name: 'Ada' }); // markup messages only; see message-format.md
```

Returns `LocalizedString` (a branded `string`). The only option is `locale`.

## runtime.js: locale state

| Export             | Signature                                                           | Notes                                                                                            |
| ------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `getLocale`        | `() => string`                                                      | Resolves through the strategy chain; on the server reads AsyncLocalStorage set by the middleware |
| `setLocale`        | `(locale, options?: { reload?: boolean }) => void \| Promise<void>` | Full document navigation by default. Becomes async if any custom strategy's `setLocale` is async |
| `getTextDirection` | `(locale?) => "ltr" \| "rtl"`                                       | Defaults to the current locale                                                                   |
| `getUrlOrigin`     | `() => string`                                                      | Falls back to a placeholder origin off-browser; override with `overwriteGetUrlOrigin`            |

## runtime.js: URL helpers

Client-facing pair takes and returns strings, keeps relative paths, and infers the current locale:

```ts
localizeHref('/about'); // "/de/about" when locale is de
localizeHref('/about', { locale: 'fr' }); // explicit target
deLocalizeHref('/de/about'); // "/about"
```

Server-facing pair takes `URL` (or an absolute string) and always returns absolute `URL` — use these in middleware and router rewrites:

```ts
localizeUrl(url, { locale: 'de' }); // => URL
deLocalizeUrl(url); // => URL
```

Others:

- `generateStaticLocalizedUrls(urls: (string | URL)[]) => URL[]` — every locale variant of the given canonical paths. For SSG page discovery, sitemaps, and `hreflang` tags.
- `shouldRedirect(input?) => Promise<{ shouldRedirect, redirectUrl?: URL, locale }>` — the same decision `paraglideMiddleware` makes, callable anywhere. Pass `{ url }` in the browser, `{ request }` on the server, plus `effectiveRequestUrl` behind a proxy.
- `getStrategyForUrl(url)` and `isExcludedByRouteStrategy(url)` — resolve `routeStrategies` for a URL.

## runtime.js: locale extraction

Low-level readers, useful when writing a custom integration rather than using the middleware:

| Export                                             | Environment                                                                             |
| -------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `extractLocaleFromUrl(url)`                        | Both. Case-insensitive only in default routing mode; custom `urlPatterns` match exactly |
| `extractLocaleFromCookie()`                        | Browser (`document` required)                                                           |
| `extractLocaleFromNavigator()`                     | Browser (`navigator.languages`)                                                         |
| `extractLocaleFromHeader(request)`                 | Server (`Accept-Language`)                                                              |
| `extractLocaleFromRequest(request, options?)`      | Server, synchronous — skips async custom strategies                                     |
| `extractLocaleFromRequestAsync(request, options?)` | Server, required if any custom server strategy is async                                 |

Both request variants accept `{ effectiveRequestUrl }`.

## runtime.js: validation and constants

- `isLocale(value): value is string` — exact match against the project's canonical casing.
- `toLocale(value)` — case-insensitive coercion to canonical form, or `undefined`.
- `assertIsLocale(value)` — same, but throws. Common in SSG loaders: `setLocale(assertIsLocale(params.locale))`.
- Constants: `baseLocale`, `locales`, `strategy`, `urlPatterns`, `routeStrategies`, `cookieName`, `cookieMaxAge`, `isServer`, `disableAsyncLocalStorage`, `experimentalStaticLocale`, `experimentalMiddlewareLocaleSplitting`.

## runtime.js: overrides and custom strategies

- `overwriteGetLocale(fn: () => string)` and `overwriteSetLocale(fn)` — must run at the app entrypoint, before rendering, or locale resolution fails. On the server, back `overwriteGetLocale` with `AsyncLocalStorage` (or React `cache`) or concurrent requests will read each other's locale.
- `defineCustomClientStrategy(name, { getLocale, setLocale })` — `getLocale` must be synchronous; `setLocale` may be async.
- `defineCustomServerStrategy(name, { getLocale })` — may be async (database or API lookup).

Names must match `custom-<something>`; register them before the runtime is first used, and list them in the `strategy` array. A strategy returning `undefined` falls through to the next; a throwing custom strategy is isolated and also falls through.

## server.js

```ts
paraglideMiddleware<T>(
  request: Request,
  resolve: (args: { request: Request; locale: string }) => T | Promise<T>,
  options?: {
    effectiveRequestUrl?: string | URL | ((request: Request) => string | URL);
    onRedirect?: (response: Response) => void;
  }
): Promise<Response>
```

Order of operations: detect locale → redirect check (307, document requests only) → de-localize URL → open the AsyncLocalStorage scope → run `resolve`.

`disableAsyncLocalStorage` is a _compiler_ option, not a middleware argument.

## Compiler options

Required: `project` (path to `project.inlang`), `outdir`.

| Option                                                | Default                                      | Notes                                                                                                                         |
| ----------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `strategy`                                            | `["cookie", "globalVariable", "baseLocale"]` | Ordered fallthrough. Values: `url`, `cookie`, `localStorage`, `preferredLanguage`, `globalVariable`, `baseLocale`, `custom-*` |
| `urlPatterns`                                         | wildcard `/:path(.*)?`                       | See routing.md                                                                                                                |
| `routeStrategies`                                     | `[]`                                         | `{ match, strategy }` or `{ match, exclude: true }`; first match wins                                                         |
| `outputStructure`                                     | `"message-modules"`                          | `message-modules` tree-shakes best; `locale-modules` emits far fewer files (large projects, faster dev)                       |
| `emitTsDeclarations`                                  | `false`                                      | Needs TypeScript 5.6+; slower compile, reliable editor types                                                                  |
| `cookieName` / `localStorageKey`                      | `PARAGLIDE_LOCALE`                           |                                                                                                                               |
| `cookieMaxAge`                                        | `60*60*24*400` seconds                       |                                                                                                                               |
| `cookieDomain`                                        | `""`                                         | Empty scopes the cookie to the exact host. Set to share across subdomains                                                     |
| `disableAsyncLocalStorage`                            | `false`                                      | Compatibility fallback only; risks cross-request locale leaks                                                                 |
| `isServer`                                            | `typeof window === "undefined"`              | Set to `"import.meta.env.SSR"` on Vite for better tree-shaking                                                                |
| `cleanOutdir`                                         | `true`                                       |                                                                                                                               |
| `emitGitIgnore` / `emitPrettierIgnore` / `emitReadme` | `true`                                       |                                                                                                                               |
| `includeEslintDisableComment`                         | `true`                                       |                                                                                                                               |
| `additionalFiles`                                     | —                                            | `Record<filename, contents>` copied into `outdir`                                                                             |

Experimental, do not reach for unprompted: `experimentalMiddlewareLocaleSplitting` (SSR/SSG without client routing), `experimentalStaticLocale` (build-time locale constant), and the Vite 8+ `experimentalPerLocaleBuild` backend (owns `builder.buildApp`; incompatible with SvelteKit and TanStack Start, and rejects `outputStructure: "message-modules"`).

## Generated output layout

```
paraglide/
  messages/          one folder per message (message-modules) or per locale (locale-modules)
  messages.js        re-exports every message function
  runtime.js         locale state, URL helpers, strategy
  server.js          paraglideMiddleware
  README.md          generated API docs for this project
  .gitignore
```

Generated files are ignored by default — commit the message files and config, not `outdir`.

## Invoking the compiler

Bundler plugin (recommended: recompiles on message-file change, no watch process):

```ts
import { paraglideVitePlugin } from '@inlang/paraglide-js';
// also exported: paraglideWebpackPlugin, paraglideRollupPlugin,
// paraglideRspackPlugin, paraglideRolldownPlugin, paraglideEsbuildPlugin
```

CLI (CI, or no bundler) — must run before the build:

```bash
npx @inlang/paraglide-js compile --project ./project.inlang --outdir ./src/paraglide --emit-ts-declarations [--watch]
```

Programmatic: `compile(options)`. For custom output handling, `compileProject()` returns a filename→contents map and requires `@inlang/sdk`.
