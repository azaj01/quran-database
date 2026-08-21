#!/usr/bin/env python3
"""Export Ruku boundaries from saved Quran Foundation verse metadata."""

from __future__ import annotations

import argparse
import json
from itertools import groupby
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "output" / "quran-foundation-verses-by-page.json"
DEFAULT_OUTPUT = ROOT / "data" / "rukus.json"
EXPECTED_AYAH_COUNT = 6236
EXPECTED_RUKU_COUNT = 558


def validate_verses(verses: list[dict]) -> None:
    if len(verses) != EXPECTED_AYAH_COUNT:
        raise ValueError(f"Expected 6,236 ayahs, found {len(verses)}")
    if [verse.get("id") for verse in verses] != list(
        range(1, EXPECTED_AYAH_COUNT + 1)
    ):
        raise ValueError("Ayah IDs are not continuous and ordered")

    required = {"id", "verse_key", "ruku_number"}
    for verse in verses:
        missing = required - verse.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Ayah {verse.get('id', '?')} is missing: {fields}")

    if verses[0]["verse_key"] != "1:1" or verses[-1]["verse_key"] != "114:6":
        raise ValueError("Ayah keys do not span 1:1 through 114:6")


def build_rukus(verses: list[dict]) -> list[dict]:
    rukus = []
    grouped_verses = groupby(verses, key=lambda verse: verse["ruku_number"])
    for ruku_number, grouped in grouped_verses:
        group = list(grouped)
        first, last = group[0], group[-1]
        rukus.append(
            {
                "number": ruku_number,
                "start_ayah_id": first["id"],
                "start_ayah": first["verse_key"],
                "end_ayah_id": last["id"],
                "end_ayah": last["verse_key"],
                "ayah_count": len(group),
            }
        )
    return rukus


def export_rukus(source: Path, output: Path) -> dict:
    verses = json.loads(source.read_text(encoding="utf-8"))["verses"]
    validate_verses(verses)
    rukus = build_rukus(verses)

    if [ruku["number"] for ruku in rukus] != list(
        range(1, EXPECTED_RUKU_COUNT + 1)
    ):
        raise ValueError("Expected 558 continuous Ruku numbers")

    payload = {
        "meta": {
            "format_version": "1.0",
            "kind": "ruku-boundaries",
            "convention": "Quran Foundation global Ruku numbering",
            "source": "Quran Foundation Content API v4 verse metadata",
            "source_endpoint": (
                "https://api.quran.com/api/v4/verses/by_page/{page}"
            ),
            "source_field": "ruku_number",
            "source_terms": (
                "https://api-docs.quran.foundation/legal/developer-terms/"
            ),
            "retrieved": "2026-08-10",
            "ruku_count": len(rukus),
            "ayah_count": len(verses),
        },
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
    count = payload["meta"]["ruku_count"]
    print(f"Exported {count} Ruku boundaries to {arguments.output}")


if __name__ == "__main__":
    main()
