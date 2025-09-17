#!/usr/bin/env python3
"""Check current database state"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='fantrax_user',
    password='fantrax_password',
    database='fantrax_value_hunter'
)

cur = conn.cursor()

# Count players
cur.execute('SELECT COUNT(*) FROM players')
print(f'Total players: {cur.fetchone()[0]}')

# List tables
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public'
    ORDER BY table_name
""")
print('\nCurrent tables:')
for t in cur.fetchall():
    print(f'  - {t[0]}')

# Check if snapshot tables exist
cur.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema='public'
    AND table_name LIKE '%snapshot%'
""")
snapshot_count = cur.fetchone()[0]
print(f'\nSnapshot tables found: {snapshot_count}')

conn.close()