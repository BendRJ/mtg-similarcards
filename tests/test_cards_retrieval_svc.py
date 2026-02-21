"""Unit tests for CardsRetrievalService (Scryfall API)."""

import unittest
from unittest.mock import MagicMock, patch, call

import requests

from database.etl.cards.cards_retrieval_svc import CardsRetrievalService


class TestGetCardsCollection(unittest.TestCase):
    """Tests for CardsRetrievalService.get_cards_collection()."""

    def setUp(self):
        self.service = CardsRetrievalService()

    def test_returns_list_of_cards(self):
        """get_cards_collection() returns card data from the response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "not_found": [],
            "data": [
                {
                    "object": "card",
                    "id": "64a5d494-efa1-446b-bebe-2ad36e154376",
                    "name": "Ugin, Eye of the Storms",
                    "set": "tdm",
                    "collector_number": "1",
                },
                {
                    "object": "card",
                    "id": "abcdef12-3456-7890-abcd-ef1234567890",
                    "name": "Some Other Card",
                    "set": "tdm",
                    "collector_number": "2",
                },
            ],
        }

        identifiers = [
            {"set": "tdm", "collector_number": "1"},
            {"set": "tdm", "collector_number": "2"},
        ]

        with patch.object(self.service.session, "post", return_value=mock_response):
            result = self.service.get_cards_collection(identifiers)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Ugin, Eye of the Storms")
        self.assertEqual(result[1]["collector_number"], "2")

    def test_returns_empty_list_for_empty_identifiers(self):
        """get_cards_collection() returns [] when given no identifiers."""
        result = self.service.get_cards_collection([])
        self.assertEqual(result, [])

    def test_raises_on_http_error(self):
        """get_cards_collection() raises HTTPError on a failed response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500")

        identifiers = [{"set": "tdm", "collector_number": "1"}]

        with patch.object(self.service.session, "post", return_value=mock_response):
            with self.assertRaises(requests.HTTPError):
                self.service.get_cards_collection(identifiers)

    def test_handles_not_found_identifiers(self):
        """get_cards_collection() still returns found cards when some are not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "not_found": [{"set": "tdm", "collector_number": "999"}],
            "data": [
                {
                    "object": "card",
                    "id": "64a5d494-efa1-446b-bebe-2ad36e154376",
                    "name": "Ugin, Eye of the Storms",
                    "set": "tdm",
                    "collector_number": "1",
                },
            ],
        }

        identifiers = [
            {"set": "tdm", "collector_number": "1"},
            {"set": "tdm", "collector_number": "999"},
        ]

        with patch.object(self.service.session, "post", return_value=mock_response):
            result = self.service.get_cards_collection(identifiers)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Ugin, Eye of the Storms")

    @patch("database.etl.cards.cards_retrieval_svc.time.sleep")
    def test_batches_large_identifier_lists(self, mock_sleep):
        """get_cards_collection() splits requests into batches of 75."""
        # Create 80 identifiers → should result in 2 batches (75 + 5)
        identifiers = [
            {"set": "tdm", "collector_number": str(i)} for i in range(80)
        ]

        mock_response_batch1 = MagicMock()
        mock_response_batch1.json.return_value = {
            "object": "list",
            "not_found": [],
            "data": [{"id": str(i), "name": f"Card {i}"} for i in range(75)],
        }

        mock_response_batch2 = MagicMock()
        mock_response_batch2.json.return_value = {
            "object": "list",
            "not_found": [],
            "data": [{"id": str(i), "name": f"Card {i}"} for i in range(75, 80)],
        }

        with patch.object(
            self.service.session,
            "post",
            side_effect=[mock_response_batch1, mock_response_batch2],
        ):
            result = self.service.get_cards_collection(identifiers)

        self.assertEqual(len(result), 80)
        # Verify rate-limit sleep was called between batches
        mock_sleep.assert_called_once()

    def test_session_has_default_headers(self):
        """Session should include Scryfall-required headers."""
        headers = self.service.session.headers
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)


if __name__ == "__main__":
    unittest.main()
