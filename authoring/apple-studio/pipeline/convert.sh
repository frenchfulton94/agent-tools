#!/usr/bin/env bash
# Convert EPUB/PDF books to plain text/markdown in corpus/ for distillation.
#
# Usage: pipeline/convert.sh <book-file>...
#
# EPUB -> corpus/<slug>.md   (pandoc, GitHub-flavored markdown) + corpus/<slug>.toc.md
# PDF  -> corpus/<slug>.txt  (pdftotext -layout)
#
# corpus/ is gitignored: converted text is copyrighted and never committed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS="$REPO_ROOT/corpus"
mkdir -p "$CORPUS"

slugify() {
  basename "$1" | sed -E 's/\.(epub|pdf)$//I' \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'
}

for src in "$@"; do
  if [[ ! -f "$src" ]]; then
    echo "SKIP (not found): $src" >&2
    continue
  fi
  slug="$(slugify "$src")"
  case "$src" in
    *.epub|*.EPUB)
      out="$CORPUS/$slug.md"
      echo "EPUB -> $out"
      pandoc "$src" --to=gfm-raw_html --wrap=none --markdown-headings=atx -o "$out"
      # TOC: headings with line numbers, for chapter mapping without reading the file
      grep -n '^#\{1,3\} ' "$out" > "$CORPUS/$slug.toc.md" || true
      ;;
    *.pdf|*.PDF)
      out="$CORPUS/$slug.txt"
      echo "PDF  -> $out"
      pdftotext -layout "$src" "$out"
      ;;
    *)
      echo "SKIP (unknown type): $src" >&2
      ;;
  esac
done

echo "Done. Corpus contents:"
ls -lh "$CORPUS"
