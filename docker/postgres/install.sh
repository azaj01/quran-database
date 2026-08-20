#!/usr/bin/env bash
set -euo pipefail

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

echo "Extracting the Quran source dump for PostgreSQL..."
unzip -q /opt/quran/quran.sql.zip quran.sql -d "${workdir}"

echo "Importing Quran data into PostgreSQL database ${POSTGRES_DB}..."
cd "${workdir}"
PGHOST=/var/run/postgresql \
PGPORT=5432 \
PGUSER="${POSTGRES_USER}" \
PGPASSWORD="${POSTGRES_PASSWORD}" \
PGDATABASE="${POSTGRES_DB}" \
python3 /opt/quran/convert_to_postgres.py
echo "PostgreSQL Quran import complete."
