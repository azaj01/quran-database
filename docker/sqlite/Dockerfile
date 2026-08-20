FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*

COPY data/quran.sql.zip /opt/quran/quran.sql.zip
COPY convert_to_sqlite.py /opt/quran/convert_to_sqlite.py
COPY --chmod=755 docker/sqlite/install.sh /usr/local/bin/export-quran-sqlite

ENTRYPOINT ["export-quran-sqlite"]
