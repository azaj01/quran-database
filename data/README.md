# Supplemental datasets

## Ruku boundaries

`rukus.json` records the 558 global Ruku boundaries used by the Quran
Foundation Content API. It is supplemental metadata: it does not change the
repository's Quran text, database dumps, converters, or schemas.

### Format

The top-level `meta` object identifies the format, source, retrieval date, and
Ruku convention. Each item in `rukus` contains:

| Field | Description |
| --- | --- |
| `number` | Global Ruku number in the Quran Foundation convention |
| `start_ayah_id` | First global ayah ID in the Ruku |
| `start_ayah` | First ayah key in `surah:ayah` form |
| `end_ayah_id` | Last global ayah ID in the Ruku |
| `end_ayah` | Last ayah key in `surah:ayah` form |
| `ayah_count` | Number of ayahs in the inclusive range |

Page and Juz fields are intentionally omitted. Page numbers depend on a Mushaf
layout, and a Ruku can cross a Juz boundary; neither belongs in a minimal
boundary record.

### Provenance and reproduction

The data was extracted on 2026-08-10 from the `ruku_number` field returned for
all 6,236 ayahs by the Quran.com API v4 `by_page` endpoint. The ignored source
file is a JSON object with one ordered `verses` array containing `id`,
`verse_key`, and `ruku_number` for every ayah.

Download that response (604 requests) and regenerate the tracked file with:

```sh
python3 scripts/export_rukus.py --fetch
```

Omit `--fetch` to reuse an existing `output/quran-foundation-verses-by-page.json`.
`meta.retrieved` defaults to the source file's modification date; pass
`--retrieved YYYY-MM-DD` to set it explicitly. Every `verse_key` is checked
against `manifest/quran-arabic.manifest.json`.

The [field reference][fields] documents `ruku_number`. The current
[Quran Foundation developer terms][qf-terms] define returned metadata as Quran
Foundation content and restrict redistribution as a dataset without separate
permission. The repository's MIT license does not override those source terms;
redistribution permission must be confirmed before this dataset is released.

### Cross-check and convention difference

Tanzil's independently published [Quran Metadata version 1.0][tanzil-data]
uses a 556-Ruku convention, not 558. Comparing the start boundaries found four
Quran Foundation-only starts (`26:52`, `26:69`, `28:83`, and `31:31`) and two
Tanzil-only starts (`26:53` and `26:70`). This is a documented convention
difference, not evidence that the two extra Rukus are universally canonical.

[fields]: https://api-docs.quran.com/docs/api/field-reference/
[qf-terms]: https://api-docs.quran.foundation/legal/developer-terms/
[tanzil-data]: https://tanzil.net/res/text/metadata/quran-data.xml
