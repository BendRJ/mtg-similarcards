"""Unit tests for SetsRetrievalService (Scryfall API)."""

import unittest
from unittest.mock import MagicMock, patch

import requests

from database.etl.sets.sets_retrieval_svc import SetsRetrievalService


class TestGetSets(unittest.TestCase):
    """Tests for SetsRetrievalService.get_sets()."""

    def setUp(self):
        self.service = SetsRetrievalService()

    def test_returns_list_of_sets(self):
        """get_sets() returns a list when the Scryfall response contains 'data'."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "has_more": False,
            "data": [
                {"code": "tdm", "name": "Tarkir: Dragonstorm", "set_type": "expansion"}
            ],
        }

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_sets()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["code"], "tdm")
        self.assertEqual(result[0]["name"], "Tarkir: Dragonstorm")

    def test_returns_empty_list_when_no_data_key(self):
        """get_sets() returns an empty list when 'data' key is missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"object": "list"}

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_sets()

        self.assertEqual(result, [])

    def test_raises_on_http_error(self):
        """get_sets() raises HTTPError on a failed response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500")

        with patch.object(self.service.session, "get", return_value=mock_response):
            with self.assertRaises(requests.HTTPError):
                self.service.get_sets()


class TestGetSet(unittest.TestCase):
    """Tests for SetsRetrievalService.get_set()."""

    def setUp(self):
        self.service = SetsRetrievalService()

    def test_returns_single_set(self):
        """get_set() returns the set object directly (no wrapper key)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "set",
            "code": "tdm",
            "name": "Tarkir: Dragonstorm",
            "set_type": "expansion",
            "released_at": "2025-04-11",
            "digital": False,
        }

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_set("tdm")

        self.assertEqual(result["code"], "tdm")
        self.assertEqual(result["name"], "Tarkir: Dragonstorm")
        self.assertEqual(result["set_type"], "expansion")
        self.assertFalse(result["digital"])

    def test_raises_on_http_error(self):
        """get_set() raises HTTPError on a failed response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch.object(self.service.session, "get", return_value=mock_response):
            with self.assertRaises(requests.HTTPError):
                self.service.get_set("INVALID")

    def test_session_has_default_headers(self):
        """Session should include Scryfall-required headers."""
        headers = self.service.session.headers
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)


if __name__ == "__main__":
    unittest.main()
