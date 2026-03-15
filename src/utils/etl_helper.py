"""doc"""

import logging

from app.config.logging_config import setup_logging
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.DEBUG)


def get_search_uri_by_set(set_code: str) -> str | None:
    logging.info("Retrieving search_uri of set: %s", set_code)

    sets_svc = SetsRetrievalService()
    try:
        df = sets_svc.get_set(set_code)
        return df["search_uri"]
    except (KeyError, TypeError, ValueError) as e:
        logging.info("Couldnt get set %s from api", set_code)
        logging.info("Error: %s", e)
