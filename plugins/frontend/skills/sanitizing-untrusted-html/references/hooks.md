# DOMPurify Hooks

Contents:

- [The hook points](#the-hook-points)
- [Signature and hook event](#signature-and-hook-event)
- [Managing hooks](#managing-hooks)
- [Safety rules](#safety-rules)
- [Recipes](#recipes)

## The hook points

Registered with `DOMPurify.addHook(name, callback)`:

| Hook                       | Runs                                                           |
| -------------------------- | -------------------------------------------------------------- |
| `beforeSanitizeElements`   | Before element sanitization begins, per node                   |
| `uponSanitizeElement`      | For **every** element as it is checked (note: no trailing "s") |
| `afterSanitizeElements`    | After element sanitization, per node                           |
| `beforeSanitizeAttributes` | Before attribute sanitization, per node                        |
| `uponSanitizeAttribute`    | For every attribute as it is checked                           |
| `afterSanitizeAttributes`  | After attribute sanitization, per node                         |
| `beforeSanitizeShadowDOM`  | Before shadow-root sanitization                                |
| `uponSanitizeShadowNode`   | Per node inside a shadow root                                  |
| `afterSanitizeShadowDOM`   | After shadow-root sanitization                                 |

The `upon*` hooks sit at the decision points inside the walk. The `before*`/`after*` hooks bracket each phase.

## Signature and hook event

```js
DOMPurify.addHook('uponSanitizeAttribute', function (currentNode, hookEvent, config) {
	// hookEvent carries verified node/attribute data for `upon*` hooks.
	// For other hook types it is null.
});
```

For `uponSanitizeElement`, the event carries `tagName` and the `allowedTags` map. For `uponSanitizeAttribute`, it carries `attrName`, `attrValue`, `keepAttr`, `forceKeepAttr`, and `allowedAttributes`.

Mutating the event changes what DOMPurify does with the current node: setting `data.attrValue` rewrites the value that then goes through validation; setting `data.keepAttr = true` keeps an attribute that would otherwise be dropped; `forceKeepAttr` keeps it without further checks.

## Managing hooks

```js
DOMPurify.addHook('beforeSanitizeAttributes', fn);
DOMPurify.removeHook('beforeSanitizeAttributes'); // removes the last hook of that type, and returns it
DOMPurify.removeHooks('beforeSanitizeAttributes'); // removes all hooks of that type
DOMPurify.removeAllHooks();
```

## Safety rules

**`afterSanitize*` output is never re-validated.** That is the defining purpose of an "after" hook, and it is the most common way an application reintroduces a payload the sanitizer already removed. Verified behavior:

```js
// Reintroduces XSS — output is <a data-url="javascript:alert(1)" href="javascript:alert(1)">
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
	if (node.hasAttribute('data-url')) node.setAttribute('href', node.getAttribute('data-url'));
});

// Safe — runs before validation, so the rewritten value is checked and dropped
DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
	if (data.attrName === 'data-url') data.attrName = 'href';
});
```

Put attacker-influenced values through `uponSanitize*`. Reserve `afterSanitize*` for values you fully control.

**Prefer `data.keepAttr` over `data.allowedAttributes[name] = true`.** Both keep an attribute from inside a hook, but writing to `allowedAttributes` is the persistent-shaped tool and has repeatedly caused cross-call and cross-element leaks. `keepAttr` and `forceKeepAttr` are per-element and cannot leak.

**Hooks are global to the instance and persist across calls.** Registering inside a request handler applies the hook to every later request in the process. Register once at module scope, or pair `addHook` with removal.

## Recipes

### Force every link to open in a new window

Constant values, so `afterSanitizeAttributes` is appropriate here.

```js
DOMPurify.addHook('afterSanitizeAttributes', function (node) {
	if ('target' in node) node.setAttribute('target', '_blank');
	if (
		!node.hasAttribute('target') &&
		(node.hasAttribute('xlink:href') || node.hasAttribute('href'))
	) {
		node.setAttribute('xlink:show', 'new');
	}
});
```

`target="_blank"` enables reverse tabnabbing via `window.opener`; add `rel="noopener"` in the same hook or enforce it downstream.

### Restrict URI schemes beyond the default set

```js
const allowlist = ['http', 'https', 'ftp'];
const regex = RegExp('^(' + allowlist.join('|') + '):', 'gim');

DOMPurify.addHook('afterSanitizeAttributes', function (node) {
	const anchor = document.createElement('a');
	for (const attr of ['href', 'action', 'xlink:href']) {
		if (node.hasAttribute(attr)) {
			anchor.href = node.getAttribute(attr);
			if (anchor.protocol && !anchor.protocol.match(regex)) node.removeAttribute(attr);
		}
	}
});
```

This only ever removes, so an after-hook is safe. Under jsdom, `document` here must be the jsdom window's document.

### Remove an element together with its content

`ALLOWED_TAGS` strips a tag but keeps its text, and `FORBID_TAGS` cannot be combined with `ALLOWED_TAGS`. Allow the tag so the hook can see it, then remove the node:

```js
DOMPurify.setConfig({ ALLOWED_TAGS: ['div', '#text', 'footer'] });
DOMPurify.addHook('uponSanitizeElement', (node) => {
	if (node.tagName === 'FOOTER') node.remove();
});
```

### Drop empty leftovers

```js
DOMPurify.addHook('uponSanitizeElement', (node) => {
	if (!node.hasChildNodes() && !node.textContent) node.remove();
});
```

### Proxy outbound links

Useful for de-referrer behavior and controlling where links point.

```js
DOMPurify.addHook('afterSanitizeAttributes', function (node) {
	for (const attr of ['action', 'href', 'xlink:href']) {
		if (node.hasAttribute(attr)) {
			node.setAttribute(attr, proxy + encodeURIComponent(node.getAttribute(attr)));
		}
	}
});
```

DOMPurify does not reliably stop HTML that requests external resources — there are too many ways to do it, and HTTP leaks are an explicit non-goal. The project's `demos/hooks-proxy-demo.html` is a comprehensive starting point covering inline styles, `@media`, `@font-face` and `@keyframes`, and stripping `@charset`/`@import`.

### Re-add namespaces for SVG rendered via `<img>`

Sanitization strips the `xmlns` declarations that tools like Illustrator emit, which an `<img>`-embedded SVG needs:

```js
DOMPurify.addHook('afterSanitizeAttributes', function (node) {
	if (node.tagName && node.tagName.toLowerCase() === 'svg') {
		node.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
		node.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
	}
});
const clean = DOMPurify.sanitize(dirty, { ADD_TAGS: ['filter'] });
```

### Sanitizing CSS

DOMPurify is not a CSS sanitizer and does not inspect CSS inside allowed `<style>` elements or `style` attributes. To constrain it, walk `node.sheet.cssRules` in an `uponSanitizeElement` hook and keep only declarations on a small property allow-list, as `demos/hooks-sanitize-css-demo.html` does. The simpler answer is to drop CSS entirely with `FORBID_TAGS: ['style']` and `FORBID_ATTR: ['style']`.
