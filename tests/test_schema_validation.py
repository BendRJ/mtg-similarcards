"""
Unit tests to verify Pydantic schema models stay aligned with CREATE TABLE SQL definitions.

If a column is added/removed in SQL but not reflected in the Pydantic model (or vice versa),
these tests will fail with a clear diff of the mismatch.
"""

import re
import unittest
from pathlib import Path

from database.etl.schema_validation import CardsValidation, SetsValidation

# Relative to project root (tests are executed from the repo root)
SQL_DIR = Path(__file__).resolve().parent.parent / "src" / "database" / "sql" / "create_tables"


def parse_sql_columns(sql_path: Path) -> set[str]:
    """
    Extract column names from a CREATE TABLE SQL file.

    Parses lines between the opening '(' and closing ');' of the CREATE TABLE
    statement and extracts the first word of each non-empty, non-comment line
    as the column name.
    """
    text = sql_path.read_text()

    # Extract the body between the first '(' and the closing ');'
    match = re.search(r"\((.*)\);", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find CREATE TABLE body in {sql_path}")

    body = match.group(1)
    columns: set[str] = set()

    for line in body.splitlines():
        stripped = line.strip()
        # Skip empty lines and SQL comments
        if not stripped or stripped.startswith("--"):
            continue
        # First word on the line is the column name
        col_match = re.match(r"(\w+)", stripped)
        if col_match:
            columns.add(col_match.group(1))

    return columns


class TestSetsSchemaAlignment(unittest.TestCase):
    """Verify SetsValidation Pydantic fields match sets.sql columns."""

    def test_pydantic_fields_match_sql_columns(self):
        """Every SQL column must exist as a Pydantic field and vice versa."""
        sql_columns = parse_sql_columns(SQL_DIR / "sets.sql")
        pydantic_fields = set(SetsValidation.model_fields.keys())

        self.assertEqual(
            sql_columns,
            pydantic_fields,
            f"Schema mismatch between SetsValidation and sets.sql:\n"
            f"  In SQL but not in Pydantic: {sql_columns - pydantic_fields}\n"
            f"  In Pydantic but not in SQL: {pydantic_fields - sql_columns}",
        )


@unittest.skip("CardsValidation model not yet implemented — add fields to enable this test")
class TestCardsSchemaAlignment(unittest.TestCase):
    """Verify CardsValidation Pydantic fields match cards.sql columns."""

    def test_pydantic_fields_match_sql_columns(self):
        """Every SQL column must exist as a Pydantic field and vice versa."""
        sql_columns = parse_sql_columns(SQL_DIR / "cards.sql")
        pydantic_fields = set(CardsValidation.model_fields.keys())

        self.assertEqual(
            sql_columns,
            pydantic_fields,
            f"Schema mismatch between CardsValidation and cards.sql:\n"
            f"  In SQL but not in Pydantic: {sql_columns - pydantic_fields}\n"
            f"  In Pydantic but not in SQL: {pydantic_fields - sql_columns}",
        )


if __name__ == "__main__":
    unittest.main()
