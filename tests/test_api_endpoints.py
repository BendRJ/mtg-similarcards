"""
Unit tests for API endpoint configuration using unittest module
"""

import unittest
from src.app.config.api_endpoints import APIEndpointsConfig


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for APIEndpoints class using unittest"""

    def test_base_urls(self):
        """Test that base URLs are correctly configured"""
        self.assertEqual(APIEndpointsConfig.BASE_URL, "https://api.magicthegathering.io/v1")
        self.assertEqual(APIEndpointsConfig.CARDS_ENDPOINT, "https://api.magicthegathering.io/v1/cards")
        self.assertEqual(APIEndpointsConfig.SETS_ENDPOINT, "https://api.magicthegathering.io/v1/sets")

    def test_get_card_url_no_params(self):
        """Test card URL with no parameters"""
        url = APIEndpointsConfig.get_card_url()
        self.assertEqual(url, "https://api.magicthegathering.io/v1/cards")

    def test_get_card_url_with_card_id(self):
        """Test card URL with specific card ID"""
        url = APIEndpointsConfig.get_card_url(card_id="12345")
        self.assertEqual(url, "https://api.magicthegathering.io/v1/cards/12345")

    def test_get_card_url_with_single_query_param(self):
        """Test card URL with single query parameter"""
        url = APIEndpointsConfig.get_card_url(set_code="KTK")
        self.assertEqual(url, "https://api.magicthegathering.io/v1/cards?set=KTK")

    def test_get_card_url_with_multiple_query_params(self):
        """Test card URL with multiple query parameters"""
        url = APIEndpointsConfig.get_card_url(set_code="KTK", rarity="rare", page=2)
        self.assertEqual(url, "https://api.magicthegathering.io/v1/cards?set=KTK&rarity=rare&page=2")

    def test_get_card_url_with_all_query_params(self):
        """Test card URL with all query parameters"""
        url = APIEndpointsConfig.get_card_url(
            set_code="KTK",
            rarity="mythic",
            page=3,
            pageSize=50
        )
        self.assertEqual(
            url,
            "https://api.magicthegathering.io/v1/cards?set=KTK&rarity=mythic&page=3&pageSize=50"
        )

    def test_get_card_url_with_page_zero(self):
        """Test that page=0 is included in query params"""
        url = APIEndpointsConfig.get_card_url(page=0)
        self.assertEqual(url, "https://api.magicthegathering.io/v1/cards?page=0")

    def test_get_set_url_no_params(self):
        """Test set URL with no parameters"""
        url = APIEndpointsConfig.get_set_url()
        self.assertEqual(url, "https://api.magicthegathering.io/v1/sets")

    def test_get_set_url_with_set_code(self):
        """Test set URL with specific set code"""
        url = APIEndpointsConfig.get_set_url(set_code="KTK")
        self.assertEqual(url, "https://api.magicthegathering.io/v1/sets/KTK")

    def test_card_url_contains_base_url(self):
        """Test that card URL contains the base URL"""
        url = APIEndpointsConfig.get_card_url(card_id="123")
        self.assertIn("magicthegathering.io", url)

    def test_set_url_is_string(self):
        """Test that set URL returns a string"""
        url = APIEndpointsConfig.get_set_url()
        self.assertIsInstance(url, str)


if __name__ == '__main__':
    unittest.main()
