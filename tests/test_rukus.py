from __future__ import annotations

import importlib.util
import json
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rukus.json"


def load_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_rukus", ROOT / "scripts" / "export_rukus.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load scripts/export_rukus.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = load_module()


class RukuDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(DATA.read_text(encoding="utf-8"))
        cls.rukus = cls.payload["rukus"]

    def test_metadata_identifies_the_source_convention(self) -> None:
        meta = self.payload["meta"]
        self.assertEqual(meta["format_version"], "1.0")
        self.assertEqual(
            meta["convention"], "Quran Foundation global Ruku numbering"
        )
        self.assertEqual(meta["retrieved"], "2026-08-10")
        self.assertEqual(meta["ruku_count"], 558)
        self.assertEqual(meta["ayah_count"], 6236)

    def test_boundaries_cover_every_ayah_once(self) -> None:
        self.assertEqual(
            [ruku["number"] for ruku in self.rukus], list(range(1, 559))
        )
        self.assertEqual(self.rukus[0]["start_ayah_id"], 1)
        self.assertEqual(self.rukus[0]["start_ayah"], "1:1")
        self.assertEqual(self.rukus[-1]["end_ayah_id"], 6236)
        self.assertEqual(self.rukus[-1]["end_ayah"], "114:6")
        self.assertEqual(sum(ruku["ayah_count"] for ruku in self.rukus), 6236)

        for previous, current in zip(self.rukus, self.rukus[1:]):
            self.assertEqual(
                current["start_ayah_id"], previous["end_ayah_id"] + 1
            )

        for ruku in self.rukus:
            self.assertEqual(
                ruku["ayah_count"], ruku["end_ayah_id"] - ruku["start_ayah_id"] + 1
            )

    def test_builder_groups_contiguous_source_metadata(self) -> None:
        verses = [
            {"id": 1, "verse_key": "1:1", "ruku_number": 1},
            {"id": 2, "verse_key": "1:2", "ruku_number": 1},
            {"id": 3, "verse_key": "1:3", "ruku_number": 2},
        ]
        self.assertEqual(
            exporter.build_rukus(verses),
            [
                {
                    "number": 1,
                    "start_ayah_id": 1,
                    "start_ayah": "1:1",
                    "end_ayah_id": 2,
                    "end_ayah": "1:2",
                    "ayah_count": 2,
                },
                {
                    "number": 2,
                    "start_ayah_id": 3,
                    "start_ayah": "1:3",
                    "end_ayah_id": 3,
                    "end_ayah": "1:3",
                    "ayah_count": 1,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
