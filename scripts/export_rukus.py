#!/usr/bin/env python3
"""Export Ruku boundaries from saved Quran Foundation verse metadata."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date, datetime
from itertools import groupby
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "output" / "quran-foundation-verses-by-page.json"
DEFAULT_OUTPUT = ROOT / "data" / "rukus.json"
MANIFEST = ROOT / "manifest" / "quran-arabic.manifest.json"
SOURCE_ENDPOINT = "https://api.quran.com/api/v4/verses/by_page/{page}"
PAGE_COUNT = 604
EXPECTED_AYAH_COUNT = 6236
EXPECTED_RUKU_COUNT = 558


def fetch_verses(source: Path) -> None:
    """Assemble the source dump from the by_page endpoint (one request per page)."""
    verses = []
    for page in range(1, PAGE_COUNT + 1):
        url = SOURCE_ENDPOINT.format(page=page) + "?per_page=50"
        with urllib.request.urlopen(url, timeout=30) as response:
            verses.extend(json.load(response)["verses"])
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        json.dumps({"verses": verses}, ensure_ascii=False), encoding="utf-8"
    )


def validate_verses(verses: list[dict]) -> None:
    if len(verses) != EXPECTED_AYAH_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_AYAH_COUNT:,} ayahs, found {len(verses):,}"
        )
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

    # The manifest lists every verse key in global ayah order.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_keys = list(manifest["verses"])
    for verse, expected in zip(verses, expected_keys):
        if verse["verse_key"] != expected:
            raise ValueError(
                f"Ayah {verse['id']} has key {verse['verse_key']}, "
                f"expected {expected}"
            )


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


def export_rukus(source: Path, output: Path, retrieved: date | None = None) -> dict:
    verses = json.loads(source.read_text(encoding="utf-8"))["verses"]
    validate_verses(verses)
    rukus = build_rukus(verses)

    if [ruku["number"] for ruku in rukus] != list(
        range(1, EXPECTED_RUKU_COUNT + 1)
    ):
        raise ValueError(f"Expected {EXPECTED_RUKU_COUNT} continuous Ruku numbers")

    if retrieved is None:
        retrieved = datetime.fromtimestamp(source.stat().st_mtime).date()

    payload = {
        "meta": {
            "format_version": "1.0",
            "kind": "ruku-boundaries",
            "convention": "Quran Foundation global Ruku numbering",
            "source": "Quran Foundation Content API v4 verse metadata",
            "source_endpoint": SOURCE_ENDPOINT,
            "source_field": "ruku_number",
            "source_terms": (
                "https://api-docs.quran.foundation/legal/developer-terms/"
            ),
            "retrieved": retrieved.isoformat(),
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
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="download the source dump from the API before exporting",
    )
    parser.add_argument(
        "--retrieved",
        type=date.fromisoformat,
        help="retrieval date (YYYY-MM-DD); defaults to the source file's mtime",
    )
    arguments = parser.parse_args()
    if arguments.fetch:
        fetch_verses(arguments.source)
    payload = export_rukus(arguments.source, arguments.output, arguments.retrieved)
    count = payload["meta"]["ruku_count"]
    print(f"Exported {count} Ruku boundaries to {arguments.output}")


if __name__ == "__main__":
    main()
