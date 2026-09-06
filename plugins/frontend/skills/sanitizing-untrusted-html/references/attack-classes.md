# Attack Classes and Test Vectors

Defensive reference drawn from DOMPurify's public regression suite and wiki. Every payload here corresponds to a class that was once a real bypass and now has a regression test. Use them as test vectors for your own pipeline. If you find a working bypass against a current release, report it privately through the project's security advisories rather than publishing it.

Contents:

- [Rule zero: sanitization is contextual](#rule-zero-sanitization-is-contextual)
- [Mutation XSS](#mutation-xss)
- [Rawtext and RCDATA breakouts](#rawtext-and-rcdata-breakouts)
- [Nesting, depth, and foster-parenting](#nesting-depth-and-foster-parenting)
- [DOM clobbering](#dom-clobbering)
- [Cross-realm and IN_PLACE input](#cross-realm-and-in_place-input)
- [Template-expression injection](#template-expression-injection)
- [Custom elements and prototype pollution](#custom-elements-and-prototype-pollution)
- [Engine-deferred mutation](#engine-deferred-mutation)
- [Self-inflicted bypasses](#self-inflicted-bypasses)
- [How to test](#how-to-test)

## Rule zero: sanitization is contextual

A sanitizer's output is only safe if the context it is re-inserted into parses it the same way the sanitizer did. DOMPurify's own suite tests three re-insertion contexts for this reason: `element.innerHTML = clean`, `jQuery(...).html(clean)` (which does extra parsing before insertion), and `document.write` / `iframe.contentDocument.write` (a fresh parsing context).

A string inert under `innerHTML` is not automatically inert under every other sink. That gap is the root of most of what follows.

## Mutation XSS

The payload looks harmless right after `sanitize()`, then the parser mutates it into executable markup when the string is serialized and re-parsed. The sanitizer inspected one tree; the browser later built a different one.

**Namespace confusion (HTML ↔ SVG ↔ MathML).** Foreign-content elements switch the tokenizer into a mode where the same bytes nest differently, so markup that reads as benign foreign content breaks out into HTML on re-parse.

```html
<svg></p><style><a id="</style><img src=1 onerror=alert(1)>"></svg>
<math><mtext><table><mglyph><style><img src onerror=alert(1)>
```

Defense: track the namespace of every node and forbid unsanctioned foreign-to-HTML transitions. Never disable the namespace check. HTML-only applications should use `USE_PROFILES: { html: true }` and remove the surface entirely.

**Foreign-content integration points.** Some foreign elements have children parsed as HTML despite sitting inside SVG/MathML — `<math><annotation-xml encoding="text/html">` and `<svg><foreignObject>`. Wrapping a text-only legacy element such as `<xmp>` inside one mixes parsing modes:

```html
<math><annotation-xml encoding="text/html"><xmp><img src=x onerror=alert(1)></xmp></annotation-xml></math>
<svg><foreignobject><xmp><img src=x onerror=alert(1)></xmp></foreignobject></svg>
```

**Re-contextualization via wrapper elements.** Markup benign in one context becomes live when re-inserted inside a rawtext wrapper (`script`, `xmp`, `iframe`, `noembed`, `noframes`, `noscript`).

## Rawtext and RCDATA breakouts

`noscript`, `noembed`, `noframes`, `xmp`, `textarea`, `title` and `style` switch the tokenizer into text-only mode. A closing tag embedded in an **attribute value** can terminate that mode early and let the rest of the attribute be re-parsed as live markup.

```html
<noscript><p title="</noscript><img src=x onerror=alert(1)>">
<noembed><img src=x onerror=alert(1)></noembed>
<style>a[href="</style><img src=x onerror=alert(1)>"]{}</style>
```

`SAFE_FOR_XML` (default on) is the narrow attribute-value guard covering this class. Do not disable it.

Server-side subtlety: in SSR and jsdom, **scripting is disabled**, so the contents of `<noscript>` parse as HTML rather than as text. This bypass class does not reproduce in a scripting-enabled browser but is very real on the server.

## Nesting, depth, and foster-parenting

The HTML parser foster-parents misplaced nodes out to a different position than where they were written:

```html
<table>
	<script>
		alert(1);
	</script>
</table>
```

Two risks: content relocation can move a node out of the subtree being inspected, so the sanitizer must evaluate the tree the parser actually produced rather than the literal nesting in the string; and deeply nested re-parenting historically caused O(n²) blow-up, so a depth cap matters.

```html
<table>
	<table>
		<table>
			… (×200)
		</table>
	</table>
</table>
```

Assert both that foster-parented script is removed and that deep nesting completes within a time bound. Prototype pollution has weakened depth checks in past versions.

## DOM clobbering

Named elements shadow JavaScript properties through the browser's named-property lookup — no script required.

```html
<form><input name="nodeName" /></form>
<form><input name="attributes" /></form>
<img src="x" name="getElementById" />
```

`form.nodeName` then resolves to the `<input>` rather than the string `"FORM"`, confusing any sanitizer logic that reads `node.nodeName` as an instance property, or making it throw and partially sanitize.

Two bounds worth knowing: clobbering yields node references, not attacker-chosen strings, and only works on elements exposing named children (forms, document, window) — it cannot make a plain `<a>` report a fake tag name. A clobbered form can also be reached via an external `form=` association from an input elsewhere in the document.

Defense: read security-sensitive properties through realm-safe cached prototype getters rather than instance properties. Controls are `SANITIZE_DOM` (on by default) and `SANITIZE_NAMED_PROPS`.

## Cross-realm and IN_PLACE input

When the input is a DOM node rather than a string, the node may come from a different realm (an iframe's document) whose prototype chain and constructors differ, so naive `instanceof` checks misbehave. The caller's live nodes are processed directly, so pre-existing state on them — including clobbering or explicitly defined property getters — is in scope.

Test by feeding a node built in a foreign realm and confirming `href="javascript:…"` is still stripped.

## Template-expression injection

When sanitized HTML is fed into a client-side template engine, `SAFE_FOR_TEMPLATES` scrubs `{{ … }}`, `${ … }` and ERB tags. A subtle bypass splits an expression across adjacent text nodes so no single node matches the regex, yet the fragments merge into a live expression after `normalize()`:

```
text node 1:  "$"
text node 2:  "{constructor.constructor(\"alert(1)\")()"
```

A sharper variant hides the split text nodes inside `<template>.content`, a separate `DocumentFragment` that a `NodeIterator` rooted at the body does not traverse.

`SAFE_FOR_TEMPLATES` is a last resort with its own history of edge bugs (CVE-2025-26791). The safer design is not passing user HTML through a second interpreter at all. Relatedly, DOMPurify does not protect against script-gadget frameworks that re-enable execution from otherwise-inert attributes.

## Custom elements and prototype pollution

With default config, unknown custom elements are rejected. Two risks: an over-broad `tagNameCheck`/`attributeNameCheck` lets arbitrary custom elements with arbitrary attributes through; and if an earlier gadget pollutes `Object.prototype`, a sanitizer initializing config with `{}` can inherit attacker-controlled check values, downgrading default-deny. DOMPurify initializes internal config with `Object.create(null)` for exactly this reason.

Prototype-pollution gadgets are common in the ecosystem, which makes this practically relevant rather than theoretical. Verify that polluting `Object.prototype.tagNameCheck` does not loosen your output.

## Engine-deferred mutation

Newer engine features mutate the DOM _after_ sanitization. Chrome's `<selectedcontent>` mirrors the selected `<option>`'s subtree into its own children after parsing, so a sanitizer inspecting only static markup misses what the engine later clones in. Declarative partial updates (`<template for=…>`, `patchsrc`) similarly teleport or fetch DOM ranges post-sanitize.

The general lesson: any feature that clones, defers, or fetches content needs post-mutation re-inspection. Keep such elements forbidden unless explicitly opted in, and re-walk the subtree after the engine populates it.

## Self-inflicted bypasses

Many reported "bypasses" are misconfigurations:

- `ADD_TAGS` / `ADD_ATTR` widen the allow-list; predicate forms must not short-circuit URI validation.
- `ALLOW_UNKNOWN_PROTOCOLS`, `ADD_URI_SAFE_ATTR`, and a loosened `ALLOWED_URI_REGEXP` re-admit dangerous schemes.
- `ALLOW_SELF_CLOSE_IN_ATTR` interacts with older jQuery's `html()` normalization.
- `WHOLE_DOCUMENT`, `RETURN_DOM`, `RETURN_DOM_FRAGMENT` change the output shape and the re-insertion contract.

The secure defaults are the product; most flags trade safety for capability and need a threat-model justification.

## How to test

Run each vector through your sanitizer in all three re-insertion contexts, and **assert on the live parsed tree, not on a substring of the output string** — encoded markup produces false negatives either way.

`scripts/verify-sanitizer.mjs` automates this for the string-plus-`innerHTML` path: it sanitizes each vector with your config, re-parses the result, and reports any surviving handler, script URL, or live element. Passing is a smoke test, not a proof of safety.

When reviewing a config rather than testing one, walk the self-inflicted-bypasses list above and require a justification for every non-default flag.
