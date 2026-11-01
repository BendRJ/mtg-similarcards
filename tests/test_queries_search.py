"""
SQL tests for the advanced search query, against a real Postgres (skipped without one).
"""

import unittest
from typing import Any

from app.backend import queries
from tests.db_fixtures import DBTestCase, insert_card


def f(field: str, op: str, value: Any) -> dict[str, Any]:
    return {"field": field, "op": op, "value": value}


class TestSearchQuery(DBTestCase):
    def search(self, *filters: dict[str, Any], sort: str = "name", limit: int = 200) -> list[str]:
        return [c["name"] for c in queries.search_cards(self.cur, list(filters), sort, limit)["cards"]]

    def test_search_types(self):
        self.assertEqual(
            queries.SEARCH_TYPES,
            ("Artifact", "Battle", "Creature", "Enchantment", "Instant",
             "Kindred", "Land", "Planeswalker", "Sorcery"),
        )

    def test_result_has_summary_keys_and_total(self):
        insert_card(self.cur, "a1", "Bolt", oracle_id="o1", oracle_text="Deal damage")
        result = queries.search_cards(self.cur, [f("name", "contains", "bolt")], "name")
        self.assertEqual(result["total"], 1)
        self.assertEqual(
            set(result["cards"][0]),
            {"id", "name", "mana_cost", "type_line", "colors", "rarity", "set_code", "image_url"},
        )

    def test_no_match_total_zero(self):
        self.assertEqual(queries.search_cards(self.cur, [f("name", "contains", "x")], "name"),
                         {"total": 0, "cards": []})

    def test_oracle_text_contains(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", oracle_text="Create a Treasure token")
        insert_card(self.cur, "a2", "B", oracle_id="o2", oracle_text="Draw a card")
        insert_card(self.cur, "a3", "C", oracle_id="o3")
        self.assertEqual(self.search(f("oracle_text", "contains", "treasure")), ["A"])

    def test_oracle_text_not_contains(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", oracle_text="Create a Treasure token")
        insert_card(self.cur, "a2", "B", oracle_id="o2", oracle_text="Draw a card")
        insert_card(self.cur, "a3", "C", oracle_id="o3")
        self.assertEqual(self.search(f("oracle_text", "not_contains", "treasure")), ["B"])

    def test_oracle_contains_falls_back_to_keywords(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", keywords=["Flying", "Transform"])
        self.assertEqual(self.search(f("oracle_text", "contains", "fly")), ["A"])
        self.assertEqual(self.search(f("oracle_text", "not_contains", "zzz")), [])

    def test_name_contains_and_not_contains(self):
        insert_card(self.cur, "a1", "Lightning Bolt", oracle_id="o1")
        insert_card(self.cur, "a2", "Giant Growth", oracle_id="o2")
        self.assertEqual(self.search(f("name", "contains", "BOLT")), ["Lightning Bolt"])
        self.assertEqual(self.search(f("name", "not_contains", "bolt")), ["Giant Growth"])

    def test_keywords_contains_and_not_contains(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", keywords=["Flying", "Haste"])
        insert_card(self.cur, "a2", "B", oracle_id="o2", keywords=["Trample"])
        insert_card(self.cur, "a3", "C", oracle_id="o3")
        self.assertEqual(self.search(f("keywords", "contains", "hast")), ["A"])
        self.assertEqual(self.search(f("keywords", "not_contains", "hast")), ["B"])

    def test_type_is_whole_word(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", type_line="Land")
        insert_card(self.cur, "a2", "B", oracle_id="o2", type_line="Legendary Land — Gate")
        insert_card(self.cur, "a3", "C", oracle_id="o3", type_line="Creature — Landfall Elf")
        self.assertEqual(self.search(f("type", "is", "Land")), ["A", "B"])

    def test_type_is_not(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", type_line="Land")
        insert_card(self.cur, "a2", "B", oracle_id="o2", type_line="Creature — Elf")
        insert_card(self.cur, "a3", "C", oracle_id="o3")
        self.assertEqual(self.search(f("type", "is_not", "Land")), ["B"])

    def test_type_contains_and_not_contains(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", type_line="Creature — Landfall Elf")
        insert_card(self.cur, "a2", "B", oracle_id="o2", type_line="Instant")
        insert_card(self.cur, "a3", "C", oracle_id="o3")
        self.assertEqual(self.search(f("type", "contains", "landf")), ["A"])
        self.assertEqual(self.search(f("type", "not_contains", "landf")), ["B"])

    def test_kindred_matches_tribal(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1", type_line="Kindred Sorcery — Elf")
        insert_card(self.cur, "a2", "B", oracle_id="o2", type_line="Tribal Instant — Goblin")
        insert_card(self.cur, "a3", "C", oracle_id="o3", type_line="Instant")
        self.assertEqual(self.search(f("type", "is", "Kindred")), ["A", "B"])

    def test_colors_any(self):
        insert_card(self.cur, "a1", "Red", oracle_id="o1", colors=["R"])
        insert_card(self.cur, "a2", "Green", oracle_id="o2", colors=["G"])
        insert_card(self.cur, "a3", "Colorless", oracle_id="o3", colors=[])
        insert_card(self.cur, "a4", "Null", oracle_id="o4")
        self.assertEqual(self.search(f("colors", "any", ["R"])), ["Red"])
        self.assertEqual(self.search(f("colors", "any", ["R", "C"])), ["Colorless", "Red"])

    def test_colors_all(self):
        insert_card(self.cur, "a1", "RG", oracle_id="o1", colors=["R", "G"])
        insert_card(self.cur, "a2", "R", oracle_id="o2", colors=["R"])
        insert_card(self.cur, "a3", "Null", oracle_id="o3")
        self.assertEqual(self.search(f("colors", "all", ["R", "G"])), ["RG"])
        self.assertEqual(self.search(f("colors", "all", ["R"])), ["R", "RG"])

    def test_colors_all_with_c_is_empty(self):
        insert_card(self.cur, "a1", "RG", oracle_id="o1", colors=["R", "G"])
        insert_card(self.cur, "a2", "Colorless", oracle_id="o2", colors=[])
        self.assertEqual(self.search(f("colors", "all", ["C", "R"])), [])
        self.assertEqual(self.search(f("colors", "all", ["C"])), ["Colorless"])

    def test_colors_none(self):
        insert_card(self.cur, "a1", "Red", oracle_id="o1", colors=["R"])
        insert_card(self.cur, "a2", "Green", oracle_id="o2", colors=["G"])
        insert_card(self.cur, "a3", "Colorless", oracle_id="o3", colors=[])
        self.assertEqual(self.search(f("colors", "none", ["R"])), ["Colorless", "Green"])

    def test_colors_none_c_excludes_only_colorless(self):
        insert_card(self.cur, "a1", "Red", oracle_id="o1", colors=["R"])
        insert_card(self.cur, "a2", "Colorless", oracle_id="o2", colors=[])
        insert_card(self.cur, "a3", "Null", oracle_id="o3")
        self.assertEqual(self.search(f("colors", "none", ["C"])), ["Red"])

    def test_null_never_matches_negative(self):
        insert_card(self.cur, "a1", "A", oracle_id="o1")
        self.assertEqual(self.search(f("type", "is_not", "Land")), [])
        self.assertEqual(self.search(f("colors", "none", ["G"])), [])

    def test_user_example(self):
        def land(id: str, name: str, text: str | None, type_line: str = "Land") -> None:
            insert_card(self.cur, id, name, oracle_id=id, oracle_text=text, type_line=type_line)

        land("l1", "Artifact Land", "Add one mana. Create a Treasure artifact token.")
        land("l2", "Land", "Create an artifact token.")
        land("l3", "Clue Land", "Create an artifact token. Clue")
        land("l4", "Landfall Creature", "Create an artifact token.", "Creature — Landfall Elf")
        insert_card(self.cur, "l5", "Land", oracle_id="l2", oracle_text="Create an artifact token.",
                    type_line="Land", released_at="2000-01-01")  # second printing
        names = self.search(
            f("oracle_text", "contains", "artifact"),
            f("oracle_text", "contains", "token"),
            f("oracle_text", "not_contains", "clue"),
            f("type", "is", "Land"),
        )
        self.assertEqual(names, ["Artifact Land", "Land"])

    def test_wildcards_literal(self):
        insert_card(self.cur, "a1", "50% Off", oracle_id="o1")
        insert_card(self.cur, "a2", "500 Off", oracle_id="o2")
        insert_card(self.cur, "a3", "abc", oracle_id="o3")
        self.assertEqual(self.search(f("name", "contains", "50%")), ["50% Off"])
        self.assertEqual(self.search(f("name", "contains", "a_c")), [])

    def test_latest_matching_printing_shown(self):
        insert_card(self.cur, "old", "Card", oracle_id="o1", oracle_text="Flying", released_at="2000-01-01")
        insert_card(self.cur, "new", "Card", oracle_id="o1", oracle_text="Reach", released_at="2020-01-01")
        cards = queries.search_cards(self.cur, [f("oracle_text", "contains", "flying")], "name")["cards"]
        self.assertEqual([c["id"] for c in cards], ["old"])
        cards = queries.search_cards(self.cur, [f("name", "contains", "card")], "name")["cards"]
        self.assertEqual([c["id"] for c in cards], ["new"])

    def test_sort_cmc_asc_desc_nulls_last(self):
        insert_card(self.cur, "a1", "B", oracle_id="o1", cmc=2)
        insert_card(self.cur, "a2", "A", oracle_id="o2", cmc=2)
        insert_card(self.cur, "a3", "C", oracle_id="o3", cmc=5)
        insert_card(self.cur, "a4", "D", oracle_id="o4")
        flt = f("name", "not_contains", "zzz")
        self.assertEqual(self.search(flt, sort="name"), ["A", "B", "C", "D"])
        self.assertEqual(self.search(flt, sort="cmc_asc"), ["A", "B", "C", "D"])
        self.assertEqual(self.search(flt, sort="cmc_desc"), ["C", "A", "B", "D"])

    def test_limit_and_total(self):
        for i in range(5):
            insert_card(self.cur, f"a{i}", f"Card {i}", oracle_id=f"o{i}")
        result = queries.search_cards(self.cur, [f("name", "contains", "card")], "name", limit=2)
        self.assertEqual(len(result["cards"]), 2)
        self.assertEqual(result["total"], 5)

    def test_excludes_tokens(self):
        insert_card(self.cur, "a1", "Elemental", oracle_id="o1", layout="token")
        insert_card(self.cur, "a2", "Elemental Shaman", oracle_id="o2", layout="normal")
        self.assertEqual(self.search(f("name", "contains", "elemental")), ["Elemental Shaman"])

    def test_unknown_filter_raises(self):
        with self.assertRaises(ValueError):
            queries.search_cards(self.cur, [f("name", "bogus", "x")], "name")


if __name__ == "__main__":
    unittest.main()
