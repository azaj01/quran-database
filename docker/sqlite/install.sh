#!/usr/bin/env bash
set -euo pipefail

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

echo "Extracting the Quran source dump for SQLite..."
unzip -q /opt/quran/quran.sql.zip quran.sql -d "${workdir}"

echo "Generating /output/quran.db..."
cd "${workdir}"
python3 /opt/quran/convert_to_sqlite.py
python3 -c 'import sqlite3; db = sqlite3.connect("quran.db"); db.execute("PRAGMA journal_mode=DELETE"); db.close()'
install -m 0644 quran.db /output/quran.db
echo "SQLite Quran export complete."
