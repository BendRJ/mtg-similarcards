"""Sets ETL docstring"""

import logging
from pathlib import Path
from typing import LiteralString, cast

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.INFO)

# Load SQL statement from file
SQL_FILE = Path(__file__).parents[2] / "sql" / "upsert" / "sets_upsert.sql"
logging.info(SQL_FILE)
SETS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())

sets_svc = SetsRetrievalService()

sets = sets_svc.get_sets()


for set in sets:
    logging.info(f"Processing set: {set['name']} ({set['code']})")
    logging.info(f"Raw API response for set: {len(set.keys())} fields")
    loaded_df = SetsValidation.model_validate(set) #only validates
    cleaned_df = loaded_df.model_dump() #model_config with extra="ignore" will drop any fields not defined in the model here!
    logging.info(f"After pydantic validation: {len(set.keys())} fields")

    # Set identification
    SET_CODE = cleaned_df["code"]
    SET_NAME = cleaned_df["name"]

    # Set properties
    SET_TYPE = cleaned_df["set_type"]
    RELEASED_AT = cleaned_df["released_at"]
    CARD_COUNT = cleaned_df["card_count"]
    DIGITAL = cleaned_df["digital"]
    FOIL_ONLY = cleaned_df["foil_only"]
    NONFOIL_ONLY = cleaned_df["nonfoil_only"]
    ICON_SVG_URI = cleaned_df["icon_svg_uri"]

    with get_cursor() as cur:
        cur.execute(SETS_UPSERT_SQL, ( #upsert ensures we never insert duplicate data
            SET_CODE,
            SET_NAME,
            SET_TYPE,
            RELEASED_AT,
            CARD_COUNT,
            DIGITAL,
            FOIL_ONLY,
            NONFOIL_ONLY,
            ICON_SVG_URI
        ))
        logging.info(f"Inserted/Updated set: {SET_NAME} ({SET_CODE})")

    #break