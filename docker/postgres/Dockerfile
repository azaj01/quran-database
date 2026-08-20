FROM postgres:16-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      python3 \
      python3-psycopg2 \
      unzip \
    && rm -rf /var/lib/apt/lists/*

COPY data/quran.sql.zip /opt/quran/quran.sql.zip
COPY convert_to_postgres.py /opt/quran/convert_to_postgres.py
COPY --chmod=755 docker/postgres/install.sh /docker-entrypoint-initdb.d/10-quran.sh
