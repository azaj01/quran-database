#!/usr/bin/env python3
"""
Convert quran.sql (MySQL dump) to quran.db (SQLite) with schema improvements.
Line-based streaming parser — handles multi-line INSERT statements.
"""

import sqlite3
import re
import os
from pathlib import Path

SQL_FILE = "quran.sql"
DB_FILE = "quran.db"

def create_sqlite_schema(db):
    """Create the improved SQLite schema."""
    db.executescript("""
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;
        PRAGMA encoding = 'UTF-8';

        CREATE TABLE IF NOT EXISTS surahs (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_en_translation TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('meccan', 'medinan', 'Meccan', 'Medinan')),
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS juzs (
            id INTEGER PRIMARY KEY,
            juz_number INTEGER NOT NULL UNIQUE,
            name_ar TEXT NOT NULL,
            start_ayah_id INTEGER NOT NULL,
            end_ayah_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hizbs (
            id INTEGER PRIMARY KEY,
            hizb_number INTEGER NOT NULL UNIQUE,
            juz_id INTEGER NOT NULL,
            name_ar TEXT NOT NULL,
            start_ayah_id INTEGER NOT NULL,
            end_ayah_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ayahs (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL,
            text TEXT NOT NULL,
            number_in_surah INTEGER NOT NULL,
            page INTEGER NOT NULL,
            surah_id INTEGER NOT NULL REFERENCES surahs(id),
            hizb_id INTEGER NOT NULL,
            juz_id INTEGER NOT NULL,
            sajda INTEGER NOT NULL DEFAULT 0 CHECK(sajda IN (0, 1)),
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS editions (
            id INTEGER PRIMARY KEY,
            identifier TEXT NOT NULL UNIQUE,
            language TEXT NOT NULL,
            name TEXT NOT NULL,
            english_name TEXT NOT NULL,
            format TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS ayah_edition (
            id INTEGER PRIMARY KEY,
            ayah_id INTEGER NOT NULL REFERENCES ayahs(id),
            edition_id INTEGER NOT NULL REFERENCES editions(id),
            data TEXT NOT NULL,
            is_audio INTEGER NOT NULL DEFAULT 0 CHECK(is_audio IN (0, 1)),
            created_at TEXT,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_ayahs_surah_id ON ayahs(surah_id);
        CREATE INDEX IF NOT EXISTS idx_ayahs_juz_id ON ayahs(juz_id);
        CREATE INDEX IF NOT EXISTS idx_ayahs_hizb_id ON ayahs(hizb_id);
        CREATE INDEX IF NOT EXISTS idx_ayahs_page ON ayahs(page);
        CREATE INDEX IF NOT EXISTS idx_ayahs_number_in_surah ON ayahs(surah_id, number_in_surah);
        CREATE INDEX IF NOT EXISTS idx_ayahs_sajda ON ayahs(sajda) WHERE sajda = 1;
        CREATE INDEX IF NOT EXISTS idx_ayah_edition_ayah ON ayah_edition(ayah_id);
        CREATE INDEX IF NOT EXISTS idx_ayah_edition_edition ON ayah_edition(edition_id);
        CREATE INDEX IF NOT EXISTS idx_ayah_edition_lookup ON ayah_edition(ayah_id, edition_id);
    """)


def parse_sql_value(v):
    """Parse a single SQL value string into Python type."""
    v = v.strip()
    if v == 'NULL':
        return None
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        s = v[1:-1]
        s = s.replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')
        s = s.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        # Handle BOM at start of first value
        if s.startswith('\ufeff'):
            s = s[1:]
        return s
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def parse_insert_row(line, col_names):
    """Parse a single (...) row from an INSERT VALUES clause into a tuple."""
    # Remove leading ( and trailing ), then split by , while handling quotes
    line = line.strip()
    if line.startswith('('):
        line = line[1:]
    if line.endswith(');') or line.endswith(');\n'):
        line = line[:-2].strip()
    elif line.endswith(')'):
        line = line[:-1]
    
    values = []
    current = ''
    in_quotes = False
    quote_char = None
    escape_next = False
    
    for ch in line:
        if escape_next:
            current += ch
            escape_next = False
            continue
        if ch == '\\':
            current += ch
            escape_next = True
            continue
        if in_quotes:
            current += ch
            if ch == quote_char:
                in_quotes = False
        else:
            if ch in ("'", '"'):
                in_quotes = True
                quote_char = ch
                current += ch
            elif ch == ',':
                values.append(parse_sql_value(current))
                current = ''
            else:
                current += ch
    
    if current.strip():
        values.append(parse_sql_value(current.strip()))
    
    return tuple(values)


def column_map(col_str):
    """Extract column names from INSERT column specification."""
    clean = [c.strip('` ') for c in col_str.split(',')]
    return clean


def stream_inserts(filepath):
    """Generator that yields (table_name, columns, [rows]) from MySQL dump."""
    in_insert = False
    current_table = None
    current_columns = None
    current_rows = []
    
    insert_pattern = re.compile(r"INSERT INTO `([^`]+)` \((.*?)\) VALUES", re.IGNORECASE)
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            
            if in_insert:
                # Check if this is the end of the INSERT
                stripped = line.strip()
                if stripped.endswith(');'):
                    # Remove trailing );
                    value = stripped[:-2].strip()
                    if value.startswith('('):
                        row = parse_insert_row(value, current_columns)
                        current_rows.append(row)
                    yield (current_table, current_columns, current_rows)
                    current_rows = []
                    in_insert = False
                    current_table = None
                    current_columns = None
                elif stripped.endswith('),'):
                    value = stripped[:-2].strip()
                    if value.startswith('('):
                        row = parse_insert_row(value, current_columns)
                        current_rows.append(row)
                elif stripped.startswith('(') and stripped.endswith(')'):
                    row = parse_insert_row(stripped, current_columns)
                    current_rows.append(row)
                else:
                    # Could be continuation of a single row
                    pass
            
            # Check for new INSERT statement
            m = insert_pattern.search(line)
            if m and not in_insert:
                current_table = m.group(1)
                current_columns_raw = m.group(2)
                current_columns = [c.strip('` ') for c in current_columns_raw.split(',')]
                current_rows = []
                in_insert = True
                
                # Check if values start on the same line
                after_values = line[m.end():].strip()
                if after_values.startswith('('):
                    if after_values.endswith(');'):
                        row = parse_insert_row(after_values, current_columns)
                        current_rows.append(row)
                        yield (current_table, current_columns, current_rows)
                        current_rows = []
                        in_insert = False
                    elif after_values.endswith('),'):
                        row = parse_insert_row(after_values, current_columns)
                        current_rows.append(row)
                    elif after_values.endswith(')'):
                        row = parse_insert_row(after_values, current_columns)
                        current_rows.append(row)
    
    # Yield any remaining
    if in_insert and current_rows:
        yield (current_table, current_columns, current_rows)


def populate_lookup_tables(db):
    """Populate juzs and hizbs lookup tables."""
    juzs_data = [
        (1,  1,  'الجزء الأول',   1,   148),
        (2,  2,  'الجزء الثاني',   149, 259),
        (3,  3,  'الجزء الثالث',   260, 385),
        (4,  4,  'الجزء الرابع',   386, 516),
        (5,  5,  'الجزء الخامس',   517, 640),
        (6,  6,  'الجزء السادس',   641, 750),
        (7,  7,  'الجزء السابع',   751, 899),
        (8,  8,  'الجزء الثامن',   900, 1041),
        (9,  9,  'الجزء التاسع',   1042, 1230),
        (10, 10, 'الجزء العاشر',   1231, 1414),
        (11, 11, 'الجزء الحادي عشر',  1415, 1597),
        (12, 12, 'الجزء الثاني عشر',  1598, 1773),
        (13, 13, 'الجزء الثالث عشر',  1774, 1934),
        (14, 14, 'الجزء الرابع عشر',  1935, 2078),
        (15, 15, 'الجزء الخامس عشر',  2079, 2213),
        (16, 16, 'الجزء السادس عشر',  2214, 2395),
        (17, 17, 'الجزء السابع عشر',  2396, 2548),
        (18, 18, 'الجزء الثامن عشر',  2549, 2722),
        (19, 19, 'الجزء التاسع عشر',  2723, 2889),
        (20, 20, 'الجزء العشرون',     2890, 3050),
        (21, 21, 'الجزء الحادي والعشرون',  3051, 3187),
        (22, 22, 'الجزء الثاني والعشرون',  3188, 3325),
        (23, 23, 'الجزء الثالث والعشرون',  3326, 3495),
        (24, 24, 'الجزء الرابع والعشرون',  3496, 3667),
        (25, 25, 'الجزء الخامس والعشرون',  3668, 3838),
        (26, 26, 'الجزء السادس والعشرون',  3839, 4006),
        (27, 27, 'الجزء السابع والعشرون',  4007, 4203),
        (28, 28, 'الجزء الثامن والعشرون',  4204, 4405),
        (29, 29, 'الجزء التاسع والعشرون',  4406, 4602),
        (30, 30, 'الجزء الثلاثون',         4603, 6236),
    ]
    hizbs_data = [
        (1,  1,  1,  'الحزب الأول',     1,    74),
        (2,  2,  1,  'الحزب الثاني',     75,   148),
        (3,  3,  2,  'الحزب الثالث',    149,  202),
        (4,  4,  2,  'الحزب الرابع',    203,  259),
        (5,  5,  3,  'الحزب الخامس',    260,  321),
        (6,  6,  3,  'الحزب السادس',    322,  385),
        (7,  7,  4,  'الحزب السابع',    386,  450),
        (8,  8,  4,  'الحزب الثامن',    451,  516),
        (9,  9,  5,  'الحزب التاسع',    517,  577),
        (10, 10, 5,  'الحزب العاشر',    578,  640),
        (11, 11, 6,  'الحزب الحادي عشر',   641,  694),
        (12, 12, 6,  'الحزب الثاني عشر',   695,  750),
        (13, 13, 7,  'الحزب الثالث عشر',   751,  826),
        (14, 14, 7,  'الحزب الرابع عشر',   827,  899),
        (15, 15, 8,  'الحزب الخامس عشر',   900,  969),
        (16, 16, 8,  'الحزب السادس عشر',   970,  1041),
        (17, 17, 9,  'الحزب السابع عشر',   1042, 1134),
        (18, 18, 9,  'الحزب الثامن عشر',   1135, 1230),
        (19, 19, 10, 'الحزب التاسع عشر',   1231, 1321),
        (20, 20, 10, 'الحزب العشرون',      1322, 1414),
        (21, 21, 11, 'الحزب الحادي والعشرون',  1415, 1505),
        (22, 22, 11, 'الحزب الثاني والعشرون',  1506, 1597),
        (23, 23, 12, 'الحزب الثالث والعشرون',  1598, 1684),
        (24, 24, 12, 'الحزب الرابع والعشرون',  1685, 1773),
        (25, 25, 13, 'الحزب الخامس والعشرون',  1774, 1852),
        (26, 26, 13, 'الحزب السادس والعشرون',  1853, 1934),
        (27, 27, 14, 'الحزب السابع والعشرون',  1935, 2005),
        (28, 28, 14, 'الحزب الثامن والعشرون',  2006, 2078),
        (29, 29, 15, 'الحزب التاسع والعشرون',  2079, 2144),
        (30, 30, 15, 'الحزب الثلاثون',         2145, 2213),
        (31, 31, 16, 'الحزب الحادي والثلاثون',  2214, 2303),
        (32, 32, 16, 'الحزب الثاني والثلاثون',  2304, 2395),
        (33, 33, 17, 'الحزب الثالث والثلاثون',  2396, 2470),
        (34, 34, 17, 'الحزب الرابع والثلاثون',  2471, 2548),
        (35, 35, 18, 'الحزب الخامس والثلاثون',  2549, 2634),
        (36, 36, 18, 'الحزب السادس والثلاثون',  2635, 2722),
        (37, 37, 19, 'الحزب السابع والثلاثون',  2723, 2804),
        (38, 38, 19, 'الحزب الثامن والثلاثون',  2805, 2889),
        (39, 39, 20, 'الحزب التاسع والثلاثون',  2890, 2968),
        (40, 40, 20, 'الحزب الأربعون',         2969, 3050),
        (41, 41, 21, 'الحزب الحادي والأربعون',  3051, 3117),
        (42, 42, 21, 'الحزب الثاني والأربعون',  3118, 3187),
        (43, 43, 22, 'الحزب الثالث والأربعون',  3188, 3253),
        (44, 44, 22, 'الحزب الرابع والأربعون',  3254, 3325),
        (45, 45, 23, 'الحزب الخامس والأربعون',  3326, 3409),
        (46, 46, 23, 'الحزب السادس والأربعون',  3410, 3495),
        (47, 47, 24, 'الحزب السابع والأربعون',  3496, 3580),
        (48, 48, 24, 'الحزب الثامن والأربعون',  3581, 3667),
        (49, 49, 25, 'الحزب التاسع والأربعون',  3668, 3749),
        (50, 50, 25, 'الحزب الخمسون',          3750, 3838),
        (51, 51, 26, 'الحزب الحادي والخمسون',   3839, 3919),
        (52, 52, 26, 'الحزب الثاني والخمسون',   3920, 4006),
        (53, 53, 27, 'الحزب الثالث والخمسون',   4007, 4101),
        (54, 54, 27, 'الحزب الرابع والخمسون',   4102, 4203),
        (55, 55, 28, 'الحزب الخامس والخمسون',   4204, 4300),
        (56, 56, 28, 'الحزب السادس والخمسون',   4301, 4405),
        (57, 57, 29, 'الحزب السابع والخمسون',   4406, 4503),
        (58, 58, 29, 'الحزب الثامن والخمسون',   4504, 4602),
        (59, 59, 30, 'الحزب التاسع والخمسون',   4603, 5415),
        (60, 60, 30, 'الحزب الستون',            5416, 6236),
    ]
    db.executemany("INSERT INTO juzs VALUES (?,?,?,?,?)", juzs_data)
    db.executemany("INSERT INTO hizbs VALUES (?,?,?,?,?,?)", hizbs_data)


TABLE_ORDER = ['surahs', 'ayahs', 'editions', 'ayah_edition']


def convert():
    print("Creating SQLite database with improved schema...")

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db = sqlite3.connect(DB_FILE)
    create_sqlite_schema(db)
    
    # Disable FK checks during import for speed and to handle cross-references
    db.execute("PRAGMA foreign_keys = OFF")
    
    table_counts = {t: 0 for t in TABLE_ORDER}
    
    print(f"Reading {SQL_FILE}...")
    
    for table, columns, rows in stream_inserts(SQL_FILE):
        if table in TABLE_ORDER:
            ncols = len(columns)
            placeholders = ','.join(['?'] * ncols)
            insert_sql = f"INSERT INTO {table} VALUES ({placeholders})"
            
            db.executemany(insert_sql, rows)
            table_counts[table] += len(rows)
            if table_counts[table] <= len(rows) or table_counts[table] % 5000 == 0:
                print(f"  {table}: {table_counts[table]} rows...")
    
    # Re-enable FK checks
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA foreign_key_check")
    db.commit()
    
    db.commit()
    
    # Populate lookup tables after data
    print("  Populating juzs and hizbs lookup tables...")
    populate_lookup_tables(db)
    
    # Create views
    db.execute("""
        CREATE VIEW IF NOT EXISTS surah_stats AS
        SELECT s.id, s.name_ar, s.name_en, s.name_en_translation, s.type,
               COUNT(a.id) as ayat_count,
               MIN(a.id) as start_ayah_id,
               MAX(a.id) as end_ayah_id
        FROM surahs s
        JOIN ayahs a ON a.surah_id = s.id
        GROUP BY s.id
    """)
    
    db.execute("""
        CREATE VIEW IF NOT EXISTS ayah_with_translation AS
        SELECT a.id, a.surah_id, a.number_in_surah, a.text as arabic,
               ae.data as translation, e.language, e.name as edition_name
        FROM ayahs a
        JOIN ayah_edition ae ON ae.ayah_id = a.id
        JOIN editions e ON e.id = ae.edition_id
    """)
    
    db.commit()
    
    print(f"\nDatabase created: {DB_FILE}")
    for table in TABLE_ORDER:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")
    
    sajdah_count = db.execute("SELECT COUNT(*) FROM ayahs WHERE sajda = 1").fetchone()[0]
    juz_count = db.execute("SELECT COUNT(*) FROM juzs").fetchone()[0]
    hizb_count = db.execute("SELECT COUNT(*) FROM hizbs").fetchone()[0]
    print(f"  Sajdah ayahs: {sajdah_count}, Juzs: {juz_count}, Hizbs: {hizb_count}")
    
    db_size = os.path.getsize(DB_FILE) / (1024 * 1024)
    print(f"  Database size: {db_size:.1f} MB")
    
    db.close()
    print("\nDone!")


if __name__ == '__main__':
    convert()
