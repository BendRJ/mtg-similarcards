"""Helper util functions for ETL"""

import logging

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.INFO)


def get_search_uri_by_set(set_code: str) -> str | None:
    """
    Retrieve the search_uri for a given set code.
    """
    logging.info("Retrieving search_uri of set: %s", set_code)

    sets_svc = SetsRetrievalService()
    try:
        df = sets_svc.get_set(set_code)
        return df["search_uri"]
    except (KeyError, TypeError, ValueError) as e:
        logging.info("Couldnt get set %s from api", set_code)
        logging.info("Error: %s", e)
        return None

def _set_has_cards(set_code: str) -> bool:
    """Check whether the cards table already contains rows for a given set."""
    with get_cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM cards WHERE set_code = %s)", (set_code,))
        row = cur.fetchone()
        return bool(row and row[0])
