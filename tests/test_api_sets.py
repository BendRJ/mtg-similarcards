"""
Route tests for /sets with a fake cursor and patched query functions.
The SQL is covered by test_queries_sets.
"""

import unittest
from unittest.mock import ANY, MagicMock, patch

from fastapi.testclient import TestClient

from app.backend.backend import create_app
from app.backend.db import get_db_cursor


def fake_cursor():
    yield MagicMock()


class TestSetRoutes(unittest.TestCase):
    def setUp(self):
        app = create_app([])
        app.dependency_overrides[get_db_cursor] = fake_cursor
        self.client = TestClient(app)

    @patch("app.backend.queries.list_sets", return_value=[{"code": "mh3", "name": "Modern Horizons 3"}])
    def test_list_sets(self, _):
        r = self.client.get("/sets")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()[0]["code"], "mh3")

    @patch("app.backend.queries.get_set_cards")
    @patch("app.backend.queries.set_exists", return_value=False)
    def test_unknown_set_404(self, _, get_set_cards):
        self.assertEqual(self.client.get("/sets/nope/cards").status_code, 404)
        get_set_cards.assert_not_called()

    @patch("app.backend.queries.get_set_cards", return_value=[])
    @patch("app.backend.queries.set_exists", return_value=True)
    def test_colors_passed_as_list(self, _, get_set_cards):
        self.assertEqual(self.client.get("/sets/mh3/cards?colors=R,G").status_code, 200)
        get_set_cards.assert_called_once_with(ANY, "mh3", ["R", "G"])

    @patch("app.backend.queries.get_set_cards", return_value=[])
    @patch("app.backend.queries.set_exists", return_value=True)
    def test_no_colors_means_no_filter(self, _, get_set_cards):
        self.client.get("/sets/mh3/cards")
        get_set_cards.assert_called_once_with(ANY, "mh3", None)

    @patch("app.backend.queries.set_exists", return_value=True)
    def test_invalid_colors_422(self, _):
        for bad in ["X", "r", "R,,G", "R,"]:
            with self.subTest(colors=bad):
                self.assertEqual(self.client.get(f"/sets/mh3/cards?colors={bad}").status_code, 422)


if __name__ == "__main__":
    unittest.main()
