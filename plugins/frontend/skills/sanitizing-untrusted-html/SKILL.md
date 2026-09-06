---
name: sanitizing-untrusted-html
description: Sanitizes untrusted HTML with DOMPurify, including server-side use on jsdom — wiring, config choice, hooks, and verification against known bypass classes. Use when user-submitted or third-party HTML, Markdown output, or email bodies get rendered into a page; when DOMPurify comes up, or jsdom is used to host a sanitizer in Node; when guarding against XSS from rendered markup; and when reviewing or tightening an existing sanitizer config or hook. Also use on symptoms where no library is named — "is this safe to put in innerHTML", "strip the dangerous tags out of this", "my sanitizer eats too much of the content", a sanitize call that throws "sanitize is not a function", or a Node process that never exits after sanitizing.
license: MIT
---

# Sanitizing Untrusted HTML

DOMPurify parses untrusted markup into an inert DOM, walks it, and keeps only what is on its allow-list. Its **secure defaults are the product**: nearly every real-world bypass comes from a config that widened the allow-list, a hook that wrote back into cleaned output, or post-processing after the sanitize call. Aim for the smallest configuration that renders the content correctly.

## The three rules that prevent most incidents

1. **Sanitize with defaults unless you have a stated reason not to.** `DOMPurify.sanitize(dirty)` already blocks script, event handlers, `javascript:` URLs, mXSS and DOM clobbering.
2. **Narrow, never widen.** `ALLOWED_TAGS`/`ALLOWED_ATTR` and `FORBID_*` only remove capability and stay safe. `ADD_TAGS`, `ADD_ATTR`, `ADD_URI_SAFE_ATTR`, `ALLOW_UNKNOWN_PROTOCOLS` and `CUSTOM_ELEMENT_HANDLING` re-admit it — each needs a reason written down.
3. **Sanitize for the exact sink, and insert the result untouched.** Any string edit after `sanitize()` voids it. `clean.replace('<a ', '<a target="_blank" ')` on clean output happily accepts `onmouseover` injected next to it, and HTML sanitized for `innerHTML` is not safe dropped into SVG, `<style>`, `<textarea>`, or an attribute value.

## Wiring it up in Node

DOMPurify needs a DOM. In Node the module's default export is a **factory** — calling `.sanitize()` on it directly throws `DOMPurify.sanitize is not a function`, which is the single most common way this integration fails.

Build the window once at module scope and reuse it. Constructing a `JSDOM` per call measured **16× slower** over 200 sanitize calls, and buys nothing.

```js
// sanitize.js — one window, one DOMPurify, for the process lifetime
import { JSDOM } from 'jsdom';
import createDOMPurify from 'dompurify';

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

if (!DOMPurify.isSupported) {
	throw new Error('DOMPurify is not supported on this DOM; refusing to serve unsanitized HTML.');
}

export const sanitize = (dirty) => DOMPurify.sanitize(dirty);
```

Keep `jsdom` current and pinned. The DOM you run on is part of your trusted computing base — DOMPurify's maintainers document known XSS vectors in older jsdom that DOMPurify cannot defend against however correctly it behaves, and they consider `happy-dom` unsafe for this purpose. In a browser bundle, skip jsdom entirely and use `DOMPurify.sanitize` against the real `window`.

If a short-lived script or test hangs instead of exiting, an un-closed jsdom window is holding a timer open; call `window.close()` when done. Long-lived servers keep the single window for the process lifetime and never close it.

## Picking a configuration

Start at the top of this list and stop at the first row that renders your content.

| Situation                                                      | Configuration                                                                                                                     |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Rich text from users, anything general                         | `sanitize(dirty)` — no config                                                                                                     |
| Plain rich text: CMS bodies, rendered Markdown, email previews | `{ USE_PROFILES: { html: true } }` — drops SVG and MathML, the namespace-confusion surface                                        |
| Comments, tightly-scoped formatting                            | `{ ALLOWED_TAGS: ['b','i','em','strong','a','p','ul','ol','li','code','pre','br','blockquote'], ALLOWED_ATTR: ['href','title'] }` |
| Inserting into the DOM you control, no string round-trip       | `{ RETURN_DOM_FRAGMENT: true }` then `element.replaceChildren(fragment)`                                                          |

`USE_PROFILES` overrides `ALLOWED_TAGS`, so never pass both. `FORBID_TAGS`/`FORBID_ATTR` win over the `ADD_*` equivalents — rely on that when a config gets complicated. If you do not need CSS, drop it: `FORBID_TAGS: ['style']`, `FORBID_ATTR: ['style']`. DOMPurify keeps CSS but does not sanitize it, so CSS-based exfiltration is yours to own.

Read `references/config-reference.md` before setting any flag not shown above, and whenever reviewing a config someone else wrote — it lists every option with its default and what widening it costs.

## Hooks

Hooks are the supported way to add behavior beyond allow-listing. Three edges to know.

**`afterSanitize*` hooks run after validation and their output is never re-checked.** An `afterSanitizeAttributes` hook copying a user-controlled value into `href` emits `<a href="javascript:alert(1)">` in the final output. Put attacker-influenced values through `uponSanitizeElement` / `uponSanitizeAttribute` instead, which run _before_ validation so their output is re-checked; the same payload through `uponSanitizeAttribute` is dropped. Reserve `afterSanitize*` for values you fully control, like setting a constant `target="_blank"`.

**Hooks are global to the DOMPurify instance and persist across every later call.** A hook added inside a request handler silently applies to every subsequent request. Register hooks once at module scope beside the instance, or pair each `addHook` with `removeHook`/`removeAllHooks`.

To keep an attribute from inside a hook, prefer `data.keepAttr` / `hookEvent.forceKeepAttr` over writing `data.allowedAttributes[name] = true`; the latter is persistent-shaped and has repeatedly leaked across elements and calls.

Read `references/hooks.md` for the full hook list, the shape of each hook event, and working recipes (forcing `target="_blank"`, URI-scheme allow-lists, proxying resource URLs, SVG for `<img>`).

## Persistent configuration

`DOMPurify.setConfig(cfg)` persists until `clearConfig()` — and while it is set, **per-call config is ignored entirely**. Passing `{ FORBID_ATTR: ['href'] }` to `sanitize()` after a `setConfig()` call has no effect whatsoever. Reach for `setConfig` only where one process-wide policy serves every call site; anywhere two call sites need different rules, pass config per call.

## Gotchas that defy reasonable assumptions

- A top-level `<style>` or `<template>` parses into `<head>` and therefore vanishes from default output; it survives only nested in body content or under `WHOLE_DOCUMENT: true`.
- `KEEP_CONTENT: false` drops the text of removed elements _and_ of allowed ones unless `#text` is on `ALLOWED_TAGS`. `{ ALLOWED_TAGS: ['p'], KEEP_CONTENT: false }` returns `<p></p>`; adding `'#text'` returns `<p>keep this</p>`.
- `DOMPurify.removed` under-reports — a run that stripped a `<script>`, an `onerror` and an `<iframe>` listed only two of the three. It is a debugging aid, never a security signal or audit log.
- `iframe` + `srcdoc` is the classic self-inflicted hole: `srcdoc` holds a whole nested document that DOMPurify does not recurse into, so allowing both makes `<iframe srcdoc="<img src=x onerror=...>">` live again.
- Server-side DOMs parse `<noscript>` with scripting _disabled_, so its contents are treated as markup rather than text — a parse-asymmetry footgun that does not reproduce in a browser. Leave `noscript` forbidden.
- Leave jsdom's `runScripts` and `resources` at their defaults on a sanitizing window. Both are off by default; jsdom's sandbox is explicitly not foolproof, so `runScripts: "dangerously"` against untrusted input runs attacker code with your process's privileges.

## Verify before calling it done

Run the corpus against the actual config you are shipping:

```bash
node scripts/verify-sanitizer.mjs --config '{"ALLOWED_TAGS":["b","a"],"ALLOWED_ATTR":["href"]}'
```

It sanitizes ~20 public regression vectors (mXSS, rawtext breakouts, clobbering, URL sinks, engine-deferred mutation), **re-parses each result and asserts on the resulting tree** rather than substring-matching the output string, and exits non-zero if anything stayed live. It also names every surface-widening flag in the config. If code execution is unavailable, work through `references/attack-classes.md` by hand instead — it carries the same vectors with the reasoning behind each.

Then confirm by reading the integration:

- [ ] One window and one DOMPurify instance at module scope, `isSupported` checked
- [ ] Config only narrows, or every widening flag has a written reason
- [ ] Nothing edits the sanitized string between `sanitize()` and the sink
- [ ] The sink matches what was sanitized for (HTML into an HTML sink)
- [ ] No `afterSanitize*` hook writes attacker-influenced values
- [ ] Hooks registered once at module scope, not per request

## Where to look

- `references/config-reference.md` — every config option, its default, and the cost of changing it. Load before setting an unfamiliar flag or auditing someone else's config.
- `references/hooks.md` — hook list, event shapes, and recipes. Load when adding behavior beyond allow-listing.
- `references/attack-classes.md` — the attack families and their test vectors. Load when building a test corpus, reviewing a proposed widening, or when code execution is unavailable for the verify step.
- `references/jsdom-notes.md` — jsdom options, `fromURL`/`fromFile`/`fragment`, virtual consoles, and its documented limits. Load when the task uses jsdom for more than hosting a sanitizer window.
