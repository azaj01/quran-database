from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def load_sqlite_converter() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "convert_to_sqlite", ROOT / "convert_to_sqlite.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load convert_to_sqlite.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_postgres_converter() -> types.ModuleType:
    """Same psycopg2 stubbing as test_convert_to_postgres, so this runs with
    no PostgreSQL client installed."""
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.connect = mock.Mock()
    extensions = types.ModuleType("psycopg2.extensions")
    extensions.connection = object
    extensions.cursor = object
    psycopg2.extensions = extensions

    spec = importlib.util.spec_from_file_location(
        "convert_to_postgres", ROOT / "convert_to_postgres.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load convert_to_postgres.py")
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(
        sys.modules, {"psycopg2": psycopg2, "psycopg2.extensions": extensions}
    ):
        spec.loader.exec_module(module)
    return module


sqlite_converter = load_sqlite_converter()
postgres_converter = load_postgres_converter()
CONVERTERS = {
    "sqlite": sqlite_converter,
    "postgres": postgres_converter,
}


class TargetColumnTests(unittest.TestCase):
    def test_renames_the_two_columns_the_enriched_model_changes(self) -> None:
        for name, converter in CONVERTERS.items():
            with self.subTest(converter=name):
                self.assertEqual(
                    converter.target_columns("ayahs", ["surah_id", "hizb_id"]),
                    ["surah_id", "rub_id"],
                )
                self.assertEqual(
                    converter.target_columns("editions", ["name", "englishName"]),
                    ["name", "english_name"],
                )

    def test_passes_unrenamed_columns_through(self) -> None:
        for name, converter in CONVERTERS.items():
            with self.subTest(converter=name):
                self.assertEqual(
                    converter.target_columns("surahs", ["id", "name_ar"]),
                    ["id", "name_ar"],
                )

    def test_rejects_names_that_are_not_plain_identifiers(self) -> None:
        # These names are interpolated into SQL, so a malformed dump must fail
        # here rather than produce a statement nobody wrote.
        for name, converter in CONVERTERS.items():
            for bad in ("id) VALUES (1); DROP TABLE surahs; --", "", "2col", "a b"):
                with self.subTest(converter=name, column=bad):
                    with self.assertRaises(ValueError):
                        converter.target_columns("surahs", ["id", bad])


class ReorderedDumpTests(unittest.TestCase):
    """The regression this guards: a dump that lists the same columns in a
    different order used to load every value into the wrong field, silently."""

    def convert_fixture(self, fixture: Path) -> sqlite3.Connection:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "quran.db"
            with (
                mock.patch.object(sqlite_converter, "SQL_FILE", str(fixture)),
                mock.patch.object(sqlite_converter, "DB_FILE", str(db_path)),
                mock.patch("builtins.print"),
            ):
                sqlite_converter.convert()

            memory = sqlite3.connect(":memory:")
            self.addCleanup(memory.close)
            disk = sqlite3.connect(db_path)
            try:
                disk.backup(memory)
            finally:
                disk.close()
        return memory

    def test_values_land_in_the_columns_they_are_named_for(self) -> None:
        db = self.convert_fixture(FIXTURES / "reordered_columns.sql")

        name_ar, name_en = db.execute(
            "SELECT name_ar, name_en FROM surahs WHERE id = 1"
        ).fetchone()
        self.assertEqual(name_ar, "الفاتحة")
        self.assertEqual(name_en, "Al-Fatiha")

        (english_name,) = db.execute(
            "SELECT english_name FROM editions WHERE id = 1"
        ).fetchone()
        self.assertEqual(english_name, "Saheeh International")

        (rub_id,) = db.execute("SELECT rub_id FROM ayahs WHERE id = 1").fetchone()
        self.assertEqual(rub_id, 1)

    def test_an_unknown_column_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "unknown_column.sql"
            fixture.write_text(
                "INSERT INTO `surahs` (`id`, `number`, `name_ar`, `name_en`, "
                "`name_en_translation`, `type`, `created_at`, `unexpected`) VALUES\n"
                "(1, 1, 'a', 'b', 'c', 'Meccan', NULL, NULL);\n"
            )
            with self.assertRaises(sqlite3.OperationalError):
                self.convert_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
