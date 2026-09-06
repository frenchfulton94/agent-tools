# Trigger Battery

For maintainers of this skill. Run each query in a clean-context session where only the skill's `name` and `description` are visible, and record whether the skill loads. The valuable signal is in the near-misses.

## Should trigger

1. We let users leave comments with a bit of formatting — how do I render that without opening an XSS hole?
2. Add DOMPurify to the Express route that renders user bios.
3. Review this config for me: `{ ADD_TAGS: ['iframe'], ADD_ATTR: ['srcdoc', 'target'] }`.
4. Our Markdown pipeline produces HTML that we drop into `innerHTML`. Is that safe?
5. I'm getting `DOMPurify.sanitize is not a function` and I definitely installed it.
6. My test suite hangs forever after the HTML-cleaning tests run.
7. Write me a hook that forces every link in sanitized output to open in a new tab.
8. Is it fine to add `target="_blank"` to the output after sanitizing it?
9. Sanitize this email body before we show a preview of it.
10. Why is DOMPurify eating my `<style>` block?
11. We need to clean HTML server-side in Node before storing it.

## Should not trigger

1. Set up jsdom as the test environment for my React component tests. _(jsdom, but no untrusted markup — this is test tooling)_
2. Write a Content-Security-Policy header for my site. _(XSS-adjacent, different mitigation layer)_
3. Escape this string before interpolating it into a SQL query. _(injection, wrong domain)_
4. Parse this HTML file and extract all the links into a CSV. _(scraping; nothing is rendered)_
5. How does React escape interpolated values in JSX? _(framework behavior, no sanitizer involved)_
6. Minify this HTML file for production.
7. Convert this HTML document to Markdown.
8. `npm install jsdom` fails on my Node version. _(dependency troubleshooting)_
9. Validate that this string is a well-formed email address.
10. Explain how the HTML parser's foster-parenting algorithm works. _(parser theory, no sanitization task)_
11. Write a fuzzer for our REST API. _(security, but unrelated)_

## Borderline — judgment, not failure

- _"Write a regex that strips HTML tags from a string."_ Loading is fine if the intent is sanitizing for display, since the correct answer is that regex-stripping is the wrong tool. Not loading is fine if the intent is extracting plain text, where `textContent` is the answer and no sanitizer is needed. Either outcome is acceptable; both answers should reach the same conclusion.
- _"Is `dangerouslySetInnerHTML` safe here?"_ Should usually trigger — the answer depends entirely on whether the value was sanitized.

## Reading the results

A miss in "should trigger" means the description lacks that intent phrasing; add the trigger, do not rewrite the body. A hit in "should not trigger" means a term in the description is too broad — the likely culprits are the bare mentions of jsdom and XSS, which are deliberately qualified ("host a sanitizer in Node", "from rendered markup") to keep test-tooling and CSP questions out.
