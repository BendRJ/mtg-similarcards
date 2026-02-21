"""Unit tests for SetsRetrievalService."""

import unittest
from unittest.mock import MagicMock, patch

import requests

from database.etl.sets.sets_retrieval_svc import SetsRetrievalService


class TestGetSets(unittest.TestCase):
    """Tests for SetsRetrievalService.get_sets()."""

    def setUp(self):
        self.service = SetsRetrievalService()

    def test_returns_list_of_sets(self):
        """Test that get_sets() returns a list of sets when the API response contains a 'sets' key."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sets": [{"code": "KTK", "name": "Khans of Tarkir"}]
        }

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_sets()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["code"], "KTK")

    def test_returns_empty_list_when_no_sets_key(self):
        """
        Test that get_sets() returns an empty list when the API response does not contain a 'sets' key.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {}

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_sets()

        self.assertEqual(result, [])

    def test_raises_on_http_error(self):
        """
        Test that get_sets() raises an HTTPError when the API response indicates an error.
        """
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
        """
        Test that get_set() returns a single set when the API response contains a 'set' key.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "set": {"code": "KTK", "name": "Khans of Tarkir"}
        }

        with patch.object(self.service.session, "get", return_value=mock_response):
            result = self.service.get_set("KTK")

        self.assertEqual(result["code"], "KTK")
        self.assertEqual(result["name"], "Khans of Tarkir")

    def test_raises_on_http_error(self):
        """
        Test that get_set() raises an HTTPError when the API response indicates an error.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch.object(self.service.session, "get", return_value=mock_response):
            with self.assertRaises(requests.HTTPError):
                self.service.get_set("INVALID")


if __name__ == "__main__":
    unittest.main()
