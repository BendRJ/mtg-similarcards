"""
Example upsert for the sets table using Tarkir: Dragonstorm data.
"""
from pathlib import Path
from typing import cast, LiteralString
from database.db import get_cursor

# Load SQL statement from file
SQL_FILE = Path(__file__).parent / "sets_upsert.sql"
SETS_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())

# Set identification
SET_CODE = "tdm"
SET_NAME = "Tarkir: Dragonstorm"

# Set properties
SET_TYPE = "expansion"
RELEASED_AT = "2025-04-11"
CARD_COUNT = 427
DIGITAL = False
FOIL_ONLY = False
NONFOIL_ONLY = False
ICON_SVG_URI = "https://svgs.scryfall.io/sets/tdm.svg?1771218000"

with get_cursor() as cur:
    cur.execute(SETS_UPSERT_SQL, (
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
    print(f"Inserted/Updated set {SET_NAME} ({SET_CODE})")
