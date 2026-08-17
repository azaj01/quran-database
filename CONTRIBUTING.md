# Contributing to Quran Database

Thank you for helping improve Quran Database. Contributions may affect sacred
text and a large derived dataset, so changes should be small, reproducible, and
easy to review.

Before starting substantial work, open an issue or comment on an existing one.
This helps confirm the scope, data source, and schema direction before time is
spent on an implementation.

## Repository orientation

- `data/quran.sql.zip` is the tracked MySQL source dump.
- `convert_to_sqlite.py` and `convert_to_postgres.py` stream an extracted
  root-level `quran.sql` into their target databases.
- `quran.db.gz` is the distributed compressed SQLite database.
- `schema/` is reserved for readable, database-specific schema references.
- [`docs/architecture.md`](docs/architecture.md) describes the data flow,
  domain model, and known constraints.

## Prepare a change

1. Fork the repository and clone your fork.
2. Add the canonical repository as `upstream`:

   ```bash
   git remote add upstream https://github.com/AbdullahGhanem/quran-database.git
   git fetch upstream
   ```

3. Create a focused branch from the latest upstream default branch:

   ```bash
   git switch --create feat/short-description upstream/main
   ```

Use a short prefix that matches the change, such as `feat/`, `fix/`, `docs/`,
`test/`, or `chore/`. Keep one concern per branch and avoid including unrelated
formatting or generated artifacts.

## Make the change

### Code and schema changes

- Preserve streaming behavior; the uncompressed dump is large and should not
  be loaded into memory as one value.
- Keep the SQLite and PostgreSQL target models aligned unless the pull request
  clearly explains a database-specific difference.
- Treat generated databases and schema references as outputs. Change their
  source or generator, regenerate them, and include the verification command in
  the pull request.
- Do not weaken foreign keys, checks, or post-import validation to make an
  import pass. Explain and test changes to constraints or import order.
- Do not commit extracted dumps, local databases, credentials, editor files, or
  cache directories.

### Quranic text and metadata

- Do not manually “correct” Quranic text, translations, transliterations, or
  recitation metadata without an authoritative, reviewable source.
- Cite the source, its version or retrieval date, and its license or reuse terms
  in the pull request. Include a script or documented procedure that reproduces
  a bulk data change.
- Preserve Unicode text exactly. Verify representative Arabic text, including
  tashkeel, after every import or conversion change.
- Call out changes to identifiers, verse numbering, surah boundaries, sajdah
  markers, pages, juzs, hizbs, or rub-el-hizb values explicitly.

### Documentation

Document the repository as it exists on the target branch. Clearly label
planned components and do not describe placeholders as implemented features.
Use relative links so documentation works both on GitHub and in a local clone.

## Verify the change

Run the checks that are relevant to the files you changed. Every change should
pass:

```bash
git diff --check
```

For Python changes, also run at minimum:

```bash
python3 -m py_compile convert_to_sqlite.py convert_to_postgres.py
```

For converter, schema, or data changes, also perform a clean end-to-end import
for every affected database and report:

- 114 surahs;
- 6,236 ayahs;
- 134 editions;
- 835,624 `ayah_edition` rows;
- intact representative Arabic text;
- no unexpected foreign-key violations or orphaned relationships.

If a check cannot be run, say why in the pull request. Do not imply that a
static or partial check is an end-to-end verification.

## Commit and open a pull request

Use a concise, imperative commit subject. Conventional Commit prefixes are
preferred, for example:

```text
docs: explain database architecture
fix: preserve Arabic text during PostgreSQL import
```

Push the branch to your fork and open a pull request against
`AbdullahGhanem/quran-database:main`. The pull request should include:

- the problem and the chosen approach;
- the scope and any intentional omissions;
- data provenance and licensing details when data changes;
- exact verification commands and results;
- migration or compatibility impact;
- screenshots only when they clarify a visual change.

Respond to review with additional commits. Avoid force-pushing after review has
started unless rebasing is necessary and clearly communicated.
