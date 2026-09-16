import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_index as pi

SAMPLE = """# PARA index

Root: /Users/me/Documents
Updated: 2026-09-15

## Projects
- client-redesign — ship the new marketing site — due 2026-10-15
- taxes-2025

## Areas
- finances — accounts reconciled monthly

## Resources
- photography

## Never read
- ~/.ssh
- **/*.kdbx

## Never move
- **/*.app
"""


class Parse(unittest.TestCase):
    def setUp(self):
        self.index = pi.parse_index(SAMPLE)

    def test_reads_each_section(self):
        self.assertEqual(self.index.projects, ["client-redesign", "taxes-2025"])
        self.assertEqual(self.index.areas, ["finances"])
        self.assertEqual(self.index.resources, ["photography"])

    def test_strips_description_after_em_dash(self):
        self.assertIn("client-redesign", self.index.projects)
        self.assertNotIn("ship the new marketing site", " ".join(self.index.projects))

    def test_reads_policy_sections(self):
        self.assertEqual(self.index.never_read, ["~/.ssh", "**/*.kdbx"])
        self.assertEqual(self.index.never_move, ["**/*.app"])

    def test_classify_maps_to_destinations(self):
        self.assertEqual(self.index.classify("client-redesign"), "1-Projects")
        self.assertEqual(self.index.classify("finances"), "2-Areas")
        self.assertEqual(self.index.classify("photography"), "3-Resources")
        self.assertIsNone(self.index.classify("nothing-here"))

    def test_classify_is_case_insensitive(self):
        self.assertEqual(self.index.classify("Client-Redesign"), "1-Projects")

    def test_empty_text_yields_empty_index(self):
        empty = pi.parse_index("")
        self.assertEqual(empty.projects, [])
        self.assertIsNone(empty.classify("anything"))


class Render(unittest.TestCase):
    def test_round_trips(self):
        text = pi.render_index(pi.parse_index(SAMPLE), "/Users/me/Documents", "2026-09-15")
        self.assertEqual(pi.parse_index(text).projects, ["client-redesign", "taxes-2025"])


if __name__ == "__main__":
    unittest.main()
