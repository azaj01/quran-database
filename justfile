set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Show the available project commands.
default:
    @just --list

# Check that the local tools used by the current workflows are installed.
doctor:
    @command -v python3 >/dev/null
    @command -v unzip >/dev/null
    @echo "Required tools are available."

# Extract quran.sql from the repository's source archive when needed.
extract: doctor
    @if [[ -f quran.sql ]]; then \
        echo "quran.sql already exists; leaving it unchanged."; \
    else \
        unzip data/quran.sql.zip quran.sql; \
    fi

# Build quran.db from the MySQL dump.
sqlite: extract
    python3 convert_to_sqlite.py

# Build a PostgreSQL database from the MySQL dump. Honours PGHOST/PGUSER/PGDATABASE.
postgres: extract
    python3 convert_to_postgres.py

# Validate the Python converters and run the test suite.
check: doctor
    unzip -tqq data/quran.sql.zip
    python3 -c 'from pathlib import Path; [compile(Path(p).read_bytes(), p, "exec") for p in ("convert_to_sqlite.py", "convert_to_postgres.py")]'
    python3 -m unittest discover -s tests
