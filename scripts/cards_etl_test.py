"""Quick smoke test for Scryfall cards retrieval services."""

import logging

from app.config.logging_config import setup_logging
from database.etl.cards.cards_retrieval_svc import CardsRetrievalService

setup_logging(log_level=logging.DEBUG)

cards_svc = CardsRetrievalService()

# collection lookup (POST /cards/collection)
identifiers = [
    {"set": "tdm", "collector_number": "1"},
    {"set": "tdm", "collector_number": "2"},
]
cards = cards_svc.get_cards_collection(identifiers)
logging.info(f"\nGot {len(cards)} cards from collection lookup")
for card in cards:
    logging.info(f"  {card['collector_number']}: {card['name']} ({card['set']})")

# set search (GET via search_uri with pagination)
search_uri = (
    "https://api.scryfall.com/cards/search"
    "?include_extras=true&include_variations=true&order=set&q=e%3Atdm&unique=prints"
)
set_cards = cards_svc.get_cards_by_set(search_uri)
logging.info(f"\nGot {len(set_cards)} cards from set search (tdm)")
for card in set_cards[:5]:
    logging.info(f"  {card['collector_number']}: {card['name']} ({card['set']})")
if len(set_cards) > 5:
    logging.info(f"  ... and {len(set_cards) - 5} more")
