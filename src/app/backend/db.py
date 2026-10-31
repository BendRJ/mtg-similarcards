"""Request-scoped database access for the API routes."""

from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from database.db import get_db_connection


def get_db_cursor() -> Iterator[psycopg.Cursor[dict[str, Any]]]:
    """FastAPI dependency yielding a cursor whose rows are dicts.

    One connection per request; it is closed when the response is done.
    """
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            yield cur
