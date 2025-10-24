#!/usr/bin/env python3
"""
Force update fixture multipliers for all players
"""

import sys
sys.path.append('src')
sys.path.append('.')

import psycopg2
import psycopg2.extras
from calculation_engine_v2 import FormulaEngineV2
import json
import time

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

print("=" * 70)
print("FORCING FIXTURE MULTIPLIER UPDATE")
print("=" * 70)

# Load parameters
with open('config/system_parameters.json', 'r') as f:
    params = json.load(f)

# Initialize engine
engine = FormulaEngineV2(DB_CONFIG, params)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get all players with opponents
cursor.execute("""
    SELECT
        p.id, p.name, p.position,
        pm.next_opponent, pm.is_home
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.next_opponent IS NOT NULL AND pm.next_opponent != ''
""")

players = cursor.fetchall()
print(f"Updating {len(players)} players...")

start_time = time.time()
updates = []

for i, player in enumerate(players):
    player_data = {
        'player_id': player['id'],
        'name': player['name'],
        'position': player['position'],
        'next_opponent': player['next_opponent'],
        'is_home': player['is_home'],
        # Dummy data for other required fields
        'price': 10.0,
        'ppg': 5.0,
        'xgi90': 0.3,
        'baseline_xgi': None,
        'fixture_difficulty': 0.0,
        'starter_multiplier': 1.0,
        'total_points_historical': 0,
        'games_played_historical': 0,
        'games_historical': 0,
        'total_points_current': 50,
        'games_current': 10,
        'historical_ppg': None
    }

    # Calculate fixture multiplier only
    result = engine._calculate_npxg_fixture_multiplier(player_data)
    updates.append((result, player['id']))

    if (i + 1) % 100 == 0:
        print(f"  Processed {i + 1}/{len(players)}...")

# Update database
print("Applying updates to database...")
cursor.executemany("""
    UPDATE player_metrics
    SET fixture_multiplier = %s
    WHERE player_id = %s
""", updates)

conn.commit()

# Verify some results
print("\nVerification - Sample players:")
cursor.execute("""
    SELECT p.name, p.team, pm.next_opponent, pm.is_home, pm.fixture_multiplier
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE p.team IN ('MCI', 'WHU', 'LIV', 'ARS')
    AND p.name IN (
        'Erling Haaland', 'Phil Foden',
        'Mohammed Kudus', 'Jarrod Bowen',
        'Mohamed Salah', 'Darwin Nunez',
        'Bukayo Saka', 'Martin Odegaard'
    )
    ORDER BY p.team, p.name
""")

for player in cursor.fetchall():
    location = "HOME" if player['is_home'] else "AWAY"
    print(f"  {player['name'][:20]:20} ({player['team']}) vs {player['next_opponent']} {location:5} = {player['fixture_multiplier']:.3f}")

cursor.close()
conn.close()

elapsed = time.time() - start_time
print(f"\n[DONE] Updated {len(players)} players in {elapsed:.2f} seconds")
print("=" * 70)