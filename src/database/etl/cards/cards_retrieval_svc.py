"""Service for retrieving MTG card data from the Scryfall API.

Supports two retrieval strategies:
- Collection lookup: POST /cards/collection with specific identifiers
  (set + collector_number). Scryfall limits to 75 identifiers per request;
  this service handles automatic batching.
- Set search: GET via a set's ``search_uri``. Scryfall returns up to 175
  cards per page; this service follows ``next_page`` links automatically.
"""

import logging
import time
from typing import Any

import requests

from app.config.api_endpoints import APIEndpointsConfig
from database.etl.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Scryfall asks for 50-100 ms between requests
RATE_LIMIT_DELAY_SECONDS = 0.1


class CardsRetrievalService(SessionManager):
    """Retrieves MTG card data from the Scryfall API.

    Scryfall API reference: https://scryfall.com/docs/api/cards/collection
    """

    def get_cards_collection(
        self, identifiers: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        """Retrieve cards by a list of identifiers via POST /cards/collection.

        Automatically batches requests when the identifier list exceeds
        Scryfall's 75-item limit.

        Each identifier should contain 'set' and 'collector_number' keys.
        Example: [{"set": "tdm", "collector_number": "1"}]

        Args:
            identifiers: List of card identifier dicts.

        Returns:
            List of card dictionaries.

        Raises:
            requests.RequestException: If any batch request fails after retries.
        """
        if not identifiers:
            return []

        batch_size = APIEndpointsConfig.MAX_COLLECTION_BATCH_SIZE
        batches = [
            identifiers[i : i + batch_size]
            for i in range(0, len(identifiers), batch_size)
        ]

        logger.info(
            "Fetching %d cards in %d batch(es)", len(identifiers), len(batches)
        )

        all_cards: list[dict[str, Any]] = []
        all_not_found: list[dict[str, str]] = []

        for batch_num, batch in enumerate(batches, start=1):
            if batch_num > 1:
                time.sleep(RATE_LIMIT_DELAY_SECONDS)

            cards, not_found = self._post_collection_batch(batch, batch_num)
            all_cards.extend(cards)
            all_not_found.extend(not_found)

        if all_not_found:
            logger.warning(
                "%d identifier(s) were not found: %s",
                len(all_not_found),
                all_not_found,
            )

        logger.info("Retrieved %d cards total", len(all_cards))
        return all_cards

    def _post_collection_batch(
        self,
        identifiers: list[dict[str, str]],
        batch_num: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        """Post a single batch of identifiers to the collection endpoint.

        Args:
            identifiers: Batch of identifier dicts (max 75).
            batch_num: Batch number for logging.

        Returns:
            Tuple of (cards list, not_found list).

        Raises:
            requests.RequestException: If the request fails after retries.
        """
        url = APIEndpointsConfig.get_cards_collection_url()
        body = APIEndpointsConfig.build_collection_body(identifiers)

        logger.info(
            "Batch %d: POSTing %d identifiers to %s",
            batch_num,
            len(identifiers),
            url,
        )

        try:
            response = self.session.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception(
                "Batch %d: Failed to fetch cards from %s", batch_num, url
            )
            raise

        data = response.json()
        cards = data.get("data", [])
        not_found = data.get("not_found", [])

        logger.info(
            "Batch %d: Retrieved %d cards, %d not found",
            batch_num,
            len(cards),
            len(not_found),
        )
        return cards, not_found


    def get_cards_by_set(self, search_uri: str) -> list[dict[str, Any]]:
        """Retrieve all cards for a set via its paginated search URI.

        Scryfall returns: {"object": "list", "total_cards": 408, "has_more": true, "next_page": <url>, "data": [...]}
        with up to 175 cards per page.
        This method follows ``next_page`` links until all pages are
        consumed.

        Args:
            search_uri: The ``search_uri`` from a Scryfall set object
                        (e.g. from the sets API response).

        Returns:
            List of card dictionaries.

        Raises:
            requests.RequestException: If any page request fails after retries.
        """
        all_cards: list[dict[str, Any]] = []
        url: str | None = search_uri
        page = 0

        while url:
            page += 1
            if page > 1:
                time.sleep(RATE_LIMIT_DELAY_SECONDS)

            logger.info("Page %d: fetching cards from %s", page, url)

            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException:
                logger.exception(
                    "Page %d: failed to fetch cards from %s", page, url
                )
                raise

            data = response.json()
            cards = data.get("data", [])
            all_cards.extend(cards) #extend to not nest the list of dict further but just keep appending dicts on same list level

            logger.info("Page %d: retrieved %d cards", page, len(cards))

            url = data.get("next_page") if data.get("has_more") else None

        logger.info(
            "Retrieved %d cards total across %d page(s)", len(all_cards), page
        )
        return all_cards
