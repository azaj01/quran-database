from __future__ import annotations

import importlib.util
import sqlite3
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_converter() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "convert_to_sqlite", ROOT / "convert_to_sqlite.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load convert_to_sqlite.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


converter = load_converter()


class PageMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        converter.create_sqlite_schema(self.db)
        self.db.execute("INSERT INTO surahs VALUES (1,1,'a','a','a','Meccan',NULL,NULL)")

    def tearDown(self) -> None:
        self.db.close()

    def add_full_ayah_set(self, page_for_id: int | None = None) -> None:
        rows = []
        for ayah_id in range(1, 6237):
            page = page_for_id or min(604, (ayah_id - 1) * 604 // 6236 + 1)
            rows.append(
                (ayah_id, ayah_id, "t", ayah_id, page, 1, 1, 1, 0, None, None)
            )
        self.db.executemany("INSERT INTO ayahs VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)

    def test_derives_and_validates_the_complete_mapping(self) -> None:
        self.add_full_ayah_set()

        converter.populate_pages(self.db)
        converter.validate_page_mapping(self.db)

        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*), MIN(page_number), MAX(page_number) FROM pages"
            ).fetchone(),
            (604, 1, 604),
        )
        self.assertEqual(
            self.db.execute(
                "SELECT start_ayah_id, end_ayah_id FROM pages WHERE id = 1"
            ).fetchone(),
            (1, 11),
        )
        self.assertEqual(
            self.db.execute(
                "SELECT start_ayah_id, end_ayah_id FROM pages WHERE id = 604"
            ).fetchone(),
            (6227, 6236),
        )

    def test_rejects_an_incomplete_full_source_mapping(self) -> None:
        self.add_full_ayah_set(page_for_id=1)
        converter.populate_pages(self.db)

        with self.assertRaisesRegex(ValueError, "complete 604-page"):
            converter.validate_page_mapping(self.db)


if __name__ == "__main__":
    unittest.main()
