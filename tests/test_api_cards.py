"""
Route tests for /cards. The database is replaced by a fake cursor and the
query functions are patched, so these check HTTP behaviour only. The SQL is
covered by test_queries_cards.
"""

import unittest
from unittest.mock import ANY, MagicMock, patch

from fastapi.testclient import TestClient

from app.backend.backend import create_app
from app.backend.db import get_db_cursor


def fake_cursor():
    yield MagicMock()


class CardRoutesTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app([])
        app.dependency_overrides[get_db_cursor] = fake_cursor
        self.client = TestClient(app)


class TestRandomRoute(CardRoutesTestCase):
    # get_card raising proves /cards/random isn't shadowed by /cards/{card_id}.
    @patch("app.backend.queries.get_card", side_effect=AssertionError("shadowed by /{card_id}"))
    @patch("app.backend.queries.random_cards", return_value=[])
    def test_random_passes_colors_and_default_limit(self, random_cards, _):
        response = self.client.get("/cards/random?colors=R")
        self.assertEqual(response.status_code, 200)
        random_cards.assert_called_once_with(ANY, ["R"], 100)

    @patch("app.backend.queries.random_cards", return_value=[])
    def test_random_passes_multiple_colors_and_limit(self, random_cards):
        self.assertEqual(self.client.get("/cards/random?colors=R,G&limit=5").status_code, 200)
        random_cards.assert_called_once_with(ANY, ["R", "G"], 5)

    def test_random_requires_colors(self):
        self.assertEqual(self.client.get("/cards/random").status_code, 422)

    def test_random_rejects_unknown_color(self):
        self.assertEqual(self.client.get("/cards/random?colors=X").status_code, 422)

    def test_random_rejects_limit_over_100(self):
        self.assertEqual(self.client.get("/cards/random?colors=R&limit=101").status_code, 422)


class TestCardDetailRoutes(CardRoutesTestCase):
    @patch("app.backend.queries.get_card", return_value=None)
    def test_get_card_404(self, _):
        self.assertEqual(self.client.get("/cards/nope").status_code, 404)

    @patch("app.backend.queries.get_card", return_value={"id": "a1", "name": "Bolt"})
    def test_get_card_200(self, _):
        self.assertEqual(self.client.get("/cards/a1").json()["name"], "Bolt")

    @patch("app.backend.queries.get_card",
           return_value={"id": "a1", "name": "Bolt", "image_url_large": "https://x/l.jpg"})
    def test_get_card_includes_large_image_url(self, _):
        self.assertEqual(self.client.get("/cards/a1").json()["image_url_large"], "https://x/l.jpg")

    @patch("app.backend.queries.get_printings", return_value=[])
    def test_printings_404_when_empty(self, _):
        self.assertEqual(self.client.get("/cards/nope/printings").status_code, 404)


class TestAutocompleteRoute(CardRoutesTestCase):
    @patch("app.backend.queries.get_card", side_effect=AssertionError("matched as a card id"))
    @patch("app.backend.queries.autocomplete_cards", return_value=[{"id": "a1", "name": "Bolt"}])
    def test_autocomplete_not_shadowed_by_card_id(self, autocomplete, _):
        r = self.client.get("/cards/autocomplete?q=bo")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()[0]["id"], "a1")
        autocomplete.assert_called_once_with(unittest.mock.ANY, "bo", 10)

    def test_autocomplete_q_too_short_422(self):
        self.assertEqual(self.client.get("/cards/autocomplete?q=b").status_code, 422)

    def test_autocomplete_limit_over_max_422(self):
        self.assertEqual(self.client.get("/cards/autocomplete?q=bo&limit=26").status_code, 422)


class TestSimilarRoute(CardRoutesTestCase):
    @patch("app.backend.queries.similar_cards")
    @patch("app.backend.queries.get_card", return_value=None)
    def test_similar_unknown_card_404(self, _, similar):
        r = self.client.get("/cards/nope/similar")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "Card not found.")
        similar.assert_not_called()

    @patch("app.backend.queries.similar_cards", return_value=None)
    @patch("app.backend.queries.get_card", return_value={"id": "a1", "name": "Bolt"})
    def test_similar_no_embedding_404_with_own_message(self, *_):
        r = self.client.get("/cards/a1/similar")
        self.assertEqual(r.status_code, 404)
        self.assertNotEqual(r.json()["detail"], "Card not found.")

    @patch("app.backend.queries.similar_cards",
           return_value=[{"id": "s1", "name": "Shock", "distance": 0.1}])
    @patch("app.backend.queries.get_card", return_value={"id": "a1", "name": "Bolt"})
    def test_similar_default_limit_12(self, _, similar):
        r = self.client.get("/cards/a1/similar")
        self.assertEqual(r.json(), [{"id": "s1", "name": "Shock", "mana_cost": None, "type_line": None,
                                     "colors": None, "rarity": None, "set_code": None,
                                     "image_url": None, "distance": 0.1}])
        similar.assert_called_once_with(unittest.mock.ANY, "a1", 12)

    def test_similar_limit_over_max_422(self):
        self.assertEqual(self.client.get("/cards/a1/similar?limit=51").status_code, 422)


class TestCardImageRoute(CardRoutesTestCase):
    @patch("app.backend.queries.get_card_image",
           return_value={"image": b"\x89PNG", "content_type": "image/png"})
    def test_image_served_with_cache_headers(self, _):
        r = self.client.get("/cards/a1/image")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"\x89PNG")
        self.assertEqual(r.headers["content-type"], "image/png")
        self.assertEqual(r.headers["cache-control"], "public, max-age=31536000, immutable")

    @patch("app.backend.queries.get_card_image", return_value={"image": b"img", "content_type": None})
    def test_image_without_content_type_defaults_to_jpeg(self, _):
        self.assertEqual(self.client.get("/cards/a1/image").headers["content-type"], "image/jpeg")

    @patch("app.backend.queries.get_card_image", return_value=None)
    def test_image_missing_404(self, _):
        self.assertEqual(self.client.get("/cards/a1/image").status_code, 404)


if __name__ == "__main__":
    unittest.main()
