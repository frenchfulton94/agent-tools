# Trigger battery: using-paraglide-js

## Should trigger (10)

1. "Add Paraglide to my SvelteKit app so I can support German and French."
2. "My language switcher updates the URL to /de/about but all the text stays in English."
3. "Getting 'no locale found' when I call a message from a util file on the server."
4. "How do I do pluralization in inlang message format? `{count, plural, one {# item} other {# items}}` just renders literally."
5. "We're on i18next and want to try Paraglide without rewriting all our locale JSON files."
6. "I set strategy to ['url', 'localStorage', 'cookie'] and localStorage is being ignored completely."
7. "Infinite redirect loop on my TanStack Start app after adding paraglideMiddleware."
8. "Set up localized pathnames — /about in English, /ueber-uns in German — in my project.inlang config."
9. "Upgrading from paraglide 1.x. `languageTag()` is undefined and `@inlang/paraglide-sveltekit` won't install."
10. "Users pick a language, refresh, and it resets. SSR app, Vite, paraglide."

## Should not trigger (10) — near-misses

1. "Add i18next to my Next.js app." (different library, no Paraglide signal)
2. "Translate these UI strings into Japanese." (translation content, not the library)
3. "Format this number as EUR currency with Intl.NumberFormat." (plain Intl, no messages involved)
4. "How do I use AsyncLocalStorage to trace request IDs in Express?" (shared primitive, unrelated domain)
5. "Set up a Vite plugin that injects build metadata." (Vite plugin authoring, not Paraglide)
6. "What's the best i18n library for React in 2026?" (evaluation/recommendation question — answer normally; do not assume Paraglide)
7. "My SvelteKit reroute hook is stripping the wrong path segment." (reroute exists outside Paraglide; no i18n signal)
8. "Write a URLPattern that matches /blog/:slug." (bare URLPattern question)
9. "Explain how tree-shaking works in Rollup." (mechanism question, no i18n)
10. "Our Crowdin sync is dropping keys on export." (translation management platform, no Paraglide in play)
