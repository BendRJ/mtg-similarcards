"""
Route tests for /cards. The database is replaced by a fake cursor and the
query functions are patched, so these check HTTP behaviour only. The SQL is
covered by test_queries_cards.
"""

import unittest
from unittest.mock import MagicMock, patch

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


class TestCardDetailRoutes(CardRoutesTestCase):
    @patch("app.backend.queries.get_card", return_value=None)
    def test_get_card_404(self, _):
        self.assertEqual(self.client.get("/cards/nope").status_code, 404)

    @patch("app.backend.queries.get_card", return_value={"id": "a1", "name": "Bolt"})
    def test_get_card_200(self, _):
        self.assertEqual(self.client.get("/cards/a1").json()["name"], "Bolt")

    @patch("app.backend.queries.get_printings", return_value=[])
    def test_printings_404_when_empty(self, _):
        self.assertEqual(self.client.get("/cards/nope/printings").status_code, 404)


if __name__ == "__main__":
    unittest.main()
