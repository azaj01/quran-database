from __future__ import annotations

import importlib.util
import sqlite3
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {"surahs", "ayahs", "editions", "ayah_edition", "juzs", "hizbs"}
EXPECTED_VIEWS = {"surah_stats", "ayah_with_translation"}


def load_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_schema", ROOT / "scripts" / "export_schema.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load scripts/export_schema.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export_schema = load_module()


def read(name: str) -> str:
    return (ROOT / "schema" / name).read_text()


class GeneratedSqliteSchemaTests(unittest.TestCase):
    """The reference is only worth shipping if it is executable SQL."""

    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(read("sqlite/schema.sql"))

    def tearDown(self) -> None:
        self.db.close()

    def objects(self, kind: str) -> set[str]:
        rows = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type = ?", (kind,)
        ).fetchall()
        return {name for (name,) in rows}

    def test_creates_the_documented_tables(self) -> None:
        self.assertEqual(self.objects("table"), EXPECTED_TABLES)

    def test_creates_the_documented_views(self) -> None:
        self.assertEqual(self.objects("view"), EXPECTED_VIEWS)

    def test_carries_no_drop_statements(self) -> None:
        # A reference someone might paste into a live database must not open
        # by dropping their tables.
        self.assertNotIn("DROP", read("sqlite/schema.sql").upper())
        self.assertNotIn("DROP", read("postgres/schema.sql").upper())


class SourceSchemaTests(unittest.TestCase):
    def test_mysql_reference_describes_the_full_source_dump(self) -> None:
        mysql = read("mysql/schema.sql")
        for table in EXPECTED_TABLES | {"users", "password_resets", "migrations"}:
            self.assertIn(f"CREATE TABLE `{table}`", mysql)

    def test_mysql_reference_excludes_row_data(self) -> None:
        self.assertNotIn("INSERT INTO", read("mysql/schema.sql"))


class DriftTests(unittest.TestCase):
    def test_checked_in_files_match_a_fresh_generation(self) -> None:
        """Fails when a converter changes and `just schema` was not re-run."""
        fresh = {
            "sqlite/schema.sql": export_schema.ddl_from_converter(
                ROOT / "convert_to_sqlite.py"
            ),
            "postgres/schema.sql": export_schema.ddl_from_converter(
                ROOT / "convert_to_postgres.py"
            ),
        }
        for name, body in fresh.items():
            with self.subTest(schema=name):
                self.assertIn(body, read(name), f"stale {name} — run `just schema`")


if __name__ == "__main__":
    unittest.main()
