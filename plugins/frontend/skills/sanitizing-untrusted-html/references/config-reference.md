# DOMPurify Configuration Reference

Contents:

- [How config is applied](#how-config-is-applied)
- [Allow-list and block-list](#allow-list-and-block-list)
- [URI and protocol control](#uri-and-protocol-control)
- [Custom elements](#custom-elements)
- [Return type](#return-type)
- [Parsing and sanitization behavior](#parsing-and-sanitization-behavior)
- [Trusted Types](#trusted-types)
- [Dangerous tags: think twice before allow-listing](#dangerous-tags-think-twice-before-allow-listing)
- [Dangerous attributes](#dangerous-attributes)
- [Removed options](#removed-options)

## How config is applied

Per call: `DOMPurify.sanitize(dirty, config)`. Persistent: `DOMPurify.setConfig(config)`, cleared with `DOMPurify.clearConfig()`.

There is only one active configuration. While a persistent config is set, **every per-call config argument is ignored** — including `TRUSTED_TYPES_POLICY: null` and a per-call `FORBID_ATTR`. `clearConfig()` also drops any caller-supplied Trusted Types policy.

Incoming config is cloned and internal config is created prototype-free, because prototype pollution is a realistic precondition rather than a theoretical one: a `|| {}` fallback inheriting from `Object.prototype` was a real default-config bypass (CVE-2026-41238, fixed in 3.4.0), and `USE_PROFILES` array pollution was another (GHSA-cj63-jhhr-wcxv).

## Allow-list and block-list

| Option                             | Default       | Effect                                                                                                                      |
| ---------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `ALLOWED_TAGS`                     | built-in list | Replaces the tag allow-list entirely. Include `'#text'` to keep text nodes when `KEEP_CONTENT: false`.                      |
| `ALLOWED_ATTR`                     | built-in list | Replaces the attribute allow-list entirely.                                                                                 |
| `USE_PROFILES`                     | unset         | `{ html, svg, svgFilters, mathMl }` booleans. **Overrides `ALLOWED_TAGS`** — never pass both.                               |
| `FORBID_TAGS`                      | `[]`          | Removes tags from the effective allow-list. Wins over `ADD_TAGS`.                                                           |
| `FORBID_ATTR`                      | `[]`          | Removes attributes. Wins over `ADD_ATTR`.                                                                                   |
| `ADD_TAGS`                         | `[]`          | Extends the allow-list. Also accepts a predicate `(tagName) => boolean`. Widens surface.                                    |
| `ADD_ATTR`                         | `[]`          | Extends the allow-list. Also accepts `(attributeName, tagName) => boolean`. Widens surface.                                 |
| `FORBID_CONTENTS`                  | built-in list | Tags whose _children_ are dropped when the tag is removed.                                                                  |
| `ADD_FORBID_CONTENTS`              | `[]`          | Extends `FORBID_CONTENTS` rather than replacing it.                                                                         |
| `KEEP_CONTENT`                     | `true`        | Keep the text of removed elements. Setting `false` also drops text of allowed elements unless `#text` is in `ALLOWED_TAGS`. |
| `ALLOW_ARIA_ATTR`                  | `true`        | Permit `aria-*`.                                                                                                            |
| `ALLOW_DATA_ATTR`                  | `true`        | Permit `data-*`. Set `false` if your app ever reads `data-*` as a URL or HTML.                                              |
| `ALLOWED_NAMESPACES` / `NAMESPACE` | HTML          | Change the default namespace. Do not set without a specific reason.                                                         |

`ALLOWED_TAGS` strips a tag but keeps its content. To remove an element _and_ everything inside it, allow the tag and remove the node in an `uponSanitizeElement` hook — the node must be on the allow-list for the hook to see it.

For the exact built-in defaults, see the project's [Default TAGs & ATTRIBUTEs allow-list & blocklist](https://github.com/cure53/DOMPurify/wiki/Default-TAGs-ATTRIBUTEs-allow-list-&-blocklist) wiki page.

## URI and protocol control

| Option                    | Default   | Effect                                                             |
| ------------------------- | --------- | ------------------------------------------------------------------ |
| `ALLOWED_URI_REGEXP`      | see below | The pattern URL-bearing attribute values must match.               |
| `ALLOW_UNKNOWN_PROTOCOLS` | `false`   | Admits arbitrary URI schemes.                                      |
| `ADD_URI_SAFE_ATTR`       | `[]`      | Marks attributes as URI-safe, **skipping URL validation on them**. |
| `ADD_DATA_URI_TAGS`       | `[]`      | Extends which elements may carry `data:` URIs.                     |

Default permitted schemes: relative and protocol-relative URLs, `http`, `https`, `ftp`, `ftps`, `tel`, `mailto`, `callto`, `sms`, `cid`, `xmpp`, and `matrix`. The default pattern is:

```
/^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
```

A custom `ALLOWED_URI_REGEXP` is tested against attacker-controlled strings, so a catastrophically-backtracking pattern is an attacker-triggerable denial of service. Supply only linear-time patterns; DOMPurify cannot detect a pathological one for you.

## Custom elements

`CUSTOM_ELEMENT_HANDLING` — default-deny, and deliberately restrictive:

```js
{
  CUSTOM_ELEMENT_HANDLING: {
    tagNameCheck: null,                    // null = no custom elements allowed
    attributeNameCheck: null,              // null = standard attribute allow-list
    allowCustomizedBuiltInElements: false, // no is="" customized built-ins
  }
}
```

`tagNameCheck` and `attributeNameCheck` accept a RegExp or a predicate. `attributeNameCheck` optionally receives `tagName` as a second parameter for per-element rules:

```js
{
  CUSTOM_ELEMENT_HANDLING: {
    tagNameCheck: (tag) => tag.match(/^element-(one|two)$/),
    attributeNameCheck: (attr, tag) =>
      tag === 'element-one' ? ['attribute-one'].includes(attr) : false,
    allowCustomizedBuiltInElements: false,
  }
}
```

A permissive check such as `tagNameCheck: /.*/` is a broad escape hatch: lifecycle reactions, framework hydration, and `is=` built-ins can all attach behavior after sanitization.

## Return type

| Option                | Default | Returns                                                                               |
| --------------------- | ------- | ------------------------------------------------------------------------------------- |
| _(none)_              | —       | A sanitized HTML string                                                               |
| `RETURN_DOM`          | `false` | An `HTMLBodyElement`                                                                  |
| `RETURN_DOM_FRAGMENT` | `false` | A `DocumentFragment` — avoids the serialize/reparse step and a class of mXSS concerns |
| `RETURN_TRUSTED_TYPE` | `false` | A `TrustedHTML` object where Trusted Types is available                               |

## Parsing and sanitization behavior

| Option                 | Default       | Effect                                                                                                                                                                   |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SAFE_FOR_XML`         | `true`        | Guards attribute values against comment/CDATA closers and rawtext/RCDATA closing tags. Also gates the `for`/`patchsrc` handling. Disabling removes real mXSS protection. |
| `SANITIZE_DOM`         | `true`        | DOM-clobbering protection.                                                                                                                                               |
| `SANITIZE_NAMED_PROPS` | `false`       | Prefixes user `id`/`name` with `user-content-`, isolating them from JS variable lookup. Worth enabling.                                                                  |
| `SAFE_FOR_TEMPLATES`   | `false`       | Strips `{{ … }}`, `${ … }`, `<% … %>`. Last resort — see the template-expression notes in `attack-classes.md`.                                                           |
| `WHOLE_DOCUMENT`       | `false`       | Returns the document including `<html>`, so `<head>` content such as `<style>` survives.                                                                                 |
| `FORCE_BODY`           | `false`       | Glues head-only elements to `document.body`.                                                                                                                             |
| `IN_PLACE`             | `false`       | Sanitizes a live node you pass in and returns that same node.                                                                                                            |
| `PARSER_MEDIA_TYPE`    | `'text/html'` | Set `'application/xhtml+xml'` to parse as XML.                                                                                                                           |

## Trusted Types

`RETURN_TRUSTED_TYPE: true` returns `TrustedHTML`. To use DOMPurify _inside_ your own policy, `createHTML` needs a plain string, so pass `RETURN_TRUSTED_TYPE: false`:

```js
window.trustedTypes.createPolicy('default', {
	createHTML: (input) => DOMPurify.sanitize(input, { RETURN_TRUSTED_TYPE: false })
});
```

With no `TRUSTED_TYPES_POLICY` supplied, DOMPurify creates an internal policy named `dompurify`. Under a strict CSP that does not allow that name, creation is blocked and logs a warning plus a CSP violation. Pass `TRUSTED_TYPES_POLICY: null` to opt out of the internal fallback — the right choice when calling `sanitize` from inside your own policy:

```js
window.trustedTypes.createPolicy('my-organization', {
	createHTML: (input) => DOMPurify.sanitize(input, { TRUSTED_TYPES_POLICY: null })
});
```

Never pass your own wrapping policy back as `TRUSTED_TYPES_POLICY` when that policy's `createHTML` already calls `sanitize` — it is circular, and DOMPurify throws a descriptive `TypeError` to prevent infinite recursion. Your policy calls DOMPurify; DOMPurify is not configured to call your policy.

For page-wide enforcement of this pattern across legacy code and third-party widgets, DOMFortify is the separate Cure53 project that installs such a default policy; document-wide enforcement is deliberately out of DOMPurify's scope.

## Dangerous tags: think twice before allow-listing

Two kinds of danger deserve different caution. **Foot-guns** are dangerous in an obvious, local way — an allowed `<iframe>` is risky and you know it, and DOMPurify still sanitizes it. **Landmines** are dangerous where you cannot see or fix it, often after the sanitizer has finished.

| Tag               | Default     | Why                                                                                                                                                                                                    | If you must                                                                                                  |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `selectedcontent` | forbidden   | **Landmine.** The customizable-select engine re-clones the selected `<option>`'s subtree into it _after_ DOMPurify walked the tree.                                                                    | Prefer leaving it forbidden. If unavoidable, empty its children post-walk and re-verify each engine release. |
| `iframe`          | forbidden   | Embedding/navigation primitive; `srcdoc` opens a full nested document; sandbox attrs are easy to get wrong.                                                                                            | Pin `src` to an allow-listed origin via `ALLOWED_URI_REGEXP`; never also allow `srcdoc`.                     |
| `object`, `embed` | forbidden   | Load and render arbitrary external content.                                                                                                                                                            | Avoid; constrain `data`/`type` tightly.                                                                      |
| `base`            | forbidden   | One `<base href>` rewrites **every relative URL** in the document.                                                                                                                                     | Almost never.                                                                                                |
| `form`            | **allowed** | Clobbering vector; `action`/`formaction` are navigation sinks.                                                                                                                                         | Keep `SANITIZE_DOM` on, consider `SANITIZE_NAMED_PROPS`, scrutinize actions.                                 |
| `meta`            | forbidden   | `http-equiv="refresh"`; `charset` switching is an mXSS lever.                                                                                                                                          | Hard-restrict `http-equiv`/`charset`.                                                                        |
| `link`            | forbidden   | `rel=stylesheet`, `preload`/`prefetch`, `imagesrcset`.                                                                                                                                                 | Restrict `rel` and the URL.                                                                                  |
| `style`           | allowed     | Kept, but the CSS inside is **not** sanitized.                                                                                                                                                         | `FORBID_TAGS: ['style']` when CSS is not needed.                                                             |
| `noscript`        | forbidden   | Parses differently with scripting enabled vs disabled — a classic server-side mXSS footgun.                                                                                                            | Avoid, especially server-side.                                                                               |
| `template`        | allowed     | Inert `DocumentFragment` parsed differently from live DOM; under declarative partial updates a `<template for=…>` is a post-sanitize teleport directive. DOMPurify strips the `for`/`patchsrc` wiring. | `FORBID_TAGS: ['template']` unless needed; keep `SAFE_FOR_XML` on.                                           |
| `math`, `svg`     | **allowed** | Foreign content — namespace confusion and integration points are where much mXSS lives.                                                                                                                | Fine to keep; never disable the namespace check. HTML-only apps use `USE_PROFILES: { html: true }`.          |
| custom elements   | forbidden   | Lifecycle reactions and hydration add behavior after sanitization.                                                                                                                                     | Narrow `tagNameCheck`; keep `allowCustomizedBuiltInElements: false`.                                         |

## Dangerous attributes

Several of these are allowed by default — the danger is usually turning off protection DOMPurify already applies, or reading them as a sink it never validated.

| Attribute                                                                       | Default                              | Why                                                                                                      | Guidance                                                                                          |
| ------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `on*`                                                                           | forbidden                            | Direct script execution.                                                                                 | Never allow-list.                                                                                 |
| `href`, `src`, `action`, `cite`, `poster`, `background`, `srcset`, `xlink:href` | allowed, URI-validated               | URL sinks, but the value is checked.                                                                     | Do not weaken the check via `ALLOW_UNKNOWN_PROTOCOLS`, a loosened regexp, or `ADD_URI_SAFE_ATTR`. |
| `formaction`, `data`, `ping`, `imagesrcset`                                     | forbidden                            | URL/navigation sinks not in the default list.                                                            | If added, keep URI validation — never via `ADD_URI_SAFE_ATTR`.                                    |
| `srcdoc`                                                                        | forbidden                            | **Landmine.** A complete nested HTML document; DOMPurify does not recurse into it.                       | Don't. If truly required, sanitize the inner document separately first.                           |
| `style`                                                                         | allowed                              | Inline CSS is kept but not sanitized.                                                                    | `FORBID_ATTR: ['style']` when not needed.                                                         |
| `id`, `name`                                                                    | allowed                              | DOM clobbering.                                                                                          | Enable `SANITIZE_NAMED_PROPS`; keep `SANITIZE_DOM` on.                                            |
| `data-*`                                                                        | allowed                              | DOMPurify cannot know your app later reads `data-target` as a URL or HTML.                               | Validate yourself, or `ALLOW_DATA_ATTR: false`.                                                   |
| `xmlns`                                                                         | allowed                              | Needed for SVG/MathML; misuse is namespace confusion.                                                    | Leave the namespace check on.                                                                     |
| `is`                                                                            | forbidden                            | Turns a built-in into a customized built-in with attached behavior.                                      | Avoid unless the custom-element policy is narrow.                                                 |
| `for`                                                                           | allowed on `<label>`/`<output>` only | Elsewhere it is declarative-partial-updates patch wiring that teleports DOM ranges after sanitization.   | Don't re-add it in an after-hook; keep `SAFE_FOR_XML` on.                                         |
| `patchsrc`                                                                      | forbidden                            | Fetches remote markup and applies it as a patch.                                                         | Don't add via `ADD_ATTR`.                                                                         |
| `autofocus`                                                                     | forbidden                            | Fires `onfocus` with no interaction — an execution amplifier that appeared in the CVE-2026-41238 bypass. | Don't pair with handler attributes.                                                               |
| `target`                                                                        | forbidden                            | `target=_blank` enables reverse tabnabbing via `window.opener`.                                          | Enforce `rel="noopener"` semantics downstream.                                                    |
| `dirname`                                                                       | forbidden                            | Smuggles extra form-field values on submit.                                                              | Avoid on form controls.                                                                           |

**Rule of thumb:** if allowing something means the _engine_, a _second parser_, or _your own later code_ decides whether the output executes, keep it forbidden.

## Removed options

| Option            | Removed in | Note                                                                    |
| ----------------- | ---------- | ----------------------------------------------------------------------- |
| `SAFE_FOR_JQUERY` | 2.1.0      | No replacement needed — output is safe for jQuery `.html()` by default. |
