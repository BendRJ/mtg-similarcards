"""
Unit tests for the text that gets embedded for card similarity.
"""

import unittest

from utils.vector_helper import build_card_text


class TestBuildCardText(unittest.TestCase):
    def test_uses_rules_text_only(self):
        card = {"type_line": "Creature — Elf Druid", "oracle_text": "{T}: Add {G}.",
                "keywords": [], "colors": ["G"]}
        self.assertEqual(build_card_text(card), "{T}: Add {G}.")

    def test_falls_back_to_keywords_without_rules_text(self):
        card = {"oracle_text": None, "keywords": ["Flying", "Transform"], "colors": ["U"]}
        self.assertEqual(build_card_text(card), "Flying, Transform")

    def test_empty_without_rules_text_or_keywords(self):
        self.assertEqual(build_card_text({"oracle_text": None, "keywords": []}), "")
        self.assertEqual(build_card_text({"oracle_text": None, "keywords": None}), "")


if __name__ == "__main__":
    unittest.main()
