"""
Unit tests for app-wide behaviour of the backend-for-frontend: DB error
mapping, CORS, and removed routes. No database needed.
"""

import unittest

import psycopg
from fastapi import Depends
from fastapi.testclient import TestClient

from app.backend.backend import create_app
from app.backend.db import get_db_cursor

ALLOWED_ORIGIN = "http://localhost:5173"


def failing_cursor():
    # Message mimics psycopg echoing connection details; it must never reach the client.
    raise psycopg.OperationalError("connection failed: password=hunter2")
    yield  # pragma: no cover - makes this a generator dependency like the real one


class TestApp(unittest.TestCase):
    def setUp(self):
        app = create_app([ALLOWED_ORIGIN])

        @app.get("/_boom")
        def boom(cur=Depends(get_db_cursor)):
            return {}

        app.dependency_overrides[get_db_cursor] = failing_cursor
        self.client = TestClient(app)

    def test_db_error_returns_503_without_detail(self):
        r = self.client.get("/_boom")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json(), {"detail": "Database unavailable."})
        self.assertNotIn("hunter2", r.text)

    def test_cors_allows_configured_origin(self):
        r = self.client.options("/sets", headers={"Origin": ALLOWED_ORIGIN,
                                                  "Access-Control-Request-Method": "GET"})
        self.assertEqual(r.headers.get("access-control-allow-origin"), ALLOWED_ORIGIN)

    def test_cors_rejects_other_origin(self):
        r = self.client.options("/sets", headers={"Origin": "http://evil.example",
                                                  "Access-Control-Request-Method": "GET"})
        self.assertNotIn("access-control-allow-origin", r.headers)

    def test_list_all_cards_route_removed(self):
        self.assertEqual(self.client.get("/cards").status_code, 404)


if __name__ == "__main__":
    unittest.main()
