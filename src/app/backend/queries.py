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

# Tokens, emblems, art-series and Jumpstart front cards aren't cards a player looks
# for, and many share a name ("Elemental") under different oracle_ids. Filtered by
# layout and by set type, since some (e.g. front_card in memorabilia sets) only show
# in the latter. Kept out of search and similarity; still reachable by id and on set
# pages. NULL-safe: a NULL layout or set_type stays in.
PLAYABLE: LiteralString = (
    "COALESCE(c.layout, '') NOT IN ('token', 'double_faced_token', 'emblem', 'art_series') "
    "AND COALESCE(c.set_type, '') NOT IN ('token', 'memorabilia', 'minigame')"
)

# Numeric part first so "2" < "10", then the raw string so "10" < "10a".
COLLECTOR_ORDER: LiteralString = (
    "NULLIF(regexp_replace(c.collector_number, '\\D', '', 'g'), '')::numeric NULLS LAST, "
    "c.collector_number"
)

# A stored image wins (existence check only; the bytes are fetched by get_card_image alone).
# Otherwise fall back to the Scryfall link, or NULL when the card has none.
IMAGE_URL: LiteralString = """
    CASE WHEN EXISTS (SELECT 1 FROM card_images ci WHERE ci.card_id = c.id)
         THEN '/cards/' || c.id || '/image'
         ELSE c.image_uris->>'normal' END AS image_url"""

SUMMARY_COLUMNS: LiteralString = (
    "c.id, c.name, c.mana_cost, c.type_line, c.colors, c.rarity, c.set_code, " + IMAGE_URL
)

DETAIL_COLUMNS: LiteralString = SUMMARY_COLUMNS + """,
    c.oracle_id, c.cmc, c.oracle_text, c.flavor_text, c.power, c.toughness, c.loyalty,
    c.keywords, c.color_identity, c.set_name, c.collector_number, c.released_at,
    c.artist, c.legalities, c.image_uris->>'large' AS image_url_large"""

PRINTING_COLUMNS: LiteralString = (
    "c.id, c.set_code, c.set_name, c.collector_number, c.released_at, c.rarity, " + IMAGE_URL
)


# Any-of color filter shared by set pages and random cards. Parameters come from
# color_params. "C" means colorless; NULL colors (double-faced) never match a filter.
COLOR_FILTER: LiteralString = (
    "%(filtered)s IS FALSE OR c.colors && %(colored)s::text[] "
    "OR (%(colorless)s AND c.colors = '{}')"
)


def color_params(colors: list[str] | None) -> dict[str, Any]:
    """Bound parameters for COLOR_FILTER. None means no filter."""
    return {
        "filtered": colors is not None,
        "colored": [c for c in colors if c != "C"] if colors is not None else None,
        "colorless": colors is not None and "C" in colors,
    }


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
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS},
                   c.image_uris->>'small' AS image_url_small
            FROM cards c
            WHERE c.name ILIKE %(contains)s AND {PLAYABLE}
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


def get_card_image(cur: Cursor, card_id: str) -> dict[str, Any] | None:
    """The stored image bytes and content type for a printing, or None if none is stored."""
    cur.execute("SELECT ci.image, ci.content_type FROM card_images ci WHERE ci.card_id = %(card_id)s",
                {"card_id": card_id})
    return cur.fetchone()


def list_sets(cur: Cursor) -> list[dict[str, Any]]:
    """Sets with at least one loaded card, newest first."""
    cur.execute(
        """
        SELECT s.code, s.name, s.released_at, s.set_type, s.card_count, s.icon_svg_uri
        FROM sets s
        WHERE EXISTS (SELECT 1 FROM cards c WHERE c.set_code = s.code)
        ORDER BY s.released_at DESC NULLS LAST, s.code
        """
    )
    return cur.fetchall()


def set_exists(cur: Cursor, set_code: str) -> bool:
    cur.execute("SELECT 1 FROM sets s WHERE lower(s.code) = lower(%(set_code)s)",
                {"set_code": set_code})
    return cur.fetchone() is not None


def get_set_cards(cur: Cursor, set_code: str, colors: list[str] | None) -> list[dict[str, Any]]:
    """A set's cards in collector order, one per card (its lowest collector number).

    colors keeps cards having any of the given colors, "C" meaning colorless.
    None means no filter. Cards with NULL colors (double-faced) never match a filter.
    """
    cur.execute(
        f"""
        SELECT id, name, mana_cost, type_line, colors, rarity, set_code, image_url
        FROM (
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS},
                   NULLIF(regexp_replace(c.collector_number, '\\D', '', 'g'), '')::numeric AS collector_num,
                   c.collector_number
            FROM cards c
            WHERE lower(c.set_code) = lower(%(set_code)s)
              AND ({COLOR_FILTER})
            ORDER BY {CARD_KEY}, {COLLECTOR_ORDER}
        ) t
        ORDER BY t.collector_num NULLS LAST, t.collector_number
        """,
        {"set_code": set_code, **color_params(colors)},
    )
    return cur.fetchall()


def random_cards(cur: Cursor, colors: list[str], limit: int) -> list[dict[str, Any]]:
    """Random playable cards having any of the given colors ("C" = colorless).

    One per card (its most recent printing), picked uniformly among the cards.
    """
    cur.execute(
        f"""
        SELECT id, name, mana_cost, type_line, colors, rarity, set_code, image_url
        FROM (
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS}
            FROM cards c
            WHERE {PLAYABLE} AND ({COLOR_FILTER})
            ORDER BY {CARD_KEY}, c.released_at DESC NULLS LAST, {COLLECTOR_ORDER}
        ) t
        ORDER BY random()
        LIMIT %(limit)s
        """,
        {**color_params(colors), "limit": limit},
    )
    return cur.fetchall()
