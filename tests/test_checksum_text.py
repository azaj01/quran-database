from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from tests import load_script

ROOT = Path(__file__).resolve().parents[1]

checksum = load_script("checksum_text")

# Two real verses, enough to exercise hashing without shipping a fixture DB.
VERSES = {
    "1:1": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
    "1:2": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
}


class DigestTests(unittest.TestCase):
    def test_ignores_surrounding_whitespace(self) -> None:
        self.assertEqual(checksum.digest("  نص  "), checksum.digest("نص"))

    def test_decomposed_and_composed_arabic_hash_alike(self) -> None:
        # NFD and NFC of the same verse must agree, or the manifest would
        # report damage on a copy that merely round-tripped through a
        # different Unicode normalisation.
        import unicodedata

        text = VERSES["1:1"]
        self.assertEqual(
            checksum.digest(unicodedata.normalize("NFD", text)),
            checksum.digest(text),
        )

    def test_a_single_changed_diacritic_changes_the_hash(self) -> None:
        self.assertNotEqual(
            checksum.digest(VERSES["1:1"]),
            checksum.digest(VERSES["1:1"].replace("َ", "ُ", 1)),
        )


class VerifyTests(unittest.TestCase):
    def test_unmodified_text_verifies(self) -> None:
        manifest = checksum.build(VERSES)
        self.assertEqual(checksum.verify(manifest, VERSES), 0)

    def test_tampered_verse_is_rejected(self) -> None:
        manifest = checksum.build(VERSES)
        tampered = dict(VERSES, **{"1:2": VERSES["1:2"] + "ّ"})
        self.assertEqual(checksum.verify(manifest, tampered), 1)

    def test_missing_verse_is_rejected(self) -> None:
        manifest = checksum.build(VERSES)
        self.assertEqual(checksum.verify(manifest, {"1:1": VERSES["1:1"]}), 1)

    def test_rollups_are_order_dependent(self) -> None:
        reversed_verses = dict(reversed(list(VERSES.items())))
        self.assertNotEqual(
            checksum.build(VERSES)["quran"], checksum.build(reversed_verses)["quran"]
        )


class ReadVersesTests(unittest.TestCase):
    def test_reads_ayahs_in_canonical_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quran.db"
            with closing(sqlite3.connect(path)) as db:
                db.execute(
                    "CREATE TABLE ayahs (surah_id INT, number_in_surah INT, text TEXT)"
                )
                db.executemany(
                    "INSERT INTO ayahs VALUES (?, ?, ?)",
                    [(1, 2, VERSES["1:2"]), (1, 1, VERSES["1:1"])],
                )
                db.commit()
            self.assertEqual(list(checksum.read_verses(path)), ["1:1", "1:2"])


class ShippedManifestTests(unittest.TestCase):
    def test_manifest_is_well_formed_and_complete(self) -> None:
        manifest = json.loads(
            (ROOT / "manifest" / "quran-arabic.manifest.json").read_text()
        )
        self.assertEqual(len(manifest["verses"]), checksum.EXPECTED_VERSES)
        self.assertEqual(len(manifest["surahs"]), checksum.EXPECTED_SURAHS)
        self.assertEqual(manifest["meta"]["verse_count"], checksum.EXPECTED_VERSES)
        self.assertTrue(all(len(h) == 64 for h in manifest["verses"].values()))


if __name__ == "__main__":
    unittest.main()
