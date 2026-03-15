"""Cards ETL docstring."""

import logging
from pathlib import Path
from typing import LiteralString, cast

from pydantic import ValidationError

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.schema_validation import CardsValidation
from database.etl.cards.cards_retrieval_svc import CardsRetrievalService

setup_logging(log_level=logging.INFO)

SQL_FILE = Path(__file__).parents[2] / "sql" / "upsert" / "cards_upsert.sql"
logging.info(f"Reading SQL file: {SQL_FILE}")
CARDS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())

def run_cards_etl(set_code: str) -> list[dict] | None:
    pass