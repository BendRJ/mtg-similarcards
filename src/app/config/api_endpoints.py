"""
Module for Scryfall API endpoint configurations.

Scryfall API docs: https://scryfall.com/docs/api
"""

from typing import Optional


class APIEndpointsConfig:
    """
    Storage class for Scryfall API endpoint URLs and default headers.
    """

    BASE_URL = "https://api.scryfall.com"
    SETS_ENDPOINT = f"{BASE_URL}/sets"
    CARDS_COLLECTION_ENDPOINT = f"{BASE_URL}/cards/collection"

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "mtg-similarcards-v1.0",
    }

    # Scryfall limits collection requests to 75 identifiers per call
    MAX_COLLECTION_BATCH_SIZE = 75

    @staticmethod
    def get_set_url(set_code: Optional[str] = None) -> str:
        """Construct URL for set lookup.

        Args:
            set_code: The set code to look up (e.g. 'tdm').
                      If None, returns the URL for all sets.

        Returns:
            Complete URL for the sets endpoint.
        """
        url = APIEndpointsConfig.SETS_ENDPOINT
        if set_code:
            url = f"{url}/{set_code}"
        return url

    @staticmethod
    def get_cards_collection_url() -> str:
        """Return the URL for the cards collection POST endpoint.

        Returns:
            Complete URL for the cards/collection endpoint.
        """
        return APIEndpointsConfig.CARDS_COLLECTION_ENDPOINT

    @staticmethod
    def build_collection_body(
        identifiers: list[dict[str, str]],
    ) -> dict:
        """Build the JSON request body for the cards/collection endpoint.

        Each identifier should be a dict with 'set' and 'collector_number' keys.
        Example: [{"set": "tdm", "collector_number": "1"}]

        Args:
            identifiers: List of card identifier dicts.

        Returns:
            Dict ready to be serialised as JSON request body.

        Raises:
            ValueError: If identifiers list exceeds the max batch size.
        """
        max_size = APIEndpointsConfig.MAX_COLLECTION_BATCH_SIZE
        if len(identifiers) > max_size:
            raise ValueError(
                f"identifiers list has {len(identifiers)} items, "
                f"but Scryfall allows at most {max_size} per request. "
                "Use CardsRetrievalService.get_cards_collection() for automatic batching."
            )
        return {"identifiers": identifiers}
