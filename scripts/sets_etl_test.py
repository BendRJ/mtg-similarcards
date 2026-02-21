"""Quick smoke test for Scryfall sets and cards retrieval services."""

import logging
from app.config.logging_config import setup_logging
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService
from database.etl.cards.cards_retrieval_svc import CardsRetrievalService

setup_logging(log_level=logging.DEBUG)

# ── Sets ─────────────────────────────────────────────────────────────
sets_svc = SetsRetrievalService()

# test get_sets (all sets)
sets = sets_svc.get_sets()
logging.info(f"Got {len(sets)} sets")
logging.info(f"First set: {sets[0]['name']}")
logging.info(f"Full payload: {sets[0]}")

# test get_set (single set)
tdm = sets_svc.get_set("tdm")
logging.info(f"Single set: {tdm['name']} ({tdm['code']})")
logging.info(f"  set_type: {tdm['set_type']}")
logging.info(f"  released_at: {tdm['released_at']}")
logging.info(f"  digital: {tdm['digital']}")
