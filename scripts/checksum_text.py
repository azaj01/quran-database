#!/usr/bin/env python3
"""
Verse-level SHA-256 integrity manifest for the Arabic Quran text.

Lets anyone who imports this database prove their copy of the Arabic text is
byte-exact, catching encoding damage, bad migrations, and silent edits.

    python3 scripts/checksum_text.py               # verify quran.db
    python3 scripts/checksum_text.py --generate    # rebuild the manifest

Hashing is deliberately identical to github.com/spqrxi/quranchecksum so the
two manifests are directly comparable: strip -> NFC -> UTF-8 -> SHA-256, with
surah and root hashes rolled up from the concatenated child hashes in order.

Standard library only. See docs/provenance.md for where the text comes from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import unicodedata
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "quran.db"
DEFAULT_MANIFEST = ROOT / "manifest" / "quran-arabic.manifest.json"

EXPECTED_VERSES = 6236
EXPECTED_SURAHS = 114


def digest(text: str) -> str:
    """Canonical hash of one verse. NFC because Arabic diacritics have more
    than one legal byte sequence; two visually identical verses must hash the
    same or the manifest reports damage that is not there."""
    return hashlib.sha256(
        unicodedata.normalize("NFC", text.strip()).encode("utf-8")
    ).hexdigest()


def read_verses(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        sys.exit(f"{db_path} not found — run `just extract && just sqlite`, or `gunzip -k quran.db.gz`")
    # closing(), not `with sqlite3.connect(...)`: the connection context
    # manager commits the transaction but leaves the handle open.
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as db:
        rows = db.execute(
            "SELECT surah_id, number_in_surah, text FROM ayahs "
            "ORDER BY surah_id, number_in_surah"
        ).fetchall()
    return {f"{surah}:{ayah}": text for surah, ayah, text in rows}


def build(verses: dict[str, str]) -> dict:
    verse_hashes = {key: digest(text) for key, text in verses.items()}

    surah_hashes = {}
    for surah in range(1, EXPECTED_SURAHS + 1):
        ordered = [h for k, h in verse_hashes.items() if int(k.split(":")[0]) == surah]
        surah_hashes[str(surah)] = hashlib.sha256("".join(ordered).encode()).hexdigest()

    return {
        "meta": {
            "format_version": "1.0",
            "kind": "text",
            "source": "tanzil-uthmani",
            "upstream": "KFGQPC Madinah Mushaf -> Tanzil -> alquran.cloud -> this repository",
            "edition": "quran-uthmani (alquran.cloud edition identifier)",
            "extracted": "2018-06-07",
            "normalization": "NFC",
            "hash_algorithm": "sha256",
            "verse_count": len(verse_hashes),
            "surah_count": EXPECTED_SURAHS,
            "granularity": "verse",
            "rollup_method": "sha256 of concatenated child hashes, in canonical order",
        },
        "verses": verse_hashes,
        "surahs": surah_hashes,
        "quran": hashlib.sha256("".join(verse_hashes.values()).encode()).hexdigest(),
    }


def verify(manifest: dict, verses: dict[str, str]) -> int:
    expected = manifest["verses"]
    missing = sorted(set(expected) - set(verses))
    extra = sorted(set(verses) - set(expected))
    changed = [k for k in expected.keys() & verses.keys() if digest(verses[k]) != expected[k]]

    for label, keys in (("missing", missing), ("unexpected", extra), ("changed", changed)):
        if keys:
            print(f"{len(keys)} {label} verse(s): {', '.join(keys[:10])}"
                  f"{' ...' if len(keys) > 10 else ''}", file=sys.stderr)

    if missing or extra or changed:
        return 1

    root = build(verses)["quran"]
    if root != manifest["quran"]:
        print(f"root hash mismatch: {root} != {manifest['quran']}", file=sys.stderr)
        return 1

    print(f"OK — {len(verses)} verses match {manifest['meta']['source']}, root {root[:16]}...")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true", help="rebuild the manifest instead of verifying")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    verses = read_verses(args.db)
    if len(verses) != EXPECTED_VERSES:
        print(f"expected {EXPECTED_VERSES} verses, found {len(verses)}", file=sys.stderr)
        return 1

    if args.generate:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(build(verses), ensure_ascii=False, indent=1) + "\n")
        print(f"wrote {args.manifest} ({len(verses)} verses)")
        return 0

    return verify(json.loads(args.manifest.read_text()), verses)


if __name__ == "__main__":
    raise SystemExit(main())
