"""
Unit tests guarding the execution order of the database init scripts.

PostgreSQL's docker-entrypoint-initdb.d runs every file in
src/database/sql/create_tables/ in lexicographic order under ON_ERROR_STOP=1.
A file declaring a REFERENCES foreign key must therefore sort AFTER the file
creating the referenced table.

Getting this wrong is expensive and quiet: the first failing script aborts
initialization, but PGDATA is already initialized, so the postgres_data volume
is left valid-looking and table-less. Every later start logs
"Skipping initialization" and never retries, while the container still reports
healthy. Only dropping the volume recovers it.

That is exactly what happened when card_images.sql sorted before cards.sql
('_' = 0x5F < 's' = 0x73). These tests derive the required order from the
REFERENCES clauses in the SQL itself, so the DDL stays the single source of
truth for dependencies and the filenames are merely checked against it.
"""

import re
import unittest
from pathlib import Path

DDL_DIR = Path(__file__).resolve().parent.parent / "src" / "database" / "sql" / "create_tables"

# Matches "CREATE TABLE foo" and "CREATE TABLE IF NOT EXISTS foo"
CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][\w]*)",
    re.IGNORECASE,
)
# Matches the target of "REFERENCES foo(id)" / "REFERENCES foo (id)"
REFERENCES_RE = re.compile(r"REFERENCES\s+([A-Za-z_][\w]*)\s*\(", re.IGNORECASE)

# Init scripts must be numerically prefixed so execution order is explicit
# rather than an accident of how the table names happen to sort.
PREFIX_RE = re.compile(r"^\d{2}_")


def ddl_files() -> list[Path]:
    """
    DDL files in the order PostgreSQL will execute them.

    sorted() on the filename reproduces the entrypoint's lexicographic glob
    ordering, which is the whole property under test.
    """
    return sorted(DDL_DIR.glob("*.sql"), key=lambda p: p.name)


def tables_created(sql_path: Path) -> set[str]:
    """Table names created by a DDL file."""
    return {m.group(1) for m in CREATE_TABLE_RE.finditer(sql_path.read_text())}


def tables_referenced(sql_path: Path) -> set[str]:
    """Table names a DDL file points at via REFERENCES foreign keys."""
    return {m.group(1) for m in REFERENCES_RE.finditer(sql_path.read_text())}


class TestDDLFileNaming(unittest.TestCase):
    """Every init script carries an explicit numeric order prefix."""

    def test_all_ddl_files_are_numerically_prefixed(self):
        """A file without a NN_ prefix has an accidental position in the run order."""
        unprefixed = [p.name for p in ddl_files() if not PREFIX_RE.match(p.name)]

        self.assertEqual(
            [],
            unprefixed,
            f"DDL files missing a two-digit order prefix: {unprefixed}. "
            f"Rename to NN_<name>.sql, placed after any table they reference.",
        )

    def test_ddl_directory_is_not_empty(self):
        """Guards against the tests silently passing if DDL_DIR moves."""
        self.assertTrue(ddl_files(), f"No .sql files found in {DDL_DIR}")


class TestForeignKeyExecutionOrder(unittest.TestCase):
    """Foreign keys must resolve at the point their file executes."""

    def test_references_resolve_in_execution_order(self):
        """Each REFERENCES target must be created no later than the referencing file."""
        files = ddl_files()

        # table name -> index of the earliest file that creates it
        creation_index: dict[str, int] = {}
        for index, path in enumerate(files):
            for table in tables_created(path):
                creation_index.setdefault(table, index)

        violations: list[str] = []
        for index, path in enumerate(files):
            for table in sorted(tables_referenced(path)):
                created_at = creation_index.get(table)

                if created_at is None:
                    violations.append(
                        f"{path.name} references '{table}', which no file in "
                        f"{DDL_DIR.name}/ creates"
                    )
                elif created_at > index:
                    violations.append(
                        f"{path.name} references '{table}', but it is only created "
                        f"later in {files[created_at].name} - renumber so the "
                        f"referenced table comes first"
                    )
                # created_at == index is allowed: a file may group a table with
                # its own foreign keys. PostgreSQL runs statements top-to-bottom
                # within a file, so this is valid as long as the CREATE precedes
                # the reference - which these regexes cannot verify.

        self.assertEqual(
            [],
            violations,
            "Foreign keys reference tables that do not exist yet at execution time:\n"
            + "\n".join(f"  {v}" for v in violations),
        )


if __name__ == "__main__":
    unittest.main()
