"""Read queries behind the API routes.

Every function takes a dict_row cursor and returns plain dicts shaped like the
response models in app.backend.models. Column lists are always explicit, so the
384-float `embedding` never leaves the database. Only the constants below are
interpolated into SQL; every value is a bound parameter.
"""

from typing import Any, LiteralString, cast

import psycopg

Cursor = psycopg.Cursor[dict[str, Any]]


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

# Which printing represents a card: a physical one if any exists (digital = Arena/MTGO-only
# printings sort last, false < true), then the newest, then collector order.
LATEST_PRINTING: LiteralString = "c.digital, c.released_at DESC NULLS LAST, " + COLLECTOR_ORDER

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
            ORDER BY {CARD_KEY}, {LATEST_PRINTING}
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


def similar_cards(cur: Cursor, card_id: str, limit: int, offset: int = 0,
                  filters: list[dict[str, Any]] | None = None) -> list[dict[str, Any]] | None:
    """Most similar other cards by rules-text embedding, closest first.

    One row per card (latest matching printing), excluding the card itself and its
    reprints. The reference vector comes from any embedded printing of the card, so an
    older printing without an embedding still works. Optional advanced-search filters
    (already validated) narrow the candidates before ranking, so a page always holds the
    closest cards that match. Ties are broken by id, which keeps paging stable.

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

    params: dict[str, Any] = {"card_id": card_id, "limit": limit, "offset": offset}
    clauses: list[LiteralString] = []
    for index, flt in enumerate(filters or []):
        clause, clause_params = filter_clause(index, flt)
        clauses.append(clause)
        params.update(clause_params)
    filter_sql: LiteralString = "".join(f" AND {clause}" for clause in clauses)

    cur.execute(
        f"""
        WITH ref AS (
            SELECT COALESCE(oracle_id, id) AS card_key, embedding
            FROM cards
            WHERE COALESCE(oracle_id, id) = (SELECT COALESCE(oracle_id, id) FROM cards WHERE id = %(card_id)s)
              AND embedding IS NOT NULL
            ORDER BY released_at DESC NULLS LAST
            LIMIT 1
        ), candidates AS (
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS},
                   c.embedding <=> ref.embedding AS distance
            FROM cards c
            CROSS JOIN ref
            WHERE c.embedding IS NOT NULL
              AND {CARD_KEY} <> ref.card_key
              AND {PLAYABLE}{filter_sql}
            ORDER BY {CARD_KEY}, {LATEST_PRINTING}
        )
        SELECT id, name, mana_cost, type_line, colors, rarity, set_code, image_url, distance
        FROM candidates
        ORDER BY distance, id
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )
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
            ORDER BY {CARD_KEY}, {LATEST_PRINTING}
        ) t
        ORDER BY random()
        LIMIT %(limit)s
        """,
        {**color_params(colors), "limit": limit},
    )
    return cur.fetchall()


# Card types offered by the advanced search "type is" filter. Only these are ever
# put into a regex, so no user text reaches one.
SEARCH_TYPES = (
    "Artifact", "Battle", "Creature", "Enchantment", "Instant",
    "Kindred", "Land", "Planeswalker", "Sorcery",
)

SEARCH_SORTS: dict[str, LiteralString] = {
    "name": "t.name, t.id",
    "cmc_asc": "t.cmc ASC NULLS LAST, t.name, t.id",
    "cmc_desc": "t.cmc DESC NULLS LAST, t.name, t.id",
}

# Text filters. Negative ones need the column to be known: a NULL never matches.
# {p} is the parameter name. Cards without rules text (some double-faced layouts)
# match "contains" through their keywords instead.
KEYWORD_MATCH: LiteralString = "EXISTS (SELECT 1 FROM unnest(c.keywords) k WHERE k ILIKE %({p})s)"
TEXT_CLAUSES: dict[tuple[str, str], LiteralString] = {
    ("oracle_text", "contains"):
        "(c.oracle_text ILIKE %({p})s OR (c.oracle_text IS NULL AND " + KEYWORD_MATCH + "))",
    ("oracle_text", "not_contains"): "(c.oracle_text IS NOT NULL AND c.oracle_text NOT ILIKE %({p})s)",
    ("name", "contains"): "c.name ILIKE %({p})s",
    ("name", "not_contains"): "c.name NOT ILIKE %({p})s",
    ("keywords", "contains"): KEYWORD_MATCH,
    ("keywords", "not_contains"): "(c.keywords IS NOT NULL AND NOT " + KEYWORD_MATCH + ")",
    ("type", "contains"): "c.type_line ILIKE %({p})s",
    ("type", "not_contains"): "(c.type_line IS NOT NULL AND c.type_line NOT ILIKE %({p})s)",
}

TYPE_CLAUSES: dict[str, LiteralString] = {
    "is": "c.type_line ~* %({p})s",
    "is_not": "(c.type_line IS NOT NULL AND c.type_line !~* %({p})s)",
}

# {p}_c holds the colored letters, {p}_cl whether "C" (colorless) was picked.
COLOR_CLAUSES: dict[str, LiteralString] = {
    "any": "(c.colors && %({p}_c)s::text[] OR (%({p}_cl)s AND c.colors = '{}'))",
    "none": "(c.colors IS NOT NULL AND NOT (c.colors && %({p}_c)s::text[]) "
            "AND NOT (%({p}_cl)s AND c.colors = '{}'))",
}


def filter_clause(index: int, flt: dict[str, Any]) -> tuple[LiteralString, dict[str, Any]]:
    """SQL fragment and bound parameters for one validated filter.

    Parameter names carry the filter's index so several filters can be ANDed.
    Raises ValueError for an unknown (field, op); validation happens upstream.
    """
    field, op, value = flt["field"], flt["op"], flt["value"]
    p = f"p{index}"
    if (field, op) in TEXT_CLAUSES:
        return (cast(LiteralString, TEXT_CLAUSES[field, op].replace("{p}", p)),
                {p: f"%{escape_like(value)}%"})
    if field == "type" and op in TYPE_CLAUSES:
        if value not in SEARCH_TYPES:
            raise ValueError(f"Unknown type: {value!r}")
        # Whole word, so "Land" doesn't match "Landfall". Kindred was once Tribal.
        word = "Kindred|Tribal" if value == "Kindred" else value
        return (cast(LiteralString, TYPE_CLAUSES[op].replace("{p}", p)),
                {p: rf"\m({word})\M"})
    if field == "colors" and op in ("any", "all", "none"):
        colored = [c for c in value if c != "C"]
        colorless = "C" in value
        if op == "all":
            if colorless:
                # Colorless and colored are mutually exclusive.
                return ("FALSE" if colored else "c.colors = '{}'"), {}
            return f"c.colors @> %({p}_c)s::text[]", {f"{p}_c": colored}
        return (cast(LiteralString, COLOR_CLAUSES[op].replace("{p}", p)),
                {f"{p}_c": colored, f"{p}_cl": colorless})
    raise ValueError(f"Unknown filter: {field}.{op}")


def search_cards(cur: Cursor, filters: list[dict[str, Any]], sort: str,
                 limit: int = 200) -> dict[str, Any]:
    """Playable cards matching every filter, one per card (its latest matching printing).

    Returns the first `limit` cards in the given sort and `total`, the full match count.
    """
    clauses: list[LiteralString] = []
    params: dict[str, Any] = {"limit": limit}
    for i, flt in enumerate(filters):
        clause, clause_params = filter_clause(i, flt)
        clauses.append(clause)
        params.update(clause_params)
    where = "".join(f" AND {clause}" for clause in clauses)
    cur.execute(
        f"""
        SELECT id, name, mana_cost, type_line, colors, rarity, set_code, image_url,
               count(*) OVER () AS total
        FROM (
            SELECT DISTINCT ON ({CARD_KEY}) {SUMMARY_COLUMNS}, c.cmc
            FROM cards c
            WHERE {PLAYABLE}{where}
            ORDER BY {CARD_KEY}, {LATEST_PRINTING}
        ) t
        ORDER BY {SEARCH_SORTS[sort]}
        LIMIT %(limit)s
        """,  # type: ignore[arg-type]
        params,
    )
    rows = cur.fetchall()
    total = rows[0]["total"] if rows else 0
    return {"total": total, "cards": [{k: v for k, v in r.items() if k != "total"} for r in rows]}
