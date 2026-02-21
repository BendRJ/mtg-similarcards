"""Service for retrieving MTG set data from the Scryfall API."""

import logging
from typing import Any

import requests

from app.config.api_endpoints import APIEndpointsConfig
from database.etl.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SetsRetrievalService(SessionManager):
    """Retrieves MTG set data from the Scryfall API.

    Scryfall API reference: https://scryfall.com/docs/api/sets
    """

    def get_sets(self) -> list[dict[str, Any]]:
        """Retrieve all sets from the Scryfall API.

        Scryfall returns: {"object": "list", "has_more": false, "data": [...]}

        Returns:
            List of set dictionaries.

        Raises:
            requests.RequestException: If the request fails after retries.
        """
        url = APIEndpointsConfig.SETS_ENDPOINT
        logger.info("Fetching all sets from %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch sets from %s", url)
            raise

        sets = response.json().get("data", [])
        logger.info("Retrieved %d sets", len(sets))
        return sets

    def get_set(self, set_code: str) -> dict[str, Any]:
        """Retrieve a single set by its code.

        Scryfall returns the set object directly at the top level
        (no wrapper key).

        Args:
            set_code: The set code (e.g. 'tdm').

        Returns:
            Set dictionary.

        Raises:
            requests.RequestException: If the request fails after retries.
        """
        url = APIEndpointsConfig.get_set_url(set_code)
        logger.info("Fetching set '%s' from %s", set_code, url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch set '%s' from %s", set_code, url)
            raise

        return response.json()
