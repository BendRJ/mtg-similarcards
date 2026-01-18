"""
Docstring for database.sql.insert.example_insert
"""
from pathlib import Path
from typing import cast, LiteralString
from src.database.db import get_cursor

# Load SQL statement from file
SQL_FILE = Path(__file__).parent / "cards_insert.sql"
CARDS_INSERT_SQL = cast(LiteralString, SQL_FILE.read_text())

# Card identification
CARD_ID = "2c6d7ee7-b635-584f-b96f-59979998134f"
CARD_NAME = "Lumra, Bellow of the Woods"

# Card properties
MANA_COST = "{4}{G}{G}"
CMC = 6.0
COLORS = ["G"]
COLOR_IDENTITY = ["G"]

# Card type information
CARD_TYPE = "Legendary Creature — Elemental Bear"
SUPERTYPES = ["Legendary"]
TYPES = ["Creature"]
SUBTYPES = ["Elemental", "Bear"]

# Card metadata
RARITY = "Mythic"
SET_CODE = "BLB"
SET_NAME = "Bloomburrow"
TEXT = "Vigilance, reach\n..."
ARTIST = "Matt Stewart"
NUMBER = "183"

# Card stats
POWER = "*"
TOUGHNESS = "*"

# Card layout and variations
LAYOUT = "normal"
VARIATIONS = ["f4816114...", "7d95bac2..."]
PRINTINGS = ["BLB"]

with get_cursor() as cur:
    cur.execute(CARDS_INSERT_SQL, (
        CARD_ID,
        CARD_NAME,
        MANA_COST,
        CMC,
        COLORS,
        COLOR_IDENTITY,
        CARD_TYPE,
        SUPERTYPES,
        TYPES,
        SUBTYPES,
        RARITY,
        SET_CODE,
        SET_NAME,
        TEXT,
        ARTIST,
        NUMBER,
        POWER,
        TOUGHNESS,
        LAYOUT,
        VARIATIONS,
        PRINTINGS
    ))
    print(f"Inserted/Updated card {CARD_NAME}")
