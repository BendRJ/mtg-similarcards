"""Read queries behind the API routes.

Every function takes a dict_row cursor and returns plain dicts shaped like the
response models in app.backend.models. Column lists are always explicit, so the
384-float `embedding` never leaves the database. Only the constants below are
interpolated into SQL; every value is a bound parameter.
"""

from pathlib import Path
from typing import Any, LiteralString, cast

import psycopg

Cursor = psycopg.Cursor[dict[str, Any]]

SQL_DIR = Path(__file__).parents[2] / "database" / "sql" / "queries"
SIMILAR_CARDS_SQL = cast(LiteralString, (SQL_DIR / "similar_cards.sql").read_text())

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


def escape_like(text: str) -> str:
    """Escape text for use inside an ILIKE pattern, so it matches literally.

    Postgres LIKE/ILIKE use backslash as the default escape character.
    """
    # Backslash first, or it would double the escapes added for % and _.
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def autocomplete_cards(cur: Cursor, query: str, limit: int) -> list[dict[str, Any]]:
    """Cards whose name contains query, one per card (its most recent printing).

    Names starting with query rank first, then alphabetical.
    """
    escaped = escape_like(query)
    cur.execute(
        f"""
        SELECT * FROM (
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS}
            FROM cards c
            WHERE c.name ILIKE %(contains)s
            ORDER BY {CARD_KEY}, c.released_at DESC NULLS LAST, {COLLECTOR_ORDER}
        ) t
        ORDER BY (t.name ILIKE %(prefix)s) DESC, t.name
        LIMIT %(limit)s
        """,
        {"contains": f"%{escaped}%", "prefix": f"{escaped}%", "limit": limit},
    )
    return cur.fetchall()


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


def similar_cards(cur: Cursor, card_id: str, limit: int) -> list[dict[str, Any]] | None:
    """Most similar other cards, closest first.

    None when no printing of the card has an embedding (including an unknown id),
    so callers can tell that apart from "embedded, but nothing else to compare".
    """
    cur.execute(
        f"""
        SELECT 1 FROM cards c
        WHERE {CARD_KEY} = (SELECT COALESCE(oracle_id, id) FROM cards WHERE id = %(card_id)s)
          AND c.embedding IS NOT NULL
        LIMIT 1
        """,
        {"card_id": card_id},
    )
    if cur.fetchone() is None:
        return None
    cur.execute(SIMILAR_CARDS_SQL, {"card_id": card_id, "limit": limit})
    return cur.fetchall()
