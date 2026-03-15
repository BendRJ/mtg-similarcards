"""Cards ETL — fetches cards for a given set and upserts them into the database."""

import logging
from pathlib import Path
from typing import LiteralString, cast

from pydantic import ValidationError
from psycopg.types.json import Json

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.schema_validation import CardsValidation
from database.etl.cards.cards_retrieval_svc import CardsRetrievalService
from utils.etl_helper import get_search_uri_by_set

setup_logging(log_level=logging.INFO)

SQL_FILE = Path(__file__).parents[2] / "sql" / "upsert" / "cards_upsert.sql"
logging.info(f"Reading SQL file: {SQL_FILE}")
CARDS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())


def _jsonb_or_none(value: dict | list | None) -> Json | None:
    """Wrap a value in psycopg Json for JSONB columns, or return None."""
    return Json(value) if value is not None else None


def run_cards_etl(set_code: str) -> list[dict] | None:
    """Run cards ETL for a given set. Returns list of cards that failed validation."""
    logging.info("Starting cards ETL for set: %s", set_code)

    cards_svc = CardsRetrievalService()

    search_uri = get_search_uri_by_set(set_code)
    if search_uri is None:
        logging.error("No search_uri found for set '%s' — skipping ETL", set_code)
        return None

    set_cards = cards_svc.get_cards_by_set(search_uri)

    logging.info(f"Got {len(set_cards)} cards from set search ({set_code})")
    failed_cards: list[dict] = []

    for mtg_card in set_cards:
        logging.info(f"Processing card: {mtg_card.get('name')} ({mtg_card.get('set')}) - {mtg_card.get('id')}")

        try:
            loaded_dict = CardsValidation.model_validate(mtg_card)
        except ValidationError as e:
            logging.error(f"Validation failed for card {mtg_card.get('name', 'UNKNOWN')}: {e}")
            failed_cards.append(mtg_card)
            continue

        c = loaded_dict.model_dump()

        with get_cursor() as cur:
            cur.execute(CARDS_UPSERT_SQL, (
                c["id"],
                c["oracle_id"],
                c["name"],
                c["lang"],
                c["released_at"],
                c["layout"],
                c["mana_cost"],
                c["cmc"],
                c["type_line"],
                c["oracle_text"],
                c["flavor_text"],
                c["power"],
                c["toughness"],
                c["loyalty"],
                c["colors"], #list but psycopg v3 handles the array adaptation natively
                c["color_identity"],
                c["keywords"],
                c["produced_mana"],
                _jsonb_or_none(c["all_parts"]),
                _jsonb_or_none(c["legalities"]),
                c["games"],
                c["reserved"],
                c["foil"],
                c["nonfoil"],
                c["finishes"],
                c["set_code"],
                c["set_name"],
                c["set_type"],
                c["collector_number"],
                c["digital"],
                c["rarity"],
                c["oversized"],
                c["promo"],
                c["promo_types"],
                c["reprint"],
                c["variation"],
                c["booster"],
                c["full_art"],
                c["textless"],
                c["story_spotlight"],
                c["border_color"],
                c["frame"],
                c["frame_effects"],
                c["security_stamp"],
                c["highres_image"],
                c["image_status"],
                _jsonb_or_none(c["image_uris"]),
                c["artist"],
                c["edhrec_rank"],
                c["penny_rank"],
                _jsonb_or_none(c["prices"]),
            ))
            logging.info(f"Inserted/Updated card: {c['name']} ({c['set_code']})")

    if failed_cards:
        logging.warning(
            f"{len(failed_cards)} cards failed validation: "
            f"{[c.get('name', 'UNKNOWN') for c in failed_cards]}"
        )

    return failed_cards


if __name__ == "__main__":
    failed = run_cards_etl("tdm")
    if failed:
        logging.warning(f"{len(failed)} cards require reprocessing")