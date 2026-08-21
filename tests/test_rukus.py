import json
import tempfile
import unittest
from pathlib import Path

from scripts.export_rukus import export_rukus


ROOT = Path(__file__).resolve().parents[1]
RUKUS = ROOT / "data" / "rukus.json"


class RukuDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(RUKUS.read_text(encoding="utf-8"))
        cls.rukus = cls.payload["rukus"]

    def test_boundaries_are_complete_and_continuous(self):
        self.assertEqual(self.payload["ruku_count"], 558)
        self.assertEqual([ruku["id"] for ruku in self.rukus], list(range(1, 559)))
        self.assertEqual(self.rukus[0]["start_verse_id"], 1)
        self.assertEqual(self.rukus[0]["start_verse_key"], "1:1")
        self.assertEqual(self.rukus[-1]["end_verse_id"], 6236)
        self.assertEqual(self.rukus[-1]["end_verse_key"], "114:6")

        for previous, current in zip(self.rukus, self.rukus[1:]):
            self.assertEqual(
                current["start_verse_id"], previous["end_verse_id"] + 1
            )

    def test_page_and_juz_ranges_are_valid(self):
        for ruku in self.rukus:
            self.assertLessEqual(ruku["start_verse_id"], ruku["end_verse_id"])
            self.assertLessEqual(ruku["start_page"], ruku["end_page"])
            self.assertIn(ruku["start_page"], range(1, 605))
            self.assertIn(ruku["end_page"], range(1, 605))
            self.assertIn(ruku["juz"], range(1, 31))

    def test_export_is_reproducible_from_verse_metadata(self):
        verses = []
        for ruku in self.rukus:
            verse_ids = range(ruku["start_verse_id"], ruku["end_verse_id"] + 1)
            for verse_id in verse_ids:
                is_first = verse_id == ruku["start_verse_id"]
                is_last = verse_id == ruku["end_verse_id"]
                verses.append(
                    {
                        "id": verse_id,
                        "verse_key": (
                            ruku["start_verse_key"]
                            if is_first
                            else ruku["end_verse_key"]
                            if is_last
                            else f"test:{verse_id}"
                        ),
                        "page_number": (
                            ruku["end_page"] if is_last else ruku["start_page"]
                        ),
                        "juz_number": ruku["juz"],
                        "ruku_number": ruku["id"],
                    }
                )

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            output = Path(directory) / "rukus.json"
            source.write_text(json.dumps({"verses": verses}), encoding="utf-8")
            self.assertEqual(export_rukus(source, output), self.payload)


if __name__ == "__main__":
    unittest.main()
