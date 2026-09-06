# jsdom Notes

jsdom is a pure-JavaScript implementation of the WHATWG DOM and HTML standards for Node, aimed at emulating enough of a browser to test and scrape real applications. This covers what matters when hosting a sanitizer and when using jsdom directly.

Contents:

- [Construction and simple options](#construction-and-simple-options)
- [Script execution](#script-execution)
- [Loading subresources](#loading-subresources)
- [Virtual consoles](#virtual-consoles)
- [Cookie jars](#cookie-jars)
- [beforeParse](#beforeparse)
- [JSDOM object API](#jsdom-object-api)
- [Convenience factories](#convenience-factories)
- [Encoding sniffing](#encoding-sniffing)
- [Shutting down](#shutting-down)
- [Known limits](#known-limits)

## Construction and simple options

```js
const { JSDOM } = require('jsdom');
const dom = new JSDOM(`<!DOCTYPE html><p>Hello world</p>`);
dom.window.document.querySelector('p').textContent; // "Hello world"
```

jsdom parses the HTML like a browser, including implied `<html>`, `<head>` and `<body>`. For simple cases destructure directly:

```js
const { document } = new JSDOM(`...`).window;
```

Second-parameter options:

| Option                 | Default              | Effect                                                                                                                                                        |
| ---------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`                  | `"about:blank"`      | Value of `window.location`, `document.URL`, `document.documentURI`; affects relative-URL resolution, same-origin checks and referrer for subresources         |
| `referrer`             | none                 | Value read from `document.referrer`                                                                                                                           |
| `contentType`          | `"text/html"`        | Sets `document.contentType` and whether parsing is HTML or XML. Non-HTML/XML MIME types throw                                                                 |
| `includeNodeLocations` | `false`              | Preserves parser location info for `nodeLocation()` and correct line numbers in `<script>` stack traces. Off for performance; unusable with XML content types |
| `storageQuota`         | 5,000,000 code units | Size cap for `localStorage`/`sessionStorage` per origin                                                                                                       |
| `pretendToBeVisual`    | `false`              | `document.hidden` false, `visibilityState` `"visible"`, enables `requestAnimationFrame`/`cancelAnimationFrame`                                                |

`url` and `referrer` are canonicalized, so `"https:example.com"` becomes `"https://example.com/"`. An unparseable URL throws. `pretendToBeVisual` does not add layout or rendering.

## Script execution

Executing scripts is jsdom's most powerful ability and its most dangerous. The sandbox is not foolproof: code inside the DOM's `<script>`s can, if it tries hard enough, reach the Node.js environment and therefore your machine. Script execution is off by default.

| `runScripts`     | Behavior                                                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| unset (default)  | `<script>` elements do not execute; `window.Array`, `window.eval` etc. are the outer Node ones, so `window.eval` will not run scripts usefully    |
| `"outside-only"` | Installs fresh copies of the JS spec globals on `window`, including a working `window.eval`. Off by default only for performance — safe to enable |
| `"dangerously"`  | Executes `<script>` elements and inline event handler attributes. Only for code you know is safe                                                  |

Event handler _attributes_ (`<div onclick="">`) are governed by this setting; event handler _properties_ (`div.onclick = ...`) work regardless.

For a sanitizing window, leave `runScripts` unset. Running it against untrusted input is executing untrusted Node code.

Avoid mashing the environments together with `global.window = dom.window`. Treat jsdom like a browser and run DOM-dependent code inside it via `window.eval` or `runScripts: "dangerously"`.

## Loading subresources

By default jsdom loads no subresources. `resources: "usable"` loads frames and iframes, stylesheets via `<link rel=stylesheet>`, scripts via `<script>` (only with `runScripts: "dangerously"`), and images via `<img>` (only if the `canvas` package v3.x is installed as a peer; otherwise `<canvas>` behaves like a `<div>`).

Because `url` defaults to `about:blank`, relative URLs fail to resolve — set `url` when loading resources.

Passing an options object instead of `"usable"` opts into that behavior as a baseline and layers customization:

```js
const { JSDOM, requestInterceptor } = require('jsdom');

const dom = new JSDOM(`<script src="https://example.com/s.js"></script>`, {
	url: 'https://example.com/',
	runScripts: 'dangerously',
	resources: {
		userAgent: 'Mellblomenator/9000',
		dispatcher: new ProxyAgent('http://127.0.0.1:9001'),
		interceptors: [
			requestInterceptor((request, context) => {
				if (request.url === 'https://example.com/s.js') {
					return new Response('window.someGlobal = 5;', {
						headers: { 'Content-Type': 'application/javascript' }
					});
				}
				// return undefined to let the request proceed
			})
		]
	}
});
```

`dispatcher` takes an undici `Dispatcher` for proxies or custom TLS; `interceptors` takes undici interceptor functions. The interceptor context includes `element` — the DOM element that initiated the request, or `null`. Flow: jsdom sets up the request, passes it through `interceptors` in order, then to the `dispatcher` (undici's global by default). A `requestInterceptor` returning a `Response` short-circuits the rest.

All resource-loading customization is ignored when in-jsdom scripts use synchronous `XMLHttpRequest` — dispatchers and interceptors cannot cross a process boundary.

## Virtual consoles

By default the `JSDOM` constructor forwards all output to the Node console — both in-page `window.console` calls and jsdom's own not-implemented warnings and CSS parse errors. To silence or redirect it:

```js
const virtualConsole = new jsdom.VirtualConsole(); // no behavior at all
const dom = new JSDOM(``, { virtualConsole });

virtualConsole.forwardTo(console); // send it to Node's console
virtualConsole.forwardTo(console, { jsdomErrors: 'none' });
virtualConsole.forwardTo(console, { jsdomErrors: ['unhandled-exception', 'not-implemented'] });
```

Attach listeners before `new JSDOM()`, since errors can occur during parsing. Beyond the standard console methods there is a `"jsdomError"` event for errors from jsdom itself, with these `type` values:

| Type                    | Extra properties                        |
| ----------------------- | --------------------------------------- |
| `"css-parsing"`         | `cause` (parser exception), `sheetText` |
| `"not-implemented"`     | —                                       |
| `"resource-loading"`    | `cause`, `url`                          |
| `"unhandled-exception"` | `cause`                                 |

A silent virtual console is the usual choice for a sanitizer window: untrusted markup routinely contains CSS that fails to parse, and the default forwards that noise to your process logs.

## Cookie jars

```js
const cookieJar = new jsdom.CookieJar(store, options);
const dom = new JSDOM(``, { cookieJar });
```

Jars come from `tough-cookie`; `jsdom.CookieJar` subclasses it with `looseMode: true` because that matches browser behavior more closely. `jsdom.toughCookie` exports the packaged module instance. Useful mainly for sharing a jar across jsdoms or priming values.

## beforeParse

Runs after `Window` and `Document` exist but before any HTML is parsed — the place to shim web platform APIs jsdom lacks:

```js
const dom = new JSDOM(`<p>Hello</p>`, {
	beforeParse(window) {
		window.someCoolAPI = () => {
			/* ... */
		};
	}
});
```

## JSDOM object API

- `dom.window` — the `Window`. `dom.virtualConsole` and `dom.cookieJar` reflect what was passed or the defaults.
- `dom.serialize()` — HTML serialization of the document **including the doctype**. Contrast `dom.window.document.documentElement.outerHTML`, which omits it.
- `dom.nodeLocation(node)` — parse5 location info; requires `includeNodeLocations: true`. Returns `null` for implicitly created nodes such as `document.body`.
- `dom.getInternalVMContext()` — the contextified global for Node's `vm` module, for pre-compiling a script and running it repeatedly. Throws if the instance was created without `runScripts`.
- `dom.reconfigure({ windowTop, url })` — override `window.top` (normally `[Unforgeable]`) and change the URL from outside. Changing the URL affects all document-URL APIs, relative-URL resolution, and same-origin checks, but performs no navigation: the DOM is unchanged and no new `Window`/`Document` is created.

## Convenience factories

- `JSDOM.fromURL(url, options)` → promise of a `JSDOM`. Follows redirects. `url` and `contentType` cannot be passed; `referrer` becomes the `Referer` header; URL, content type and referrer come from the response; `Set-Cookie` responses populate the jar and existing jar cookies are sent.
- `JSDOM.fromFile(path, options)` → promise of a `JSDOM`. `url` defaults to a file URL for the path; `contentType` defaults to `application/xhtml+xml` for `.xht`/`.xhtml`/`.xml`.
- `JSDOM.fragment(string)` → a `DocumentFragment`, no `Window` or `Document` needed. Parsed using a `<template>`, so elements with awkward parsing rules like `<td>` work. The fragment has no browsing context: `ownerDocument.defaultView` is null and resources never load. All calls share one template owner document, so calls are cheap but cannot be customized with options. Serialization is awkward — for a single element, `frag.firstChild.outerHTML` works.

`JSDOM.fragment()` cannot host DOMPurify, which needs a `window`.

## Encoding sniffing

The constructor also accepts binary data (`ArrayBuffer`, `Uint8Array`, `DataView`), sniffing the encoding by scanning for `<meta charset>` like a browser. A `charset` parameter in `contentType` overrides the sniffed encoding unless a UTF-8/UTF-16 BOM is present. This applies to `fromFile()` and `fromURL()` too, where response `Content-Type` headers take priority.

Passing bytes is often better than passing a string: `buffer.toString("utf-8")` leaves a leading BOM intact and jsdom will then interpret it verbatim, while jsdom's own decoding strips it.

## Shutting down

Timers set by `window.setTimeout`/`setInterval` execute in the future in the window's context, so outstanding timers keep the Node process alive and prevent the window from being garbage collected. `window.close()` terminates all running timers and removes window and document event listeners.

Observed: a script that creates a jsdom window with a live interval and finishes never exits — it hangs until killed. Calling `window.close()` makes it exit cleanly. Long-lived servers keep one window for the process lifetime and do not close it.

## Known limits

- **Navigation** is out of scope. Setting `window.location.href` emits a `"jsdomError"` and changes nothing. Work around it by creating a new `JSDOM` per page.
- **Layout** is out of scope — no `getBoundingClientRect()` geometry; many layout properties return zero. `Object.defineProperty` can stub them.
- CSS selector support comes from `nwsapi`; its wiki lists supported selectors.
- Async script loading is fundamentally unpredictable: there is no way to know when a page has finished loading scripts. Use loader-provided callbacks if you control the page, or poll for a specific element.
- Keep jsdom current and pinned when it hosts a sanitizer. Older versions have known XSS vectors that DOMPurify cannot compensate for; `happy-dom` is not considered safe for this use.
