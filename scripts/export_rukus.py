#!/usr/bin/env python3
"""Export Ruku boundaries from a Quran.com API verse response."""

from __future__ import annotations

import argparse
import json
from itertools import groupby
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "output" / "quran-com-verses-by-page.json"
DEFAULT_OUTPUT = ROOT / "data" / "rukus.json"
EXPECTED_VERSE_COUNT = 6236
EXPECTED_RUKU_COUNT = 558


def export_rukus(source: Path, output: Path) -> dict:
    verses = json.loads(source.read_text(encoding="utf-8"))["verses"]
    if len(verses) != EXPECTED_VERSE_COUNT:
        raise ValueError(f"Expected 6,236 verses, found {len(verses)}")
    if [verse.get("id") for verse in verses] != list(
        range(1, EXPECTED_VERSE_COUNT + 1)
    ):
        raise ValueError("Verse IDs are not continuous and ordered")
    if any(verse.get("ruku_number") is None for verse in verses):
        raise ValueError("A verse is missing its Ruku number")

    rukus = []
    for ruku_number, grouped in groupby(verses, key=lambda verse: verse["ruku_number"]):
        group = list(grouped)
        first, last = group[0], group[-1]
        rukus.append(
            {
                "id": ruku_number,
                "start_verse_id": first["id"],
                "start_verse_key": first["verse_key"],
                "end_verse_id": last["id"],
                "end_verse_key": last["verse_key"],
                "start_page": first["page_number"],
                "end_page": last["page_number"],
                "juz": first["juz_number"],
            }
        )

    if [ruku["id"] for ruku in rukus] != list(range(1, EXPECTED_RUKU_COUNT + 1)):
        raise ValueError("Expected 558 continuous Ruku identifiers")

    payload = {
        "source": "Quran.com API v4 verses metadata",
        "source_endpoint": "https://api.quran.com/api/v4/verses/by_page/{page}",
        "retrieved_at": "2026-08-10",
        "source_terms": "https://api-docs.quran.foundation/legal/developer-terms/",
        "ruku_count": len(rukus),
        "rukus": rukus,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    payload = export_rukus(arguments.source, arguments.output)
    print(f"Exported {payload['ruku_count']} Ruku boundaries to {arguments.output}")


if __name__ == "__main__":
    main()
