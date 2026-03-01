"""
Unit tests for Scryfall API endpoint configuration.
"""

import unittest
from src.app.config.api_endpoints import APIEndpointsConfig


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for APIEndpointsConfig class."""

    # ------------------------------------------------------------------
    # Base URL & constants
    # ------------------------------------------------------------------

    def test_base_url(self):
        """Test that the base URL points to Scryfall."""
        self.assertEqual(APIEndpointsConfig.BASE_URL, "https://api.scryfall.com")

    def test_sets_endpoint(self):
        """Test that the sets endpoint is correctly configured."""
        self.assertEqual(
            APIEndpointsConfig.SETS_ENDPOINT,
            "https://api.scryfall.com/sets",
        )

    def test_cards_collection_endpoint(self):
        """Test that the cards collection endpoint is correctly configured."""
        self.assertEqual(
            APIEndpointsConfig.CARDS_COLLECTION_ENDPOINT,
            "https://api.scryfall.com/cards/collection",
        )

    def test_default_headers_contain_user_agent(self):
        """Test that default headers include a User-Agent."""
        headers = APIEndpointsConfig.DEFAULT_HEADERS
        self.assertIn("User-Agent", headers)
        self.assertEqual(headers["User-Agent"], "mtg-similarcards-v0.1")

    def test_default_headers_contain_accept(self):
        """Test that default headers include Accept: application/json."""
        headers = APIEndpointsConfig.DEFAULT_HEADERS
        self.assertIn("Accept", headers)
        self.assertEqual(headers["Accept"], "application/json")

    def test_max_collection_batch_size(self):
        """Test that the max batch size is 75 per Scryfall docs."""
        self.assertEqual(APIEndpointsConfig.MAX_COLLECTION_BATCH_SIZE, 75)

    # ------------------------------------------------------------------
    # get_set_url
    # ------------------------------------------------------------------

    def test_get_set_url_no_params(self):
        """Test set URL with no parameters returns all-sets endpoint."""
        url = APIEndpointsConfig.get_set_url()
        self.assertEqual(url, "https://api.scryfall.com/sets")

    def test_get_set_url_with_set_code(self):
        """Test set URL with specific set code."""
        url = APIEndpointsConfig.get_set_url(set_code="tdm")
        self.assertEqual(url, "https://api.scryfall.com/sets/tdm")

    def test_set_url_is_string(self):
        """Test that set URL returns a string."""
        url = APIEndpointsConfig.get_set_url()
        self.assertIsInstance(url, str)

    def test_set_url_contains_base_url(self):
        """Test that set URL contains the Scryfall base URL."""
        url = APIEndpointsConfig.get_set_url(set_code="blb")
        self.assertIn("api.scryfall.com", url)

    # ------------------------------------------------------------------
    # get_cards_collection_url
    # ------------------------------------------------------------------

    def test_get_cards_collection_url(self):
        """Test that the collection URL is returned correctly."""
        url = APIEndpointsConfig.get_cards_collection_url()
        self.assertEqual(url, "https://api.scryfall.com/cards/collection")

    # ------------------------------------------------------------------
    # build_collection_body
    # ------------------------------------------------------------------

    def test_build_collection_body_single_identifier(self):
        """Test building a collection body with one identifier."""
        identifiers = [{"set": "tdm", "collector_number": "1"}]
        body = APIEndpointsConfig.build_collection_body(identifiers)
        self.assertEqual(body, {"identifiers": identifiers})

    def test_build_collection_body_multiple_identifiers(self):
        """Test building a collection body with multiple identifiers."""
        identifiers = [
            {"set": "tdm", "collector_number": "1"},
            {"set": "tdm", "collector_number": "2"},
            {"set": "blb", "collector_number": "183"},
        ]
        body = APIEndpointsConfig.build_collection_body(identifiers)
        self.assertEqual(body, {"identifiers": identifiers})
        self.assertEqual(len(body["identifiers"]), 3)

    def test_build_collection_body_empty_list(self):
        """Test building a collection body with an empty list."""
        body = APIEndpointsConfig.build_collection_body([])
        self.assertEqual(body, {"identifiers": []})

    def test_build_collection_body_exceeds_max_raises(self):
        """Test that exceeding the max batch size raises ValueError."""
        identifiers = [
            {"set": "tdm", "collector_number": str(i)}
            for i in range(76)
        ]
        with self.assertRaises(ValueError):
            APIEndpointsConfig.build_collection_body(identifiers)

    def test_build_collection_body_at_max_does_not_raise(self):
        """Test that exactly 75 identifiers does not raise."""
        identifiers = [
            {"set": "tdm", "collector_number": str(i)}
            for i in range(75)
        ]
        body = APIEndpointsConfig.build_collection_body(identifiers)
        self.assertEqual(len(body["identifiers"]), 75)


if __name__ == "__main__":
    unittest.main()
