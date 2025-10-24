#!/usr/bin/env python3
"""
Quick Fix: Update fixture multipliers directly
Faster targeted update for fixture multipliers
"""

import sys
sys.path.append('src')
sys.path.append('.')

import psycopg2
import psycopg2.extras
from src.npxg_fixture_multiplier import get_npxg_multiplier_for_player
import json
import time

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

# Load parameters to get NPxG weight
with open('config/system_parameters.json', 'r') as f:
    params = json.load(f)

# Calculate NPxG weight from slider
slider_value = params['formula_optimization_v2']['exponential_fixture']['base']
middle = 1.325
if slider_value <= middle:
    npxg_weight = 0.80 + (slider_value - 1.15) / (middle - 1.15) * 0.20
else:
    npxg_weight = 1.00 + (slider_value - middle) / (1.50 - middle) * 0.20

print(f"Using NPxG weight: {npxg_weight:.3f} (from slider value {slider_value})")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# First show some examples
print("\nChecking Man City players (should be HOME vs Everton):")
cursor.execute("""
    SELECT p.name, p.position, pm.next_opponent, pm.is_home, pm.fixture_multiplier
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE p.team = 'MCI' AND pm.next_opponent = 'EVE'
    LIMIT 5
""")

for row in cursor.fetchall():
    old_mult = row['fixture_multiplier']
    # Calculate new multiplier
    player_data = {
        'position': row['position'],
        'next_opponent': row['next_opponent'],
        'is_home': row['is_home']
    }
    new_mult = get_npxg_multiplier_for_player(player_data, DB_CONFIG, npxg_weight)

    status = "HOME" if row['is_home'] else "AWAY"
    change = "FIX NEEDED" if old_mult < 1.0 and row['is_home'] else "OK"
    print(f"  {row['name'][:25]:25} {status:5} Old: {old_mult:.3f} -> New: {new_mult:.3f} [{change}]")

print("\n" + "-" * 70)
response = input("Update ALL fixture multipliers? (y/n): ")
if response.lower() != 'y':
    print("Cancelled")
    sys.exit(0)

# Get all players with opponents
cursor.execute("""
    SELECT pm.player_id, p.position, pm.next_opponent, pm.is_home
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE pm.next_opponent IS NOT NULL AND pm.next_opponent != ''
""")

players = cursor.fetchall()
print(f"\nUpdating {len(players)} players...")

start_time = time.time()
updated = 0
batch_updates = []

for player in players:
    player_data = {
        'position': player['position'],
        'next_opponent': player['next_opponent'],
        'is_home': player['is_home']
    }

    # Calculate correct multiplier
    new_mult = get_npxg_multiplier_for_player(player_data, DB_CONFIG, npxg_weight)
    batch_updates.append((new_mult, player['player_id']))

    updated += 1
    if updated % 100 == 0:
        print(f"  Processed {updated}/{len(players)} players...")

# Batch update
cursor.executemany("""
    UPDATE player_metrics
    SET fixture_multiplier = %s
    WHERE player_id = %s
""", batch_updates)

conn.commit()
elapsed = time.time() - start_time

print(f"\nDONE! Updated {updated} players in {elapsed:.2f} seconds")
print("\nVerifying Man City:")

cursor.execute("""
    SELECT p.name, pm.fixture_multiplier
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE p.team = 'MCI' AND p.name IN ('Erling Haaland', 'Phil Foden')
""")

for row in cursor.fetchall():
    print(f"  {row['name']}: {row['fixture_multiplier']:.3f}")

cursor.close()
conn.close()

print("\nMultipliers updated! Now you need to recalculate True Values.")
print("You can do this from the dashboard by adjusting any slider.")