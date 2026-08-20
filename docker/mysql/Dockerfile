FROM python:3.12-slim-bookworm AS source

COPY data/quran.sql.zip /tmp/quran.sql.zip
RUN mkdir /opt/quran \
    && python -c 'import gzip, shutil, zipfile; archive = zipfile.ZipFile("/tmp/quran.sql.zip"); source = archive.open("quran.sql"); target = gzip.open("/opt/quran/quran.sql.gz", "wb"); shutil.copyfileobj(source, target); source.close(); target.close(); archive.close()'

FROM mysql:8.4

COPY --chmod=755 docker/mysql/install.sh /docker-entrypoint-initdb.d/10-quran.sh
COPY --from=source /opt/quran/quran.sql.gz /docker-entrypoint-initdb.d/20-quran.sql.gz
