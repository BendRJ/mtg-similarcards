"""
SQL tests for the card queries, against a real Postgres (skipped without one).
"""

import unittest

from psycopg.types.json import Jsonb

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

    def test_image_url_falls_back_to_scryfall_normal(self):
        insert_card(self.cur, "a1", "Bolt", image_uris=Jsonb({"normal": "https://cards.scryfall.io/n/a1.jpg"}))
        self.assertEqual(queries.get_card(self.cur, "a1")["image_url"], "https://cards.scryfall.io/n/a1.jpg")

    def test_stored_image_wins_over_scryfall(self):
        insert_card(self.cur, "a1", "Bolt", image_uris=Jsonb({"normal": "https://x/a1.jpg"}))
        insert_image(self.cur, "a1")
        self.assertEqual(queries.get_card(self.cur, "a1")["image_url"], "/cards/a1/image")

    def test_get_card_returns_large_image_url(self):
        insert_card(self.cur, "a1", "Bolt", image_uris=Jsonb({"normal": "https://x/n.jpg", "large": "https://x/l.jpg"}))
        self.assertEqual(queries.get_card(self.cur, "a1")["image_url_large"], "https://x/l.jpg")

    def test_large_image_url_none_without_image_uris(self):
        insert_card(self.cur, "a1", "Bolt")
        self.assertIsNone(queries.get_card(self.cur, "a1")["image_url_large"])

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
    def test_autocomplete_prefers_physical_over_newer_digital(self):
        insert_card(self.cur, "paper", "Bolt", oracle_id="o1", released_at="2020-01-01", digital=False)
        insert_card(self.cur, "arena", "Bolt", oracle_id="o1", released_at="2025-01-01", digital=True)
        insert_card(self.cur, "alch", "Bolt Arena", oracle_id="o2", digital=True)
        self.assertEqual({c["id"] for c in queries.autocomplete_cards(self.cur, "bolt", 10)}, {"paper", "alch"})

    def test_autocomplete_returns_scryfall_small_image(self):
        insert_card(self.cur, "a", "Bolt", oracle_id="o1",
                    image_uris=Jsonb({"small": "https://x/s.jpg", "normal": "https://x/n.jpg"}))
        insert_card(self.cur, "b", "Boltwing", oracle_id="o2")
        rows = {c["id"]: c for c in queries.autocomplete_cards(self.cur, "bolt", 10)}
        self.assertEqual(rows["a"]["image_url_small"], "https://x/s.jpg")
        self.assertIsNone(rows["b"]["image_url_small"])

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

    def test_autocomplete_matches_literal_underscore_in_name(self):
        insert_card(self.cur, "u", "A_c", oracle_id="o1")
        insert_card(self.cur, "b", "Abc", oracle_id="o2")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "a_", 10)], ["u"])

    def test_autocomplete_matches_literal_backslash_in_name(self):
        insert_card(self.cur, "s", "A\\c", oracle_id="o1")
        insert_card(self.cur, "b", "Abc", oracle_id="o2")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "a\\", 10)], ["s"])

    def test_autocomplete_matches_literal_percent_in_name(self):
        insert_card(self.cur, "p", "100% Pure", oracle_id="o1")
        insert_card(self.cur, "q", "1000 Pure", oracle_id="o2")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "0%", 10)], ["p"])

    def test_autocomplete_excludes_tokens_emblems_and_art_cards(self):
        insert_card(self.cur, "t1", "Elemental", oracle_id="o1", layout="token")
        insert_card(self.cur, "t2", "Elemental", oracle_id="o2", layout="double_faced_token")
        insert_card(self.cur, "e", "Elemental Emblem", oracle_id="o3", layout="emblem")
        insert_card(self.cur, "art", "Elemental Bond // Elemental Bond", oracle_id="o4", layout="art_series")
        insert_card(self.cur, "real", "Elemental Bond", oracle_id="o5", layout="normal")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "elemental", 10)], ["real"])

    def test_autocomplete_excludes_token_memorabilia_and_minigame_sets(self):
        insert_card(self.cur, "front", "Counterargument", oracle_id="o1",
                    layout="front_card", set_type="memorabilia")
        insert_card(self.cur, "tok", "Counter Token", oracle_id="o2", layout="normal", set_type="token")
        insert_card(self.cur, "mini", "Counter Game", oracle_id="o3", layout="normal", set_type="minigame")
        insert_card(self.cur, "real", "Counterspell", oracle_id="o4", layout="normal", set_type="masters")
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "counter", 10)], ["real"])

    def test_autocomplete_keeps_cards_without_set_type(self):
        insert_card(self.cur, "a", "Counterspell", oracle_id="o1", set_type=None)
        self.assertEqual([c["id"] for c in queries.autocomplete_cards(self.cur, "counter", 10)], ["a"])

    def test_autocomplete_respects_limit(self):
        for i in range(5):
            insert_card(self.cur, f"c{i}", f"Goblin {i}", oracle_id=f"o{i}")
        self.assertEqual(len(queries.autocomplete_cards(self.cur, "gob", 3)), 3)


class TestSimilarQuery(DBTestCase):
    def seed_mana_sources(self):
        insert_card(self.cur, "birds", "Birds of Paradise", oracle_id="o0", embedding=vec(1, 0))
        insert_card(self.cur, "elf", "Llanowar Elves", oracle_id="o1", type_line="Creature — Elf Druid",
                    colors=["G"], embedding=vec(1, 0.1))
        insert_card(self.cur, "rock", "Mind Stone", oracle_id="o2", type_line="Artifact",
                    colors=[], embedding=vec(1, 0.2))
        insert_card(self.cur, "hind", "Golden Hind", oracle_id="o3", type_line="Creature — Elk",
                    colors=["G"], embedding=vec(1, 0.3))
        insert_card(self.cur, "red", "Fire Dork", oracle_id="o4", type_line="Creature — Goblin",
                    colors=["R"], embedding=vec(1, 0.4))

    def test_similar_filters_keep_similarity_order(self):
        self.seed_mana_sources()
        filters = [{"field": "type", "op": "contains", "value": "Creature"},
                   {"field": "colors", "op": "any", "value": ["G"]}]
        result = queries.similar_cards(self.cur, "birds", 10, filters=filters)
        self.assertEqual([c["id"] for c in result], ["elf", "hind"])

    def test_similar_offset_pages_through_results(self):
        self.seed_mana_sources()
        first = [c["id"] for c in queries.similar_cards(self.cur, "birds", 2)]
        second = [c["id"] for c in queries.similar_cards(self.cur, "birds", 2, offset=2)]
        self.assertEqual(first, ["elf", "rock"])
        self.assertEqual(second, ["hind", "red"])

    def test_similar_equal_distance_ordered_by_id(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o0", embedding=vec(1))
        for card_id, oracle in [("z", "o1"), ("a", "o2"), ("m", "o3")]:
            insert_card(self.cur, card_id, card_id, oracle_id=oracle, embedding=vec(1))
        self.assertEqual([c["id"] for c in queries.similar_cards(self.cur, "ref", 10)], ["a", "m", "z"])

    def test_similar_uses_scryfall_fallback(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1))
        insert_card(self.cur, "s", "Shock", oracle_id="o2", embedding=vec(1),
                    image_uris=Jsonb({"normal": "https://x/s.jpg"}))
        self.assertEqual(queries.similar_cards(self.cur, "ref", 5)[0]["image_url"], "https://x/s.jpg")

    def test_similar_prefers_physical_over_newer_digital(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1))
        insert_card(self.cur, "paper", "Shock", oracle_id="o2", released_at="2020-01-01", digital=False, embedding=vec(1))
        insert_card(self.cur, "arena", "Shock", oracle_id="o2", released_at="2025-01-01", digital=True, embedding=vec(1))
        self.assertEqual([c["id"] for c in queries.similar_cards(self.cur, "ref", 10)], ["paper"])

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

    def test_similar_excludes_tokens_emblems_and_art_cards(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1))
        for i, layout in enumerate(["token", "double_faced_token", "emblem", "art_series"]):
            insert_card(self.cur, layout, layout, oracle_id=f"x{i}", layout=layout, embedding=vec(1))
        insert_card(self.cur, "real", "Shock", oracle_id="o2", layout="normal", embedding=vec(1, 0.5))
        self.assertEqual([c["id"] for c in queries.similar_cards(self.cur, "ref", 10)], ["real"])

    def test_similar_excludes_token_memorabilia_and_minigame_sets(self):
        insert_card(self.cur, "ref", "Bolt", oracle_id="o1", embedding=vec(1))
        for i, set_type in enumerate(["token", "memorabilia", "minigame"]):
            insert_card(self.cur, set_type, set_type, oracle_id=f"x{i}", set_type=set_type, embedding=vec(1))
        insert_card(self.cur, "real", "Shock", oracle_id="o2", set_type="core", embedding=vec(1, 0.5))
        self.assertEqual([c["id"] for c in queries.similar_cards(self.cur, "ref", 10)], ["real"])

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


class TestRandomQuery(DBTestCase):
    def test_random_prefers_physical_over_newer_digital(self):
        insert_card(self.cur, "paper", "Shock", oracle_id="o1", colors=["R"], released_at="2020-01-01", digital=False)
        insert_card(self.cur, "arena", "Shock", oracle_id="o1", colors=["R"], released_at="2025-01-01", digital=True)
        self.assertEqual([c["id"] for c in queries.random_cards(self.cur, ["R"], 100)], ["paper"])

    def test_random_any_of_colors_one_per_card_playable_only(self):
        insert_card(self.cur, "r_old", "Shock", oracle_id="o1", colors=["R"], released_at="2010-01-01")
        insert_card(self.cur, "r_new", "Shock", oracle_id="o1", colors=["R"], released_at="2025-01-01")
        insert_card(self.cur, "rg", "Gruul", oracle_id="o2", colors=["R", "G"])
        insert_card(self.cur, "u", "Blue", oracle_id="o3", colors=["U"])
        insert_card(self.cur, "tok", "Goblin", oracle_id="o4", colors=["R"], layout="token")
        self.assertEqual({c["id"] for c in queries.random_cards(self.cur, ["R"], 100)}, {"r_new", "rg"})

    def test_random_colorless(self):
        insert_card(self.cur, "c", "Sol Ring", oracle_id="o1", colors=[])
        insert_card(self.cur, "n", "Null", oracle_id="o2", colors=None)
        self.assertEqual([c["id"] for c in queries.random_cards(self.cur, ["C"], 100)], ["c"])

    def test_random_mixed_colored_and_colorless(self):
        insert_card(self.cur, "r", "Shock", oracle_id="o1", colors=["R"])
        insert_card(self.cur, "c", "Sol Ring", oracle_id="o2", colors=[])
        insert_card(self.cur, "u", "Blue", oracle_id="o3", colors=["U"])
        self.assertEqual({c["id"] for c in queries.random_cards(self.cur, ["R", "C"], 100)}, {"r", "c"})

    def test_random_respects_limit(self):
        for i in range(5):
            insert_card(self.cur, f"r{i}", f"R{i}", oracle_id=f"o{i}", colors=["R"])
        self.assertEqual(len(queries.random_cards(self.cur, ["R"], 3)), 3)


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
