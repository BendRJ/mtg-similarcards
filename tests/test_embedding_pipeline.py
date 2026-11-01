"""
DB tests for the embedding pipeline core, against a real Postgres (skipped without one).
The model is replaced by a fake encoder, so these test grouping and writing only.
"""

import datetime
import unittest

from database.etl.embedding_pipeline import embed_missing
from tests.db_fixtures import DBTestCase, insert_card, vec


class FakeEncoder:
    """Records every text it is asked to encode; returns a distinct vector per call position."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t))] + [0.0] * 383 for t in texts]

    @property
    def texts(self) -> list[str]:
        return [t for batch in self.calls for t in batch]


class TestEmbedMissing(DBTestCase):
    def embedded(self, card_id: str) -> bool:
        self.cur.execute("SELECT embedding IS NOT NULL AS e FROM cards WHERE id = %s", (card_id,))
        return self.cur.fetchone()["e"]

    def test_each_distinct_text_is_encoded_once_and_written_to_all_printings(self):
        insert_card(self.cur, "p1", "Llanowar Elves", oracle_text="{T}: Add {G}.")
        insert_card(self.cur, "p2", "Llanowar Elves", oracle_text="{T}: Add {G}.")
        insert_card(self.cur, "p3", "Elvish Mystic", oracle_text="{T}: Add {G}.")
        insert_card(self.cur, "s1", "Shock", oracle_text="Shock deals 2 damage to any target.")
        encode = FakeEncoder()
        self.assertEqual(embed_missing(self.cur, encode), 4)
        self.assertEqual(sorted(encode.texts), ["Shock deals 2 damage to any target.", "{T}: Add {G}."])
        self.assertTrue(all(self.embedded(i) for i in ["p1", "p2", "p3", "s1"]))

    def test_keyword_fallback_and_empty_text_skipped(self):
        insert_card(self.cur, "dfc", "Delver", oracle_text=None, keywords=["Flying", "Transform"])
        insert_card(self.cur, "blank", "Vanilla", oracle_text=None, keywords=[])
        encode = FakeEncoder()
        self.assertEqual(embed_missing(self.cur, encode), 1)
        self.assertEqual(encode.texts, ["Flying, Transform"])
        self.assertFalse(self.embedded("blank"))

    def test_already_embedded_cards_are_left_alone(self):
        insert_card(self.cur, "done", "Bolt", oracle_text="3 damage.", embedding=vec(1))
        insert_card(self.cur, "todo", "Shock", oracle_text="2 damage.")
        encode = FakeEncoder()
        self.assertEqual(embed_missing(self.cur, encode), 1)
        self.assertEqual(encode.texts, ["2 damage."])

    def test_batches_respect_batch_size_and_call_after_each_batch(self):
        for i in range(5):
            insert_card(self.cur, f"c{i}", f"Card {i}", oracle_text=f"Text {i}.")
        encode = FakeEncoder()
        done: list[int] = []
        self.assertEqual(embed_missing(self.cur, encode, batch_size=2, after_batch=lambda: done.append(1)), 5)
        self.assertEqual([len(b) for b in encode.calls], [2, 2, 1])
        self.assertEqual(len(done), 3)

    def test_released_after_keeps_cards_with_a_newer_printing_and_embeds_all_their_printings(self):
        insert_card(self.cur, "bolt93", "Bolt", oracle_text="3 damage.", released_at="1993-08-05")
        insert_card(self.cur, "bolt20", "Bolt", oracle_text="3 damage.", released_at="2020-01-01")
        insert_card(self.cur, "old", "Old Card", oracle_text="Only printed long ago.", released_at="2005-01-01")
        insert_card(self.cur, "edge", "Edge Card", oracle_text="Printed on the cutoff day.", released_at="2010-12-31")
        encode = FakeEncoder()
        self.assertEqual(embed_missing(self.cur, encode, released_after=datetime.date(2010, 12, 31)), 2)
        self.assertEqual(encode.texts, ["3 damage."])
        self.assertTrue(self.embedded("bolt93"))
        self.assertTrue(self.embedded("bolt20"))
        self.assertFalse(self.embedded("old"))
        self.assertFalse(self.embedded("edge"))

    def test_nothing_to_do(self):
        insert_card(self.cur, "done", "Bolt", oracle_text="3 damage.", embedding=vec(1))
        encode = FakeEncoder()
        self.assertEqual(embed_missing(self.cur, encode), 0)
        self.assertEqual(encode.calls, [])


if __name__ == "__main__":
    unittest.main()
