# Behavior test cases: using-paraglide-js

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence from the response.

Cases 1–3 are the must-pass set: they target failures baselines reproduce
reliably, because Paraglide v2 renamed the v1 API and inverts the mental
model of every runtime i18n library a model has seen more of.

## Case 1 — Locale switcher in a React + Vite SPA

**Prompt:** "I've got Paraglide set up in my React + Vite app with English and German. Write me a language switcher component."

**Assertions:**

1. Imports come from the generated `./paraglide/runtime.js` and `./paraglide/messages.js` only.
2. Uses `setLocale()`, `getLocale()`, and `locales` — not `setLanguageTag()`, `languageTag()`, or `availableLanguageTags`.
3. No provider, context, `useTranslation` hook, `t()` helper, or `@inlang/paraglide-js-adapter-*` import is introduced. (Baselines reliably fail this: they scaffold an i18next-shaped provider around Paraglide.)
4. The switcher calls `setLocale()` on click rather than rendering a client-routed `<a href={localizeHref(...)}>` as the sole mechanism.
5. Does not reach for `setLocale(locale, { reload: false })` to "avoid a full reload"; if `reload: false` appears at all, it is scoped to a client-only surface and its trade-offs are stated.

## Case 2 — Strategy ordering

**Prompt:** "Here's my Vite config. Users pick a language and it persists, but on a hard refresh they're back to whatever the URL says. Fix it.

```ts
paraglideVitePlugin({
	project: './project.inlang',
	outdir: './src/paraglide',
	strategy: ['url', 'localStorage', 'cookie', 'baseLocale']
});
```

"

**Assertions:**

1. Identifies that the `url` strategy resolves on every path via the default wildcard, so `localStorage` and `cookie` are never evaluated.
2. Proposed fix moves the preference strategies before `url` and keeps `baseLocale` last.
3. Notes that `localStorage` is invisible to the server, so an SSR app needs `cookie` for the first document request. (Or explicitly establishes the app is client-only before omitting this.)
4. Does not invent a nonexistent option (`priority`, `fallback`, `defaultLocale`) to solve it.

## Case 3 — Server-side "no locale found"

**Prompt:** "SvelteKit app. `m.welcome()` throws 'no locale found' but only when I call it from `src/lib/email.ts`. Works fine in components."

**Assertions:**

1. Attributes the error to calling a message outside a request context rather than to a missing config value.
2. Fix is to call the message inside the `paraglideMiddleware` callback / a `load` function / a request-scoped path — or to pass an explicit `{ locale }` to the message call.
3. Does not recommend `overwriteGetLocale(() => 'en')` at module scope as the fix without flagging cross-request locale leakage.
4. If AsyncLocalStorage is discussed, it is kept enabled; `disableAsyncLocalStorage` is not offered as a fix.

## Case 4 — Pluralization in the default message format

**Prompt:** "Add a message that says '1 item in cart' / '5 items in cart' to my messages/en.json. We're using the default inlang setup."

**Assertions:**

1. Checks or names the plugin in `project.inlang/settings.json` as the thing that determines syntax.
2. Produces the declarations/selectors/match variant shape, not bare ICU `{count, plural, one {# item} other {# items}}` inside a default-format file.
3. Uses the formatter name `plural` exactly.
4. Adds the matching `de`/other-locale entry or notes that every locale needs its own arms, including categories the target locale requires.

## Case 5 — Edge: routing conflict, not a Paraglide bug

**Prompt:** "Added `paraglideMiddleware` to my TanStack Start app and now every request is an infinite redirect loop."

**Assertions:**

1. Identifies double de-localization — TanStack Router's `rewrite.input`/`output` plus the middleware — as the cause.
2. Fix passes the **original** request to the handler (`paraglideMiddleware(req, () => handler.fetch(req))`), not the callback's `request`.
3. Explains that locale detection, cookies, and AsyncLocalStorage still work when the callback's request is bypassed.
4. Does not resolve it by removing the middleware, disabling the `url` strategy, or deleting the router rewrite.

## Case 6 — Scope: recommend against the library

**Prompt:** "All our UI copy comes out of a headless CMS and the keys aren't known until runtime. Can we use Paraglide for it?"

**Assertions:**

1. States plainly that Paraglide wants build-time keys, because that is what enables type safety and tree-shaking.
2. Offers the real options — explicit CMS-ID → message-function map, or CMS returns already-localized content.
3. Says a runtime i18n library may be the better fit when most strings are only known at runtime, rather than forcing the compiler model.
4. Does not fabricate a dynamic-loading or `registerMessages()` API.
