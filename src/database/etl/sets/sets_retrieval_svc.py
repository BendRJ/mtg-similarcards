"""Service for retrieving MTG set data from the API."""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.api_endpoints import APIEndpointsConfig

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3


class SetsRetrievalService:
    """Retrieves MTG set data from the magicthegathering.io API."""

    # calling the class instantiates a new session with retry strategy
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        """Create a requests Session with retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_sets(self) -> list[dict[str, Any]]:
        """Retrieve all sets from the API.

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

        sets = response.json().get("sets", [])
        logger.info("Retrieved %d sets", len(sets))
        return sets

    def get_set(self, set_code: str) -> dict[str, Any]:
        """Retrieve a single set by its code.

        Args:
            set_code: The set code (e.g. 'KTK').

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

        return response.json().get("set", {})
