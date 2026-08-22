from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tests import load_script

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "surahs", "ayahs", "editions", "ayah_edition", "juzs", "hizbs", "pages"
}
MYSQL_SOURCE_TABLES = EXPECTED_TABLES - {"pages"}
EXPECTED_VIEWS = {"surah_stats", "ayah_with_translation"}

export_schema = load_script("export_schema")


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

    def test_quarter_column_is_named_rub_id(self) -> None:
        columns = {
            row[1]
            for row in self.db.execute("PRAGMA table_info(ayahs)").fetchall()
        }
        self.assertIn("rub_id", columns)
        self.assertNotIn("hizb_id", columns)

    def test_rub_id_rejects_values_outside_the_quarter_range(self) -> None:
        self.db.execute("INSERT INTO surahs VALUES (1,1,'a','a','a','Meccan',NULL,NULL)")
        row = "INSERT INTO ayahs VALUES (?,1,'t',1,1,1,?,1,0,NULL,NULL)"
        self.db.execute(row, (1, 240))  # the highest legal quarter
        for bad in (0, 241):
            with self.subTest(rub_id=bad), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(row, (bad + 100, bad))

    def test_pages_table_maps_ayah_ranges_within_the_mushaf_domain(self) -> None:
        self.db.execute("INSERT INTO surahs VALUES (1,1,'a','a','a','Meccan',NULL,NULL)")
        ayah = "INSERT INTO ayahs VALUES (?,1,'t',1,1,1,1,1,0,NULL,NULL)"
        self.db.executemany(ayah, [(1,), (2,)])
        self.db.execute("INSERT INTO pages VALUES (1,1,1,2)")
        self.assertEqual(
            self.db.execute("SELECT start_ayah_id, end_ayah_id FROM pages").fetchone(),
            (1, 2),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO pages VALUES (605,605,1,2)")

    def test_carries_no_drop_statements(self) -> None:
        # A reference someone might paste into a live database must not open
        # by dropping their tables.
        self.assertNotIn("DROP", read("sqlite/schema.sql").upper())
        self.assertNotIn("DROP", read("postgres/schema.sql").upper())


class SourceSchemaTests(unittest.TestCase):
    def test_mysql_reference_describes_the_full_source_dump(self) -> None:
        mysql = read("mysql/schema.sql")
        for table in MYSQL_SOURCE_TABLES | {"users", "password_resets", "migrations"}:
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
