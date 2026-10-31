"""
Helpers for tests that run SQL against a real Postgres.

Each test gets a throwaway `bff_test` schema built from the real DDL inside one
transaction, which tearDown rolls back. Postgres DDL is transactional, so
nothing persists, not even in a dev database. Without a reachable database the
tests are skipped, so `make run-all-tests` still works without Docker.
"""

import unittest
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from database.db import get_connection

DDL_DIR = Path(__file__).resolve().parent.parent / "src" / "database" / "sql" / "create_tables"
EMBEDDING_DIM = 384


class DBTestCase(unittest.TestCase):
    """Base class giving each test `self.cur`, a dict_row cursor on an empty schema."""

    @classmethod
    def setUpClass(cls):
        try:
            get_connection().close()
        except psycopg.OperationalError as e:
            raise unittest.SkipTest(f"No database reachable: {e.__class__.__name__}")

    def setUp(self):
        self.conn = get_connection()
        self.cur = self.conn.cursor(row_factory=dict_row)
        self.cur.execute("CREATE SCHEMA bff_test")
        # public stays on the path for the pgvector `vector` type.
        self.cur.execute("SET LOCAL search_path TO bff_test, public")
        # 00_extensions.sql is skipped: the extension already lives in public.
        for ddl in sorted(DDL_DIR.glob("0[1-9]_*.sql")):
            self.cur.execute(ddl.read_text())

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()


def _insert(cur: psycopg.Cursor, table: str, values: dict[str, Any]) -> None:
    columns = list(values)
    cur.execute(
        sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        ),
        [values[c] for c in columns],
    )


def insert_card(cur: psycopg.Cursor, id: str, name: str, **cols: Any) -> None:
    _insert(cur, "cards", {"id": id, "name": name, **cols})


def insert_set(cur: psycopg.Cursor, code: str, name: str, **cols: Any) -> None:
    _insert(cur, "sets", {"code": code, "name": name, **cols})


def insert_image(cur: psycopg.Cursor, card_id: str, image: bytes = b"img",
                 content_type: str | None = "image/jpeg") -> None:
    _insert(cur, "card_images", {"card_id": card_id, "image": image, "content_type": content_type})


def vec(*leading: float) -> str:
    """pgvector literal: the given values, padded with zeros to 384. Pass at least one non-zero."""
    values = list(leading) + [0.0] * (EMBEDDING_DIM - len(leading))
    return "[" + ",".join(str(v) for v in values) + "]"
