"""Sets ETL docstring"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import LiteralString, cast

from pydantic import ValidationError

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

logger = logging.getLogger(__name__)

SQL_FILE = Path(__file__).parents[2] / "sql" / "upsert" / "sets_upsert.sql"
logger.info(f"Reading SQL file: {SQL_FILE}")
SETS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())


@dataclass
class SetsETLResult:
    """Result of the sets ETL process."""
    failed_sets: list[dict] = field(default_factory=list)
    processed_set_codes: list[str] = field(default_factory=list)


def run_sets_etl(release_year: int | None = None) -> SetsETLResult:
    """Run sets ETL. Returns list of sets that failed schema validation.
    param: release_year
    """
    # TODO: we could also add a retry mechanism for failed sets here, but for now we just log them and return them for manual reprocessing
    # TODO: handle schema evolution on the database side, e.g. if we add a new field from the API response to the pydantic model, we need to add it to the database table and the upsert SQL statement as well.
    # We could potentially automate this by comparing the pydantic model fields with the database schema and generating the necessary SQL statements, but for now we will just do it manually.
    # manually via docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db & ALTER TABLE statements and updating the pydantic model and upsert SQL statement accordingly.
    # this is ok for now cause we have unit tests that will catch any mismatches between the pydantic model and the database schema
    sets_svc = SetsRetrievalService()
    sets = sets_svc.get_sets()
    failed_sets: list[dict] = []
    processed_set_codes: list[str] = []

    for mtg_set in sets:
        logger.info(f"Processing set: {mtg_set['name']} ({mtg_set['code']})")
        if release_year and int(mtg_set["released_at"][:4]) != release_year:
            logger.info(f"Set skipped due to release year of set being before or after {release_year}.")
            continue
        logger.info(f"Raw API response for set: {len(mtg_set.keys())} fields")

        try:
            loaded_dict = SetsValidation.model_validate(mtg_set)
        except ValidationError as e:
            logger.error(f"Validation failed for set {mtg_set.get('code', 'UNKNOWN')}: {e}")
            failed_sets.append(mtg_set)
            continue

        cleaned_dict = loaded_dict.model_dump()
        logger.info(f"After pydantic validation: {len(cleaned_dict.keys())} fields")

        # Set identification
        set_code = cleaned_dict["code"]
        set_name = cleaned_dict["name"]

        processed_set_codes.append(set_code)

        # Set properties
        set_type = cleaned_dict["set_type"]
        released_at = cleaned_dict["released_at"]
        card_count = cleaned_dict["card_count"]
        search_uri = cleaned_dict["search_uri"]
        digital = cleaned_dict["digital"]
        foil_only = cleaned_dict["foil_only"]
        nonfoil_only = cleaned_dict["nonfoil_only"]
        icon_svg_uri = cleaned_dict["icon_svg_uri"]

        with get_cursor() as cur:
            cur.execute(SETS_UPSERT_SQL, (
                set_code,
                set_name,
                set_type,
                released_at,
                card_count,
                search_uri,
                digital,
                foil_only,
                nonfoil_only,
                icon_svg_uri
            ))
            logger.info(f"Inserted/Updated set: {set_name} ({set_code})")

    if failed_sets:
        logger.warning(
            f"{len(failed_sets)} sets failed validation: "
            f"{[s.get('code', 'UNKNOWN') for s in failed_sets]}"
        )

    return SetsETLResult(failed_sets=failed_sets, processed_set_codes=processed_set_codes)


if __name__ == "__main__":
    result = run_sets_etl()
    if result.failed_sets:
        logger.warning(f"{len(result.failed_sets)} sets require reprocessing")
