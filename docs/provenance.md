# Provenance

Where the Arabic text in this repository comes from, how far it can be
trusted, and how to check that for yourself instead of taking our word for it.

## The chain

```text
KFGQPC Madinah Mushaf        printed reference (Hafs 'an 'Asim)
        |
        v
Tanzil Project               digital transcription, manually verified
tanzil.net                   verse-by-verse against the Madinah Mushaf
        |
        v
alquran.cloud                API distribution; edition `quran-uthmani`
        |
        v
this repository              MySQL dump, generated 2018-06-07
```

Every `editions.identifier` in this database is an alquran.cloud edition ID
(`quran-uthmani`, `quran-simple`, `en.sahih`, `ar.alafasy`, and so on), which
is what pins the third hop. The Arabic in `ayahs.text` is byte-identical to
the `quran-uthmani` edition rows in `ayah_edition`, so the two never drifted
apart inside this repository.

We are three hops from the printed Mushaf. None of those hops is us
retyping the text.

## What the text actually is

Tanzil **Uthmani**, exported with pause marks, sajdah signs, rub-el-hizb
signs, and special tanween included, and without the tatweel that Tanzil
optionally inserts before a superscript alef. Concretely, the text carries:

| | |
| --- | --- |
| `U+0671` ALEF WASLA, `U+0670` SUPERSCRIPT ALEF | Uthmani orthography |
| `U+06D6`–`U+06DA` | pause (waqf) marks |
| `U+06DE` | rub-el-hizb signs |
| `U+06E2`, `U+06ED` | iqlab meem marks (special tanween) |

## Verified against Tanzil, August 2026

The text was compared verse-by-verse against a fresh download from Tanzil:

```bash
curl -o tanzil-uthmani.txt \
  "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2\
&agree=true&marks=true&sajdah=true&rub=true&stanween=true"
```

**5,927 of 6,236 verses (95.0%) are byte-identical** under NFC normalisation.

The 309 that are not differ only in how a character is *carried*, never in
which letters or diacritics are present:

| Count | Difference | Example |
| ---: | --- | --- |
| 277 | `ء` here vs `ـٔ` (tatweel + hamza above) at Tanzil | `ٱلْءَاخِرَةِ` / `ٱلْـَٔاخِرَةِ` |
| 38 | `ۦ` here vs `ـۧ` (tatweel + small high yeh) at Tanzil | |
| 3 | word spacing | `بَعْدَمَا` / `بَعْدَ مَا` (2:181, 8:6, 13:37) |
| 2 | alef maksura carrier under a superscript alef | `يَٰصَىٰحِبَىِ` / `يَٰصَٰحِبَىِ` (12:39, 12:41) |
| 2 | a tatweel joiner | 17:7, 21:88 |

These are the expected consequence of this dump being taken in 2018 from a
Tanzil release whose hamza-carrier convention has since changed. **No letter
and no diacritic of the Quranic text differs** across all 6,236 verses.

## Verifying your own copy

The repository ships a verse-level SHA-256 manifest so you can prove your
import is undamaged:

```bash
just verify
```

That rebuilds every verse hash from `quran.db` and compares it against
`manifest/quran-arabic.manifest.json`, which also carries per-surah and
whole-mushaf root hashes. CI runs it on every push, so a change to the Arabic
text cannot land here unnoticed.

The hashing is deliberately identical to
[quranchecksum](https://github.com/spqrxi/quranchecksum) — strip, NFC, UTF-8,
SHA-256, with rollups over concatenated child hashes — so the two manifests
are directly comparable. Against *their* published manifest this text scores
1,877 / 6,236, for exactly the reasons tabulated above: their manifest
describes a Tanzil export with the annotation marks omitted, which we
confirmed matches a plain Tanzil download 6,236 / 6,236.

## What this does not claim

- It does not re-verify Tanzil's original manual check against the printed
  Madinah Mushaf. That check happened once, at Tanzil, and we inherit it.
- It does not cover the 134 translation and tafsir editions. Those carry the
  provenance of their own translators, and no checksum makes a translation
  correct.
- The strongest honest claim any digital Quran distribution can make is
  "matches this named, verified transcription" — not "is the Quran". That is
  the claim made here.

Corrections to any of the above are welcome; open an issue with the verse
references and the source you checked against.
