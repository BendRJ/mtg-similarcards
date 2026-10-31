"""
SQL tests for the card queries, against a real Postgres (skipped without one).
"""

import unittest

from app.backend import queries
from tests.db_fixtures import DBTestCase, insert_card, insert_image, vec


class TestCardQueries(DBTestCase):
    def test_get_card_returns_detail_without_embedding(self):
        insert_card(self.cur, "a1", "Bolt", oracle_id="o1", embedding=vec(1))
        card = queries.get_card(self.cur, "a1")
        self.assertEqual(card["name"], "Bolt")
        self.assertNotIn("embedding", card)
        self.assertIsNone(card["image_url"])

    def test_get_card_unknown_returns_none(self):
        self.assertIsNone(queries.get_card(self.cur, "nope"))

    def test_image_url_set_when_image_stored(self):
        insert_card(self.cur, "a1", "Bolt")
        insert_image(self.cur, "a1")
        self.assertEqual(queries.get_card(self.cur, "a1")["image_url"], "/cards/a1/image")

    def test_printings_newest_first_including_self(self):
        insert_card(self.cur, "old", "Bolt", oracle_id="o1", released_at="1993-08-05")
        insert_card(self.cur, "new", "Bolt", oracle_id="o1", released_at="2025-06-01")
        insert_card(self.cur, "other", "Shock", oracle_id="o2")
        ids = [p["id"] for p in queries.get_printings(self.cur, "old")]
        self.assertEqual(ids, ["new", "old"])

    def test_printings_null_oracle_id_is_own_card(self):
        insert_card(self.cur, "x", "Reversible", oracle_id=None)
        insert_card(self.cur, "y", "Other", oracle_id=None)
        self.assertEqual([p["id"] for p in queries.get_printings(self.cur, "x")], ["x"])


if __name__ == "__main__":
    unittest.main()
