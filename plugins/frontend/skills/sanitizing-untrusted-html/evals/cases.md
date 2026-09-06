# A/B Cases

For maintainers. Run each task twice in clean context — once without the skill, once with — and grade the output against the assertions with quoted evidence. No benefit of the doubt: an assertion passes only if the output actually contains the behavior.

Each case is anchored to a failure observed in a real baseline run against `dompurify@3.4.13` and `jsdom@30.0.1`, recorded in the "Baseline" line.

---

### Case 1 — Node wiring

**Task:** "Add HTML sanitization to this Express handler that renders user-submitted bios."

**Baseline:** `require('dompurify')` used directly; `DOMPurify.sanitize` is `undefined` and the call throws `TypeError: DOMPurify.sanitize is not a function`.

Assertions:

- [ ] Passes a jsdom window into the DOMPurify factory
- [ ] Creates the window once at module scope, not per request
- [ ] Sanitizes with defaults or a narrowing config, not `ADD_*`
- [ ] Does not enable `runScripts` or `resources` on the window

---

### Case 2 — the after-hook trap

**Task:** "Users can attach a link to their post in a `data-url` attribute. Write a DOMPurify hook that promotes it to a real `href`."

**Baseline:** an `afterSanitizeAttributes` hook that emits `<a data-url="javascript:alert(1)" href="javascript:alert(1)">` — a live payload in sanitized output.

Assertions:

- [ ] Uses `uponSanitizeAttribute` (or validates the URL explicitly), not a bare `afterSanitizeAttributes` write
- [ ] States that `afterSanitize*` output is not re-validated
- [ ] Registers the hook once at module scope rather than inside the handler

---

### Case 3 — config review

**Task:** "Review this config: `{ ADD_TAGS: ['iframe','style'], ADD_ATTR: ['srcdoc','target'], ALLOW_UNKNOWN_PROTOCOLS: true, SAFE_FOR_XML: false }`"

**Baseline:** generic "looks reasonable, be careful with iframes" commentary with no specific vector named.

Assertions:

- [ ] Identifies `iframe` + `srcdoc` as live XSS, and says DOMPurify does not recurse into `srcdoc`
- [ ] Flags `SAFE_FOR_XML: false` as removing mXSS protection
- [ ] Flags `ALLOW_UNKNOWN_PROTOCOLS` as re-admitting dangerous schemes
- [ ] Notes `target` enables reverse tabnabbing
- [ ] Proposes a narrowing alternative rather than only listing risks

---

### Case 4 — the persistent-config surprise

**Task:** "We call `setConfig` at startup, but the `FORBID_ATTR` we pass on this one route is being ignored. Why?"

**Baseline:** speculation about ordering or merge semantics; suggests merging the objects manually.

Assertions:

- [ ] States that per-call config is ignored entirely while a persistent config is set
- [ ] Recommends per-call config or `clearConfig()`, not manual merging

---

### Case 5 — post-processing

**Task:** "After sanitizing, we do `clean.replace('<a ', '<a target=\"_blank\" ')`. Any problem?"

**Baseline:** answers only the tabnabbing question and approves the string edit.

Assertions:

- [ ] Says editing the string after `sanitize()` voids sanitization
- [ ] Offers a hook or DOM-level alternative
- [ ] Mentions `rel="noopener"` for `target="_blank"`

---

### Case 6 — content loss, not a security question

**Task:** "With `{ ALLOWED_TAGS: ['p'], KEEP_CONTENT: false }` my paragraphs come back empty."

**Baseline:** blames `KEEP_CONTENT` alone and suggests setting it back to `true`, losing the caller's intent.

Assertions:

- [ ] Identifies the missing `'#text'` entry in `ALLOWED_TAGS`
- [ ] Preserves the caller's intent of dropping content from non-allowed elements

---

## Grading notes

Variance across repetitions matters as much as the average. If the same case produces three different shapes of answer across three runs, the corresponding SKILL.md wording is not binding — add one concrete example or a scope clause rather than another rule.
