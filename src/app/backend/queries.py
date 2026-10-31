"""Read queries behind the API routes.

Every function takes a dict_row cursor and returns plain dicts shaped like the
response models in app.backend.models. Column lists are always explicit, so the
384-float `embedding` never leaves the database. Only the constants below are
interpolated into SQL; every value is a bound parameter.
"""

from typing import Any, LiteralString

import psycopg

Cursor = psycopg.Cursor[dict[str, Any]]

# One card across all its printings. Scryfall omits oracle_id on a few layouts
# (e.g. reversible_card); such a printing counts as its own card.
CARD_KEY: LiteralString = "COALESCE(c.oracle_id, c.id)"

# Numeric part first so "2" < "10", then the raw string so "10" < "10a".
COLLECTOR_ORDER: LiteralString = (
    "NULLIF(regexp_replace(c.collector_number, '\\D', '', 'g'), '')::numeric NULLS LAST, "
    "c.collector_number"
)

# Checks existence only; the image bytes are fetched by get_card_image alone.
IMAGE_URL: LiteralString = """
    CASE WHEN EXISTS (SELECT 1 FROM card_images ci WHERE ci.card_id = c.id)
         THEN '/cards/' || c.id || '/image' END AS image_url"""

SUMMARY_COLUMNS: LiteralString = (
    "c.id, c.name, c.mana_cost, c.type_line, c.colors, c.rarity, c.set_code, " + IMAGE_URL
)

DETAIL_COLUMNS: LiteralString = SUMMARY_COLUMNS + """,
    c.oracle_id, c.cmc, c.oracle_text, c.flavor_text, c.power, c.toughness, c.loyalty,
    c.keywords, c.color_identity, c.set_name, c.collector_number, c.released_at,
    c.artist, c.legalities"""

PRINTING_COLUMNS: LiteralString = (
    "c.id, c.set_code, c.set_name, c.collector_number, c.released_at, c.rarity, " + IMAGE_URL
)


def get_card(cur: Cursor, card_id: str) -> dict[str, Any] | None:
    cur.execute(f"SELECT {DETAIL_COLUMNS} FROM cards c WHERE c.id = %(card_id)s",
                {"card_id": card_id})
    return cur.fetchone()


def get_printings(cur: Cursor, card_id: str) -> list[dict[str, Any]]:
    """All printings of the card behind card_id, newest first. Empty for an unknown id."""
    cur.execute(
        f"""
        SELECT {PRINTING_COLUMNS}
        FROM cards c
        WHERE {CARD_KEY} = (SELECT COALESCE(oracle_id, id) FROM cards WHERE id = %(card_id)s)
        ORDER BY c.released_at DESC NULLS LAST, {COLLECTOR_ORDER}
        """,
        {"card_id": card_id},
    )
    return cur.fetchall()
