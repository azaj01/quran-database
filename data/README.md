# Supplemental datasets

## Ruku boundaries

`rukus.json` stores 558 global Ruku boundaries extracted on 2026-08-10 from
the `ruku_number` metadata returned for all 6,236 verses by the Quran.com API
v4 `by_page` endpoint. It is kept separate from the repository's Quran text and
databases so the provenance and proposed schema can be reviewed independently
before any database integration.

Each entry records the first and last verse IDs and keys, its page range, and
the Juz containing its first verse. Regenerate it from the locally downloaded
API response with:

```sh
python3 scripts/export_rukus.py
```

The raw API response remains under the ignored `output/` directory. The
[Quran Foundation field reference][fields] defines `ruku_number`, while its
[developer terms][terms] govern use of API content. The repository's MIT
license does not override those source terms.

The committed file records the exact endpoint and retrieval date. Its boundary
sequence is checked by `tests/test_rukus.py`, but it has not been independently
verified against a second authoritative Ruku source.

[fields]: https://api-docs.quran.com/docs/api/field-reference/
[terms]: https://api-docs.quran.foundation/legal/developer-terms/
