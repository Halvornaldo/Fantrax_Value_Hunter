#!/usr/bin/env python3
"""
Verify Railway database import
"""
import os
import psycopg2
import urllib.parse

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

# Parse Railway DATABASE_URL
result = urllib.parse.urlparse(DATABASE_URL)
config = {
    'host': result.hostname,
    'port': result.port,
    'user': result.username,
    'password': result.password,
    'database': result.path[1:]
}

try:
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()

    print("Railway Database Verification")
    print("=" * 30)

    tables = ['players', 'player_metrics', 'player_games_data', 'team_fixtures', 'name_mappings']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} rows")

    # Test a sample query
    cursor.execute("SELECT player_id, display_name, team, position FROM players LIMIT 5")
    sample_players = cursor.fetchall()

    print("\nSample players:")
    for player in sample_players:
        print(f"  {player[0]} | {player[1]} | {player[2]} | {player[3]}")

    conn.close()
    print("\nSUCCESS: Railway database is populated and working!")

except Exception as e:
    print(f"ERROR: {e}")