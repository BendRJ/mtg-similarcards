"""
SQL tests for the set queries, against a real Postgres (skipped without one).
"""

import unittest

from psycopg.types.json import Jsonb

from app.backend import queries
from tests.db_fixtures import DBTestCase, insert_card, insert_set


class TestSetQueries(DBTestCase):
    def test_list_sets_only_with_cards_newest_first(self):
        insert_set(self.cur, "old", "Old", released_at="2001-01-01")
        insert_set(self.cur, "new", "New", released_at="2025-01-01")
        insert_set(self.cur, "empty", "Empty", released_at="2026-01-01")
        insert_card(self.cur, "a", "A", set_code="old")
        insert_card(self.cur, "b", "B", set_code="new")
        self.assertEqual([s["code"] for s in queries.list_sets(self.cur)], ["new", "old"])

    def test_set_exists_case_insensitive(self):
        insert_set(self.cur, "mh3", "Modern Horizons 3")
        self.assertTrue(queries.set_exists(self.cur, "MH3"))
        self.assertFalse(queries.set_exists(self.cur, "nope"))


class TestSetCardsQuery(DBTestCase):
    def ids(self, set_code, colors=None):
        return [c["id"] for c in queries.get_set_cards(self.cur, set_code, colors)]

    def test_set_cards_collector_order(self):
        for cid, num in [("a", "10"), ("b", "2"), ("c", "10a"), ("d", "★5"), ("e", None)]:
            insert_card(self.cur, cid, cid, oracle_id=cid, set_code="mh3", collector_number=num)
        self.assertEqual(self.ids("mh3"), ["b", "d", "a", "c", "e"])

    def test_set_cards_dedupe_keeps_lowest_collector_number(self):
        insert_card(self.cur, "show", "Bolt", oracle_id="o1", set_code="mh3", collector_number="300")
        insert_card(self.cur, "reg", "Bolt", oracle_id="o1", set_code="mh3", collector_number="12")
        self.assertEqual(self.ids("mh3"), ["reg"])

    def test_set_cards_use_scryfall_fallback(self):
        insert_card(self.cur, "a", "A", set_code="mh3", image_uris=Jsonb({"normal": "https://x/a.jpg"}))
        self.assertEqual(queries.get_set_cards(self.cur, "mh3", None)[0]["image_url"], "https://x/a.jpg")

    def test_set_cards_case_insensitive(self):
        insert_card(self.cur, "a", "A", set_code="mh3")
        self.assertEqual(self.ids("MH3"), ["a"])

    def test_set_cards_only_from_that_set(self):
        insert_card(self.cur, "a", "A", set_code="mh3")
        insert_card(self.cur, "b", "B", set_code="dmu")
        self.assertEqual(self.ids("mh3"), ["a"])

    def test_color_filter_any_of_and_colorless_and_null(self):
        rows = [("r", ["R"]), ("g", ["G"]), ("rg", ["R", "G"]), ("u", ["U"]), ("c", []), ("dfc", None)]
        for i, (cid, colors) in enumerate(rows):
            insert_card(self.cur, cid, cid, oracle_id=cid, set_code="s",
                        collector_number=str(i), colors=colors)
        self.assertEqual(set(self.ids("s", ["R", "G"])), {"r", "g", "rg"})
        self.assertEqual(set(self.ids("s", ["C"])), {"c"})
        self.assertEqual(set(self.ids("s", ["U", "C"])), {"u", "c"})
        self.assertEqual(set(self.ids("s")), {"r", "g", "rg", "u", "c", "dfc"})


if __name__ == "__main__":
    unittest.main()
