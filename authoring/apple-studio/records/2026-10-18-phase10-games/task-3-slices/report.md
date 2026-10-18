# Task 3 report: sources, slices, ledger checker

The controller wrote this file from the implementer's returned report. The
harness refused the implementer's Write of report files (SDD ruling P10).

## Ledger checker

`pipeline/check_ledger.py` (tests: `pipeline/test_check_ledger.py`, 10/10).
Against an empty ledger on the real data it exits 1 with 1,222 `missing:`
lines: 1,176 manifest rows plus 46 source rows. A synthetic complete ledger
(not committed) exits 0. Every page reads `yes`, and the four 404 rows read
`no-unfetchable:404:deferred-<n>`.

What the checker enforces, beyond the brief:

- Paths compare case-insensitively.
- `--only` reads only the named slices' ledger files. An unknown id exits 2.
- `unsliced:` reports a manifest or source path that no slice lists. This
  check runs on whole-corpus runs only.
- `malformed:` reports any of these:
  - a `yes` row on a non-200 page;
  - an unfetchable code that differs from the manifest's;
  - a slice path unknown to the manifest and sources;
  - a path listed in two slices;
  - an empty `fed` field;
  - non-numeric `words`.
- `fed` must be non-empty. Its `file#section` shape is not checked.

## Sources

`sources.tsv` has 46 rows:

- **MSL 4.1.** The PDF's sha256 matches `survey/metal-toolchain.log`. It has
  383 pages, and printed page numbers equal PDF page indices. The rows tile
  pages 1–383 with no gap. `make_slices.py` asserts the tiling, and that each
  chapter's first page opens with its heading.

  | Row | Pages | Words |
  |---|---|---:|
  | `pdf:msl-4.1#front` (cover, contents, table lists) | 1–10 | 2,812 |
  | `#ch1` Introduction | 11–24 | 3,934 |
  | `#ch2` Data Types | 25–111 | 20,747 |
  | `#ch3` Operators | 112–117 | 2,325 |
  | `#ch4` Address Spaces | 118–123 | 1,834 |
  | `#ch5` Function and Variable Declarations | 124–199 | 20,077 |
  | `#ch6` Metal Standard Library | 200–348 | 37,675 |
  | `#ch7` Metal Performance Primitives | 349–367 | 3,795 |
  | `#ch8` Numerical Compliance | 368–381 | 3,705 |
  | `#ch9` Appendix | 382–383 | 437 |

  Total: 97,341 words. No row exceeds 60,000 words, so ruling P6 needed no
  split. No manifest page exceeds 60,000 words either; the largest has
  27,199.
- **Feature Set Tables.** One row, `pdf:fst#all`, 6,587 words, from
  `pdftotext`.
- **Book.** 35 rows: the 31 chapter files, `glossary.md`, `patterns.md`,
  `cheatsheet.md`, and `SKILL.md`, about 55,000 words in all. Paths are
  relative to the skill directory, for example
  `book:metal-by-tutorials/chapters/ch01-hello-metal.md`.

## Feature Set Tables spreadsheet

The spreadsheet export failed on its one try. The command opened the
`.numbers` file in `/Applications/Numbers Creator Studio.app` and sent
`export … as CSV`. It returned `AppleEvent timed out (-1712)` after 120 s and
wrote no file. `fst.csv` does not exist. The PDF text stands alone, and a
reader resolves garbled cells from the PDF page image.

## Slices

`slices.tsv` has 19 slices and 1,222 rows. Rows are packed in manifest order
within each dest. The sources are appended after the manifest rows for
`apple-metal`. Slices are balanced toward an even share rather than filled to
the cap. They are packed by **loaded** words (the whole cached file), because
the manifest's `words` column excludes the roughly 24-word metadata comment
that a reader also loads.

| Dest | Slices | Rows | Manifest words | Loaded words | Largest slice (loaded words) |
|---|---|---:|---:|---:|---|
| apple-metal | m01–m08 | 322 | 420,769 | 429,001 | m04, 59,558 (52 rows) |
| apple-games | g01–g09 | 832 | 467,025 | 488,986 | g09, 57,274 (66 rows) |
| apple-performance | p01 | 39 | 46,972 | 47,975 | p01 |
| app-release | r01 | 29 | 32,835 | 33,562 | r01 |

- The MSL front matter is in m05, chapters 1–5 are in m06, and chapters 6–9,
  the Feature Set Tables, and book ch01 are in m07. The rest of the book is in
  m08.
- The four 404 rows carry 0 words and sit in m05, g09 (two rows), and r01.
- g06 and g07 have the most rows (169 and 206), because Accelerate's pages are
  short.

`make_slices.py --check` re-derives both TSVs and fails if either differs
from the file on disk. It also checks that every 200 row's cached word count
equals the manifest's `words`.
