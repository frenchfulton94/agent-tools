#!/usr/bin/env python3
"""Offline tests for crawl_corpus.py. Standard library only.

Run: python3 -m unittest test_crawl_corpus -v   (from this directory)

The survey's prototype crawler truncated links at the first ")" and keyed the
seen-set on exact case, so a page was read twice or reported missing. These
tests pin both, plus the bound rules the manifest depends on.
"""
import contextlib
import importlib.util
import io
import pathlib
import tempfile
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


    def test_doc_scheme_links(self):
        links = cc.extract_links((FIXTURES / "doc-forms.md").read_text())
        self.assertEqual(links, [
            "/documentation/Metal/MTLDevice/makeBuffer(length:options:)",
            "/documentation/Metal/using-metal-to-draw-a-view's-contents",
            "/documentation/GameController",
            "/design/human-interface-guidelines/offering-help",
            "/design/human-interface-guidelines/designing-for-games",
            "/design/human-interface-guidelines/apple-pay",
            "/documentation/Metal/shared",
        ])

    def test_doc_scheme_links_are_followed(self):
        fetch = Stub({"/documentation/Foo/seed": "doc-forms.md"})
        seeds = [cc.Seed("/documentation/Foo/seed", "depth1", "apple-games")]
        cc.crawl(seeds, fetch)
        self.assertIn("/documentation/GameController", fetch.fetched)
        self.assertIn("/design/human-interface-guidelines/apple-pay", fetch.fetched)
        self.assertNotIn("/videos/play/wwdc2023/10073", fetch.fetched)


    def test_signature_links_are_not_fetched(self):
        fetch = Stub({"/documentation/Metal/paren-seed": "paren-seed.md",
                      "/documentation/Metal/plain": "case-a.md"})
        seeds = [cc.Seed("/documentation/Metal/paren-seed", "depth1", "apple-metal")]
        rows = cc.crawl(seeds, fetch)
        self.assertIn("/documentation/Metal/plain", paths(rows))
        self.assertFalse([p for p in fetch.fetched if "(" in p])
        self.assertFalse([r.path for r in rows if "(" in r.path])
        # A seed is never skipped, even with a signature-shaped path.
        seeds = [cc.Seed("/documentation/Metal/x(y)", "page", "apple-metal")]
        self.assertEqual(len(cc.crawl(seeds, Stub({}))), 1)


class StubFetcher(cc.Fetcher):
    """A real Fetcher whose network is a dict: path -> (code, body)."""

    def __init__(self, cache_dir, offline=False, served=None):
        super().__init__(cache_dir, offline)
        self.served = served or {}
        self.downloads = []

    def _download(self, path):
        self.downloads.append(path)
        code, name = self.served.get(path.lower(), (0, None))
        body = (FIXTURES / name).read_bytes() if name else None
        return code, body


class MainExitCodeTests(unittest.TestCase):
    SEED = "/documentation/Foo/seed"
    MAP = ("## Seeds\n\n- depth1 apple-games https://developer.apple.com"
           + SEED + ".md\n")

    def run_main(self, served, offline=False, map_text=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        (root / "m.md").write_text(map_text or self.MAP)
        out = root / "manifest.tsv"
        made = []

        def factory(cache, off):
            f = StubFetcher(cache, off, served)
            made.append(f)
            return f

        argv = [str(root / "m.md"), "--out", str(out),
                "--cache", str(root / "cache")]
        if offline:
            argv.append("--offline")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = cc.main(argv, fetcher_factory=factory)
        return code, out, err.getvalue(), made[0]

    def test_non_200_seed_exits_1(self):
        code, out, err, _ = self.run_main({self.SEED.lower(): (404, None)})
        self.assertEqual(code, 1)
        self.assertIn("seed not 200", err)
        rows = out.read_text().splitlines()
        self.assertEqual(rows[1].split("\t")[7], "404")

    def test_transport_failure_of_child_fails_the_run(self):
        served = {self.SEED.lower(): (200, "d1-seed.md"),
                  "/documentation/foo/child": (0, None)}
        code, out, err, _ = self.run_main(served)
        self.assertEqual(code, 2)
        self.assertIn("/documentation/Foo/child", err)
        self.assertFalse(out.exists())

    def test_server_error_of_child_fails_the_run(self):
        served = {self.SEED.lower(): (200, "d1-seed.md"),
                  "/documentation/foo/child": (503, None)}
        code, out, _, _ = self.run_main(served)
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_offline_cache_miss_fails_the_run(self):
        code, out, err, fetcher = self.run_main({}, offline=True)
        self.assertNotEqual(code, 0)
        self.assertIn("fetch failed", err)
        self.assertEqual(fetcher.downloads, [])
        self.assertFalse(out.exists())

    def test_real_404_child_stays_a_row(self):
        served = {self.SEED.lower(): (200, "d1-seed.md"),
                  "/documentation/foo/child": (404, None)}
        code, out, _, _ = self.run_main(served)
        self.assertEqual(code, 0)
        rows = [l.split("\t") for l in out.read_text().splitlines()[1:]]
        self.assertEqual([(r[0], r[7]) for r in rows],
                         [("/documentation/Foo/child", "404"), (self.SEED, "200")])

    def test_real_404_is_remembered_for_offline_reruns(self):
        served = {self.SEED.lower(): (200, "d1-seed.md"),
                  "/documentation/foo/child": (404, None)}
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        (root / "m.md").write_text(self.MAP)
        args = [str(root / "m.md"), "--cache", str(root / "cache")]
        outs = []
        for offline in (False, True):
            out = root / ("offline.tsv" if offline else "online.tsv")
            argv = args + ["--out", str(out)] + (["--offline"] if offline else [])
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = cc.main(argv, fetcher_factory=lambda c, o: StubFetcher(c, o, served))
            self.assertEqual(code, 0)
            outs.append(out.read_bytes())
        self.assertEqual(outs[0], outs[1])

    def test_crawl_keeps_code_zero(self):
        rows = cc.crawl([cc.Seed("/documentation/Foo/x", "page", "apple-games")], Stub({}),
                        status=lambda p: 0)
        self.assertEqual(rows[0].http, 0)


if __name__ == "__main__":
    unittest.main()
