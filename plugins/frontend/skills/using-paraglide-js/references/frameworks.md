# Framework Integration

Contents:

- [Vite (React, Vue, Solid, vanilla)](#vite-react-vue-solid-vanilla)
- [SvelteKit](#sveltekit)
- [TanStack Start and TanStack Router](#tanstack-start-and-tanstack-router)
- [React Router v7](#react-router-v7)
- [Astro](#astro)
- [Next.js](#nextjs)
- [Standalone servers](#standalone-servers)
- [Static site generation](#static-site-generation)
- [Monorepos](#monorepos)

Every setup starts with `npx @inlang/paraglide-js@latest init`.

## Vite (React, Vue, Solid, vanilla)

One plugin, no provider, no wrapper component:

```ts
import { paraglideVitePlugin } from '@inlang/paraglide-js';

export default defineConfig({
	plugins: [
		react(),
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/paraglide',
			emitTsDeclarations: true
		})
	]
});
```

A locale switcher is a button calling `setLocale`, mapped over `locales`. Nothing else is required for a client-only SPA — skip the middleware entirely.

## SvelteKit

Paraglide is SvelteKit's official i18n integration; `npx sv add paraglide` wires all of it. Four manual pieces:

1. Plugin in `vite.config.js`, typically `outdir: './src/lib/paraglide'` with `strategy: ['url', 'cookie', 'baseLocale']`.
2. `src/app.html`: `<html lang="%lang%" dir="%dir%">`.
3. `src/hooks.server.ts` — middleware plus placeholder substitution:

```ts
export const handle: Handle = ({ event, resolve }) =>
	paraglideMiddleware(event.request, ({ request: localizedRequest, locale }) => {
		event.request = localizedRequest;
		return resolve(event, {
			transformPageChunk: ({ html }) =>
				html.replace('%lang%', locale).replace('%dir%', getTextDirection(locale))
		});
	});
```

4. `src/hooks.ts` — **not** `hooks.server.ts` — the reroute hook that maps localized URLs onto canonical routes:

```ts
export const reroute: Reroute = (request) => deLocalizeUrl(request.url).pathname;
```

Cross-locale links need `data-sveltekit-reload`, or SvelteKit client-navigates and the text never changes. For prerendering, `export const prerender = true` in `+layout.ts` and expose a locale switcher linking to every locale so the crawler finds all variants. With the static adapter's SPA fallback, set `paths.relative: false` to avoid locale-prefixed 404s on assets.

## TanStack Start and TanStack Router

TanStack Router owns the route tree, loaders, navigation, and typed links; Paraglide owns locale detection, URL mapping, and messages. Paraglide runs in TanStack's CI on every router commit.

Router rewrites are the integration point:

```ts
const router = createRouter({
	routeTree,
	rewrite: {
		input: ({ url }) => deLocalizeUrl(url),
		output: ({ url }) => localizeUrl(url)
	}
});
```

Because the router already de-localizes, `server.ts` must pass the **original** request through — passing the callback's `request` gives an infinite redirect loop:

```ts
export default {
	fetch(req: Request): Promise<Response> {
		return paraglideMiddleware(req, () => handler.fetch(req)); // not ({ request }) => ...fetch(request)
	}
};
```

Set `<html lang={getLocale()}>` in `__root.tsx`. For offline-capable apps, redirect client-side in `beforeLoad` with `shouldRedirect()`. Prerendering: map paths through `localizeHref()` into `prerenderRoutes`, compiling with the CLI before the build. Typed translated pathnames can be derived from `FileRoutesByTo` and fed into `urlPatterns`.

Starter: `npx gitpick TanStack/router/tree/main/examples/react/start-i18n-paraglide start-i18n-paraglide`.

## React Router v7

Plugin into `vite.config.ts` with `outdir: "./app/paraglide"`. With the middleware future flag:

```ts
// react-router.config.ts → future: { v8_middleware: true }
// root.tsx
export const middleware: MiddlewareFunction[] = [
	(ctx, next) => paraglideMiddleware(ctx.request, () => next())
];
```

React Router's middleware API cannot hand a rewritten request to loaders before route matching, so the locale segment stays in `routes.ts`:

```ts
export default [
	...prefix(':locale?', [index('routes/home.tsx'), route('about', 'routes/about.tsx')])
] satisfies RouteConfig;
```

Keep that prefix consistent with `urlPatterns`. For translated pathnames, declare one alias route per locale pointing at the same module with distinct `id`s.

Without the middleware flag: read the locale in the root `loader`, put it in a React context, and `overwriteGetLocale(() => assertIsLocale(useContext(LocaleContextSSR)))` under `import.meta.env.SSR` so each request is scoped. Meta functions run in a separate client context and need their own `overwriteGetLocale` using the root loader's `data`.

## Astro

Two different setups — pick by output mode.

SSR (`output: "server"`): plugin in `astro.config.mjs` under `vite.plugins`, then `src/middleware.ts`:

```ts
export const onRequest = defineMiddleware((context, next) =>
	paraglideMiddleware(context.request, ({ request }) => next(request))
);
```

SSG (`output: "static"`): do **not** use `paraglideMiddleware` — it de-localizes URLs for SSR, while static pages need Astro to render each localized path. Set the locale instead:

```ts
export const onRequest = defineMiddleware((context, next) => {
	setLocale(assertIsLocale(context.currentLocale ?? baseLocale));
	return next();
});
```

Include `globalVariable` before `baseLocale` in `strategy` so `setLocale()` has somewhere to store the build-time locale, and mirror `project.inlang` locales in Astro's `i18n` config. Note `output: "server"` makes Astro ignore `getStaticPaths()` unless a route opts in with `prerender = true`.

## Next.js

App Router SSR — `middleware.ts`:

```ts
export async function middleware(request: Request) {
	return paraglideMiddleware(request, async ({ request, locale }) => NextResponse.next());
}
```

SSG/ISR renders pages concurrently, so `setLocale()` is unsafe; scope the locale per render with React `cache` plus `overwriteGetLocale`:

```tsx
const ssrLocale = cache(() => ({ locale: baseLocale }));
overwriteGetLocale(() => assertIsLocale(ssrLocale().locale));

export default function RootLayout({ children, params }) {
	ssrLocale().locale = params.locale;
	return (
		<html lang={getLocale()} dir={getTextDirection()}>
			{children}
		</html>
	);
}
```

`generateStaticParams()` returns `locales.map((locale) => ({ locale }))`. A `@/paraglide` path alias avoids brittle relative imports.

## Standalone servers

Compile via CLI in the `build`/`dev` scripts (or `compile()` at startup), then wrap requests. Hono passes `c.req.raw` straight through:

```ts
app.use('*', (c, next) => paraglideMiddleware(c.req.raw, () => next()));
```

Express and Fastify use Node req/res objects, so construct a Web `Request` from the URL, method, and headers first, run the middleware to capture `locale`, then continue. Elysia does the same inside `.derive()`. Cloudflare Workers works directly with the `fetch` handler — keep AsyncLocalStorage on with `nodejs_compat`.

## Static site generation

There is no request, so there is no middleware, and the locale must be set explicitly before each page renders.

- Sequential builds → `setLocale()` in the layout `load`/middleware.
- Concurrent rendering (React) → `overwriteGetLocale()` scoped per render.

SSG generally needs _all_ locales prefixed so each variant is a distinct file. Enumerate pages with `generateStaticLocalizedUrls()`, or the framework's own hook: SvelteKit `entries()`, Next `generateStaticParams()`, Astro `getStaticPaths()`. Crawler-based builders can also be fed hidden anchors linking each locale variant. Add `<link rel="alternate" hreflang>` tags built from `localizeHref(path, { locale })` plus an `x-default` pointing at `baseLocale`.

## Monorepos

**Pattern 1 (default):** one shared `project.inlang` at the root; every consuming package compiles it into its own `outdir` with its own `--strategy`. Allows per-app strategies at the cost of multiple compile steps.

**Pattern 2:** a dedicated `@myorg/i18n` package compiles once and exports `./messages` and `./runtime`. Single compile step, but every consumer is locked to one strategy — unusable when the web app needs `url` and another needs `cookie`. Use `--emit-ts-declarations` so consumers get types.

Shared UI packages should not detect locale themselves. Either accept already-translated strings as props, or compile the UI package with `strategy: baseLocale` and let each app inject its own runtime once at startup via `overwriteGetLocale`/`overwriteSetLocale`. In SSR, inject the app's request-scoped `getLocale` function rather than a concrete locale value.
