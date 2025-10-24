#!/usr/bin/env python3
"""
Update Fixture Multipliers in Database
Applies the corrected NPxG calculation to all players
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

print("FIXTURE MULTIPLIER UPDATE")
print("=" * 70)
print("This will update all fixture multipliers with the corrected calculation")
print("that properly uses the is_home flag.\n")

# First, ensure AVG row exists
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("Step 1: Ensuring league average row exists...")
cursor.execute("""
    INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
    SELECT
        'AVG' as team_code,
        'League Average' as team_name,
        AVG(npxg) as npxg,
        AVG(npxga) as npxga,
        AVG(npxg) - AVG(npxga) as npxgd,
        20 as matches_played,
        NOW() as last_updated
    FROM team_metrics
    WHERE team_code != 'AVG' AND npxg IS NOT NULL
    ON CONFLICT (team_code) DO UPDATE SET
        npxg = EXCLUDED.npxg,
        npxga = EXCLUDED.npxga,
        npxgd = EXCLUDED.npxgd,
        last_updated = EXCLUDED.last_updated
""")
conn.commit()
print("  [OK] League average row ready\n")

# Load parameters to get NPxG weight
with open('config/system_parameters.json', 'r') as f:
    params = json.load(f)

slider_value = params['formula_optimization_v2']['exponential_fixture']['base']
middle = 1.325
if slider_value <= middle:
    npxg_weight = 0.80 + (slider_value - 1.15) / (middle - 1.15) * 0.20
else:
    npxg_weight = 1.00 + (slider_value - middle) / (1.50 - middle) * 0.20

print(f"Step 2: Using NPxG weight {npxg_weight:.3f} (from slider {slider_value})\n")

# Initialize engine with current parameters
engine = FormulaEngineV2(DB_CONFIG, params)

# Get all players with opponents
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cursor.execute("""
    SELECT pm.player_id, p.position, pm.next_opponent, pm.is_home, pm.fixture_multiplier as old_mult
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE pm.next_opponent IS NOT NULL AND pm.next_opponent != ''
""")

players = cursor.fetchall()
print(f"Step 3: Updating {len(players)} players...")

start_time = time.time()
batch_updates = []
fixes_needed = 0

for player in players:
    player_data = {
        'player_id': player['player_id'],
        'name': '',
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

    # Initialize engine once outside loop (actually, move this before the loop)
    # Calculate correct multiplier
    new_mult = engine._calculate_npxg_fixture_multiplier(player_data)
    old_mult = float(player['old_mult']) if player['old_mult'] else 0

    # Track how many need fixing
    if player['is_home'] and old_mult < 1.0 and new_mult > 1.0:
        fixes_needed += 1

    batch_updates.append((new_mult, player['player_id']))

# Update database
cursor.executemany("""
    UPDATE player_metrics
    SET fixture_multiplier = %s
    WHERE player_id = %s
""", batch_updates)

conn.commit()
elapsed = time.time() - start_time

print(f"\n[DONE] Updated {len(players)} players in {elapsed:.2f} seconds")
print(f"  Fixed {fixes_needed} home teams that had incorrect penalties\n")

# Verify the fix
cursor.execute("""
    SELECT
        p.name, pm.fixture_multiplier, pm.is_home
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE p.team = 'MCI' AND pm.next_opponent = 'EVE'
    LIMIT 3
""")

print("Verification - Man City vs Everton (HOME):")
for row in cursor.fetchall():
    status = "[OK]" if row['fixture_multiplier'] > 1.0 else "[X]"
    print(f"  {status} {row['name'][:25]:25} {row['fixture_multiplier']:.3f}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("COMPLETE! Fixture multipliers have been corrected.")
print("Home teams now have appropriate boosts (>1.0)")
print("\nNext: Trigger a recalculation from the dashboard to update True Values")