# Quran Database

A comprehensive MySQL database containing the complete Quran text with multiple translations and editions.

## Contents

The repository includes a `quran.sql.zip` file (~187 MB uncompressed) that contains the full database dump.

## Database Schema

### `quran_surahs`

Stores metadata for all 114 surahs.

| Column             | Description                          |
| ------------------ | ------------------------------------ |
| `id`               | Surah number                         |
| `name_ar`          | Surah name in Arabic (e.g. الفاتحة) |
| `name_en`          | Surah name transliterated (e.g. Al-Fatiha) |
| `name_en_translation` | English meaning (e.g. The Opening) |
| `type`             | Revelation type (Meccan / Medinan)   |

### `quran_ayahs`

Contains the original Arabic text of every ayah.

| Column     | Description              |
| ---------- | ------------------------ |
| `id`       | Unique ayah ID           |
| `surah_id` | Reference to surah       |
| `ayah_id`  | Ayah number within surah |
| `text`     | Ayah text in Arabic      |

### `quran_ayat_edition`

Contains ayah text across different editions and translations.

| Column     | Description                        |
| ---------- | ---------------------------------- |
| `id`       | Unique ID                          |
| `surah_id` | Reference to surah                 |
| `ayah_id`  | Ayah number within surah           |
| `text`     | Ayah text in the given edition     |

### `quran_addons`

Additional metadata and author/scholar information.

| Column  | Description          |
| ------- | -------------------- |
| `id`    | Unique ID            |
| `name`  | Name (Arabic)        |
| `author`| Author / scholar name|

## Setup

1. Extract the SQL file:
   ```bash
   unzip quran.sql.zip
   ```

2. Import into MySQL:
   ```bash
   mysql -u <username> -p <database_name> < quran.sql
   ```

## Roadmap

We welcome contributions! Here's the planned roadmap for this project. Pick any item and submit a PR.

### Database Improvements
- [ ] Add proper indexes for faster queries
- [ ] Add `juz` (parts) table with ayah ranges
- [ ] Add `hizb` and `rub` (quarter) divisions
- [ ] Add `pages` table (Mushaf page mapping)
- [ ] Add word-by-word breakdown table (Arabic root, morphology)
- [ ] Add sajdah (prostration) markers
- [ ] Support PostgreSQL and SQLite exports
- [ ] Add foreign key constraints and proper normalization

### Data Expansion
- [ ] Add more translations (Urdu, French, Turkish, Indonesian, etc.)
- [ ] Add Tafsir (exegesis) data — Ibn Kathir, Al-Tabari, Al-Sa'di, etc.
- [ ] Add audio recitation references (Mishary, Al-Husary, Abdul Basit, etc.)
- [ ] Add transliteration for each ayah
- [ ] Add asbab al-nuzul (reasons of revelation)
- [ ] Add hadith references related to each ayah
- [ ] Add dua (supplication) extractions from the Quran

### API / Backend
- [ ] Build a RESTful API (Node.js or Python)
- [ ] GraphQL endpoint for flexible queries
- [ ] Search endpoint with full-text Arabic search
- [ ] Pagination and filtering support
- [ ] API rate limiting and authentication
- [ ] Docker setup for easy deployment
- [ ] API documentation (Swagger / OpenAPI)

### Frontend / App
- [ ] Web app for browsing surahs and ayahs
- [ ] Ayah-by-ayah reader with translation toggle
- [ ] Audio player integration with reciter selection
- [ ] Search functionality (by surah, ayah, keyword)
- [ ] Bookmarking and progress tracking
- [ ] Dark mode and responsive design
- [ ] Mobile-friendly PWA support

## Contributing

Contributions are welcome and encouraged! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Contribution Guidelines
- Follow the existing database schema conventions
- Include sample queries or screenshots for database changes
- Add tests for API endpoints
- Keep translations accurate — reference established scholarly sources
- For new data, include the source/reference

If you're unsure where to start, look for items marked in the roadmap above or open an issue to discuss your idea.

## Screenshots

![Surahs Table](screenshots/Screen%20Shot%202022-04-19%20at%207.56.15%20AM.png)
![Ayahs Table](screenshots/Screen%20Shot%202022-04-19%20at%207.55.54%20AM.png)
![Editions Table](screenshots/Screen%20Shot%202022-04-19%20at%207.56.08%20AM.png)
![Addons Table](screenshots/Screen%20Shot%202022-04-19%20at%207.55.32%20AM.png)

## Related Projects

- [Quran Lumen API](https://github.com/AbdullahGhanem/quran-lumen-api) — Laravel Lumen API
- [Quran Vue](https://github.com/adibemohamed/quranaho)

## Sponsor

[Become a Sponsor](https://github.com/sponsors/AbdullahGhanem)

## License

This project is open source. The Quran text is in the public domain.
