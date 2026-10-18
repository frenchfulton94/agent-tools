#!/usr/bin/env python3
"""Offline tests for crawl_corpus.py. Standard library only.

Run: python3 -m unittest test_crawl_corpus -v   (from this directory)

The survey's prototype crawler truncated links at the first ")" and keyed the
seen-set on exact case, so a page was read twice or reported missing. These
tests pin both, plus the bound rules the manifest depends on.
"""
import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "crawl"

spec = importlib.util.spec_from_file_location("crawl_corpus", HERE / "crawl_corpus.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)  # must not run main() on import


class Stub:
    """Maps lowercased page paths to fixture files and records every fetch."""

    def __init__(self, mapping):
        self.mapping = {p.lower(): f for p, f in mapping.items()}
        self.fetched = []

    def __call__(self, path):
        self.fetched.append(path)
        name = self.mapping.get(path.lower())
        if name is None:
            return None
        return (FIXTURES / name).read_text()


def paths(rows):
    return sorted(r.path for r in rows)


class CrawlCorpusTests(unittest.TestCase):
    def test_paren_and_apostrophe_links(self):
        links = cc.extract_links((FIXTURES / "paren-seed.md").read_text())
        self.assertIn("/documentation/Metal/MTLDevice/makeBuffer(length:options:)", links)
        self.assertIn("/documentation/Metal/using-metal-to-draw-a-view's-contents", links)
        # The fragment is dropped, and /design/ links are scanned too.
        self.assertIn("/documentation/Metal/plain", links)
        self.assertIn("/design/human-interface-guidelines/designing-for-games", links)
        self.assertEqual(len(links), 4)

    def test_case_variants_dedupe(self):
        fetch = Stub({"/documentation/Xcode/seed": "case-seed.md",
                      "/documentation/Xcode/A": "case-a.md"})
        seeds = [cc.Seed("/documentation/Xcode/seed", "depth1", "apple-metal")]
        rows = cc.crawl(seeds, fetch)
        self.assertEqual(paths(rows), ["/documentation/Xcode/A", "/documentation/Xcode/seed"])
        # The first spelling seen is the canonical one, and no variant was fetched.
        self.assertEqual([p for p in fetch.fetched if p.lower().endswith("/a")],
                         ["/documentation/Xcode/A"])

    def test_recursive_stays_in_framework(self):
        fetch = Stub({"/documentation/metal": "rec-seed.md",
                      "/documentation/metal/in-framework": "rec-in-framework.md",
                      "/documentation/metal/deeper": "rec-deeper.md",
                      "/documentation/swiftui/x": "rec-swiftui-x.md"})
        seeds = [cc.Seed("/documentation/metal", "recursive", "apple-metal")]
        rows = cc.crawl(seeds, fetch)
        self.assertEqual(paths(rows), ["/documentation/Metal/deeper",
                                       "/documentation/metal",
                                       "/documentation/metal/in-framework"])
        self.assertNotIn("/documentation/swiftui/x", fetch.fetched)
        depths = {r.path.lower(): r.depth for r in rows}
        self.assertEqual(depths["/documentation/metal/deeper"], 2)

    def test_depth1_stops(self):
        fetch = Stub({"/documentation/Foo/seed": "d1-seed.md",
                      "/documentation/Foo/child": "d1-child.md",
                      "/documentation/Foo/grandchild": "d1-grandchild.md"})
        seeds = [cc.Seed("/documentation/Foo/seed", "depth1", "apple-games")]
        rows = cc.crawl(seeds, fetch)
        self.assertEqual(paths(rows), ["/documentation/Foo/child", "/documentation/Foo/seed"])
        self.assertNotIn("/documentation/Foo/grandchild", fetch.fetched)
        by_path = {r.path: r for r in rows}
        self.assertEqual(by_path["/documentation/Foo/child"].depth, 1)
        self.assertEqual(by_path["/documentation/Foo/child"].bound, "depth1")
        self.assertEqual(by_path["/documentation/Foo/child"].dest, "apple-games")
        self.assertEqual(by_path["/documentation/Foo/child"].seed, "/documentation/Foo/seed")

    def test_page_bound_does_not_expand(self):
        fetch = Stub({"/documentation/Foo/seed": "d1-seed.md",
                      "/documentation/Foo/child": "d1-child.md"})
        seeds = [cc.Seed("/documentation/Foo/seed", "page", "apple-games")]
        self.assertEqual(paths(cc.crawl(seeds, fetch)), ["/documentation/Foo/seed"])
        self.assertEqual(fetch.fetched, ["/documentation/Foo/seed"])

    def test_symbols_excluded(self):
        fetch = Stub({"/documentation/Foo/seed": "sym-seed.md",
                      "/documentation/Foo/SomeClass": "sym-class.md",
                      "/documentation/Foo/Group": "sym-group.md",
                      "/documentation/Foo/member-article": "sym-member.md",
                      "/documentation/Foo/hidden-from-class": "sym-hidden.md"})
        seeds = [cc.Seed("/documentation/Foo/seed", "recursive", "apple-metal")]
        rows = cc.crawl(seeds, fetch)
        got = paths(rows)
        self.assertNotIn("/documentation/Foo/SomeClass", got)
        self.assertNotIn("/documentation/Foo/hidden-from-class", got)
        self.assertIn("/documentation/Foo/Group", got)
        self.assertIn("/documentation/Foo/member-article", got)
        group = next(r for r in rows if r.path.endswith("/Group"))
        self.assertEqual((group.documentType, group.role), ("symbol", "collectionGroup"))

    def test_metadata_words(self):
        text = (FIXTURES / "words.md").read_text()
        self.assertEqual(cc.page_words(text), 5)
        self.assertEqual(cc.page_meta(text)["documentType"], "article")
        fetch = Stub({"/documentation/Foo/w": "words.md"})
        rows = cc.crawl([cc.Seed("/documentation/Foo/w", "page", "app-release")], fetch)
        self.assertEqual(rows[0].words, 5)
        self.assertEqual(rows[0].http, 200)

    def test_seed_that_is_also_a_child_keeps_its_own_row(self):
        fetch = Stub({"/documentation/Foo/seed": "d1-seed.md",
                      "/documentation/Foo/child": "d1-child.md",
                      "/documentation/Foo/grandchild": "d1-grandchild.md"})
        seeds = [cc.Seed("/documentation/Foo/seed", "depth1", "apple-metal"),
                 cc.Seed("/documentation/foo/CHILD", "depth1", "apple-games")]
        rows = {r.path.lower(): r for r in cc.crawl(seeds, fetch)}
        child = rows["/documentation/foo/child"]
        self.assertEqual((child.depth, child.dest, child.bound), (0, "apple-games", "depth1"))
        self.assertIn("/documentation/foo/grandchild", rows)

    def test_non_200_seed_is_a_row(self):
        fetch = Stub({})
        rows = cc.crawl([cc.Seed("/documentation/Foo/gone", "depth1", "apple-metal")], fetch,
                        status=lambda p: 404)
        self.assertEqual([(r.path, r.http, r.documentType) for r in rows],
                         [("/documentation/Foo/gone", 404, "")])

    def test_cache_key(self):
        self.assertEqual(cc.key("/documentation/Metal/using-metal-to-draw-a-view's-contents"),
                         "documentation__metal__using-metal-to-draw-a-view's-contents")
        self.assertEqual(cc.key("/documentation/Metal/MTLDevice/makeBuffer(length:options:)"),
                         "documentation__metal__mtldevice__makebuffer(length_options_)")

    def test_parse_map(self):
        text = ("# Map\n\nprose with - recursive apple-metal https://x not a seed\n\n## Seeds\n\n"
                "- recursive apple-metal https://developer.apple.com/documentation/metal.md\n"
                "- depth1 app-release https://developer.apple.com/design/human-interface-guidelines/designing-for-games.md\n"
                "- MISSING: documentation/foo -> 404\n")
        seeds = cc.parse_map(text)
        self.assertEqual([(s.path, s.bound, s.dest) for s in seeds],
                         [("/documentation/metal", "recursive", "apple-metal"),
                          ("/design/human-interface-guidelines/designing-for-games",
                           "depth1", "app-release")])


if __name__ == "__main__":
    unittest.main()
