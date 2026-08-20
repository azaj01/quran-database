from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def load_converter() -> types.ModuleType:
    """Load the converter without requiring a PostgreSQL client installation."""
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.connect = mock.Mock()
    extensions = types.ModuleType("psycopg2.extensions")
    extensions.connection = object
    extensions.cursor = object
    psycopg2.extensions = extensions

    module_path = ROOT / "convert_to_postgres.py"
    spec = importlib.util.spec_from_file_location("convert_to_postgres", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")

    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(
        sys.modules,
        {"psycopg2": psycopg2, "psycopg2.extensions": extensions},
    ):
        spec.loader.exec_module(module)
    return module


converter = load_converter()


class ParseSqlValueTests(unittest.TestCase):
    def test_parses_null_and_numbers(self) -> None:
        self.assertIsNone(converter.parse_sql_value("NULL"))
        self.assertEqual(converter.parse_sql_value("6236"), 6236)
        self.assertEqual(converter.parse_sql_value("1.5"), 1.5)

    def test_preserves_arabic_text_and_removes_bom(self) -> None:
        value = converter.parse_sql_value("'\ufeffبِسْمِ ٱللَّهِ'")
        self.assertEqual(value, "بِسْمِ ٱللَّهِ")

    def test_unescapes_mysql_string_sequences(self) -> None:
        value = converter.parse_sql_value(r"'line one\nIt\'s here\\done'")
        self.assertEqual(value, "line one\nIt's here\\done")


class ParseInsertRowTests(unittest.TestCase):
    def test_does_not_split_a_comma_inside_text(self) -> None:
        row = converter.parse_insert_row("(1, 'mercy, compassion', NULL);", [])
        self.assertEqual(row, (1, "mercy, compassion", None))


class StreamInsertTests(unittest.TestCase):
    def test_parses_all_fixture_rows_with_matching_widths(self) -> None:
        batches = list(converter.stream_inserts(str(FIXTURES / "out_of_order.sql")))

        self.assertEqual(
            [table for table, _, _ in batches],
            ["ayahs", "ayah_edition", "editions", "surahs"],
        )
        self.assertTrue(batches)
        for _, columns, rows in batches:
            self.assertTrue(rows)
            self.assertTrue(all(len(row) == len(columns) for row in rows))

    def test_batches_follow_foreign_key_dependency_order(self) -> None:
        batches = list(
            converter.stream_inserts_in_dependency_order(
                str(FIXTURES / "out_of_order.sql")
            )
        )
        observed = [table for table, _, _ in batches]

        self.assertEqual(observed, converter.TABLE_ORDER)


class ConversionSafetyTests(unittest.TestCase):
    def test_missing_source_is_rejected_before_connecting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sql"
            with (
                mock.patch.object(converter, "SQL_FILE", str(missing)),
                mock.patch.object(converter.psycopg2, "connect") as connect,
                self.assertRaises(FileNotFoundError),
            ):
                converter.convert()

        connect.assert_not_called()

    def test_schema_creation_does_not_commit_independently(self) -> None:
        database = mock.Mock()

        converter.create_postgres_schema(database)

        database.commit.assert_not_called()

    def test_schema_enforces_lookup_table_relationships(self) -> None:
        database = mock.Mock()

        converter.create_postgres_schema(database)

        schema_sql = database.cursor.return_value.execute.call_args.args[0]
        self.assertGreaterEqual(
            schema_sql.count("juz_id INTEGER NOT NULL REFERENCES juzs(id)"), 2
        )
        self.assertNotIn("rub_id INTEGER NOT NULL REFERENCES hizbs(id)", schema_sql)

    def test_ayahs_names_the_quarter_column_rub_id(self) -> None:
        # The source dump calls this hizb_id, which is wrong: the values run
        # 1-240 (rub' al-hizb quarters) while there are only 60 hizbs. The
        # enriched model must not carry that name forward.
        database = mock.Mock()

        converter.create_postgres_schema(database)

        schema_sql = database.cursor.return_value.execute.call_args.args[0]
        self.assertIn("rub_id INTEGER NOT NULL CHECK(rub_id BETWEEN 1 AND 240)", schema_sql)
        self.assertNotIn("hizb_id", schema_sql)

    def test_insert_failure_rolls_back_and_closes_connection(self) -> None:
        database = mock.Mock()
        database.cursor.return_value.executemany.side_effect = RuntimeError(
            "insert failed"
        )

        with (
            mock.patch.object(
                converter, "SQL_FILE", str(FIXTURES / "out_of_order.sql")
            ),
            mock.patch.object(converter.psycopg2, "connect", return_value=database),
            mock.patch.object(converter, "create_postgres_schema"),
            self.assertRaisesRegex(RuntimeError, "insert failed"),
        ):
            converter.convert()

        database.commit.assert_not_called()
        database.rollback.assert_called_once_with()
        database.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
