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


class TestAutocompleteQuery(DBTestCase):
    def test_autocomplete_dedupes_to_most_recent_printing(self):
        insert_card(self.cur, "old", "Lightning Bolt", oracle_id="o1", released_at="1993-08-05")
        insert_card(self.cur, "new", "Lightning Bolt", oracle_id="o1", released_at="2025-06-01")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "bolt", 10)], ["new"])

    def test_autocomplete_prefix_before_substring_case_insensitive(self):
        insert_card(self.cur, "f", "Firebolt", oracle_id="o1")
        insert_card(self.cur, "b", "Bolt of Fire", oracle_id="o2")
        self.assertEqual([c["name"] for c in queries.autocomplete_cards(self.cur, "BOL", 10)],
                         ["Bolt of Fire", "Firebolt"])

    def test_autocomplete_wildcards_are_literal(self):
        insert_card(self.cur, "a", "Abc", oracle_id="o1")
        self.assertEqual(queries.autocomplete_cards(self.cur, "%_", 10), [])
        self.assertEqual(queries.autocomplete_cards(self.cur, "a\\", 10), [])

    def test_autocomplete_matches_literal_percent_in_name(self):
        insert_card(self.cur, "p", "100% Pure", oracle_id="o1")
        insert_card(self.cur, "q", "1000 Pure", oracle_id="o2")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "0%", 10)], ["p"])

    def test_autocomplete_respects_limit(self):
        for i in range(5):
            insert_card(self.cur, f"c{i}", f"Goblin {i}", oracle_id=f"o{i}")
        self.assertEqual(len(queries.autocomplete_cards(self.cur, "gob", 3)), 3)


class TestSimilarQuery(DBTestCase):
    def test_similar_excludes_reprints_and_dedupes(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1, 0))
        insert_card(self.cur, "ref2", "Bolt", oracle_id="o1", embedding=vec(1, 0))
        insert_card(self.cur, "s_old", "Shock", oracle_id="o2", released_at="2010-01-01", embedding=vec(1, 0.1))
        insert_card(self.cur, "s_new", "Shock", oracle_id="o2", released_at="2025-01-01", embedding=vec(1, 0.1))
        insert_card(self.cur, "far", "Forest", oracle_id="o3", embedding=vec(0, 1))
        result = queries.similar_cards(self.cur, "ref", 10)
        self.assertEqual([c["id"] for c in result], ["s_new", "far"])
        self.assertLess(result[0]["distance"], result[1]["distance"])
        self.assertNotIn("embedding", result[0])

    def test_similar_uses_embedding_of_another_printing(self):
        insert_card(self.cur, "old", "Bolt", oracle_id="o1", embedding=None)
        insert_card(self.cur, "new", "Bolt", oracle_id="o1", embedding=vec(1))
        insert_card(self.cur, "s", "Shock", oracle_id="o2", embedding=vec(1))
        self.assertEqual([c["id"] for c in queries.similar_cards(self.cur, "old", 10)], ["s"])

    def test_similar_respects_limit(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1))
        for i in range(3):
            insert_card(self.cur, f"s{i}", f"Shock {i}", oracle_id=f"o{i + 2}", embedding=vec(1, i))
        self.assertEqual(len(queries.similar_cards(self.cur, "ref", 2)), 2)

    def test_similar_empty_when_no_other_cards(self):
        insert_card(self.cur, "a", "Bolt", oracle_id="o1", embedding=vec(1))
        self.assertEqual(queries.similar_cards(self.cur, "a", 10), [])

    def test_similar_none_without_any_embedding(self):
        insert_card(self.cur, "a", "Bolt", oracle_id="o1", embedding=None)
        self.assertIsNone(queries.similar_cards(self.cur, "a", 10))

    def test_similar_unknown_id_is_none_not_random_cards(self):
        insert_card(self.cur, "s", "Shock", oracle_id="o2", embedding=vec(1))
        self.assertIsNone(queries.similar_cards(self.cur, "does-not-exist", 10))


class TestCardImageQuery(DBTestCase):
    def test_get_card_image_round_trips_bytes(self):
        insert_card(self.cur, "a1", "Bolt")
        insert_image(self.cur, "a1", b"\x89PNG", "image/png")
        image = queries.get_card_image(self.cur, "a1")
        self.assertEqual(bytes(image["image"]), b"\x89PNG")
        self.assertEqual(image["content_type"], "image/png")

    def test_get_card_image_unknown_returns_none(self):
        self.assertIsNone(queries.get_card_image(self.cur, "nope"))


if __name__ == "__main__":
    unittest.main()
