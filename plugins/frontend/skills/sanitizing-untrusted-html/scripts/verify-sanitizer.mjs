#!/usr/bin/env node
/**
 * verify-sanitizer.mjs — run a regression corpus against a DOMPurify config.
 *
 * Assertions run against the PARSED TREE, not the output string, because an
 * encoded payload in a string ("&lt;script&gt;") looks like a hit to a substring
 * check and produces false failures, while a payload that only becomes live on
 * re-parse produces false passes.
 *
 * Usage:
 *   node verify-sanitizer.mjs
 *   node verify-sanitizer.mjs --config '{"ALLOWED_TAGS":["b","a"],"ALLOWED_ATTR":["href"]}'
 *   node verify-sanitizer.mjs --config-file ./sanitize-config.json
 *   node verify-sanitizer.mjs --json
 *
 * Exit codes: 0 all vectors inert · 1 a vector stayed live · 2 could not run.
 * Requires `dompurify` and `jsdom` resolvable from the working directory.
 */

import { readFileSync } from 'node:fs';

const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const val = (f) => { const i = argv.indexOf(f); return i === -1 ? null : argv[i + 1]; };

if (has('--help') || has('-h')) {
  console.log(`verify-sanitizer.mjs — check a DOMPurify config against known attack classes.

  --config <json>       Config object passed to sanitize(). Default: {} (secure defaults).
  --config-file <path>  Read the config object from a JSON file instead.
  --json                Emit machine-readable JSON instead of a table.
  --help                This message.

Exit 0 = every vector inert. Exit 1 = at least one vector stayed live. Exit 2 = setup error.`);
  process.exit(0);
}

let JSDOM, createDOMPurify;
try {
  ({ JSDOM } = await import('jsdom'));
  createDOMPurify = (await import('dompurify')).default;
} catch (err) {
  console.error(`Could not load dompurify and/or jsdom from ${process.cwd()}.`);
  console.error(`Expected: both installed as dependencies. Try: npm install dompurify jsdom`);
  console.error(`Underlying error: ${err.message}`);
  process.exit(2);
}

let config = {};
try {
  const raw = val('--config-file') ? readFileSync(val('--config-file'), 'utf8') : val('--config');
  if (raw) config = JSON.parse(raw);
} catch (err) {
  console.error(`Could not parse the config. Expected a JSON object literal.`);
  console.error(`Underlying error: ${err.message}`);
  process.exit(2);
}

// Vectors are public, fixed regression cases from DOMPurify's own suite and wiki.
// Each is a class of attack, not an exhaustive list: passing here is a smoke test,
// not a proof of safety.
const VECTORS = [
  ['inline handler', '<img src=x onerror=alert(1)//>'],
  ['svg handler', '<svg><g/onload=alert(2)//<p>'],
  ['obfuscated protocol', '<p>abc<iframe//src=jAva&Tab;script:alert(3)>def</p>'],
  ['xlink data URI', '<math><mi//xlink:href="data:x,<script>alert(4)</script>">'],
  ['mXSS: svg + style breakout', '<svg></p><style><a id="</style><img src=1 onerror=alert(1)>"></svg>'],
  ['mXSS: math integration point', '<math><annotation-xml encoding="text/html"><xmp><img src=x onerror=alert(1)></xmp></annotation-xml></math>'],
  ['mXSS: svg foreignObject', '<svg><foreignobject><xmp><img src=x onerror=alert(1)></xmp></foreignobject></svg>'],
  ['rawtext: noscript breakout', '<noscript><p title="</noscript><img src=x onerror=alert(1)>">'],
  ['rawtext: noembed', '<noembed><img src=x onerror=alert(1)></noembed>'],
  ['rawtext: style attr breakout', '<style>a[href="</style><img src=x onerror=alert(1)>"]{}</style>'],
  ['foster-parented script', '<table><script>alert(1)</script></table>'],
  ['DOM clobbering: nodeName', '<form><input name="nodeName"></form>'],
  ['DOM clobbering: attributes', '<form><input name="attributes"></form>'],
  ['iframe srcdoc nested doc', '<iframe srcdoc="<img src=x onerror=alert(1)>"></iframe>'],
  ['javascript: href', '<a href="javascript:alert(1)">click</a>'],
  ['formaction sink', '<form><button formaction="javascript:alert(1)">go</button></form>'],
  ['base href rewrite', '<base href="https://evil.test/">'],
  ['meta refresh', '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">'],
  ['autofocus amplifier', '<input autofocus onfocus=alert(1)>'],
  ['selectedcontent engine clone', '<select><button><selectedcontent></selectedcontent></button><option><img src=x onerror=alert(1)></option></select>'],
];

// Config flags that trade safety for capability. Each needs a threat-model reason.
const RISKY = {
  ADD_TAGS: 'widens the tag allow-list',
  ADD_ATTR: 'widens the attribute allow-list',
  ADD_URI_SAFE_ATTR: 'skips URI validation on those attributes',
  ADD_DATA_URI_TAGS: 'permits data: URIs on more elements',
  ALLOW_UNKNOWN_PROTOCOLS: 'admits arbitrary URI schemes',
  ALLOWED_URI_REGEXP: 'replaces the default URL check (also a ReDoS surface)',
  CUSTOM_ELEMENT_HANDLING: 'permits custom elements and their attributes',
  SAFE_FOR_XML: 'when false, removes the mXSS attribute-value guard',
  SANITIZE_DOM: 'when false, removes DOM-clobbering protection',
  SANITIZE_NAMED_PROPS: 'when false, leaves id/name un-namespaced',
  WHOLE_DOCUMENT: 'keeps head content such as <style> in the output',
  IN_PLACE: 'sanitizes live nodes; caller state is in scope',
  FORCE_BODY: 'changes where head-only elements land',
};

// jsdom's default virtual console forwards CSS parse errors and not-implemented
// warnings to the Node console; silence it so this script's output stays clean.
const { VirtualConsole } = await import('jsdom');
const quiet = () => new VirtualConsole();

const window = new JSDOM('', { virtualConsole: quiet() }).window;
const DOMPurify = createDOMPurify(window);

if (!DOMPurify.isSupported) {
  console.error('DOMPurify reports isSupported === false on this DOM. Nothing was verified.');
  process.exit(2);
}

/** Re-parse the output the way the destination will, then look for live constructs. */
function findLiveConstructs(output) {
  const doc = new JSDOM(`<body>${output}</body>`, { virtualConsole: quiet() }).window.document;
  const findings = [];
  for (const el of doc.querySelectorAll('*')) {
    const tag = el.localName;
    if (tag === 'script') findings.push('<script> element');
    if (tag === 'iframe' && el.hasAttribute('srcdoc')) findings.push('iframe srcdoc');
    if (tag === 'base') findings.push('<base> element');
    if (tag === 'meta' && el.hasAttribute('http-equiv')) findings.push('meta http-equiv');
    if (tag === 'selectedcontent') findings.push('<selectedcontent> element');
    for (const attr of Array.from(el.attributes)) {
      const name = attr.name.toLowerCase();
      const value = (attr.value || '').replace(/[\u0000-\u0020]/g, '').toLowerCase();
      if (name.startsWith('on')) findings.push(`${name}= handler`);
      if (/^(href|src|xlink:href|action|formaction|data|poster|background)$/.test(name)
          && /^(javascript|vbscript|data):/.test(value)) {
        findings.push(`${name}= script URL`);
      }
    }
  }
  return [...new Set(findings)];
}

const results = VECTORS.map(([name, payload]) => {
  let output, error = null, findings = [];
  try {
    output = String(DOMPurify.sanitize(payload, config));
    findings = findLiveConstructs(output);
  } catch (err) {
    error = err.message;
  }
  return { name, payload, output, findings, error, pass: !error && findings.length === 0 };
});

const warnings = Object.keys(RISKY)
  .filter((k) => Object.prototype.hasOwnProperty.call(config, k))
  .map((k) => ({ flag: k, why: RISKY[k] }));

const failed = results.filter((r) => !r.pass);

if (has('--json')) {
  console.log(JSON.stringify({
    dompurify: DOMPurify.version, config, warnings,
    passed: results.length - failed.length, failed: failed.length, results,
  }, null, 2));
} else {
  console.log(`DOMPurify ${DOMPurify.version} · config: ${JSON.stringify(config)}\n`);
  for (const r of results) {
    const mark = r.pass ? 'ok  ' : 'LIVE';
    console.log(`${mark} ${r.name}`);
    if (!r.pass) {
      console.log(`     found : ${r.error ? 'threw: ' + r.error : r.findings.join(', ')}`);
      console.log(`     output: ${String(r.output).slice(0, 160)}`);
    }
  }
  console.log(`\n${results.length - failed.length}/${results.length} vectors inert.`);
  if (warnings.length) {
    console.log('\nConfig flags that widen the attack surface — each needs a stated reason:');
    for (const w of warnings) console.log(`  ${w.flag} — ${w.why}`);
  }
  if (failed.length) {
    console.log('\nA LIVE result means the sanitized output still parsed into an executable');
    console.log('construct. Narrow the config until every vector is inert.');
  }
}

window.close();
process.exit(failed.length ? 1 : 0);
