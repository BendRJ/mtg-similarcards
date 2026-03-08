"""Sets ETL docstring"""

import logging
from pathlib import Path
from typing import LiteralString, cast

from pydantic import ValidationError

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.INFO)

SQL_FILE = Path(__file__).parents[2] / "sql" / "upsert" / "sets_upsert.sql"
logging.info(f"Reading SQL file: {SQL_FILE}")
SETS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())


def run_sets_etl() -> list[dict]:
    """Run sets ETL. Returns list of sets that failed schema validation."""
    # TODO: we could also add a retry mechanism for failed sets here, but for now we just log them and return them for manual reprocessing
    # TODO: handle schema evolution on the database side, e.g. if we add a new field from the API response to the pydantic model, we need to add it to the database table and the upsert SQL statement as well.
    # We could potentially automate this by comparing the pydantic model fields with the database schema and generating the necessary SQL statements, but for now we will just do it manually.
    # manually via docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db & ALTER TABLE statements and updating the pydantic model and upsert SQL statement accordingly.
    # this is ok for now cause we have unit tests that will catch any mismatches between the pydantic model and the database schema
    sets_svc = SetsRetrievalService()
    sets = sets_svc.get_sets()
    failed_sets: list[dict] = []

    for set in sets:
        logging.info(f"Processing set: {set['name']} ({set['code']})")
        logging.info(f"Raw API response for set: {len(set.keys())} fields")

        try:
            loaded_dict = SetsValidation.model_validate(set)
        except ValidationError as e:
            logging.error(f"Validation failed for set {set.get('code', 'UNKNOWN')}: {e}")
            failed_sets.append(set)
            continue

        cleaned_dict = loaded_dict.model_dump()
        logging.info(f"After pydantic validation: {len(cleaned_dict.keys())} fields")

        # Set identification
        SET_CODE = cleaned_dict["code"]
        SET_NAME = cleaned_dict["name"]

        # Set properties
        SET_TYPE = cleaned_dict["set_type"]
        RELEASED_AT = cleaned_dict["released_at"]
        CARD_COUNT = cleaned_dict["card_count"]
        SEARCH_URI = cleaned_dict["search_uri"]
        DIGITAL = cleaned_dict["digital"]
        FOIL_ONLY = cleaned_dict["foil_only"]
        NONFOIL_ONLY = cleaned_dict["nonfoil_only"]
        ICON_SVG_URI = cleaned_dict["icon_svg_uri"]

        with get_cursor() as cur:
            cur.execute(SETS_UPSERT_SQL, (
                SET_CODE,
                SET_NAME,
                SET_TYPE,
                RELEASED_AT,
                CARD_COUNT,
                SEARCH_URI,
                DIGITAL,
                FOIL_ONLY,
                NONFOIL_ONLY,
                ICON_SVG_URI
            ))
            logging.info(f"Inserted/Updated set: {SET_NAME} ({SET_CODE})")

    if failed_sets:
        logging.warning(
            f"{len(failed_sets)} sets failed validation: "
            f"{[s.get('code', 'UNKNOWN') for s in failed_sets]}"
        )

    return failed_sets


if __name__ == "__main__":
    failed = run_sets_etl()
    if failed:
        logging.warning(f"{len(failed)} sets require reprocessing")
