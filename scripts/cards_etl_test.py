"""Quick smoke test for Scryfall cards retrieval services."""

import logging
from app.config.logging_config import setup_logging
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService
from database.etl.cards.cards_retrieval_svc import CardsRetrievalService

setup_logging(log_level=logging.DEBUG)

cards_svc = CardsRetrievalService()

identifiers = [
    {"set": "tdm", "collector_number": "1"},
    {"set": "tdm", "collector_number": "2"},
]
cards = cards_svc.get_cards_collection(identifiers)
logging.info(f"\nGot {len(cards)} cards from collection lookup")
for card in cards:
    logging.info(f"  {card['collector_number']}: {card['name']} ({card['set']})")